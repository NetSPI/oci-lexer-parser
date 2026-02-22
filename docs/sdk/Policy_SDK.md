# Policy SDK Usage

This guide focuses on `parse_policy_statements` and policy-specific utilities. For full output shapes, see `docs/schema/Policy_Schema.md`.

---

## Function Signature

```python
from oci_lexer_parser import parse_policy_statements

# Return type:
# - error_mode='report'  -> (payload: dict, diagnostics: dict)
# - error_mode in {'raise','ignore'} -> payload: dict
payload_or_tuple = parse_policy_statements(
    text: str | list[str] | tuple[str, ...],
    define_subs: bool = False,
    return_filter: str | list[str] | dict | None = None,
    include_spans: bool = False,
    nested_simplify: bool = False,
    error_mode: str = "raise",   # "raise" | "report" | "ignore"
    default_tenancy_alias: str | None = None,
    default_identity_domain: str | None = None,
)
```

---

## Return Types

| error_mode | Return type | Notes |
|---|---|---|
| `raise` | `dict` | Raises `ValueError` on first syntax error |
| `report` | `(dict, diagnostics)` | `diagnostics.error_count` > 0 when errors exist |
| `ignore` | `dict` | Best-effort parse, no diagnostics |

Payload shape (non-JSONL):
```json
{ "schema_version": "1.0", "statements": [ ... ] }
```

---

## Parameter Reference

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `text` | `str` \| `list[str]` \| `tuple[str, ...]` | - | Policy input. `str` may contain multiple newline-separated statements. Lists/tuples are joined with `\n` before parsing. Comments (`#`, `//`, `/* ... */`) are ignored. |
| `define_subs` | `bool` | `False` | Apply DEFINE substitutions where resolvable. |
| `return_filter` | `str` \| `list[str]` \| `dict` \| `None` | `None` | Filter or project fields (kinds, fields, first_only). |
| `include_spans` | `bool` | `False` | Include source span metadata per statement (adds `span` and `source_text`). |
| `nested_simplify` | `bool` | `False` | If `True`, flattens same-mode nested condition groups (ANY within ANY, ALL within ALL). |
| `error_mode` | `raise` \| `report` \| `ignore` | `raise` | Error handling mode. |
| `default_tenancy_alias` | `str` \| `None` | `None` | Inject a name for `IN TENANCY` location values. |
| `default_identity_domain` | `str` \| `None` | `None` | Default identity domain for group/dynamic-group subjects without explicit `Domain/Name`. |

---

## Parameter Examples

**`text`**  
Input:
```python
# Single blob with multiple statements
text = """
allow group Admins to manage all-resources in tenancy
allow any-user to read buckets in compartment Apps
"""
parse_policy_statements(text)
```
Output (abridged):
```json
{
  "schema_version": "1.0",
  "statements": [
    {"kind": "allow", "subject": {"type": "group", "values": [{"label": "Admins"}]}},
    {"kind": "allow", "subject": {"type": "any-user", "values": []}}
  ]
}
```

List/tuple inputs are joined with `\n` before parsing:
```python
lines = [
    "allow group Admins to manage all-resources in tenancy",
    "allow any-user to read buckets in compartment Apps",
]
parse_policy_statements(lines)
```

**`text` (tuple input)**  
```python
parts = (
    "allow group Admins to manage all-resources in tenancy",
    "allow any-user to read buckets in compartment Apps",
)
parse_policy_statements(parts)
```
Output (abridged):
```json
{
  "schema_version": "1.0",
  "statements": [
    {"kind": "allow", "subject": {"type": "group", "values": [{"label": "Admins"}]}},
    {"kind": "allow", "subject": {"type": "any-user", "values": []}}
  ]
}
```

**`define_subs`**  
```python
text = """
define group Admins as ocid1.group.oc1..aaaa
allow group Admins to manage all-resources in tenancy
"""
parse_policy_statements(text, define_subs=True)
```
Output (abridged):
```json
{
  "schema_version": "1.0",
  "statements": [
    {"kind": "allow", "subject": {"type": "group-id", "values": [{"label": "ocid1.group.oc1..aaaa"}]}}
  ]
}
```

