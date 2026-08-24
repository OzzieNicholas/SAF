"""治理结构机检 —— 把控制平面适配与项目台账变成可执行约束。

纯文本校验，只用 stdlib，**现在就真跑、应全绿**（证明治理散文这层当场就有牙）：
  1) decisions schema：每条 D-00x 有 裁决/依据/状态（日期已去，时间归 git；见 D-011 起）
  2) reference 富参考在位：docs/ 的 5 份编号文档和文献输入区存在（committed 富参考家）
  3) 活动文件中不再出现旧目录路径；历史决策和个人 GPT 备忘明确豁免
  4) params 关键键存在：configs/params.yaml 含 semantic/n_directions/epsilon_voxels/resolution/radius_world/overhang_angle_deg（D-021 冻结键）
  5) 决策完整性：每条 D-0NN 被验收层作为 decisions= 标注交代（语义化，非裸提及），或在结构 allowlist
  6) 交付物、研究输入、临时产物和已退役个人目录边界不漂移
"""

import os
import re
import json

from . import result

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


def check_decisions_schema():
    try:
        txt = _read("governance/decisions.md")
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
    extra = ["README.md", "references_cn.md"]
    missing += [f"references/{n}" for n in extra
                if not os.path.exists(os.path.join(_ROOT, "docs", "references", n))]
    literature = os.path.join(_ROOT, "docs", "references", "literature")
    has_literature = False
    if os.path.isdir(literature):
        with os.scandir(literature) as entries:
            has_literature = any(entry.is_file() and entry.name == "README.md" for entry in entries)
    if not has_literature:
        missing.append("references/literature")
    return result("reference_docs_exist", not missing,
                  "富参考与文献输入区在位" if not missing else "缺:" + ",".join(missing))


def check_asset_boundaries():
    """研究输入、论文交付物和本地临时目录不能重新混合。"""
    forbidden = [
        "tmp",
        os.path.join("deliverables", "paper", "reference"),
        os.path.join("deliverables", "paper", "references_cn.md"),
    ]
    missing = [rel.replace(os.sep, "/") for rel in forbidden
               if os.path.exists(os.path.join(_ROOT, rel))]
    required = [
        os.path.join("docs", "references", "README.md"),
        os.path.join("docs", "references", "references_cn.md"),
        os.path.join("docs", "references", "literature"),
    ]
    missing += [f"required:{rel.replace(os.sep, '/')}" for rel in required
                if not os.path.exists(os.path.join(_ROOT, rel))]
    return result("asset_boundaries", not missing,
                  "研究输入、交付物和临时目录边界清晰" if not missing
                  else "边界漂移:" + ",".join(missing))


def check_retired_data_and_dvc():
    """The active tree cannot silently regain repository data or DVC control files."""
    forbidden = [
        "data",
        ".dvcignore",
        "dvc.yaml",
        "dvc.lock",
        os.path.join("artifacts", "archive"),
        os.path.join("deliverables", "archive"),
    ]
    found = [rel.replace(os.sep, "/") for rel in forbidden
             if os.path.exists(os.path.join(_ROOT, rel))]
    return result("retired_data_and_dvc", not found,
                  "仓库内数据、DVC 和旧 archive 均未复活" if not found
                  else "禁止的旧资产:" + ",".join(found))


def check_retired_roots():
    """旧治理入口、个人备忘目录和旧 Agent 入口不得复活。"""
    legacy = {
        "CLAUDE.md", "constitution.md", "decisions.md", "research.md",
        "scaffold.sh", "使用说明.md", "运行协议.md",
    }
    found = []
    for name in legacy:
        if os.path.exists(os.path.join(_ROOT, name)):
            found.append(name)
    for rel in ("method", "plans", os.path.join("governance", "reference")):
        if os.path.exists(os.path.join(_ROOT, rel)):
            found.append(rel.replace(os.sep, "/"))
    return result("retired_roots", not found,
                  "个人备忘目录和退役入口均已清理" if not found
                  else "禁止的旧入口:" + ",".join(found))


