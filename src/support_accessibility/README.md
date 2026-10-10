# support_accessibility — 实现包

唯一的 Python 包，按职责分模块，不按阶段号命名。验收性质见 `tests/acceptance/`。

| 模块 | 职责 |
|---|---|
| `oracle/` | 几何 oracle：体素距离场腐蚀、方向 ray-march、边界带精确胶囊求交（`capsule.py`）、方向级可达性场；冻结口径见 `governance/决策台账.md` |
| `data/` | `records.py` 带标签样本与按模型切分；`procedural.py` 程序化已知答案件（含旗舰配对）；`mesh.py` 网格到占据栅格与缠绕安全外移；`overhang.py` 下朝悬垂面提取；`fusion360.py` / `thingi.py` 公开数据 ingest；`dataset.py` 统一数据集读写；`mesh_quality.py` 网格质量审计 |
| `models/` | `convonet.py` 形状条件编码器 + 点查询解码器（ConvONet-lite，需 torch）；`tiny_patch_mlp.py` numpy 小模型，作无全局上下文的对照 |
| `baselines/` | 几何启发式对照：射线可见性（oracle 在 r=0）、多数类、局部规则、粗有限工具代理 |
| `eval/` | `metrics.py` 不可达 F1 / IoU / 点占比误差 / 方向 Top-k / Spearman；`cost.py` 计时、预算外推、数据集摘要；`run_reports.py` 实验运行记录 |
| `viz/` | 可达性审计图（热图拼板） |
| `runtime/` | `data_paths.py` 数据位置解析与逻辑引用；`run_records.py` 运行记录与缓存清理；`console.py` 终端编码与 OpenMP 设置 |

实验产物写入 `artifacts/runs/`，数据集写入数据根（见 `configs/paths.yaml`）。
