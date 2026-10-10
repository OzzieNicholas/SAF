#!/usr/bin/env python3
"""按规范参数依次运行全部实验，生成论文和结果账本所依据的证据（artifacts/runs/<实验名>/result.json）。

规范参数只在这里登记一次；结果账本和论文证据清单引用实验名，不再各自抄写命令。
实验按耗时由短到长排列，GPU 训练类实验顺序执行，不并发。

用法：
  python tools/reproduce_experiments.py --list
  python tools/reproduce_experiments.py                       # 全部
  python tools/reproduce_experiments.py --only baseline_comparison,regression_check
"""

import argparse
from pathlib import Path
import subprocess
import sys
import time

from support_accessibility.runtime.data_paths import REPO_ROOT, resolve_data_paths

# (实验名, 命令行参数)。参数中的 {fusion_root} 由数据路径配置解析。
CANONICAL_RUNS = (
    ("support_area_vs_accessibility", []),
    ("tool_radius_effect", []),
    ("inference_speed", []),
    ("label_audit", ["--write"]),
    ("oracle_differential_audit", ["--cases", "10000"]),
    ("mesh_quality_audit", []),
    ("true_triangle_area_check", []),
    ("baseline_comparison", ["--max-models", "400", "--epochs", "80", "--tiny-epochs", "300", "--seed", "0"]),
    ("regression_check", ["--max-models", "400", "--epochs", "80", "--seed", "0", "--n-boot", "2000"]),
    ("shape_context_ablation", ["--max-models", "400", "--epochs", "60", "--seed", "0"]),
    ("failure_analysis", ["--max-models", "400", "--epochs", "80", "--seed", "0", "--seeds", "5",
                          "--figure-case", "116082_b59d8605_0002"]),
    ("cross_model_prediction", ["--seeds", "5", "--epochs", "80"]),
    ("cross_domain_robustness", ["--seeds", "3", "--epochs", "80"]),
    ("direction_field_audit", ["--max-models", "500"]),
    ("direction_field_prediction", ["--max-models", "500", "--seeds", "3", "--epochs", "100",
                                    "--root", "{fusion_root}"]),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true", help="只列出规范运行")
    parser.add_argument("--only", default="", help="逗号分隔的实验名；缺省运行全部")
    args = parser.parse_args()

    selected = {name for name in args.only.split(",") if name}
    known = {name for name, _ in CANONICAL_RUNS}
    if selected - known:
        parser.error(f"未知实验：{sorted(selected - known)}")
    fusion_root = str(resolve_data_paths().fusion360_root)

    for name, options in CANONICAL_RUNS:
        if selected and name not in selected:
            continue
        command = [sys.executable, str(Path("experiments") / f"{name}.py"),
                   *[option.format(fusion_root=fusion_root) for option in options]]
        if args.list:
            print(name, *options)
            continue
        print(f"== {name}", flush=True)
        started = time.perf_counter()
        completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
        print(f"== {name} 用时 {time.perf_counter() - started:.0f}s，退出码 {completed.returncode}", flush=True)
        if completed.returncode:
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
