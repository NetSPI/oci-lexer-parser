from __future__ import annotations

import re
import sys
from dataclasses import asdict, dataclass
from typing import Any, Literal, Sequence

from antlr4 import CommonTokenStream, InputStream, Token
from antlr4.error.ErrorListener import ErrorListener
from antlr4.error.Errors import ParseCancellationException
from antlr4.error.ErrorStrategy import BailErrorStrategy

from .grammar.gen.DynamicGroupMatchingRuleLexer import DynamicGroupMatchingRuleLexer
from .grammar.gen.DynamicGroupMatchingRuleParser import DynamicGroupMatchingRuleParser as P
from .parser_utils import (
    DG_SCHEMA_VERSION,
    ctx_span,
    simplify_group_tree,
    span_source,
    split_rules_by_newline_preserving_groups,
    strip_comments_preserve_offsets,
    validate_ascii,
)

# Comment stripping / ASCII validation / spans live in parser_utils.


# ============================================================
# Diagnostics
# ============================================================

@dataclass(slots=True)
class SyntaxIssue:
    line: int
    column: int
    message: str
    offending: str | None = None
    expected: list[str] | None = None
    line_text: str | None = None
    caret: str | None = None
    rule_index: int | None = None


class CollectingErrorListener(ErrorListener):
    def __init__(self, source_text: str) -> None:
        super().__init__()
        self.issues: list[SyntaxIssue] = []
        self._lines_keep = source_text.splitlines(keepends=True)

        def _rstrip_crlf(s: str) -> str:
            if s.endswith("\r\n"):
                return s[:-2]
            if s.endswith("\n") or s.endswith("\r"):
                return s[:-1]
            return s

        self._lines = [_rstrip_crlf(ln) for ln in self._lines_keep]

    def syntaxError(  # type: ignore[override]
        self,
        recognizer: Any,
        offendingSymbol: Any,
        line: int,
        column: int,
        msg: Any,
        e: Any,
    ) -> None:
        tok_text = offendingSymbol.text if isinstance(offendingSymbol, Token) else None

        expected_names: list[str] = []
        try:
            exp = recognizer.getExpectedTokens()
            ints = list(exp.toList())
            sym = getattr(recognizer, "symbolicNames", None)
            lit = getattr(recognizer, "literalNames", None)
            for ttype in ints:
                name = None
                if lit and ttype < len(lit) and lit[ttype] is not None:
                    name = lit[ttype]
                elif sym and ttype < len(sym) and sym[ttype] is not None:
                    name = sym[ttype]
                if name:
                    expected_names.append(name)
        except Exception:
            pass

        line_text = None
        caret = None
        try:
            if 1 <= line <= len(self._lines):
                line_text = self._lines[line - 1]
                caret = (" " * column) + "^"
        except Exception:
            pass

        self.issues.append(
            SyntaxIssue(
                line=line,
                column=column,
                message=str(msg),
                offending=tok_text,
                expected=(expected_names or None),
                line_text=line_text,
                caret=caret,
            )
        )


# ============================================================
# Helpers to tolerate generated-parser accessor differences
# ============================================================

def _call0(obj: Any, *names: str) -> Any | None:
    """Try calling the first callable attribute among names()."""
    for name in names:
        fn = getattr(obj, name, None)
        if callable(fn):
            try:
                return fn()
            except TypeError:
                # sometimes accessors take an index; we only want 0-arg ones here
                continue
    return None


def _first_child_text(ctx: Any) -> str | None:
    """Fallback to parse the first child text if no accessor exists."""
    try:
        for ch in ctx.getChildren():
            t = getattr(ch, "getText", None)
            if callable(t):
                s = t()
                if s:
                    return s
            else:
                s2 = getattr(ch, "text", None)
                if isinstance(s2, str) and s2:
                    return s2
    except Exception:
        pass
    return None


def _mode_from_ctx(ctx: Any) -> str:
    """
    Get all/any from:
      1) known accessors
      2) first child token text
      3) default ALL
    """
    mode_ctx = _call0(ctx, "dgMode", "dgMode_", "mode", "mode_", "DGMode", "DGMode_")
    if mode_ctx is not None:
        try:
            return mode_ctx.getText().lower()
        except Exception:
            pass

    first = _first_child_text(ctx)
    if first:
        u = first.upper()
        if u in {"ALL", "ANY"}:
            return u.lower()

    return "all"


