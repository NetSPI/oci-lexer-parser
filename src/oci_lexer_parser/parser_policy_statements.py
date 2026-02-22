from __future__ import annotations

import re
import sys
from bisect import bisect_right
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any, Literal

from antlr4 import CommonTokenStream, InputStream, Token
from antlr4.error.ErrorListener import ErrorListener
from antlr4.error.Errors import ParseCancellationException
from antlr4.error.ErrorStrategy import BailErrorStrategy

from .grammar.gen.PolicyStatementLexer import PolicyStatementLexer
from .grammar.gen.PolicyStatementParser import PolicyStatementParser as P
from .parser_utils import (
    STATEMENT_SCHEMA_VERSION,
    ctx_span,
    simplify_group_tree,
    span_source,
    strip_comments_preserve_offsets,
    validate_ascii,
)

# ============================================================
# Precompiled regexes (hot-path)
# ============================================================

_STMT_START_RE = re.compile(
    r"^\s*(?i:(allow|define|admit|endorse|deny))\b",
    flags=re.MULTILINE,
)

# Comment and ASCII handling live in parser_utils.

TextInput = str | list[str] | tuple[str, ...]


def _normalize_text_input(text: TextInput) -> str:
    """
    Accept either:
      - a single string (existing behavior), or
      - a list/tuple of strings (each entry is a statement or chunk)

    We join with '\n' so:
      - your ^ multiline regex still works,
      - statement starts are still detectable,
      - line numbers remain sane for diagnostics.
    """
    if isinstance(text, str):
        return text
    if isinstance(text, (list, tuple)):
        # Defensive: ensure every entry is a string
        bad = [type(x).__name__ for x in text if not isinstance(x, str)]
        if bad:
            raise TypeError(f"text must be str or list[str]; got non-str entries: {bad}")
        return "\n".join(text)
    raise TypeError(f"text must be str or list[str]; got {type(text).__name__}")

# ============================================================
# Small perf helpers
# ============================================================

_intern = sys.intern


def _ilower(s: str) -> str:
    return _intern(s.lower())


# Comment stripping / ASCII validation are provided by parser_utils.


# ============================================================
# Small utilities
# ============================================================


def _strip_quotes(s: str) -> str:
    return s[1:-1] if len(s) >= 2 and s[0] == s[-1] == "'" else s


def _qname(qn_ctx: Any) -> str:
    left = _strip_quotes(qn_ctx.name(0).getText())
    if qn_ctx.SLASH():
        right = _strip_quotes(qn_ctx.name(1).getText())
        return f"{left}/{right}"
    return left


def _compartment_path(path_ctx: Any) -> list[str]:
    return [_strip_quotes(n.getText()) for n in path_ctx.name()]


def _typed_value(vctx: Any) -> dict[str, Any]:
    t = vctx.getText()
    if getattr(vctx, "QUOTED", None) and vctx.QUOTED():
        return {"type": "literal", "value": _strip_quotes(t)}
    if getattr(vctx, "QUOTED_OCID", None) and vctx.QUOTED_OCID():
        return {"type": "ocid", "value": _strip_quotes(t)}
    if getattr(vctx, "OCID", None) and vctx.OCID():
        return {"type": "ocid", "value": t}
    if getattr(vctx, "PATTERN", None) and vctx.PATTERN():
        return {"type": "regex", "value": t, "pattern": t[1:-1]}
    return {"type": "literal", "value": t}


def _lhs_value(name: str) -> str:
    """Left-hand side attribute name for a condition."""
    return name


def _append(clauses: list[dict[str, Any]], lhs: dict[str, Any], op: str, rhs: dict[str, Any]) -> None:
    clauses.append({"lhs": lhs, "op": op, "rhs": rhs})


_STD_VERBS = frozenset(map(_intern, ("manage", "use", "read", "inspect")))

# ============================================================
# Diagnostics collector
# ============================================================

