# governance — 治理地图

SAF 的治理入口：把「意图、决策、证据、结果」写成散文，再让每一条冻结的决策都有一个会跑的验收性质守护。原则是一个事实只有一个家、用指针而不是复制、行为的最终权威是代码和测试。

## 文件分工

| 文件 | 内容 | 强制力 |
|---|---|---|
| [问题定义](问题定义.md) | 做什么、硬约束、非目标、指标、样例 | 人和智能体阅读 |
| [铁律约束](铁律约束.md) | 不可破的铁律 | 人和智能体阅读 |
| [文献证据](文献证据.md) | 每条文献对本问题意味着什么、边界在哪 | 人和智能体阅读 |
| [决策台账](决策台账.md) | 已冻结的判定语义与口径，只增不改实质 | `test_governance` 机检格式与覆盖 |
| [结果账本](结果账本.md) | 假设 → 指标 → 数值 → 样本 → 复现命令，权威数字的唯一出处 | 复现脚本背书 |
| [研发路线](研发路线.md) | 研发阶段的划分、每阶段的产出位置与后续方向，不手写门状态 | `test_governance` 检查无手写状态 |
| [工程规范](工程规范.md) | 代码、测试、产物、文档和命名规范 | `tools/check_structure.py` |

现状（哪些门绿、哪些待办）不手写，一律运行 `python tests/gate.py --format md` 看。

## 决策与验收性质的对应

每条决策都有会跑的性质守护它；改一条决策，就要同步改对应性质。完整性由 `test_governance.py::check_decisions_covered` 保证：每条 `D-0NN` 必须被验收层引用，或属于结构性决策。

| 决策 | 守护性质（`tests/acceptance/`） |
|---|---|
| D-001 语义 C（盲腔判例） | `test_known_answers`（盲腔不可达）、`test_mesh_frontend`（两盒窄隙） |
| D-002 基板不建模 / 下半球 | `test_known_answers`（开阔下朝面可达）、`test_mesh_frontend`（盒下朝面） |
| D-003 体素腐蚀口径 + 边界带精确胶囊细化 | `test_differential`（体素 == 暴力参考）、`test_capsule`（精确原语与三态判定） |
| D-005 球模型 / 方向灵活 | 判据由 `test_known_answers`、`test_capsule` 间接守护；旋转 / 尺度等变已判 N/A（D-008、D-011、D-027） |
| D-007 环境 | `test_env` |
| D-008 半径单调证伪 | `test_properties::test_radius_monotonic`（跳过，不作不变量） |
| D-009 网格前端口径 | `test_mesh_frontend`（solidify IoU；numpy 堆叠） |
| D-010 支撑接触区提取 | `test_support_contact` |
| D-011 尺度不变证伪 | `test_properties::test_scale_invariance`（跳过） |
| D-016 数据架构 | `test_dataset`（round-trip、两类俱在、按模型切分、标签 == oracle、manifest 良构） |
| D-017 Fusion360 主数据源 | `test_fusion360`（OBJ 解析、final 过滤、端到端物化） |
| D-019 研发路线不手写状态 | `test_governance`（`check_roadmap`） |
| D-020 边界带精确细化 | `test_capsule` |
| D-022 野网格加固与 Thingi 采样上限 | `test_capsule`（逐比特等价、退化三角）、`test_thingi`（确定性无偏子采样） |
| D-024 方向级可达性场 | `test_direction_field`（逐方向判定、any 归约不变量、模型方向头） |
| D-028 网格前端加固 | `test_mesh_frontend`（缠绕安全外移三态、栅格维度） |
| D-025 标签审核客观化 | `experiments/label_audit.py` 与 `test_differential`、`test_capsule`、`test_label_quality` |
| D-026 预算门与回归门 | `gate.py::budget_gate`；`gate.py::regression_gate` 读 `experiments/regression_check.py` 的产出 |
| D-033 布局与路径策略 | `test_governance`（`check_repository_structure`） |
| 指标实现 | `test_eval`（已知答案锚定） |
| 程序化已知答案件 | `test_procedural_cases`（含旗舰配对：同支撑面积、可达性相反） |
| 跨模型预测可行性 | `test_model` |
| 工具尺寸效应 / 基线对照 | `test_baselines` |
| 跨域鲁棒性跨域（Thingi10K） | `test_thingi` |
| 标签质量门（六项趋势） | `test_label_quality` 与 `test_known_answers`、`test_differential`、`test_support_contact`、`test_procedural_cases` |

无 `tests/acceptance/` 专属性质，由实验脚本、门或结构检查守护的决策：D-000、D-004、D-006、D-012、D-013、D-014、D-015、D-018、D-021、D-023、D-025、D-026、D-027、D-029、D-030、D-031、D-032。

## 工程门与论文门

| 门 | 命令 | 检查范围 |
|---|---|---|
| 工程门 | `python tests/gate.py`、`python -m pytest tests -q` | 工程代码、合成几何、治理和单元回归；不要求外部数据 |
| 论文门 | `python -m paper.pipeline.paper_gate` | 另外要求处理后数据与原始网格、机器证据清单、源稿审计（图件、引用、数值与证据一致）和论文 PDF；缺任一项都明确失败 |

## 修改触发

| 改什么 | 必须同步 |
|---|---|
| 判定语义 / 口径（D-001/002/003/005） | 在决策台账新增 supersede 条目（不改旧条目）、改对应验收性质、重生受影响标签 |
| 铁律 | 铁律约束（极少发生） |
| 连续数值（方向数、半径、分辨率、阈值） | `configs/oracle_params.yaml`；标签审核通过后在决策台账另立条目冻结 |
| 某个性质变红 | 先判断是代码错（改代码，性质不动）还是决策错（新增 supersede 并改性质）；已绿的不许静默退绿 |
