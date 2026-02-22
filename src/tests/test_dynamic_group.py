from __future__ import annotations

from pathlib import Path

import pytest

from helpers import read_text
from oci_lexer_parser import parse_dynamic_group_matching_rules

FIXTURES = Path(__file__).parent / "fixtures" / "dynamic_group"


def parse_dynamic(text: str, **kwargs):
    res = parse_dynamic_group_matching_rules(text, **kwargs)
    if isinstance(res, tuple):
        payload, _ = res
    else:
        payload = res
    return payload["rules"]


def test_payload_includes_schema_version():
    payload = parse_dynamic_group_matching_rules("ALL { resource.type = 'instance' }")
    if isinstance(payload, tuple):
        payload, _ = payload
    assert payload["schema_version"] == "1.0"
    assert isinstance(payload["rules"], list)


def test_include_spans_adds_source_text():
    text = "ALL { resource.type = 'instance' }"
    payload = parse_dynamic_group_matching_rules(text, include_spans=True)
    if isinstance(payload, tuple):
        payload, _ = payload
    rule = payload["rules"][0]
    assert rule["expr"]["source_text"] == text


def test_single_rule_parses():
    text = read_text(FIXTURES / "01_all_basic.txt")
    out = parse_dynamic(text)

    assert isinstance(out, list)
    assert len(out) == 1
    assert out[0]["level"] == 1
    assert "predicates" not in out[0]

    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert expr["mode"] == "all"
    assert len(expr["items"]) == 2

    p0 = expr["items"][0]["node"]
    assert p0["lhs"] == "instance.compartment.id"
    assert p0["op"] == "eq"
    assert p0["rhs"]["type"] == "ocid"
    assert p0["rhs"]["value"] == "ocid1.compartment.oc1..example"


def test_nested_any_any_preserves_expr_by_default():
    text = read_text(FIXTURES / "02_nested_any_any.txt")
    out = parse_dynamic(text)

    assert len(out) == 1
    assert out[0]["level"] == 2
    assert "predicates" not in out[0]
    assert "expr" in out[0]

    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert expr["mode"] == "any"
    assert expr["items"][0]["type"] == "group"
    assert expr["items"][0]["mode"] == "any"


def test_nested_any_any_simplifies_with_flag():
    text = read_text(FIXTURES / "02_nested_any_any.txt")
    out = parse_dynamic(text, nested_simplify=True)

    assert len(out) == 1
    assert out[0]["level"] == 1

    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert expr["mode"] == "any"
    assert len(expr["items"]) == 3


def test_any_single_child_all_preserves_expr_by_default():
    text = read_text(FIXTURES / "03_any_single_child_all.txt")
    out = parse_dynamic(text)

    assert len(out) == 1
    assert out[0]["level"] == 2
    assert "predicates" not in out[0]
    assert "expr" in out[0]

    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert expr["mode"] == "any"
    assert expr["items"][0]["type"] == "group"
    assert expr["items"][0]["mode"] == "all"


def test_any_single_child_all_simplifies_with_flag():
    text = read_text(FIXTURES / "03_any_single_child_all.txt")
    out = parse_dynamic(text, nested_simplify=True)

    assert len(out) == 1
    assert out[0]["level"] == 1

    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert expr["mode"] == "all"
    assert len(expr["items"]) == 1

    p0 = expr["items"][0]["node"]
    assert p0["lhs"] == "resource.type"
    assert p0["op"] == "eq"
    assert p0["rhs"]["type"] == "literal"
    assert p0["rhs"]["value"] == "vaults"


def test_depth4_recursive_case_preserves_depth_by_default():
    text = read_text(FIXTURES / "04_depth4_recursive.txt")
    out = parse_dynamic(text)

    assert len(out) == 1
    assert out[0]["level"] == 4
    assert "predicates" not in out[0]
    assert "expr" in out[0]

    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert expr["mode"] == "any"


def test_depth4_recursive_case_simplifies_with_flag():
    text = read_text(FIXTURES / "04_depth4_recursive.txt")
    out = parse_dynamic(text, nested_simplify=True)

    assert len(out) == 1
    assert out[0]["level"] == 1

    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert len(expr["items"]) == 1
    assert expr["items"][0]["node"]["lhs"] == "instance.id"


def test_multiple_rules_newlines_parse_supported():
    text = read_text(FIXTURES / "05_multiple_rules_newlines.txt")
    out = parse_dynamic(text)

    assert isinstance(out, list)
    assert len(out) == 3

    assert out[0]["level"] == 1
    assert len(out[0]["expr"]["items"]) == 2
    assert out[0]["expr"]["mode"] == "any"

    assert out[1]["level"] == 1
    assert len(out[1]["expr"]["items"]) == 1
    assert out[1]["expr"]["mode"] == "all"
    assert out[1]["expr"]["items"][0]["node"]["lhs"] == "instance.compartment.id"
    assert out[1]["expr"]["items"][0]["node"]["op"] == "eq"
    assert out[1]["expr"]["items"][0]["node"]["rhs"]["type"] == "ocid"

    assert out[2]["level"] == 1
    assert len(out[2]["expr"]["items"]) == 1
    assert out[2]["expr"]["mode"] == "all"
    assert out[2]["expr"]["items"][0]["node"]["lhs"] == "tag.department.operations.value"
    assert out[2]["expr"]["items"][0]["node"]["op"] == "exists"
    assert "rhs" not in out[2]["expr"]["items"][0]["node"]


