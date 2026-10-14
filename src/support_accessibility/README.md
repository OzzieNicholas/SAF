# support_accessibility — 实现包

唯一的 Python 包，按职责分模块，不按阶段号命名。验收性质见 `tests/acceptance/`。

| 模块 | 职责 |
|---|---|
| `oracle/` | 几何 oracle：体素距离场腐蚀、方向 ray-march、边界带精确胶囊求交（`capsule.py`）、方向级可达性场；冻结口径见 `governance/决策台账.md` |
| `data/` | `records.py` 带标签样本、按零件切分与两类零件筛选；`procedural.py` 程序化已知答案件（含旗舰配对）；`mesh.py` 网格到占据栅格、缠绕安全外移、接触查询点生成与网格标注（入库、实验与作图共用）；`overhang.py` 下朝悬垂面提取与 6 个轴向候选构建方向；`fusion360.py` / `thingi.py` 公开数据 ingest 与方向级标签；`dataset.py` 统一数据集读写；`mesh_quality.py` 网格质量审计 |
| `models/` | `convonet.py` 形状条件编码器 + 点查询解码器（ConvONet-lite，需 torch）；`tiny_patch_mlp.py` numpy 小模型，作无全局上下文的对照 |
| `baselines/` | 对照基线：不经细化的体素判定（可调半径与方向数，零半径射线可见性与 16 方向粗判定是其特例）、多数类、局部规则 |
| `eval/` | `metrics.py` 不可达 F1 / IoU / 方向 Top-k / Spearman；`cost.py` 标签构建的预算外推与输入数据摘要 |
| `runtime/` | `data_paths.py` 数据位置解析与逻辑引用；`run_records.py` 运行记录与缓存清理；`console.py` 终端编码与 OpenMP 设置 |

实验产物写入 `artifacts/runs/`，数据集写入数据根（见 `configs/paths.yaml`）。