@dataclass(slots=True)
class SyntaxIssue:
    line: int
    column: int
    message: str
    offending: str | None = None
    expected: list[str] | None = None
    statement_index: int | None = None
    line_text: str | None = None
    caret: str | None = None


class CollectingErrorListener(ErrorListener):
    def __init__(self, source_text: str) -> None:
        super().__init__()
        self.issues: list[SyntaxIssue] = []
        self._source = source_text

        self._lines_keep = source_text.splitlines(keepends=True)

        def _rstrip_crlf(s: str) -> str:
            if s.endswith("\r\n"):
                return s[:-2]
            if s.endswith("\n") or s.endswith("\r"):
                return s[:-1]
            return s

        self._lines = [_rstrip_crlf(ln) for ln in self._lines_keep]

        self._line_offsets: list[int] = [0]
        acc = 0
        for ln in self._lines_keep:
            acc += len(ln)
            self._line_offsets.append(acc)

        # Use comment-stripped text so statement indices aren't skewed by
        # keywords inside comments.
        cleaned = strip_comments_preserve_offsets(source_text)
        self._stmt_starts: list[int] = [m.start() for m in _STMT_START_RE.finditer(cleaned)]

    def syntaxError(
        self,
        recognizer: Any,
        offendingSymbol: Any,
        line: int,
        column: int,
        msg: Any,
        e: Any,
    ) -> None:  # type: ignore[override]
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

        stmt_index = None
        try:
            line_idx = max(0, min(line - 1, len(self._lines)))
            offset = self._line_offsets[line_idx] + max(0, column)
            idx = bisect_right(self._stmt_starts, offset)
            stmt_index = idx if idx > 0 else 1
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
                statement_index=stmt_index,
                line_text=line_text,
                caret=caret,
            )
        )


# Span utility is provided by parser_utils.


# ============================================================
# Condition shaping
# ============================================================


def _condition_clause(cond: Any) -> dict[str, Any]:
    # LHS: typed attribute name (or "?" fallback)
    word = cond.WORD().getText() if hasattr(cond, "WORD") and cond.WORD() else "?"
    lhs = _lhs_value(word)

    # x = y   /   x != y
    if isinstance(cond, P.CondEqContext):
        raw_op = (cond.EQ() or cond.NEQ()).getText()
        op = "eq" if raw_op == "=" else "neq"
        return {"lhs": lhs, "op": op, "rhs": _typed_value(cond.condValue())}

    # x IN (a, b, c)
    if isinstance(cond, P.CondInContext):
        return {
            "lhs": lhs,
            "op": "in",
            "rhs": {"type": "list", "values": [_typed_value(v) for v in cond.condValue()]},
        }

    # x BEFORE t
    if isinstance(cond, P.CondBeforeContext):
        return {"lhs": lhs, "op": "before", "rhs": _typed_value(cond.condValue())}

    # x AFTER t
    if isinstance(cond, P.CondAfterContext):
        return {"lhs": lhs, "op": "after", "rhs": _typed_value(cond.condValue())}

    # x BETWEEN a AND b
    if isinstance(cond, P.CondBetweenContext):
        a, b = cond.condValue()
        return {
            "lhs": lhs,
            "op": "between",
            "rhs": {"type": "range", "from": _typed_value(a), "to": _typed_value(b)},
        }

    # Fallback unknown condition
    return {"lhs": _lhs_value("?"), "op": "unknown", "rhs": {"type": "literal", "value": "?"}}


def _cond_node(ctx: Any) -> dict[str, Any]:
    # conditionExpr can be either a group or a single condition
    group_ctx = getattr(ctx, "conditionGroup", None)
    if callable(group_ctx):
        g = group_ctx()
        if g is not None:
            mode = "any" if g.ANY() else "all"
            items = [_cond_node(c) for c in g.conditionExpr()]
            return {"type": "group", "mode": mode, "items": items}

    cond = ctx.condition() if hasattr(ctx, "condition") else None
    if cond is not None:
        return {"type": "clause", "clause": _condition_clause(cond)}

    # Defensive fallback
    return {"type": "clause", "clause": _condition_clause(ctx)}


