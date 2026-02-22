from __future__ import annotations

from oci_lexer_parser import build_symbols, parse_policy_statements


def parse_policy(text: str, **kwargs):
    res = parse_policy_statements(text, **kwargs)
    if isinstance(res, tuple):
        payload, _ = res
    else:
        payload = res
    return payload["statements"]


def test_payload_includes_schema_version():
    payload = parse_policy_statements("allow group A to read buckets in tenancy")
    if isinstance(payload, tuple):
        payload, _ = payload
    assert payload["schema_version"] == "1.0"
    assert isinstance(payload["statements"], list)


def test_include_spans_adds_source_text():
    text = "allow group A to read buckets in tenancy"
    payload = parse_policy_statements(text, include_spans=True)
    if isinstance(payload, tuple):
        payload, _ = payload
    stmt = payload["statements"][0]
    assert stmt["source_text"] == text


def test_single_allow_parses():
    text = "Allow group A to use buckets in tenancy"
    out = parse_policy(text)
    assert isinstance(out, list)
    assert out and out[0]["kind"] in {"allow", "deny"}


def test_build_symbols_nested_and_flat():
    text = "\n".join(
        [
            "define tenancy T as 'ocid1.tenancy.oc1..ten'",
            "define group foo/bar as 'ocid1.group.oc1..g'",
            "define compartment C as 'ocid1.compartment.oc1..c'",
        ]
    )
    stmts = parse_policy(text)
    nested = build_symbols(stmts, form="nested")
    flat = build_symbols(stmts, form="flat")
    assert nested["tenancy"]["T"] == "ocid1.tenancy.oc1..ten"
    assert flat[("group", "foo/bar")] == "ocid1.group.oc1..g"


def test_return_filter_fields_and_kinds():
    text = "\n".join(
        [
            "define tenancy T as 'ocid1.tenancy.oc1..t1'",
            "allow group A to read all-resources in tenancy",
            "define compartment C as 'ocid1.compartment.oc1..c1'",
        ]
    )
    out = parse_policy(
        text,
        return_filter={
            "kinds": ["define"],
            "fields": ["symbol", "def"],
            "first_only": True,
        },
    )
    assert isinstance(out, list)
    assert len(out) == 1
    assert out[0]["kind"] == "define"
    assert "def" in out[0] and "symbol" in out[0]


def test_default_tenancy_alias_applied_to_in_tenancy():
    text = "ALLOW SERVICE faas TO {KEY_READ} IN TENANCY"
    stmts = parse_policy(
        text,
        define_subs=False,
        error_mode="raise",
        default_tenancy_alias="MyTenancy",
    )
    assert isinstance(stmts, list) and len(stmts) == 1
    st = stmts[0]
    assert st["kind"] == "allow"

    loc = st["location"]
    assert isinstance(loc, dict)
    assert loc["type"] == "tenancy"
    assert loc["values"] == ["MyTenancy"]


def test_default_tenancy_alias_does_not_affect_compartment_locations():
    text = "ALLOW SERVICE faas TO {KEY_READ} IN COMPARTMENT Projects"
    stmts = parse_policy(
        text,
        define_subs=False,
        error_mode="raise",
        default_tenancy_alias="ShouldNotApply",
    )
    st = stmts[0]
    loc = st["location"]
    assert loc["type"] == "compartment_name"
    assert loc["values"] == ["Projects"]


def test_default_tenancy_alias_applies_only_to_in_tenancy_location_not_source():
    text = "ADMIT SERVICE faas OF TENANCY SrcTenancy TO {KEY_READ} IN TENANCY"
    stmts = parse_policy(
        text,
        define_subs=False,
        error_mode="raise",
        default_tenancy_alias="LocAlias",
    )
    st = stmts[0]
    src = st.get("source")
    assert isinstance(src, dict)
    assert src["type"] == "tenancy"
    assert src["values"] == ["SrcTenancy"]

    loc = st["location"]
    assert loc["type"] == "tenancy"
    assert loc["values"] == ["LocAlias"]


def test_default_tenancy_alias_not_applied_when_location_is_compartment():
    text = "ADMIT SERVICE faas OF TENANCY SrcTenancy TO {KEY_READ} IN COMPARTMENT Projects"
    stmts = parse_policy(
        text,
        define_subs=False,
        error_mode="raise",
        default_tenancy_alias="ShouldNotApply",
    )
    st = stmts[0]
    src = st.get("source")
    assert isinstance(src, dict)
    assert src["type"] == "tenancy"
    assert src["values"] == ["SrcTenancy"]

    loc = st["location"]
    assert loc["type"] == "compartment_name"
    assert loc["values"] == ["Projects"]


