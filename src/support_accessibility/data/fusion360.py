"""Fusion 360 Gallery reconstruction 网格 ingest（D-017）：真实 CAD 网格 → 统一 processed 数据集。

只用**最终零件**的 .obj 三角网格；.json **仅作 final 存在标记（看基名在否）、从不打开/解析其构造序列内容**，
.smt/.step B-Rep 不碰（故非 CAD 序列建模）。管线：
  走目录取 final obj（.obj 有同名 .json 兄弟＝final 存在标记）→ load_obj → normalize（最长边=1，闭合体素↔归一单位桥）
  → mesh_to_occupancy（igl winding number, D-009）→ 下朝悬垂面 S(P,d)（D-010）取支撑接触点
  → oracle 打标（语义 C, D-001..D-003）→ 物化 D-016 记录（source=fusion360）+ viz 审计图。

铁律 #6 / D-018（发放机制经 D-025 客观化）：真实网格 oracle 有效性**未过审核**前，本 ingest 记
`human_signoff=false`，不得直接进训练集。**验证由量化审核** `tools/audit_labels.py`（差分/res-稳定/分布，
D-025）裁定并写 `label_audit` + 置 human_signoff——**非人工视觉审图**（视觉主观、不可复现、易造假绿）。

模块级只 stdlib（os）；numpy/igl/trimesh/oracle 在函数内 import（沿袭 data 包约定，裸 py 仍可 import）。
纯逻辑（_parse_obj_text / iter_final_designs）不依赖 numpy，可在无几何栈环境直接自检。
"""

import os


# ————— 纯 stdlib：OBJ 解析 + 目录遍历（裸环境可执行自检） —————
def _parse_obj_text(text):
    """OBJ 文本 → (verts[list[3 float]], faces[list[3 int]])，仅取 v / f。

    f 支持 'v'、'v/vt'、'v//vn'、'v/vt/vn'（取首索引）；多边形面扇形三角化；1-based→0-based；支持负索引。
    """
    verts, faces = [], []
    for ln in text.splitlines():
        if ln.startswith("v "):
            p = ln.split()
            verts.append([float(p[1]), float(p[2]), float(p[3])])
        elif ln.startswith("f "):
            idx = [int(tok.split("/")[0]) for tok in ln.split()[1:]]
            idx = [(i - 1) if i > 0 else (len(verts) + i) for i in idx]   # 负索引=从末尾数
            for k in range(1, len(idx) - 1):                              # 扇形三角化
                faces.append([idx[0], idx[k], idx[k + 1]])
    return verts, faces


def iter_final_designs(root):
    """走 reconstruction 目录，产出 (design_name, obj_path)：只取 final 零件网格。

    判据：.obj 有同名 .json 兄弟（同目录）＝final 存在标记。真实数据里 final（<id>_<hash>_<reconIdx>）
    与中间拉伸步骤（..._<reconIdx>_<stepIdx>）都以 _NNNN 结尾、无法靠后缀区分；仅 final 有构造序列 .json 兄弟。
    D-017：.json **只作存在标记（看基名在否），从不打开/解析其内容**（不碰构造序列）。
    每目录内先收 .json 基名集合再判 .obj → sorted 保确定性；.json 无对应 .obj 者不产出（只遍历 .obj）。
    """
    for dirpath, _dirs, files in sorted(os.walk(root), key=lambda t: t[0]):   # 目录序确定（跨机字节可复现，配 sorted(files)）
        json_bases = {fn[:-5] for fn in files if fn.endswith(".json")}   # 仅取基名（存在标记），不读内容
        for fn in sorted(files):
            if fn.endswith(".obj") and fn[:-4] in json_bases:
                yield fn[:-4], os.path.join(dirpath, fn)


# ————— numpy/几何栈：归一 / 载入 / 筛选 / 物化 —————
def load_obj(path):
    """OBJ 文件 → (V[np (n,3) float], F[np (m,3) int32])。纯 stdlib 解析 + numpy 包壳（绕开 trimesh，D-009）。"""
    import numpy as np
    with open(path, encoding="utf-8", errors="replace") as f:
        verts, faces = _parse_obj_text(f.read())
    return np.asarray(verts, float), np.asarray(faces, np.int32)