def _simplify_cond(node: dict[str, Any]) -> dict[str, Any]:
    return simplify_group_tree(node, collapse_single=False)


def _cond_expr_to_output(node: dict[str, Any]) -> dict[str, Any]:
    # Always return a group/clause tree (mirrors dynamic-group expr shape)
    def _to_expr(n: dict[str, Any]) -> dict[str, Any]:
        if n.get("type") == "clause":
            clause = n["clause"]
            return {
                "type": "clause",
                "node": {"lhs": clause["lhs"], "op": clause["op"], "rhs": clause["rhs"]},
            }
        return {
            "type": "group",
            "mode": n.get("mode", "all"),
            "items": [_to_expr(i) for i in n.get("items", [])],
        }

    expr = _to_expr(node)
    if expr.get("type") == "group":
        return expr
    # wrap single clause in a default ALL group for a consistent shape
    return {"type": "group", "mode": "all", "items": [expr]}


def _conditions(ctx_with_cond: Any, *, nested_simplify: bool) -> dict[str, Any] | None:
    c = ctx_with_cond.conditionExpr()
    if not c:
        return None

    tree = _cond_node(c)
    if nested_simplify:
        tree = _simplify_cond(tree)
    return _cond_expr_to_output(tree)


# ============================================================
# Subject shaping
# ============================================================


def _subject_node(sctx: Any) -> dict[str, Any]:
    if isinstance(sctx, P.AnyGroupContext):
        return {"type": "any-group", "values": []}
    if isinstance(sctx, P.AnyUserContext):
        return {"type": "any-user", "values": []}
    if isinstance(sctx, P.ServiceSubjectContext):
        names = [_strip_quotes(q.getText()) for q in sctx.nameList().qualifiedName()]
        return {"type": "service", "values": names}
    if isinstance(sctx, P.GroupByNameContext):
        vals = [_qname(qn) for qn in sctx.nameList().qualifiedName()]
        return {"type": "group", "values": vals}
    if isinstance(sctx, P.GroupByIdContext):
        ocids = [_strip_quotes(o.getText()) for o in sctx.idList().ocid()]
        return {"type": "group-id", "values": ocids}
    if isinstance(sctx, P.DynGroupByNameContext):
        vals = [_qname(qn) for qn in sctx.nameList().qualifiedName()]
        return {"type": "dynamic-group", "values": vals}
    if isinstance(sctx, P.DynGroupByIdContext):
        ocids = [_strip_quotes(o.getText()) for o in sctx.idList().ocid()]
        return {"type": "dynamic-group-id", "values": ocids}
    return {"type": "unknown", "values": []}


def _subject_from_stmt(stmt_ctx: Any) -> dict[str, Any]:
    get_single = getattr(stmt_ctx, "subject", None)
    if get_single:
        single_ctx = get_single()
        if single_ctx:
            return _subject_node(single_ctx)
    return {"type": "unknown", "values": []}

