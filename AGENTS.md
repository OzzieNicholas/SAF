# AGENTS.md

<!-- 稳定的项目级 Agent 入口。领域约束与机械检查以 governance/ 和 tests/ 为准。 -->

## 项目

SAF (Support Accessibility Field)：金属增材制造**支撑接触区**表面的几何可达性代理评价与**形状条件神经预测**。几何/AI 题，DfAM 前端，非材料/工艺实验。治理入口见 `governance/README.md`；判定语义与冻结决定见 `governance/decisions.md`。

## 技术栈 / 环境

- Python；几何：trimesh / Open3D / libigl（generalized winding number 判内外）/ numpy / scipy（距离变换）。
- 神经：PyTorch；可选 tiny-cuda-nn / Kaolin / PyTorch3D。
- 实验：工程 CLI + 外部数据路径解析（tools/data_paths.py）+ Hydra 口径登记（configs/params.yaml）。
- 硬件上限：单卡 RTX 4060 / 32G，模型与数据规模据此控制。
- **环境**：conda env `saf`（py3.12，conda-forge）；建/复现 `conda env create -f environment.yml`；由 `tests/acceptance/test_env.py` 的 `env_ready` 门守护（环境不对当场红）。

## 完成的定义（Definition of Done）

- 验收门通过：`python tests/gate.py` 绿
- 所有测试为绿；指标不劣于基线（回归门）

## 怎么跑

- 验收门：`conda run -n saf python tests/gate.py`（现 **GREEN**：工程 DoD 达成，D-027；工程门不访问外部数据，状态跑门 `--format md` 看；论文专属外部门用 `--paper` 显式启用）
- 测试：`conda run -n saf python -m pytest -q`
- 造数据集：conda run -n saf python tools/build_dataset.py --dataset procedural_v1（输出到 E:/Work/Data/Temporary/SAF/<dataset>/<run>）
- 复现数据：使用 tools/data_paths.py 与各 CLI 的 --data-root/--out，不在 SAF 仓库内保存数据
- 实验 CLI（tools/）：`train_convonet`(H3) · `eval_h5`(H5) · `eval_e5`(E5) · `failure_cases` · `audit_labels`(标签审核 D-025) · `regression_check`(回归门 D-026) · `eval_baselines`(表5 基线汇总) · `eval_true_area`(H1 真面积对照)
- **非交互/agent 兜底跑法**：壳内激活最稳——`source "D:/Miniforge/Install/etc/profile.d/conda.sh" && conda activate saf && python …`；**勿裸调 python.exe 绝对路径**（未激活 → OpenBLAS gemm 延迟加载崩 0xC06D007F），勿并发两个 `conda run`（本条即完整跑法备忘）。

## 绝不能碰

- 企业边界、oracle 判定口径私改（见 `governance/constraints.md`）。
- 把方向评价写成方向优化；声称方法首创；把哈希当主创新。
- oracle/标签未过质量门就训练网络。

## 约定

- 治理散文在 `governance/`（实质不可改、修辞可策展的台账 `governance/decisions.md`，政策见 D-014）；富参考在 `docs/`（退役只读）。
- 验收层 `tests/acceptance/` 是工程规格脊椎，`tests/unit/` 覆盖工程单元回归，`tests/paper/` 覆盖论文包契约；门 `tests/gate.py` 做工程棘轮。
- 代码按**模块**：`src/support_accessibility/{oracle,data,eval,models,baselines,viz}`，不按阶段号前缀。
- SAF 治理自包含在 governance/；运行状态由工程门 tests/gate.py 和论文门 deliverables/paper/pipeline/paper_gate.py 生成。外部数据在 E:/Work/Data，论文证据在 deliverables/paper/evidence/；原始 run 和缓存进 artifacts/runs/ 与 artifacts/cache/（均不入 Git）。
- 阶段/实验号（阶段0–10、E0–E8）是**逻辑标签**，用于 decisions / 提交信息 / run 清单，**不作文件名前缀**。
