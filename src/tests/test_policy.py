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


def test_whitespace_variance_does_not_change_parse_tree():
    base = (
        "allow group A to read all-resources in tenancy\n"
        "allow dynamic-group DG to manage buckets in compartment 'apps'\n"
    )

    with_extra_whitespace = (
        "  \n"
        "allow  group   A   to   read   all-resources   in   tenancy   \n"
        "  \n"
        "allow dynamic-group DG to manage buckets in compartment 'apps'   \n"
    )

    a = parse_policy(base)
    b = parse_policy(with_extra_whitespace)

    assert a == b


def test_admit_of_any_tenancy():
    text = "Admit any-user of any-tenancy to manage object-family in tenancy"
    stmts = parse_policy(text, error_mode="raise")
    st = stmts[0]

    assert st["subject"]["type"] == "any-user"
    assert st["source"] == {"type": "any-tenancy", "values": []}


def test_admit_of_named_tenancy():
    text = "Admit any-user of tenancy SourceTenancy to manage object-family in tenancy"
    stmts = parse_policy(text, error_mode="raise")
    st = stmts[0]

    assert st["subject"]["type"] == "any-user"
    assert st["source"] == {"type": "tenancy", "values": ["SourceTenancy"]}


def test_admit_malformed_of_clause_reports_error_instead_of_crashing():
    # Regression test: ctx.OF() being truthy under error recovery previously
    # didn't guarantee ctx.name() was populated, causing an unhandled
    # AttributeError instead of a reported diagnostic.
    text = "Admit any-user of banana to manage object-family in tenancy"
    _, diags = parse_policy_statements(text, error_mode="report")
    assert diags["error_count"] > 0


def test_admit_of_any_tenancy_accepts_only_wildcard_subjects():
    # OCI only accepts the ANY-USER or ANY-GROUP wildcard subjects when the scope
    # is OF ANY-TENANCY; named group/dynamic-group/service subjects are rejected.
    # This is enforced at the grammar level (two labeled admitStmt alternatives),
    # not as a separate semantic check on an otherwise-successful parse.
    for subject_type in ("any-user", "any-group"):
        text = f"Admit {subject_type} of any-tenancy to manage object-family in tenancy"
        stmts = parse_policy(text, error_mode="raise")
        st = stmts[0]
        assert st["subject"] == {"type": subject_type, "values": []}
        assert st["source"] == {"type": "any-tenancy", "values": []}

    for subject in ("group ABC", "dynamic-group DGs", "service faas"):
        text = f"Admit {subject} of any-tenancy to manage object-family in tenancy"
        _, diags = parse_policy_statements(text, error_mode="report")
        assert diags["error_count"] > 0, f"expected a syntax error for: {text!r}"


def test_comments_are_not_supported_and_raise_syntax_errors():
    # Comment syntax (//, #, /* */) is not part of OCI's policy language and this
    # parser does not special-case it. Leftover comment-like text from a user's
    # editor must surface as a loud syntax error, never be silently swallowed -
    # a naive comment stripper here previously corrupted quoted values containing
    # '//' (e.g. URLs) or '#' by truncating them with zero reported errors.
    for text in (
        "// a line comment\nallow group A to read all-resources in tenancy\n",
        "# a line comment\nallow group A to read all-resources in tenancy\n",
        "allow group A to read all-resources in tenancy // trailing note\n",
        "allow group A to read all-resources in tenancy # trailing note\n",
        "/* a block comment */\nallow group A to read all-resources in tenancy\n",
    ):
        try:
            parse_policy(text)
        except ValueError:
            continue
        raise AssertionError(f"expected a syntax error for: {text!r}")


def test_quoted_values_containing_slash_slash_or_hash_are_preserved():
    # Regression test: the old comment stripper ran on raw text before quoting
    # was tokenized, so any quoted value containing '//' (e.g. a URL) or '#'
    # was silently truncated at that point with zero reported errors.
    cases = {
        "https://accounts.google.com": (
            "allow group Admins to manage all-resources in tenancy "
            "where target.resource.tag = 'https://accounts.google.com'"
        ),
        "ticket#1234": (
            "allow group Admins to manage all-resources in tenancy "
            "where target.resource.tag = 'ticket#1234'"
        ),
    }
    for expected_value, text in cases.items():
        out = parse_policy(text, error_mode="raise")
        node = out[0]["conditions"]["items"][0]["node"]
        assert node["rhs"]["value"] == expected_value


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


def test_condition_not_in_single_value():
    text = (
        "Allow group test_conditions_group to manage all-resources in tenancy "
        "where request.operation not in ('ListBuckets')"
    )
    out = parse_policy(text, error_mode="raise")
    node = out[0]["conditions"]["items"][0]["node"]

    assert node["lhs"] == "request.operation"
    assert node["op"] == "not_in"
    assert node["rhs"]["type"] == "list"
    assert [v["value"] for v in node["rhs"]["values"]] == ["ListBuckets"]