def _strip_quotes(s: str) -> str:
    return s[1:-1] if len(s) >= 2 and s[0] == s[-1] == "'" else s


_OCID_RE = re.compile(r"^ocid1\.[a-z0-9_]+\.[a-z0-9-]+\.[a-z0-9-]*\..+$", re.IGNORECASE)


def _is_ocid(value: str) -> bool:
    return bool(_OCID_RE.match(value))


def _rhs_node(raw: str) -> dict[str, Any]:
    if len(raw) >= 2 and raw[0] == "/" and raw[-1] == "/":
        return {"type": "regex", "value": raw, "pattern": raw[1:-1]}
    if _is_ocid(raw):
        return {"type": "ocid", "value": raw}
    return {"type": "literal", "value": raw}


# ============================================================
# Tree building from contexts (using safe accessors)
# ============================================================

def _predicate_node(pred_ctx: Any, *, include_spans: bool, source_text: str) -> dict[str, Any]:
    path_ctx = _call0(pred_ctx, "path")
    path = path_ctx.getText() if path_ctx is not None else pred_ctx.getText()

    node: dict[str, Any] = {"lhs": path}

    op_ctx = _call0(pred_ctx, "op")
    lit_ctx = _call0(pred_ctx, "literal")

    if op_ctx is None or lit_ctx is None:
        node["op"] = "exists"
    else:
        op_txt = op_ctx.getText()
        node["op"] = "neq" if op_txt == "!=" else "eq"
        node["rhs"] = _rhs_node(_strip_quotes(lit_ctx.getText()))

    if include_spans:
        node["span"] = ctx_span(pred_ctx)
        node["source_text"] = span_source(source_text, node["span"])
    return node


def _group_items(group_ctx: Any, *, include_spans: bool, source_text: str) -> list[dict[str, Any]]:
    elist = _call0(group_ctx, "elementList", "elementList_")
    if elist is None:
        return []

    elems = _call0(elist, "element", "element_")
    if elems is None:
        return []

    if not isinstance(elems, list):
        elems = [elems]

    out: list[dict[str, Any]] = []
    for el in elems:
        pred = _call0(el, "predicate", "predicate_")
        if pred is not None:
            out.append(
                {
                    "type": "clause",
                    "node": _predicate_node(pred, include_spans=include_spans, source_text=source_text),
                }
            )
            continue

        grp = _call0(el, "group", "group_")
        if grp is not None:
            out.append(
                {
                    "type": "group",
                    "mode": _mode_from_ctx(el),
                    "items": _group_items(grp, include_spans=include_spans, source_text=source_text),
                    **(
                        {"span": ctx_span(el), "source_text": span_source(source_text, ctx_span(el))}
                        if include_spans
                        else {}
                    ),
                }
            )
            continue

    return out


def _build_tree(rule_ctx: Any, *, include_spans: bool, source_text: str) -> dict[str, Any]:
    """
    Builds a uniform tree:
      {"type":"group","mode":"all|any","items":[...]}
    """
    mode = _mode_from_ctx(rule_ctx)

    gol = _call0(rule_ctx, "groupOrList", "groupOrList_", "grouporList", "grouporList_")
    # Some generated parsers may inline groupOrList; handle both
    if gol is None:
        grp = _call0(rule_ctx, "group", "group_")
        if grp is not None:
            items = _group_items(grp, include_spans=include_spans, source_text=source_text)
            return {
                "type": "group",
                "mode": mode,
                "items": items,
                **(
                    {"span": ctx_span(rule_ctx), "source_text": span_source(source_text, ctx_span(rule_ctx))}
                    if include_spans
                    else {}
                ),
            }

        elist = _call0(rule_ctx, "elementList", "elementList_")
        if elist is None:
            return {"type": "group", "mode": mode, "items": [], **({"span": ctx_span(rule_ctx)} if include_spans else {})}
        # treat elementList as top-level group
        tmp = type("Tmp", (), {"elementList": lambda self: elist})()  # tiny shim
        items = _group_items(tmp, include_spans=include_spans, source_text=source_text)
        return {
            "type": "group",
            "mode": mode,
            "items": items,
            **(
                {"span": ctx_span(rule_ctx), "source_text": span_source(source_text, ctx_span(rule_ctx))}
                if include_spans
                else {}
            ),
        }

    grp = _call0(gol, "group", "group_")
    if grp is not None:
        items = _group_items(grp, include_spans=include_spans, source_text=source_text)
        return {
            "type": "group",
            "mode": mode,
            "items": items,
            **(
                {"span": ctx_span(rule_ctx), "source_text": span_source(source_text, ctx_span(rule_ctx))}
                if include_spans
                else {}
            ),
        }

    elist = _call0(gol, "elementList", "elementList_")
    if elist is not None:
        tmp = type("Tmp", (), {"elementList": lambda self: elist})()
        items = _group_items(tmp, include_spans=include_spans, source_text=source_text)
        return {
            "type": "group",
            "mode": mode,
            "items": items,
            **(
                {"span": ctx_span(rule_ctx), "source_text": span_source(source_text, ctx_span(rule_ctx))}
                if include_spans
                else {}
            ),
        }

    return {
        "type": "group",
        "mode": mode,
        "items": [],
        **(
            {"span": ctx_span(rule_ctx), "source_text": span_source(source_text, ctx_span(rule_ctx))}
            if include_spans
            else {}
        ),
    }


