"""viz 审计仪器验收（D-018）：可达性 montage 渲染出**合法非平凡** PNG——命门签收赖以进行的图。

无导师 → 真实网格标签靠人眼审 viz 热图签收（铁律 #7），故 viz 本身必须有门（否则命门仪器可能坏了都不知）。
numpy 段：合成 occ+点+标签 → accessibility_montage → 解析 PNG（IHDR 尺寸符合 montage 几何 +
逐行解码含红[不可达]与绿[可达]像素）。PNG 编码器（_png）纯 stdlib、已在裸环境自检；本模块验 numpy 光栅装配。
缺 numpy → PENDING/skip（CI 的 saf 环境真跑）。
"""

import struct
import zlib
from unittest import SkipTest

from . import pending, result

_SCALE, _PAD, _GAP = 4, 6, 8
_RED, _GREEN = bytes([220, 40, 40]), bytes([40, 160, 40])


def _render():
    import os
    import tempfile
    import numpy as np
    from support_accessibility import viz
    nx, ny, nz = 10, 8, 12
    occ = np.zeros((nx, ny, nz), bool)
    occ[:, :, 4:8] = True                                 # 一层板
    points = np.array([[5.0, 4.0, 3.0], [5.0, 4.0, 8.0]])  # 板下 / 板上
    labels = np.array([True, False])                       # 一红（不可达）一绿（可达）
    with tempfile.TemporaryDirectory() as d:
        p = viz.accessibility_montage(occ, points, labels, os.path.join(d, "m.png"),
                                      scale=_SCALE, pad=_PAD, gap=_GAP)
        raw = open(p, "rb").read()
    return (nx, ny, nz), raw


def _idat(raw):
    i = 8
    while i < len(raw):
        ln = struct.unpack(">I", raw[i:i + 4])[0]
        if raw[i + 4:i + 8] == b"IDAT":
            return raw[i + 8:i + 8 + ln]
        i += 12 + ln
    return b""


def _check():
    (nx, ny, nz), raw = _render()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        return result("viz_montage_png", False, "PNG 签名错", "D-018")
    w, h = struct.unpack(">II", raw[16:24])
    exp_w = _SCALE * (nx + ny) + _GAP + 2 * _PAD           # 两侧面板(XZ|YZ)横拼 + 缝 + 边
    exp_h = _SCALE * nz + 2 * _PAD                         # 竖直=z
    dims_ok = (w, h) == (exp_w, exp_h)
    dec = zlib.decompress(_idat(raw))                      # 逐行 filter=0，像素字节字面
    colors_ok = (_RED in dec) and (_GREEN in dec)
    return result("viz_montage_png", dims_ok and colors_ok,
                  f"PNG {w}x{h}（期望 {exp_w}x{exp_h}={dims_ok}）·红&绿像素在位={colors_ok}", "D-018")


def checks():
    try:
        import numpy  # noqa: F401
        from support_accessibility import viz  # noqa: F401
    except ImportError as e:
        return [pending("viz_montage_png", f"依赖未就绪：{e}", "D-018")]
    try:
        return [_check()]
    except Exception as e:
        return [result("viz_montage_png", False, f"异常：{e}", "D-018")]


def test_viz_montage_png():
    """montage 出合法 PNG，尺寸符合几何、含红绿像素（命门仪器有门）。"""
    try:
        import numpy  # noqa: F401
        from support_accessibility import viz  # noqa: F401
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    r = _check()
    assert r["status"] == "PASS", r["detail"]
