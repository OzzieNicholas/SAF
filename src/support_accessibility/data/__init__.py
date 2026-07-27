"""程序化已知答案件生成器 —— walking skeleton 的头几个测试件（构造即知答案）。

本批用**解析占据栅格**（numpy）直接构造，绕开 mesh 布尔/manifold 依赖；mesh→occupancy 的真实前端
（igl 判内外、trimesh 读取）属后续批次。点/半径以体素为单位，与 oracle 口径一致。
构造即知答案：造了个窄盲腔，其天花板下的点就必然不可达（D-001）；开阔下朝面必然可达（D-002）。

模块级只用 stdlib；numpy 在函数内 import，保证系统 py（无 numpy）仍能 `import data`（gate 兜底 PENDING）。
"""

from dataclasses import dataclass


@dataclass
class VoxelCase:
    """占据栅格上的一个构造即知答案件。"""
    name: str
    decision: str
    occ: object          # np.ndarray[bool]，True=实体
    point: tuple         # (x,y,z) 体素坐标（支撑接触点，下朝面）
    radius: float        # 工具球半径（体素）
    expected: str        # "accessible" | "inaccessible"


def blind_cavity_case(N=40, opening=3, depth=16, radius=3.0):
    """底面开口的盲孔：实心厚板 z∈[z0,z1)，从底面 z0 向上挖 opening×opening 方孔到 z0+depth（不透顶）。
    查询点 = 孔顶（下朝天花板）下方的自由体素。opening 窄于 ~2r → 球进不去 → 不可达（D-001）。
    板上下留自由空间（基板不建模，遮挡下界）。"""
    import numpy as np
    occ = np.zeros((N, N, N), dtype=bool)
    z0, z1 = 8, N - 8
    occ[:, :, z0:z1] = True                              # 实心厚板（x,y 全）
    c, h = N // 2, opening // 2
    occ[c - h:c + h + 1, c - h:c + h + 1, z0:z0 + depth] = False   # 从底面挖方孔到 z0+depth（盲）
    ceiling = z0 + depth                                 # 天花板（实体）在 z=ceiling
    point = (float(c), float(c), float(ceiling - 1))     # 天花板下的自由体素（下朝面）
    return VoxelCase("blind_cavity", "D-001", occ, point, float(radius), "inaccessible")


def open_downface_case(N=40, radius=3.0):
    """开阔下朝面：厚板 z∈[z0,z1)，底面 z0 下方全自由。查询点=板底中心下方的自由体素 → 可达（D-002）。"""
    import numpy as np
    occ = np.zeros((N, N, N), dtype=bool)
    z0, z1 = 20, N - 6
    occ[:, :, z0:z1] = True
    c = N // 2
    point = (float(c), float(c), float(z0 - 1))          # 板底下的自由体素（下朝面）
    return VoxelCase("open_downface", "D-002", occ, point, float(radius), "accessible")


# —— 后续批次 ——
def deep_narrow_slot(width, depth):
    """深窄槽；随 width/depth 与工具半径耦合，用于半径单调趋势（D-003）。"""
    raise NotImplementedError("后续批次（变形性质）。")


def flagship_pair(support_area_target=64, cavity_depth_a=4, cavity_depth_b=16,
                  width=2, radius=3.0, margin=8, n_directions=64):
    """E1/H1 存在性旗舰对：两件**支撑面积（下朝悬垂接触体素数）近似相等**、**可达性相反**——
    证「支撑面积 ⊥ 可达性」，补 H1 统计 ρ≈0 的存在性证据。返回 (case_a, case_b) 两个 LabeledModel。

    两件下朝悬垂面都是 width×L 条带（L=round(support_area_target/width)）→ 支撑面积≈相等：
    - **case_a「open_ledge」**：悬空薄板，条带下朝面四周开阔（free_dist>r）→ oracle 判**可达**（D-002）。
    - **case_b「deep_narrow_cavity」**：实体块自底面挖 width×L 窄槽（width<2r）至深 cavity_depth_b，
      槽顶为下朝面但被窄壁夹（沿途 free_dist<r）→ oracle 判**不可达**（D-001）。
    可达性差异源自腔几何（开阔 vs 深窄），**非面积**——即 H1 立论。需 width<2·radius。
    """
    import numpy as np
    from support_accessibility.oracle import SupportAccessibilityOracle
    L = max(1, int(round(support_area_target / width)))

    # case_a：悬空薄板（width×L 底面开阔）→ 可达
    t = 3
    occ_a = np.zeros((L + 2 * margin, width + 2 * margin, t + 2 * margin + cavity_depth_a), dtype=bool)
    xa, ya, za = margin, margin, margin + cavity_depth_a
    occ_a[xa:xa + L, ya:ya + width, za:za + t] = True

    # case_b：实体块自底面挖 width×L 窄槽至深 cavity_depth_b（槽顶下朝、窄壁夹）→ 不可达
    occ_b = np.ones((L + 2 * margin, width + 2 * margin, cavity_depth_b + margin), dtype=bool)
    xb, yb = margin, margin
    occ_b[xb:xb + L, yb:yb + width, 0:cavity_depth_b] = False

    r = float(radius)
    parts = []
    for name, occ in (("flagship_open_ledge", occ_a), ("flagship_deep_narrow_cavity", occ_b)):
        pts = down_facing_points(occ)
        orc = SupportAccessibilityOracle(occ, {"n_directions": n_directions})
        labels = np.array([orc.label(p, r).value == "inaccessible" for p in pts], dtype=bool)
        parts.append(LabeledModel(name, occ, pts, labels, r))
    return parts[0], parts[1]


