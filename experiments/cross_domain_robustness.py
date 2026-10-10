#!/usr/bin/env python3
"""跨域鲁棒性评测（D-022；需 torch）。镜像 experiments/cross_model_prediction.py 的训练制度
（split 0.6/0.2/0.2、多种子），同一 ConvONet-lite 模型上评 **域内**（留出 Fusion）vs **OOD**（Thingi10K）
不可达 F1 → 跨域掉幅。域内结果应与点级主结果同量级（一致性自检）。

用法：
  python experiments/cross_domain_robustness.py --seeds 3
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
    ap = argparse.ArgumentParser(description="跨域鲁棒性：Fusion 域内留出 vs Thingi10K 野外网格（D-022）")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--procedural", default=str(paths.processed_root("procedural")))
    ap.add_argument("--thingi", default=str(paths.processed_root("thingi10k")))
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/cross_domain_robustness/result.json（试跑请指定其他路径，避免覆盖证据）")
    a = ap.parse_args()

    import json
    from support_accessibility.runtime.run_records import write_result
    import numpy as np
    import torch
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data import split_by_model
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    from support_accessibility import eval as E, baselines as B

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"device={dev} torch={torch.__version__}")
    fus, _ = load_dataset(a.fusion)
    proc, _ = load_dataset(a.procedural)
    thi, _ = load_dataset(a.thingi)
    fus_bc, thi_bc = both_class(fus), both_class(thi)

    def prep(m):
        occ = torch.as_tensor(np.asarray(m.occ, np.float32)).view(1, 1, *m.occ.shape).to(dev)
        gc = to_grid_coords(m.points, m.occ.shape).to(dev)
        y = torch.as_tensor(np.asarray(m.labels, np.float32)).to(dev)
        return occ, gc, y

    def f1_on(net, models):
        pr, go = [], []
        with torch.no_grad():
            for m in models:
                occ, gc, _ = prep(m)
                pr.append((torch.sigmoid(net(occ, gc)) >= 0.5).cpu().numpy())
                go.append(np.asarray(m.labels, bool))
        p, g = np.concatenate(pr), np.concatenate(go)
        return E.f1_inaccessible(p, g), E.iou_inaccessible(p, g)

    gold_thi = np.concatenate([np.asarray(m.labels, bool) for m in thi_bc])
    rv = np.concatenate([B.ray_visibility(m.occ, m.points, FROZEN.n_directions) for m in thi_bc])   # OOD 几何基线（确定性）

    rows = []
    for seed in range(a.seeds):
        ftr, _fva, fte = split_by_model(fus_bc, frac_train=0.6, frac_val=0.2, seed=seed)
        fte = [m for m in fte if m.points.shape[0] > 0]
        torch.manual_seed(seed)
        net = ConvONetLite().to(dev)
        opt = torch.optim.Adam(net.parameters(), lr=a.lr, weight_decay=1e-4)
        lossf = torch.nn.BCEWithLogitsLoss()
        data = [prep(m) for m in (ftr + proc)]
        for _ in range(a.epochs):
            net.train()
            for i in torch.randperm(len(data)):
                occ, gc, y = data[i]
                opt.zero_grad(); lossf(net(occ, gc), y).backward(); opt.step()
        net.eval()
        in_f1, _ = f1_on(net, fte)
        ood_f1, ood_iou = f1_on(net, thi_bc)
        rows.append((in_f1, ood_f1, ood_iou))
        print(f"seed{seed} in_f1={in_f1:.3f} ood_f1={ood_f1:.3f} drop={in_f1 - ood_f1:.3f}")

    arr = np.array(rows)
    rep = write_result("cross_domain_robustness", {
        "seeds": a.seeds, "epochs": a.epochs, "device": dev,
        "fusion_bothclass": len(fus_bc), "thingi_bothclass": len(thi_bc), "thingi_pts": int(gold_thi.size),
        "thingi_gold_inacc_frac": round(float(gold_thi.mean()), 3),
        "indomain_f1_mean": round(float(arr[:, 0].mean()), 3), "indomain_f1_std": round(float(arr[:, 0].std()), 3),
        "crossdomain_f1_mean": round(float(arr[:, 1].mean()), 3), "crossdomain_f1_std": round(float(arr[:, 1].std()), 3),
        "crossdomain_iou_mean": round(float(arr[:, 2].mean()), 3),
        "f1_drop_mean": round(float((arr[:, 0] - arr[:, 1]).mean()), 3),
        "crossdomain_rayvis_f1": round(E.f1_inaccessible(rv, gold_thi), 3),
    }, a.out, (a.fusion, a.procedural, a.thingi))
    print("CROSS_DOMAIN_ROBUSTNESS " + json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
