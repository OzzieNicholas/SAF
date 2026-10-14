"""tests/gate.py — 验收裁决门（棘轮）。

汇总 governance/决策台账.md 冻结决策对应的性质 + 两道门 → JSON 裁决 + 退出码。
零安装可跑：`python tests/gate.py`（延续"会跑、可全红"）。几何性质在 oracle 实现前 PENDING；
文档机检（test_governance）现在就应绿——证明治理散文这层当场有牙。

门：
  预算门   D0 实测单点单方向 ms → eval.extrapolate → 超上限先换口径再降采样
  回归门   模型级配对 + bootstrap CI 不劣于最强几何基线
  棘轮     绿了的性质不许静默退绿；放松须 append decisions
"""

import json
import os
import sys
from collections import Counter

from support_accessibility.runtime.console import setup_console

setup_console()                                        # torch+scipy OMP 重复运行时保护、终端 UTF-8

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo root
if _ROOT not in sys.path:                              # 作为脚本运行时，使 paper 包可导入
    sys.path.insert(0, _ROOT)

from acceptance import PASS, NA, test_env, test_governance, test_invariants, test_known_answers, test_properties, test_differential, test_mesh_frontend, test_support_contact, test_capsule, test_direction_field, test_eval, test_procedural_cases, test_dataset, test_fusion360, test_thingi, test_model, test_baselines, test_label_quality, test_figure_face_mapping

PENDING = "PENDING"


# 预算门冻结参（D-026）：D0=实测参考（机器无关，避免 gate 依赖机速）；MVP 规模=全量构建（D-021 冻结参）；
# 上限=单卡/单人一次性构建可容忍。门守护**规模膨胀**（改 _BUDGET_SCALE 使不可负担即红），非机速/算法放缓
# （后者由实验重跑 + eval.stage 计时暴露）。D0 重测（换机/改口径）时更新 _D0_REF_MS 并 append decisions。
_D0_REF_MS = 0.0596             # 实测：40 件 fusion360 纯体素单点单方向 ms（D-003 体素口径）
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
    """回归门（D-026）：读 experiments/baseline_comparison.py 的产出。形状条件网络相对零半径射线的逐件配对差
    95% bootstrap 区间下界 > 0 → PASS；否则 FAIL。无产出、或产出记录的数据摘要与当前数据不一致 → PENDING。"""
    path = os.path.join(_ROOT, "artifacts", "runs", "baseline_comparison", "result.json")
    run = "跑 `experiments/baseline_comparison.py`（D-026）"
    if not os.path.exists(path):
        return {"name": "regression", "status": PENDING, "detail": f"未见基线对照产出——{run}"}
    try:
        with open(path, encoding="utf-8") as f:
            r = json.load(f)
    except (OSError, ValueError) as e:
        return {"name": "regression", "status": PENDING, "detail": f"基线对照产出读失败：{e}"}
    from support_accessibility.eval import data_digest
    from support_accessibility.runtime.data_paths import resolve_data_paths, resolve_logical_data_ref
    paths = resolve_data_paths()
    current = data_digest(*[str(resolve_logical_data_ref(ref, paths)) for ref in r.get("data_roots", [])])
    if r.get("data_digest") != current:
        return {"name": "regression", "status": PENDING,
                "detail": f"基线对照产出过期（数据摘要 {r.get('data_digest')} ≠ 当前 {current}）——{run}"}
    delta = r["paired_delta_convonet_minus_ray"]
    ok = delta["ci95"][0] > 0
    methods = r["methods"]
    return {"name": "regression", "status": PASS if ok else "FAIL",
            "detail": f"网络 F1 {methods['convonet']['f1_overall']} vs 零半径射线 {methods['ray_visibility']['f1_overall']}，"
                      f"逐件配对差 {delta['mean']}，95% 区间 {delta['ci95']}（D-026）"}


