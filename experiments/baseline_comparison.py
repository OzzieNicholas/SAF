#!/usr/bin/env python3
"""表 5 基线汇总复现器：同一留出集一次产出六类方法的不可达 F1。

方法：多数类 / 局部几何规则 / 射线可见性(r=0) / 粗方向有限工具代理 /
局部形状感知基线(tiny MLP) / 本文(ConvONet-lite)。
镜像 regression_check 制度（both_class[:max_models]、模型级三切 seed、ftr+程序化 训练、留出 fte 评测），
报告各方法点级总体 F1 + 零件级均值±std，写入 artifacts/runs/baseline_comparison/result.json（论文基线表的唯一数据源）。
需 torch。

用法：
  python experiments/baseline_comparison.py --max-models 400 --epochs 80
"""
import argparse

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths
from support_accessibility.runtime.frozen_params import FROZEN

setup_console()


def both_class(ms):
    import numpy as np
    return [m for m in ms if np.asarray(m.labels).size and np.asarray(m.labels).any() and (~np.asarray(m.labels)).any()]


def main():
    ap = argparse.ArgumentParser(description="表5 基线汇总：五类方法同一留出集 F1")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--procedural", default=str(paths.processed_root("procedural")))
    ap.add_argument("--max-models", type=int, default=400)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--tiny-epochs", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-directions", type=int, default=FROZEN.n_directions)   # 射线可见性基线方向数（D-021 冻结）
    ap.add_argument("--coarse-n-directions", type=int, default=16,
                    help="有限工具粗方向代理的全局候选方向数（刻意小于参考标签的 128）")
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/baseline_comparison/result.json（试跑请指定其他路径，避免覆盖证据）")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from support_accessibility.runtime.run_records import write_result
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data import split_by_model
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    from support_accessibility import models as TINY, eval as E, baselines as B

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    fus, _ = load_dataset(a.fusion)
    proc, _ = load_dataset(a.procedural)
    fus_bc = both_class(fus)[:a.max_models]
    ftr, _fva, fte = split_by_model(fus_bc, frac_train=0.6, frac_val=0.2, seed=a.seed)
    fte = [m for m in fte if m.points.shape[0] > 0]
    train_set = ftr + proc
    print(f"device={dev} both_class={len(fus_bc)} train={len(ftr)}(+proc {len(proc)}) test={len(fte)}", flush=True)

    # —— 本文（ConvONet-lite，镜像 regression_check 训练制度）——
    def prep(m):
        occ = torch.as_tensor(np.asarray(m.occ, np.float32)).view(1, 1, *m.occ.shape).to(dev)
        return occ, to_grid_coords(m.points, m.occ.shape).to(dev)

    torch.manual_seed(a.seed)
    net = ConvONetLite().to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
    lossf = torch.nn.BCEWithLogitsLoss()
    data = [(prep(m), torch.as_tensor(np.asarray(m.labels, np.float32)).to(dev)) for m in train_set]
    for _ in range(a.epochs):
        for i in torch.randperm(len(data)):
            (occ, gc), y = data[i]
            opt.zero_grad(); lossf(net(occ, gc), y).backward(); opt.step()
    net.eval()

    tiny = TINY.train(train_set, epochs=a.tiny_epochs, seed=a.seed)     # 局部形状感知基线（tiny MLP）
    maj = B.majority_label(train_set)

    preds = {k: [] for k in ("majority", "local_rule", "ray_visibility", "coarse_finite_tool", "tiny_local", "convonet")}
    golds = []
    with torch.no_grad():
        for m in fte:
            gold = np.asarray(m.labels, bool)
            golds.append(gold)
            preds["majority"].append(B.predict_majority(gold.size, maj))
            preds["local_rule"].append(B.local_solid_rule(m.occ, m.points))
            preds["ray_visibility"].append(B.ray_visibility(m.occ, m.points, a.n_directions))
            preds["coarse_finite_tool"].append(
                B.coarse_finite_tool_proxy(m.occ, m.points, m.radius, a.coarse_n_directions)
            )
            preds["tiny_local"].append(TINY.predict(tiny, m.occ, m.points))
            occ, gc = prep(m)
            preds["convonet"].append((torch.sigmoid(net(occ, gc)) >= 0.5).cpu().numpy())

    G = np.concatenate(golds)
    bootstrap_rng = np.random.default_rng(0)

    def bootstrap_mean_ci(values, draws=10000):
        values = np.asarray(values, float)
        samples = bootstrap_rng.integers(0, len(values), size=(draws, len(values)))
        means = values[samples].mean(axis=1)
        return [round(float(v), 4) for v in np.quantile(means, [.025, .975])]

    rep = {"n_test_models": len(fte), "n_test_points": int(G.size), "seed": a.seed,
           "epochs": a.epochs, "tiny_epochs": a.tiny_epochs, "device": dev,
           "reference_n_directions": a.n_directions, "coarse_n_directions": a.coarse_n_directions,
           "method_roles": B.baseline_method_roles(), "bootstrap_seed": 0,
           "bootstrap_draws": 10000, "test_names": [m.name for m in fte], "methods": {}}
    per_method = {}
    for k, ps in preds.items():
        P = np.concatenate(ps)
        per = np.array([E.f1_inaccessible(p, g) for p, g in zip(ps, golds)])
        per_method[k] = per
        rep["methods"][k] = {"f1_overall": round(E.f1_inaccessible(P, G), 4),
                             "f1_model_mean": round(float(per.mean()), 4),
                             "f1_model_std": round(float(per.std()), 4),
                             "f1_model_ci95": bootstrap_mean_ci(per),
                             "f1_by_model": [round(float(value), 6) for value in per]}
    delta = per_method["convonet"] - per_method["ray_visibility"]
    rep["paired_delta_convonet_minus_ray"] = {
        "mean": round(float(delta.mean()), 4), "ci95": bootstrap_mean_ci(delta)
    }
    rep = write_result("baseline_comparison", rep, output=a.out, inputs=(a.fusion, a.procedural))
    print("BASELINES_RESULT " + json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
