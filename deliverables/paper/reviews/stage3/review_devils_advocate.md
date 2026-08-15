# Stage 3 Devil's Advocate Review

## Manuscript Information

- **Title:** 金属增材制造支撑接触区的有限工具几何可达性评价与形状条件神经预测
- **Manuscript ID:** anonymous
- **Review date:** 2026-08-15
- **Review round:** Round 1 / Stage 3
- **Reviewer identity:** 对计算制造学习系统持怀疑态度的资深几何算法研究者，专门检验核心论证、替代解释、标签—预测闭环中的循环性和结论外推。
- **Overall recommendation:** Major Revision
- **Confidence:** 5/5 — core expertise: computational geometry and learned surrogates

## Genuine Strengths

### S1: 作者主动把真实工艺效用与代理拟合分开

文稿多次否认生产认证、连续路径和方向优化，这使核心反驳可以集中于证据是否足以支持“有用代理”，而不是先纠正明显的工艺越界。

**Evidence Anchor:** `text: §6 "不是生产放行或工艺认证结论"`

### S2: 失效不是被平均值完全隐藏

边界方向数分箱、代表性误差面和差分 mismatch 均有披露，说明作者没有只保留成功案例。

**Evidence Anchor:** `figure: Fig. 10 — error concentration near low-viable-direction regions`

### S3: 近邻工作没有被虚假贬低

DeepMill、PARC 和 IMF 的已有能力被承认，论文没有使用“首次”或“唯一”等无法支持的首创语言。

**Evidence Anchor:** `text: §2.3 "本文不把神经可达性学习表述为最早工作"`

## Strongest Counter-Argument

对本文最强的反驳是：SAF 目前证明的是“一个轻量网络可以拟合作者自己定义并生成的离散几何标签”，而不是“该标签是 AM 支撑后处理风险中不可替代、对实际决策有效的表示”。有限球、固定半径、固定 +z 构建方向和 64 个离散槽位共同定义了标签；网络只接收占据栅格和查询坐标，因此性能高可能主要说明 Fusion 数据中的局部占据与绝对位置足以预测这个冻结 oracle。射线基线较弱并不能排除更合理的距离场、局部净空、可见锥或多尺度几何基线；“no shape”与几个网络变体也不是对成熟几何算法的充分替代。跨域 F1 近似甚至可能来自经过双类筛选的 Thingi10K 子集更易于当前标签，而不是模型获得了通用后处理知识。方向 Top-1 只在存在可达方向的点上报告，若大多数此类点有很多可达方向，0.957 可能由基率驱动。最后，所谓五折实际上是五次随机留出，削弱了 headline 的统计描述。即使所有 F1 都完全复现，论文最多仍证明了一个特定代理上的 surrogate fidelity；除非增加独立几何/CAM/专家验证、强几何基线和条件敏感性，不能据此推出该代理会改善真实 DfAM 设计决策。

## Issue List

### CRITICAL

| # | Dimension | Issue Description | Evidence Anchor | Confidence | Field-Norm Boundary | Evidence-Crossing Rationale |
|---|---|---|---|---|---|---|
| — | — | 未发现单项足以独立否定全部核心结果的致命缺陷；现有问题可通过重分析、收窄和补充验证修复。 | `text: §6 "几何风险的下界代理"` | 5 — severity calibration | — | — |

### MAJOR

| # | Dimension | Issue Description | Evidence Anchor | Confidence | Field-Norm Boundary | Evidence-Crossing Rationale |
|---|---|---|---|---|---|---|
| M1 | Core thesis | 训练与测试共享同一作者定义的代理标签；F1 证明 surrogate fidelity，不证明 AM 后处理效用。需要独立 CAM/连续几何/专家或真实支撑接触对照，或将核心结论严格改为“拟合该代理”。 | `absence: §5 Experiments — expected independent task-validity reference; checked H1--H5, E5, E8 and failure audit` | 5 — core expertise: surrogate validation | — | — |
| M2 | Alternative paths | 基线没有覆盖距离场、可见锥、多尺度局部净空或直接胶囊近似等更接近 oracle 的强几何方法；射线基线弱不能证明神经网络必要。 | `table: Table 5 — majority, local rule, ray, tiny local and ConvONet comparison` | 5 — core expertise: geometric baselines | — | — |
| M3 | Scope consistency | 网络不接收工具半径、构建方向或方向向量，却以“有限工具可达性预测”呈现；实际只适用于一个冻结配置，程序化与 Fusion 训练样本的体素半径还不同。 | `equation: Eq. (6) — only occupancy feature and query coordinate enter q_theta` | 5 — core expertise: conditional models | — | — |
| M4 | Evaluation validity | headline 被称为五折交叉验证，实际为五次 60/20/20 随机留出；固定前 400 件子集又承担基线、消融和回归，可能产生选择依赖。 | `text: §5.3 "5 折零件级交叉验证"` | 5 — core expertise: evaluation design | — | — |
| M5 | Directional claim | Top-1=0.957 只在至少一个方向可达的点上统计，却缺少 eligible 点数、可达方向数分布和随机/先验排序基线；方向贡献可能被容易点的基率夸大。 | `table: Table 6 — Top-1 / Top-3 without denominator or ranking baseline` | 5 — core expertise: ranking evaluation | — | — |
| M6 | Domain validity | “支撑接触区”实为 45° 下朝面代理，未生成真实支撑或接触；若不新增对照，题目和全文应统一改成“潜在接触区代理”。 | `equation: Eq. (1) — downward-facing samples define the support-contact proxy` | 4 — adjacent expertise: DfAM geometry | — | — |