def _normalize_subject_values(
    stmts: list[dict[str, Any]],
    default_identity_domain: str | None,
) -> None:
    """
    V1 subject normalization.

    Transform subject.values from raw strings:
        ["DomA/User1", "User2", ...]
    into structured value objects:
        [
          { "label": "User1", "identity_domain": "DomA" },
          { "label": "User2" },  # domain may come from default_identity_domain
        ]

    Rules:
      - For subject.type in {"group", "dynamic-group"}:
          * If value looks like "Dom/Name", split on first "/" and treat "Dom" as
            identity_domain and "Name" as the principal label.
          * If there is no explicit prefix and 'default_identity_domain' is provided,
            attach that identity domain.
      - For subject.type in {"group-id", "dynamic-group-id"}:
          * Values are treated as OCIDs. We still store them under "label" so that
            downstream code only has to look at "label" plus subject.type.
      - For subject.type == "service":
          * Values are treated as service names, stored in "label".
      - For "any-user" / "any-group":
          * Values list is typically empty; we leave it as-is.

    This mutates 'stmts' in place, *after* DEFINE substitutions so that lookups
    still see the original string values.
    """
    if not isinstance(stmts, list):
        return

    for st in stmts:
        sub = st.get("subject")
        if not isinstance(sub, dict):
            continue

        stype = sub.get("type")
        vals = sub.get("values")
        if not isinstance(vals, list) or not vals:
            continue

        new_vals: list[dict[str, Any]] = []

        for v in vals:
            # If someone already gave us structured values, don't break them.
            if isinstance(v, dict):
                new_vals.append(v)
                continue

            if not isinstance(v, str):
                # Fallback: keep as-is in a minimal wrapper.
                new_vals.append({"label": str(v)})
                continue

            dom: str | None = None
            label = v

            if stype in ("group", "dynamic-group"):
                # Try explicit Domain/Name pattern first
                if "/" in v:
                    dom_candidate, rest = v.split("/", 1)
                    if dom_candidate and rest:
                        dom = _intern(dom_candidate)
                        label = rest
                # If no explicit prefix, use global default identity domain if provided
                if dom is None and default_identity_domain:
                    dom = _intern(default_identity_domain)

            elif stype in ("group-id", "dynamic-group-id"):
                # OCIDs; we still store as "label"
                label = v

            elif stype == "service":
                # Service names; treated as labels.
                label = v

            else:
                # any-user / any-group (values usually empty) or unknown types
                label = v

            val_obj: dict[str, Any] = {"label": label}
            if dom is not None:
                val_obj["identity_domain"] = dom

            new_vals.append(val_obj)

        sub["values"] = new_vals

# ============================================================
# Verb/resource/location shaping
# ============================================================


def _verb_chunks_from_ctx(vctx: Any) -> list[dict[str, Any]]:
    """
    Turn a single 'verb' parser context into 1..N normalized action chunks.

    - Standard verbs (manage/use/read/inspect) -> [{"type": "verbs", "values": ["manage"]}]
    - Service-defined single WORD (e.g. KEY_READ) -> [{"type": "permissions", "values": ["key_read"]}]
    - {WORD, WORD, ...} -> [{"type": "permissions", "values": ["key_read","key_write",...]}]
    """
    # Braced list: {A,B,C} -> one "permissions" chunk with multiple values
    if getattr(vctx, "LBRACE", None) and vctx.LBRACE():
        nodes = vctx.WORD()
        if isinstance(nodes, list):
            words = [n.getText() for n in nodes]
        elif nodes is not None:
            words = [nodes.getText()]
        else:
            words = []
        values = [_ilower(w) for w in words if w]
        if not values:
            return [{"type": "unknown", "values": []}]
        return [{"type": "permissions", "values": values}]

    # Single WORD: either a standard verb or a service-defined permission
    text = vctx.getText()
    if not text:
        return [{"type": "unknown", "values": []}]
    low = _ilower(text)
    if low in _STD_VERBS:
        return [{"type": "verbs", "values": [low]}]
    if not low:
        return [{"type": "unknown", "values": []}]
    return [{"type": "permissions", "values": [low]}]


def _actions_from_stmt(stmt_ctx: Any) -> dict[str, Any]:
    get_single = getattr(stmt_ctx, "verb", None)
    if get_single:
        vctx = get_single()
        if vctx:
            chunks = _verb_chunks_from_ctx(vctx)
            if chunks:
                return chunks[0]
    return {"type": "unknown", "values": []}


def _resource_node(rctx: Any) -> dict[str, Any]:
    tok = rctx.getText()
    if not tok:
        return {"type": "unknown", "values": []}
    if _ilower(tok) == "all-resources":
        return {"type": "all-resources", "values": []}
    return {"type": "specific", "values": [tok]}


def _resource_from_stmt(stmt_ctx: Any) -> dict[str, Any]:
    get_single = getattr(stmt_ctx, "resource", None)
    if get_single:
        rctx = get_single()
        if rctx:
            return _resource_node(rctx)
    return {"type": "unknown", "values": []}


