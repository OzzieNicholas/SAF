"""未决触发册 → 门：把 charter/open.md 的未决项接进 gate（人肉提醒 → 门提醒）。

每条 open 项 = 前置条件(触发) → 义务。checks() 把每条 surfaced 为门项、指回 open.md id；
机器可判的条目（flagship-pair 的 import-check）附注"休眠/可闭合"。闭合：满足义务后从 open.md 删除。
纯 stdlib 解析 open.md；机器可判条目的依赖在函数内 import（缺失不崩）。
"""

import os
import re

from . import pending, result

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_OPEN = os.path.join(_ROOT, "charter", "open.md")


def _parse_open():
    """解析 charter/open.md → [(id, 触发, 义务), ...]。"""
    try:
        with open(_OPEN, encoding="utf-8") as f:
            txt = f.read()
    except OSError:
        return []
    items = []
    for m in re.finditer(r"^##\s+([\w-]+)\s*$(.*?)(?=^##\s|\Z)", txt, re.M | re.S):
        body = m.group(2)
        trig = re.search(r"触发[:：]\s*(.+)", body)
        duty = re.search(r"义务[:：]\s*(.+)", body)
        items.append((m.group(1),
                      trig.group(1).strip() if trig else "?",
                      duty.group(1).strip() if duty else "?"))
    return items


def _flagship_implemented():
    """flagship-pair 机器可判：flagship_pair 是否已实现（None=依赖未就绪）。"""
    try:
        from support_accessibility import data
    except ImportError:
        return None
    try:
        data.flagship_pair(0.0, 1.0, 2.0)
        return True
    except NotImplementedError:
        return False
    except Exception:
        return True     # 抛别的错 = 已有实现（只是参数不合），视为已实现


def checks():
    items = _parse_open()
    if not items:
        return [pending("open_register", "charter/open.md 缺失或为空", "")]
    out = []
    for oid, trig, duty in items:
        detail = f"触发={trig} → 义务={duty}"
        if oid == "flagship-pair" and _flagship_implemented() is True:
            out.append(result(f"open:{oid}", True, detail + "（已触发：flagship_pair 已实现，可闭合）", ""))
        else:
            if oid == "flagship-pair":
                detail += "（休眠：E1 未到，flagship_pair 仍 NotImplementedError）"
            out.append(pending(f"open:{oid}", detail, ""))
    return out


def test_open_register_parses():
    """治理未决册在位且可解析（至少一条 ## 未决项）。"""
    assert _parse_open(), "charter/open.md 应存在且含至少一条 ## 未决项"
