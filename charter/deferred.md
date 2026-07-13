# deferred — 未决决策（触发册）

<!-- 未决决策 = 前置条件(触发) → 义务。无日期，按阶段门排序（早→晚）。是 decisions.md 的"未决半"。
     由 tests/acceptance/test_deferred.py 接进 gate：每条 surfaced 为门项、指回本册 id（人肉提醒→门提醒）。
     机器可判的条目（如 flagship-pair 的 import-check）附注"休眠/已触发/可闭合"。
     闭合：满足义务后 append decisions.md 记录，并把此条从本册删除。命名原则见 conventions.md §3。 -->

## flagship-pair
- 触发：进入 E1/H1 实验
- 义务：实现 src/support_accessibility/data/__init__.py::flagship_pair（现 NotImplementedError）
- 阻塞：E1（支撑面积≈但腔深不同的旗舰配对；H1 立论存在性）
- 机器可判：是（import-check：flagship_pair 是否仍 NotImplementedError）

## params-freeze
- 触发：六项趋势审核通过（标签质量门）
- 义务：append decisions 冻结 conf/params.yaml 临时数值（n_directions/voxel_res/radii/overhang）
- 阻塞：正式神经实验（铁律 #6 标签先于模型）
- 机器可判：否（趋势审核为人审；将来挂 labels_quality sentinel）

## point-touch-refine
- 触发：真实网格证据到手（ABC/Thingi10K 接入后）
- 义务：定 D-001 point-touch 是否细化（D-008 radius / D-011 scale 共同指向）
- 阻塞：无（留待证据）
- 机器可判：否

## workflow-done-DoD
- 触发：Tier-1 收尾前（指标/数据管线/真实数据接入就绪）
- 义务：达成"尺子造好、可开实验"的 DoD（定义见 D-013）：除 budget/regression 门外 gate 全绿 + conventions CI 绿 + gate.yml CI 绿。当前未达（几何/数据/指标多项 PENDING）。
- 阻塞：Tier-3 实验开工
- 机器可判：部分（gate 内除 budget/regression 外是否全 PASS 可算；数据/指标就绪需人确认）