### MINOR

| # | Dimension | Issue Description | Evidence Anchor | Confidence |
|---|---|---|---|---|
| m1 | Evidence selection | H2 的 Fusion 4.86% 来自 600 件样本，但摘要未写样本范围，容易被误读为全部 8,590 件统计。 | `text: §5.2 "Fusion 的 600 件样本中有 4.86%"` | 5 — evidence-scope audit |
| m2 | Runtime claim | 112 倍只比较当前实现的单点时间；需要端到端和 batch 口径，或进一步弱化为量级观察。 | `text: §5.5 "逐点几何判定平均为 3.97 ms"` | 5 — performance benchmarking |
| m3 | Label certainty | 0.63% 差分审核样本只有 160 点，97.28% 跨分辨率只有 10 件；应加入 10,000 seed 差分审计且不再称整个 oracle“精确”。 | `table: Table 4 — audit sample sizes` | 5 — geometric validation |
| m4 | Reproducibility | H5 capture 与 E5 legacy artifact 不具备与主要基线相同的统一运行 envelope。 | `dataset: integrity_report.md — EXP-H5 and EXP-E5 provenance notes` | 5 — reproducibility audit |

## Ignored Alternative Explanations / Paths

1. **局部距离与绝对坐标捷径：** 三层同分辨率卷积的感受野有限，模型可能主要学习查询点邻域和归一坐标，而非全局遮挡；应报告感受野并加入强局部距离场基线。
2. **双类筛选改变难度：** 主任务只在 1,553 件双类零件上训练/测试，可能对全可达件部署产生不同误报结构；应同时报告全量分布。
3. **跨域子集更容易：** Thingi10K 固定双类子集的不可达率与几何分布不同，F1 接近不等于 representation 域不变；应做分层匹配或按难度校正。
4. **方向基率解释：** 可达方向多的点上任取方向就容易命中，0.957 需要与随机、全局方向先验和可见性排序比较。

## Missing Stakeholder Perspectives

- CAD/CAM 软件工程师需要知道输入网格失败状态、端到端延迟和接口契约。
- AM 后处理工程师需要看到完整工具、夹具、支撑去除顺序和至少一个独立碰撞对照。
- 设计工程师需要明确概率热图触发何种人工复核，而不是只看到颜色和箭头。

## Unexamined Premise

全文隐含一个前提：只要一个代理与支撑量不同、且可由网络高 F1 预测，它就值得成为 DfAM 设计信号。这个前提尚未被直接验证。真正需要检验的是 SAF 是否改善了某个外部决策，例如更准确地排序专家认定的难清理区域、减少 CAM 碰撞检查数量，或在固定复核预算下提高风险召回。没有这一层时，SAF 的几何自洽性成立，但“为什么设计流程需要它”仍是推论。

## “So What?” Verdict

如果作者把论文收窄为“潜在接触区的有限工具几何代理及其可复现 surrogate benchmark”，它具有明确的专业价值：提供公开对象定义、审计标签和方向级失败分析。如果坚持把它写成已验证的后处理风险方法，则当前证据不足。最可能提高投稿成功率的路线不是增加更大的网络，而是补一个独立有效性锚点、一个强几何基线、一个真实的五折/重复留出说明以及条件敏感性。

## Questions for Authors

1. 除了与自身 oracle 一致外，作者希望 SAF 对哪个外部决策产生可测量改进？
2. 是否存在一个不训练网络的距离场/可见锥基线，能够在相似速度下接近 0.886？
3. eligible 方向点平均有多少个可达方向，随机 Top-1 期望是多少？
4. 若工具半径从 0.05 改为 0.02，现有模型输出还有何含义？

## Observations (Non-Defects)

- 没有物理实验并非自动致命，因为论文可以合法定位为计算几何代理；问题在于应用结论必须与这一定位完全对齐。
- 方向场比点级 F1 更可能形成后续独立价值，但需要基率透明和连续/完整工具边界。
- 当前稿件的诚实局限说明是修订的基础，建议保留而不是为了显得“更强”而删减。

