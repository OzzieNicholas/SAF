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

> 环境：conda env `sfa`（`../environment.yml`，py3.12 + igl/numpy/scipy/trimesh），由 `test_env.py` 的 `env_ready` 门守护；跑 `conda run -n sfa python ../tests/gate.py`。

## 阅读顺序

1. `problem.md` — 做什么、硬约束、非目标、指标、样例
2. `constraints.md` — 不可破的铁律
3. `decisions.md` — 冻结的判定语义与口径（D-000..）
4. `evidence.md` — 文献证据（来源↔问题）；富矩阵在 `reference/2_文献矩阵与相关工作.md`
5. `reference/` — 退役的富文档（问题/文献/实验/执行路线全本），只读参考

## 决策 ↔ 性质 映射（棘轮门守护）

每条冻结决策都有一条会跑的验收性质守护它；改一条决策 → 改对应性质（见"修改触发"）。

| 决策 | 验收性质（`../tests/acceptance/`）| 现状 |
|---|---|---|
| D-001 语义C（盲腔判例）| `test_known_answers.py::test_blind_cavity_inaccessible` | PENDING（待 oracle）|
| D-002 基板不建模/下半球 | `test_known_answers.py::test_open_downface_accessible` | PENDING |
| D-003 体素腐蚀口径 | `test_properties.py::test_radius_monotonic` `::test_direction_monotonic` · `test_differential.py::test_voxel_matches_bruteforce` | PENDING |
| D-005 球模型/方向灵活 | `test_properties.py::test_rotation_equivariance` `::test_scale_invariance` | PENDING |
| （治理自检）| `test_charter.py`（schema / 参考在位 / 无残留 / params 键）| **GREEN** |
| （环境自检）| `test_env.py`（env_ready：igl/numpy/scipy/trimesh + py≥3.12）| **GREEN**（sfa 内）|

跑门：`python ../tests/gate.py` → JSON 裁决 + 退出码。当前 **RED**（几何未实现），但 `test_charter` 已 **GREEN**——治理散文这层当场就有牙。

## 修改触发（改什么必须同步什么）

- 改判定语义/口径（D-001/002/003/005）→ 新增 `decisions.md` 条目 supersede（**不改旧条目**）+ 改对应验收性质 + 重生受影响标签。
- 改铁律 → `constraints.md`（极少）。
- 改连续数值（方向数/半径/分辨率/阈值）→ `../conf/params.yaml`；标签质量审核通过后立新 decisions 冻结。
- 性质变红 → 决策树：**代码错**（改码，性质不动）/ **决策错**（append supersede + 改性质）。绿了不许静默退绿。