def _location_node(lctx: Any) -> dict[str, Any]:
    if isinstance(lctx, P.LocTenancyContext):
        return {"type": "tenancy", "values": []}
    if isinstance(lctx, P.LocCompartmentIdContext):
        return {"type": "compartment-id", "values": [_strip_quotes(lctx.ocid().getText())]}
    names = _compartment_path(lctx.compartmentPath())
    if len(names) == 1:
        return {"type": "compartment_name", "values": names}
    return {"type": "compartment-path", "values": names}


def _location_from_stmt(stmt_ctx: Any) -> dict[str, Any]:
    get_single = getattr(stmt_ctx, "location", None)
    if get_single:
        lctx = get_single()
        if lctx:
            return _location_node(lctx)
    # No explicit location present (likely due to syntax error/recovery)
    return {"type": "unknown", "values": []}


# ============================================================
# Statement shapers
# ============================================================


def _allow(
    ctx: P.AllowStmtContext,
    include_spans: bool,
    *,
    nested_simplify: bool,
    source_text: str | None,
) -> dict[str, Any]:
    eff = _ilower(ctx.effect().getText())  # "allow" or "deny"

    out: dict[str, Any] = {
        "kind": eff,  # "allow" or "deny"
        "subject": _subject_from_stmt(ctx),
        "actions": _actions_from_stmt(ctx),
        "resources": _resource_from_stmt(ctx),
        "location": _location_from_stmt(ctx),
    }

    cond = _conditions(ctx, nested_simplify=nested_simplify)
    if cond:
        out["conditions"] = cond
    if include_spans:
        out["span"] = ctx_span(ctx)
        if source_text is not None:
            out["source_text"] = span_source(source_text, out["span"])
    return out



def _define(ctx: P.DefineStmtContext, include_spans: bool, *, source_text: str | None) -> dict[str, Any]:
    # Build the define 'symbol' (typed alias) and its 'def' (typed value, usually ocid)
    tgt = ctx.defineTarget()
    if tgt.TENANCY():
        symbol = {"type": "tenancy", "name": _strip_quotes(tgt.name().getText())}
    elif tgt.GROUP():
        symbol = {"type": "group", "name": _qname(tgt.qualifiedName())}
    elif tgt.DYNAMIC_GROUP():
        symbol = {"type": "dynamic-group", "name": _qname(tgt.qualifiedName())}
    else:
        symbol = {"type": "compartment", "name": _strip_quotes(tgt.name().getText())}

    ocid_text = _strip_quotes(ctx.ocid().getText())
    node = {
        "kind": "define",
        "symbol": symbol,
        "def": {"type": "ocid", "value": ocid_text},
    }
    if include_spans:
        node["span"] = ctx_span(ctx)
        if source_text is not None:
            node["source_text"] = span_source(source_text, node["span"])
    return node


def _target_node(es: Any) -> dict[str, Any]:
    # Normalize ENDORSE target to typed shape
    if es.ANY_TENANCY():
        return {"type": "any-tenancy", "values": []}
    return {"type": "tenancy", "values": [_strip_quotes(es.name().getText())]}


def _target_from_stmt(stmt_ctx: Any) -> dict[str, Any]:
    get_single = getattr(stmt_ctx, "endorseScope", None)
    if get_single:
        tctx = get_single()
        if tctx:
            return _target_node(tctx)
    return {"type": "unknown", "values": []}


def _endorse_actions_from_ctx(evctx: Any) -> dict[str, Any]:
    # ASSOCIATE is treated as a standard high-level verb for endorse
    if evctx.ASSOCIATE():
        return {"type": "verbs", "values": ["associate"]}
    vctx = evctx.verb()
    chunks = _verb_chunks_from_ctx(vctx)
    return chunks[0] if chunks else {"type": "verbs", "values": []}


