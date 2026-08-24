"""Paper evidence CLIs must let smoke runs avoid canonical evidence paths."""

import subprocess
import sys
from pathlib import Path


def test_paper_evidence_clis_expose_an_explicit_output_option():
    root = Path(__file__).resolve().parents[2]
    for relative_path in ("deliverables/paper/pipeline/qa/review_metrics.py", "tools/eval_e5.py"):
        completed = subprocess.run(
            [sys.executable, str(root / relative_path), "--help"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert "--out" in completed.stdout, relative_path