# —— 程序化标签数据集（Phase 1）：形状条件样本，oracle 自动打标（无人工标注）——
@dataclass
class LabeledModel:
    """一个程序化件的形状条件训练样本。occ=形状条件；points=下朝支撑接触点；labels=oracle 标签。"""
    name: str
    occ: object            # np.ndarray[bool]，True=实体（形状条件输入）
    points: object         # np.ndarray (K,3) float，体素坐标（下朝支撑接触点，查询点）
    labels: object         # np.ndarray (K,) bool，True=不可达（风险正类，D-004 二分类）
    radius: float          # 工具球半径（体素）


def _slab_blind_hole(N, opening, depth):
    """厚板从底面挖 opening×opening 盲孔 depth 深。窄孔顶=不可达、板底开阔面=可达（一件含两类）。"""
    import numpy as np
    occ = np.zeros((N, N, N), dtype=bool)
    z0, z1 = 8, N - 8
    occ[:, :, z0:z1] = True
    c, h = N // 2, opening // 2
    occ[c - h:c + h + 1, c - h:c + h + 1, z0:z0 + depth] = False
    return occ


def _open_slab(N, thickness):
    """开阔厚板：底面下方全自由 → 下朝面全可达（D-002）。"""
    import numpy as np
    occ = np.zeros((N, N, N), dtype=bool)
    z0 = (N - thickness) // 2
    occ[:, :, z0:z0 + thickness] = True
    return occ


def down_facing_points(occ, max_points=None, rng=None):
    """下朝支撑接触点 = 自由体素且其 +z 邻为实体（构建方向 +z，D-010 底面/悬垂）。返回 (K,3) float。

    **按高度 z 分层采样**：开阔底面（低 z）与受限腔顶（高 z）是几何上不同的下朝面，体素数悬殊；
    面积均匀采样会让庞大的开阔底面淹没小小的腔顶（风险正类）。分层给每个 z-面配额，保证受限腔顶
    被代表——与"不可达=稀有风险正类"（problem.md）一致，不靠伪造平衡。（真实网格前端将按面积泊松采样，
    见 conf/params.yaml sampling；此处是程序化件的务实提取。）
    """
    import numpy as np
    occ = np.asarray(occ, dtype=bool)
    below_solid = np.zeros_like(occ)
    below_solid[:, :, :-1] = occ[:, :, 1:]              # (x,y,z) 上方 (z+1) 是实体
    cand = np.argwhere((~occ) & below_solid)            # (M,3) 自由且上方实体
    if max_points is None or cand.shape[0] <= max_points:
        return cand.astype(float)
    rng = rng if rng is not None else np.random.default_rng(0)
    levels = np.unique(cand[:, 2])
    per = max(1, max_points // len(levels))             # 每个下朝面（z-层）配额
    picked = []
    for zz in levels:
        g = cand[cand[:, 2] == zz]
        picked.append(g[rng.choice(g.shape[0], size=min(per, g.shape[0]), replace=False)])
    out = np.vstack(picked)
    if out.shape[0] > max_points:
        out = out[rng.choice(out.shape[0], size=max_points, replace=False)]
    return out.astype(float)


def make_dataset(n_models=12, N=28, max_points=24, radius=3.0, n_directions=32, seed=0):
    """程序化标签数据集：n_models 个参数化件 → 提取下朝接触点 → oracle 自动打标。

    形状条件训练用（按模型切分，见 split_by_model / conf/params.yaml split.by=model）。默认是小烟测集,
    Phase-2/3 靠增大 n_models/N/max_points 扩量。半径以体素为单位（对齐 oracle 口径与已知答案件）。
    """
    import numpy as np
    from support_accessibility.oracle import SupportAccessibilityOracle
    rng = np.random.default_rng(seed)
    models = []
    for i in range(n_models):
        if i % 3 == 0:
            thickness = int(rng.integers(6, 14))
            occ = _open_slab(N, thickness)
            name = f"open_slab_t{thickness}_{i}"
        else:
            opening = int(rng.integers(2, 8))           # 窄→不可达、宽→可达（腔顶两类兼有）
            depth = int(rng.integers(6, max(7, N - 18)))
            occ = _slab_blind_hole(N, opening, depth)
            name = f"blind_hole_o{opening}_d{depth}_{i}"
        pts = down_facing_points(occ, max_points=max_points, rng=rng)
        orc = SupportAccessibilityOracle(occ, {"n_directions": n_directions})
        labels = np.array([orc.label(p, radius).value == "inaccessible" for p in pts], dtype=bool)
        models.append(LabeledModel(name, occ, pts, labels, float(radius)))
    return models


def split_by_model(models, frac_train=0.7, frac_val=None, seed=0):
    """按模型切分（split.by=model；禁按点随机切分，见 conf/params.yaml）。

    frac_val=None → 返回 (train, test)（2-way；在内存快评/薄纵切用）；
    frac_val 给值 → 返回 (train, val, test)（物化数据集用，落地 D-016 切分 {train,val,test}；调参只用 val）。
    """
    import numpy as np
    idx = np.arange(len(models))
    np.random.default_rng(seed).shuffle(idx)
    n = len(models)
    n_tr = int(round(n * frac_train))
    if frac_val is None:
        return [models[i] for i in idx[:n_tr]], [models[i] for i in idx[n_tr:]]
    n_va = int(round(n * frac_val))
    return ([models[i] for i in idx[:n_tr]],
            [models[i] for i in idx[n_tr:n_tr + n_va]],
            [models[i] for i in idx[n_tr + n_va:]])
