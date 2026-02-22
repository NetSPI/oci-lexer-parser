from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from helpers import read_text

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
FIXTURES = Path(__file__).parent / "fixtures" / "cli"
DG_FIXTURES = Path(__file__).parent / "fixtures" / "dynamic_group"


def run_cli(args, input_text=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        f"{SRC_DIR}{os.pathsep}{env['PYTHONPATH']}" if "PYTHONPATH" in env else str(SRC_DIR)
    )
    return subprocess.run(
        [sys.executable, "-m", "oci_lexer_parser.cli", *args],
        text=True,
        input=input_text,
        capture_output=True,
        check=False,
        env=env,
        cwd=str(REPO_ROOT),
    )


def test_cli_parses_stdin():
    text = read_text(FIXTURES / "01_simple.txt")
    proc = run_cli(["--pretty", "--jsonl"], input_text=text)
    assert proc.returncode == 0
    assert '"kind": "allow"' in proc.stdout
    assert proc.stderr == ""


def test_cli_policy_mode_explicit():
    text = read_text(FIXTURES / "01_simple.txt")
    proc = run_cli(["--policy", "--pretty"], input_text=text)
    assert proc.returncode == 0
    assert '"kind": "allow"' in proc.stdout


def test_cli_file_path(tmp_path: Path):
    p = tmp_path / "policy.txt"
    p.write_text(read_text(FIXTURES / "04_define_tenancy.txt"), encoding="utf-8")
    proc = run_cli(["--symbols", str(p)])
    assert proc.returncode == 0
    assert '"tenancy"' in proc.stdout
    assert '"T"' in proc.stdout


def test_cli_reports_errors_json():
    bad = read_text(FIXTURES / "05_bad_statement.txt")  # malformed on purpose
    proc = run_cli(["--error-mode", "report"], input_text=bad)

    assert proc.returncode == 1
    assert "diagnostics" in proc.stdout


def test_cli_chunked_reports_errors_json():
    bad = read_text(FIXTURES / "05_bad_statement.txt")  # malformed on purpose
    proc = run_cli(["--error-mode", "report", "--chunked"], input_text=bad)

    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert "diagnostics" in payload
    assert "errors" in payload["diagnostics"]


def test_cli_dynamic_group_mode():
    text = read_text(FIXTURES / "03_dynamic_group_matching_rules.txt")
    proc = run_cli(["--dynamic-group", "--pretty"], input_text=text)
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert "rules" in payload
    assert payload["rules"][0]["expr"]["type"] == "group"


def test_cli_dynamic_group_jsonl():
    text = read_text(FIXTURES / "03_dynamic_group_matching_rules.txt")
    proc = run_cli(["--dynamic-group", "--jsonl"], input_text=text)
    assert proc.returncode == 0
    first = proc.stdout.splitlines()[0]
    obj = json.loads(first)
    assert "expr" in obj


def test_cli_dynamic_group_report_includes_diagnostics():
    text = read_text(DG_FIXTURES / "13_error_missing_brace.txt")
    proc = run_cli(["--dynamic-group", "--error-mode", "report", "--pretty"], input_text=text)
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert "diagnostics" in payload
    assert payload["diagnostics"]["error_count"] >= 1


def test_cli_rejects_both_modes():
    text = read_text(FIXTURES / "01_simple.txt")
    proc = run_cli(["--policy", "--dynamic-group"], input_text=text)
    assert proc.returncode == 2
    assert "Choose only one" in proc.stderr


def test_cli_dynamic_group_rejects_chunked():
    text = read_text(FIXTURES / "03_dynamic_group_matching_rules.txt")
    proc = run_cli(["--dynamic-group", "--chunked"], input_text=text)
    assert proc.returncode == 2
    assert "--chunked is not supported" in proc.stderr


def test_cli_dynamic_group_rejects_symbols():
    text = read_text(FIXTURES / "03_dynamic_group_matching_rules.txt")
    proc = run_cli(["--dynamic-group", "--symbols"], input_text=text)
    assert proc.returncode == 2
    assert "--symbols is not supported" in proc.stderr
