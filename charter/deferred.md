# deferred — 未决决策（触发册）

<!-- 未决决策 = 前置条件(触发) → 义务。无日期，按阶段门排序（早→晚）。是 decisions.md 的"未决半"。
     由 tests/acceptance/test_deferred.py 接进 gate：每条 surfaced 为门项、指回本册 id（人肉提醒→门提醒）。
     机器可判的条目（如 flagship-pair 的 import-check）附注"休眠/已触发/可闭合"。
     闭合：满足义务后 append decisions.md 记录，并把此条从本册删除。命名原则见 conventions.md §3。 -->

## flagship-pair（已实现 + E1/H1 存在性验证）
- 触发：E1/H1 实验——已到并完成
- 已达：`data.flagship_pair` 落地（不再 NotImplementedError）：开阔悬空 ledge vs 深窄槽腔顶，两件**支撑面积严格相等**（各 64 下朝接触点）、**可达性相反**（100% vs 0%）→ 证「支撑面积 ⊥ 可达性」，补 H1 统计 ρ≈0 的存在性证据。守护性质 `test_data`（flagship_pair_area_perp_access + pytest）。
- 机器可判：是（import 非 NotImplementedError + 面积相等/可达相反可判）

## point-touch-refine
- 触发：真实网格证据到手（Fusion360 接入后，已到）
- 义务：定 D-001 point-touch 是否细化（D-008 radius / D-011 scale 共同指向）。**进展**：res/scale 那半（D-011 指向）已由 D-020（D-003 精确胶囊-网格细化）解决——真实 CAD 标签 res-稳定（48/96/192 一致 1.000），无需改 D-001 语义；D-008 radius / point-touch 工具模型那半仍开，但真实标签已几何正确、优先级低
- 阻塞：无（留待证据）
- 机器可判：否

## workflow-done-DoD
- 触发：Tier-1 收尾前（指标/数据管线/真实数据接入就绪）
- 义务：达成"尺子造好、可开实验"的 DoD（定义见 D-013）：除 budget/regression 门外 gate 全绿 + conventions CI 绿 + gate.yml CI 绿。当前未达（几何/数据/指标多项 PENDING）。
- 阻塞：Tier-3 实验开工
- 机器可判：部分（gate 内除 budget/regression 外是否全 PASS 可算；数据/指标就绪需人确认）

## fusion360-ingest
- 触发：Fusion 360 Gallery reconstruction 数据集放入并配置路径（conf/params.yaml data.fusion360_root）
- 义务：iter_final_designs（走目录取有同名 .json 兄弟的 final .obj；.json 仅作存在标记、不解析——D-017）+ _meshes_from_root/load_obj + normalize（最长边=1）+ 合格性筛选（docs §4.8：水密-合并后/非退化厚度/有悬垂/有封闭凹腔/面数预算/可归一）+ **真实网格 oracle 有效性门（人签收，D-018；连 point-touch-refine）**；产出统一 processed 记录（对齐 D-016 格式，source=fusion360）。骨架码已落 + 1000 件已物化（探索级 n_dir=32）；未决 = 按冻结参（n_dir=128 / 细化开，D-020）重采训练级标签 + 人签收。
- 阻塞：Fusion360 作主训练/验证/测试源（H3 跨模型）
- 机器可判：部分（路径存在性 + ingest round-trip 可判；标签有效性需人签收）
- 备注：ABC 经 D-023 彻底弃用（D-017 曾退为可选/背景）；数据源定为三——Fusion360/Thingi10K/程序化，无 ABC 接入项。

## thingi-ingest（接入 + H5 完成，见 D-022；残留仅可选人审）
- 触发：跨域鲁棒性阶段（H5）——已完成
- 已达：`data/thingi.py` 落地（STL bin/ascii 解析 + 下朝面用 **stored 法向** + occ igl winding，稳健非流形；恒 split=test、绝不进训练 docs §4.6；D-016 source=thingi10k，`test_thingi` 接门）。**300 件物化**（149 both-class / agg 不可达 19.4%）；**H5 跨域评测完成**：域内留出 F1 0.915±0.005 vs 跨域 Thingi 0.908±0.005（掉幅 0.006、噪声内），胜几何基线 0.725（见 D-022）。野网格加固（precompute + 退化三角跳过，D-022）令 D-020 细化在 Thingi 上可跑不崩。
- 残留（可选、非命门）：Thingi 标签质量人眼审（非水密件 winding 不稳→标签噪声）——**因 Thingi 恒 test、绝不进训练，铁律 #7 命门签收不适用**；H5 已在含噪 OOD 标签下得 0.908，噪声属跨域挑战本身。审计图仪器 `viz.audit_model` 可复用。
- 机器可判：是（STL 解析 + ingest round-trip + H5 F1 可判；标签噪声属已知特性）

## dvc-pipeline
- 触发：首个昂贵/真实数据源物化——已到（Fusion360 全量 8625 + Thingi10K 300 物化；原写 ABC，D-023 已弃用）
- 义务：引入 DVC（dvc 入 environment.yml + dvc.yaml 包裹流水线阶段 + CI 接线），把 build 变 dvc repro；把 data/processed/ 交 DVC 追踪
- 阻塞：大产物版本化与一键复现
- 机器可判：是（dvc.yaml 存在性）

## local-blas-gate-crash（已诊断：启动/激活问题，非 numpy 缺陷 → 降级为已知跑法项）
- 触发：已到，且**根因查明**（2026-07）：0xC06D007F（bash 退出码 127 = 低字节 &0xFF）**只在直接裸调 `python.exe` 绝对路径**（未激活 env）时发生——OpenBLAS 的 2D×2D **gemm** 延迟加载其线程 DLL，而 env 的 `Library\bin` 不在 DLL 搜索路径 → 延迟加载失败崩；gemv(2D×1D) 时好时坏故显"间歇"。**numpy 本身没坏**（壳内激活下 gemm/igl/scipy/torch 全绿）。原记"重装 numpy"系误诊。
- 义务（已满足→降级）：用**壳内激活**稳定跑，勿裸调 python.exe，勿并发两个 `conda run`（并发会崩其插件层）：`source "D:/Miniforge/Install/etc/profile.d/conda.sh" && conda activate saf && python …`。此法下 gate/pytest 可稳定全跑（实测 50 passed / 5 skipped）。跑法备忘 memory/saf-env-launch.md。
- 阻塞：无（有稳定跑法）；残留 gotcha = 裸调 python.exe 仍崩 gemm（launch-hygiene，非代码缺陷）
- 机器可判：是（壳内激活下 gate 稳定全绿可验）
