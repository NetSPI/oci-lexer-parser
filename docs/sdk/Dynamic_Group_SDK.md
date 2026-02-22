# Dynamic Group SDK Usage

This guide focuses on `parse_dynamic_group_matching_rules`. For full output shapes, see `docs/schema/Dynamic_Group_Schema.md`.

---

## Function Signature

```python
from oci_lexer_parser import parse_dynamic_group_matching_rules

# Return type:
# - error_mode='report'  -> (payload: dict, diagnostics: dict)
# - error_mode in {'raise','ignore'} -> payload: dict
payload_or_tuple = parse_dynamic_group_matching_rules(
    text: str | list[str] | tuple[str, ...],
    include_spans: bool = False,
    nested_simplify: bool = False,
    error_mode: str = "raise",
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
{ "schema_version": "1.0", "rules": [ ... ] }
```

---

## Parameter Reference

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `text` | `str` \| `list[str]` \| `tuple[str, ...]` | - | Rules input. `str` may contain multiple newline-separated rules. Lists/tuples are joined with `\n` before parsing. Comments (`#`, `//`, `/* ... */`) are ignored. |
| `include_spans` | `bool` | `False` | Include source span metadata per rule (adds `span` and `source_text`). |
| `nested_simplify` | `bool` | `False` | If `True`, collapses same-mode nesting and single-child groups. |
| `error_mode` | `raise` \| `report` \| `ignore` | `raise` | Error handling mode. |

Supported LHS paths:
- `instance.compartment.id`
- `instance.id`
- `resource.id`
- `resource.compartment.id`
- `resource.type`
- `tag.<tagnamespace>.<tagkey>.value`

---

## Parameter Examples

**`text` (string input)**  
Input:
```python
parse_dynamic_group_matching_rules(
    "ALL { resource.type = 'instance', instance.compartment.id = 'ocid1.compartment.oc1..example' }"
)
```
Output (abridged):
```json
{
  "schema_version": "1.0",
  "rules": [
    {
      "level": 1,
      "expr": {
        "type": "group",
        "mode": "all",
        "items": [
          {"type": "clause", "node": {"lhs": "resource.type", "op": "eq", "rhs": {"type": "literal", "value": "instance"}}},
          {"type": "clause", "node": {"lhs": "instance.compartment.id", "op": "eq", "rhs": {"type": "ocid", "value": "ocid1.compartment.oc1..example"}}}
        ]
      }
    }
  ]
}
```

**`text` (list input)**  
List/tuple inputs are joined with `\n` before parsing, so this is equivalent to one multi-line blob.
```python
lines = [
    "ALL { resource.type = 'instance' }",
    "ANY { resource.type = 'bucket', resource.type = 'cluster' }",
]
parse_dynamic_group_matching_rules(lines)
```
Output (abridged):
```json
{
  "schema_version": "1.0",
  "rules": [
    {"level": 1, "expr": {"type": "group", "mode": "all", "items": [ ... ]}},
    {"level": 1, "expr": {"type": "group", "mode": "any", "items": [ ... ]}}
  ]
}
```

**`text` (tuple input)**  
```python
parts = (
    "ALL { resource.type = 'instance' }",
    "ANY { resource.type = 'bucket', resource.type = 'cluster' }",
)
parse_dynamic_group_matching_rules(parts)
```
Output (abridged):
```json
{
  "schema_version": "1.0",
  "rules": [
    {"level": 1, "expr": {"type": "group", "mode": "all", "items": [ ... ]}},
    {"level": 1, "expr": {"type": "group", "mode": "any", "items": [ ... ]}}
  ]
}
```

**`include_spans`**  
Spans are most useful when you want to map a parsed node back to the exact
slice of the original rule (for UI highlighting, error pinning, or traceability).

