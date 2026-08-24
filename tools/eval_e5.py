#!/usr/bin/env python3
"""E5 方向级可达性场预测评测 CLI（D-024；需 torch）。

把 ConvONet-lite 扩为方向级输出头（out_dim=D=下半球逼近方向数），跨模型预测**每点每方向**是否被挡
（blocked=1=风险，方向级类比点级"不可达"）。目标由 oracle `direction_labels` 生成——**缺省占据口径**（无网格）；
`--root` 给定则载原网格重建 (Vn,F,lo,pitch) 传 oracle，方向目标走 **D-020 边界带精确细化口径**（指引 §6.1-B1a；
占据逐比特校验，不符则回落占据口径并计数；细化标签作 headline 训练源须作者签收，D-024）。
指标：per-direction F1（逐方向逐点）+ per-point 方向集 IoU（预测可达方向集 vs oracle）+ 复原点级二分 F1
（全方向皆挡→点不可达，any-归约 = D-004）。对照 per-direction 多数类基线。self-add src。

用法：
  conda run -n saf python tools/eval_e5.py --data ${SAF_TEMPORARY_ROOT}/SAF/procedural_v1/latest --seeds 3
  conda run -n saf python tools/eval_e5.py --data ${SAF_TEMPORARY_ROOT}/SAF/fusion360_full/latest --max-models 500 \
    --root E:/Work/Data/Fusion360Gallery/reconstruction   # 细化口径方向目标（B1a 升级）
"""
import argparse
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_ROOT), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
try:
    from data_paths import logical_data_ref, resolve_data_paths
except ImportError:
    from tools.data_paths import logical_data_ref, resolve_data_paths

for _s in (sys.stdout, sys.stderr):            # Windows GBK 控制台防崩：⟹/⟺ 等非 GBK 字符（仿 tests/gate.py）
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def build_seed_run_record(
    *,
    seed,
    n_train_models,
    n_test_models,
    n_train_points,
    n_test_points,
    n_directions,
    test_refined_models,
    test_occupancy_fallback_models,
    split_rule,
    metrics,
):
    """Serialize the denominator-aware evidence for one E5 holdout seed."""
    required_metrics = (
        "dir_f1",
        "dir_set_iou",
        "recovered_binary_f1",
        "majority_dir_baseline_f1",
        "topk_hit_top1",
        "topk_hit_top3",
        "topk_precision_at3",
    )
    return {
        "seed": int(seed),
        "split_rule": str(split_rule),
        "n_train_models": int(n_train_models),
        "n_test_models": int(n_test_models),
        "n_train_points": int(n_train_points),
        "n_test_points": int(n_test_points),
        "n_directions": int(n_directions),
        "n_train_direction_labels": int(n_train_points) * int(n_directions),
        "n_test_direction_labels": int(n_test_points) * int(n_directions),
        "test_refined_models": int(test_refined_models),
        "test_occupancy_fallback_models": int(test_occupancy_fallback_models),
        **{name: float(metrics[name]) for name in required_metrics},
    }


def build_e5_report(
    *,
    data,
    seeds,
    epochs,
    device,
    n_directions,
    n_models,
    target_mode,
    refined_models,
    occupancy_fallback,
    rows,
):
    """Build an E5 envelope without discarding the seed-level evidence."""
    import numpy as np

    rows = list(rows)
    if not rows:
        raise ValueError("at least one seed run is required")
    arr = np.asarray([
        [
            row["dir_f1"],
            row["dir_set_iou"],
            row["recovered_binary_f1"],
            row["majority_dir_baseline_f1"],
            row["topk_hit_top1"],
            row["topk_hit_top3"],
            row["topk_precision_at3"],
        ]
        for row in rows
    ], dtype=float)
    return {
        "data": data,
        "seeds": int(seeds),
        "epochs": int(epochs),
        "device": device,
        "D_dirs": int(n_directions),
        "models": int(n_models),
        "target_mode": target_mode,
        "refined_models": int(refined_models),
        "occupancy_fallback": int(occupancy_fallback),
        "dir_f1_mean": round(float(arr[:, 0].mean()), 3),
        "dir_f1_std": round(float(arr[:, 0].std()), 3),
        "dir_setiou_mean": round(float(arr[:, 1].mean()), 3),
        "recovered_binary_f1_mean": round(float(arr[:, 2].mean()), 3),
        "majority_dir_baseline_f1": round(float(arr[:, 3].mean()), 3),
        "topk_hit_top1_mean": round(float(arr[:, 4].mean()), 3),
        "topk_hit_top3_mean": round(float(arr[:, 5].mean()), 3),
        "topk_precision_at3_mean": round(float(arr[:, 6].mean()), 3),
        "runs": rows,
    }