def normalize(V):
    """归一到最长包围盒边 = 1（configs/params.yaml geometry.normalize）：居中 + 除以最长边。返回 (V_norm, scale)。"""
    import numpy as np
    V = np.asarray(V, float)
    lo, hi = V.min(0), V.max(0)
    scale = float((hi - lo).max()) or 1.0
    return (V - (lo + hi) / 2.0) / scale, scale


def qualify(V, F, min_faces=8, max_faces=200000, d=(0.0, 0.0, 1.0), overhang_deg=45.0):
    """§4.8 几何轻筛（非 oracle 判定）。返回 (ok, reason)：面数非退化区间 + 存在下朝悬垂面（否则无接触区可评）。"""
    import numpy as np
    from support_accessibility.data.overhang import support_contact_faces
    F = np.asarray(F)
    if F.shape[0] < min_faces:
        return False, f"面数过少({F.shape[0]}<{min_faces})"
    if F.shape[0] > max_faces:
        return False, f"面数过多({F.shape[0]}>{max_faces})"
    sc = support_contact_faces(V, F, d, overhang_deg)
    if len(sc.centroids) == 0:
        return False, "无下朝悬垂面（无支撑接触区可评）"
    return True, f"面数{F.shape[0]}、悬垂面{len(sc.centroids)}"


def build_from_meshes(meshes, out_dir, d=(0.0, 0.0, 1.0), resolution=48, radius_world=0.05,
                      overhang_deg=45.0, n_directions=128, nudge_voxels=2.0,
                      max_models=None, emit_audit=True, frac_train=0.6, frac_val=0.2, seed=0):
    """(name, V, F) 迭代 → 物化 D-016 记录（source=fusion360，按模型三切 train/val/test）+ viz 审计图。

    radius_world 在归一尺度（最长边=1）下。支撑接触点 = 下朝悬垂面质心沿外法向外移 nudge_voxels 体素到自由侧。
    D-018/D-025：本 ingest 记 human_signoff=false；有效性由量化审核 `tools/audit_labels.py` 裁定后置真。返回 out_dir。
    """
    os.makedirs(out_dir, exist_ok=True)                 # models/、audit/ 由 save_model / montage 各自建
    audit_dir = os.path.join(out_dir, "audit")
    records = []
    n_flip_total = 0
    for name, V, F in meshes:
        if max_models is not None and len(records) >= max_models:
            break
        Vn, _s = normalize(V)
        if not qualify(Vn, F, d=d, overhang_deg=overhang_deg)[0]:
            continue
        rec, n_flip = _label_one(name, Vn, F, d, resolution, radius_world, overhang_deg, n_directions, nudge_voxels)
        n_flip_total += n_flip
        if rec is None:
            continue
        _save(rec, out_dir)
        if emit_audit:
            _try_audit(rec, os.path.join(audit_dir, name + ".png"))
        records.append(rec)
    _write_manifest(out_dir, records, "fusion360", n_directions, seed, frac_train, frac_val,
                    human_signoff=False, extra_meta={"nudge_discarded_flipped_normal": n_flip_total})
    return out_dir


def build_from_root(out_dir, root, **kw):
    """便捷入口：从 reconstruction 目录读真实网格再物化。root 缺失 → FileNotFoundError（deferred: fusion360-ingest）。"""
    if not root or not os.path.isdir(root):
        raise FileNotFoundError(
            f"Fusion360 reconstruction 目录不存在：{root!r}"
            "（见 tools/data_paths.py 或 SAF_FUSION360_ROOT）"
        )
    return build_from_meshes(_meshes_from_root(root), out_dir, **kw)


# ————— 内部 —————
def _meshes_from_root(root):
    for name, path in iter_final_designs(root):
        try:
            V, F = load_obj(path)
        except Exception:                       # 坏 obj 跳过（失败计入 §4.8 排除，不中断批处理）
            continue
        yield name, V, F