def test_condition_not_in_multiple_values_within_all_group():
    text = (
        "allow group Admins to manage all-resources in tenancy where "
        "all { request.operation not in ('ListBuckets', 'GetObject'), "
        "request.region = 'us-ashburn-1' }"
    )
    out = parse_policy(text, error_mode="raise")
    conds = out[0]["conditions"]

    assert conds["type"] == "group"
    assert conds["mode"] == "all"
    not_in_node = conds["items"][0]["node"]
    assert not_in_node["op"] == "not_in"
    assert [v["value"] for v in not_in_node["rhs"]["values"]] == ["ListBuckets", "GetObject"]


def test_condition_bare_presence_check():
    text = (
        "Allow group test_conditions_group to manage object-family in tenancy "
        "where any {target.resource.tag.Foo.Bar}"
    )
    out = parse_policy(text, error_mode="raise")
    node = out[0]["conditions"]["items"][0]["node"]

    assert node == {"lhs": "target.resource.tag.Foo.Bar", "op": "exists"}
    assert "rhs" not in node


def test_condition_unary_not_presence_check():
    text = (
        "Allow group test_conditions_group to manage object-family in tenancy "
        "where any {not target.resource.tag.Foo.Bar}"
    )
    out = parse_policy(text, error_mode="raise")
    node = out[0]["conditions"]["items"][0]["node"]

    assert node == {"lhs": "target.resource.tag.Foo.Bar", "op": "not_exists"}
    assert "rhs" not in node


def test_condition_not_presence_combined_with_neq_in_any_group():
    text = (
        "Allow group test_conditions_group to manage object-family in tenancy where any "
        "{ not target.resource.tag.Foo.Bar, target.resource.tag.Foo.Bar != 'baz' }"
    )
    out = parse_policy(text, error_mode="raise")
    conds = out[0]["conditions"]

    assert conds["mode"] == "any"
    assert conds["items"][0]["node"] == {
        "lhs": "target.resource.tag.Foo.Bar",
        "op": "not_exists",
    }
    assert conds["items"][1]["node"] == {
        "lhs": "target.resource.tag.Foo.Bar",
        "op": "neq",
        "rhs": {"type": "literal", "value": "baz"},
    }


def test_condition_standalone_presence_checks_without_group_wrapper():
    present = parse_policy(
        "allow group A to manage object-family in tenancy where target.resource.tag.Foo.Bar",
        error_mode="raise",
    )
    node = present[0]["conditions"]["items"][0]["node"]
    assert node == {"lhs": "target.resource.tag.Foo.Bar", "op": "exists"}

    not_present = parse_policy(
        "allow group A to manage object-family in tenancy where not target.resource.tag.Foo.Bar",
        error_mode="raise",
    )
    node = not_present[0]["conditions"]["items"][0]["node"]
    assert node == {"lhs": "target.resource.tag.Foo.Bar", "op": "not_exists"}


def test_endorse_permission_list_drops_to_and_resource():
    # Live-validated: ENDORSE ... {PERM, ...} IN ... has no TO and no resource-type,
    # unlike every other endorseVerb form (named verbs / associate / single-word
    # permission), which still require "TO <verb> <resource> IN ...".
    text = "Endorse group test_conditions_group {BUCKET_INSPECT} in any-tenancy"
    stmts = parse_policy(text, error_mode="raise")
    st = stmts[0]

    assert st["subject"] == {"type": "group", "values": [{"label": "test_conditions_group"}]}
    assert st["target"] == {"type": "any-tenancy", "values": []}
    assert st["actions"] == {"type": "permissions", "values": ["bucket_inspect"]}
    assert st["resources"] == {"type": "unknown", "values": []}


def test_endorse_permission_list_multiple_values_and_where_clause():
    text = (
        "Endorse group test_conditions_group {BUCKET_INSPECT, BUCKET_READ} in any-tenancy "
        "where request.region = 'us-ashburn-1'"
    )
    stmts = parse_policy(text, error_mode="raise")
    st = stmts[0]

    assert st["actions"] == {"type": "permissions", "values": ["bucket_inspect", "bucket_read"]}
    assert st["conditions"]["items"][0]["node"] == {
        "lhs": "request.region",
        "op": "eq",
        "rhs": {"type": "literal", "value": "us-ashburn-1"},
    }


def test_endorse_general_form_with_to_and_resource_still_works():
    # Regression: the pre-existing "TO {list} <resource> IN ..." shape must
    # keep working unchanged alongside the new no-TO/no-resource shorthand.
    text = "Endorse group test_conditions_group to {BUCKET_INSPECT} buckets in any-tenancy"
    stmts = parse_policy(text, error_mode="raise")
    st = stmts[0]

    assert st["actions"] == {"type": "permissions", "values": ["bucket_inspect"]}
    assert st["resources"] == {"type": "specific", "values": ["buckets"]}


