from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from helpers import discover_txt, read_text
from oci_lexer_parser import (
    parse_dynamic_group_matching_rules,
    parse_policy_statements,
)

GENERATE = "GENERATE_JSON"

pytestmark = pytest.mark.generate_json

ROOT = Path(__file__).parent
OUT_ROOT = ROOT / "fixtures"
POLICY_ROOT = OUT_ROOT / "policy"
DG_ROOT = OUT_ROOT / "dynamic_group"
CLI_ROOT = OUT_ROOT / "cli"

POLICY_PARSE_DIRS = [
    ("valid_subs", True),
    ("matrix", False),
    ("examples", False),
    ("edge", False),
]


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _policy_out_path(txt_path: Path) -> Path:
    rel = txt_path.relative_to(POLICY_ROOT)
    return OUT_ROOT / "policy" / rel.with_suffix(".json")


def _dg_out_path(txt_path: Path) -> Path:
    rel = txt_path.relative_to(DG_ROOT)
    return OUT_ROOT / "dynamic_group" / rel.with_suffix(".json")


def test_generate_policy_json_outputs() -> None:
    if not os.getenv(GENERATE):
        pytest.skip("set GENERATE_JSON=1 to generate JSON outputs")
    # Parseable fixtures
    for dir_name, define_subs in POLICY_PARSE_DIRS:
        for txt_path in discover_txt(POLICY_ROOT / dir_name):
            text = read_text(txt_path)
            payload = parse_policy_statements(text, define_subs=define_subs)
            _write_json(_policy_out_path(txt_path), payload)

    # Error fixtures -> diagnostics (capture hard failures too)
    for txt_path in discover_txt(POLICY_ROOT / "error"):
        text = read_text(txt_path)
        try:
            res = parse_policy_statements(text, error_mode="report")
            if isinstance(res, tuple):
                payload, diags = res
            else:
                payload, diags = res, {"errors": [], "error_count": 0}
        except ValueError as exc:
            payload = {"schema_version": "1.0", "statements": []}
            diags = {"errors": [{"message": str(exc)}], "error_count": 1}
        payload["diagnostics"] = diags
        _write_json(_policy_out_path(txt_path), payload)


def test_generate_dynamic_group_json_outputs() -> None:
    if not os.getenv(GENERATE):
        pytest.skip("set GENERATE_JSON=1 to generate JSON outputs")
    for txt_path in discover_txt(DG_ROOT):
        text = read_text(txt_path)
        if "error" in txt_path.stem:
            try:
                res = parse_dynamic_group_matching_rules(text, error_mode="report")
                if isinstance(res, tuple):
                    payload, diags = res
                else:
                    payload, diags = res, {"errors": [], "error_count": 0}
            except ValueError as exc:
                payload = {"schema_version": "1.0", "rules": []}
                diags = {"errors": [{"message": str(exc)}], "error_count": 1}
            payload["diagnostics"] = diags
        else:
            payload = parse_dynamic_group_matching_rules(text)
        _write_json(_dg_out_path(txt_path), payload)


def _cli_out_path(txt_path: Path) -> Path:
    rel = txt_path.relative_to(CLI_ROOT)
    return OUT_ROOT / "cli" / rel.with_suffix(".json")


def test_generate_cli_json_outputs() -> None:
    if not os.getenv(GENERATE):
        pytest.skip("set GENERATE_JSON=1 to generate JSON outputs")
    for txt_path in discover_txt(CLI_ROOT):
        text = read_text(txt_path)
        stem = txt_path.stem

        if "dynamic_group" in stem:
            payload = parse_dynamic_group_matching_rules(text)
        elif "bad" in stem or "error" in stem:
            try:
                res = parse_policy_statements(text, error_mode="report")
                if isinstance(res, tuple):
                    payload, diags = res
                else:
                    payload, diags = res, {"errors": [], "error_count": 0}
            except ValueError as exc:
                payload = {"schema_version": "1.0", "statements": []}
                diags = {"errors": [{"message": str(exc)}], "error_count": 1}
            payload["diagnostics"] = diags
        else:
            payload = parse_policy_statements(text)

        _write_json(_cli_out_path(txt_path), payload)
