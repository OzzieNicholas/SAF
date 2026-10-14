"""治理结构机检 —— 把台账、参考文档和仓库布局变成可执行约束。

纯文本校验，只用 stdlib，现在就真跑、应全绿：
  1) decisions schema：每条 D-0NN 有 裁决/依据/状态
  2) 决策完整性：每条 D-0NN 被验收层作为 decisions= 标注交代，或在结构 allowlist
  3) 参考文档在位：docs/ 的研究背景文档和文献入口存在
  4) 冻结参数键存在：configs/oracle_params.yaml 含 D-021 冻结键
  5) 研发路线不手写门状态（现状看门）
  6) 仓库布局、命名、依赖方向与可移植性（tools/check_structure.py）
"""

import importlib.util
import os
import re

from . import result

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 无专属验收性质、由结构检查或文档守护的决策
STRUCTURAL = {"D-000", "D-004", "D-006", "D-012", "D-013", "D-014", "D-015", "D-018", "D-021", "D-023",
              "D-025", "D-026", "D-027", "D-029", "D-030", "D-031", "D-032", "D-034"}


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


def check_decisions_schema():
    try:
        txt = _read("governance/决策台账.md")
    except OSError as e:
        return result("decisions_schema", False, f"读不到决策台账: {e}")
    ids = re.findall(r"^##\s+(D-\d+)", txt, re.M)
    blocks = re.split(r"^##\s+D-\d+", txt, flags=re.M)[1:]
    missing = []
    for did, block in zip(ids, blocks):
        for field in ("裁决", "依据", "状态"):
            if field not in block:
                missing.append(f"{did}:缺{field}")
    ok = bool(ids) and not missing
    detail = f"{len(ids)} 条决策，schema " + ("完整" if ok else "缺失:" + ",".join(missing))
    return result("decisions_schema", ok, detail)


def check_decisions_covered():
    """每条决策都被验收层作为 decisions= 标注字面量（如 "D-009"）交代，或在结构 allowlist。"""
    try:
        dtxt = _read("governance/决策台账.md")
    except OSError as e:
        return result("decisions_covered", False, f"读不到决策台账: {e}")
    ids = set(re.findall(r"^##\s+(D-\d+)", dtxt, re.M))
    acc = os.path.join(_ROOT, "tests", "acceptance")
    referenced = set()
    for fn in os.listdir(acc):
        if fn.endswith(".py"):
            with open(os.path.join(acc, fn), encoding="utf-8") as f:
                for lit in re.findall(r'"(D-\d+(?:/D-\d+)*)"', f.read()):
                    referenced |= set(re.findall(r"D-\d+", lit))
    orphan = sorted(ids - (referenced | STRUCTURAL))
    return result("decisions_covered", not orphan,
                  f"{len(ids)} 条决策全被验收层交代" if not orphan else "孤儿决策:" + ",".join(orphan))


def check_reference_docs():
    need = [("docs", n) for n in ("研究背景与设计.md", "文献矩阵与相关工作.md")]
    missing = [f"{d}/{n}" for d, n in need if not os.path.exists(os.path.join(_ROOT, d, n))]
    return result("reference_docs_exist", not missing,
                  "研究背景文档与文献入口在位" if not missing else "缺:" + ",".join(missing))


def check_params_keys():
    try:
        txt = _read("configs/oracle_params.yaml")
    except OSError as e:
        return result("params_keys", False, f"读不到 oracle_params.yaml: {e}")
    need = ["semantic", "n_directions", "epsilon_voxels", "resolution", "radius_world", "overhang_angle_deg"]   # D-021 冻结键
    missing = [k for k in need if k not in txt]
    return result("params_keys", not missing,
                  "关键键在位" if not missing else "缺:" + ",".join(missing))


def check_roadmap():
    """研发路线不手写门状态（D-019：现状看门，防状态文档漂移）。"""
    try:
        txt = _read("governance/研发路线.md")
    except OSError as e:
        return result("roadmap_no_handwritten_status", False, f"读不到研发路线: {e}", "D-019")
    banned = [t for t in ("✅", "❌", "⏳", "| 状态 |") if t in txt]
    banned += [w for w in ("PASS", "FAIL", "PENDING", "GREEN", "RED") if re.search(rf"\b{w}\b", txt)]
    return result("roadmap_no_handwritten_status", not banned,
                  "研发路线在位、无手写门状态（现状看门）" if not banned
                  else "含手写门状态 token:" + ",".join(banned), "D-019")


def check_repository_structure():
    """布局、命名、依赖方向、文档规范、可移植性——规则唯一之家是 tools/check_structure.py。"""
    spec = importlib.util.spec_from_file_location(
        "check_structure", os.path.join(_ROOT, "tools", "check_structure.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors = module.check()
    return result("repository_structure", not errors,
                  "布局、命名、依赖方向与可移植性通过" if not errors else "; ".join(errors[:8]), "D-033")


def checks():
    return [check_decisions_schema(), check_decisions_covered(), check_reference_docs(),
            check_params_keys(), check_roadmap(), check_repository_structure()]


# —— pytest 入口：真断言，现在就应绿 ——
def _assert(r):
    assert r["status"] == "PASS", r["detail"]


def test_decisions_schema():
    _assert(check_decisions_schema())


def test_decisions_covered():
    _assert(check_decisions_covered())


def test_reference_docs():
    _assert(check_reference_docs())


def test_params_keys():
    _assert(check_params_keys())


def test_roadmap():
    _assert(check_roadmap())


def test_repository_structure():
    _assert(check_repository_structure())
