from __future__ import annotations

import re
from typing import Any
from antlr4 import ParserRuleContext, Token

_LINE_COMMENTS = re.compile(r"//[^\r\n]*|#[^\r\n]*")
_BLOCK_C = re.compile(r"/\*.*?\*/", re.DOTALL)

_INVALID_ASCII = re.compile(r"[^\t\r\n\x20-\x7E]")
_NON_CRLF = re.compile(r"[^\r\n]")

STATEMENT_SCHEMA_VERSION = "1.0"
DG_SCHEMA_VERSION = "1.0"


def strip_comments_preserve_offsets(text: str) -> str:
    def repl_line(m: re.Match) -> str:
        return " " * len(m.group(0))

    def repl_block(m: re.Match) -> str:
        return _NON_CRLF.sub(" ", m.group(0))

    text = _LINE_COMMENTS.sub(repl_line, text)
    text = _BLOCK_C.sub(repl_block, text)
    return text


def validate_ascii(text: str) -> None:
    m = _INVALID_ASCII.search(text)
    if m:
        ch = m.group(0)
        i = m.start() + 1
        o = ord(ch)
        raise ValueError(
            f"Invalid character {ch!r} (U+{o:04X}) at position {i}. Only printable ASCII is supported."
        )


def ctx_span(ctx: ParserRuleContext) -> dict[str, int]:
    start: Token = ctx.start
    stop: Token = ctx.stop or ctx.start
    return {
        "start": start.start,
        "stop": stop.stop,
        "line": start.line,
        "column": start.column,
    }


def span_source(text: str, span: dict[str, int]) -> str:
    start = span.get("start", 0)
    stop = span.get("stop", -1)
    if start < 0 or stop < start or start >= len(text):
        return ""
    stop = min(stop, len(text) - 1)
    return text[start : stop + 1]


def split_rules_by_newline_preserving_groups(text: str) -> list[str]:
    """
    Split by newline, but do not split inside braces or single-quoted strings.
    """
    chunks: list[str] = []
    depth = 0
    in_str = False
    esc = False

    start = 0
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == "'":
                in_str = False
            i += 1
            continue

        if ch == "'":
            in_str = True
            i += 1
            continue

        if ch == "{":
            depth += 1
            i += 1
            continue
        if ch == "}":
            depth = max(0, depth - 1)
            i += 1
            continue

        if (ch == "\n" or ch == "\r") and depth == 0:
            chunk = text[start:i].strip()
            if chunk:
                chunks.append(chunk)
            if ch == "\r" and i + 1 < n and text[i + 1] == "\n":
                i += 2
            else:
                i += 1
            start = i
            continue

        i += 1

    tail = text[start:].strip()
    if tail:
        chunks.append(tail)

    return chunks


def simplify_group_tree(node: dict[str, Any], *, collapse_single: bool) -> dict[str, Any]:
    """
    Simplify a nested group tree by flattening same-mode child groups and,
    optionally, collapsing single-child groups.
    """
    if node.get("type") != "group":
        return node

    items: list[dict[str, Any]] = []
    for it in node.get("items") or []:
        if it.get("type") == "group":
            items.append(simplify_group_tree(it, collapse_single=collapse_single))
        else:
            items.append(it)

    node = dict(node)
    node["items"] = items

    if collapse_single and len(node["items"]) == 1 and node["items"][0].get("type") == "group":
        child = dict(node["items"][0])
        # Preserve the parent's span/source_text when collapsing, since the
        # collapsed node now represents the parent expression.
        if "span" in node:
            child["span"] = node["span"]
        if "source_text" in node:
            child["source_text"] = node["source_text"]
        return child

    flattened: list[dict[str, Any]] = []
    for it in node["items"]:
        if it.get("type") == "group" and it.get("mode") == node.get("mode"):
            flattened.extend(it.get("items") or [])
        else:
            flattened.append(it)
    node["items"] = flattened

    if collapse_single and len(node["items"]) == 1 and node["items"][0].get("type") == "group":
        child = dict(node["items"][0])
        if "span" in node:
            child["span"] = node["span"]
        if "source_text" in node:
            child["source_text"] = node["source_text"]
        return child

    return node
