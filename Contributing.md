# Contributing and Development Guide

Thank you for helping improve OCI Lexer Parser.

---

## Important Note

OCI may accept and save a policy statement or dynamic group rule in teh web UI even if it is ineffective or contains subtle issues. Before filing an issue, validate that the statement or rule actually enforces the behavior you expect (and isn’t failing silently due to syntax issues).

---

## Reporting an Issue

Include the following details:

| Item | Description |
|---|---|
| Impacted sentence | Full policy statement or rule |
| Where it occurs | CLI, SDK, tests |
| Steps to reproduce | Command or Python snippet |
| Expected behavior | What should happen |
| Actual behavior | What happened |
| Environment | OS, Python version, parser version |

Example:
```
Impacted sentence:
Allow dynamic-group DG_Prod to manage all-resources in tenancy

Where it occurs:
CLI - oci-lexer-parse --pretty

Steps to reproduce:
1. Paste the sentence above into a file
2. Run: oci-lexer-parse policy.txt --pretty

Expected behavior:
Should classify 'DG_Prod' as a dynamic-group

Actual behavior:
Classified as 'group'

Environment:
Python 3.12, parser v1.0.0, macOS
```

---

## Project Structure

| Path | Purpose |
|---|---|
| `src/oci_lexer_parser/grammar/PolicyStatement.g4` | Policy grammar (source of truth) |
| `src/oci_lexer_parser/grammar/DynamicGroupMatchingRule.g4` | Dynamic group grammar |
| `src/oci_lexer_parser/grammar/gen/` | Generated lexer/parser (See ANTLR JAR below) |
| `src/oci_lexer_parser/parser_policy_statements.py` | Policy shaping and diagnostics |
| `src/oci_lexer_parser/parser_dynamic_group_matching_rules.py` | Dynamic group parsing |
| `src/oci_lexer_parser/cli.py` | CLI entrypoint for both policies and dynmaic groups |
| `src/tests/` | Unit tests and fixtures |

---

## Local Setup

To perform testing/development you need the python packages below. Basically the two dependencies in pyproject.toml (`pytest` and `antlr4-python3-runtime` if you want to install them individually with `pip`)

```bash
virtualenv test_venv && source test_venv/bin/activate
pip install -U pip
pip install .[dev]
```

---

## Regenerate ANTLR Artifacts

If you edit the *.g4 files as part of your modifications you need to re-generate the Python files in the gen/ folder. To do so you need to download the ANTLR Java Jar and run them against your modified *.g4 files. if you have to modify the *.g4 files its probably better filing an issue (see above) to prompt a fix. Stillcommands and references provided below in case you want to modify it:

```bash
java -jar src/oci_lexer_parser/grammar/antlr-4.13.2-complete.jar \
  -Dlanguage=Python3 \
  -o src/oci_lexer_parser/grammar/gen \
  src/oci_lexer_parser/grammar/PolicyStatement.g4

java -jar src/oci_lexer_parser/grammar/antlr-4.13.2-complete.jar \
  -Dlanguage=Python3 \
  -o src/oci_lexer_parser/grammar/gen \
  src/oci_lexer_parser/grammar/DynamicGroupMatchingRule.g4
```

Commit the generated files if your CI does not regenerate them. Note the SHA256 sum of the JAR I used to compile the gen files is as follows: `eae2dfa119a64327444672aff63e9ec35a20180dc5b8090b7a6ab85125df4d76`

Download References:
- https://www.antlr.org/download.html
- https://github.com/antlr/antlr4/blob/master/doc/java-target.md
- https://github.com/antlr/antlr4/blob/master/doc/python-target.md
- https://www.antlr.org/download/antlr-4.13.2-complete.jar
---

## Example: Grammar Change Walkthrough (PolicyStatement.g4)

This is a small, end-to-end example showing how a typical grammar change flows from fork to PR.

1. Fork the repo on GitHub.
2. Clone your fork and create a branch:
   ```bash
   git clone git@github.com:<your-username>/oci-lexer-parser.git
   cd oci-lexer-parser
   git checkout -b grammar-update
   ```
3. Create a virtualenv and install dev deps:
   ```bash
   virtualenv .venv && source .venv/bin/activate
   pip install -U pip
   pip install .[dev]
   ```
4. Edit the grammar:
   ```bash
   # example: add/adjust a rule in PolicyStatement.g4
   $EDITOR src/oci_lexer_parser/grammar/PolicyStatement.g4
   ```
5. Regenerate the ANTLR artifacts:
   ```bash
   java -jar src/oci_lexer_parser/grammar/antlr-4.13.2-complete.jar \
     -Dlanguage=Python3 \
     -o src/oci_lexer_parser/grammar/gen \
     src/oci_lexer_parser/grammar/PolicyStatement.g4
   ```
6. Run tests. Add tests to the test/ folder if your changes cover a new use case:
   ```bash
   python -m pytest -q -m "not generate_json"
   ```
7. Update fixtures (if the output shape changed). This should be pretty rare as we already generated the golden use cases but can be used if you are addig new use cases:
   ```bash
   GENERATE_JSON=1 python -m pytest -q -m generate_json
   ```
8. Commit and push:
   ```bash
   git add src/oci_lexer_parser/grammar/PolicyStatement.g4 src/oci_lexer_parser/grammar/gen
   git commit -m "Update PolicyStatement grammar"
   git push origin grammar-update
   ```
9. Open a PR from your fork into `NetSPI/oci-lexer-parser` and include:
   - the new grammar behavior
   - any fixture updates
   - before/after examples

---

## Tests

| Task | Command |
|---|---|
| Run unit tests | `python -m pytest -q -m "not generate_json"` |
| Generate JSON outputs | `GENERATE_JSON=1 python -m pytest -q -m generate_json` |

Generated JSON files are written alongside the fixture `.txt` files under `src/tests/fixtures/` (policy, dynamic_group, and cli).

Test modules:

| File | Purpose |
|---|---|
| `src/tests/test_policy.py` | Policy statement parsing (core behavior) |
| `src/tests/test_dynamic_group.py` | Dynamic group matching rules |
| `src/tests/test_cli.py` | CLI smoke tests |
| `src/tests/test_fixtures.py` | Fixture-driven parsing and validation |

Fixtures layout:

| Path | Purpose |
|---|---|
| `src/tests/fixtures/cli/` | CLI input samples |
| `src/tests/fixtures/policy/valid_subs/` | Valid policy samples with DEFINE substitutions |
| `src/tests/fixtures/policy/examples/` | Curated real-world samples |
| `src/tests/fixtures/policy/edge/` | Edge parsing cases |
| `src/tests/fixtures/policy/error/` | Inputs expected to error |
| `src/tests/fixtures/policy/matrix/` | Expanded matrix split by statement type |
| `src/tests/fixtures/dynamic_group/` | Dynamic group fixtures |

---

## CI (GitHub Actions)

Tests in relation to 1800+ unit test cases run automatically on every push and pull request (including those from Dependabot) to ensure no regressive issues. 

Publishing to the PyPi repo is only manually invoked from the NetSPI side restricting publish access to the appropriate audience.

## Dependabot

This repo uses Dependabot for security updates with version updates being triggered once a week. Security PRs are created as soon as a vulnerability is detected. Make sure to pull and merge any changes before submitting your PR in case Dependabot made any updates.

---
