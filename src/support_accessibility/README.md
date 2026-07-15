# support_accessibility — 实现包（按模块，不按阶段号）

> 唯一 Python 包，代码深度全在此。按 TDD 内环（探索 → 计划 → 测试先行）填充，
> 测试对着 `tests/acceptance/` 写。阶段号（阶段0–10）与实验号（E0–E8）是逻辑标签，不作文件名前缀。

| 模块 | 职责 |
|---|---|
| `oracle/` | 几何 oracle：体素/距离场腐蚀、方向扫掠、标签生成（冻结口径见 `charter/decisions.md`）|
| `data/` | 程序化已知答案件生成（含旗舰配对）+ 公开数据（ABC/Thingi10K）清洗/筛选/切分；`dataset.py` 物化/载入统一数据集（D-016）|
| `eval/` | 点/区域/方向/效率指标 + 预算外推 |
| `models/` | 形状条件编码器 + 点查询解码器 |
| `baselines/` | 几何启发式对照基线（射线可见性=oracle@r=0 / 多数类 / 局部规则；E4 对照，非主线，见 D-015）|
| `viz/` | 热图、方向球面图、失败案例 |

实验产物写入 `runs/`（DVC，按 E0–E8 + run-id，机器 emit）；**数据集**物化到 `data/processed/`（D-016，gitignore）。配置见 `conf/params.yaml`（Hydra）。
