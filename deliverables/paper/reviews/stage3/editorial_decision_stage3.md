# Editorial Decision Package — Stage 3

**稿件：** 金属增材制造支撑接触区的有限工具几何可达性评价与形状条件神经预测  
**审稿轮次：** Stage 3 / Round 1  
**审稿面板：** Journal-Fit Reviewer（EIC）、Methodology（R1）、Domain（R2）、Perspective（R3）、Devil's Advocate（DA）  
**期刊接口：** 未冻结；Journal-Fit 以 CAD 计算制造/几何读者作为压力基准。  
**面板执行：** 单模型、五个独立角色；未启用 cross-model track，未向外部模型发送稿件。

## Part 1: Editorial Decision Letter

### Decision: Major Revision

这不是拒稿。五个角色都认为研究对象、几何代理和证据链具有可发表潜力；但 R1、R2、EIC 和 DA 分别指出了会改变主结果解释或投稿定位的 Major 问题。修订后必须重新审阅，不能只做语言润色。

### Reviewer Summary Matrix

| Dimension | Journal-Fit Reviewer | R1 Methodology | R2 Domain | R3 Perspective | DA（独立压力测试） |
|---|---|---|---|---|---|
| Overall recommendation | Major Revision | Major Revision | Major Revision | Minor Revision | Major Revision |
| Confidence | 4/5 | 5/5 | 4/5 | 4/5 | 5/5 |
| Main strength | 边界与证据链清楚 | 形式判据、切分、审计可复核 | AM 领域定位诚实 | 工作流和图表可用 | 未把代理冒充认证 |
| Main concern | 独立增量和固定条件范围 | 重复留出误称五折、指标与条件输入 | 代理不等于真实接触、方向/阈值冻结 | 缺少工程输出协议和端到端成本 | oracle 自洽不等于外部效用、强基线不足 |
| Questions | 3 | 4 | 4 | 4 | 4 |

### Weakness Sub-Claim Inventory

位置 `raised` 表示该角色明确提出，`corroborated` 表示其正文或总结明确支持，`not-mentioned` 表示未评论，不当作反对；严重度和置信度均沿用原报告。