def test_handles_comma_inside_string_literal_and_newline_join():
    text = read_text(FIXTURES / "06_comma_inside_string_and_newline.txt")
    out = parse_dynamic(text)

    assert len(out) == 1
    assert out[0]["level"] == 1
    assert len(out[0]["expr"]["items"]) == 2
    assert out[0]["expr"]["mode"] == "all"

    p0 = out[0]["expr"]["items"][0]["node"]
    assert p0["lhs"] == "instance.compartment.id"
    assert p0["op"] == "eq"
    assert p0["rhs"]["type"] == "ocid"
    assert p0["rhs"]["value"].endswith(",")

    p1 = out[0]["expr"]["items"][1]["node"]
    assert p1["lhs"] == "tag.department.operations.value"
    assert p1["op"] == "eq"
    assert p1["rhs"]["value"] == "45"


def test_lowercase_any_all_are_accepted():
    text = read_text(FIXTURES / "07_lowercase_any_all.txt")
    out = parse_dynamic(text)
    assert out[0]["expr"]["mode"] == "any"


def test_not_equal_predicate():
    text = read_text(FIXTURES / "08_not_equal_predicate.txt")
    out = parse_dynamic(text)
    assert out[0]["expr"]["items"][0]["node"]["op"] == "neq"
    assert out[0]["expr"]["items"][0]["node"]["rhs"]["type"] == "literal"


@pytest.mark.parametrize(
    "fixture_name",
    [
        "09_error_bad_path.txt",
        "13_error_missing_brace.txt",
    ],
)
def test_report_mode_diagnostics_on_error(fixture_name: str):
    bad = read_text(FIXTURES / fixture_name)
    out, diags = parse_dynamic_group_matching_rules(bad, error_mode="report")
    out = out["rules"]
    assert isinstance(out, list)
    assert diags["error_count"] >= 1


def test_depth3_varied_tags_preserves_nested_expr():
    text = read_text(FIXTURES / "10_depth3_varied_tags.txt")
    out = parse_dynamic(text)

    assert len(out) == 1
    assert out[0]["level"] == 3
    assert "predicates" not in out[0]
    assert "expr" in out[0]

    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert expr["mode"] == "any"
    assert expr["items"][1]["type"] == "group"
    assert expr["items"][1]["mode"] == "all"


def test_all_any_nested_preserves_expr():
    text = read_text(FIXTURES / "11_all_any_nested.txt")
    out = parse_dynamic(text)

    assert len(out) == 1
    assert out[0]["level"] == 2
    assert "predicates" not in out[0]
    assert "expr" in out[0]

    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert expr["mode"] == "all"
    assert expr["items"][1]["type"] == "group"
    assert expr["items"][1]["mode"] == "any"


def test_all_all_nested_preserves_expr_by_default():
    text = read_text(FIXTURES / "12_all_all_nested.txt")
    out = parse_dynamic(text)

    assert len(out) == 1
    assert out[0]["level"] == 2
    assert "predicates" not in out[0]
    assert "expr" in out[0]

    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert expr["mode"] == "all"
    assert expr["items"][1]["type"] == "group"
    assert expr["items"][1]["mode"] == "all"


def test_all_all_nested_simplifies_with_flag():
    text = read_text(FIXTURES / "12_all_all_nested.txt")
    out = parse_dynamic(text, nested_simplify=True)

    assert len(out) == 1
    assert out[0]["level"] == 1

    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert expr["mode"] == "all"
    assert len(expr["items"]) == 3
    assert expr["items"][0]["node"]["lhs"] == "instance.id"
    assert expr["items"][0]["node"]["rhs"]["type"] == "ocid"


def test_depth3_all_any_mix_preserves_by_default():
    text = "ALL { resource.type = 'instance', ANY { resource.type = 'bucket', ALL { resource.type = 'volume' } } }"
    out = parse_dynamic(text)

    assert len(out) == 1
    assert out[0]["level"] == 3
    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert expr["mode"] == "all"
    assert expr["items"][1]["type"] == "group"
    assert expr["items"][1]["mode"] == "any"
    assert expr["items"][1]["items"][1]["type"] == "group"
    assert expr["items"][1]["items"][1]["mode"] == "all"


def test_depth3_any_any_any_simplifies_recursively():
    text = "ANY { resource.type = 'instance', ANY { resource.type = 'bucket', ANY { resource.type = 'volume' } } }"
    out = parse_dynamic(text, nested_simplify=True)

    assert len(out) == 1
    assert out[0]["level"] == 1
    expr = out[0]["expr"]
    assert expr["type"] == "group"
    assert expr["mode"] == "any"
    assert len(expr["items"]) == 3
    assert all(item["type"] == "clause" for item in expr["items"])
