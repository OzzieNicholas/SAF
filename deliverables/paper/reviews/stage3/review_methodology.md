# Stage 3 Peer Review Report — Methodology Reviewer

## Manuscript Information

- **Title:** 金属增材制造支撑接触区的有限工具几何可达性评价与形状条件神经预测
- **Manuscript ID:** anonymous
- **Review date:** 2026-08-15
- **Review round:** Round 1 / Stage 3

## Reviewer Information

### Reviewer Role

Peer Reviewer 1 — Methodology

### Reviewer Identity

专长三维几何学习与计算几何评测的研究者，研究占据/隐式场、网格碰撞检测、距离场近似、模型级泛化和不平衡分类。

### Review Focus

检查有限球工具扫掠的形式定义、体素近似与边界带细化是否一致，标签审核能否支撑监督学习，网络结构和输入条件是否与其主张一致，以及数据切分、统计单位、基线、置信区间和复现材料能否支持定量结论。

## Overall Assessment

### Recommendation

**Major Revision**

### Confidence Score

5/5 — 核心问题属于计算几何标签构造、三维神经网络和统计评测。

### Summary Assessment

本文建立了一个定义清楚的有限球工具直线逼近判据，并将体素距离场筛选与连续胶囊—网格距离检查结合，随后用轻量三维卷积网络预测点级和方向级标签。方法部分优点明显：几何语义以式（1）--（5）明确给出，标签不是直接当作无误差真值，而是配有差分、跨分辨率和失败带审核；数据也按零件而非按点切分。主要问题并非模型完全无效，而是报告方式比实际实验设计更强。`train_convonet.py` 对五个 seed 分别执行新的 0.6/0.2/0.2 随机留出，测试集彼此可重叠，这不是五折交叉验证；因此主结果必须改称五次重复随机留出，或者重新实现真正的 K 折。模型只接收占据栅格和查询点，不接收工具半径、构建方向或方向向量；程序化与 Fusion 训练数据的体素半径也不同，这使“有限工具预测”的条件范围需要更明确。三层卷积的有效感受野有限，不能自动承担全文暗示的全局形状上下文。最后，主结果以点池 F1 为主、方向 Top-k 缺少分母和基率、E5 产物缺少统一运行封装。上述问题均可修复，但涉及主结果定义、模型能力边界和统计呈现，建议大修后复审。

## Strengths

### S1: 形式判据与实现分层基本一致

式（2）定义有限球工具沿外向方向的扫掠，式（5）把明确区域和边界带分开，算法 1 也按同一顺序实现；这比只给“碰撞检测”散文更可审核。

**Evidence Anchor:** `equation: Eq. (2)--Eq. (5) — finite sphere sweep and boundary-band decision`

### S2: 使用零件级切分避免了最明显的点泄漏

训练和测试不把同一零件的接触点随机拆开，程序化数据仅加入训练；这与跨模型预测问题相符。

**Evidence Anchor:** `text: §4.5 "所有切分都以零件为单位"`

### S3: 主动报告边界点失效而非只给总体 F1

按可达方向数分箱的失效分析揭示 1--5 个可达方向时误差明显升高，能够连接标签边界和模型错误。

**Evidence Anchor:** `figure: Fig. 10 — error rate by viable-direction count and representative failure surface`

### S4: 数字溯源材料允许独立核对不同运行

基线、回归、消融、跨域和方向场分别保留运行命令、样本数和摘要，避免把 0.893、0.930、0.886 和 0.463 写成同一统计量。

**Evidence Anchor:** `dataset: evidence_manifest.md — canonical run IDs and metric definitions`

## Weaknesses

### W1: 主试验被错误命名为五折交叉验证

**Problem:** 正文称“5 折零件级交叉验证”，但实际脚本对 seed 0--4 各自调用 `split_by_model(..., frac_train=0.6, frac_val=0.2, seed=seed)`。这产生五次重复随机留出；各次测试集不是互斥折，不能保证每件恰好测试一次。

**Evidence Anchor:** `text: §5.3 "主试验在 Fusion 双类零件上进行 5 折零件级交叉验证"`

**Why it matters:** “K 折”意味着一套确定的分区与覆盖性质，重复留出则估计另一种随机切分变异；两者的均值、标准差和样本依赖结构不能互换。该错误直接影响 headline 结果的统计解释。

**Suggestion:** 二选一：其一，保持现有产物，将全文统一改为“五次模型级重复随机留出（每次 60/20/20）”，并给出测试集重叠与每次件数；其二，实现真正的五折分区并重新训练，报告折间均值、标准差以及汇总的 macro/pooled 指标。不要把每个 seed 同时称为 fold 和 training seed。

**Severity:** Major

**Confidence:** 5 — core expertise: resampling design and model evaluation

### W2: 网络不是工具条件或构建方向条件模型

