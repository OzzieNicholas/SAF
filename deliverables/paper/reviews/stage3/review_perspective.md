# Stage 3 Peer Review Report — Perspective Reviewer

## Manuscript Information

- **Title:** 金属增材制造支撑接触区的有限工具几何可达性评价与形状条件神经预测
- **Manuscript ID:** anonymous
- **Review date:** 2026-08-15
- **Review round:** Round 1 / Stage 3

## Reviewer Information

### Reviewer Role

Peer Reviewer 3 — Perspective / Practical

### Reviewer Identity

具有 CAD/CAM 软件与制造工程落地经验的跨学科研究者，关注设计审阅、工具和夹具约束、可解释可视化、数据复现以及计算方法进入工程流程的条件。

### Review Focus

从论文主学科之外的工程使用视角审查 SAF 是否能成为设计审阅中的可操作信号，图表和方向推荐是否避免被误读为刀路，速度与跨域结果是否具有足够的应用透明度，以及工具、夹具和责任边界等实践假设是否被明确呈现。

## Overall Assessment

### Recommendation

**Minor Revision**

### Confidence Score

4/5 — 对 CAD/CAM 工作流和几何软件部署有较高信心；不替代方法学审稿人重算统计量。

### Summary Assessment

从工程使用角度看，本文最有价值的不是宣称一个新的制造规划器，而是把接触点风险变成可以在设计阶段查看的热图，并在方向分支中保留“从哪里接近”这一比单一二分类更接近用户决策的信息。图 1、图 7、图 9 和图 10 已经形成了从离线标签、预测、方向推荐到回到几何复核的工作流雏形；局限节也没有假装基板、夹具、刀柄和路径连续性已经解决。主要不足是“可操作”仍停留在可视化层：论文没有给出设计工程师何时应接受、标记或回到 oracle 复核的阈值，也没有说明工具半径和方向配置变更会使模型重新训练。112 倍查询量级只比较单点调用时间，未计入网格修复、体素化、标签生成、网络加载和批处理方式，因此不能直接转化为设计流程节省。跨域结果使用固定 137 件 Thingi10K 子集，工程读者需要看到网格质量筛选和失败件分布，否则“稳健”容易被理解过度。图表总体清楚，但方向图中的箭头和概率可能被非专家误读为连续姿态或可执行刀路。建议小到中等修订：增加一个面向用户的输出协议（风险等级、复核触发、不可用条件），把速度拆成端到端阶段，补充网格/数据筛选统计，并在图注中显式标注“离散推荐、非路径”。这些修改不需要改变主算法即可显著提高工程可信度。

## Strengths

### S1: 工作流而非单一模型是清晰的使用入口

论文建议先用网络筛查，再在临界位置回到几何判定器复核；这比把概率直接当成生产决定更符合工程软件的责任分层。

**Evidence Anchor:** `text: §6 "网络热图更适合筛查与排序，而不是取代几何复核"`

### S2: 图表把抽象标签转成可观察的几何情形

盲腔、窄缝、等接触量案例、方向扇区和失败面都能让非纯 ML 读者理解风险来源。

**Evidence Anchor:** `figure: Fig. 3, Fig. 6, Fig. 9 and Fig. 10 — geometric examples and error surfaces`

### S3: 结果和限制没有把速度写成生产承诺

112 倍被限定为当前实现和硬件下的摊销量级，且讨论明确列出 Python 调度、硬件和未建模工艺条件。

**Evidence Anchor:** `text: §5.5 "不能将其解释为普遍的软件或算法速度结论"`

### S4: 跨域测试至少暴露了数据分布变化

Thingi10K 被完全留作测试而非训练，提供了一个工程上有意义的网格来源变化检查。

**Evidence Anchor:** `table: Table 6 — Fusion in-domain and fixed Thingi10K cross-domain rows`

## Weaknesses

### W1: 缺少面向设计审阅的风险输出协议

**Problem:** 论文给出概率热图和 0.5 二值阈值，但没有定义工程用户如何据此行动：何种概率/方向数量触发几何复核、何种区域直接标记为“不可用”、如何处理预测不确定或输入网格不合格。

**Evidence Anchor:** `absence: §5--§6 — expected operational risk tiers and review-trigger rule; checked results, discussion and conclusion`

