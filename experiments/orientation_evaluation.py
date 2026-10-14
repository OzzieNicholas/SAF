#!/usr/bin/env python3
"""构建方向评价：对给定的候选方向集合比较支撑接触区的可达性风险（评价，不做方向优化）。

对固定留出集的每个零件取 6 个轴向构建方向 d ∈ {+z, −z, +x, −x, +y, −y}：把零件刚性旋转使 d 对齐 +z，
按入库口径重新提取下朝接触区、外移查询点、用两级判定器打标签，再用固定留出模型（只在原始 +z 朝向训练）
预测。+z 朝向与数据集逐点一致，作为自检。

每个零件得到 6 个方向上的三种量：真实不可达接触面积、网络预测的不可达接触面积、接触总面积
（传统支撑量指标；与前两者一样只计入未被判为翻面的下朝面）。报告：
  - 各方向的点池 F1（原始朝向 vs 旋转朝向，检验网络对未训练朝向的分布偏移）；
  - 逐件 Spearman ρ：网络排序与真实排序、接触面积排序与真实排序；
  - 最低风险方向命中率：网络（或接触面积）选出的方向是否属于真实不可达面积最小的方向。
每个接触面以其质心查询点的标签代表整个三角面，面积口径因此受三角剖分影响（一个大三角面可主导一个方向的
面积）；同时按点数口径（不可达点数、接触点数）重算全部排序指标，作为不依赖面积权重的稳健性对照。

用法：
  python experiments/orientation_evaluation.py
"""
import argparse

from support_accessibility.data.overhang import AXIS_BUILD_ROTATIONS as ORIENTATIONS
from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths

setup_console()


def label_orientation(Vn, F):
    """按入库口径在 +z 构建方向下标注已旋转的零件（mesh.label_mesh），返回 (标注 dict, 各接触面的面积)。"""
    from support_accessibility.data import mesh as MESH
    lab = MESH.label_mesh(Vn, F)
    return lab, MESH.face_areas(Vn, F, lab["faces"])


