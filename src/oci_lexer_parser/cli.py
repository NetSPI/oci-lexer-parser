from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Iterator
from contextlib import nullcontext
from typing import Any, Literal, cast

# Version reporting (stdlib preferred; fall back to backport)
try:  # Prefer stdlib
    import importlib.metadata as importlib_metadata  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    import importlib_metadata  # type: ignore[import-not-found]

from .parser_dynamic_group_matching_rules import parse_dynamic_group_matching_rules
from .parser_policy_statements import build_symbols, parse_policy_statements
from .parser_utils import DG_SCHEMA_VERSION, STATEMENT_SCHEMA_VERSION

try:  # pragma: no cover
    _VERSION = importlib_metadata.version("oci-lexer-parser")
except importlib_metadata.PackageNotFoundError:  # pragma: no cover
    _VERSION = "unknown"

# Match statement starters at the beginning of a line (case-insensitive).
# Now includes DENY as a starter as well.
START_RE = re.compile(r"^\s*(allow|define|admit|endorse|deny)\b", re.IGNORECASE)
DEFINE_START_RE = re.compile(r"^\s*define\b", re.IGNORECASE)


Statements = list[dict[str, Any]]
Diagnostics = dict[str, Any]
Payload = dict[str, Any]
ParseResult = Payload | tuple[Payload, Diagnostics]
ErrorMode = Literal["raise", "report", "ignore"]


# --------------------------
# Chunking
# --------------------------
def chunk_lines(
    lines: Iterable[str],
    *,
    strip_bom_first_line: bool = False,
) -> Iterator[str]:
    """
    Split an iterable of lines into statement-sized chunks.

    - Preamble (comments/blank lines before the first statement) is not emitted.
    - Newlines are preserved (avoid span drift).
    - If reading from stdin (where you can't set encoding='utf-8-sig'),
      set strip_bom_first_line=True to drop any leading U+FEFF.
    """
    first = True
    buf: list[str] = []
    seen_stmt = False

    for ln in lines:
        if first:
            if strip_bom_first_line and ln.startswith("\ufeff"):
                ln = ln.lstrip("\ufeff")
            first = False

        # Cheap first-character guard before regex (massive inputs)
        s = ln.lstrip()
        if s:
            c0 = s[0].lower()
            if c0 not in ("a", "d", "e"):  # allow/define/admit/endorse/deny
                buf.append(ln)
                continue

        if START_RE.match(ln):
            if seen_stmt and buf:
                # Emit the previous statement chunk (don’t emit preamble)
                yield "".join(buf)
            buf = [ln]
            seen_stmt = True
        else:
            buf.append(ln)

    if seen_stmt and buf:
        # Emit the final statement chunk only if we saw at least one statement
        yield "".join(buf)


# --------------------------
# JSON helpers
# --------------------------
def _json_dumps(obj: Any, pretty: bool) -> str:
    if pretty:
        return json.dumps(obj, indent=2, ensure_ascii=True)
    # Compact output for speed/smaller size
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=True)


def _emit_jsonl(stmts: Statements, pretty: bool) -> None:
    write = sys.stdout.write
    dump = _json_dumps
    for st in stmts:
        write(dump(st, pretty) + "\n")


# --------------------------
# Parsing helpers
# --------------------------
def _parse_one_chunk(
    chunk: str,
    *,
    define_subs: bool,
    error_mode: str,
    include_spans: bool,
    default_tenancy_alias: str | None,
    default_identity_domain: str | None,
    return_filter: Iterable[str] | None = None,
) -> tuple[Statements, Diagnostics | None, int]:
    """
    Normalize the parse result across error modes.
    Returns (statements, diagnostics_or_none, error_count_int).
    """
    # Avoid re-allocations for sets passed in:
    if return_filter is None:
        ret_filter: set[str] | None = None
    elif isinstance(return_filter, set):
        ret_filter = return_filter
    else:
        ret_filter = set(return_filter)

    error_mode_lit = cast(Literal["raise", "report", "ignore"], error_mode)

    res: ParseResult = parse_policy_statements(
        chunk,
        define_subs=define_subs,
        error_mode=error_mode_lit,
        include_spans=include_spans,
        default_tenancy_alias=default_tenancy_alias,
        default_identity_domain=default_identity_domain,
        return_filter=ret_filter,
    )

    if isinstance(res, tuple):
        payload, diags = res
        stmts = payload.get("statements", [])
        err = int((diags or {}).get("error_count", 0) or 0)
        return stmts, diags, err

    stmts = res.get("statements", [])
    return stmts, None, 0


