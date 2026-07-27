"""tests/gate.py — 验收裁决门（棘轮）。

汇总 charter/decisions.md 冻结决策对应的性质 + 两道门 → JSON 裁决 + 退出码。
零安装可跑：`python tests/gate.py`（延续"会跑、可全红"）。几何性质在 oracle 实现前 PENDING；
文档机检（test_charter）现在就应绿——证明治理散文这层当场有牙。

门（对应决策与量化阶段门）：
  预算门   D0 实测单点单方向 ms → eval.extrapolate → 超上限先换口径再降采样
  回归门   阶段5固化后:模型级配对 + bootstrap CI 不劣于最强几何基线
  棘轮     绿了的性质不许静默退绿；放松须 append decisions
"""

import json
import os
import sys
from collections import Counter

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")  # torch+scipy OMP 重复运行时保护（见 conftest.py）

_HERE = os.path.dirname(os.path.abspath(__file__))     # tests/
_ROOT = os.path.dirname(_HERE)                          # repo root
for _p in (os.path.join(_ROOT, "src"), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from acceptance import PASS, test_env, test_charter, test_invariants, test_known_answers, test_properties, test_differential, test_mesh_frontend, test_support_contact, test_capsule, test_direction_field, test_eval, test_data, test_dataset, test_fusion360, test_thingi, test_model, test_baselines, test_label_quality, test_viz, test_deferred

try:
    from support_accessibility import oracle
except ImportError:
    oracle = None

PENDING = "PENDING"


def budget_gate():
    return {"name": "oracle_budget", "status": PENDING,
            "detail": "需 D0 实测单点单方向 ms 后外推（D-003 体素口径）"}


def regression_gate():
    return {"name": "regression", "status": PENDING,
            "detail": "阶段5指标固化后启用（模型级配对 + bootstrap CI）"}


def build_verdict():
    acceptance = []
    # test_env / test_charter 在前：它们现在就应绿，其余几何性质 PENDING
    for mod in (test_env, test_charter, test_invariants, test_known_answers, test_properties, test_differential, test_mesh_frontend, test_support_contact, test_capsule, test_direction_field, test_eval, test_data, test_dataset, test_fusion360, test_thingi, test_model, test_baselines, test_label_quality, test_viz, test_deferred):
        acceptance += mod.checks()
    gates = [budget_gate(), regression_gate()]
    all_pass = (all(c["status"] == PASS for c in acceptance)
                and all(g["status"] == PASS for g in gates))
    return {
        "overall": "GREEN" if all_pass else "RED",
        "oracle_implemented": bool(oracle and getattr(oracle, "IMPLEMENTED", False)),
        "summary": dict(Counter(x["status"] for x in acceptance + gates)),
        "acceptance": acceptance,
        "gates": gates,
    }


_ICON = {"PASS": "✅", "FAIL": "❌", "PENDING": "⏳"}


def render_markdown(verdict):
    """把裁决渲染为 markdown（供 CI job summary / 本地 --format md）。状态生成、非手抄。"""
    lines = [f"# SAF 验收裁决 — **{verdict['overall']}**", "",
             f"`{verdict['summary']}`　oracle_implemented={verdict['oracle_implemented']}", "",
             "| 状态 | 检查 | 详情 |", "|---|---|---|"]
    for c in verdict["acceptance"] + verdict["gates"]:
        lines.append(f"| {_ICON.get(c['status'], c['status'])} {c['status']} | `{c['name']}` | {c['detail']} |")
    return "\n".join(lines)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")   # Windows 控制台默认非 UTF-8
    except (AttributeError, ValueError):
        pass
    argv = sys.argv[1:]
    fmt = "json"
    if "--format" in argv:
        j = argv.index("--format")
        fmt = argv[j + 1] if j + 1 < len(argv) else "json"
    verdict = build_verdict()
    print(render_markdown(verdict) if fmt == "md" else json.dumps(verdict, ensure_ascii=False, indent=2))
    sys.exit(0 if verdict["overall"] == "GREEN" else 1)


if __name__ == "__main__":
    main()
