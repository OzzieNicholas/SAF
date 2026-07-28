"""变形/性质测试：不需要知道绝对答案，只钉"关系"。

守护决策与现状（详见 charter/decisions.md、charter/README.md 映射）：
  D-005 尺度不变（整数上采样 k×，label 不变）—— **已证伪（D-011）**：分辨率依赖、非严格
        不变量；粗网格误判欠分辨薄特征（细网格纠正为不可达）；真实网格上复核
  D-005 旋转等变 —— 体素旋转有重采样伪影，属连续几何性质，移交 mesh 前端批次
  D-003 半径单调（r↑→不可达↑）—— **已证伪（D-008）**：point-touch 语义C 下不成立，不作不变量
  D-003 方向单调（方向集越大越可达）—— **已闭合（保证性）**：显式**嵌套**方向集 S1⊆S2 → 可达性单调不减
        （可达=any(方向可达)，超集 any≥子集）。非嵌套 Fibonacci 不保证，故用 oracle 显式方向集（params['directions']，
        E5/D-024 方向场所指路径）给保证性测试；方向**数**单调仍经验稳（非嵌套故不作严格不变量）。

四条变形性质里 scale/radius/rotation 经检验**判定为非不变量**（证伪或体素离散伪影），checks() 记
**N/A 终态**（非待办、不阻塞 DoD，见 D-027）、pytest skip；direction_monotonic 已由显式嵌套方向集闭合为
保证性测试（PASS）。（连续几何版的 scale/rotation 属 mesh 前端未来延伸，非本工程范围。）
"""

from unittest import SkipTest

from . import na, pending, result       # noqa: F401  (pending 保留给未来真 PENDING 项)


def _direction_monotonic_ok():
    """保证性：显式嵌套方向集 S1⊆S2 → 可达单调不减。返回 (ok, detail)。"""
    import numpy as np
    from support_accessibility.oracle import SupportAccessibilityOracle, Label
    from support_accessibility.data import _slab_blind_hole, down_facing_points
    occ = _slab_blind_hole(28, opening=8, depth=10)                 # 宽度8>2r：竖直可达、斜向多被壁挡（混合点）
    ofull = SupportAccessibilityOracle(occ, {"n_directions": 64})
    p = vd = bd = None
    for q in down_facing_points(occ):
        dl = ofull.direction_labels(q, 3.0)
        if dl.any() and (~dl).any():                                # 该点既有可达方向、又有被挡方向
            p, vd, bd = q, ofull.dirs[int(np.argmax(dl))], ofull.dirs[int(np.argmax(~dl))]
            break
    if p is None:
        return False, "未找到混合点（既可达又被挡的方向）"
    A = Label.ACCESSIBLE
    def acc(dirs):
        return SupportAccessibilityOracle(occ, {"directions": dirs}).label(p, 3.0) == A
    # 超集获可达：{blocked} 不可达，加入 viable → {blocked,viable} 可达
    gain = (not acc([bd])) and acc([bd, vd])
    # 可达不丢：{viable} 可达 → {viable,blocked} 仍可达（超集 any≥子集）
    keep = acc([vd]) and acc([vd, bd])
    return bool(gain and keep), f"嵌套单调：加 viable 方向获可达({gain})、超集不丢可达({keep})"


def checks():
    try:
        import numpy, scipy  # noqa: F401
        from support_accessibility import oracle, data  # noqa: F401
        ok, det = _direction_monotonic_ok()
        dm = result("direction_monotonic", ok, det, "D-003")
    except ImportError as e:
        dm = pending("direction_monotonic", f"依赖未就绪：{e}", "D-003")
    except Exception as e:
        dm = result("direction_monotonic", False, f"异常：{e}", "D-003")
    return [
        na("scale_invariance", "整数上采样证伪（D-011）：分辨率依赖、判定为非不变量（终态，非待办）", "D-011"),
        na("radius_monotonic", "已证伪（D-008）：point-touch 语义C 下不成立、判定为非不变量（终态）", "D-003"),
        dm,
        na("rotation_equivariance", "非体素不变量（终态，引理：非轴对齐旋转必重采样占据栅格→破严格体素等变；"
           "连续几何版属 mesh 前端未来延伸、非本工程范围）", "D-005"),
    ]


def test_scale_invariance():
    raise SkipTest("尺度不变经整数上采样证伪（D-011）：分辨率依赖、非严格不变量；粗网格误判欠分辨薄特征；真实网格上复核")


def test_radius_monotonic():
    raise SkipTest("半径单调已证伪（D-008）：point-touch 语义C 下不成立，不作不变量；真实网格上复核")


def test_direction_monotonic():
    """方向单调（保证性，D-003）：显式嵌套方向集 S1⊆S2 → 可达单调不减（可达=any(方向可达)，超集 any≥子集）。"""
    try:
        import numpy, scipy  # noqa: F401
        from support_accessibility import oracle, data  # noqa: F401
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    ok, det = _direction_monotonic_ok()
    assert ok, det


def test_rotation_equivariance():
    raise SkipTest("体素旋转有重采样伪影，属连续几何性质；连续版移交 mesh 前端批次")
