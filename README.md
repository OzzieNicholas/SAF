# SAF — Support Accessibility Field

[![gate](https://github.com/OzzieNicholas/SAF/actions/workflows/gate.yml/badge.svg)](https://github.com/OzzieNicholas/SAF/actions/workflows/gate.yml)

金属增材制造**支撑接触区**表面的几何可达性代理评价与**形状条件神经预测**。
在单个公开三维零件上，识别构建方向决定的支撑接触区，评价其在简化工具条件下的几何可接近性，
并用形状条件神经场在未见模型上预测——为 DfAM 预处理提供不同于支撑体积/过悬面积的后处理几何风险维度。
（几何/AI 题，DfAM 前端；非材料/工艺实验，非生产认证。）

## 从哪读起

- **治理入口**：[`charter/README.md`](charter/README.md) — 治理地图、决策↔性质映射、修改触发。
- **问题定义**：[`charter/problem.md`](charter/problem.md)
- **冻结决策**：[`charter/decisions.md`](charter/decisions.md)（判定语义 D-001..）
- **验收门**：`python tests/gate.py`（决策的可执行守护；仍 RED：多项门 PENDING by design，状态跑门看）

## 布局

```
charter/    治理散文 + 地图（problem/decisions/evidence/constraints/conventions/deferred）
docs/       退役富参考（问题/文献/实验/执行路线全本，只读）
src/support_accessibility/   实现包（oracle/data/eval/models/baselines/viz）
tests/      验收层（acceptance/ = 决策↔性质）+ gate.py（棘轮门）
conf/       Hydra 配置（params.yaml）
method/     研发方法论（本地手管，gitignore）
data/        数据：processed/ = 统一数据集（D-016，tools/build_dataset.py 生成，gitignore）
runs/ plans/ 产物（DVC，E0–E8+run-id）/ 计划（就绪后生成）
```
