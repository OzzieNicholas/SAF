#!/usr/bin/env python3
"""量化标签有效性审核（D-018 客观化：以数据指标替代人工视觉签收）。

无外部物理真值（非目标），故"标签有效"= 三条可量化性质：
  (a) 实现正确性 differential：占据口径 oracle.label(纯体素) vs oracle.reference_label(暴力 球∩实体体素) 一致
      —— 独立参考验射线-march 口径在真实占据上正确（test_differential 的真实数据版）。
  (b) 离散鲁棒性 res_stability（需 --root 原网格）：同一世界接触点在 res 48 vs 96（+D-020 细化）标签一致率
      —— 验低分辨率足够、标签非离散伪影（D-020 在样本上得 1.000 的真实数据放大版）。
  (c) 分布合理性 distribution：不可达占比、两类件占比、退化(单类)件占比 —— 非退化学习问题。
细化层由 test_capsule（精确几何原语）守护。本工具在真实数据上给客观数字，替代易错的人工视觉审核。self-add src。

用法：
  conda run -n saf python tools/audit_labels.py --data data/processed/fusion360_full --root E:/Fusion360Gallery/reconstruction
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
    ap = argparse.ArgumentParser(description="量化标签有效性审核（D-018 客观化）")
    ap.add_argument("--data", default="data/processed/fusion360_full")
    ap.add_argument("--root", default=None, help="原网格根（给定则跑 res-稳定审核）")
    ap.add_argument("--sample-points", type=int, default=160, help="差分审核采样点数（暴力参考较慢）")
    ap.add_argument("--stability-models", type=int, default=10)
    ap.add_argument("--n-directions", type=int, default=128)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--write", action="store_true", help="把 label_audit 块 + human_signoff=verdict 写回 dataset.json")
    a = ap.parse_args()

    import json
    import numpy as np
    from collections import defaultdict
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.oracle import SupportAccessibilityOracle, Label

    ms, _ = load_dataset(a.data)
    rng = np.random.default_rng(a.seed)
    INACC = Label.INACCESSIBLE

    # (c) 分布（全体）
    inacc, npts, both, single = [], [], 0, 0
    for m in ms:
        lab = np.asarray(m.labels, bool)
        if lab.size == 0:
            continue
        npts.append(lab.size); inacc.append(float(lab.mean()))
        if lab.any() and (~lab).any():
            both += 1
        else:
            single += 1
    inacc = np.array(inacc)
    dist = {"models": len(npts), "inacc_frac_mean": round(float(inacc.mean()), 3),
            "both_class_model_frac": round(both / max(len(npts), 1), 3),
            "single_class_model_frac": round(single / max(len(npts), 1), 3),
            "pts_per_model_median": int(np.median(npts)) if npts else 0}

    # (a) 差分（D-003 口径）：纯体素 oracle vs 暴力参考。**边界带 ~1 体素差可容忍**（EDT 体素 vs 连续距离，
    #     阈值附近必然小差，refinement 正是处理此带）；仅 **robust 不一致**（r±ε 邻域仍不一致）= 真 bug。
    EPS_B = 0.75
    k = a.sample_points // 2
    pos, neg = [], []
    for mi in rng.permutation(len(ms)):
        if len(pos) >= k and len(neg) >= k:
            break
        lab = np.asarray(ms[mi].labels, bool)
        for pi in range(lab.size):
            if lab[pi] and len(pos) < k:
                pos.append((mi, pi, True))
            elif (not lab[pi]) and len(neg) < k:
                neg.append((mi, pi, False))
    bym = defaultdict(list)
    for mi, pi, sl in pos + neg:
        bym[mi].append((pi, sl))
    strict = robust = changed = n = 0
    for mi, plist in bym.items():
        m = ms[mi]
        o = SupportAccessibilityOracle(m.occ, {"n_directions": a.n_directions})   # 无网格 → 纯体素
        for pi, sl in plist:
            p, r = m.points[pi], float(m.radius)
            vox = (o.label(p, r) == INACC)
            ref = (o.reference_label(p, r) == INACC)
            n += 1; changed += int(sl != vox)
            if vox == ref:
                strict += 1
            elif not all(o.label(p, r + dd).value == o.reference_label(p, r + dd).value
                         for dd in (-EPS_B, EPS_B)):
                robust += 1                                                       # 非边界 → 真差异
    diff = {"sample_n": n, "robust_mismatch_rate": round(robust / max(n, 1), 4),
            "strict_agreement": round(strict / max(n, 1), 4),
            "boundary_tolerated_rate": round((n - strict - robust) / max(n, 1), 4),
            "refinement_changed_frac": round(changed / max(n, 1), 4)}

    # (b) res-稳定（需原网格）：同世界接触点 res48 vs res96 标签一致
    stab = None
    if a.root:
        from support_accessibility.data.fusion360 import _meshes_from_root, normalize
        from support_accessibility.data import mesh as MESH, overhang as OVH
        d = np.array([0., 0, 1.]); tot = ag = done = 0
        for name, V, F in _meshes_from_root(a.root):
            if done >= a.stability_models:
                break
            try:
                Vn, _s = normalize(V)
                sc = OVH.support_contact_faces(Vn, F, d, 45.0)
                if len(sc.centroids) == 0:
                    continue
                res_labs, res_keep = {}, {}
                for res in (48, 96):
                    occ, lo, pitch = MESH.mesh_to_occupancy(Vn, F, resolution=res)
                    r = 0.05 / pitch
                    o = SupportAccessibilityOracle(occ, {"n_directions": a.n_directions}, mesh=(Vn, F, lo, pitch))
                    ll, kk = [], []
                    for c, nn in zip(sc.centroids, sc.normals):
                        status, q = MESH.nudge_to_free(occ, c, nn, 2.0 * pitch, lo, pitch)   # 同 ingest 口径（D-028）
                        ll.append((o.label(q, r).value == "inaccessible") if status != "flipped" else False)
                        kk.append(status != "flipped")
                    res_labs[res] = np.array(ll); res_keep[res] = np.array(kk)
                keep = res_keep[48] & res_keep[96]                      # 两 res 都非翻转的面才可比（与 ingest 一致）
                ag += int((res_labs[48][keep] == res_labs[96][keep]).sum()); tot += int(keep.sum()); done += 1
            except Exception as e:
                print("skip", name, str(e)[:50], flush=True)
        stab = {"models": done, "points": tot,
                "res48_vs_res96_agreement": round(ag / max(tot, 1), 4)}

    verdict = (diff["robust_mismatch_rate"] <= 0.01                              # D-003：robust 不一致≈0（边界带容忍）
               and 0.01 <= dist["inacc_frac_mean"] <= 0.9
               and dist["both_class_model_frac"] > 0.0
               and stab is not None and stab["res48_vs_res96_agreement"] >= 0.95)   # 命门须含 res-稳定腿（缺 --root→verdict False，与拒写一致）
    audit = {"verdict_pass": bool(verdict), "n_directions": a.n_directions,
             "differential": diff, "res_stability": stab, "distribution": dist,
             "criterion": "D-003 robust 差分(边界带容忍) + D-020 res-稳定 + 分布；阈值 robust≤0.01/res≥0.95/inacc∈[0.01,0.9]（D-025）"}
    print("LABEL_AUDIT " + json.dumps({"data": a.data, **audit}, ensure_ascii=False))

    if a.write and stab is None:            # 命门不半证签收：res-稳定腿缺失（需 --root）→ 拒写 signoff（D-025/铁律#7）
        sys.exit("拒绝写 human_signoff：res-稳定审核缺失（需 --root 原网格跑 res48-vs-96），命门须全证据（D-025）")

    if a.write:
        djson = os.path.join(a.data, "dataset.json")
        d = json.load(open(djson, encoding="utf-8"))
        d["label_audit"] = audit                                    # 客观证据（替代裸 human_signoff，D-025）
        d["human_signoff"] = bool(verdict)                          # 由量化审核裁定，非人工视觉
        json.dump(d, open(djson, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"WROTE label_audit + human_signoff={bool(verdict)} -> {djson}")


if __name__ == "__main__":
    main()
