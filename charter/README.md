# charter — 治理地图（索引）

> SAF (Support Accessibility Field) 的统一治理入口：散文（意图/决策/证据/铁律）+ 一张地图。
> 承袭 ffm_mesh_common 的原则：一个事实一个家、指针不复制、行为终极权威=代码+测试、每个集合有索引。

## 三层强度 + 过程（弱→强）

| 层 | 内容 | 位置 | 强制力 |
|---|---|---|---|
| 意图 | 问题定义 / 铁律 / 证据 | `problem.md` `constraints.md` `evidence.md` | 人和智能体读（最弱）|
| 台账 | 决策 + 状态（只增不改）| `decisions.md` | 记录 + `test_charter.py` 机检 |
| 可执行 | 必须恒真的性质、门 | `../tests/acceptance/` `../tests/gate.py` `../src/support_accessibility/` | 跑起来会红（最强）|
| 过程 | 研发方法 / loop 约定 | `../method/` | 运行时循环门 |

> 环境：conda env `saf`（`../environment.yml`，py3.12 + igl/numpy/scipy/trimesh），由 `test_env.py` 的 `env_ready` 门守护；跑 `conda run -n saf python ../tests/gate.py`。

## 阅读顺序

1. `problem.md` — 做什么、硬约束、非目标、指标、样例
2. `constraints.md` — 不可破的铁律
3. `decisions.md` — 冻结的判定语义与口径（D-000..）
4. `evidence.md` — 文献证据（来源↔问题）；富矩阵在 `docs/2_文献矩阵与相关工作.md`
5. `docs/` — 退役的富文档（问题/文献/实验/执行路线全本），只读参考

## 决策 ↔ 性质 映射（棘轮门守护）

每条冻结决策都有会跑的验收性质守护它；**现状不在此手写——跑 `../tests/gate.py`（`--format md` 出 markdown STATUS）看实时裁决**。改一条决策 → 改对应性质（见"修改触发"）。完整性由 `test_charter.py::check_decisions_covered` 守护：每条 D-0NN 须被验收层引用或在结构 allowlist，杜绝孤儿。

| 决策 | 守护性质（`../tests/acceptance/`）|
|---|---|
| D-001 语义C（盲腔判例）| `test_known_answers`（盲腔不可达）+ `test_mesh_frontend`（两盒窄隙）|
| D-002 基板不建模/下半球 | `test_known_answers`（开阔下朝面可达）+ `test_mesh_frontend`（盒下朝面）|
| D-003 体素腐蚀口径 | `test_differential`（voxel==暴力参考，ε边界带）|
| D-005 球模型/方向灵活 | `test_properties`（旋转等变、尺度等变形性质）|
| D-007 环境 | `test_env`（env_ready）|
| D-008 半径单调证伪 | `test_properties::test_radius_monotonic`（skip，不作不变量）|
| D-009 网格 igl 口径 | `test_mesh_frontend`（solidify IoU；无 CSG numpy 堆叠）|
| D-010 支撑接触区 | `test_support_contact`（下朝悬垂 S(P,d)：提取/方向/阈值/端到端）|
| D-011 尺度证伪 | `test_properties::test_scale_invariance`（skip，分辨率依赖）|
| D-000/004/006/012 结构·标注·布局·治理 | 无专属性质（由 `test_charter` 守护 / 结构性 allowlist）|
| （治理自检）| `test_charter`（schema/参考/无残留/params/**完整性**）+ `test_open`（未决触发册接门）|

跑门：`python ../tests/gate.py`（`--format md` 出 markdown STATUS）→ 裁决 + 退出码。**状态一律看门、不在此手写**；棘轮：绿了不许静默退绿。

## 修改触发（改什么必须同步什么）

- 改判定语义/口径（D-001/002/003/005）→ 新增 `decisions.md` 条目 supersede（**不改旧条目**）+ 改对应验收性质 + 重生受影响标签。
- 改铁律 → `constraints.md`（极少）。
- 改连续数值（方向数/半径/分辨率/阈值）→ `../conf/params.yaml`；标签质量审核通过后立新 decisions 冻结。
- 性质变红 → 决策树：**代码错**（改码，性质不动）/ **决策错**（append supersede + 改性质）。绿了不许静默退绿。
