"""Thingi10K STL ingest（跨域 H5，deferred: thingi-ingest）：真实"野外"打印网格 → 统一 processed。

Thingi 缠绕不一致/非流形（docs §11.2）；故：占据用 igl winding（对缠绕稳健，D-009），下朝面提取用
**STL stored normal**（每面 intended 外向，绕过缠绕修复）。source=thingi10k，split **恒 test**（docs §4.6，
绝不进训练）。仅测跨域鲁棒性（H5），非主训练源。numpy/igl/oracle 在函数内 import（裸 py 仍可 import 本模块）。
"""
import os
import struct


def load_stl(path):
    """STL（二进制/ASCII）→ (V[(3m,3) float], F[(m,3) int32], N[(m,3) float] 每面 stored 法向)。"""
    import numpy as np
    with open(path, "rb") as f:
        header = f.read(80)
        cnt_bytes = f.read(4)
        body = f.read()
    is_binary = False
    if len(cnt_bytes) == 4:
        cnt = struct.unpack("<I", cnt_bytes)[0]
        if cnt > 0 and (len(body) == 50 * cnt
                        or (len(body) >= 50 * cnt and not header.lstrip()[:5].lower().startswith(b"solid"))):
            is_binary = True
    if is_binary:
        dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        recs = np.frombuffer(body[:50 * cnt], dtype=dt, count=cnt)
        V = recs["v"].reshape(cnt * 3, 3).astype(float)
        N = np.ascontiguousarray(recs["n"]).astype(float)
        F = np.arange(cnt * 3, dtype=np.int32).reshape(cnt, 3)
        return V, F, N
    # —— ASCII ——
    verts, norms, cur = [], [], (0.0, 0.0, 0.0)
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            s = ln.split()
            if not s:
                continue
            if s[0] == "facet" and len(s) >= 5 and s[1] == "normal":
                cur = (float(s[2]), float(s[3]), float(s[4]))
            elif s[0] == "vertex" and len(s) >= 4:
                if len(verts) % 3 == 0:
                    norms.append(cur)
                verts.append([float(s[1]), float(s[2]), float(s[3])])
    m = len(verts) // 3
    V = np.asarray(verts[:m * 3], float)
    F = np.arange(m * 3, dtype=np.int32).reshape(m, 3)
    N = np.asarray(norms[:m], float)
    return V, F, N


def load_mesh(path):
    """按扩展名读网格 → (V,F,N)。.stl → load_stl；.obj → load_obj（N=None，用计算法向）。"""
    if path.lower().endswith(".stl"):
        return load_stl(path)
    from support_accessibility.data.fusion360 import load_obj
    V, F = load_obj(path)
    return V, F, None


def iter_thingi_meshes(root):
    """走 raw_meshes 目录，产出 (name, path)：取 .stl / .obj（.ply/.off 各 1 个，暂略）。"""
    for fn in sorted(os.listdir(root)):
        if fn.lower().endswith((".stl", ".obj")):
            yield os.path.splitext(fn)[0], os.path.join(root, fn)


def _select_points(n, max_points, seed):
    """从 n 个接触点里确定性无放回选至多 max_points 个的排序索引；无需子采样时返回 None（全取）。

    Thingi 密扫描件下朝面上万，逐点全标 × n_directions × 细化不可解；子采样把每模型成本封顶，
    且随机无放回是逐点 F1 的无偏估计（跨域读数不受偏移）。max_points=None 或 n≤cap → None（全取）。"""
    if max_points is None or n <= max_points:
        return None
    import numpy as np
    return np.sort(np.random.default_rng(seed).choice(n, size=int(max_points), replace=False))


def _outward_normals(V, F, N_stored):
    """下朝面用外向法向：优先 STL stored（intended 外向、绕过缠绕修复），退化处用计算法向。返回 (Nn[单位], 质心)。"""
    import numpy as np
    from support_accessibility.data.overhang import face_normals_centroids
    ncomp, c = face_normals_centroids(V, F)                      # 计算法向（单位）+ 质心
    if N_stored is None:
        return ncomp, c
    N = np.asarray(N_stored, float)
    ln = np.linalg.norm(N, axis=1, keepdims=True)
    Nn = N / np.where(ln > 1e-9, ln, 1.0)
    Nn[ln[:, 0] <= 1e-9] = ncomp[ln[:, 0] <= 1e-9]              # stored 退化 → 计算
    return Nn, c


def build_thingi(root, out_dir, max_models=200, d=(0.0, 0.0, 1.0), resolution=48, radius_world=0.05,
                 overhang_deg=45.0, n_directions=128, nudge_voxels=2.0, max_faces=200000,
                 max_points=None, seed=0):
    """Thingi 子集 → 统一 processed（source=thingi10k，split 恒 test）。下朝面用 stored 法向、占据用 igl winding、
    oracle 打标（含 D-020 细化）。跨域鲁棒性测试用；返回 out_dir。

    max_points：每模型接触点上限（None=全取）。Thingi 密扫描件下朝面上万，全标不可解；子采样封顶成本、
    保跨域 F1 无偏（_select_points 确定性无放回）。max_faces 同理跳过超高面数件（res 下占据已降采样）。"""
    import numpy as np
    from support_accessibility.data import mesh as MESH, dataset as DS, LabeledModel
    from support_accessibility.data.fusion360 import normalize, _write_manifest
    from support_accessibility.oracle import SupportAccessibilityOracle
    os.makedirs(out_dir, exist_ok=True)
    d = np.asarray(d, float); d = d / np.linalg.norm(d)
    thr = -np.cos(np.radians(overhang_deg))
    records = []
    for name, path in iter_thingi_meshes(root):
        if len(records) >= max_models:
            break
        try:
            V, F, N = load_mesh(path)
        except Exception:
            continue
        if F.shape[0] < 8 or F.shape[0] > max_faces:
            continue
        Vn, _s = normalize(V)
        Nn, c = _outward_normals(Vn, F, N)
        mask = (Nn @ d) < thr                                    # 下朝悬垂面
        if int(mask.sum()) == 0:
            continue
        try:
            occ, lo, pitch = MESH.mesh_to_occupancy(Vn, F, resolution=resolution)
        except Exception:
            continue
        r = radius_world / pitch
        o = SupportAccessibilityOracle(occ, {"n_directions": n_directions}, mesh=(Vn, F, lo, pitch))
        cm, nm = c[mask], Nn[mask]
        sel = _select_points(cm.shape[0], max_points, seed)          # 密件接触点封顶（确定性无放回）
        if sel is not None:
            cm, nm = cm[sel], nm[sel]
        pts, labs = [], []
        for ci, ni in zip(cm, nm):
            q = MESH.nudge_to_free(occ, ci, ni, nudge_voxels * pitch, lo, pitch)   # 缠绕安全外移（同 fusion360）
            if q is None:
                continue
            pts.append(q)
            labs.append(o.label(q, r).value == "inaccessible")
        rec = LabeledModel(name, occ, np.asarray(pts, np.float32), np.asarray(labs, bool), float(r))
        DS.save_model(rec, os.path.join(out_dir, DS._rel_npz(name)))
        records.append(rec)
    _write_manifest(out_dir, records, "thingi10k", n_directions, seed, 0.0, 0.0, human_signoff=False)  # split 恒 test
    return out_dir
