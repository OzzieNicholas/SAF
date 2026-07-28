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
  test_eval           ——          指标（不可达 F1 / 区域 IoU / 面积比例误差）已知答案锚定
  test_data           ——          程序化标签数据集（oracle 自动打标、两类俱在、按模型切分）
  test_model          H3          形状条件预测：留出(未见)模型上不可达 F1 胜基线（跨模型可行性）
  test_baselines      H2,E4       基线对照：工具尺寸不可忽略(r=0 vs r>0) + 神经胜射线可见性/多数类
  test_label_quality  D-008,D-004 标签质量审核门（六项趋势）：受限盲腔半径单调非减 + 批量分布合理
  test_dataset        D-016       物化数据集：build→load round-trip·两类·按模型切分·标签=oracle·manifest 良构
  test_fusion360      D-017       Fusion360 网格 ingest：OBJ 解析/final 过滤（纯 stdlib）+ box 端到端物化（source=fusion360）
  test_viz            D-018       viz 审计仪器：可达性 montage 出合法 PNG（尺寸符几何 + 红/绿像素在位；命门签收之图）

决策↔性质映射见 charter/README.md。几何性质在 oracle 实现 + 依赖安装前保持 PENDING；
pytest 下相应 test_* 抛 unittest.SkipTest。
"""

PASS, FAIL, PENDING, NA = "PASS", "FAIL", "PENDING", "N/A"


def pending(name, why, decisions=""):
    tag = f"[{decisions}] " if decisions else ""
    return {"name": name, "status": PENDING, "detail": tag + why}


def na(name, why, decisions=""):
    """终态 N/A：经检验**判定为非不变量**或**已被他处覆盖**——非待办、不阻塞 DoD（区别于 PENDING=尚未做）。
    仍可见、附理由；不是 PASS（不声称性质成立），不是 PENDING（不声称还没做）。见 D-027。"""
    tag = f"[{decisions}] " if decisions else ""
    return {"name": name, "status": NA, "detail": tag + why}


def result(name, ok, detail, decisions=""):
    tag = f"[{decisions}] " if decisions else ""
    return {"name": name, "status": PASS if ok else FAIL, "detail": tag + detail}