**Why it matters:** 没有输出协议，SAF 仍是研究可视化而不是可嵌入 CAD 审阅的工具；用户可能把颜色梯度当成精确余量或把 0.5 当成工艺阈值。

**Suggestion:** 增加一个不改变科学结论的“使用协议”小节：区分 oracle 复核、模型筛查和不可用输入；给出风险排序而非安全认证的推荐流程，并明确阈值只为本实验二分类，不代表设备容差。

**Severity:** Major

**Confidence:** 4 — core expertise: CAD/CAM workflow design

### W2: 查询速度比较不是端到端工程成本

**Problem:** 3.97 ms 与 0.035 ms 是单点几何/网络查询的平均值，未清楚说明是否包含 CUDA 同步、网络前向初始化、占据体素化、网格预处理、标签生成和批量点查询；两种实现的批处理粒度也不同。

**Evidence Anchor:** `table: §5.5 — 3.97 ms, 0.035 ms and approximately 112× magnitude comparison`

**Why it matters:** 工程师关心一次零件审阅的总延迟和资源占用，而非孤立点查询；当前数字容易被引用成普遍加速。

**Suggestion:** 将结果改成“单点查询量级”，并补充端到端分解（mesh→occupancy、oracle label、network load、batch query）和 CPU/GPU、batch size、同步方式。若无法重跑，删除“速度优势”式措辞，仅保留离线标注后的查询摊销观察。

**Severity:** Major

**Confidence:** 4 — core expertise: engineering performance measurement

### W3: 方向箭头和概率图仍可能被误读为连续刀路

**Problem:** 图 9 用箭头表示最低被挡概率方向，文本虽说是 64 个离散方向，却没有在图中标明相邻方向之间不能插值，也没有显示刀柄、夹具和路径连续性未建模。

**Evidence Anchor:** `figure: Fig. 9 — arrows for lowest blocked probability among 64 directions`

**Why it matters:** 设计工程师可能把 Top-1 方向直接交给 CAM，忽略工具姿态碰撞或从当前方向进入的连续路径问题。

**Suggestion:** 在图 9 中加入“discrete approach hint / not a toolpath”图例；在正文给出一个三步使用流程：热图排序→离散方向候选→几何/CAM 复核。不要把 Top-k 命中率翻译为刀路成功率。

**Severity:** Minor

**Confidence:** 4 — competence basis: CAD/CAM human-factors review

### W4: 跨域稳健性对输入质量的依赖尚未对工程用户可见

**Problem:** Thingi10K 的 137 件双类子集经过面数、法向和可物化筛选，但文稿没有给出从原始候选到最终件的失败类型和输入质量分布。工程用户无法判断自己的开放网格、非流形网格或多实体装配是否在可用范围内。

**Evidence Anchor:** `absence: §5.4 and Table 6 — expected input-quality acceptance statistics; checked cross-domain setup and dataset table`

**Why it matters:** “跨域 F1 近似”只适用于通过当前前端的固定子集，不能直接转化为任意 CAD/网格文件的鲁棒性承诺。

**Suggestion:** 在数据与复现节增加输入验收清单和排除统计；将不合格网格明确标为“需要修复/不评估”，并在图 1 流程中放置失败分支。

**Severity:** Major

**Confidence:** 4 — competence basis: geometry pipeline deployment

### W5: 数据发布和复现入口还不足以让外部工程师直接运行

**Problem:** 证据清单给出了本地运行命令和哈希，但 Fusion 360 真实数据路径为本地私有路径，稿件没有给出公开下载、版本、许可和再物化步骤的最小说明；E5 还缺少统一 run envelope。

**Evidence Anchor:** `dataset: evidence_manifest.md — local source roots and E5 legacy provenance note`

**Why it matters:** 研究可审计不等于工程可复现。没有公开数据获取和许可说明，外部读者只能核对脚本结构，不能重建主数字。

**Suggestion:** 补充公开数据的版本/访问日期/许可链接、脱离本地路径的配置示例和一套小型公开 smoke dataset；把 E5 产物升级为统一 envelope。若数据许可不允许再分发，应明确“代码可复现、主数据需按原始仓库获取”。

**Severity:** Minor

**Confidence:** 4 — competence basis: reproducible engineering software

### W6: 工具和夹具边界虽写出，但没有一个具体的“不可用”示例