**`return_filter`**  
```python
text = """
define group Admins as ocid1.group.oc1..aaaa
allow group Admins to read buckets in tenancy
"""

parse_policy_statements(text, return_filter="define")
```
Output (abridged):
```json
{
  "schema_version": "1.0",
  "statements": [
    {"kind": "define", "symbol": {"type": "group", "name": "Admins"}, "def": {"type": "ocid", "value": "ocid1.group.oc1..aaaa"}}
  ]
}
```

Return only certain fields (projection):
```python
text = """
define group Admins as ocid1.group.oc1..aaaa
allow group Admins to read buckets in tenancy
"""

parse_policy_statements(
    text,
    return_filter={
        "kinds": ["define", "allow"],
        "fields": ["kind", "symbol", "def", "subject", "location"],
    },
)
```
Output (abridged):
```json
{
  "schema_version": "1.0",
  "statements": [
    {
      "kind": "define",
      "symbol": {"type": "group", "name": "Admins"},
      "def": {"type": "ocid", "value": "ocid1.group.oc1..aaaa"}
    },
    {
      "kind": "allow",
      "subject": {"type": "group", "values": [{"label": "Admins"}]},
      "location": {"type": "tenancy", "values": []}
    }
  ]
}
```

**`include_spans`**  
```python
payload = parse_policy_statements(
    "allow group Admins to read buckets in tenancy",
    include_spans=True,
)
```
Note: `include_spans` currently adds `span` and `source_text` only at the statement level (not per condition node).
Output (abridged):
```json
{
  "schema_version": "1.0",
  "statements": [
    {
      "kind": "allow",
      "subject": {"type": "group", "values": [{"label": "Admins"}]},
      "actions": {"type": "verbs", "values": ["read"]},
      "resources": {"type": "specific", "values": ["buckets"]},
      "location": {"type": "tenancy", "values": []},
      "span": {"start": 0, "stop": 49, "line": 1, "column": 0},
      "source_text": "allow group Admins to read buckets in tenancy"
    }
  ]
}
```

**`nested_simplify`**  
```python
text = (
    "allow group Admins to manage all-resources in tenancy where "
    "any { request.region = 'us-ashburn-1', any { request.region = 'us-phoenix-1' } }"
)

parse_policy_statements(text)
# -> preserves the nested any-group by default

parse_policy_statements(text, nested_simplify=True)
# -> flattens same-mode nesting into a single any-group with two clauses
```
Output (abridged, default):
```json
{
  "schema_version": "1.0",
  "statements": [
    {
      "kind": "allow",
      "conditions": {
        "type": "group",
        "mode": "any",
        "items": [
          {
            "type": "clause",
            "node": {
              "lhs": "request.region",
              "op": "eq",
              "rhs": {"type": "literal", "value": "us-ashburn-1"}
            }
          },
          {
            "type": "group",
            "mode": "any",
            "items": [
              {
                "type": "clause",
                "node": {
                  "lhs": "request.region",
                  "op": "eq",
                  "rhs": {"type": "literal", "value": "us-phoenix-1"}
                }
              }
            ]
          }
        ]
      }
    }
  ]
}
```
Output (abridged, `nested_simplify=True`):
```json
{
  "schema_version": "1.0",
  "statements": [
    {
      "kind": "allow",
      "conditions": {
        "type": "group",
        "mode": "any",
        "items": [
          {
            "type": "clause",
            "node": {
              "lhs": "request.region",
              "op": "eq",
              "rhs": {"type": "literal", "value": "us-ashburn-1"}
            }
          },
          {
            "type": "clause",
            "node": {
              "lhs": "request.region",
              "op": "eq",
              "rhs": {"type": "literal", "value": "us-phoenix-1"}
            }
          }
        ]
      }
    }
  ]
}
```