| Sub-claim ID | 原子问题 | EIC | R1 | R2 | R3 | DA | 结论 |
|---|---|---|---|---|---|---|---|
| SC-1 | 五次随机留出被称为五折交叉验证 | corroborated / major / 4 | raised / major / 5 | not-mentioned | not-mentioned | raised / major / 5 | CONSENSUS-3；必须改称或重跑 |
| SC-2 | 网络不接收工具半径、构建方向或方向向量 | raised / major / 4 | raised / major / 5 | raised / major / 5 | corroborated / major / 4 | raised / major / 5 | CONSENSUS-4；必须收窄能力边界 |
| SC-3 | 下朝面代理不等于真实支撑接触区 | corroborated / minor / 4 | not-mentioned | raised / major / 5 | not-mentioned | raised / major / 4 | SPLIT（严重度/补救路径）；按领域证据保留并收窄 |
| SC-4 | 需要独立于自身 oracle 的任务效用锚点 | raised / major / 4 | not-mentioned | raised / major / 5 | raised / major / 4 | raised / major / 5 | CONSENSUS-4；至少增加独立几何/CAM或专家对照 |
| SC-5 | 构建方向、悬垂角和工具尺度冻结，缺少敏感性 | raised / major / 4 | raised / major / 5 | raised / major / 5 | corroborated / major / 4 | raised / major / 5 | CONSENSUS-4；至少补范围声明和一组敏感性 |
| SC-6 | 形状上下文的实际感受野有限，不能默认称全局 | not-mentioned | raised / major / 5 | not-mentioned | not-mentioned | raised / major / 5 | corroborated finding；需改解释或补消融 |
| SC-7 | headline 只给点池 F1，模型级宏平均不足 | not-mentioned | raised / major / 5 | not-mentioned | not-mentioned | raised / major / 5 | corroborated finding；补宏平均和区间 |
| SC-8 | 方向 Top-k 缺 eligible 分母、方向基率和强基线 | not-mentioned | raised / major / 5 | not-mentioned | not-mentioned | raised / major / 5 | corroborated finding；补统计分母/基线 |
| SC-9 | 网格质量、法向/闭合筛选的跨域分布不透明 | not-mentioned | not-mentioned | raised / major / 4 | raised / major / 4 | not-mentioned | corroborated finding；补输入质量清单 |
| SC-10 | 单点 112 倍不是端到端工程成本 | not-mentioned | not-mentioned | not-mentioned | raised / major / 4 | raised / minor / 5 | SPLIT（严重度）；保留为应用报告项，降为 P2 |
| SC-11 | 缺少风险等级/复核触发/非刀路使用协议 | not-mentioned | not-mentioned | not-mentioned | raised / major / 4 | corroborated via alternatives | single-reviewer + DA observation；P2 |
| SC-12 | 相对于 DeepMill/PARC 的独立贡献需要更锋利 | raised / major / 4 | not-mentioned | corroborated / minor / 4 | not-mentioned | raised / major / 5 | corroborated finding；重写 RQ/贡献 |
| SC-13 | 缺少强几何基线（距离场/可见锥等） | not-mentioned | not-mentioned | not-mentioned | not-mentioned | raised / major / 5 | single-reviewer；P2 建议，不单独阻塞 |
| SC-14 | 0.5 阈值、PR-AUC和概率校准未报告 | not-mentioned | raised / minor / 5 | not-mentioned | not-mentioned | not-mentioned | single-reviewer；P3/P2 视热图用途决定 |
| SC-15 | H5/E5 运行封装与公开复现入口不统一 | not-mentioned | raised / minor / 5 | not-mentioned | raised / minor / 4 | raised / minor / 5 | corroborated finding；补 envelope/获取说明 |
| SC-16 | “支撑接触区/代理/下朝面”术语层级需统一 | raised / minor / 4 | not-mentioned | raised / major / 5 | not-mentioned | raised / major / 4 | SPLIT（severity）；按 R2 领域语义执行收窄 |

### Consensus and Arbitration

#### Points of Agreement

- **[CONSENSUS-4 / SC-2]** 目前网络是固定代理配置下的形状条件分类器，不是可直接换半径、构建方向或方向集的通用工具条件模型。所有角色的意见和 Eq. (6) 证据一致。编辑裁决：正文、摘要、图注必须显式收窄；若新增条件化实验则可恢复更宽表述，但不是本轮必须假设已完成。
- **[CONSENSUS-4 / SC-4]** 仅用同一 oracle 生成标签再测网络，不能单独证明真实后处理效用。编辑裁决：必须加入一个独立几何/CAM/专家案例层，或把论文的核心结论明确改为 surrogate fidelity，并把外部效用列为未验证假设；不能用“代理”一词静默替代验证。
- **[CONSENSUS-4 / SC-5]** 构建方向、阈值和半径冻结对外推构成边界。编辑裁决：至少增加敏感性/条件范围说明，禁止把固定设置写成一般 AM 结论。
- **[CONSENSUS-3 / SC-1]** R1、DA 明确指出，EIC 在结果评论中也要求区分重复留出和真正 K 折。编辑裁决：当前数据不应继续称“五折交叉验证”；若不重跑，统一称“五次重复模型级随机留出”。

#### Points of Disagreement and Arbitration

- **SC-3 / SC-16 代理名称和严重度：** R2/DA 认为“支撑接触区”会让 AM 读者误解为真实支撑—零件界面；EIC 认为这是可通过定位修复的 Minor。编辑采纳 R2 的领域证据，但不要求在没有数据时虚构真实接触：统一改为“潜在支撑接触区代理/下朝悬垂面代理”，并在摘要、公式、表 1、图注和结论同步。若增加真实支撑对照，才可恢复较短术语。
- **SC-10 速度严重度：** R3 将端到端缺失视为 Major，DA 将其视为 Minor。两者并不冲突于事实，只冲突于对应用影响的评级。编辑认为它不改变核心几何/预测结论，降为 P2；必须拆分预处理、单点查询、批量查询和硬件同步，不能用 112 倍作为普遍加速承诺。
- **SC-6 感受野：** R1/DA 的技术担忧成立，但它不等于网络无效。编辑要求改写为“局部至中程占据上下文”，给出感受野计算和消融解释；新增全局分支作为可选增强，不把它设为阻塞条件。
- **SC-13 强几何基线：** 只有 DA 明确要求，但它直接关系“神经网络是否必要”。编辑将其列为 P2：至少实现一个距离场/可见锥或多尺度局部净空基线；若无法重跑，必须在讨论中承认当前基线阶梯未覆盖该类替代路径。

