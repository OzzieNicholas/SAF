"""环境自检（env_ready）—— 把"用对环境"变成会跑的门。

canonical 环境源 = environment.yml（conda env `sfa`，见 charter/decisions.md D-007）。
本检查验证**当前解释器**能 import 几何/数值栈 + py≥3.12；不对就当场 FAIL（不是 PENDING），
从而"环境歧义"变成 RED 而非静默。模块级只用 stdlib（重型 import 在函数内 try/except），
保证 tests/gate.py 在任何解释器都能 import 本模块不崩。
"""

import sys

from . import result

_REQUIRED = ("igl", "numpy", "scipy", "trimesh")
_MIN_PY = (3, 12)


def _probe():
    missing = []
    for name in _REQUIRED:
        try:
            __import__(name)
        except Exception:
            missing.append(name)
    py_ok = sys.version_info[:2] >= _MIN_PY
    return missing, py_ok


def checks():
    missing, py_ok = _probe()
    ok = not missing and py_ok
    py = ".".join(map(str, sys.version_info[:3]))
    if ok:
        detail = f"py{py} + {'/'.join(_REQUIRED)} 就绪（env sfa）"
    else:
        parts = []
        if not py_ok:
            parts.append(f"py{py}<3.12")
        if missing:
            parts.append("缺:" + ",".join(missing))
        detail = "；".join(parts) + "（应在 conda env sfa 内跑：conda env create -f environment.yml）"
    return [result("env_ready", ok, detail)]


def test_env_ready():
    r = checks()[0]
    assert r["status"] == "PASS", r["detail"]
