"""标签质量审核门（六项趋势，铁律 #6；研究背景与设计 §5）——oracle/标签未过此门不进正式神经实验。

六项趋势的守护分工（一个事实一个家，不重复造门）：
  ① 典型几何   test_known_answers（盲腔=不可达 / 开阔下朝面=可达）
  ② 随机抽样   test_differential（体素 vs 暴力参考，随机件 robust 一致）
  ③ 边界稳定   test_differential（ε 边界带容忍 vs robust 不一致）
  ④ 半径趋势   **本模块**——受限盲腔不可达随 r 单调非减（仅受限几何；D-008 证伪的是一般半径单调性）
  ⑤ 方向变化   test_support_contact（S(P,d) 随 d 改变：d=+z 底面 vs d=+x 侧面）
  ⑥ 跨数据     程序化=test_procedural_cases（两类俱在、按模型切分）；真实网格见 experiments/label_audit.py
本模块补 ④ + 批量聚合体检（②的系统化：标签分布合理、非退化）。全绿=标签质量门就绪。
"""

from unittest import SkipTest

from . import pending, result

_N_DIR = 32
_N = 28


def _deps():
    import numpy, scipy  # noqa: F401
    from support_accessibility import data, oracle  # noqa: F401


def _radius_monotone_confined():
    """④ 受限盲腔：不可达数随工具半径单调非减（D-008 收窄——仅受限几何）。"""
    from support_accessibility import data as D
    from support_accessibility.oracle import SupportAccessibilityOracle
    bad = []
    for opening, depth in ((3, 9), (4, 9), (5, 9), (6, 9)):
        occ = D.slab_with_blind_hole(_N, opening, depth)
        o = SupportAccessibilityOracle(occ, {"n_directions": _N_DIR})
        ceil = [p for p in D.down_facing_points(occ) if p[2] > 8]     # 高于板底=腔顶（受限）
        seq = [sum(o.label(p, r).value == "inaccessible" for p in ceil) for r in (1., 2., 3., 4., 5.)]
        if any(seq[i] > seq[i + 1] for i in range(len(seq) - 1)):
            bad.append(f"o{opening}d{depth}:{seq}")
    return (not bad), ("受限盲腔不可达随 r 非减（4 腔 ×5 半径）" if not bad else "违反:" + ";".join(bad))


def _direction_count_stable():
    """方向离散稳定性：操作区（≥16 方向）标签收敛，粗采样确应偏离（证参数活跃、收敛非平凡）。

    支撑 params-freeze 的 n_directions 敏感性证据：实测标签在 n_dir≈12 收敛、≥16 稳定；<12 欠采样误判
    （与 D-011 分辨率教训同族——离散不足会真错）。故 n_directions 冻结在收敛区任一值都给正确标签。
    """
    from support_accessibility import data as D
    from support_accessibility.oracle import SupportAccessibilityOracle
    import numpy as np
    ms = D.make_dataset(n_models=6, N=_N, max_points=24, radius=3.0, n_directions=32, seed=2)

    def lab(nd):
        return np.concatenate([np.array([SupportAccessibilityOracle(m.occ, {"n_directions": nd}).label(p, 3.0).value == "inaccessible"
                                         for p in m.points]) for m in ms])
    ref = lab(64)
    agree_op = float((lab(16) == ref).mean())        # 操作区（≥16）应收敛
    agree_coarse = float((lab(6) == ref).mean())     # 粗采样（6）应偏离
    ok = agree_op >= 0.98 and agree_coarse < 0.9
    return ok, f"n_dir 16 vs 64 一致 {agree_op*100:.0f}%（操作区收敛）；粗采样(6) {agree_coarse*100:.0f}%<90%（参数活跃、收敛非平凡）"


def _batch_distribution_sane():
    """②聚合：一批程序化件标签分布合理——两类俱在、无退化件、风险类占比在 5–60%。"""
    from support_accessibility import data as D
    import numpy as np
    ms = D.make_dataset(n_models=16, N=_N, max_points=24, radius=3.0, n_directions=_N_DIR, seed=1)
    if any(m.points.shape[0] == 0 for m in ms):
        return False, "有退化件（0 接触点）"
    lab = np.concatenate([m.labels for m in ms])
    frac = float(lab.mean())
    both = bool(lab.any() and (~lab).any())
    sane = both and 0.05 <= frac <= 0.60
    return sane, f"{len(ms)} 件 不可达占比 {frac*100:.0f}%（两类俱在、5–60% 合理风险区）"


def checks():
    try:
        _deps()
    except ImportError as e:
        return [pending(n, f"依赖未就绪：{e}", "D-008") for n in
                ("lq_radius_monotone_confined", "lq_batch_distribution_sane")]
    out = []
    for name, fn, dec in (("lq_radius_monotone_confined", _radius_monotone_confined, "D-008"),
                          ("lq_direction_count_stable", _direction_count_stable, "D-003"),
                          ("lq_batch_distribution_sane", _batch_distribution_sane, "D-004")):
        try:
            ok, detail = fn()
            out.append(result(name, ok, detail, dec))
        except Exception as e:
            out.append(result(name, False, f"异常：{e}", dec))
    return out


def test_radius_monotone_confined():
    """④ 受限盲腔不可达随 r 单调非减（D-008 收窄口径成立）。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    ok, detail = _radius_monotone_confined()
    assert ok, detail


def test_direction_count_stable():
    """方向离散在操作区收敛（n_directions 敏感性证据，支撑 params-freeze）。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    ok, detail = _direction_count_stable()
    assert ok, detail


def test_batch_distribution_sane():
    """②聚合：程序化标签分布合理、非退化（标签质量门）。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    ok, detail = _batch_distribution_sane()
    assert ok, detail
