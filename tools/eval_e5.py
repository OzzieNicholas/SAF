#!/usr/bin/env python3
"""E5 方向级可达性场预测评测 CLI（D-024；需 torch）。

把 ConvONet-lite 扩为方向级输出头（out_dim=D=下半球逼近方向数），跨模型预测**每点每方向**是否被挡
（blocked=1=风险，方向级类比点级"不可达"）。目标由 oracle `direction_labels` 生成（占据口径，无网格）。
指标：per-direction F1（逐方向逐点）+ per-point 方向集 IoU（预测可达方向集 vs oracle）+ 复原点级二分 F1
（全方向皆挡→点不可达，any-归约 = D-004）。对照 per-direction 多数类基线。self-add src。

用法：
  conda run -n saf python tools/eval_e5.py --data data/processed/procedural_v1 --seeds 3
"""
import argparse
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_ROOT), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def main():
    ap = argparse.ArgumentParser(description="E5 方向级可达性场预测（D-024）")
    ap.add_argument("--data", default="data/processed/procedural_v1")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--n-directions", type=int, default=128)     # D-021 冻结值；下半球得 D≈64
    ap.add_argument("--max-models", type=int, default=None)
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data import split_by_model
    from support_accessibility.oracle import SupportAccessibilityOracle
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    from support_accessibility import eval as E

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    ms, _ = load_dataset(a.data)
    if a.max_models:
        ms = ms[:a.max_models]

    # 方向级目标：blocked=1（风险），(K,D)，由 oracle direction_labels（占据口径，无网格）生成
    D = None
    items = []
    for m in ms:
        if m.points.shape[0] == 0:
            continue
        o = SupportAccessibilityOracle(m.occ, {"n_directions": a.n_directions})
        if D is None:
            D = len(o.dirs)
        viable = np.stack([o.direction_labels(p, m.radius) for p in m.points])   # (K,D) True=可达
        items.append((m.name, m.occ, m.points, (~viable).astype(np.float32)))    # blocked=1
    print(f"device={dev} D_dirs={D} models={len(items)} pts={sum(it[2].shape[0] for it in items)}", flush=True)

    def prep(occ, pts):
        occt = torch.as_tensor(np.asarray(occ, np.float32)).view(1, 1, *occ.shape).to(dev)
        gc = to_grid_coords(pts, occ.shape).to(dev)
        return occt, gc

    def evaluate(net, test):
        P, G, SC = [], [], []
        with torch.no_grad():
            for _n, occ, pts, blk in test:
                occt, gc = prep(occ, pts)
                logit = net(occt, gc)                                   # (K,D) blocked logit
                P.append((torch.sigmoid(logit) >= 0.5).cpu().numpy().reshape(-1, D))
                SC.append((-logit).cpu().numpy().reshape(-1, D))       # 可达性打分 = −blocked_logit（高=更可达）
                G.append(blk.astype(bool).reshape(-1, D))
        P, G, SC = np.concatenate(P), np.concatenate(G), np.concatenate(SC)
        f1 = E.f1_inaccessible(P.ravel(), G.ravel())                     # per-direction（blocked=正）
        ious = []
        for p, g in zip(P, G):
            pv, gv = ~p, ~g                                             # 可达方向集
            u = int((pv | gv).sum())
            ious.append(1.0 if u == 0 else int((pv & gv).sum()) / u)
        dir_iou = float(np.mean(ious))
        bin_f1 = E.f1_inaccessible(P.all(1), G.all(1))                  # 复原点级二分（全挡→不可达）
        viable = ~G                                                    # oracle 可达方向
        top1 = E.topk_direction_hit_rate(SC, viable, 1)                # 最有把握方向真可达的点占比
        top3 = E.topk_direction_hit_rate(SC, viable, 3)
        prec3 = E.topk_direction_precision(SC, viable, 3)
        return f1, dir_iou, bin_f1, top1, top3, prec3

    rows = []
    for seed in range(a.seeds):
        tr, te = split_by_model(items, frac_train=0.7, seed=seed)
        torch.manual_seed(seed)
        net = ConvONetLite(out_dim=D).to(dev)
        opt = torch.optim.Adam(net.parameters(), lr=a.lr, weight_decay=1e-4)
        lossf = torch.nn.BCEWithLogitsLoss()
        data = [(prep(occ, pts), torch.as_tensor(blk).to(dev)) for _n, occ, pts, blk in tr]
        for _ in range(a.epochs):
            for i in torch.randperm(len(data)):
                (occt, gc), y = data[i]
                opt.zero_grad(); lossf(net(occt, gc), y).backward(); opt.step()
        net.eval()
        f1, dir_iou, bin_f1, top1, top3, prec3 = evaluate(net, te)
        # 对照：per-direction 多数类基线（train 每方向 blocked 先验）
        tr_t = np.concatenate([blk.reshape(-1, D) for _n, _o, _p, blk in tr])
        maj = (tr_t.mean(0) >= 0.5)
        te_t = np.concatenate([blk.reshape(-1, D) for _n, _o, _p, blk in te]).astype(bool)
        base_f1 = E.f1_inaccessible(np.broadcast_to(maj, te_t.shape).ravel(), te_t.ravel())
        rows.append((f1, dir_iou, bin_f1, base_f1, top1, top3, prec3))
        print(f"seed{seed} dir_f1={f1:.3f} dir_iou={dir_iou:.3f} bin_f1={bin_f1:.3f} "
              f"top1={top1:.3f} top3={top3:.3f} prec@3={prec3:.3f} maj_base_f1={base_f1:.3f}", flush=True)

    arr = np.array(rows)
    print("E5_RESULT " + json.dumps({
        "data": a.data, "seeds": a.seeds, "epochs": a.epochs, "device": dev, "D_dirs": D, "models": len(items),
        "dir_f1_mean": round(float(arr[:, 0].mean()), 3), "dir_f1_std": round(float(arr[:, 0].std()), 3),
        "dir_setiou_mean": round(float(arr[:, 1].mean()), 3),
        "recovered_binary_f1_mean": round(float(arr[:, 2].mean()), 3),
        "majority_dir_baseline_f1": round(float(arr[:, 3].mean()), 3),
        "topk_hit_top1_mean": round(float(arr[:, 4].mean()), 3),
        "topk_hit_top3_mean": round(float(arr[:, 5].mean()), 3),
        "topk_precision_at3_mean": round(float(arr[:, 6].mean()), 3),
    }))


if __name__ == "__main__":
    main()