def _parse_and_emit_chunks(
    chunks: Iterable[str],
    *,
    jsonl: bool,
    pretty: bool,
    define_subs: bool,
    error_mode: str,
    include_spans: bool,
    default_tenancy_alias: str | None,
    default_identity_domain: str | None,
    symbols_only: bool,
) -> tuple[Statements, Statements, int, list[dict[str, Any]] | None]:
    """
    Parse a sequence of chunks, optionally emit JSONL as we go,
    and optionally accumulate statements.

    Simplified mode matrix:
      - symbols_only=True  => skip non-DEFINE chunks, parser returns only DEFINEs,
                              accumulate only DEFINEs, and print symbol table later.
      - symbols_only=False => parse everything; optionally emit JSONL.

    Returns (all_statements, define_statements, total_error_count).
    """
    all_stmts: Statements = []
    define_stmts: Statements = []
    total_errors = 0
    error_items: list[dict[str, Any]] | None = [] if error_mode == "report" else None

    # When symbols_only, tell parser to only return DEFINEs and skip non-DEFINE chunks upfront
    ret_filter = {"define"} if symbols_only else None

    for chunk in chunks:
        if symbols_only and not DEFINE_START_RE.match(chunk):
            # Skip parsing non-DEFINE chunks entirely for speed.
            continue

        stmts, diags, err = _parse_one_chunk(
            chunk,
            define_subs=define_subs,
            error_mode=error_mode,
            include_spans=include_spans,
            default_tenancy_alias=default_tenancy_alias,
            default_identity_domain=default_identity_domain,
            return_filter=ret_filter,
        )
        total_errors += err
        if error_items is not None and diags:
            errors = diags.get("errors")
            if isinstance(errors, list):
                error_items.extend(errors)

        if jsonl and not symbols_only:
            _emit_jsonl(stmts, pretty)

        if symbols_only:
            # Parser already projected to DEFINEs only
            define_stmts.extend(stmts)
        else:
            define_stmts.extend(s for s in stmts if s.get("kind") == "define")

        # In non-symbols mode, you may also want the full array if not jsonl:
        if not symbols_only and not jsonl:
            all_stmts.extend(stmts)

    return all_stmts, define_stmts, total_errors, error_items


# --------------------------
# IO helpers
# --------------------------
def _read_source_from_file_or_stdin(path: str | None) -> str:
    """
    Read entire input into memory (stdin if path is None or '-').
    Use 'utf-8-sig' to be robust against BOM at start of file.
    """
    if path and path != "-":
        with open(path, encoding="utf-8-sig", newline="") as fh:
            return fh.read()
    return sys.stdin.read()


# --------------------------
# Small utility helpers (for simpler main)
# --------------------------
def _open_input_ctx(file_arg: str | None):
    """Return (context-manager, strip_bom_first_line_flag)."""
    use_file = bool(file_arg and file_arg != "-")
    if use_file:
        # BOM handled by codec; we do NOT strip in chunk_lines
        return open(file_arg, encoding="utf-8-sig", newline=""), False
    # stdin is already a text stream; allow chunk_lines to strip BOM only once
    return nullcontext(sys.stdin), True


def _write_diagnostics_file(path: str | None, payload: dict) -> None:
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as df:
            df.write(_json_dumps(payload, pretty=True))
    except OSError as e:  # pragma: no cover
        sys.stderr.write(f"Failed to write diagnostics file: {e}\n")


def _exit_code_for_errors(mode: ErrorMode, error_count: int) -> int:
    # - raise: we never get here on parse errors (it already raised)
    # - report: exit 1 if any errors
    # - ignore: always 0
    return 1 if (mode == "report" and error_count) else 0


