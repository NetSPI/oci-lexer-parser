from __future__ import annotations

import json
from pathlib import Path

from helpers import discover_txt, read_text
from oci_lexer_parser import parse_dynamic_group_matching_rules, parse_policy_statements
from oci_lexer_parser.parser_utils import DG_SCHEMA_VERSION, STATEMENT_SCHEMA_VERSION

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


def _load_json(path: Path) -> dict:
    return json.loads(read_text(path))


def _policy_payload_for_compare(text: str, *, define_subs: bool) -> dict:
    try:
        res = parse_policy_statements(text, define_subs=define_subs, error_mode="report")
        if isinstance(res, tuple):
            payload, diags = res
        else:
            payload, diags = res, {"errors": [], "error_count": 0}
    except ValueError as exc:
        payload = {"schema_version": STATEMENT_SCHEMA_VERSION, "statements": []}
        diags = {"errors": [{"message": str(exc)}], "error_count": 1}
    if diags:
        payload["diagnostics"] = diags
    return payload


def _dg_payload_for_compare(text: str) -> dict:
    try:
        res = parse_dynamic_group_matching_rules(text, error_mode="report")
        if isinstance(res, tuple):
            payload, diags = res
        else:
            payload, diags = res, {"errors": [], "error_count": 0}
    except ValueError as exc:
        payload = {"schema_version": DG_SCHEMA_VERSION, "rules": []}
        diags = {"errors": [{"message": str(exc)}], "error_count": 1}
    if diags and diags.get("error_count"):
        payload["diagnostics"] = diags
    return payload


def test_policy_outputs_match_golden() -> None:
    for dir_name, define_subs in POLICY_PARSE_DIRS:
        for txt_path in discover_txt(POLICY_ROOT / dir_name):
            text = read_text(txt_path)
            payload = parse_policy_statements(text, define_subs=define_subs)
            if isinstance(payload, tuple):
                payload, _ = payload

            json_path = txt_path.with_suffix(".json")
            assert json_path.exists(), f"Missing golden JSON for {txt_path}"
            golden = _load_json(json_path)
            assert payload == golden, f"Golden mismatch for {txt_path}"

    # Error fixtures compare with diagnostics
    for txt_path in discover_txt(POLICY_ROOT / "error"):
        text = read_text(txt_path)
        payload = _policy_payload_for_compare(text, define_subs=False)
        json_path = txt_path.with_suffix(".json")
        assert json_path.exists(), f"Missing golden JSON for {txt_path}"
        golden = _load_json(json_path)
        assert payload == golden, f"Golden mismatch for {txt_path}"


def test_dynamic_group_outputs_match_golden() -> None:
    for txt_path in discover_txt(DG_ROOT):
        text = read_text(txt_path)
        payload = _dg_payload_for_compare(text)
        json_path = txt_path.with_suffix(".json")
        assert json_path.exists(), f"Missing golden JSON for {txt_path}"
        golden = _load_json(json_path)
        assert payload == golden, f"Golden mismatch for {txt_path}"


def test_cli_outputs_match_golden() -> None:
    for txt_path in discover_txt(CLI_ROOT):
        text = read_text(txt_path)
        stem = txt_path.stem

        if "dynamic_group" in stem:
            payload = parse_dynamic_group_matching_rules(text)
            if isinstance(payload, tuple):
                payload, _ = payload
        elif "bad" in stem or "error" in stem:
            payload = _policy_payload_for_compare(text, define_subs=False)
        else:
            payload = parse_policy_statements(text)
            if isinstance(payload, tuple):
                payload, _ = payload

        json_path = txt_path.with_suffix(".json")
        assert json_path.exists(), f"Missing golden JSON for {txt_path}"
        golden = _load_json(json_path)
        assert payload == golden, f"Golden mismatch for {txt_path}"
