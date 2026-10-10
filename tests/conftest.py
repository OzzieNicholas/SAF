"""pytest 全局设置：OpenMP 重复加载保护与 torch DLL 预加载顺序。

torch(iomp5) 与 numpy/scipy(libomp) 同进程共存时，某些导入序下 OpenMP 重复运行时会硬崩
（"OMP Error #15"，无 traceback）；收集前置好 KMP_DUPLICATE_LIB_OK 抑制该 abort
（PyTorch/Intel 既定 workaround，本负载安全）。
"""

import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# Windows 上先载入 torch 的 DLL，再让几何测试引入 scipy/OpenBLAS；反向顺序会在
# torch._load_dll_libraries 中以 0xc0000139 硬退出，无法由 pytest 捕获或跳过。
if os.name == "nt":
    try:
        import torch  # noqa: F401
    except ImportError:
        pass