**Problem:** 式（6）的网络输入只有占据特征和查询坐标，工具半径、构建方向、悬垂阈值和方向集合均固定在标签生成阶段。方向模型一次输出固定 64 个槽位，也不接收方向向量。因此新工具半径、旋转后的构建方向或不同方向离散化不能直接查询同一个已训练模型。

**Evidence Anchor:** `equation: Eq. (6) — q_theta receives only interpolated occupancy feature and p`

**Why it matters:** 论文多处把“工具尺寸必须进入几何语义”与“形状条件预测”相连，读者容易误以为模型可随工具条件变化；实际模型只逼近一个冻结配置上的标签函数。

**Suggestion:** 最低修复是把模型明确写成 `q_theta(p,P | r=0.05,d=+z,V=V_64)`，并在摘要、贡献和结论声明换条件需重标和重训。更强修复是把归一化半径与方向向量作为输入，做至少两个半径和两个构建方向的条件化评测。

**Severity:** Major

**Confidence:** 5 — core expertise: conditional neural fields

### W3: “形状条件”成立，但网络的空间上下文被表述得比实际感受野更广

**Problem:** ConvONetLite 由三个无下采样的 3×3×3 卷积组成，对查询特征的理论感受野为 7×7×7 体素；MLP 另接绝对坐标。它确实依赖占据形状，但不能从任意距离传播全局遮挡。正文将性能提升解释为“形状上下文有助于区分盲腔、通道和开阔区域”，尚未区分局部/中程上下文与全局形状编码。

**Evidence Anchor:** `figure: Fig. 5 — three same-resolution convolution blocks with no pooling or global branch`

**Why it matters:** 论文的核心动机之一是可达性依赖远程遮挡；若编码器只看 7 体素邻域，读者需要知道性能来自局部占据、绝对位置先验还是更广形状信息。否则“shape-conditioned”可能被误读成完整全局形状表征。

**Suggestion:** 在正文给出实际感受野和各消融变体定义；将“全局形状上下文”改为“局部至中程占据上下文”，除非新增池化/多尺度/全局分支。可加入坐标-only、7³ patch、全局池化三组对照以分解来源。

**Severity:** Major

**Confidence:** 5 — core expertise: convolutional receptive fields

### W4: 主性能统计仍偏向点池，不能充分描述跨零件稳健性

**Problem:** headline 0.886 是把留出点连接后计算的点池 F1；不同零件接触点数差异较大。表 5 虽报告 80 件子集的零件级均值和区间，H3 全量主试验没有相同的 macro F1、每件分位数或置信区间。

**Evidence Anchor:** `text: §5.1 "点池 F1 先连接所有留出点再计算"`

**Why it matters:** 点多的网格在点池指标中权重更高，可能掩盖少点或高风险零件上的低性能；论文主张跨模型，模型级分布应与点池指标同等重要。

**Suggestion:** 对每次留出同时报告 point-pooled F1/IoU、model-macro F1、模型级中位数与 IQR，并按零件 bootstrap 给出差值区间。若保留固定 400 件基线子集，说明为何取“前 400”而非预注册随机样本，并给出其标签分布与全部 1,553 件的差异。

**Severity:** Major

**Confidence:** 5 — core expertise: clustered-data evaluation

### W5: 方向级 Top-k 结果缺少必要分母和基率

**Problem:** Top-1/Top-3 只在至少有一个可达方向的点上统计，但表 6 没有报告这类点的数量、方向可达率、随机或简单几何排序基线。0.957 可能很强，也可能部分来自大量方向均可达的容易点。

**Evidence Anchor:** `table: Table 6 — Top-1 / Top-3 row without eligible-point count or ranking baseline`

**Why it matters:** 方向级输出是论文区别于普通二分类的重要贡献，排名指标必须让读者判断它超过“随便挑一个方向”的程度。

**Suggestion:** 报告 eligible points、每点可达方向数分布、随机 Top-k 期望、按全局方向先验排序的基线，并按可达方向数分箱给出 Top-1。补充 E5 统一 run envelope，再进入终稿。

**Severity:** Major

**Confidence:** 5 — core expertise: ranking metrics and class prevalence

### W6: 标签审核对“代理一致性”有用，但不能支持连续几何真值的措辞

**Problem:** 表 4 的 0.63% 差分审核只有 160 个采样点，97.28% 跨分辨率一致率来自 10 件；差分参考本身也是离散 occupancy 近似。正文已承认这一点，但“精确胶囊—网格求交”和“可审核自动标签”容易让读者高估整体真值质量。

**Evidence Anchor:** `table: Table 4 — 160-point differential audit and 10-model resolution audit`

**Why it matters:** 标签误差会成为网络性能上限和失效带的一部分；小样本一致率不能推断全数据的连续几何误差率。