def test_endorse_named_verb_still_requires_to_and_resource():
    text = "endorse group Endorsers to associate all-resources in tenancy T"
    stmts = parse_policy(text, error_mode="raise")
    st = stmts[0]

    assert st["actions"] == {"type": "verbs", "values": ["associate"]}
    assert st["resources"] == {"type": "all-resources", "values": []}


def test_endorse_scope_compartment_of_tenancy():
    # Live-validated: ENDORSE ... IN COMPARTMENT <name> OF TENANCY <name> is a
    # distinct endorseScope form alongside plain ANY-TENANCY / TENANCY <name>.
    text = "Endorse group test_conditions_group to manage object-family in compartment foo of tenancy bar"
    stmts = parse_policy(text, error_mode="raise")
    st = stmts[0]

    assert st["target"] == {"type": "compartment_name", "values": ["foo"], "tenancy": "bar"}
    assert st["actions"] == {"type": "verbs", "values": ["manage"]}
    assert st["resources"] == {"type": "specific", "values": ["object-family"]}


def test_endorse_scope_nested_compartment_path_of_tenancy():
    text = "Endorse group test_conditions_group to manage object-family in compartment Root:Apps of tenancy bar"
    stmts = parse_policy(text, error_mode="raise")
    st = stmts[0]

    assert st["target"] == {
        "type": "compartment-path",
        "values": ["Root", "Apps"],
        "tenancy": "bar",
    }


def test_endorse_scope_compartment_of_tenancy_combined_with_permission_list():
    # The two ENDORSE fixes compose: the no-TO/no-resource permission-list shorthand
    # together with a compartment-of-tenancy scope.
    text = "Endorse group test_conditions_group {BUCKET_INSPECT} in compartment foo of tenancy bar"
    stmts = parse_policy(text, error_mode="raise")
    st = stmts[0]

    assert st["target"] == {"type": "compartment_name", "values": ["foo"], "tenancy": "bar"}
    assert st["actions"] == {"type": "permissions", "values": ["bucket_inspect"]}
    assert st["resources"] == {"type": "unknown", "values": []}


def test_identity_domain_subject_does_not_swallow_a_later_regex_pattern():
    # Regression test: PATTERN previously didn't exclude unescaped single quotes, so
    # the SLASH in a quoted 'domain'/'group' subject could be mis-lexed as the start
    # of PATTERN and greedily consume everything up to the *next* real '/' in the
    # statement - including a genuine /pattern/ condition later in the same line.
    text = (
        "Allow group 'identity-domain'/'group' to manage all-resources in tenancy "
        "where target.user.name = /somepattern/"
    )
    stmts = parse_policy(text, error_mode="raise")
    st = stmts[0]

    assert st["subject"] == {
        "type": "group",
        "values": [{"label": "group", "identity_domain": "identity-domain"}],
    }
    assert st["conditions"]["items"][0]["node"] == {
        "lhs": "target.user.name",
        "op": "eq",
        "rhs": {"type": "regex", "value": "/somepattern/", "pattern": "somepattern"},
    }


def test_define_with_missing_ocid_reports_error_instead_of_crashing():
    # Regression test: ctx.ocid() being None under error recovery (DEFINE with
    # nothing after AS) previously raised an unhandled AttributeError instead
    # of being caught and reported as a diagnostic.
    text = "define compartment foo as"
    _, diags = parse_policy_statements(text, error_mode="report")
    assert diags["error_count"] > 0


def test_define_group_with_missing_name_reports_error_instead_of_crashing():
    text = "define group as ocid1.group.oc1..aaaa"
    _, diags = parse_policy_statements(text, error_mode="report")
    assert diags["error_count"] > 0


def test_condition_not_without_in_is_a_syntax_error():
    # "not" alone (without "in") is invalid OCI policy syntax - only "not in" is valid.
    text = (
        "Allow group test_conditions_group to manage all-resources in tenancy "
        "where request.operation not ('ListBuckets')"
    )
    _, diags = parse_policy_statements(text, error_mode="report")
    assert diags["error_count"] > 0


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


def test_statement_index_unaffected_by_a_leading_malformed_line():
    # There's no comment syntax to ignore anymore (see
    # test_comments_are_not_supported_and_raise_syntax_errors); a leading '#'
    # line is just another malformed statement and reports its own error.
    # This checks that error reporting for a later, well-formed statement
    # doesn't get shifted or otherwise confused by an earlier broken one.
    text = (
        "# allow group commented out to read all-resources in tenancy\n"
        "allow group A to read all-resources in tenancy\n"
        "allow group B to read\n"
    )
    payload, diags = parse_policy_statements(text, error_mode="report")
    errors = diags.get("errors", [])
    assert len(errors) == 2
    assert errors[1]["statement_index"] == 2
    assert errors[1]["line"] == 4