def _emit_symbols_from_defines(stmts: list[dict], pretty: bool) -> int:
    # Read DEFINE as {"symbol": {...}, "def": {"type":"ocid","value":"..."}}
    print(_json_dumps(build_symbols(stmts, form="nested"), pretty))
    return 0


def _emit_statements_jsonl_or_array(
    *,
    stmts: list[dict],
    diags: dict | None,
    jsonl: bool,
    pretty: bool,
    schema_version: str,
) -> None:
    if jsonl:
        _emit_jsonl(stmts, pretty)
    else:
        payload: dict[str, Any] = {"schema_version": schema_version, "statements": stmts}
        if diags is not None:
            payload["diagnostics"] = diags
        print(_json_dumps(payload, pretty))


def _emit_rules_jsonl_or_array(
    *,
    rules: list[dict],
    diags: dict | None,
    jsonl: bool,
    pretty: bool,
    schema_version: str,
) -> None:
    if jsonl:
        _emit_jsonl(rules, pretty)
    else:
        payload: dict[str, Any] = {"schema_version": schema_version, "rules": rules}
        if diags is not None:
            payload["diagnostics"] = diags
        print(_json_dumps(payload, pretty))


# --------------------------
# CLI
# --------------------------
def main() -> int:
    ap = argparse.ArgumentParser("oci-lexer-parse", description="Parse OCI IAM policy statements to JSON.")
    ap.add_argument("file", nargs="?", help="Policy file; if omitted or '-', reads from stdin.")

    ap.add_argument("--define-subs", action="store_true", help="Resolve DEFINE aliases where possible.")
    ap.add_argument(
        "--default-tenancy-alias",
        metavar="NAME",
        help="When a statement says 'IN TENANCY', place NAME into that location's values (e.g., for organization).",
    )
    ap.add_argument(
        "--default-identity-domain",
        metavar="NAME",
        help=(
            "Default identity domain for group/dynamic-group subjects "
            "that do not have an explicit 'Domain/Name' prefix. "
            "Subject values will then include an 'identity_domain' field."
        ),
    )
    ap.add_argument(
        "--error-mode",
        choices=["raise", "report", "ignore"],
        default="report",
        help=(
            "Syntax error handling mode. "
            "'raise' = stop at first error with nonzero exit; "
            "'report' = include diagnostics JSON and exit 1 if any errors; "
            "'ignore' = suppress diagnostics and always exit 0."
        ),
    )
    ap.add_argument(
        "--include-spans",
        action="store_true",
        help="Include source spans per statement or rule.",
    )
    ap.add_argument(
        "--dynamic-group",
        "--dg",
        action="store_true",
        help="Parse OCI dynamic group matching rules instead of policy statements.",
    )
    ap.add_argument(
        "--policy",
        action="store_true",
        help="Explicitly parse policy statements (default mode).",
    )
    ap.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    ap.add_argument("--jsonl", action="store_true", help="Emit one JSON object per line (statement or rule).")
    ap.add_argument(
        "--chunked",
        action="store_true",
        help=(
            "Chunk input by statement starters to handle huge files. "
            "With --error-mode raise, stops at the first failing chunk."
        ),
    )
    ap.add_argument("--symbols", action="store_true", help="Print symbol table (from DEFINE) and exit.")
    ap.add_argument("--diagnostics-file", help="If set, write diagnostics JSON to this path.")
    ap.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"oci-lexer-parse {_VERSION}",
        help="Show version and exit.",
    )
    args = ap.parse_args()

    symbols_only = bool(args.symbols)
    error_mode: ErrorMode = cast(ErrorMode, args.error_mode)
    default_identity_domain = args.default_identity_domain
    default_tenancy_alias = args.default_tenancy_alias
    dynamic_group_mode = bool(args.dynamic_group)
    policy_mode = bool(args.policy)
    if dynamic_group_mode and policy_mode:
        sys.stderr.write("Choose only one of --dynamic-group or --policy.\n")
        return 2

    # === DYNAMIC GROUP PATH ===
    if dynamic_group_mode:
        if args.chunked:
            sys.stderr.write("--chunked is not supported with --dynamic-group.\n")
            return 2
        if symbols_only:
            sys.stderr.write("--symbols is not supported with --dynamic-group.\n")
            return 2

        source = _read_source_from_file_or_stdin(args.file)
        res = parse_dynamic_group_matching_rules(
            source,
            error_mode=error_mode,
            include_spans=args.include_spans,
        )

        if isinstance(res, tuple):
            payload, diags = res
            rules = payload.get("rules", [])
            _emit_rules_jsonl_or_array(
                rules=rules,
                diags=diags,
                jsonl=args.jsonl,
                pretty=args.pretty,
                schema_version=DG_SCHEMA_VERSION,
            )
            _write_diagnostics_file(args.diagnostics_file, diags)

            errors = int((diags or {}).get("error_count", 0) or 0)
            if error_mode == "report" and errors:
                sys.stderr.write(f"{errors} syntax error(s) detected\n")
            return _exit_code_for_errors(error_mode, errors)

        # res is a payload (ignore mode or raise with no errors)
        _emit_rules_jsonl_or_array(
            rules=res.get("rules", []),
            diags=None,
            jsonl=args.jsonl,
            pretty=args.pretty,
            schema_version=DG_SCHEMA_VERSION,
        )
        return 0

    # === CHUNKED PATH (POLICY) ===
    if args.chunked:
        ctx, strip_first = _open_input_ctx(args.file)
        with ctx as fh:
            chunks = chunk_lines(fh, strip_bom_first_line=strip_first)
            all_stmts, define_stmts, total_errors, error_items = _parse_and_emit_chunks(
                chunks,
                jsonl=args.jsonl,
                pretty=args.pretty,
                define_subs=args.define_subs,
                error_mode=error_mode,
                include_spans=args.include_spans,
                default_tenancy_alias=default_tenancy_alias,
                default_identity_domain=default_identity_domain,
                symbols_only=symbols_only,
            )

        if symbols_only:
            return _emit_symbols_from_defines(define_stmts, args.pretty)

        if not args.jsonl:
            diags = None if error_mode == "raise" else {"error_count": total_errors}
            if error_items is not None:
                diags["errors"] = error_items
            _emit_statements_jsonl_or_array(
                stmts=all_stmts,
                diags=diags,
                jsonl=False,
                pretty=args.pretty,
                schema_version=STATEMENT_SCHEMA_VERSION,
            )
            _write_diagnostics_file(args.diagnostics_file, diags or {"error_count": total_errors})

        if error_mode == "report" and total_errors:
            sys.stderr.write(f"{total_errors} syntax error(s) detected\n")
        return _exit_code_for_errors(error_mode, total_errors)

    # === NON-CHUNKED PATH ===
    source = _read_source_from_file_or_stdin(args.file)
    ret_filter = {"define"} if symbols_only else None

    res = parse_policy_statements(
        source,
        define_subs=args.define_subs,
        error_mode=error_mode,
        include_spans=args.include_spans,
        default_tenancy_alias=default_tenancy_alias,
        default_identity_domain=default_identity_domain,
        return_filter=ret_filter,
    )

    if isinstance(res, tuple):
        payload, diags = res
        stmts = payload.get("statements", [])
        if symbols_only:
            return _emit_symbols_from_defines(stmts, args.pretty)

        _emit_statements_jsonl_or_array(
            stmts=stmts,
            diags=diags,
            jsonl=args.jsonl,
            pretty=args.pretty,
            schema_version=STATEMENT_SCHEMA_VERSION,
        )
        _write_diagnostics_file(args.diagnostics_file, diags)

        errors = int((diags or {}).get("error_count", 0) or 0)
        if error_mode == "report" and errors:
            sys.stderr.write(f"{errors} syntax error(s) detected\n")
        return _exit_code_for_errors(error_mode, errors)

    # res is a payload (ignore mode or raise with no errors)
    if symbols_only:
        return _emit_symbols_from_defines(res.get("statements", []), args.pretty)

    _emit_statements_jsonl_or_array(
        stmts=res.get("statements", []),
        diags=None,
        jsonl=args.jsonl,
        pretty=args.pretty,
        schema_version=STATEMENT_SCHEMA_VERSION,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
