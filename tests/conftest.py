"""让 pytest 能 import support_accessibility（src-layout；未做 editable 安装时的兜底）。"""

import os
import sys

_TESTS = os.path.dirname(os.path.abspath(__file__))   # tests/
_ROOT = os.path.dirname(_TESTS)                        # repo root
for _p in (os.path.join(_ROOT, "src"), _TESTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