def _level(node: dict[str, Any]) -> int:
    if node.get("type") != "group":
        return 0
    child_levels = []
    for it in node.get("items") or []:
        if it.get("type") == "group":
            child_levels.append(_level(it))
    return 1 + (max(child_levels) if child_levels else 0)


# ============================================================
# Public API
# ============================================================

def parse_dynamic_group_matching_rules(
    text: str | Sequence[str],
    *,
    include_spans: bool = False,
    nested_simplify: bool = False,
    error_mode: Literal["raise", "report", "ignore"] = "raise",
) -> dict[str, Any] | tuple[dict[str, Any], dict[str, Any]]:
    if isinstance(text, (list, tuple)):
        source_text = "\n".join("" if t is None else str(t) for t in text)
    else:
        source_text = "" if text is None else str(text)

    text_clean = strip_comments_preserve_offsets(source_text)
    validate_ascii(text_clean)

    if text_clean.strip() == "":
        payload = {"schema_version": DG_SCHEMA_VERSION, "rules": []}
        if error_mode == "report":
            return payload, {"errors": [], "error_count": 0}
        return payload

    chunks = split_rules_by_newline_preserving_groups(text_clean)

    out: list[dict[str, Any]] = []
    issues: list[SyntaxIssue] = []

    for chunk in chunks:
        input_stream = InputStream(chunk)
        lexer = DynamicGroupMatchingRuleLexer(input_stream)
        tokens = CommonTokenStream(lexer)
        parser = P(tokens)
        parser.removeErrorListeners()

        if error_mode == "raise":
            parser._errHandler = BailErrorStrategy()
            try:
                rule_ctx = parser.matchingRule()
            except ParseCancellationException as ex:
                tok = getattr(ex, "offendingToken", None)
                if isinstance(tok, Token):
                    raise ValueError(f"syntax error at line {tok.line}, col {tok.column}.") from None
                raise ValueError("syntax error while parsing matching rules.") from None

        elif error_mode == "report":
            listener = CollectingErrorListener(chunk)
            parser.addErrorListener(listener)
            rule_ctx = parser.matchingRule()
            issues.extend(listener.issues)

        else:
            rule_ctx = parser.matchingRule()

        tree = _build_tree(rule_ctx, include_spans=include_spans, source_text=chunk)
        tree2 = simplify_group_tree(tree, collapse_single=True) if nested_simplify else tree
        lvl = _level(tree2)

        rule_obj: dict[str, Any] = {
            "level": lvl,
            "expr": tree2,
        }

        out.append(rule_obj)

    if error_mode == "report":
        diags = {"errors": [asdict(i) for i in issues], "error_count": len(issues)}
        return {"schema_version": DG_SCHEMA_VERSION, "rules": out}, diags

    return {"schema_version": DG_SCHEMA_VERSION, "rules": out}


def parse_dynamic_group_matching_rule(
    text: str, **kwargs: Any
) -> dict[str, Any] | tuple[dict[str, Any], dict[str, Any]]:
    return parse_dynamic_group_matching_rules(text, **kwargs)