def main():
    ap = argparse.ArgumentParser(description="E5 方向级可达性场预测（D-024）")
    ap.add_argument("--data", default=str(resolve_data_paths().processed_root("procedural_v1")))
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--n-directions", type=int, default=128)     # D-021 冻结值；下半球得 D≈64
    ap.add_argument("--max-models", type=int, default=None)
    ap.add_argument(
        "--root",
        default=None,
        help="可选 Fusion 原网格根；显式给定才启用 D-020 细化口径（B1a），否则使用占据口径",
    )
    ap.add_argument("--resolution", type=int, default=48, help="须与 ingest 一致（占据逐比特校验）")
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/e5/latest.json")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from artifacts import write_result
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data import split_by_model
    from support_accessibility.oracle import SupportAccessibilityOracle
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    from support_accessibility import eval as E

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    ms, _ = load_dataset(a.data)
    if a.max_models:
        ms = ms[:a.max_models]

    # 方向级目标：blocked=1（风险），(K,D)。缺省占据口径；--root → 载原网格走 D-020 细化（§6.1-B1a）
    mesh_of = {}
    if a.root:
        from support_accessibility.data.fusion360 import iter_final_designs
        mesh_of = {name: path for name, path in iter_final_designs(a.root)}   # 同名后者覆盖，镜像 ingest

    def make_oracle(m):
        """(oracle, refined?)。--root 下重建占据并逐比特校验；不符 → 回落占据口径并计数（不静默混口径）。"""
        if a.root and m.name in mesh_of:
            try:
                from support_accessibility.data.fusion360 import load_obj, normalize
                from support_accessibility.data import mesh as MESH
                V, F = load_obj(mesh_of[m.name])
                Vn, _s = normalize(V)
                occ2, lo, pitch = MESH.mesh_to_occupancy(Vn, F, resolution=a.resolution)
                if occ2.shape == m.occ.shape and bool((occ2 == np.asarray(m.occ, bool)).all()):
                    return SupportAccessibilityOracle(m.occ, {"n_directions": a.n_directions},
                                                     mesh=(Vn, F, lo, pitch)), True
            except Exception:
                pass
        return SupportAccessibilityOracle(m.occ, {"n_directions": a.n_directions}), False

    D = None
    items = []
    n_refined = n_occup = 0
    for m in ms:
        if m.points.shape[0] == 0:
            continue
        o, refined = make_oracle(m)
        n_refined += int(refined)
        n_occup += int(not refined)
        if D is None:
            D = len(o.dirs)
        viable = np.stack([o.direction_labels(p, m.radius) for p in m.points])   # (K,D) True=可达
        items.append((m.name, m.occ, m.points, (~viable).astype(np.float32), bool(refined)))  # blocked=1
    if a.root:
        mode = "refined(D-020)" if n_occup == 0 else "mixed refined(D-020) with occupancy fallback"
    else:
        mode = "occupancy"
    print(f"device={dev} D_dirs={D} models={len(items)} pts={sum(it[2].shape[0] for it in items)} "
          f"target_labels={mode} refined={n_refined} occup_fallback={n_occup}", flush=True)
    if a.root and n_occup:
        print(f"警告：{n_occup} 件未匹配原网格或占据校验不符，回落占据口径（混口径——建议排查后重跑）", flush=True)
    if a.root:
        print("注意：细化口径方向标签作 headline 训练源属命门（D-024）——数字入账前须作者据实签收。", flush=True)

    def prep(occ, pts):
        occt = torch.as_tensor(np.asarray(occ, np.float32)).view(1, 1, *occ.shape).to(dev)
        gc = to_grid_coords(pts, occ.shape).to(dev)
        return occt, gc

    def evaluate(net, test):
        P, G, SC = [], [], []
        with torch.no_grad():
            for _n, occ, pts, blk, _refined in test:
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
        data = [(prep(occ, pts), torch.as_tensor(blk).to(dev)) for _n, occ, pts, blk, _refined in tr]
        for _ in range(a.epochs):
            for i in torch.randperm(len(data)):
                (occt, gc), y = data[i]
                opt.zero_grad(); lossf(net(occt, gc), y).backward(); opt.step()
        net.eval()
        f1, dir_iou, bin_f1, top1, top3, prec3 = evaluate(net, te)
        # 对照：per-direction 多数类基线（train 每方向 blocked 先验）
        tr_t = np.concatenate([blk.reshape(-1, D) for _n, _o, _p, blk, _refined in tr])
        maj = (tr_t.mean(0) >= 0.5)
        te_t = np.concatenate([blk.reshape(-1, D) for _n, _o, _p, blk, _refined in te]).astype(bool)
        base_f1 = E.f1_inaccessible(np.broadcast_to(maj, te_t.shape).ravel(), te_t.ravel())
        split_rule = f"model-level random 70/30 holdout; seed={seed}"
        rows.append(build_seed_run_record(
            seed=seed,
            n_train_models=len(tr),
            n_test_models=len(te),
            n_train_points=sum(pts.shape[0] for _n, _occ, pts, _blk, _refined in tr),
            n_test_points=sum(pts.shape[0] for _n, _occ, pts, _blk, _refined in te),
            n_directions=D,
            test_refined_models=sum(int(refined) for _n, _occ, _pts, _blk, refined in te),
            test_occupancy_fallback_models=sum(int(not refined) for _n, _occ, _pts, _blk, refined in te),
            split_rule=split_rule,
            metrics={
                "dir_f1": f1,
                "dir_set_iou": dir_iou,
                "recovered_binary_f1": bin_f1,
                "majority_dir_baseline_f1": base_f1,
                "topk_hit_top1": top1,
                "topk_hit_top3": top3,
                "topk_precision_at3": prec3,
            },
        ))
        print(f"seed{seed} dir_f1={f1:.3f} dir_iou={dir_iou:.3f} bin_f1={bin_f1:.3f} "
              f"top1={top1:.3f} top3={top3:.3f} prec@3={prec3:.3f} maj_base_f1={base_f1:.3f}", flush=True)

    rep = build_e5_report(
        data=logical_data_ref(a.data),
        seeds=a.seeds,
        epochs=a.epochs,
        device=dev,
        n_directions=D,
        n_models=len(items),
        target_mode=mode,
        refined_models=n_refined,
        occupancy_fallback=n_occup,
        rows=rows,
    )
    rep = write_result("e5", rep, output=a.out, inputs=(a.data, a.root or ""))
    print("E5_RESULT " + json.dumps(rep))


if __name__ == "__main__":
    main()
