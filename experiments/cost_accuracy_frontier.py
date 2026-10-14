#!/usr/bin/env python3
"""精度–耗时前沿：在固定留出集上比较各几何判定口径与网络的每件耗时和不可达类 F1。

参考标签是数据集中冻结的两级标签（128 全局方向 + 边界带胶囊细化）。比较对象：
  - 纯体素判定（无细化），全局方向数 8 / 16 / 32 / 64 / 128 / 256；
  - 零半径射线可见性（128 方向）；
  - 两级标签器本身（重算，核对与冻结标签的一致率，并给出生成标签的真实耗时）；
  - 固定留出模型（experiments/holdout_model.py 的权重），GPU 与 CPU（单线程）各计一次。
每件耗时从占据栅格开始计：几何方法含距离场构造与逐点判定，两级标签器另含网格预处理与细化，
网络含张量上传与一次前向。网格→占据栅格对所有方法相同，单列为公共预处理耗时。

用法：
  python experiments/cost_accuracy_frontier.py
"""
import argparse
import time

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths
from support_accessibility.runtime.frozen_params import FROZEN

setup_console()

VOXEL_DIRECTIONS = (8, 16, 32, 64, 128, 256)


def main():
    ap = argparse.ArgumentParser(description="精度–耗时前沿（固定留出集）")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--root", default=str(paths.fusion360_root), help="Fusion 原网格根（两级标签器需要网格）")
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/cost_accuracy_frontier/result.json（试跑请指定其他路径）")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from holdout_model import holdout_split, load_holdout_model, load_holdout_models, predict_proba   # 同目录脚本
    from support_accessibility.runtime.run_records import write_result
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data.fusion360 import iter_final_designs, load_obj, normalize
    from support_accessibility.data import mesh as MESH
    from support_accessibility.oracle import SupportAccessibilityOracle
    from support_accessibility.models.convonet import to_grid_coords
    from support_accessibility import baselines as B, eval as E

    fus, _ = load_dataset(a.fusion)
    _tr, _va, test = holdout_split(fus)
    torch.set_num_threads(1)                  # 与单进程单线程的几何方法同条件计时
    gpu = torch.cuda.is_available()
    net_gpu, ckpt = load_holdout_model(0, "cuda" if gpu else "cpu")       # 计时用种子 0；精度报全部种子
    if [m.name for m in test] != list(ckpt["test_names"]):
        raise RuntimeError("留出集与固定留出模型的测试名单不一致")
    net_cpu, _ = load_holdout_model(0, "cpu")
    mesh_path = dict(iter_final_designs(a.root))
    print(f"test parts={len(test)} gpu={gpu}", flush=True)

    def timed(fn):
        t0 = time.perf_counter()
        out = fn()
        return out, time.perf_counter() - t0

    def net_labels(net, occ, pts, dev):
        occ_t = torch.as_tensor(np.asarray(occ, np.float32)).view(1, 1, *occ.shape).to(dev)
        gc = to_grid_coords(pts, occ.shape).to(dev)
        with torch.no_grad():
            prob = torch.sigmoid(net(occ_t, gc))
        if dev == "cuda":
            torch.cuda.synchronize()
        return prob.cpu().numpy().reshape(-1) >= 0.5

    # 预热：CUDA 首次前向与 VTK/igl 首次调用的开销不计入
    m0 = test[0]
    net_labels(net_gpu, m0.occ, m0.points, "cuda" if gpu else "cpu")
    net_labels(net_cpu, m0.occ, m0.points, "cpu")

    methods = [f"voxel_{n}" for n in VOXEL_DIRECTIONS] + ["ray_r0_128", "two_stage_128", "network_gpu", "network_cpu"]
    preds = {k: [] for k in methods}
    secs = {k: [] for k in methods + ["occupancy"]}
    golds, names, n_points, refine_agree = [], [], [], []
    for i, m in enumerate(test):
        gold = np.asarray(m.labels, bool)
        pts, r, occ = m.points, float(m.radius), np.asarray(m.occ, bool)
        V, F = load_obj(mesh_path[m.name])
        Vn, _ = normalize(V)
        (occ2, lo, pitch), t_occ = timed(lambda: MESH.mesh_to_occupancy(Vn, F, resolution=FROZEN.resolution))
        if occ2.shape != occ.shape or not np.array_equal(occ2, occ):
            raise RuntimeError(f"占据栅格与数据集不一致：{m.name}")
        secs["occupancy"].append(t_occ)
        for n in VOXEL_DIRECTIONS:
            p, t = timed(lambda: B.voxel_judgment(occ, pts, r, n))
            preds[f"voxel_{n}"].append(p); secs[f"voxel_{n}"].append(t)
        p, t = timed(lambda: B.ray_visibility(occ, pts))
        preds["ray_r0_128"].append(p); secs["ray_r0_128"].append(t)

        def two_stage():
            o = SupportAccessibilityOracle(occ, {"n_directions": FROZEN.n_directions}, mesh=(Vn, F, lo, pitch))
            return np.array([o.label(q, r).value == "inaccessible" for q in pts], bool)
        p, t = timed(two_stage)
        preds["two_stage_128"].append(p); secs["two_stage_128"].append(t)
        refine_agree.append(float((p == gold).mean()))
        p, t = timed(lambda: net_labels(net_gpu, occ, pts, "cuda" if gpu else "cpu"))
        preds["network_gpu"].append(p); secs["network_gpu"].append(t)
        p, t = timed(lambda: net_labels(net_cpu, occ, pts, "cpu"))
        preds["network_cpu"].append(p); secs["network_cpu"].append(t)
        golds.append(gold); names.append(m.name); n_points.append(int(gold.size))
        if (i + 1) % 10 == 0:
            print(f"{i + 1}/{len(test)} parts", flush=True)

    G = np.concatenate(golds)
    rows = {}
    for k in methods:
        per = np.array([E.f1_inaccessible(p, g) for p, g in zip(preds[k], golds)])
        s = np.array(secs[k])
        rows[k] = {"pooled_f1": round(float(E.f1_inaccessible(np.concatenate(preds[k]), G)), 4),
                   "part_f1_mean": round(float(per.mean()), 4),
                   "seconds_per_part_mean": round(float(s.mean()), 5),
                   "seconds_per_part_median": round(float(np.median(s)), 5),
                   "ms_per_point": round(float(s.sum() / G.size * 1e3), 4)}
    seed_f1 = [float(E.f1_inaccessible(np.concatenate([predict_proba(net, m, "cuda" if gpu else "cpu") >= 0.5
                                                        for m in test]), G))
               for _s, net, _c in load_holdout_models("cuda" if gpu else "cpu")]
    rows["network_gpu"]["pooled_f1_seed_mean"] = round(float(np.mean(seed_f1)), 4)
    rows["network_gpu"]["pooled_f1_seed_std"] = round(float(np.std(seed_f1)), 4)
    rows["network_gpu"]["pooled_f1_by_seed"] = [round(v, 4) for v in seed_f1]
    occ_s = np.array(secs["occupancy"])
    rep = write_result("cost_accuracy_frontier", {
        "reference": "frozen two-stage labels (128 global directions, boundary-band capsule refinement)",
        "n_test_models": len(test), "n_test_points": int(G.size), "gpu": gpu,
        "device_name": torch.cuda.get_device_name(0) if gpu else "cpu",
        "voxel_directions": list(VOXEL_DIRECTIONS),
        "occupancy_seconds_per_part_mean": round(float(occ_s.mean()), 5),
        "occupancy_seconds_per_part_median": round(float(np.median(occ_s)), 5),
        "two_stage_relabel_agreement_mean": round(float(np.mean(refine_agree)), 6),
        "methods": rows,
        "timing_note": "single process, single CPU thread, wall clock per part from occupancy grid; occupancy construction listed separately and shared by all methods",
        "per_part": {"names": names, "n_points": n_points,
                     "seconds": {k: [round(float(v), 5) for v in secs[k]] for k in secs}},
    }, a.out, (a.fusion, a.root))
    print("COST_ACCURACY_FRONTIER " + json.dumps({k: v for k, v in rep.items() if k != "per_part"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
