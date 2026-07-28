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

from acceptance import PASS, NA, test_env, test_charter, test_invariants, test_known_answers, test_properties, test_differential, test_mesh_frontend, test_support_contact, test_capsule, test_direction_field, test_eval, test_data, test_dataset, test_fusion360, test_thingi, test_model, test_baselines, test_label_quality, test_viz, test_deferred

try:
    from support_accessibility import oracle
except ImportError:
    oracle = None

PENDING = "PENDING"


# 预算门冻结参（D-026）：D0=实测参考（机器无关，避免 gate 依赖机速）；MVP 规模=全量构建（D-021 冻结参）；
# 上限=单卡/单人一次性构建可容忍。门守护**规模膨胀**（改 _BUDGET_SCALE 使不可负担即红），非机速/算法放缓
# （后者由实验重跑 + eval.stage 计时暴露）。D0 重测（换机/改口径）时更新 _D0_REF_MS 并 append decisions。
_D0_REF_MS = 0.0596             # 实测：40 件 fusion360_full 纯体素单点单方向 ms（D-003 体素口径）
_BUDGET_SCALE = dict(n_models=8625, points_per_model=38, n_directions=128, n_radii=1)
_BUDGET_CEILING_H = 4.0         # 实测全量外推 ~0.69h，~6× 余量；外推超上限=预算回归


def budget_gate():
    """D-003 体素口径预算门（D-026）：冻结实测 D0 → eval.extrapolate 到 MVP 规模 → 比时间上限。
    机器无关（用冻结 D0，非 live 计时）；守护规模膨胀——超上限先换口径再降采样。"""
    try:
        from support_accessibility.eval import extrapolate_oracle_cost
    except ImportError as e:
        return {"name": "oracle_budget", "status": PENDING, "detail": f"依赖未就绪：{e}"}
    hours = extrapolate_oracle_cost(_D0_REF_MS, **_BUDGET_SCALE)
    ok = hours <= _BUDGET_CEILING_H
    return {"name": "oracle_budget", "status": PASS if ok else "FAIL",
            "detail": f"D0(实测)={_D0_REF_MS}ms × {_BUDGET_SCALE['n_models']}件×{_BUDGET_SCALE['points_per_model']}点×"
                      f"{_BUDGET_SCALE['n_directions']}向 → 全量外推 {hours:.2f}h ≤ 上限 {_BUDGET_CEILING_H}h（D-026）"}


def regression_gate():
    """回归门（D-026）：读 tools/regression_check.py 产出（模型级配对 + bootstrap CI）。神经二分显著**不劣于
    最强几何基线**（射线可见性 E4；配对差 95%CI 下界 >0）→ PASS；含 0/负 → FAIL；无产出（未跑实验）→ PENDING。
    产出在 runs/（机器 emit、gitignore），故裸克隆 PENDING、跑实验后棘轮。"""
    path = os.path.join(_ROOT, "runs", "regression", "latest.json")
    if not os.path.exists(path):
        return {"name": "regression", "status": PENDING,
                "detail": "未见回归产出——跑 `tools/regression_check.py` 生成 runs/regression/latest.json（D-026）"}
    try:
        with open(path, encoding="utf-8") as f:
            r = json.load(f)
    except (OSError, ValueError) as e:
        return {"name": "regression", "status": PENDING, "detail": f"回归产出读失败：{e}"}
    ok = bool(r.get("diff_ci_low", -1) > 0)
    return {"name": "regression", "status": PASS if ok else "FAIL",
            "detail": f"神经 F1 {r.get('neural_f1')} vs 几何基线 {r.get('baseline_f1')}，模型级配对差 95%CI "
                      f"[{r.get('diff_ci_low')},{r.get('diff_ci_high')}] {'>0 显著胜' if ok else '含0/负—回归'}（D-026）"}


def label_audit_gate():
    """真实标签有效性**命门门**（D-025 / 铁律#7）：机械复核 fusion360_full 的 label_audit 裁定，而非只靠散文。
    verdict_pass 且 human_signoff → PASS；未过 → FAIL；无产物（裸克隆/未跑审核）→ PENDING（诚实活检，同 regression）。
    数据集 gitignore（机器 emit），跑 `tools/audit_labels.py --write` 后棘轮。"""
    path = os.path.join(_ROOT, "data", "processed", "fusion360_full", "dataset.json")
    if not os.path.exists(path):
        return {"name": "label_audit", "status": PENDING,
                "detail": "未见真实数据集 dataset.json——跑 `tools/audit_labels.py --write` 生成 label_audit（D-025）"}
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError) as e:
        return {"name": "label_audit", "status": PENDING, "detail": f"dataset.json 读失败：{e}"}
    la = d.get("label_audit")
    if not la:
        return {"name": "label_audit", "status": PENDING,
                "detail": "dataset.json 无 label_audit 块——跑 `tools/audit_labels.py --write`（D-025）"}
    ok = bool(la.get("verdict_pass")) and bool(d.get("human_signoff"))
    diff = la.get("differential", {}); stab = la.get("res_stability", {})
    return {"name": "label_audit", "status": PASS if ok else "FAIL",
            "detail": f"真实标签审核 verdict={la.get('verdict_pass')}/signoff={d.get('human_signoff')}："
                      f"robust 差分 {diff.get('robust_mismatch_rate')} / res稳定 {(stab or {}).get('res48_vs_res96_agreement')}（D-025）"}


def build_verdict():
    acceptance = []
    # test_env / test_charter 在前：它们现在就应绿，其余几何性质 PENDING
    for mod in (test_env, test_charter, test_invariants, test_known_answers, test_properties, test_differential, test_mesh_frontend, test_support_contact, test_capsule, test_direction_field, test_eval, test_data, test_dataset, test_fusion360, test_thingi, test_model, test_baselines, test_label_quality, test_viz, test_deferred):
        acceptance += mod.checks()
    gates = [budget_gate(), regression_gate(), label_audit_gate()]
    # GREEN = 无 FAIL 且无 PENDING（N/A 是终态、非待办、不阻塞——决定为非不变量/已覆盖，见 D-027）
    ok_states = (PASS, NA)
    all_pass = (all(c["status"] in ok_states for c in acceptance)
                and all(g["status"] in ok_states for g in gates))
    return {
        "overall": "GREEN" if all_pass else "RED",
        "oracle_implemented": bool(oracle and getattr(oracle, "IMPLEMENTED", False)),
        "summary": dict(Counter(x["status"] for x in acceptance + gates)),
        "acceptance": acceptance,
        "gates": gates,
    }


_ICON = {"PASS": "✅", "FAIL": "❌", "PENDING": "⏳", "N/A": "➖"}


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
