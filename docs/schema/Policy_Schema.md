# OCI Policy Statement JSON Schema (v1.0)

This document describes the normalized JSON output for OCI IAM policy statements after parsing, optional DEFINE substitutions, and optional identity-domain normalization.

---

## Top-Level Object

Top-level payload:

| Field | Type | Description |
|---|---|---|
| `schema_version` | `string` | Current schema version (`"1.0"`) |
| `statements` | `list[object]` | Parsed statement objects |
| `diagnostics` | `object` (optional) | Present when `error_mode="report"` |

Statement types and required keys (inside `statements`):

| Key | allow / deny | admit / deny_admit | endorse / deny_endorse | define |
|---|---|---|---|---|
| `kind` | required | required | required | required |
| `subject` | required | required | required | - |
| `actions` | required | required | required | - |
| `resources` | required | required | required | - |
| `location` | required | required | - | - |
| `source` | - | required | - | - |
| `target` | - | - | required | - |
| `symbol` | - | - | - | required |
| `def` | - | - | - | required |
| `conditions` | optional | optional | optional | - |
| `span` | optional | optional | optional | optional |
| `source_text` | optional | optional | optional | optional |

Notes:
- `subject.values` can contain multiple entries (for example, `group A, B`).
- `span` and `source_text` are included only when `include_spans=True`.
- `source` (object) is reserved for ADMIT source tenancy; `source_text` is separate span metadata.

---

## Core Objects

### `subject`

| Field | Type | Description |
|---|---|---|
| `type` | `string` | Principal category |
| `values` | `list[object]` | Each item has `label` and optional `identity_domain` |

`subject.type` values:

| Value | Meaning |
|---|---|
| `service` | OCI service principal |
| `group` | Group by name |
| `group-id` | Group by OCID |
| `dynamic-group` | Dynamic group by name |
| `dynamic-group-id` | Dynamic group by OCID |
| `any-user` | Wildcard for any user |
| `any-group` | Wildcard for any group |
| `unknown` | Fallback when unrecognized |

`subject.values` entry shape:

| Field | Type | Description |
|---|---|---|
| `label` | `string` | Name or OCID |
| `identity_domain` | `string` (optional) | Identity domain for `Domain/Name` or `default_identity_domain` |

**Examples:**

Service subject:
```
Allow service faas to read keys in tenancy
```
```json
"subject": {"type": "service", "values": [{"label": "faas"}]}
```

Group list:
```
Allow group Admins, Developers to manage all-resources in tenancy
```
```json
"subject": {
  "type": "group",
  "values": [{"label": "Admins"}, {"label": "Developers"}]
}
```

Group with identity domain:
```
Allow group CorpDom/Admins to read keys in tenancy
```
```json
"subject": {
  "type": "group",
  "values": [{"label": "Admins", "identity_domain": "CorpDom"}]
}
```

---

### `actions`

| Field | Type | Description |
|---|---|---|
| `type` | `string` | `verbs` or `permissions` |
| `values` | `list[string]` | Verb or permission values |

`actions.type` values:

| Value | Meaning |
|---|---|
| `verbs` | OCI verbs (`manage`, `use`, `read`, `inspect`, and `associate` in ENDORSE) |
| `permissions` | Permission names (from `{...}` or custom verb tokens) |
| `unknown` | Appears only when parsing errors prevent a valid action from being resolved |

**Examples:**

Verb:
```
Allow group Admins to read keys in tenancy
```
```json
"actions": {"type": "verbs", "values": ["read"]}
```

Permissions:
```
Allow service faas to {KEY_READ, KEY_WRITE} in tenancy
```
```json
"actions": {"type": "permissions", "values": ["key_read", "key_write"]}
```

---

### `resources`

| Field | Type | Description |
|---|---|---|
| `type` | `string` | `all-resources` or `specific` |
| `values` | `list[string]` | Empty for `all-resources`, otherwise resource family names |

**Examples:**

All resources:
```
Allow group Admins to manage all-resources in tenancy
```
```json
"resources": {"type": "all-resources", "values": []}
```

Specific resource family:
```
Allow group Admins to read buckets in tenancy
```
```json
"resources": {"type": "specific", "values": ["buckets"]}
```

Notes:
- `resources.type` may be `unknown` when syntax errors prevent a resource from being resolved.

---

### `location`

| Field | Type | Description |
|---|---|---|
| `type` | `string` | `tenancy`, `compartment_name`, `compartment-id`, `compartment-path`, or `unknown` |
| `values` | `list[string]` | Location values (path order preserved) |

**Examples:**

Tenancy:
```
Allow group Admins to read buckets in tenancy
```
```json
"location": {"type": "tenancy", "values": []}
```

Compartment name:
```
Allow group Admins to read buckets in compartment Apps
```
```json
"location": {"type": "compartment_name", "values": ["Apps"]}
```