def _label_one(name, Vn, F, d, resolution, radius_world, overhang_deg, n_directions, nudge_voxels):
    """归一网格 → occupancy → 下朝接触点 → oracle 打标 → LabeledModel（无接触点则 None）。

    传 mesh=(Vn,F,lo,pitch) 给 oracle → 启用 D-020 边界带精确胶囊-网格细化（真实 CAD 标签 res-稳定训练级）。
    """
    import numpy as np
    from support_accessibility.data import mesh as MESH, overhang as OVH, LabeledModel
    from support_accessibility.oracle import SupportAccessibilityOracle
    occ, lo, pitch = MESH.mesh_to_occupancy(Vn, F, resolution=resolution)
    sc = OVH.support_contact_faces(Vn, F, d, overhang_deg)
    r = radius_world / pitch
    o = SupportAccessibilityOracle(occ, {"n_directions": n_directions}, mesh=(Vn, F, lo, pitch))
    pts, labs, n_flip = [], [], 0
    for c, n in zip(sc.centroids, sc.normals):
        status, q = MESH.nudge_to_free(occ, c, n, nudge_voxels * pitch, lo, pitch)   # 缠绕安全外移（D-028）
        if status == "flipped":             # 法向翻转、非真下朝面 → 丢弃并计数
            n_flip += 1
            continue
        pts.append(q)                        # "free"/"confined"：同旧 +n 口径（confined 保留稀有不可达正类）
        labs.append(o.label(q, r).value == "inaccessible")
    if not pts:
        return None, n_flip
    return LabeledModel(name, occ, np.asarray(pts, np.float32), np.asarray(labs, bool), float(r)), n_flip


def _save(rec, out_dir):
    from support_accessibility.data import dataset as DS
    DS.save_model(rec, os.path.join(out_dir, DS._rel_npz(rec.name)))


def _try_audit(rec, path):
    try:                                        # 审计图是旁路产物；出图失败不得污染数据管线
        from support_accessibility import viz
        viz.audit_model(rec, path)
    except Exception:
        pass


def _write_manifest(out_dir, records, source, n_directions, seed, frac_train, frac_val, human_signoff, extra_meta=None):
    """复用 D-016 格式（dataset.COLUMNS/MANIFEST/DATASET_JSON），source + 三切 + human_signoff 标记。
    extra_meta：可选，并入 dataset.json（如 D-028 的 nudge_discarded_flipped_normal 计数，防静默丢弃）。"""
    import csv
    import json
    import numpy as np
    from support_accessibility.data import dataset as DS, split_by_model
    if records:
        tr, va, te = split_by_model(records, frac_train=frac_train, frac_val=frac_val, seed=seed)
    else:
        tr, va, te = [], [], []
    split_of = {m.name: "train" for m in tr}
    split_of.update({m.name: "val" for m in va})
    split_of.update({m.name: "test" for m in te})
    rows = []
    for m in records:
        lab = np.asarray(m.labels, bool)
        n_pts, n_inacc = int(lab.size), int(lab.sum())
        rows.append({"name": m.name, "source": source, "split": split_of[m.name],
                     "npz_path": DS._rel_npz(m.name), "occ_shape": "x".join(map(str, m.occ.shape)),
                     "n_points": n_pts, "n_inaccessible": n_inacc,
                     "inaccessible_frac": (n_inacc / n_pts) if n_pts else 0.0,
                     "radius": float(m.radius), "n_directions": int(n_directions), "seed": int(seed)})
    with open(os.path.join(out_dir, DS.MANIFEST), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=DS.COLUMNS)
        w.writeheader()
        w.writerows(rows)
    meta = {"schema_version": DS.RECORD_SCHEMA_VERSION, "source": source,
            "record_keys": ["occ", "points", "labels"], "units": "voxel",
            "human_signoff": bool(human_signoff),          # D-018：人审 audit/ 后方可训练
            "build_params": {"n_directions": n_directions, "seed": seed,
                             "frac_train": frac_train, "frac_val": frac_val},
            "split": {"n_train": len(tr), "n_val": len(va), "n_test": len(te)}}
    if extra_meta:
        meta.update(extra_meta)
    with open(os.path.join(out_dir, DS.DATASET_JSON), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, sort_keys=True)
