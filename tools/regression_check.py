#!/usr/bin/env python3
"""回归门实测（阶段5 指标固化；D-026；需 torch）。**模型级配对 + bootstrap CI**：神经二分预测
是否**显著不劣于最强几何基线**（射线可见性 E4）。产出 runs/regression/latest.json 供 tests/gate.py 的
regression_gate 读取裁决（配对差 95%CI 下界 >0 → 神经显著胜 → PASS）。self-add src。

用法：
  conda run -n saf python tools/regression_check.py --max-models 400 --epochs 80
"""
import argparse
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_ROOT), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def both_class(ms):
    import numpy as np
    return [m for m in ms if np.asarray(m.labels).size and np.asarray(m.labels).any() and (~np.asarray(m.labels)).any()]


def main():
    ap = argparse.ArgumentParser(description="回归门：神经 vs 几何基线 模型级配对 bootstrap CI（D-026）")
    ap.add_argument("--fusion", default="data/processed/fusion360_full")
    ap.add_argument("--procedural", default="data/processed/procedural_v1")
    ap.add_argument("--max-models", type=int, default=400)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--baseline-dirs", type=int, default=128)
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data import split_by_model
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    from support_accessibility import eval as E, baselines as B

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    fus, _ = load_dataset(a.fusion)
    proc, _ = load_dataset(a.procedural)
    fus_bc = both_class(fus)[:a.max_models]
    ftr, _fva, fte = split_by_model(fus_bc, frac_train=0.6, frac_val=0.2, seed=a.seed)
    fte = [m for m in fte if m.points.shape[0] > 0]

    def prep(m):
        occ = torch.as_tensor(np.asarray(m.occ, np.float32)).view(1, 1, *m.occ.shape).to(dev)
        return occ, to_grid_coords(m.points, m.occ.shape).to(dev)

    torch.manual_seed(a.seed)
    net = ConvONetLite().to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
    lossf = torch.nn.BCEWithLogitsLoss()
    data = [(prep(m), torch.as_tensor(np.asarray(m.labels, np.float32)).to(dev)) for m in (ftr + proc)]
    for _ in range(a.epochs):
        for i in torch.randperm(len(data)):
            (occ, gc), y = data[i]
            opt.zero_grad(); lossf(net(occ, gc), y).backward(); opt.step()
    net.eval()

    # 模型级配对：每件 神经 F1 与 几何基线(射线可见性) F1
    nf, bf = [], []
    alln, allb, allg = [], [], []
    with torch.no_grad():
        for m in fte:
            occ, gc = prep(m)
            pred = (torch.sigmoid(net(occ, gc)) >= 0.5).cpu().numpy()
            base = B.ray_visibility(m.occ, m.points, a.baseline_dirs)
            gold = np.asarray(m.labels, bool)
            nf.append(E.f1_inaccessible(pred, gold)); bf.append(E.f1_inaccessible(base, gold))
            alln.append(pred); allb.append(base); allg.append(gold)
    nf, bf = np.array(nf), np.array(bf)
    diff = nf - bf
    # bootstrap over 件（模型级）：配对差均值的 95%CI
    rng = np.random.default_rng(a.seed)
    boots = np.array([diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(a.n_boot)])
    ci_low, ci_high = float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))
    P, Bd, G = np.concatenate(alln), np.concatenate(allb), np.concatenate(allg)

    rep = {"n_test_models": len(fte), "n_bootstrap": a.n_boot, "seed": a.seed, "device": dev,
           "neural_f1": round(E.f1_inaccessible(P, G), 4), "baseline_f1": round(E.f1_inaccessible(Bd, G), 4),
           "paired_diff_mean": round(float(diff.mean()), 4),
           "diff_ci_low": round(ci_low, 4), "diff_ci_high": round(ci_high, 4),
           "passes": bool(ci_low > 0), "baseline": "ray_visibility(E4)"}
    outdir = os.path.join(os.path.dirname(_ROOT), "runs", "regression")
    os.makedirs(outdir, exist_ok=True)
    json.dump(rep, open(os.path.join(outdir, "latest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("REGRESSION " + json.dumps(rep))


if __name__ == "__main__":
    main()