### Decision Rationale

稿件已经拥有一个清楚的几何对象、可复核的标签链路、公开数据和多层图表证据，因此不适合拒稿。与此同时，主结果的实验设计命名错误、模型固定条件与标题/摘要的宽泛措辞不一致，以及缺少独立外部效用锚点，都会让读者高估结论范围。四位非 DA 角色中，EIC、R1 和 R2 给出 Major Revision，R3 给出 Minor Revision；DA 的主要反驳与 R1/R2 的关键部分相互 corroborate。编辑没有把所有“没有物理实验”的意见机械升级为致命要求，因为稿件可以合法定位为计算几何代理；但代理必须在术语和证据上保持诚实，并至少通过独立几何/CAM/专家层验证其不只是自洽标签。修订需要重写研究问题、主实验统计解释、条件范围和应用协议，且应升级运行封装与关键表格。由此决定为 Major Revision，并要求 Stage 3' re-review。修订目标不是把 F1 数字做得更大，而是让每个数字、每个图和每个结论都只承担它实际能证明的内容。

### Top Blocking Issues

| Rank | Blocking issue | Source reviewer(s) | Evidence anchor | Resolving roadmap item |
|---:|---|---|---|---|
| 1 | 主试验“5 折交叉验证”命名与实际重复随机留出不一致 | R1, EIC, DA | `text: §5.3 "5 折零件级交叉验证"` | R1 |
| 2 | 模型固定工具/方向配置，却使用较一般的有限工具可达性表述 | EIC, R1, R2, DA | `equation: Eq. (6) — q_theta only takes occupancy feature and p` | R2 |
| 3 | 网络高 F1 尚未由独立于自身 oracle 的任务效用证据支撑 | EIC, R2, R3, DA | `absence: §5 — expected independent geometric/CAM/expert validity layer; checked H1--H5 and E5` | R3 |

## Part 2: Revision Roadmap

### Required Revisions (Must Fix)

| # | Revision item | Sub-claim(s) | Severity | Evidence anchor | Confidence | Source | Priority | Estimated effort |
|---:|---|---|---|---|---:|---|---|---|
| R1 | 将主试验从“5 折交叉验证”改为“五次重复模型级随机留出”，明确每次 60/20/20、测试集可能重叠、seed 与重复的关系；若改跑真正 K 折，则同步更新所有运行产物和区间。 | SC-1 | major | `text: §5.3 "5 折零件级交叉验证"` | 5 — R1/resampling | R1, EIC, DA | P1 | 0.5--3 天 |
| R2 | 全文将网络能力限定为固定 $r=0.05$, $\hat d=+z$, $V_{64}$ 和固定阈值下的 surrogate；摘要、题目、Eq. (6)、图 1/5/9、结论和讨论一致。若有可用资源，增加两个半径或方向的条件化敏感性；不能把未做的实验写成已做。 | SC-2, SC-5 | major | `equation: Eq. (6) — occupancy feature and p only` | 5 — R1/R2 | EIC, R1, R2, R3, DA | P1 | 2--5 天 |
| R3 | 增加独立效用锚点：优先使用不同实现的连续胶囊/工具碰撞检查、CAM 可达性检查或盲式领域专家案例排序；如果当前范围不允许，明确把论文主结论改为“代理标签的跨模型 surrogate fidelity”，并把真实后处理相关性列为待验证假设。 | SC-3, SC-4, SC-16 | major | `absence: §5 — expected independent validity layer; checked experiments, discussion and evidence manifest` | 5 — R2/DA | EIC, R2, R3, DA | P1 | 3--10 天 |
| R4 | 对主结果同时报告 point-pooled 与 model-macro F1/IoU、零件级中位数/IQR 和模型级 bootstrap；说明 1,553 双类件筛选对部署范围的影响，并标出固定前 400 件基线子集的选择与分布。 | SC-7 | major | `text: §5.1 "点池 F1 先连接所有留出点再计算"` | 5 — R1 | R1, DA | P1 | 1--3 天 |
| R5 | 补方向级 Top-k 的 eligible 点数、每点可达方向数分布、随机/全局先验/几何排序基线，并将 Top-1 的适用范围写进摘要和图注。 | SC-8 | major | `table: Table 6 — Top-1/Top-3 without denominator or ranking baseline` | 5 — R1/DA | R1, DA | P1 | 1--3 天 |
| R6 | 将“全局形状上下文”改成有实现依据的“局部至中程占据上下文”，报告 7³ 理论感受野和各消融定义；若保留全局表述，新增全局/多尺度分支并重跑。 | SC-6 | major | `figure: Fig. 5 — three same-resolution convolution blocks` | 5 — R1 | R1, DA | P1 | 1--4 天 |
| R7 | 公开当前标签质量的 10,000 件差分审计与 robust mismatch 口径，把表 4 的 160 点/10 件审核作为历史或补充；统一使用“边界带连续网格细化”而不是整个 oracle 的无条件“精确真值”。 | SC-15（标签部分） | minor | `table: Table 4 — audit sample sizes` | 5 — R1 | R1 | P1 | 0.5--2 天 |

