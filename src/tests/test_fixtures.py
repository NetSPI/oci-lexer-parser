from __future__ import annotations

import pytest
from pathlib import Path

from helpers import discover_txt, read_text
from oci_lexer_parser import parse_policy_statements


def parse_policy(text: str, **kwargs):
    res = parse_policy_statements(text, **kwargs)
    if isinstance(res, tuple):
        payload, _ = res
    else:
        payload = res
    return payload["statements"]

FIXTURES_ROOT = Path(__file__).parent / "fixtures" / "policy"

PARSE_DIRS = [
    ("valid_subs", True),
    ("matrix", False),
    ("examples", False),
    ("edge", False),
]


def _parse_matrix() -> list[tuple[Path, bool]]:
    cases: list[tuple[Path, bool]] = []
    for dir_name, define_subs in PARSE_DIRS:
        for txt_path in discover_txt(FIXTURES_ROOT / dir_name):
            cases.append((txt_path, define_subs))
    return cases


@pytest.mark.parametrize("txt_path, define_subs", _parse_matrix())
def test_policy_fixtures_parse(txt_path: Path, define_subs: bool) -> None:
    text = read_text(txt_path)
    out = parse_policy(text, define_subs=define_subs)
    assert isinstance(out, list)


@pytest.mark.parametrize("txt_path", discover_txt(FIXTURES_ROOT / "error"))
def test_policy_fixtures_error(txt_path: Path) -> None:
    text = read_text(txt_path)
    try:
        res = parse_policy_statements(text, error_mode="report")
    except ValueError:
        return
    if isinstance(res, tuple):
        _, diags = res
    else:
        diags = {"error_count": 0}
    assert diags.get("error_count", 0) > 0
