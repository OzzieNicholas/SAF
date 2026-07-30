#!/usr/bin/env python3
"""训练 + 缓存图件用 ConvONet **方向级**模型（out_dim=D）→ runs/figures/ckpt_dir.pt。

镜像 tools/eval_e5.py 训练配方（占据口径方向目标，图件用故不走 --root 细化，省时）。
保存：state_dict, D, dirs(D,3), n_directions, test_names, 展示候选点（name, idx, viable_frac）供 fig09 选件。
用法：python tools/figures/_train_dir_ckpt.py [--max-models 250] [--epochs 120]
"""
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
    from support_accessibility.oracle import SupportAccessibilityOracle
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-models", type=int, default=250)
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--n-directions", type=int, default=128)
    a = ap.parse_args()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    fus, _ = load_dataset(os.path.join(_ROOT, "data", "processed", "fusion360_full"))
    proc, _ = load_dataset(os.path.join(_ROOT, "data", "processed", "procedural_v1"))
    ms = both_class(fus)[:a.max_models]
    tr_names, _va, te = split_by_model(ms, frac_train=0.6, frac_val=0.2, seed=0)

    D = None
    dirs = None

    def targets(m):
        nonlocal D, dirs
        o = SupportAccessibilityOracle(m.occ, {"n_directions": a.n_directions})
        if D is None:
            D = len(o.dirs); dirs = np.asarray(o.dirs, np.float32)
        viable = np.stack([o.direction_labels(p, m.radius) for p in m.points])   # (K,D) True=可达
        return (~viable).astype(np.float32)                                       # blocked=1

    print(f"device={dev} 生成方向目标：train={len(tr_names)}+proc{len(proc)} test={len(te)} ...", flush=True)
    train_set = [(m.occ, m.points, targets(m)) for m in (tr_names + proc)]
    print(f"D_dirs={D} 训练开始 epochs={a.epochs}", flush=True)

    torch.manual_seed(0)
    net = ConvONetLite(out_dim=D).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
    lossf = torch.nn.BCEWithLogitsLoss()
    data = []
    for occ, pts, blk in train_set:
        occt = torch.as_tensor(np.asarray(occ, np.float32)).view(1, 1, *occ.shape).to(dev)
        gc = to_grid_coords(pts, occ.shape).to(dev)
        data.append((occt, gc, torch.as_tensor(blk).to(dev)))
    for _ in range(a.epochs):
        for i in torch.randperm(len(data)):
            occt, gc, y = data[i]
            opt.zero_grad(); lossf(net(occt, gc), y).backward(); opt.step()

    # 展示候选：留出件中 oracle 可达方向占比 ∈[0.3,0.6] 的点（方向盘混合、好看）
    cand = []
    for m in te:
        if m.points.shape[0] == 0:
            continue
        o = SupportAccessibilityOracle(m.occ, {"n_directions": a.n_directions})
        for idx, p in enumerate(m.points):
            vf = float(o.direction_labels(p, m.radius).mean())
            if 0.3 <= vf <= 0.6:
                cand.append((m.name, int(idx), round(vf, 3)))
    cand = cand[:40]
    out = os.path.join(_ROOT, "runs", "figures"); os.makedirs(out, exist_ok=True)
    torch.save({"state_dict": net.state_dict(), "D": D, "dirs": dirs, "n_directions": a.n_directions,
                "test_names": [m.name for m in te], "showcase_cand": cand}, os.path.join(out, "ckpt_dir.pt"))
    print(f"SAVED ckpt_dir.pt (D={D}, test={len(te)}, showcase_cand={len(cand)})")
    for c in cand[:8]:
        print("  cand:", c)


if __name__ == "__main__":
    main()
