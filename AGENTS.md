# AGENTS.md

给智能体的项目规则。项目介绍、目录结构和命令见 [README.md](README.md)，领域约束与机械检查以 `governance/` 和 `tests/` 为准。

## 项目

SAF（Support Accessibility Field）：金属增材制造支撑接触区表面的几何可达性代理评价与形状条件神经预测。几何 / AI 课题，DfAM 前端，不是材料或工艺实验。判定语义与冻结决定见 `governance/决策台账.md`。

## 环境

- conda 环境 `saf`（Python 3.12，依赖见 `environment.yml`），由 `tests/acceptance/test_env.py` 守护。
- 硬件上限：单卡 RTX 4060 Ti / 32G，模型与数据规模据此控制。
- 非交互 shell 先 `conda activate saf` 再运行；不要直接调用环境里的 `python.exe`（未激活会因 OpenBLAS 延迟加载崩溃），不要同时开两个 `conda run`。

## 完成的定义

- `python tests/gate.py` 为绿（工程门不访问外部数据；`--paper` 才检查论文证据）。
- `python -m pytest tests -q` 全绿，指标不劣于基线（回归门）。

## 不能碰的

- 企业边界；oracle 判定口径私自修改（见 `governance/铁律约束.md`，改动必须在决策台账新增 supersede 条目）。
- 把方向评价写成方向优化；声称方法首创；把哈希当主创新。
- oracle / 标签未通过质量门就训练网络。

## 约定

- 代码按模块组织（`src/support_accessibility/{oracle,data,eval,models,baselines,viz,runtime}`），不按阶段号命名；阶段号（阶段 0–10）和假设号（H1–H5）只是逻辑标签，用在决策台账和结果账本里，不出现在文件名中。
- 依赖方向：`src` ← `experiments` / `tools` / `paper` ← `tests`；`src` 不得导入后者。
- 路径只通过 `support_accessibility.runtime.data_paths` 取得，仓库内不写绝对路径（由 `tools/check_structure.py` 检查）。
- 机器产物写 `artifacts/runs/`（证据）和 `artifacts/cache/`（可清理），都不入库；数据放 `data/`（不入库）。
- 文档与命名规范见 `governance/工程规范.md`。
