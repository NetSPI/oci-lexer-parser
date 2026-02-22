from __future__ import annotations

import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SUPPORT_DIR = TESTS_DIR / "support"

# Ensure src/tests and src/tests/support are importable (for helpers, etc.)
for p in (TESTS_DIR, SUPPORT_DIR):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)
