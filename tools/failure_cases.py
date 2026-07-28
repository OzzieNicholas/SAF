#!/usr/bin/env python3
"""失败案例分析（阶段8；需 torch）。神经二分预测 vs oracle 在**留出真实件**上何处/为何误判。

训 ConvONet-lite 二分头（镜像 H3 制度），留出集上定位 pred≠gold 的点，按**几何难度**刻画：
每点可达方向数 n_viable（oracle direction_labels，D-024）——n_viable 小=勉强可达/临界=最难。
产出：整体 F1、误判率、假正(FP:判不可达实可达)/假负(FN:判可达实不可达)拆分、按 n_viable 分箱误判率，
+ 误判最多的几件审计 PNG（occ 剪影 + 误判掩码）。self-add src。

用法：
  conda run -n saf python tools/failure_cases.py --fusion data/processed/fusion360_full --max-models 400
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
    ap = argparse.ArgumentParser(description="失败案例分析（阶段8）")
    ap.add_argument("--fusion", default="data/processed/fusion360_full")
    ap.add_argument("--procedural", default="data/processed/procedural_v1")
    ap.add_argument("--max-models", type=int, default=400, help="截取 fusion both-class 前 N 件（可解性）")
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-directions", type=int, default=128)
    ap.add_argument("--outdir", default=None, help="审计 PNG 输出目录（默认 scratch 内）")
    ap.add_argument("--top-audit", type=int, default=4)
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data import split_by_model
    from support_accessibility.oracle import SupportAccessibilityOracle
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    from support_accessibility import eval as E, viz as VIZ

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    fus, _ = load_dataset(a.fusion)
    proc, _ = load_dataset(a.procedural)
    fus_bc = both_class(fus)[:a.max_models]
    ftr, _fva, fte = split_by_model(fus_bc, frac_train=0.6, frac_val=0.2, seed=a.seed)
    fte = [m for m in fte if m.points.shape[0] > 0]
    print(f"device={dev} fusion_bc={len(fus_bc)} train={len(ftr)} test={len(fte)}", flush=True)

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

    # 留出集逐点：pred(不可达=1) vs gold + 每点 n_viable（难度代理）
    all_pred, all_gold, all_nv = [], [], []
    per_model = []                                              # (name, n_err, err_mask, model)
    with torch.no_grad():
        for m in fte:
            occ, gc = prep(m)
            pred = (torch.sigmoid(net(occ, gc)) >= 0.5).cpu().numpy()
            gold = np.asarray(m.labels, bool)
            o = SupportAccessibilityOracle(m.occ, {"n_directions": a.n_directions})
            nv = np.array([int(o.direction_labels(p, m.radius).sum()) for p in m.points])
            err = pred != gold
            all_pred.append(pred); all_gold.append(gold); all_nv.append(nv)
            per_model.append((m.name, int(err.sum()), err, m))
    P, G, NV = np.concatenate(all_pred), np.concatenate(all_gold), np.concatenate(all_nv)
    err = P != G
    fp = P & ~G                                                # 判不可达、实可达
    fn = ~P & G                                                # 判可达、实不可达（漏报风险，最糟）

    def rate(mask):
        return round(float(err[mask].mean()), 3) if mask.any() else None
    bins = {"0": NV == 0, "1-2": (NV >= 1) & (NV <= 2), "3-5": (NV >= 3) & (NV <= 5), "6+": NV >= 6}

    # 审计 PNG：误判最多的 top-K 件（掩码=误判点）
    outdir = a.outdir or os.path.join(_ROOT, "..", "runs", "failure_audit")
    emitted = []
    try:
        os.makedirs(outdir, exist_ok=True)
        for name, ne, emask, m in sorted(per_model, key=lambda t: -t[1])[:a.top_audit]:
            if ne == 0:
                continue
            p = os.path.join(outdir, f"fail_{name}_{ne}err.png")
            VIZ.accessibility_montage(m.occ, m.points, emask, p)
            emitted.append(os.path.basename(p))
    except Exception as e:
        emitted = [f"(PNG 跳过：{str(e)[:50]})"]

    print("FAILURE_ANALYSIS " + json.dumps({
        "test_models": len(fte), "test_points": int(G.size),
        "f1_inaccessible": round(E.f1_inaccessible(P, G), 3),
        "error_rate": round(float(err.mean()), 3),
        "false_pos_rate": round(float(fp.mean()), 3), "false_neg_rate": round(float(fn.mean()), 3),
        "gold_inacc_frac": round(float(G.mean()), 3),
        "error_rate_by_nviable": {k: rate(v) for k, v in bins.items()},
        "nviable_share": {k: round(float(v.mean()), 3) for k, v in bins.items()},
        "audit_pngs": emitted, "audit_dir": os.path.normpath(outdir),
    }))


if __name__ == "__main__":
    main()
