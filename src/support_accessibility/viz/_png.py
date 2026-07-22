"""极简 PNG 编码器（纯 stdlib：zlib + struct），零第三方依赖。

避免为出图引入 matplotlib/Pillow（environment.yml 只有 igl/numpy/scipy/trimesh）——与 D-009
「用 numpy/stdlib 绕开重依赖」同源。只写 8-bit RGB、无 alpha、无交错。
本模块**不 import numpy**，故系统 py 也能直接用（viz 审计门在裸环境可自检 PNG 合法性）。
"""

import struct
import zlib


def _chunk(tag, data):
    """PNG chunk = 长度(4) + 类型(4) + 数据 + CRC32(类型+数据)(4)，全大端。"""
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def write_png(path, rows, width, height):
    """把逐行 RGB8 字节写成 PNG。

    rows : 可迭代，每条长度 = width*3 的 bytes（R,G,B,R,G,B,...）。
    每行前置 filter 字节 0（None 滤波），zlib 压缩后作单个 IDAT。
    """
    raw = b"".join(b"\x00" + bytes(r) for r in rows)                 # 每行 filter=0
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)     # 8bit深, 2=RGB, 无交错
    idat = zlib.compress(raw, 9)
    with open(path, "wb") as f:
        f.write(sig + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b""))
    return path
