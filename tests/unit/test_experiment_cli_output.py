"""每个实验脚本都必须提供 --out，使试跑可以避免覆盖 artifacts/runs/ 下的证据。"""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS = sorted(path for path in (ROOT / "experiments").glob("*.py") if path.name != "__init__.py")


def test_every_experiment_exposes_an_explicit_output_option():
    assert EXPERIMENTS
    for script in EXPERIMENTS:
        completed = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert "--out" in completed.stdout, script.name