def label_audit_gate():
    """真实标签有效性**命门门**（D-025 / 铁律#7）：机械复核 fusion360 的 label_audit 裁定，而非只靠散文。
    verdict_pass 且 human_signoff → PASS；未过 → FAIL；无产物（裸克隆/未跑审核）→ PENDING（诚实活检，同 regression）。
    数据集 gitignore（机器 emit），跑 `experiments/label_audit.py --write` 后棘轮。"""
    from support_accessibility.runtime.data_paths import resolve_data_paths
    path = os.path.join(str(resolve_data_paths().processed_root("fusion360")), "dataset.json")
    if not os.path.exists(path):
        return {"name": "label_audit", "status": PENDING,
                "detail": "未见真实数据集 dataset.json——跑 `experiments/label_audit.py --write` 生成 label_audit（D-025）"}
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError) as e:
        return {"name": "label_audit", "status": PENDING, "detail": f"dataset.json 读失败：{e}"}
    la = d.get("label_audit")
    if not la:
        return {"name": "label_audit", "status": PENDING,
                "detail": "dataset.json 无 label_audit 块——跑 `experiments/label_audit.py --write`（D-025）"}
    diff = la.get("differential", {}); stab = la.get("res_stability") or {}
    res_ok = stab.get("res48_vs_res96_agreement", 0.0) >= 0.95        # 命门须含 res-稳定腿（D-025，防半证签收）
    ok = bool(la.get("verdict_pass")) and bool(d.get("human_signoff")) and res_ok
    return {"name": "label_audit", "status": PASS if ok else "FAIL",
            "detail": f"真实标签审核 verdict={la.get('verdict_pass')}/signoff={d.get('human_signoff')}："
                      f"robust 差分 {diff.get('robust_mismatch_rate')} / res稳定 {stab.get('res48_vs_res96_agreement')}（D-025）"}


def build_verdict(include_external=False):
    acceptance = []
    # test_env / test_governance 在前：它们现在就应绿，其余几何性质 PENDING
    for mod in (test_env, test_governance, test_invariants, test_known_answers, test_properties, test_differential, test_mesh_frontend, test_support_contact, test_capsule, test_direction_field, test_eval, test_procedural_cases, test_dataset, test_fusion360, test_thingi, test_model, test_baselines, test_label_quality, test_figure_face_mapping):
        acceptance += mod.checks()
    core_gates = [budget_gate()]
    # Keep the default engineering gate hermetic: external-data gates are only
    # evaluated when the caller explicitly opts into the paper envelope.
    external_gates = (
        [regression_gate(), label_audit_gate()]
        if include_external
        else [
            {"name": "regression", "status": NA, "detail": "论文门专属：使用 `tests/gate.py --paper` 才检查外部回归产物"},
            {"name": "label_audit", "status": NA, "detail": "论文门专属：使用 `tests/gate.py --paper` 才检查外部标签审核"},
        ]
    )
    gates = core_gates + external_gates
    # The engineering gate is intentionally independent of external datasets.
    # --paper opts into the stricter evidence gates.
    ok_states = (PASS, NA)
    all_pass = (all(c["status"] in ok_states for c in acceptance)
                and all(g["status"] in ok_states for g in core_gates))
    paper_pass = all_pass and all(g["status"] in ok_states for g in external_gates)
    return {
        "overall": "GREEN" if (paper_pass if include_external else all_pass) else "RED",
        "engineering_overall": "GREEN" if all_pass else "RED",
        "paper_overall": "GREEN" if include_external and paper_pass else ("RED" if include_external else "NOT_RUN"),
        "include_external": bool(include_external),
        "summary": dict(Counter(x["status"] for x in acceptance + gates)),
        "acceptance": acceptance,
        "gates": gates,
    }


_ICON = {"PASS": "✅", "FAIL": "❌", "PENDING": "⏳", "N/A": "➖"}


def render_markdown(verdict):
    """把裁决渲染为 markdown（供 CI job summary / 本地 --format md）。状态生成、非手抄。"""
    lines = [f"# SAF 验收裁决 — **{verdict['overall']}**", "",
             f"`{verdict['summary']}`", "",
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
    verdict = build_verdict(include_external="--paper" in argv)
    print(render_markdown(verdict) if fmt == "md" else json.dumps(verdict, ensure_ascii=False, indent=2))
    sys.exit(0 if verdict["overall"] == "GREEN" else 1)


if __name__ == "__main__":
    main()