def _endorse(
    ctx: P.EndorseStmtContext,
    include_spans: bool,
    *,
    nested_simplify: bool,
    source_text: str | None,
) -> dict[str, Any]:
    denym = getattr(ctx, "DENY", None)
    is_deny = bool(denym()) if callable(denym) else False
    kind = "deny_endorse" if is_deny else "endorse"

    targets = _target_from_stmt(ctx)
    actions = _endorse_actions_from_ctx(ctx.endorseVerb())

    out: dict[str, Any] = {
        "kind": kind,
        "subject": _subject_from_stmt(ctx),
        "target": targets,
        "actions": actions,
        "resources": _resource_from_stmt(ctx),
    }

    cond = _conditions(ctx, nested_simplify=nested_simplify)
    if cond:
        out["conditions"] = cond

    if include_spans:
        out["span"] = ctx_span(ctx)
        if source_text is not None:
            out["source_text"] = span_source(source_text, out["span"])

    return out



def _admit(
    ctx: P.AdmitStmtContext,
    include_spans: bool,
    *,
    nested_simplify: bool,
    source_text: str | None,
) -> dict[str, Any]:
    denym = getattr(ctx, "DENY", None)
    is_deny = bool(denym()) if callable(denym) else False
    kind = "deny_admit" if is_deny else "admit"

    source_tenancy = _strip_quotes(ctx.name().getText()) if ctx.OF() else None

    out: dict[str, Any] = {
        "kind": kind,
        "subject": _subject_from_stmt(ctx),
        "actions": _actions_from_stmt(ctx),
        "resources": _resource_from_stmt(ctx),
        "location": _location_from_stmt(ctx),
    }

    if source_tenancy:
        out["source"] = {"type": "tenancy", "values": [source_tenancy]}

    cond = _conditions(ctx, nested_simplify=nested_simplify)
    if cond:
        out["conditions"] = cond

    if include_spans:
        out["span"] = ctx_span(ctx)
        if source_text is not None:
            out["source_text"] = span_source(source_text, out["span"])

    return out



# ============================================================
# DEFINE symbols & substitution
# ============================================================


def build_symbols(
    stmts: list[dict[str, Any]],
    *,
    form: Literal["flat", "nested"] = "flat",
) -> dict[Any, Any]:
    # Build mapping: (type, name) -> ocid  from define statements using new shape
    triples = (
        (sym.get("type"), sym.get("name"), (defn or {}).get("value"))
        for st in stmts
        if st.get("kind") == "define"
        for sym in (st.get("symbol", {}),)
        for defn in (st.get("def", {}),)
        if isinstance(sym.get("name"), str) and sym.get("name")
    )

    if form == "flat":
        return {(t, name): oc for (t, name, oc) in triples}

    out: dict[str, dict[str, str]] = {}
    for t, name, oc in triples:
        out.setdefault(t, {})[name] = oc
    return out


