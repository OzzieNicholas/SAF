"""未决触发册 → 门：把 governance/deferred.md 的未决项接进 gate（人肉提醒 → 门提醒）。

每条未决项 = 前置条件(触发) → 义务。checks() 把每条 surfaced 为门项、指回 deferred.md id；
机器可判的条目（flagship-pair 的 import-check）附注"休眠/可闭合"。闭合：满足义务后从 deferred.md 删除。
纯 stdlib 解析 deferred.md；机器可判条目的依赖在函数内 import（缺失不崩）。
"""

import os
import re

from . import pending, result

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DEFERRED = os.path.join(_ROOT, "governance", "deferred.md")


def _parse_deferred():
    """解析 governance/deferred.md → [(id, 触发, 义务), ...]。"""
    try:
        with open(_DEFERRED, encoding="utf-8") as f:
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
    if not os.path.exists(_DEFERRED):
        return [pending("deferred_register", "governance/deferred.md 缺失", "")]
    items = _parse_deferred()
    if not items:                       # 空册 = 无开放未决义务（终态，非 PENDING；闭合记录在 decisions.md）
        return [result("deferred_register", True, "无开放未决义务（历次闭合见 decisions.md）", "")]
    out = []
    for oid, trig, duty in items:
        detail = f"触发={trig} → 义务={duty}"
        if oid == "flagship-pair" and _flagship_implemented() is True:
            out.append(result(f"deferred:{oid}", True, detail + "（已触发：flagship_pair 已实现，可闭合）", ""))
        else:
            if oid == "flagship-pair":
                detail += "（休眠：E1 未到，flagship_pair 仍 NotImplementedError）"
            out.append(pending(f"deferred:{oid}", detail, ""))
    return out


def test_deferred_register_parses():
    """治理未决册在位且可解析（空册=无开放义务，合法终态；解析不得抛错）。"""
    assert os.path.exists(_DEFERRED), "governance/deferred.md 应存在"
    _parse_deferred()   # 不抛即可（空册返回 []，是合法终态）
