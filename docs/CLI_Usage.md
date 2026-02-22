# OCI Lexer Parser - CLI Guide

This guide covers `oci-lexer-parse` (alias: `oci-lexer-parser`): flags, output shapes, error behavior, and examples.

---

## Quick Start

```bash
# Parse a file and pretty-print JSON (policy statements)
oci-lexer-parse --policy policy.txt --pretty

# Stream statements as JSON Lines (one JSON object per line)
oci-lexer-parse --policy policy.txt --jsonl

# Handle huge files efficiently
oci-lexer-parse --policy policy.txt --chunked --jsonl

# Print only the symbol table (from DEFINE) and exit
oci-lexer-parse --policy policy.txt --symbols --pretty

# Parse dynamic group matching rules
oci-lexer-parse --dynamic-group rules.txt --pretty
```

Read from stdin by omitting the file or passing `-`:
```bash
cat policy.txt | oci-lexer-parse --policy - --jsonl
```

UTF-8 input is expected. UTF-8 with BOM is supported.

---

## Modes

Choose one:
- `--policy` for policy statements (default if no mode flag is set)
- `--dynamic-group` / `--dg` for dynamic group matching rules

`--policy` and `--dynamic-group` are mutually exclusive.

## Flags

Common flags:

| Flag | Type / Values | Default | Description |
|---|---|---:|---|
| `file` | positional or `-` | - | Input file to parse. Omit or pass `-` to read from stdin. |
| `--error-mode` | `raise` \/ `report` \/ `ignore` | `report` | Syntax error handling mode. |
| `--include-spans` | switch | off | Include source spans per statement or rule. |
| `--pretty` | switch | off | Pretty-print JSON output. |
| `--jsonl` | switch | off | Emit JSON Lines (one statement or rule per line). |
| `--diagnostics-file PATH` | path | - | Write diagnostics JSON to a file (useful with `--jsonl`). |
| `--version`, `-V` | switch | - | Show version and exit. |

Policy-only flags:

| Flag | Type / Values | Default | Description |
|---|---|---:|---|
| `--policy` | switch | off | Explicitly parse policy statements (default mode). |
| `--define-subs` | switch | off | Apply DEFINE substitutions where possible. |
| `--default-tenancy-alias NAME` | string | - | Fill `IN TENANCY` with `NAME`. |
| `--default-identity-domain NAME` | string | - | Default identity domain for group/dynamic-group subjects without `Domain/Name`. |
| `--chunked` | switch | off | Split input by statement starters to reduce memory usage. |
| `--symbols` | switch | off | Print only the DEFINE symbol table and exit. |

Dynamic-group-only flags:

| Flag | Type / Values | Default | Description |
|---|---|---:|---|
| `--dynamic-group`, `--dg` | switch | off | Parse dynamic group matching rules. |

---

## Output Shapes

| Mode | STDOUT shape |
|---|---|
| Default (policy) | `{ "schema_version": "1.0", "statements": [ ... ] }` |
| Default (dynamic-group) | `{ "schema_version": "1.0", "rules": [ ... ] }` |
| `--jsonl` | One JSON object per line (statement or rule) |
| `--error-mode report` and not JSONL | Includes `diagnostics` |
| `--symbols` | Symbol table object (policy mode only) |

Diagnostics can also be written to a file via `--diagnostics-file path.json`.

---

## Error Handling and Exit Codes

| Error mode | Behavior | Exit code |
|---|---|---|
| `raise` | Stops on first syntax error (exception) | non-zero |
| `report` | Returns statements plus diagnostics | `1` if any errors, else `0` |
| `ignore` | Best-effort parse without diagnostics | `0` |

When `--error-mode report` finds errors, the CLI prints a one-line summary to stderr.

---

## Examples

### Basic parse (pretty)
```bash
oci-lexer-parse --policy policy.txt --pretty
```

### JSON Lines (stream)
```bash
oci-lexer-parse --policy policy.txt --jsonl
```

### Chunked + JSONL (huge files)
```bash
oci-lexer-parse --policy big.txt --chunked --jsonl
```

### Diagnostics (report)
```bash
cat <<'POLICY' | oci-lexer-parse --policy - --error-mode report --pretty
Allow group Devs to read repos in tenancy

Alow group X to manage repos in tenancy
POLICY
```

### Dynamic group rules
```bash
cat <<'RULES' | oci-lexer-parse --dynamic-group - --pretty
ALL { resource.type = 'instance', instance.compartment.id = 'ocid1.compartment.oc1..example' }
RULES
```

### Separate diagnostics file (streaming)
```bash
oci-lexer-parse --policy policy.txt --chunked --jsonl --error-mode report \
  --diagnostics-file diags.json
```

---

## Version

```bash
oci-lexer-parse --version
```

Depending on install method, the CLI reads the version from installed package metadata. If unavailable, it prints `unknown`.
