from __future__ import annotations

from pathlib import Path

# Root anchor for test data
TESTS_DIR = Path(__file__).resolve().parents[1]
GOLDEN_DIR = TESTS_DIR / "fixtures" / "policy"

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def discover_txt(dir_path: Path) -> list[Path]:
    return sorted(dir_path.rglob("*.txt"))
