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
论文写作中（`deliverables/paper/`）。权威结果数字见 **[`governance/results.md`](governance/results.md)**。

## 从哪读起（按你想知道的）

- **做什么 / 为什么 / 硬约束 / 非目标 / 指标**（需求）→ [`governance/problem.md`](governance/problem.md) + [`governance/constraints.md`](governance/constraints.md)（不可破铁律）
- **做到哪了 / 有哪些结果**（完成情况）→ 跑 `python tests/gate.py`（现 **GREEN**：budget/regression/label_audit PASS + 4 项 N/A）｜**[`governance/results.md`](governance/results.md)**（结果账本：假设→指标→数值±std→样本→**复现命令** + 局限）｜[`governance/roadmap.md`](governance/roadmap.md)（研发弧位置）
- **怎么判定 / 为什么这么设计**（决策）→ [`governance/decisions.md`](governance/decisions.md)（判定语义/口径 D-000..D-030，append-only 台账）+ [`governance/README.md`](governance/README.md)（决策↔性质映射 + 修改触发）
- **当前配置 / 冻结口径** → [`configs/params.yaml`](configs/params.yaml)（**D-021 冻结**：n_dir=128 / res=48+细化 / radius=0.05 / overhang=45° / ε=1.5）+ [`environment.yml`](environment.yml)（conda env `saf`）
- **怎么跑 / 复现** → 建环境 `conda env create -f environment.yml`；工程门 `python tests/gate.py`；实验 CLI 在 `tools/`（数据默认位于 `E:\Work\Data\Temporary\SAF`，可由 `SAF_DATA_ROOT`/CLI 覆盖）；论文门 `python deliverables/paper/pipeline/paper_gate.py --strict`；论文构建 `python deliverables/paper/pipeline/build_paper.py --strict-zotero`；非交互跑法注意见 [`AGENTS.md`](AGENTS.md)「怎么跑」。

## 布局

```
governance/    治理散文 + 地图（problem/decisions/evidence/constraints/conventions/deferred）
docs/       退役富参考（问题/文献/实验/执行路线全本，只读）
docs/references/  只读文献入口（Zotero 指针/候选书目；PDF 不入仓库）
deliverables/paper/      论文下游包（源稿、pipeline、canonical 图/PDF、证据与审稿）
src/support_accessibility/   实现包（oracle/data/eval/models/baselines/viz）
tests/      验收层（tests/acceptance/）+ 单元层（tests/unit/）+ 论文层（tests/paper/）+ gate.py（棘轮门）
configs/       冻结口径与外部数据配置（params.yaml）
E:\\Work\\Data/  外部原始网格与 processed 数据（由 tools/data_paths.py 解析，不入 SAF）
artifacts/runs/ 机器运行证据（结果/审计/QA，含 run-id；gitignore）
artifacts/cache/ 机器运行缓存（检查点/日志/候选图，可按 TTL 清理）
```

运行契约和外部运行时管理计划，不建立第二套 `plans/` 权威；artifact 生命周期见 [`artifacts/README.md`](artifacts/README.md)。
