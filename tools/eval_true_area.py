#!/usr/bin/env python3
"""H1 真面积对照复现器（指引 §6.1-B3）：以真实三角面积复算"支撑面积—可达性"相关。

eval_h1 的"支撑面积"是下朝面**计数**代理（逐三角质心、未面积加权）。本工具从原 .obj 重建
S(P,d) 并**复现 ingest 的缠绕安全外移三态**（D-028：丢 flipped、保 free/confined），使保留面序列
与 npz 点序 1:1 对齐（逐件点数 + 逐点坐标校验，不符即跳过并计数——不静默）；按三角面积加权
聚合每件"不可达面积占比"，报告 Spearman ρ(总下朝面积 vs 不可达面积占比) 全体/两类两口径，
并列同一批件上的计数代理 ρ 供直接对照。产出入 results.md 后供论文局限（面积口径）引用。self-add src。

用法：
  conda run -n saf python tools/eval_true_area.py --data ${SAF_TEMPORARY_ROOT}/SAF/fusion360_full/latest \
    --root E:/Work/Data/Fusion360Gallery/reconstruction
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


def main():
    ap = argparse.ArgumentParser(description="H1 真面积对照（面积加权；复现 D-028 三态剔除以对齐 npz 点序）")
    paths = resolve_data_paths()
    ap.add_argument("--data", default=str(paths.processed_root("fusion360_full")))
    ap.add_argument("--root", default=str(paths.fusion360_root), help="Fusion reconstruction 原网格根")
    ap.add_argument("--resolution", type=int, default=48)      # 须与 ingest 一致（否则对齐校验会拒）
    ap.add_argument("--overhang-deg", type=float, default=45.0)
    ap.add_argument("--nudge-voxels", type=float, default=2.0)
    ap.add_argument("--max-models", type=int, default=None)
    ap.add_argument("--out", default="artifacts/runs/true_area/latest.json")
    a = ap.parse_args()

    import json
    import numpy as np
    from artifacts import write_result
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data.fusion360 import iter_final_designs, load_obj, normalize
    from support_accessibility.data import mesh as MESH, overhang as OVH
    from support_accessibility import eval as E

    ms, rows = load_dataset(a.data)
    if a.max_models:
        ms = ms[:a.max_models]
    path_of = {name: path for name, path in iter_final_designs(a.root)}   # 同名后者覆盖，镜像 ingest 覆写序

    d = np.array([0.0, 0.0, 1.0])
    area_tot, area_frac, cnt_tot, cnt_frac, per_model = [], [], [], [], []
    done = miss = mismatch = bad = 0
    for m, row in zip(ms, rows):
        if m.points.shape[0] == 0:
            continue
        p = path_of.get(m.name)
        if p is None:
            miss += 1
            continue
        try:
            V, F = load_obj(p)
            Vn, _s = normalize(V)
            occ, lo, pitch = MESH.mesh_to_occupancy(Vn, F, resolution=a.resolution)
            sc = OVH.support_contact_faces(Vn, F, d, a.overhang_deg)
        except Exception:
            bad += 1
            continue
        tri = np.asarray(Vn, float)[np.asarray(F, np.int64)[sc.indices]]          # (k,3,3) 下朝三角
        areas = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
        kept_q, kept_area = [], []
        for c, n, ar in zip(sc.centroids, sc.normals, areas):
            status, q = MESH.nudge_to_free(occ, c, n, a.nudge_voxels * pitch, lo, pitch)
            if status == "flipped":                        # 复现 D-028 剔除 → 保留序 == npz 点序
                continue
            kept_q.append(q)
            kept_area.append(float(ar))
        if len(kept_q) != m.points.shape[0] or not np.allclose(
                np.asarray(kept_q, np.float32), np.asarray(m.points, np.float32), atol=1e-2):
            mismatch += 1                                  # 对齐失败：跳过并计数（不静默；勿混标签）
            continue
        lab = np.asarray(m.labels, bool)
        kept_area = np.asarray(kept_area, float)
        s = float(kept_area.sum())
        if s <= 0:
            bad += 1
            continue
        done += 1
        area_tot.append(s)
        area_frac.append(float(kept_area[lab].sum()) / s)  # 不可达面积占比（面积加权）
        cnt_tot.append(float(lab.size))
        cnt_frac.append(float(lab.mean()))
        per_model.append({"name": m.name, "split": row.get("split", ""),
                          "contact_area": s,
                          "inaccessible_area_fraction": float(kept_area[lab].sum()) / s,
                          "contact_count": int(lab.size),
                          "inaccessible_count_fraction": float(lab.mean())})

    area_tot, area_frac = np.asarray(area_tot), np.asarray(area_frac)
    cnt_tot, cnt_frac = np.asarray(cnt_tot), np.asarray(cnt_frac)
    both_a = (area_frac > 0) & (area_frac < 1)
    both_c = (cnt_frac > 0) & (cnt_frac < 1)
    out = {
        "data": logical_data_ref(a.data, paths),
        "source_root": logical_data_ref(a.root, paths),
        "models_used": done, "skipped_no_mesh": miss,
        "skipped_align_mismatch": mismatch, "skipped_bad": bad,
        "true_area": {
            "spearman_all": round(E.spearman(area_tot, area_frac), 4),
            "n_both_class": int(both_a.sum()),
            "spearman_bothclass": round(E.spearman(area_tot[both_a], area_frac[both_a]), 4) if both_a.sum() >= 2 else 0.0,
        },
        "count_proxy_same_models": {
            "spearman_all": round(E.spearman(cnt_tot, cnt_frac), 4),
            "spearman_bothclass": round(E.spearman(cnt_tot[both_c], cnt_frac[both_c]), 4) if both_c.sum() >= 2 else 0.0,
        },
        "interpretation": "真面积 ρ 与计数代理 ρ 同量级或更小 ⟹ H1 弱相关结论非计数代理伪影（论文局限-面积口径引用）",
        "per_model": per_model,
    }
    out = write_result("true_area", out, a.out, (a.data, a.root))
    out["output"] = os.path.abspath(a.out)
    summary = {key: value for key, value in out.items() if key != "per_model"}
    print("TRUE_AREA_RESULT " + json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