def check_no_stale_paths():
    """旧路径只允许出现在不可改写的历史台账或个人备忘中。

    匹配要求旧目录位于路径开头，因而不会把新的 ``deliverables/paper``、
    ``artifacts/runs`` 或 ``tools/hooks`` 误报为旧根目录。
    """
    stale = {
        "charter/": re.compile(r"(?<![A-Za-z0-9_/-])charter/"),
        "conf/": re.compile(r"(?<![A-Za-z0-9_/-])conf/"),
        "paper/": re.compile(r"(?<![A-Za-z0-9_/-])paper/"),
        "runs/": re.compile(r"(?<![A-Za-z0-9_/-])runs/"),
        "hooks/": re.compile(r"(?<![A-Za-z0-9_/-])hooks/"),
        "charter": re.compile(r"\bcharter\b"),
        "test_charter": re.compile(r"\btest_charter\b"),
    }
    hits = []
    skip = {"governance/decisions.md", "docs/other/GPT.md",
            "tests/acceptance/test_governance.py", "tools/check_structure.py"}
    for base, dirs, names in os.walk(_ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", "data", "artifacts", "tmp"}]
        for name in names:
            path = os.path.join(base, name)
            rel = os.path.relpath(path, _ROOT).replace(os.sep, "/")
            if rel in skip:
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    txt = f.read()
            except (OSError, UnicodeDecodeError):
                continue
            for label, pattern in stale.items():
                if pattern.search(txt):
                    hits.append(f"{rel}:{label}")
    return result("no_stale_paths", not hits,
                  "当前态散文无残留黑话路径" if not hits else "残留:" + "; ".join(hits))


def check_project_manifest():
    """SAF 适配声明必须是完整、可解析且与仓库布局一致的 JSON。"""
    path = os.path.join(_ROOT, "governance", "project.json")
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError) as e:
        return result("project_manifest", False, f"project.json 读取/解析失败: {e}")
    required = {
        "schema_version": "1.1",
        "project": "SAF",
    }
    missing = [key for key in required if manifest.get(key) != required[key]]
    roots = manifest.get("roots", {})
    expected_roots = {
        "governance": "governance",
        "source": "src",
        "tests": "tests",
        "tools": "tools",
        "configs": "configs",
        "runs": "artifacts/runs",
        "paper": "deliverables/paper",
        "references": "docs/references",
        "artifacts": "artifacts",
        "deliverables": "deliverables",
    }
    missing += [f"roots.{key}" for key, value in expected_roots.items()
                if roots.get(key) != value]
    external = manifest.get("external_data", {})
    if external.get("default_root") != "E:/Work/Data":
        missing.append("external_data.default_root")
    if external.get("temporary_root") != "E:/Work/Data/Temporary/SAF":
        missing.append("external_data.temporary_root")
    lifecycle = manifest.get("artifact_lifecycle", {})
    for key, value in {"evidence_root": "artifacts/runs", "cache_root": "artifacts/cache",
                       "cache_ttl_days": 7, "latest_compatibility_file": "latest.json"}.items():
        if lifecycle.get(key) != value:
            missing.append(f"artifact_lifecycle.{key}")
    adapters = manifest.get("adapters", {})
    for key in ("pytest", "gate", "evaluation", "figures", "latex", "paper"):
        if key not in adapters or not isinstance(adapters[key], dict):
            missing.append(f"adapters.{key}")
    return result("project_manifest", not missing,
                  "SAF 控制平面适配声明完整" if not missing else "缺失/不一致:" + ",".join(missing))


def check_control_plane_spec():
    """SAF governance is self-contained; no external control-plane bundle is required."""
    return result("control_plane_spec", True, "SAF 自包含治理，不依赖 docs/other/project-control-plane")


def check_path_consistency():
    """关键入口、忽略规则和适配声明使用同一组活动根路径。"""
    checks = {
        ".gitignore": ("artifacts/runs/", "artifacts/cache/", "tmp/"),
        "tests/gate.py": ("artifacts", "runs", "regression", "latest.json"),
        "tests/acceptance/test_deferred.py": ("governance", "deferred.md"),
        "tools/check_conventions.py": ("governance/conventions.md", "tools/hooks/"),
        "tools/check_structure.py": ("AGENTS.md", "artifacts/cache"),
        "governance/README.md": ("project.json", "governance"),
        "AGENTS.md": ("governance/README.md", "artifacts/cache/"),
        "docs/README.md": ("docs/references", "governance"),
    }
    missing = []
    for rel, tokens in checks.items():
        try:
            txt = _read(rel)
        except OSError:
            missing.append(rel)
            continue
        missing.extend(f"{rel}:{token}" for token in tokens if token not in txt)
    return result("path_consistency", not missing,
                  "活动根路径一致" if not missing else "不一致:" + "; ".join(missing))


def check_params_keys():
    try:
        txt = _read("configs/params.yaml")
    except OSError as e:
        return result("params_keys", False, f"读不到 params.yaml: {e}")
    need = ["semantic", "n_directions", "epsilon_voxels", "resolution", "radius_world", "overhang_angle_deg"]   # D-021 冻结键（非作废的 voxel_res/临时 radii）
    missing = [k for k in need if k not in txt]
    return result("params_keys", not missing,
                  "关键键在位" if not missing else "缺:" + ",".join(missing))


