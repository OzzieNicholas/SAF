"""Thingi10K STL ingest 验收（跨域 H5）：STL 解析（ascii + binary 已知答案）+ 端到端物化。

STL 存**每面法向**（stored normal）——Thingi 缠绕不一致，故下朝面提取用 stored normal（intended 外向），
占据用 igl winding（对缠绕/非流形稳健）。纯 stdlib 段裸环境跑；几何段缺 numpy/igl → PENDING/skip。
"""
from unittest import SkipTest

from . import pending, result

_ASCII = ("solid t\n facet normal 0 0 1\n  outer loop\n"
          "   vertex 0 0 0\n   vertex 1 0 0\n   vertex 0 1 0\n"
          "  endloop\n endfacet\nendsolid t\n")


def _binary_stl():
    import struct
    return b"\x00" * 80 + struct.pack("<I", 1) + struct.pack("<12f", 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0) + b"\x00\x00"


def _check(fmt):
    import os
    import tempfile
    import numpy as np
    from support_accessibility.data.thingi import load_stl
    mode, data, suf = ("w", _ASCII, "a") if fmt == "ascii" else ("wb", _binary_stl(), "b")
    fd, p = tempfile.mkstemp(suffix=f"_{suf}.stl")
    os.close(fd)
    with open(p, mode) as f:
        f.write(data)
    try:
        V, F, N = load_stl(p)
        ok = (V.shape == (3, 3) and F.shape == (1, 3)
              and np.allclose(V[0], [0, 0, 0]) and np.allclose(V[1], [1, 0, 0]) and np.allclose(V[2], [0, 1, 0])
              and np.allclose(N[0], [0, 0, 1]))
        return result(f"stl_parse_{fmt}", ok, f"{fmt}: V{V.shape} F{F.shape} N0={N[0].tolist()}", "H5")
    finally:
        os.unlink(p)


def checks():
    try:
        import numpy  # noqa: F401
        from support_accessibility.data import thingi  # noqa: F401
    except ImportError as e:
        return [pending("stl_parse", f"依赖未就绪：{e}", "H5")]
    try:
        return [_check("ascii"), _check("binary")]
    except Exception as e:
        return [result("stl_parse", False, f"异常：{e}", "H5")]


def test_load_stl_ascii():
    try:
        import numpy  # noqa: F401
        from support_accessibility.data import thingi  # noqa: F401
    except ImportError as e:
        raise SkipTest(str(e))
    r = _check("ascii")
    assert r["status"] == "PASS", r["detail"]


def test_load_stl_binary():
    try:
        import numpy  # noqa: F401
        from support_accessibility.data import thingi  # noqa: F401
    except ImportError as e:
        raise SkipTest(str(e))
    r = _check("binary")
    assert r["status"] == "PASS", r["detail"]


def test_select_points_cap_deterministic():
    """接触点子采样（D-022 H5 接入采样上限）：None/n<=cap → 全取(返回 None)；n>cap → 恰 cap 个无重复、确定性、界内。
    密网格(Thingi 扫描)接触点上万，全标不可解；子采样有界 + 无偏（跨域 F1 的一致估计）。"""
    try:
        import numpy as np
    except ImportError as e:
        raise SkipTest(str(e))
    from support_accessibility.data.thingi import _select_points   # 缺失应真红（非 skip）
    assert _select_points(10, None, 0) is None                 # 无上限 → 全取
    assert _select_points(5, 400, 0) is None                   # n<=cap → 全取
    idx = _select_points(1000, 400, 0)
    assert idx is not None and idx.shape[0] == 400
    assert len(set(idx.tolist())) == 400                       # 无重复
    assert int(idx.min()) >= 0 and int(idx.max()) < 1000       # 界内
    assert (idx == _select_points(1000, 400, 0)).all()         # 同种子确定性
    assert not (idx == _select_points(1000, 400, 1)).all()     # 异种子不同