def main():
    ap = argparse.ArgumentParser(description="构建方向评价（6 个轴向候选方向）")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--root", default=str(paths.fusion360_root))
    ap.add_argument("--limit", type=int, default=None, help="只评前 N 件（试跑用）")
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/orientation_evaluation/result.json（试跑请指定其他路径）")
    a = ap.parse_args()

    import json
    import time
    import numpy as np
    import torch
    from holdout_model import load_holdout_models, mean_std, predict_proba      # 同目录脚本
    from support_accessibility.runtime.run_records import write_result
    from support_accessibility.data import LabeledModel
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data.fusion360 import iter_final_designs, load_obj, normalize
    from support_accessibility import eval as E

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    nets = load_holdout_models(dev)
    seeds = [s for s, _n, _c in nets]
    test_names = list(nets[0][2]["test_names"])
    names = test_names[: a.limit] if a.limit else test_names
    stored = {m.name: m for m in load_dataset(a.fusion)[0] if m.name in set(names)}
    mesh_path = dict(iter_final_designs(a.root))
    keys = list(ORIENTATIONS)

    parts, golds = [], {k: [] for k in keys}
    preds = {s: {k: [] for k in keys} for s in seeds}
    native_agree = []
    t_label = t_net = 0.0
    for i, name in enumerate(names):
        V, F = load_obj(mesh_path[name])
        rows = {}
        for key, R in ORIENTATIONS.items():
            Vr, _ = normalize(np.asarray(V, float) @ np.asarray(R, float).T)
            t0 = time.perf_counter()
            lab, area = label_orientation(Vr, F)
            gold = lab["labels"]
            t_label += time.perf_counter() - t0
            golds[key].append(gold)
            pred_area, pred_points = [], []
            for seed, net, _ck in nets:
                t0 = time.perf_counter()
                part = LabeledModel(name, lab["occ"], lab["points"], gold, lab["radius"])
                pred = predict_proba(net, part, dev) >= 0.5 if gold.size else np.zeros(0, bool)
                t_net += time.perf_counter() - t0
                preds[seed][key].append(pred)
                pred_area.append(float(area[pred].sum()))
                pred_points.append(int(pred.sum()))
            if key == "+z":
                ref = stored[name]
                native_agree.append(bool(gold.size == ref.labels.size and np.array_equal(gold, ref.labels)))
            rows[key] = {"n_points": int(gold.size), "contact_area": float(area.sum()),
                         "true_inacc_area": float(area[gold].sum()), "true_inacc_points": int(gold.sum()),
                         "pred_inacc_area_by_seed": pred_area, "pred_inacc_points_by_seed": pred_points}
        parts.append({"name": name, "orientations": rows})
        print(f"{i + 1}/{len(names)} {name}", flush=True)

    def ranking(truth_key, score_of):
        """逐件比较某一打分与真实风险：返回 (Spearman 均值, 最低风险方向命中率)。"""
        rhos, hits = [], 0
        for p in parts:
            true = np.array([p["orientations"][k][truth_key] for k in keys], float)
            score = np.array([score_of(p["orientations"][k]) for k in keys], float)
            best = np.isclose(true, true.min(), rtol=0, atol=1e-12)
            hits += int(best[int(np.argmin(score))])
            if true.std() > 0:
                rhos.append(E.spearman(score, true))
        return float(np.mean(rhos)), hits / len(parts)

    def measure(truth_key, contact_key, pred_key):
        """一种风险口径下的接触量排序、网络排序与随机期望。"""
        rho_c, hit_c = ranking(truth_key, lambda o: o[contact_key])
        net = [ranking(truth_key, lambda o, j=j: o[pred_key][j]) for j in range(len(seeds))]
        hit_rand = float(np.mean([np.isclose(t, t.min(), rtol=0, atol=1e-12).mean() for t in (
            np.array([p["orientations"][k][truth_key] for k in keys], float) for p in parts)]))
        rho_m, rho_s = mean_std([r for r, _h in net])
        hit_m, hit_s = mean_std([h for _r, h in net])
        return {"spearman_network_vs_true_mean": rho_m, "spearman_network_vs_true_std": rho_s,
                "spearman_contact_vs_true_mean": round(rho_c, 4),
                "lowest_risk_hit_network": hit_m, "lowest_risk_hit_network_std": hit_s,
                "lowest_risk_hit_contact": round(hit_c, 4), "lowest_risk_hit_random_expected": round(hit_rand, 4)}

    by_area = measure("true_inacc_area", "contact_area", "pred_inacc_area_by_seed")
    by_points = measure("true_inacc_points", "n_points", "pred_inacc_points_by_seed")
    n_rankable = sum(np.std([p["orientations"][k]["true_inacc_area"] for k in keys]) > 0 for p in parts)

    def f1_of(seed, which):
        P = np.concatenate([np.concatenate(preds[seed][k]) for k in which])
        G = np.concatenate([np.concatenate(golds[k]) for k in which])
        return float(E.f1_inaccessible(P, G))

    per_orientation = {}
    for k in keys:
        m, s = mean_std([f1_of(seed, [k]) for seed in seeds])
        G = np.concatenate(golds[k])
        per_orientation[k] = {"pooled_f1": m, "pooled_f1_std": s, "n_points": int(G.size), "n_inaccessible": int(G.sum())}
    rot_m, rot_s = mean_std([f1_of(seed, [k for k in keys if k != "+z"]) for seed in seeds])
    rep = write_result("orientation_evaluation", {
        "model_run": "holdout_model", "training_seeds": seeds, "n_parts": len(parts), "orientations": keys,
        "native_orientation_matches_dataset": round(float(np.mean(native_agree)), 4),
        "per_orientation": per_orientation,
        "rotated_pooled_f1": rot_m, "rotated_pooled_f1_std": rot_s,
        "n_parts_rankable": int(n_rankable),
        "by_area": by_area, "by_point_count": by_points,
        "seconds_labeling_total": round(t_label, 2), "seconds_network_total": round(t_net, 2),
        "parts": parts,
    }, a.out, (a.fusion, a.root))
    print("ORIENTATION " + json.dumps({k: v for k, v in rep.items() if k != "parts"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
