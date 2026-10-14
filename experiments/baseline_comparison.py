#!/usr/bin/env python3
"""基线对照与回归门：同一固定留出集上六类方法的不可达 F1（学习类方法报多训练种子均值 ± 标准差）。

方法：多数类 / 局部几何规则 / 零半径射线可见性 / 粗方向有限工具代理 /
局部学习参照（tiny MLP）/ 形状条件网络（ConvONet-lite）。
形状条件网络直接读取 experiments/holdout_model.py 的多种子权重（不在此重训），tiny MLP 按相同训练种子训练；
几何方法是确定性的，只算一次。切分与 holdout_model 相同（前 400 件两类件，切分种子 0）。
写入 artifacts/runs/baseline_comparison/result.json：论文方法对照的数据源，也是回归门（D-026）的裁决依据——
形状条件网络相对零半径射线的逐件配对差，其 95% bootstrap 区间下界须大于 0。结果附输入数据摘要，数据变化后门判为过期。

用法：
  python experiments/baseline_comparison.py
"""
import argparse

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import logical_data_ref, resolve_data_paths
from support_accessibility.runtime.frozen_params import FROZEN

setup_console()


def main():
    ap = argparse.ArgumentParser(description="基线汇总：六类方法同一留出集 F1（多训练种子）")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--procedural", default=str(paths.processed_root("procedural")))
    ap.add_argument("--tiny-epochs", type=int, default=300)
    ap.add_argument("--coarse-n-directions", type=int, default=16,
                    help="有限工具粗方向代理的全局候选方向数（刻意小于参考标签的 128）")
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/baseline_comparison/result.json（试跑请指定其他路径，避免覆盖证据）")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from holdout_model import holdout_split, load_holdout_models, predict_proba      # 同目录脚本
    from support_accessibility.runtime.run_records import write_result
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility import models as TINY, eval as E, baselines as B

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    fus, _ = load_dataset(a.fusion)
    proc, _ = load_dataset(a.procedural)
    ftr, _fva, fte = holdout_split(fus)
    train_set = ftr + proc
    nets = load_holdout_models(dev)
    if not nets or any(list(ck["test_names"]) != [m.name for m in fte] for _s, _n, ck in nets):
        raise RuntimeError("固定留出模型缺失或测试名单不一致：先运行 experiments/holdout_model.py")
    seeds = [s for s, _n, _c in nets]
    print(f"device={dev} train={len(ftr)}(+proc {len(proc)}) test={len(fte)} seeds={seeds}", flush=True)

    golds = [np.asarray(m.labels, bool) for m in fte]
    G = np.concatenate(golds)
    maj = B.majority_label(train_set)
    fixed = {
        "majority": [B.predict_majority(g.size, maj) for g in golds],
        "local_rule": [B.local_solid_rule(m.occ, m.points) for m in fte],
        "ray_visibility": [B.ray_visibility(m.occ, m.points) for m in fte],
        "coarse_finite_tool": [B.voxel_judgment(m.occ, m.points, m.radius, a.coarse_n_directions) for m in fte],
    }
    learned = {"tiny_local": [], "convonet": []}       # 每个训练种子一组逐件预测
    for seed, net, _ck in nets:
        tiny = TINY.train(train_set, epochs=a.tiny_epochs, seed=seed)
        learned["tiny_local"].append([TINY.predict(tiny, m.occ, m.points) for m in fte])
        learned["convonet"].append([predict_proba(net, m, dev) >= 0.5 for m in fte])
        print(f"seed {seed} done", flush=True)

    rng = np.random.default_rng(0)

    def ci(values, draws=10000):
        values = np.asarray(values, float)
        means = values[rng.integers(0, len(values), size=(draws, len(values)))].mean(axis=1)
        return [round(float(v), 4) for v in np.quantile(means, [.025, .975])]

    def per_part(preds):
        return np.array([E.f1_inaccessible(p, g) for p, g in zip(preds, golds)])

    rep = {"n_test_models": len(fte), "n_test_points": int(G.size), "split_seed": 0, "training_seeds": seeds,
           "tiny_epochs": a.tiny_epochs, "device": dev,
           "reference_n_directions": FROZEN.n_directions, "coarse_n_directions": a.coarse_n_directions,
           "method_roles": B.baseline_method_roles(), "bootstrap_seed": 0, "bootstrap_draws": 10000,
           "test_names": [m.name for m in fte], "methods": {}}
    part_mean = {}
    for k, preds in fixed.items():
        per = per_part(preds)
        part_mean[k] = per
        rep["methods"][k] = {"kind": "deterministic", "f1_overall": round(E.f1_inaccessible(np.concatenate(preds), G), 4),
                             "f1_overall_std": 0.0, "f1_model_mean": round(float(per.mean()), 4),
                             "f1_model_std": round(float(per.std()), 4), "f1_model_ci95": ci(per),
                             "f1_by_model": [round(float(v), 6) for v in per]}
    for k, runs in learned.items():
        overall = np.array([E.f1_inaccessible(np.concatenate(p), G) for p in runs])
        per_seed = np.stack([per_part(p) for p in runs])            # (seeds, parts)
        per = per_seed.mean(axis=0)                                  # 逐件：种子平均
        part_mean[k] = per
        rep["methods"][k] = {"kind": "learned", "f1_overall": round(float(overall.mean()), 4),
                             "f1_overall_std": round(float(overall.std()), 4),
                             "f1_overall_by_seed": [round(float(v), 4) for v in overall],
                             "f1_model_mean": round(float(per.mean()), 4), "f1_model_std": round(float(per.std()), 4),
                             "f1_model_mean_by_seed": [round(float(v), 4) for v in per_seed.mean(axis=1)],
                             "f1_model_ci95": ci(per), "f1_by_model": [round(float(v), 6) for v in per]}
    delta = part_mean["convonet"] - part_mean["ray_visibility"]
    rep["paired_delta_convonet_minus_ray"] = {"mean": round(float(delta.mean()), 4), "ci95": ci(delta)}
    delta = part_mean["convonet"] - part_mean["coarse_finite_tool"]
    rep["paired_delta_convonet_minus_coarse"] = {"mean": round(float(delta.mean()), 4), "ci95": ci(delta)}
    rep["data_roots"] = [logical_data_ref(a.fusion, paths), logical_data_ref(a.procedural, paths)]
    rep["data_digest"] = E.data_digest(a.fusion, a.procedural)
    rep = write_result("baseline_comparison", rep, output=a.out, inputs=(a.fusion, a.procedural))
    print("BASELINES_RESULT " + json.dumps({k: v for k, v in rep.items() if k != "test_names"}, ensure_ascii=False)[:3000])


if __name__ == "__main__":
    main()
