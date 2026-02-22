# OCI SDK Examples

This page collects practical examples using the OCI Python SDK together with
`oci_lexer_parser` to parse IAM policies and dynamic group matching rules.

Note: The examples below use hardcoded OCIDs for clarity. Feel free to adapt
them to your environment, review the OCI Python SDK docs, or watch for
NetSPI’s planned OCInferno release (targeting March 2026) for additional
workflow helpers.

## Authentication Setup (OCI SDK)

A OCI python script is given below to show how to ingest and filter statments/matching rules to the SDK and get the JSON output. Note authentication can be found via the OCI references here: https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm

## Example 1: Policy Statements for a Specific Compartment (by OCID)

This script:
1. Loads the OCI config file.
2. Uses a hardcoded compartment OCID.
3. Lists policies in that compartment.
4. Parses all policy statements with `parse_policy_statements`.

```python
from __future__ import annotations

import oci
from oci.pagination import list_call_get_all_results

from oci_lexer_parser import parse_policy_statements

config = oci.config.from_file()
identity = oci.identity.IdentityClient(config)

# Replace with your compartment OCID:
target_compartment_id = "ocid1.compartment.oc1..example"

# Example statements we expect to see in this compartment:
# 1) Allow group Admins to manage all-resources in compartment Apps
# 2) Allow any-user to read buckets in compartment Apps
# 3) Allow service faas to read keys in compartment Apps
# 4) Deny group Contractors to manage all-resources in compartment Apps

policies = list_call_get_all_results(
    identity.list_policies,
    compartment_id=target_compartment_id,
).data

for policy in policies:
    payload = parse_policy_statements(policy.statements or [])
    print(
        {
            "compartment_id": target_compartment_id,
            "policy": policy.name,
            "statements": policy.statements or [],
            "parsed": payload["statements"],
        }
    )
```

Sample output:
```json
{
  "compartment_id": "ocid1.compartment.oc1..example",
  "policy": "SecurityBaseline",
  "statements": [
    "Allow group Admins to manage all-resources in compartment Apps",
    "Allow any-user to read buckets in compartment Apps"
  ],
  "parsed": [
    {
      "kind": "allow",
      "subject": {"type": "group", "values": [{"label": "Admins"}]},
      "actions": {"type": "verbs", "values": ["manage"]},
      "resources": {"type": "all-resources", "values": []},
      "location": {"type": "compartment-name", "values": ["Apps"]}
    },
    {
      "kind": "allow",
      "subject": {"type": "any-user", "values": []},
      "actions": {"type": "verbs", "values": ["read"]},
      "resources": {"type": "specific", "values": ["buckets"]},
      "location": {"type": "compartment-name", "values": ["Apps"]}
    }
  ]
}
```

## Example 2: Dynamic Group Rules for a Specific Dynamic Group (by OCID)

This script:
1. Loads the OCI config file.
2. Uses a hardcoded dynamic group OCID.
3. Parses the stored matching rule with `parse_dynamic_group_matching_rules`.

```python
from __future__ import annotations

import oci

from oci_lexer_parser import parse_dynamic_group_matching_rules

config = oci.config.from_file()
identity = oci.identity.IdentityClient(config)

# Replace with your dynamic group OCID:
target_dynamic_group_id = "ocid1.dynamicgroup.oc1..example"

# Example matching rules we expect to see on this dynamic group:
# 1) ALL { resource.type = 'instance', instance.compartment.id = 'ocid1.compartment.oc1..example' }
# 2) ANY { tag.team.env.value = 'prod', ALL { resource.type = 'bucket' } }

target = identity.get_dynamic_group(target_dynamic_group_id).data
payload = parse_dynamic_group_matching_rules(target.matching_rule or "")
print(
    {
        "dynamic_group_id": target_dynamic_group_id,
        "matching_rule": target.matching_rule or "",
        "parsed": payload["rules"],
    }
)
```

Sample output:
```json
{
  "dynamic_group_id": "ocid1.dynamicgroup.oc1..example",
  "matching_rule": "ALL { resource.type = 'instance', instance.compartment.id = 'ocid1.compartment.oc1..example' }",
  "parsed": [
    {
      "level": 1,
      "expr": {
        "type": "group",
        "mode": "all",
        "items": [
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
              "lhs": "instance.compartment.id",
              "op": "eq",
              "rhs": {"type": "ocid", "value": "ocid1.compartment.oc1..example"}
            }
          }
        ]
      }
    }
  ]
}
```
