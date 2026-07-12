"""文档断言机检 —— 把 ffm §9「文档断言机检」升级到"机检科学决策"。

纯文本校验，只用 stdlib，**现在就真跑、应全绿**（证明治理散文这层当场就有牙）：
  1) decisions schema：每条 D-00x 有 裁决/依据/状态（日期已去，时间归 git；见 D-011 起）
  2) reference 富参考在位：docs/ 的 5 份编号文档存在（committed 富参考家）
  3) 无残留黑话路径：当前态散文/配置（含 conf/params.yaml）不再出现
     research/ harness/ workflow/ governance/ constitution report.py（旧名/旧路径）
     （decisions.md 是只增不改的历史台账，合法保留旧名，故豁免）
  4) params 关键键存在：conf/params.yaml 含 semantic/n_directions/voxel_res/radii/overhang_angle_deg
"""

import os
import re

from . import result

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


def check_decisions_schema():
    try:
        txt = _read("charter/decisions.md")
    except OSError as e:
        return result("decisions_schema", False, f"读不到 decisions.md: {e}")
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


def check_reference_docs():
    need = ["0_背景与边界.md", "0_执行路线与阶段门.md", "1_选题与研究定位.md",
            "2_文献矩阵与相关工作.md", "3_实验闭环设计.md"]
    missing = [n for n in need
               if not os.path.exists(os.path.join(_ROOT, "docs", n))]
    return result("reference_docs_exist", not missing,
                  "5 份富参考在位" if not missing else "缺:" + ",".join(missing))


def check_no_stale_paths():
    stale = ("research/", "harness/", "workflow/", "governance/", "constitution", "report.py")
    # decisions.md 豁免（只增不改的历史台账）
    files = ["charter/problem.md", "charter/evidence.md", "charter/constraints.md",
             "charter/README.md", "CLAUDE.md", "conf/params.yaml"]
    hits = []
    for rel in files:
        try:
            txt = _read(rel)
        except OSError:
            continue
        for s in stale:
            if s in txt:
                hits.append(f"{rel}:{s}")
    return result("no_stale_paths", not hits,
                  "当前态散文无残留黑话路径" if not hits else "残留:" + "; ".join(hits))


def check_params_keys():
    try:
        txt = _read("conf/params.yaml")
    except OSError as e:
        return result("params_keys", False, f"读不到 params.yaml: {e}")
    need = ["semantic", "n_directions", "voxel_res", "radii", "overhang_angle_deg"]
    missing = [k for k in need if k not in txt]
    return result("params_keys", not missing,
                  "关键键在位" if not missing else "缺:" + ",".join(missing))


def checks():
    return [check_decisions_schema(), check_reference_docs(),
            check_no_stale_paths(), check_params_keys()]


# —— pytest 入口：真断言，现在就应绿 ——
def test_decisions_schema():
    r = check_decisions_schema()
    assert r["status"] == "PASS", r["detail"]


def test_reference_docs():
    r = check_reference_docs()
    assert r["status"] == "PASS", r["detail"]


def test_no_stale_paths():
    r = check_no_stale_paths()
    assert r["status"] == "PASS", r["detail"]


def test_params_keys():
    r = check_params_keys()
    assert r["status"] == "PASS", r["detail"]