def test_comments_and_whitespace_do_not_change_parse_tree():
    base = (
        "allow group A to read all-resources in tenancy\n"
        "allow dynamic-group DG to manage buckets in compartment 'apps'\n"
    )

    with_comments = (
        "  // leading spaces + a line comment\n"
        "allow  group   A   to   read   all-resources   in   tenancy   \n"
        "  # another comment on its own line\n"
        "allow dynamic-group DG to manage buckets in compartment 'apps'   \n"
        "/* trailing block comment */\n"
    )

    a = parse_policy(base)
    b = parse_policy(with_comments)

    assert a == b


def test_define_subs_changes_only_the_expected_fields():
    text = (
        "define compartment apps as 'ocid1.compartment.oc1..apps'\n"
        "allow group A to read buckets in compartment apps\n"
    )

    no_subs = parse_policy(text, define_subs=False)
    with_subs = parse_policy(text, define_subs=True)

    assert len(no_subs) == 2 and len(with_subs) == 2

    allow0 = next(s for s in no_subs if s["kind"] == "allow")
    allow1 = next(s for s in with_subs if s["kind"] == "allow")

    assert allow0["subject"] == allow1["subject"]
    assert allow0["actions"] == allow1["actions"]
    assert allow0["resources"] == allow1["resources"]

    loc0 = allow0["location"]
    loc1 = allow1["location"]

    assert loc0["type"] == "compartment_name"
    assert loc1["type"] == "compartment-id"
    assert isinstance(loc1["values"][0], str)
    assert loc1["values"][0].startswith("ocid1.compartment.oc1..")


def test_chunking_equivalence_for_simple_input():
    s1 = "allow group A to read all-resources in tenancy\n"
    s2 = "allow group B to manage all-resources in tenancy\n"
    whole = s1 + s2

    a = parse_policy(whole)
    b = parse_policy(s1) + parse_policy(s2)

    assert a == b


def test_nested_conditions_preserve_expr_for_mixed_modes():
    text = (
        "allow group Admins to manage all-resources in tenancy where "
        "any { request.region = 'us-ashburn-1', "
        "all { request.user.name = /__PSM*/, target.user.name = 'user@example.test' } }\n"
    )
    out = parse_policy(text)
    conds = out[0]["conditions"]

    assert conds["type"] == "group"
    assert conds["mode"] == "any"
    assert conds["items"][1]["type"] == "group"
    assert conds["items"][1]["mode"] == "all"


def test_nested_conditions_flatten_same_mode():
    text = (
        "allow group Admins to manage all-resources in tenancy where "
        "any { request.region = 'us-ashburn-1', "
        "any { request.region = 'us-phoenix-1' } }\n"
    )
    out = parse_policy(text, nested_simplify=True)
    conds = out[0]["conditions"]

    assert conds["type"] == "group"
    assert conds["mode"] == "any"
    assert len(conds["items"]) == 2


def test_nested_conditions_no_flatten_when_flag_false():
    text = (
        "allow group Admins to manage all-resources in tenancy where "
        "any { request.region = 'us-ashburn-1', "
        "any { request.region = 'us-phoenix-1' } }\n"
    )
    out = parse_policy(text, nested_simplify=False)
    conds = out[0]["conditions"]

    assert conds["type"] == "group"
    assert conds["mode"] == "any"
    assert conds["items"][1]["type"] == "group"
    assert conds["items"][1]["mode"] == "any"


def test_nested_conditions_depth3_all_any_mix_preserves_by_default():
    text = (
        "allow group Admins to manage all-resources in tenancy where "
        "all { request.region = 'us-ashburn-1', "
        "any { request.user.name = 'alice', all { target.user.name = 'bob' } } }"
    )
    out = parse_policy(text, nested_simplify=False)
    conds = out[0]["conditions"]

    assert conds["type"] == "group"
    assert conds["mode"] == "all"
    assert conds["items"][1]["type"] == "group"
    assert conds["items"][1]["mode"] == "any"
    assert conds["items"][1]["items"][1]["type"] == "group"
    assert conds["items"][1]["items"][1]["mode"] == "all"


def test_nested_conditions_depth3_all_any_mix_simplifies_recursively():
    text = (
        "allow group Admins to manage all-resources in tenancy where "
        "any { request.region = 'us-ashburn-1', "
        "any { request.region = 'us-phoenix-1', "
        "any { request.region = 'eu-frankfurt-1' } } }"
    )
    out = parse_policy(text, nested_simplify=True)
    conds = out[0]["conditions"]

    assert conds["type"] == "group"
    assert conds["mode"] == "any"
    assert len(conds["items"]) == 3
    assert all(item["type"] == "clause" for item in conds["items"])


def test_statement_index_ignores_comment_keywords():
    text = (
        "# allow group commented out to read all-resources in tenancy\n"
        "allow group A to read all-resources in tenancy\n"
        "allow group B to read\n"
    )
    payload, diags = parse_policy_statements(text, error_mode="report")
    errors = diags.get("errors", [])
    assert errors
    # The syntax error should be in the second statement (index 2),
    # not shifted by the commented keyword.
    assert errors[0]["statement_index"] == 2