**`error_mode`**  
```python
bad = "allow group Admins to manage all-resources in tenancy where any { request.region = }"

parse_policy_statements(bad, error_mode="raise")
# -> raises ValueError on the first syntax error

payload, diagnostics = parse_policy_statements(bad, error_mode="report")
# -> returns (payload, diagnostics) with error_count > 0
#
# Example output (payload, diagnostics) from fixtures:
# payload:
# {
#   "schema_version": "1.0",
#   "statements": [
#     {
#       "kind": "allow",
#       "subject": {"type": "group", "values": [{"label": "Admins"}]},
#       "actions": {"type": "verbs", "values": ["manage"]},
#       "resources": {"type": "all-resources", "values": []},
#       "location": {"type": "tenancy", "values": []},
#       "conditions": {
#         "type": "group",
#         "mode": "any",
#         "items": [
#           {
#             "type": "clause",
#             "node": {
#               "lhs": "request.region",
#               "op": "eq",
#               "rhs": {"type": "literal", "value": ""}
#             }
#           }
#         ]
#       }
#     }
#   ]
# }
# diagnostics:
# {
#   "errors": [
#     {
#       "line": 1,
#       "column": 83,
#       "message": "missing {OCID, QUOTED_OCID, PATTERN, WORD, QUOTED} at '}'",
#       "offending": "}",
#       "expected": null,
#       "statement_index": 1,
#       "line_text": "allow group Admins to manage all-resources in tenancy where any { request.region = }",
#       "caret": "                                                                                   ^"
#     }
#   ],
#   "error_count": 1
# }

parse_policy_statements(bad, error_mode="ignore")
# -> best-effort parse, no diagnostics (may return partial results)
```

**`default_tenancy_alias`**  
```python
text = "allow group Admins to manage all-resources in tenancy"
parse_policy_statements(text, default_tenancy_alias="RootTenancy")
```
Output (abridged):
```json
{
  "schema_version": "1.0",
  "statements": [
    {
      "kind": "allow",
      "location": {"type": "tenancy", "values": ["RootTenancy"]}
    }
  ]
}
```

**`default_identity_domain`**  
```python
text = "allow group Admins to read buckets in tenancy"
parse_policy_statements(text, default_identity_domain="DefaultDomain")
```
Output (abridged):
```json
{
  "schema_version": "1.0",
  "statements": [
    {
      "kind": "allow",
      "subject": {
        "type": "group",
        "values": [{"label": "Admins", "identity_domain": "DefaultDomain"}]
      }
    }
  ]
}
```

---

## DEFINE: Substitutions and Symbol Tables

### DEFINE statement shape
```json
{
  "kind": "define",
  "symbol": {"type": "tenancy" | "group" | "dynamic-group" | "compartment", "name": "<Alias>"},
  "def": {"type": "ocid", "value": "ocid1...."}
}
```

### Building a symbol table
```python
from oci_lexer_parser import parse_policy_statements, build_symbols

text = """
Define tenancy MyTenancy as 'ocid1.tenancy.oc1..xyz'
Define compartment Eng as 'ocid1.compartment.oc1..abc'
"""

payload = parse_policy_statements(text, error_mode="raise")
stmts = payload["statements"]

flat = build_symbols(stmts, form="flat")
# -> {('tenancy','MyTenancy'): 'ocid1.tenancy.oc1..xyz',
#     ('compartment','Eng'): 'ocid1.compartment.oc1..abc'}

nested = build_symbols(stmts, form="nested")
# -> {"tenancy": {"MyTenancy": "ocid1.tenancy.oc1..xyz"},
#     "compartment": {"Eng": "ocid1.compartment.oc1..abc"}}
```

### Substitutions (`define_subs=True`)

When enabled, resolvable names are replaced with OCIDs in:
- `subject` (group / dynamic-group names -> `*-id` when all resolve)
- `location` (single-segment compartment names -> `compartment-id`)
- `source` (ADMIT) and `target` (ENDORSE) tenancy names -> OCIDs

Substitutions are conservative: a subject becomes `*-id` only if all names resolve.
