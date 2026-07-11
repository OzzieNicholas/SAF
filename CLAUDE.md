# CLAUDE.md

<!-- 行为护栏。薄、稳定、写一次基本不动。给智能体读。铁律见 charter/constraints.md。 -->

## 项目

SAF (Support Accessibility Field)：金属增材制造**支撑接触区**表面的几何可达性代理评价与**形状条件神经预测**。几何/AI 题，DfAM 前端，非材料/工艺实验。治理入口见 `charter/README.md`；判定语义与冻结决定见 `charter/decisions.md`。

## 技术栈 / 环境

- Python；几何：trimesh / Open3D / libigl（generalized winding number 判内外）/ numpy / scipy（距离变换）。
- 神经：PyTorch；可选 tiny-cuda-nn / Kaolin / PyTorch3D。
- 实验：DVC（流水线/产物）+ Hydra（`conf/params.yaml`）。
- 硬件上限：单卡 RTX 4060 / 32G，模型与数据规模据此控制。
- **环境**：conda env `sfa`（py3.12，conda-forge）；建/复现 `conda env create -f environment.yml`；由 `tests/acceptance/test_env.py` 的 `env_ready` 门守护（环境不对当场红）。

## 完成的定义（Definition of Done）

- 验收门通过：`python tests/gate.py` 绿
- 所有测试为绿；指标不劣于基线（回归门）

## 怎么跑

- 验收门：`conda run -n sfa python tests/gate.py`（当前 RED，几何未实现）
- 测试：`conda run -n sfa python -m pytest -q`
- 实验：`conda run -n sfa dvc repro`（就绪后）
- 非交互/agent 兜底：直接用 env 的 python `D:\Miniforge\Install\envs\sfa\python.exe`

## 绝不能碰

- 企业边界、oracle 判定口径私改（见 `charter/constraints.md`）。
- 把方向评价写成方向优化；声称方法首创；把哈希当主创新。
- oracle/标签未过质量门就训练网络。

## 约定

- 治理散文在 `charter/`（只增不改的台账 `charter/decisions.md`）；富参考在 `charter/reference/`（退役只读）。
- 验收层 `tests/acceptance/` 是规格脊椎，先于 `src/` 建（建门先于建码）；门 `tests/gate.py` 做棘轮。
- 代码按**模块**：`src/support_accessibility/{oracle,data,eval,models,viz}`，不按阶段号前缀。
- 研发方法在 `method/`；产物进 `runs/`（DVC，按 E0–E8 + run-id，机器 emit）。
- 阶段/实验号（阶段0–10、E0–E8）是**逻辑标签**，用于 decisions / 提交信息 / run 清单，**不作文件名前缀**。