```python
parse_dynamic_group_matching_rules(
    "ANY { resource.type = 'instance', instance.compartment.id = 'ocid1.compartment.oc1..example' }",
    include_spans=True,
)
```
Output (abridged):
```json
{
  "schema_version": "1.0",
  "rules": [
    {
      "level": 1,
      "expr": {
        "type": "group",
        "mode": "any",
        "span": {"start": 0, "stop": 90, "line": 1, "column": 0},
        "source_text": "ANY { resource.type = 'instance', instance.compartment.id = 'ocid1.compartment.oc1..example' }",
        "items": [
          {
            "type": "clause",
            "node": {
              "lhs": "resource.type",
              "op": "eq",
              "rhs": {"type": "literal", "value": "instance"},
              "span": {"start": 6, "stop": 33, "line": 1, "column": 6},
              "source_text": "resource.type = 'instance'"
            }
          },
          {
            "type": "clause",
            "node": {
              "lhs": "instance.compartment.id",
              "op": "eq",
              "rhs": {"type": "ocid", "value": "ocid1.compartment.oc1..example"},
              "span": {"start": 36, "stop": 90, "line": 1, "column": 36},
              "source_text": "instance.compartment.id = 'ocid1.compartment.oc1..example'"
            }
          }
        ]
      }
    }
  ]
}
```

**`nested_simplify`**  
Input:
```python
text = "ANY { resource.type = 'instance', ANY { resource.type = 'bucket' } }"
```
Default (no simplify - preserve nesting):
```python
parse_dynamic_group_matching_rules(text)
```
Default (no simplify - preserve nesting) Output (abridged):
```json
{
  "schema_version": "1.0",
  "rules": [
    {
      "level": 2,
      "expr": {
        "type": "group",
        "mode": "any",
        "items": [
          {"type": "clause", "node": {"lhs": "resource.type", "op": "eq", "rhs": {"type": "literal", "value": "instance"}}},
          {"type": "group", "mode": "any", "items": [ ... ]}
        ]
      }
    }
  ]
}
```
With simplification - Converted ANY { COND1 , ANY {COND2}} to ANY {COND1, COND2}:
```python
parse_dynamic_group_matching_rules(text, nested_simplify=True)
```
Output (abridged):
```json
{
  "schema_version": "1.0",
  "rules": [
    {
      "level": 1,
      "expr": {
        "type": "group",
        "mode": "any",
        "items": [
          {"type": "clause", "node": {"lhs": "resource.type", "op": "eq", "rhs": {"type": "literal", "value": "instance"}}},
          {"type": "clause", "node": {"lhs": "resource.type", "op": "eq", "rhs": {"type": "literal", "value": "bucket"}}}
        ]
      }
    }
  ]
}
```

**`error_mode`**  
```python
bad = "ALL { resource.type = 'instance', instance.compartment.id = 'ocid1.compartment.oc1..example'"

parse_dynamic_group_matching_rules(bad, error_mode="raise")
# -> raises ValueError on the first syntax error (no partial results)

payload, diagnostics = parse_dynamic_group_matching_rules(bad, error_mode="report")
# -> returns (payload, diagnostics) with error_count > 0
#    diagnostics include line/column, offending token, expected tokens, and caret
#
# Example output (issue: missing closing brace) from fixtures:
# payload:
# {
#   "schema_version": "1.0",
#   "rules": [
#     {
#       "level": 1,
#       "expr": {
#         "type": "group",
#         "mode": "all",
#         "items": []
#       }
#     }
#   ]
# }
# diagnostics:
# {
#   "errors": [
#     {
#       "line": 1,
#       "column": 92,
#       "message": "no viable alternative at input 'ALL{resource.type='instance',instance.compartment.id='ocid1.compartment.oc1..example''",
#       "offending": "<EOF>",
#       "expected": null,
#       "line_text": "ALL { resource.type = 'instance', instance.compartment.id = 'ocid1.compartment.oc1..example'",
#       "caret": "                                                                                            ^",
#       "rule_index": null
#     }
#   ],
#   "error_count": 1
# }

parse_dynamic_group_matching_rules(bad, error_mode="ignore")
# -> best-effort parse, no diagnostics (may return partial results)
```
