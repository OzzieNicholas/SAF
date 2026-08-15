"""让 pytest 能 import support_accessibility（src-layout；未做 editable 安装时的兜底）。

另：torch(iomp5) 与 numpy/scipy(libomp) 同进程共存时，某些导入序下 OpenMP 重复运行时会硬崩
（"OMP Error #15"，无 traceback）；测试混跑 torch + scipy（test_model/test_direction_field + test_capsule）
会间歇触发。收集前置好 KMP_DUPLICATE_LIB_OK 抑制该 abort（PyTorch/Intel 既定 workaround，本负载安全）。
"""

import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")   # torch+scipy OMP 重复运行时保护（见上）

# Windows 上先载入 torch 的 DLL，再让几何测试引入 scipy/OpenBLAS；反向顺序会在
# torch._load_dll_libraries 中以 0xc0000139 硬退出，无法由 pytest 捕获或跳过。
if os.name == "nt":
    try:
        import torch as _torch  # noqa: F401
    except ImportError:
        pass

_TESTS = os.path.dirname(os.path.abspath(__file__))   # tests/
_ROOT = os.path.dirname(_TESTS)                        # repo root
for _p in (os.path.join(_ROOT, "src"), _TESTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
