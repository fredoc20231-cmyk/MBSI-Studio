"""Smoke test platform integration test."""

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def test_smoke_test_script():
    root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "smoke_test_platform.py")],
        capture_output=True,
        text=True,
        cwd=str(root),
    )
    assert result.returncode == 0, result.stderr
    assert "MBSI Studio smoke test passed." in result.stdout
    assert (root / "data" / "outputs" / "smoke_report.html").exists()