Compartment path:
```
Allow group Admins to read buckets in compartment root:apps:prod
```
```json
"location": {"type": "compartment-path", "values": ["root", "apps", "prod"]}
```

Compartment OCID:
```
Allow group Admins to read buckets in compartment ocid1.compartment.oc1..aaaa
```
```json
"location": {"type": "compartment-id", "values": ["ocid1.compartment.oc1..aaaa"]}
```

Notes:
- `location.type` may be `unknown` when syntax errors prevent a location from being resolved.

---

### `source` (ADMIT)

| Field | Type | Description |
|---|---|---|
| `type` | `string` | `tenancy` or `tenancy_id` |
| `values` | `list[string]` | Tenancy alias or OCID values |

**Examples (no DEFINE substitution):**

Tenancy alias:
```
Admit group Admins of tenancy SrcTenancy to read buckets in tenancy
```
```json
"source": {"type": "tenancy", "values": ["SrcTenancy"]}
```

Note: `tenancy_id` appears only when `define_subs=True` resolves the alias to an OCID.

Notes:
- `source.type` may be `unknown` when syntax errors prevent a source from being resolved.

**Examples (with DEFINE substitution):**

Tenancy OCID:
```
Define tenancy SrcTenancy as ocid1.tenancy.oc1..src
Admit group Admins of tenancy SrcTenancy to read buckets in tenancy
```
```json
"source": {"type": "tenancy_id", "values": ["ocid1.tenancy.oc1..src"]}
```

---

### `target` (ENDORSE)

| Field | Type | Description |
|---|---|---|
| `type` | `string` | `any-tenancy`, `tenancy`, `tenancy_id`, or `unknown` |
| `values` | `list[string]` | Empty for `any-tenancy`, else alias or OCID |

**Examples (no DEFINE substitution):**

Any tenancy:
```
Endorse group Admins to manage all-resources in any-tenancy
```
```json
"target": {"type": "any-tenancy", "values": []}
```

Named tenancy:
```
Endorse group Admins to manage all-resources in tenancy ConsumerTenancy
```
```json
"target": {"type": "tenancy", "values": ["ConsumerTenancy"]}
```

Notes:
- `target.type` may be `unknown` when syntax errors prevent a target from being resolved.

Note: `tenancy_id` appears only when `define_subs=True` resolves the alias to an OCID.

**Examples (with DEFINE substitution):**

Tenancy OCID:
```
Define tenancy ConsumerTenancy as ocid1.tenancy.oc1..consumer
Endorse group Admins to manage all-resources in tenancy ConsumerTenancy
```
```json
"target": {"type": "tenancy_id", "values": ["ocid1.tenancy.oc1..consumer"]}
```

---

### `conditions`

Conditions appear only when a `WHERE` clause exists.

| Field | Type | Description |
|---|---|---|
| `type` | `string` | Always `group` |
| `mode` | `string` | `all` or `any` |
| `items` | `list[object]` | Clause or group nodes |

Clause object:

| Field | Type | Description |
|---|---|---|
| `type` | `string` | Always `clause` |
| `node` | `object` | Clause contents (see below) |

Clause node fields:

| Field | Type | Description |
|---|---|---|
| `lhs` | `string` | Attribute path, for example `request.region` |
| `op` | `string` | Normalized operator (see table below) |
| `rhs` | `object` | Typed right-hand value |

Operator mapping:

| Operator | Normalized `op` |
|---|---|
| `=` | `eq` |
| `!=` | `neq` |
| `IN (...)` | `in` |
| `BEFORE` | `before` |
| `AFTER` | `after` |
| `BETWEEN ... AND ...` | `between` |

`rhs.type` values:

| Type | Shape | Meaning |
|---|---|---|
| `literal` | `{ "type": "literal", "value": "GetKeyVersion" }` | Plain string or bare token |
| `ocid` | `{ "type": "ocid", "value": "ocid1.compartment.oc1..example" }` | OCI OCID value |
| `regex` | `{ "type": "regex", "value": "/__PSM*/", "pattern": "__PSM*" }` | Regex pattern |
| `list` | `{ "type": "list", "values": [ { "type": "literal", "value": "us-ashburn-1" }, ... ] }` | List of typed values |
| `range` | `{ "type": "range", "from": { "type": "literal", "value": "2024-01-01T00:00:00Z" }, "to": { "type": "literal", "value": "2024-12-31T23:59:59Z" } }` | Range for BETWEEN |

**Examples:**

