"""CLI contract for keeping exploratory baseline runs out of canonical evidence."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def test_eval_baselines_exposes_explicit_output_path():
    """A smoke run must be able to avoid overwriting the canonical latest artifact."""
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "eval_baselines.py"), "--help"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    stderr = completed.stderr.decode("utf-8", errors="replace")
    stdout = completed.stdout.decode("utf-8", errors="replace")
    assert completed.returncode == 0, stderr
    assert "--out OUT" in stdout
