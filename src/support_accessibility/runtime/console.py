"""进程级运行环境设置：终端编码与 OpenMP 重复加载保护。"""

import os
import sys


def setup_console() -> None:
    """让 Windows GBK 控制台能输出非 GBK 字符，并抑制 torch 与 numpy/scipy 同进程的 OMP 重复加载中止。

    须在导入 torch、numpy、scipy 之前调用。
    """
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