**Flat conditions (literal, list, and range)**:
```
Allow group Admins to manage all-resources in tenancy where request.operation = 'GetKeyVersion'
and request.region in ('us-ashburn-1','us-phoenix-1')
and request.time between '2024-01-01T00:00:00Z' and '2024-12-31T23:59:59Z'
```
```json
"conditions": {
  "type": "group",
  "mode": "all",
  "items": [
    {"type": "clause", "node": {"lhs": "request.operation", "op": "eq", "rhs": {"type": "literal", "value": "GetKeyVersion"}}},
    {"type": "clause", "node": {"lhs": "request.region", "op": "in", "rhs": {"type": "list", "values": [
      {"type": "literal", "value": "us-ashburn-1"},
      {"type": "literal", "value": "us-phoenix-1"}
    ]}}},
    {"type": "clause", "node": {"lhs": "request.time", "op": "between", "rhs": {"type": "range",
      "from": {"type": "literal", "value": "2024-01-01T00:00:00Z"},
      "to": {"type": "literal", "value": "2024-12-31T23:59:59Z"}
    }}}
  ]
}
```

**Regex condition**:
```
Allow group Admins to manage all-resources in tenancy where target.user.name = /__PSM*/
```
```json
"conditions": {
  "type": "group",
  "mode": "all",
  "items": [
    {"type": "clause", "node": {"lhs": "target.user.name", "op": "eq", "rhs": {"type": "regex", "value": "/__PSM*/", "pattern": "__PSM*"}}}
  ]
}
```

**Nested conditions (mixed ANY/ALL) - Note: Per OCI docs not supported but still supported in this tool**:
```
Allow group Admins to manage all-resources in tenancy where any {
  request.region = 'us-ashburn-1',
  all { request.user.name = /__PSM*/ }
}
```
```json
"conditions": {
  "type": "group",
  "mode": "any",
  "items": [
    {"type": "clause", "node": {"lhs": "request.region", "op": "eq", "rhs": {"type": "literal", "value": "us-ashburn-1"}}},
    {"type": "group", "mode": "all", "items": [
      {"type": "clause", "node": {"lhs": "request.user.name", "op": "eq", "rhs": {"type": "regex", "value": "/__PSM*/", "pattern": "__PSM*"}}}
    ]}
  ]
}
```

---

### `symbol` and `def` (DEFINE)

`symbol`:

| Field | Type | Description |
|---|---|---|
| `type` | `string` | `tenancy`, `group`, `dynamic-group`, `compartment` |
| `name` | `string` | Alias name from the policy |

`def`:

| Field | Type | Description |
|---|---|---|
| `type` | `string` | Always `ocid` |
| `value` | `string` | OCID string |

Example:
```json
{
  "kind": "define",
  "symbol": {"type": "group", "name": "Admins"},
  "def": {"type": "ocid", "value": "ocid1.group.oc1..aaaa"}
}
```

---

## Examples

*Note*: "Deny" statements are optional features that can be enabled in a env and they just result in adding "deny" to the beginning of the statement for admin/endorse or switching "allow" to "deny" for the base use case: ex https://docs.oracle.com/en-us/iaas/Content/Identity/policysyntax/denypolicies.htm

### Allow / Deny

Policy:
```
Allow group Admins, Developers to manage all-resources in tenancy
```

Output:
```json
{
  "kind": "allow",
  "subject": {
    "type": "group",
    "values": [
      {"label": "Admins"},
      {"label": "Developers"}
    ]
  },
  "actions": {"type": "verbs", "values": ["manage"]},
  "resources": {"type": "all-resources", "values": []},
  "location": {"type": "tenancy", "values": []}
}
```

### Admit / Deny_Admit

Policy:
```
Admit group Admins of tenancy SrcTenancy to read buckets in compartment Apps
```

Output:
```json
{
  "kind": "admit",
  "subject": {"type": "group", "values": [{"label": "Admins"}]},
  "source": {"type": "tenancy", "values": ["SrcTenancy"]},
  "actions": {"type": "verbs", "values": ["read"]},
  "resources": {"type": "specific", "values": ["buckets"]},
  "location": {"type": "compartment_name", "values": ["Apps"]}
}
```

### Endorse / Deny_Endorse

Policy:
```
Endorse group Admins to manage all-resources in any-tenancy
```

Output:
```json
{
  "kind": "endorse",
  "subject": {"type": "group", "values": [{"label": "Admins"}]},
  "actions": {"type": "verbs", "values": ["manage"]},
  "resources": {"type": "all-resources", "values": []},
  "target": {"type": "any-tenancy", "values": []}
}
```

### Define

Policy:
```
Define group Admins as ocid1.group.oc1..aaaa
```

Output:
```json
{
  "kind": "define",
  "symbol": {"type": "group", "name": "Admins"},
  "def": {"type": "ocid", "value": "ocid1.group.oc1..aaaa"}
}
```

---

## Additional Features

For behavior details and flags, see `docs/sdk/Policy_SDK.md`:
- `define_subs` (DEFINE substitutions to OCIDs)
- `return_filter` (projection and selection)
- `include_spans` (source span metadata)
- `error_mode` (raise/report/ignore)
- `default_tenancy_alias` and `default_identity_domain`
- nested conditions (same‑mode flattening, controlled by `nested_simplify`)
- list/tuple input handling (joined with `\n`)
