# OCI Lexer Parser

[![PyPI](https://img.shields.io/pypi/v/oci-lexer-parser.svg)](https://pypi.org/project/oci-lexer-parser/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/oci-lexer-parser.svg)](https://pypi.org/project/oci-lexer-parser/)
[![Unit Tests](https://github.com/NetSPI/oci-lexer-parser/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/NetSPI/oci-lexer-parser/actions/workflows/unit-tests.yml)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](https://github.com/NetSPI/oci-lexer-parser/blob/main/LICENSE.md)
[![Issues](https://img.shields.io/github/issues/NetSPI/oci-lexer-parser.svg)](https://github.com/NetSPI/oci-lexer-parser/issues)
[![Forks](https://img.shields.io/github/forks/NetSPI/oci-lexer-parser.svg)](https://github.com/NetSPI/oci-lexer-parser/network/members)
[![Stars](https://img.shields.io/github/stars/NetSPI/oci-lexer-parser.svg)](https://github.com/NetSPI/oci-lexer-parser/stargazers)

## Overview

> Note this SDK is used in "OCInferno", a tool to be released within the NetSPI repo by end of March for OCI enumeration and mapping.
> 
> In the spirit of full transparency, the development of the script was done with the help of LLM coding assistants. The assistant did most of the heavy lifting. As with any open-source tool, make sure that you review the  code to understand what its doing before you run it. That said, we've reviewed the code for any potential issues and welcome any changes via PR requests. See `Contributing.md` at the repo root.

OCI Lexer Parser converts human-readable OCI IAM statements and dynamic group rules into normalized JSON for analysis, testing, or transformation. It is built with built with ANTLR4 and Python.

See Credits below for the original groundwork in the area by Gordon Trevorrow.

---

## At a Glance

| Area | Details |
|---|---|
| Statement types | `ALLOW`, `DENY`, `DEFINE`, `ADMIT`, `ENDORSE` |
| Verbs and permissions | `manage`, `use`, `read`, `inspect`, plus `{PERMISSION}` lists |
| Subjects | `group`, `dynamic-group`, `service`, `any-user`, `any-group` |
| Locations | tenancy, compartment name, compartment path, compartment OCID |
| Conditions | `ANY` / `ALL` clauses, nested groups, same-mode flattening |
| Dynamic group rules | `ALL` / `ANY` groups, nested structures, strict LHS paths |
| Diagnostics | `raise`, `report`, or `ignore` error handling |
| Output normalization | DEFINE substitutions, identity domain enrichment, spans |

---

## TL;DR Quickstart (SDK)

Parse policy statements:
```python
import json
from oci_lexer_parser import parse_policy_statements

text = "allow group Admins to manage all-resources in tenancy"
statements = parse_policy_statements(text)["statements"]
print(json.dumps(statements[0], indent=2))
# Output:
# {
#   "kind": "allow",
#   "subject": {"type": "group", "values": [{"label": "Admins"}]},
#   "actions": {"type": "verbs", "values": ["manage"]},
#   "resources": {"type": "all-resources", "values": []},
#   "location": {"type": "tenancy", "values": []}
# }
```

Parse dynamic group rules:
```python
import json
from oci_lexer_parser import parse_dynamic_group_matching_rules

rules = parse_dynamic_group_matching_rules("ALL { resource.type = 'instance' }")["rules"]
print(json.dumps(rules[0], indent=2))
# Output:
# {
#   "mode": "ALL",
#   "level": 1,
#   "expr": {
#     "type": "group",
#     "mode": "all",
#     "items": [
#       {
#         "type": "clause",
#         "node": {
#           "lhs": "resource.type",
#           "op": "eq",
#           "rhs": {"type": "literal", "value": "instance"}
#         }
#       }
#     ]
#   }
# }
```

---

## Installation

Requires Python 3.10+.

### Option A: pip
```bash
pip install oci-lexer-parser
```

### Option B: Git clone (recommended for now)
```bash
git clone git@github.com:NetSPI/oci-lexer-parser.git
cd oci-lexer-parser
virtualenv .venv && source .venv/bin/activate
pip install -U pip
pip install .
```

Import name in Python:
```python
import oci_lexer_parser
```

Verify the CLI:
```bash
oci-lexer-parse --help
```

---

## SDK Examples

### Parse Policy Statements

Input:
```
Allow service faas to read keys in compartment f_compartment where request.operation='GetKeyVersion'
```

SDK:
```python
from oci_lexer_parser import parse_policy_statements

text = "Allow service faas to read keys in compartment f_compartment where request.operation='GetKeyVersion'"
payload, diagnostics = parse_policy_statements(text, error_mode="report")
print(payload)
```

Output:
```json
{
  "schema_version": "1.0",
  "statements": [
    {
      "kind": "allow",
      "subject": {"type": "service", "values": [{"label": "faas"}]},
      "actions": {"type": "verbs", "values": ["read"]},
      "resources": {"type": "specific", "values": ["keys"]},
      "location": {"type": "compartment_name", "values": ["f_compartment"]},
      "conditions": {
        "type": "group",
        "mode": "all",
        "items": [
          {
            "type": "clause",
            "node": {
              "lhs": "request.operation",
              "op": "eq",
              "rhs": {"type": "literal", "value": "GetKeyVersion"}
            }
          }
        ]
      }
    }
  ]
}
```

### Parse Dynamic Group Matching Rules

Input:
```
ALL { instance.compartment.id = 'ocid1.compartment.oc1..example', resource.type = 'instance' }
```

SDK:
```python
from oci_lexer_parser import parse_dynamic_group_matching_rules

payload = parse_dynamic_group_matching_rules(
    "ALL { instance.compartment.id = 'ocid1.compartment.oc1..example', resource.type = 'instance' }"
)
print(payload)
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

Notes:
- If the rule contains mixed nested modes (for example, `ANY { ..., ALL { ... } }`), output preserves structure under `expr`.
- Same-mode nesting is simplified only when `nested_simplify=True`.
- `expr` is always present; flat rules simply contain only `clause` items.

Conditions note:
- Condition RHS values are typed as `literal`, `ocid`, or `regex` (and lists/ranges are composed of those typed values).

---

## CLI Examples

Parse from stdin:
```bash
echo "Allow service faas to read keys in compartment f_compartment" | oci-lexer-parse --pretty
```

Parse a file with diagnostics:
```bash
oci-lexer-parse --error-mode report ./policy.txt --pretty
```

Stream JSON Lines:
```bash
oci-lexer-parse ./policy.txt --jsonl
```

---

## Docs

| Document | Purpose |
|---|---|
| `docs/CLI_Usage.md` | CLI flags, output shapes, and examples |
| `docs/Examples.md` | End-to-end OCI SDK examples with sample output |
| `docs/sdk/Policy_SDK.md` | Policy SDK usage and diagnostics |
| `docs/sdk/Dynamic_Group_SDK.md` | Dynamic group SDK usage and diagnostics |
| `docs/schema/Policy_Schema.md` | Policy statement JSON schema |
| `docs/schema/Dynamic_Group_Schema.md` | Dynamic group JSON schema |
| `docs/Roadmap.md` | Expected changes and future improvements |
| `Contributing.md` | Development workflow and tests |
| `LICENSE.md` | BSD 3-Clause license text |

---

## Dependencies

Runtime dependency:
```
antlr4-python3-runtime>=4.13.2,<4.14
```

---

## Contributing

See `Contributing.md`.

---

## Credits

- Built with ANTLR4 and the Python runtime
- Based on: [Unlocking the Power of ANTLR for Oracle Cloud IAM Policy Automation](https://www.ateam-oracle.com/post/unlocking-the-power-of-antlr-for-oracle-cloud-iam-policy-automation)

Author: Webbin Root
