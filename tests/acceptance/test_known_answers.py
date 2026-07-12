"""已知答案件：语义 C 在旗舰几何上的正确性（构造即知答案）。

守护决策：
  D-001  盲腔底部 = 不可达（语义C 的旗舰正确性）
  D-002  开阔外表面下朝面 = 可达（下半球逼近、基板不建模、只计本体遮挡）

在 conda env saf（numpy/scipy）内 checks() 真跑 oracle 并与构造答案比对；
依赖缺失时优雅降级为 PENDING（env_ready 门另会红），oracle 抛错则记 FAIL（不静默）。
"""

from unittest import SkipTest

from . import pending, result

# (check 名, 决策, data 生成器名)
_CASES = [
    ("blind_cavity_inaccessible", "D-001", "blind_cavity_case"),
    ("open_downface_accessible", "D-002", "open_downface_case"),
]
_PARAMS = {"n_directions": 64}


def _label_for(gen_name):
    """构造件 → 跑 oracle → (实得标签, 期望标签)。ImportError 表示依赖未就绪。"""
    from support_accessibility import oracle as orc, data
    case = getattr(data, gen_name)()
    o = orc.SupportAccessibilityOracle(case.occ, params=_PARAMS)
    return o.label(case.point, case.radius).value, case.expected


def checks():
    try:
        from support_accessibility import oracle, data  # noqa: F401
    except ImportError as e:
        return [pending(n, f"依赖未就绪：{e}", d) for n, d, _ in _CASES]
    out = []
    for check_name, dec, gen_name in _CASES:
        try:
            got, expect = _label_for(gen_name)
            out.append(result(check_name, got == expect, f"期望={expect} 实得={got}", dec))
        except Exception as e:                       # oracle 有 bug → FAIL（可见，不静默）
            out.append(result(check_name, False, f"评估异常：{e}", dec))
    return out


def test_blind_cavity_inaccessible():
    """盲腔底部必判不可达（D-001）。"""
    try:
        got, expect = _label_for("blind_cavity_case")
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    assert got == expect == "inaccessible", f"盲腔应不可达，实得 {got}"


def test_open_downface_accessible():
    """开阔下朝面必判可达（D-002）。"""
    try:
        got, expect = _label_for("open_downface_case")
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    assert got == expect == "accessible", f"开阔下朝面应可达，实得 {got}"
