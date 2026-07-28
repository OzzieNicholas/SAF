# SAF — Support Accessibility Field

[![gate](https://github.com/OzzieNicholas/SAF/actions/workflows/gate.yml/badge.svg)](https://github.com/OzzieNicholas/SAF/actions/workflows/gate.yml)

金属增材制造**支撑接触区**表面的几何可达性代理评价与**形状条件神经预测**。
在单个公开三维零件上，识别构建方向决定的支撑接触区，评价其在简化工具条件下的几何可接近性，
并用形状条件神经场在未见模型上预测——为 DfAM 预处理提供不同于支撑体积/过悬面积的后处理几何风险维度。
（几何/AI 题，DfAM 前端；非材料/工艺实验，非生产认证。）

> 📖 **想一篇读懂全项目、不必看代码？** → **[`OVERVIEW.md`](OVERVIEW.md)**（自足综述：需求·方法·关键决策·结果·状态·配置·局限·治理·复现）。

## 一句话现状

尺子（几何 oracle）+ 三数据源（Fusion360/Thingi10K/程序化）+ 形状条件神经预测**全就位**；
假设 **H1/H2/H3/H5 · E1/E4/E5/E8 + 消融** 全部坐实、**各有可复现器**（`tools/`）；验收门 **GREEN**（工程 DoD 达成，D-027）。
论文写作中（`paper/`）。权威结果数字见 **[`charter/results.md`](charter/results.md)**。

## 从哪读起（按你想知道的）

- **做什么 / 为什么 / 硬约束 / 非目标 / 指标**（需求）→ [`charter/problem.md`](charter/problem.md) + [`charter/constraints.md`](charter/constraints.md)（不可破铁律）
- **做到哪了 / 有哪些结果**（完成情况）→ 跑 `python tests/gate.py`（现 **GREEN**：budget/regression/label_audit PASS + 4 项 N/A）｜**[`charter/results.md`](charter/results.md)**（结果账本：假设→指标→数值±std→样本→**复现命令** + 局限）｜[`charter/roadmap.md`](charter/roadmap.md)（研发弧位置）
- **怎么判定 / 为什么这么设计**（决策）→ [`charter/decisions.md`](charter/decisions.md)（判定语义/口径 D-001..D-027，append-only 台账）+ [`charter/README.md`](charter/README.md)（决策↔性质映射 + 修改触发）
- **当前配置 / 冻结口径** → [`conf/params.yaml`](conf/params.yaml)（**D-021 冻结**：n_dir=128 / res=48+细化 / radius=0.05 / overhang=45° / ε=1.5）+ [`environment.yml`](environment.yml)（conda env `saf`）
- **怎么跑 / 复现** → 建环境 `conda env create -f environment.yml`；验收门 `python tests/gate.py`；实验 CLI 在 `tools/`（`train_convonet` H3 · `eval_h5` H5 · `eval_e5` E5 · `eval_h1/h2/e8/ablation` · `audit_labels` 命门审核 · `regression_check` 回归门；每条**复现命令见 `results.md`**）；一键数据流水线 `dvc repro`；非交互跑法注意见 [`CLAUDE.md`](CLAUDE.md)「怎么跑」。

## 布局

```
charter/    治理散文 + 地图（problem/decisions/evidence/constraints/conventions/deferred）
docs/       退役富参考（问题/文献/实验/执行路线全本，只读）
paper/      论文草稿轨道（写作实验并行，活文档；从 charter 播种）
src/support_accessibility/   实现包（oracle/data/eval/models/baselines/viz）
tests/      验收层（acceptance/ = 决策↔性质）+ gate.py（棘轮门）
conf/       Hydra 配置（params.yaml）
method/     研发方法论（本地手管，gitignore）
data/        数据：processed/ = 统一数据集（D-016；tools/build_dataset.py 程序化 / build_fusion360.py 网格源，gitignore）
runs/ plans/ 产物（DVC，E0–E8+run-id）/ 计划（就绪后生成）
```