**Problem:** 局限节列出刀柄、夹具、基板和材料行为未建模，却只用文字说明；没有示例展示一个几何代理可达、但加入刀柄或夹具后应被否决的情形。

**Evidence Anchor:** `text: §6 "未建模刀柄、夹具、连续姿态轨迹、切削力、材料行为和表面质量"`

**Why it matters:** 一个反例图能帮助用户理解 SAF 是下界筛查，而不是“可达即可加工”；没有反例时，正向热图仍可能被过度信任。

**Suggestion:** 增加一个定性虚线工具/夹具遮挡示意，或在图 3 中标出“代理可达但完整工装未知”的区域；不需要声称有真实实验。

**Severity:** Minor

**Confidence:** 4 — competence basis: manufacturing workflow communication

## Detailed Comments

### Assumption Audit

- **Explicit assumptions:** 球工具、零件本体遮挡、离散直线逼近和固定构建方向均有明确说明。
- **Implicit assumptions:** 模型输出概率能被工程师按相对风险排序；输入网格已足够闭合；模型失败点可回到 oracle 复核。这些假设应在“使用协议”中写成条件，而不是留给用户推断。
- **Paradigmatic assumptions:** 计算几何代理可以先于物理过程用于早期筛查。该假设合理，但只能产生优先级信号，不产生安全/质量保证。

### Cross-Disciplinary Connections

- 可借鉴 CAD 软件中的“validity/repair status”输出，把网格质量作为预测前置状态。
- 可借鉴 CAM 的碰撞检查流程，把方向推荐设计为候选姿态列表而不是单一箭头。
- 对概率热图可借鉴软件静态分析的“warning / error / needs-review”三态，而非连续颜色直接代表物理余量。

### Practical Impact

- 适合设计早期比较两个几何方案的相对风险，尤其是等接触量案例。
- 不适合自动决定支撑去除顺序、刀具选择或生产放行。
- 工程部署前至少需要输入网格验收、固定配置声明和 oracle 复核入口。

### Broader Implications

- **Ethical dimensions:** 不涉及个人数据；主要风险是软件用户误把代理当认证，因此应加强免责声明和日志。
- **Social/industrial impact:** 可能减少设计迭代中的人工检查，但若输入质量或工具条件不匹配，也可能产生漏报；论文应把这种风险写成部署注意事项。
- **Future directions:** 与 CAM 碰撞检查、支撑生成和真实后处理记录建立盲测对应，比单纯扩大网络更能提升工程价值。

## Questions for Authors

1. 设计工程师看到模型概率 0.6、0.8 和 0.95 时，当前稿件希望其采取何种不同动作？如果没有动作差异，应避免给出看似可解释的数值精度。
2. 112 倍比较在统一 batch size、CUDA 同步和预处理后是否仍成立？一次完整零件审阅的端到端时间是多少？
3. 对开放或非流形网格，系统会拒绝、修复还是静默体素化？该状态是否进入输出文件？
4. 能否提供一个“代理可达但完整工装不可达”的示意案例，防止方向箭头被当作 CAM 刀路？

## Minor Issues

### Figures and Tables

- 图 1 应加入“输入质量检查失败”的分支。
- 图 9 的箭头旁添加离散方向数和 not-a-toolpath 标识。
- 表 6 加入端到端时间或至少说明当前只测单点 query。

### Layout / Language

- “推荐逼近方向”可改成“候选逼近方向提示”，降低动作承诺。
- “跨域稳健”在工程章节中建议改成“固定跨域子集上的未退化观察”。

## Dimension Scores

| Dimension | Score | Descriptor | Notes |
|---|---:|---|---|
| Originality (20%) | 72 | Adequate | 对设计审阅工作流有新颖的几何信号 |
| Methodological Rigor (25%) | 68 | Adequate | 端到端性能与输入状态说明不足 |
| Evidence Sufficiency (25%) | 66 | Adequate | 计算证据丰富，工程效用和质量分布不足 |
| Argument Coherence (15%) | 80 | Strong | 讨论与限制基本一致 |
| Writing Quality (15%) | 78 | Strong | 图表可读，用户动作协议缺失 |
| Significance & Impact | 70 | Adequate | 适合早期筛查，影响范围目前较窄 |
| **Weighted Average** | **70.8** | **Minor Revision** | 多数修改不需改变主算法，但需增加工程边界 |