### Suggested Revisions (Should Fix)

| # | Revision item | Sub-claim(s) | Severity | Evidence anchor | Confidence | Source | Priority | Estimated effort |
|---:|---|---|---|---|---:|---|---|---|
| S1 | 增加一个强几何替代基线（距离场/可见锥/多尺度局部净空之一）；无法重跑时，在讨论中明确其缺席以及神经网络必要性尚未被穷尽证明。 | SC-13 | major | `table: Table 5 — current baseline ladder` | 5 — DA | DA | P2 | 1--4 天 |
| S2 | 报告 Fusion/Thingi10K 的闭合、非流形、退化面、连通分量、丢弃点和从原始候选到最终 137 件的筛选统计，限定跨域结论的输入范围。 | SC-9 | major | `dataset: §4.3 — discarded-normal counts` | 4 — R2/R3 | R2, R3 | P2 | 1--3 天 |
| S3 | 将 112 倍拆成预处理、标签、模型加载、单点和批量查询；记录 CPU/GPU、同步和 batch size。无法端到端重跑时，把标题改成“单点查询量级”。 | SC-10 | minor | `text: §5.5 "约为 112 倍的量级差"` | 4 — R3 | R3, DA | P2 | 0.5--2 天 |
| S4 | 增加“设计审阅使用协议”：输入验收、风险排序、oracle 复核触发、不可用状态、离散方向提示和 not-a-toolpath 声明。 | SC-11 | major | `absence: §5--§6 — expected operational review protocol; checked results and discussion` | 4 — R3 | R3, DA | P2 | 1--2 天 |
| S5 | 为 H5/E5 生成统一 run envelope，补公开数据版本、访问日期、许可、再物化和小型 smoke dataset 入口；保留当前 provenance 注记。 | SC-15 | minor | `dataset: evidence/manifest.md — H5/E5 provenance notes` | 5 — R1/R3/DA | R1, R3, DA | P2 | 1--3 天 |
| S6 | 明确 0.5 阈值预先冻结，补 precision、recall、PR-AUC 或校准图；若不做概率校准，删去概率可直接支持决策的暗示。 | SC-14 | minor | `text: §4.5 "以 0.5 阈值生成二值结果"` | 5 — R1 | R1 | P2/P3 | 0.5--2 天 |
| S7 | 将贡献重写成一个可证伪 RQ，并加入与 DeepMill/PARC/IMF 的“可比/不可比”矩阵；不新增首创或优越性断言。 | SC-12 | major | `text: §2.3 "组织为闭环"` | 4--5 — EIC/DA | EIC, DA, R2 | P2 | 1--3 天 |
| S8 | 图 9 追加“64 个离散方向、非连续刀路”图例；图 1 增加输入网格质量失败分支；图 3 标出未建模的刀柄/夹具。 | SC-11 | minor | `figure: Fig. 9 — lowest blocked-probability arrow` | 4 — R3 | R3 | P3 | 0.5--1 天 |
| S9 | 统一术语为“潜在支撑接触区代理/下朝悬垂面代理”，在摘要、Eq. (1)、表 1、图注、讨论和结论逐处核对。 | SC-3, SC-16 | major | `equation: Eq. (1) — proxy definition` | 5 — R2 | R2, EIC, DA | P2 | 0.5--2 天 |
| S10 | 在补充材料中列出完整 8,590 件的全可达、双类和全不可达分布，避免只让读者从 82% 和 18.1% 推算。 | SC-7 | minor | `table: Table 3 — dataset statistics` | 4 — EIC | EIC | P3 | 0.5--1 天 |

