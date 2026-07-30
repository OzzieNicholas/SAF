#!/usr/bin/env python3
"""训练 + 缓存图件用 ConvONet 点级模型 → runs/figures/ckpt_point.pt（state_dict + 留出件名 + seed）。
图 7 预测热图用它在**未见（留出）件**上出预测。默认 1200 件 / 150 轮 → 预测足够自信、代表正式模型。
用法：python tools/figures/_train_ckpt.py [--max-models 1200] [--epochs 150]
末尾打印留出集里可读双类候选件（name, npts, inacc），供 fig07 选件。"""
import argparse
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_ROOT, "src"))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def both_class(ms):
    import numpy as np
    return [m for m in ms if np.asarray(m.labels).size and np.asarray(m.labels).any() and (~np.asarray(m.labels)).any()]


def main():
    import numpy as np
    import torch
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data import split_by_model
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-models", type=int, default=1200)
    ap.add_argument("--epochs", type=int, default=150)
    a = ap.parse_args()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    fus, _ = load_dataset(os.path.join(_ROOT, "data", "processed", "fusion360_full"))
    proc, _ = load_dataset(os.path.join(_ROOT, "data", "processed", "procedural_v1"))
    fbc = both_class(fus)[:a.max_models]
    ftr, _fva, fte = split_by_model(fbc, frac_train=0.6, frac_val=0.2, seed=0)
    torch.manual_seed(0)
    net = ConvONetLite().to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
    lossf = torch.nn.BCEWithLogitsLoss()
    data = []
    for m in (ftr + proc):
        occ = torch.as_tensor(np.asarray(m.occ, np.float32)).view(1, 1, *m.occ.shape).to(dev)
        gc = to_grid_coords(m.points, m.occ.shape).to(dev)
        y = torch.as_tensor(np.asarray(m.labels, np.float32)).to(dev)
        data.append((occ, gc, y))
    for _ in range(a.epochs):
        for i in torch.randperm(len(data)):
            occ, gc, y = data[i]
            opt.zero_grad(); lossf(net(occ, gc), y).backward(); opt.step()
    out = os.path.join(_ROOT, "runs", "figures")
    os.makedirs(out, exist_ok=True)
    torch.save({"state_dict": net.state_dict(), "test_names": [m.name for m in fte], "seed": 0,
                "max_models": a.max_models, "epochs": a.epochs},
               os.path.join(out, "ckpt_point.pt"))
    print(f"SAVED ckpt_point.pt (dev={dev}, train={len(ftr)}+proc{len(proc)}, test={len(fte)}, epochs={a.epochs})")

    # 留出集可读双类候选（供 fig07 curate）：0.15<inacc<0.75，按点数降序
    cand = []
    for m in fte:
        lab = np.asarray(m.labels, bool)
        if lab.size and lab.any() and (~lab).any() and 0.15 < lab.mean() < 0.75:
            cand.append((m.name, int(lab.size), float(lab.mean())))
    cand.sort(key=lambda r: -r[1])
    print("TEST both-class candidates (name, npts, inacc):")
    for r in cand[:16]:
        print("  ", r)


if __name__ == "__main__":
    main()
