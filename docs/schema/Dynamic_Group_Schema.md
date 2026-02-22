# Dynamic Group JSON Schema (v1.0)

This document describes the normalized JSON output for OCI Dynamic Group matching rules.

---

## Top-Level Object

Top-level payload:

| Field | Type | Description |
|---|---|---|
| `schema_version` | `string` | Current schema version (`"1.0"`) |
| `rules` | `list[object]` | Parsed rule objects |
| `diagnostics` | `object` (optional) | Present when `error_mode="report"` |

Each parsed rule object has:

| Field | Type | Description |
|---|---|---|
| `level` | `int` | Depth of the rule tree (outermost group starts at 1) |
| `expr` | `object` | Expression tree (always present) |

---

## Core Objects

`expr` is always a tree with uniform node shapes. There are two node types:

### `expr` (group)

```json
{"type": "group", "mode": "any", "items": [ ... ]}
```

| Field | Type | Description |
|---|---|---|
| `type` | `string` | Always `group` |
| `mode` | `string` | `all` or `any` |
| `items` | `list[object]` | Child nodes (group or clause) |
| `span` | `object` (optional) | Present when `include_spans=True` |
| `source_text` | `string` (optional) | Original text for this node (`include_spans=True`) |

### `expr` item (clause)

```json
{"type": "clause", "node": {"lhs": "resource.type", "op": "eq", "rhs": {"type": "literal", "value": "instance"}}}
```

| Field | Type | Description |
|---|---|---|
| `type` | `string` | Always `clause` |
| `node` | `object` | The actual clause (see below) |

Clause object fields:

| Field | Type | Description |
|---|---|---|
| `lhs` | `string` | Attribute path. Supported values:<br>- `instance.compartment.id`<br>- `instance.id`<br>- `resource.id`<br>- `resource.compartment.id`<br>- `resource.type`<br>- `tag.<tagnamespace>.<tagkey>.value` |
| `op` | `string` | `eq`, `neq`, or `exists` |
| `rhs` | `object` | Present for `eq` and `neq` |
| `span` | `object` (optional) | Present when `include_spans=True` |
| `source_text` | `string` (optional) | Original text for this clause (`include_spans=True`) |

`rhs.type` values:

| Type | Shape | Meaning |
|---|---|---|
| `literal` | `{ "type": "literal", "value": "instance" }` | Plain string or bare token |
| `ocid` | `{ "type": "ocid", "value": "ocid1.compartment.oc1..example" }` | OCI OCID value |
| `regex` | `{ "type": "regex", "value": "/prod.*/", "pattern": "prod.*" }` | Regex pattern |

---

## Examples

### Flat Rule (ALL)

Rule:
```
ALL { instance.compartment.id = 'ocid1.compartment.oc1..example', resource.type = 'instance' }
```

Output:
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
          {
            "type": "clause",
            "node": {
              "lhs": "instance.compartment.id",
              "op": "eq",
              "rhs": {"type": "ocid", "value": "ocid1.compartment.oc1..example"}
            }
          },
          {
            "type": "clause",
            "node": {
              "lhs": "resource.type",
              "op": "eq",
              "rhs": {"type": "literal", "value": "instance"}
            }
          }
        ]
      }
    }
  ]
}
```

### RHS Type Examples (literal vs ocid vs regex)

Rule:
```
ALL {
  instance.compartment.id = 'ocid1.compartment.oc1..example',
  resource.type = 'instance',
  tag.team.env.value = /prod.*/
}
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
          {
            "type": "clause",
            "node": {
              "lhs": "instance.compartment.id",
              "op": "eq",
              "rhs": {"type": "ocid", "value": "ocid1.compartment.oc1..example"}
            }
          },
          {
            "type": "clause",
            "node": {
              "lhs": "resource.type",
              "op": "eq",
              "rhs": {"type": "literal", "value": "instance"}
            }
          },
          {
            "type": "clause",
            "node": {
              "lhs": "tag.team.env.value",
              "op": "eq",
              "rhs": {"type": "regex", "value": "/prod.*/", "pattern": "prod.*"}
            }
          }
        ]
      }
    }
  ]
}
```

### Exists Operator

Rule:
```
ALL { tag.department.operations.value }
```

Output:
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
          {
            "type": "clause",
            "node": {
              "lhs": "tag.department.operations.value",
              "op": "exists"
            }
          }
        ]
      }
    }
  ]
}
```

### Nested Mixed Modes (Note the SDK explains how to auto-reduce some structues where possible)

Rule:
```
ANY { tag.team.env.value = 'prod', ALL { tag.finance.costcenter.value != '1234' } }
```

Output:
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
          {
            "type": "clause",
            "node": {
              "lhs": "tag.team.env.value",
              "op": "eq",
              "rhs": {
                "type": "literal",
                "value": "prod"
              }
            }
          },
          {
            "type": "group",
            "mode": "all",
            "items": [
              {
                "type": "clause",
                "node": {
                  "lhs": "tag.finance.costcenter.value",
                  "op": "neq",
                  "rhs": {
                    "type": "literal",
                    "value": "1234"
                  }
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

---

## Additional Features

For behavior details and flags, see `docs/sdk/Dynamic_Group_SDK.md`:
- `nested_simplify` (same-mode flattening and single-child collapse)
- `include_spans` (adds `span` and `source_text`)
- `error_mode` (raise/report/ignore)
- list/tuple input handling (joined with `\n`)