def _apply_define_subs(stmts: list[dict[str, Any]], sym: dict[tuple[str, str], str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    for st in stmts:
        if st.get("kind") == "define":
            out.append(st)
            continue

        s = st
        modified = False

        # subjects: group/dynamic-group -> *-id if all names resolve
        sub = st.get("subject")
        if isinstance(sub, dict):
            t = sub.get("type")
            vals = sub.get("values") or []
            if t in ("group", "dynamic-group") and isinstance(vals, list) and vals:
                ocids = [sym.get((t, name)) for name in vals]
                if all(ocids):
                    if not modified:
                        s, modified = dict(st), True
                        sub = s.get("subject")
                    if isinstance(sub, dict):
                        sub["type"] = f"{t}-id"
                        sub["values"] = ocids

        # admit: replace source tenancy alias -> tenancy_id
        if s.get("kind") in ("admit", "deny_admit"):
            src_val = s.get("source")
            if isinstance(src_val, dict) and src_val.get("type") == "tenancy":
                vals = src_val.get("values") or []
                if isinstance(vals, list) and len(vals) == 1:
                    ten = vals[0]
                    oc = sym.get(("tenancy", ten))
                    if oc:
                        if not modified:
                            s, modified = dict(st), True
                            src_val = s.get("source")
                        if isinstance(src_val, dict):
                            src_val["type"] = "tenancy_id"
                            src_val["values"] = [oc]

        # endorse: replace targets tenancy alias -> tenancy_id
        if s.get("kind") in ("endorse", "deny_endorse"):
            tgt_val = s.get("target")
            if isinstance(tgt_val, dict) and tgt_val.get("type") == "tenancy":
                vals = tgt_val.get("values") or []
                if isinstance(vals, list) and len(vals) == 1:
                    ten = vals[0]
                    oc = sym.get(("tenancy", ten))
                    if oc:
                        if not modified:
                            s, modified = dict(st), True
                            tgt_val = s.get("target")
                        if isinstance(tgt_val, dict):
                            tgt_val["type"] = "tenancy_id"
                            tgt_val["values"] = [oc]

        # location: single-name compartment -> compartment-id if resolvable
        loc = s.get("location")
        if isinstance(loc, dict) and loc.get("type") == "compartment_name":
            vals = loc.get("values") or []
            if isinstance(vals, list) and len(vals) == 1:
                oc = sym.get(("compartment", vals[0]))
                if oc:
                    if not modified:
                        s, modified = dict(st), True
                        loc = s.get("location")
                    if isinstance(loc, dict):
                        loc["type"] = "compartment-id"
                        loc["values"] = [oc]

        out.append(s)

    return out


# ============================================================
# Optional default tenancy-alias injection for "IN TENANCY"
# ============================================================

def _inject_default_tenancy_alias_in_location(stmts: list[dict[str, Any]], alias: str) -> None:
    """
    For locations that are exactly {"type":"tenancy","values":[]}, set values to [alias].
    Mutates the statements list in place. No effect on ADMIT 'OF TENANCY' or ENDORSE targets.
    """
    if not alias:
        return
    for st in stmts:
        loc = st.get("location")
        if isinstance(loc, dict) and loc.get("type") == "tenancy":
            vals = loc.get("values")
            if isinstance(vals, list) and not vals:
                loc["values"] = [alias]


# ============================================================
# Public API
# ============================================================


def parse_policy_statements(
    text: TextInput,
    define_subs: bool = False,
    return_filter: Iterable[str] | dict[str, Any] | str | None = None,
    *,
    include_spans: bool = False,
    nested_simplify: bool = False,
    error_mode: Literal["raise", "report", "ignore"] = "raise",
    default_tenancy_alias: str | None = None,
    default_identity_domain: str | None = None,
) -> dict[str, Any] | tuple[dict[str, Any], dict[str, Any]]:
    """
    Parse one or more statements and return a payload with schema_version + statements.

    Notes:
        - `subject`, `actions`, `resources`, `location`, and `target` are always single dicts.

    default_tenancy_alias:
      When provided, and a statement's location is 'IN TENANCY', we place this alias
      as the sole element of that location's 'values' list.

    nested_simplify:
      When True, same-mode nested condition groups (ANY within ANY, ALL within ALL)
      are flattened. When False (default), the original nesting is preserved.

    default_identity_domain:
      Optional current identity domain. After parsing and DEFINE substitutions, each
      subject's 'values' list is normalized to a list of objects with fields like:
        { "label": "...", "identity_domain": "Dom" (optional) }.
      If a subject value is written as 'Domain/Name', we split it and set
      identity_domain to 'Domain' and label to 'Name'. If no explicit prefix is
      present and this argument is provided, we attach that identity domain for
      group/dynamic-group subjects.
    """
    # NEW: normalize here
    text = _normalize_text_input(text)

    # 1) Preprocess (preserve positions), then validate ASCII
    text_clean = strip_comments_preserve_offsets(text)
    validate_ascii(text_clean)

    # If nothing remains, succeed with empty payload
    if text_clean.strip() == "":
        payload = {"schema_version": STATEMENT_SCHEMA_VERSION, "statements": []}
        if error_mode == "report":
            return payload, {"errors": [], "error_count": 0}
        return payload

    # 2) ANTLR pipeline
    input_stream = InputStream(text_clean)
    lexer = PolicyStatementLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = P(tokens)
    parser.removeErrorListeners()

    listener: CollectingErrorListener | None = None

    if error_mode == "raise":
        parser._errHandler = BailErrorStrategy()
        try:
            doc = parser.statements()
        except ParseCancellationException as ex:
            tok = getattr(ex, "offendingToken", None)
            if isinstance(tok, Token):
                raise ValueError(f"syntax error at line {tok.line}, col {tok.column}.") from None
            raise ValueError("syntax error while parsing.") from None
        issues: list[SyntaxIssue] = []

    elif error_mode == "report":
        listener = CollectingErrorListener(text)
        parser.addErrorListener(listener)
        doc = parser.statements()
        issues = listener.issues

    else:
        doc = parser.statements()
        issues = []

    # 3) Shape
    out: list[dict[str, Any]] = []
    for st in doc.statement():
        a = st.allowStmt()
        if a:
            out.append(
                _allow(
                    a,
                    include_spans,
                    nested_simplify=nested_simplify,
                    source_text=text_clean,
                )
            )
            continue
        d = st.defineStmt()
        if d:
            out.append(_define(d, include_spans, source_text=text_clean))
            continue
        m = st.admitStmt()
        if m:
            out.append(
                _admit(
                    m,
                    include_spans,
                    nested_simplify=nested_simplify,
                    source_text=text_clean,
                )
            )
            continue
        e = st.endorseStmt()
        if e:
            out.append(
                _endorse(
                    e,
                    include_spans,
                    nested_simplify=nested_simplify,
                    source_text=text_clean,
                )
            )
            continue
        node: dict[str, Any] = {"kind": "unknown"}
        if include_spans:
            node["span"] = ctx_span(st)
            node["source_text"] = span_source(text_clean, node["span"])
        out.append(node)

    # 4) DEFINE subs (if any)
    if define_subs:
        sym = build_symbols(out, form="flat")
        if sym:
            out = _apply_define_subs(out, sym)

    # 5) Inject default tenancy alias into location "IN TENANCY" if requested
    if default_tenancy_alias:
        _inject_default_tenancy_alias_in_location(out, default_tenancy_alias)

    # 5b) V1 subject normalization: turn subject.values into structured objects
    _normalize_subject_values(out, default_identity_domain)

    # 6) Filter / project
    if return_filter is not None:
        allowed_kinds: set[str] | None = None
        fields: set[str] | None = None
        first_only = False

        if isinstance(return_filter, str):
            allowed_kinds = {return_filter.lower()}
        elif isinstance(return_filter, (list, set, tuple)):
            allowed_kinds = {str(x).lower() for x in return_filter}
        elif isinstance(return_filter, dict):
            kinds = return_filter.get("kinds")
            if kinds is not None:
                allowed_kinds = {str(x).lower() for x in kinds}
            f = return_filter.get("fields")
            if f is not None:
                fields = set(f)
                fields.add("kind")
            first_only = bool(return_filter.get("first_only", False))

        if allowed_kinds is not None:
            out = [s for s in out if s.get("kind") in allowed_kinds]
        if fields is not None:
            out = [{k: v for k, v in s.items() if k in fields} for s in out]
        if first_only and out:
            out = [out[0]]

    payload = {"schema_version": STATEMENT_SCHEMA_VERSION, "statements": out}

    # 7) Diagnostics for "report"
    if error_mode == "report":
        diags = {"errors": [asdict(i) for i in issues], "error_count": len(issues)}
        return payload, diags

    return payload


def parse_policy_statement(
    text: TextInput, **kwargs: Any
) -> dict[str, Any] | tuple[dict[str, Any], dict[str, Any]]:
    return parse_policy_statements(text, **kwargs)