def check_decisions_covered():
    """完整性：每条 decisions.md 的 D-0NN 都被验收层**作为 decisions= 标注**交代（非仅 docstring/detail 裸提及），
    或在结构 allowlist——杜绝孤儿决策。语义化：只认 result()/na()/pending() 的决策标签字面量 "D-NNN"（可斜杠联合，如 "D-007/D-009"）。"""
    STRUCTURAL = {"D-000", "D-004", "D-006", "D-012", "D-013", "D-014", "D-015", "D-018", "D-021", "D-023", "D-025", "D-026", "D-027", "D-029", "D-030", "D-031", "D-032"}   # 结构/标注/布局/治理/规范/台账策展/主线/命门签收/参数冻结/数据源范围/标签审核机制/门激活/终态DoD/控制平面迁移/资产边界/生命周期/外部数据与论文包：无专属性质，由结构检查守护
    try:
        dtxt = _read("governance/decisions.md")
    except OSError as e:
        return result("decisions_covered", False, f"读不到 decisions.md: {e}")
    ids = set(re.findall(r"^##\s+(D-\d+)", dtxt, re.M))
    acc = os.path.join(_ROOT, "tests", "acceptance")
    referenced = set()
    for fn in os.listdir(acc):
        if fn.endswith(".py"):
            with open(os.path.join(acc, fn), encoding="utf-8") as f:
                for lit in re.findall(r'"(D-\d+(?:/D-\d+)*)"', f.read()):   # 仅决策标签字面量（decisions= 标注），排除裸提及
                    referenced |= set(re.findall(r"D-\d+", lit))
    orphan = sorted(ids - (referenced | STRUCTURAL))
    return result("decisions_covered", not orphan,
                  f"{len(ids)} 条决策全被验收层交代（decisions= 标注）" if not orphan else "孤儿决策:" + ",".join(orphan))


def check_conventions_present():
    """规范治理在位：散文规范和两个可执行结构/动作检查器都存在。"""
    need = ["governance/conventions.md", "tools/check_conventions.py", "tools/check_structure.py"]
    missing = [p for p in need if not os.path.exists(os.path.join(_ROOT, p))]
    return result("conventions_present", not missing,
                  "动作规范治理在位（conventions.md + 校验器）" if not missing else "缺:" + ",".join(missing))


def check_roadmap():
    """研发弧位置图在位，且**不手写门状态**（D-019：现状看门、防 record.md 式漂移）。

    禁用集窄而精：门图标 ✅❌⏳、独立词 PASS/FAIL/PENDING/GREEN/RED、状态列头 `| 状态 |`；
    不误伤中文"状态"/"降级"等正当散文。只扫 roadmap.md（现状仍一律跑门看）。
    """
    try:
        txt = _read("governance/roadmap.md")
    except OSError as e:
        return result("roadmap_no_handwritten_status", False, f"读不到 roadmap.md: {e}", "D-019")
    banned = [t for t in ("✅", "❌", "⏳", "| 状态 |") if t in txt]
    banned += [w for w in ("PASS", "FAIL", "PENDING", "GREEN", "RED") if re.search(rf"\b{w}\b", txt)]
    return result("roadmap_no_handwritten_status", not banned,
                  "弧位置图在位、无手写门状态（现状看门）" if not banned
                  else "含手写门状态 token:" + ",".join(banned), "D-019")


def checks():
    return [check_decisions_schema(), check_reference_docs(),
            check_asset_boundaries(), check_retired_data_and_dvc(), check_retired_roots(), check_no_stale_paths(),
            check_params_keys(), check_decisions_covered(),
            check_conventions_present(), check_roadmap(), check_project_manifest(),
            check_control_plane_spec(), check_path_consistency()]


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


def test_decisions_covered():
    r = check_decisions_covered()
    assert r["status"] == "PASS", r["detail"]


def test_conventions_present():
    r = check_conventions_present()
    assert r["status"] == "PASS", r["detail"]


def test_roadmap():
    r = check_roadmap()
    assert r["status"] == "PASS", r["detail"]


def test_asset_boundaries():
    r = check_asset_boundaries()
    assert r["status"] == "PASS", r["detail"]


def test_retired_data_and_dvc():
    r = check_retired_data_and_dvc()
    assert r["status"] == "PASS", r["detail"]


def test_retired_roots():
    r = check_retired_roots()
    assert r["status"] == "PASS", r["detail"]


def test_project_manifest():
    r = check_project_manifest()
    assert r["status"] == "PASS", r["detail"]


def test_control_plane_spec():
    r = check_control_plane_spec()
    assert r["status"] == "PASS", r["detail"]


def test_path_consistency():
    r = check_path_consistency()
    assert r["status"] == "PASS", r["detail"]
