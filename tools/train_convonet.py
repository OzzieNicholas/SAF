#!/usr/bin/env python3
"""训练 ConvONet-lite 形状条件模型 + 跨模型（H3）评测 CLI（Phase-3；需 torch，D-020 后）。

用法：
  conda run -n saf python tools/train_convonet.py --seeds 5 --epochs 80
在真实挑战件（Fusion360 both-class）+ 程序化信号集上按模型级切分训练，未见真实件上评不可达 F1/IoU；
对比 E4 几何基线 bar。self-add src（同其它 tool，免 editable 安装）。GPU 可用则用。
"""
import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

for _s in (sys.stdout, sys.stderr):            # Windows GBK 控制台防崩：⟹/⟺ 等非 GBK 字符（仿 tests/gate.py）
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def both_class(ms):
    import numpy as np
    return [m for m in ms if np.asarray(m.labels).size and np.asarray(m.labels).any() and (~np.asarray(m.labels)).any()]


def main():
    ap = argparse.ArgumentParser(description="ConvONet-lite 跨模型可达性预测（H3）")
    ap.add_argument("--fusion", default="data/processed/fusion360_full")   # headline 源（全量 8590/1621 两类）；旧 fusion360_v1=1000 件探索集
    ap.add_argument("--procedural", default="data/processed/procedural_v1")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--lr", type=float, default=1e-3)
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data import split_by_model
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    from support_accessibility import eval as E

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"device={dev} torch={torch.__version__}")
    fus, _ = load_dataset(a.fusion)
    proc, _ = load_dataset(a.procedural)
    fus_bc = both_class(fus)

    def prep(m):
        occ = torch.as_tensor(np.asarray(m.occ, np.float32)).view(1, 1, *m.occ.shape).to(dev)
        gc = to_grid_coords(m.points, m.occ.shape).to(dev)
        y = torch.as_tensor(np.asarray(m.labels, np.float32)).to(dev)
        return occ, gc, y

    def train_eval(train, test, seed):
        torch.manual_seed(seed)
        net = ConvONetLite().to(dev)
        opt = torch.optim.Adam(net.parameters(), lr=a.lr, weight_decay=1e-4)
        lossf = torch.nn.BCEWithLogitsLoss()
        data = [prep(m) for m in train]
        for _ in range(a.epochs):
            net.train()
            for i in torch.randperm(len(data)):
                occ, gc, y = data[i]
                opt.zero_grad(); lossf(net(occ, gc), y).backward(); opt.step()
        net.eval(); preds, golds = [], []
        with torch.no_grad():
            for m in test:
                occ, gc, _ = prep(m)
                preds.append((torch.sigmoid(net(occ, gc)) >= 0.5).cpu().numpy())
                golds.append(np.asarray(m.labels, bool))
        p, g = np.concatenate(preds), np.concatenate(golds)
        return E.f1_inaccessible(p, g), E.iou_inaccessible(p, g)

    f1s, ious = [], []
    for seed in range(a.seeds):
        ftr, _fva, fte = split_by_model(fus_bc, frac_train=0.6, frac_val=0.2, seed=seed)
        te = [m for m in fte if m.points.shape[0] > 0]
        f1, iou = train_eval(ftr + proc, te, seed)
        f1s.append(f1); ious.append(iou)
        print(f"seed{seed} F1={f1:.3f} IoU={iou:.3f}")
    f1s = np.array(f1s)
    print(json.dumps({"convonet_f1_mean": round(float(f1s.mean()), 3), "convonet_f1_std": round(float(f1s.std()), 3),
                      "convonet_iou_mean": round(float(np.mean(ious)), 3), "n_splits": a.seeds}))


if __name__ == "__main__":
    main()
