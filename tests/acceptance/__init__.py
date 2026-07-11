"""验收层（原"harness"概念溶于此）：把 charter/decisions.md 的冻结决策翻成会跑的性质。

每个子模块暴露 checks() -> list[dict(name,status,detail)]，由 tests/gate.py 汇总成裁决：
  test_env            ——          环境自检（igl/numpy/scipy/trimesh + py≥3.12）
  test_known_answers  D-001,D-002  盲腔=不可达 / 开阔下朝面=可达
  test_properties     D-003,D-005  变形:联合旋转等变 / 尺度不变 / 半径单调 / 方向单调
  test_differential   D-003        体素 vs 暴力胶囊对拍
  test_invariants     ——          网格 sanity
  test_charter        ——          文档断言机检（现在就真跑变绿）
  test_mesh_frontend  D-007        网格前端（igl solidify→occupancy）复现已知答案 + IoU
  test_support_contact D-010       支撑接触区提取（下朝悬垂面 S(P,d)：提取/方向/阈值/端到端）

决策↔性质映射见 charter/README.md。几何性质在 oracle 实现 + 依赖安装前保持 PENDING；
pytest 下相应 test_* 抛 unittest.SkipTest。
"""

PASS, FAIL, PENDING = "PASS", "FAIL", "PENDING"


def pending(name, why, decisions=""):
    tag = f"[{decisions}] " if decisions else ""
    return {"name": name, "status": PENDING, "detail": tag + why}


def result(name, ok, detail, decisions=""):
    tag = f"[{decisions}] " if decisions else ""
    return {"name": name, "status": PASS if ok else FAIL, "detail": tag + detail}