### Revision Checklist

#### Priority 1 — Structural Revisions

- [ ] R1：修正主试验统计设计名称或重跑真正 K 折。
- [ ] R2：冻结并显式声明网络的工具/方向/阈值适用范围。
- [ ] R3：增加独立效用锚点，或把主结论严格降为 surrogate fidelity。
- [ ] R4：补模型级宏平均和固定子集代表性报告。
- [ ] R5：补方向 Top-k 分母、基率和强排序基线。
- [ ] R6：修正感受野与“全局上下文”叙述。
- [ ] R7：将 10,000 件差分审计接入论文标签质量证据。

#### Priority 2 — Content Supplementation

- [ ] S1：加入强几何替代基线或明确其缺席。
- [ ] S2：补网格质量和跨域筛选统计。
- [ ] S3：拆分端到端/单点查询成本。
- [ ] S4：写入设计审阅使用协议。
- [ ] S5：统一 H5/E5 运行封装和公开复现入口。
- [ ] S6：补阈值、PR-AUC/校准说明。
- [ ] S7：重写 RQ、贡献与近邻方法可比矩阵。

#### Priority 3 — Text and Formatting

- [ ] S8：图 1/3/9 增加非刀路和未建模约束图例。
- [ ] S9：统一“潜在支撑接触区代理”术语。
- [ ] S10：补全数据集角色分布表。

### Re-Review Requirement

完成 R1--R7 后进入 Stage 3' verification review。Stage 3' 必须逐项对照本路线的 evidence anchor 和 acceptance criteria；不能只重新看总体 F1。若 R3/物理有效性暂时无法新增，response-to-reviewers 必须明确记录作者选择的降级结论和剩余局限。

### Response Letter Template

修订时应为每个 R/S 项提供：原意见、作者行动、修改位置、旧/新文字或结果、证据文件/哈希、未采纳部分的理由。不得把“已在局限中说明”当作已解决 R1--R7 的充分证据，除非该项本身的 acceptance criteria 只要求收窄表述。

## Part 3: Reviewer Report Summary

### Journal-Fit Reviewer

- Recommendation: Major Revision | Confidence: 4/5
- Key point: 贡献和固定条件范围需要重新定位，才能达到计算制造/CAD 读者的投稿门槛。

### Reviewer 1 (Methodology)

- Recommendation: Major Revision | Confidence: 5/5
- Key point: 五次重复留出被误称为五折，且条件输入、感受野、模型级统计和方向指标需要补强。

### Reviewer 2 (Domain)

- Recommendation: Major Revision | Confidence: 4/5
- Key point: 下朝面是潜在接触代理而非真实接触；构建方向、阈值、网格质量和独立 AM 效用证据需明确。

### Reviewer 3 (Perspective)

- Recommendation: Minor Revision | Confidence: 4/5
- Key point: 工作流和图表有工程潜力，但需要风险输出协议、端到端成本和输入质量边界。

### Devil's Advocate

- Recommendation: Major Revision | Confidence: 5/5
- Key point: 当前最强证据是对自身 oracle 的 surrogate fidelity；独立效用、强几何基线和方向基率仍需验证。