**Suggestion:** 使用新增的 10,000 个固定 seed 差分结果作为补充材料，报告 exact/boundary/robust mismatch 分类；对一组真实网格直接用全三角连续胶囊检查作为参考，给出置信区间。正文统一使用“continuous mesh refinement within the boundary band”，避免把整个标签器称作连续精确真值。

**Severity:** Minor

**Confidence:** 5 — core expertise: geometric validation and surrogate labels

### W7: 二值阈值和不平衡任务的报告仍可加强

**Problem:** 所有模型固定使用 0.5 阈值和未加权 BCE；没有说明阈值是否在验证集冻结，也没有 PR-AUC、precision/recall、校准误差或可靠性曲线。

**Evidence Anchor:** `text: §4.5 "推理时以 0.5 阈值生成二值结果"`

**Why it matters:** 不可达点在全量 Fusion 中仅占 7.5%，F1 对阈值敏感；只给 F1/IoU 无法判断热图概率是否适合“筛查与排序”。

**Suggestion:** 明确阈值为预先固定而非测试集优化；补充 precision、recall、PR-AUC 和按模型校准图。若不评估校准，删除“连续概率可用于热图”的决策性暗示，只保留相对风险可视化。

**Severity:** Minor

**Confidence:** 5 — core expertise: imbalanced classification

## Detailed Comments

### Methodology / Research Design

式（2）中的半无限路径由有限 $L$ 表示，建议给出 $L$ 的实现定义和为什么足以越过所有可能干涉三角形。`c(p,v)` 实际以 0.5 体素步长取样，应在式（4）下直接写成离散最小值，而不是先写连续最小再在散文说明离散实现。边界带中的“精确”是相对于原三角网格的 segment-triangle 距离，不包括退化面和输入网格语义错误；建议把这一层级写清。

### Data and Splits

只保留双类件用于主评测是合理的挑战集设计，但必须与“部署在全部零件”区分。建议同时在全部 8,590 件上报告零件级检出/误报分布，或明确主任务不估计全量部署性能。程序化数据半径为 3.0 体素，Fusion 为约 1.714 体素，而网络不接收半径；需要说明两者的相对尺度为何兼容，最好做移除程序化数据的消融。

### Results

表 5 很好地分开点池与零件均值，但 H3、H5 和 E5 没有采用完全一致的报告框架。建议为每个任务固定“数据、分割、重复、正类、聚合、区间、阈值”七项表头。独立回归运行可作为复现稳定性证据，不应与主试验合成一个更高性能数字。

### Reproducibility

统一运行封装、输入摘要和命令是优点。`torch.manual_seed` 不等于 GPU 完全确定性；应记录 CUDA/cuDNN deterministic 设置或明确结果为 seeded but not bitwise deterministic。H5 capture 和 E5 legacy file 均应升级到与 baselines/regression 相同的运行 envelope。

## Questions for Authors

1. 作者愿意将 0.886 重新表述为“五次重复随机留出”还是重新跑真正五折？两种方案应选择其一，不宜继续混称。
2. 程序化训练数据半径为 3.0 体素、Fusion 为约 1.714 体素，而网络没有半径输入；移除程序化数据后 H3/H5 如何变化？
3. 三层卷积的 7³ 感受野是否足以支持“全局遮挡”解释？是否有全局池化或多尺度编码的未报告实现？
4. Top-1 评测中 eligible points 的数量和每点可达方向数分布是多少？随机/先验基线是多少？

## Minor Issues

### Formula and Terminology

- 式（4）的连续 `min` 与实现中的 0.5 体素采样需统一符号。
- “五折”“五个模型级切分”“五个训练种子”目前混用，应分别定义。
- 建议把 `BCEWithLogitsLoss` 的正类（blocked/inaccessible）在式（7）后再写一次。

### Tables

- 表 4 增加审核置信区间或至少列出分子/分母。
- 表 6 增加 eligible points、blocked prevalence 和随机 Top-k 基线。
- 表 5 的 CI 是模型均值区间，不是点池 F1 区间，建议在列标题中直接写明。

## Dimension Scores

| Dimension | Score | Descriptor | Notes |
|---|---:|---|---|
| Originality (20%) | 68 | Adequate | 代理对象和标签闭环有价值，网络方法本身增量有限 |
| Methodological Rigor (25%) | 58 | Weak | 重复留出被写成五折，条件输入和感受野解释不完整 |
| Evidence Sufficiency (25%) | 65 | Adequate | 多组实验齐全，但主宏观统计与方向基率缺失 |
| Argument Coherence (15%) | 74 | Adequate | 语义链清楚，部分模型能力表述超出实现 |
| Writing Quality (15%) | 80 | Strong | 公式与结果组织成熟，需修正若干精确术语 |
| **Weighted Average** | **67.7** | **Major Revision** | 核心可修复，但需要重写主评测和能力边界 |

