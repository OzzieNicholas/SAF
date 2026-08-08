# deferred — 未决决策（触发册）

<!-- 未决决策 = 前置条件(触发) → 义务。无日期，按阶段门排序（早→晚）。是 decisions.md 的"未决半"。
     由 tests/acceptance/test_deferred.py 接进 gate：每条 surfaced 为门项、指回本册 id（人肉提醒→门提醒）。
     闭合：满足义务后 append decisions.md 记录，并把此条从本册删除。命名原则见 conventions.md §3。
     空册 = 无开放未决义务（终态，gate 记 deferred_register=PASS）。新义务出现时在此追加 `## <id>` 条目。 -->

**当前无开放未决义务** —— 历次未决项均已闭合，闭合记录见 `decisions.md`：

- `flagship-pair` → 实现 `data.flagship_pair`（E1/H1 面积⊥可达存在性），守护 `test_data`。
- `point-touch-refine` → res/scale 半由 **D-020** 精确细化解决（真实标签 res-稳定）；D-008 radius/工具模型半判定为**非不变量**（终态，见 D-008 + test_properties N/A），真实标签几何正确。
- `workflow-done-DoD` → DoD 达成，见 **D-027**（终态定义 + 门达 GREEN）。
- `fusion360-ingest` → 8625 设计 / 成功物化 8590 件 + 标签有效性**量化审核**（**D-025**：差分 robust 0.25%/res-稳定 97.7%/分布），假绿已修。
- `thingi-ingest` → Thingi10K 接入 + H5 跨域（**D-022**：OOD F1 0.908，掉幅 0.006）。
- `dvc-pipeline` → `dvc init` + `dvc.yaml`（procedural 阶段 `dvc repro` 字节一致）+ `dvc` 入 environment.yml。剩为**文档化限制**（Fusion/Thingi 外部只读原料不在可复现 DAG）+ 可选 CI 接线，非开放义务。
- `dvc-pipeline` 数据源 = 三源（Fusion360/Thingi10K/程序化），ABC 经 **D-023** 彻底弃用。
- `local-blas-gate-crash` → 诊断为启动/激活问题（非 numpy 缺陷），稳定跑法见 `AGENTS.md`「怎么跑」。
