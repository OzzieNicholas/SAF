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

## abc-subset-ingest
- 触发：真实 ABC 子集放入并配置路径（现仅 3 薄板样例，非真数据集）
- 义务：ABC mesh→occupancy 接入（mesh_to_occupancy）+ 合格性筛选（docs §4.8：水密-合并后/非退化厚度/有悬垂/有封闭凹腔/面数预算/可归一）+ 真实网格 oracle 有效性门（连 point-touch-refine）；产出统一 processed 记录（对齐 D-016 格式，source=abc）
- 阻塞：ABC 作主训练/验证/测试源（H3 跨模型）
- 机器可判：部分（ABC 路径存在性可判；标签有效性需人审 + 门）

## thingi-ingest
- 触发：进入跨域鲁棒性阶段（E7）
- 义务：Thingi10K mesh 接入 + 缠绕/法向修复（overhang.py 现假设外向一致）+ 鲁棒性门；恒 split=test、绝不进训练（docs §4.6）；对齐 D-016 格式，source=thingi10k
- 阻塞：ABC→Thingi 跨域鲁棒性实验（H5）
- 机器可判：否（网格质量与标签稳定性需人审）

## dvc-pipeline
- 触发：首个昂贵/真实数据源物化（ABC 子集接入）
- 义务：引入 DVC（dvc 入 environment.yml + dvc.yaml 包裹流水线阶段 + CI 接线），把 build 变 dvc repro；把 data/processed/ 交 DVC 追踪
- 阻塞：大产物版本化与一键复现
- 机器可判：是（dvc.yaml 存在性）

## local-blas-gate-crash
- 触发：已到（本地 Windows saf 环境 numpy 2D×2D 矩阵乘崩 0xC06D007F，BLAS DLL 加载失败，与 D-009 的 trimesh 0xC06D 同类；faulthandler 定位 models/__init__.py:86 的 MLP X@W1）
- 义务：定版/重装 numpy+openblas 使本地 gate/pytest 可全跑（现只 CI-linux 全绿，本地崩在 test_model/test_baselines）
- 阻塞：本地完整验收（几何/数据片不受影响——无矩阵乘）
- 机器可判：部分（本地 gemm 是否崩可探；修复需环境操作）
