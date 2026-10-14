"""验收性质：把 governance/ 中的冻结决策翻译成会运行的检查。

每个子模块暴露 checks() -> list[dict(name, status, detail)]，由 tests/gate.py 汇总；
pytest 直接运行其中的 test_* 函数。状态取值：PASS、FAIL、PENDING（所需外部输入缺失）、
N/A（经检验判定为非不变量，或已被他处覆盖，附理由）。

模块与守护内容：
  test_env                  环境：igl、numpy、scipy、trimesh 可导入，Python ≥ 3.12
  test_known_answers        判定语义：盲腔不可达、开阔下朝面可达
  test_capsule              边界带精确胶囊细化与三态判定
  test_differential         体素腐蚀与暴力参考对拍
  test_properties           变形与单调性性质（已证伪的不变量跳过或判 N/A，理由见模块）
  test_invariants           网格健全性检查
  test_mesh_frontend        网格前端（缠绕数占据、缠绕安全外移）的已知答案
  test_support_contact      支撑接触区提取（下朝悬垂面）
  test_eval                 指标的已知答案锚定
  test_procedural_cases     程序化已知答案件：两类俱在、按模型切分
  test_dataset              物化数据集的往返读写、标签与 oracle 一致、manifest 良构
  test_fusion360            Fusion 360 网格解析与端到端物化
  test_thingi               Thingi10K 确定性子采样
  test_model                形状条件预测在未见模型上胜过多数类基线
  test_direction_field      方向级可达性场：逐方向判定与模型输出头
  test_baselines            工具尺寸效应与基线对照
  test_label_quality        标签质量趋势（六项）
  test_figure_face_mapping  论文样本的面映射（外部数据缺失时 PENDING）
  test_governance           决策台账格式与覆盖、参考文档、路线图、仓库布局

决策与性质的对应见 governance/README.md。
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
