# Stage 3 Peer Review Report — Domain Reviewer

## Manuscript Information

- **Title:** 金属增材制造支撑接触区的有限工具几何可达性评价与形状条件神经预测
- **Manuscript ID:** anonymous
- **Review date:** 2026-08-15
- **Review round:** Round 1 / Stage 3

## Reviewer Information

### Reviewer Role

Peer Reviewer 2 — Domain

### Reviewer Identity

研究金属增材制造支撑生成、支撑移除和构建方向的 DfAM 学者，熟悉支撑接触区、悬垂判据、后处理约束和 AM 几何数据。

### Review Focus

评价下朝悬垂面是否被恰当地用作支撑接触区代理，论文是否区分支撑需求、真实接触、支撑去除和工具可达性，公开数据与固定构建方向是否支持领域结论，以及局限是否足以防止将几何代理误读为真实后处理可行性。

## Overall Assessment

### Recommendation

**Major Revision**

### Confidence Score

4/5 — 对 AM 支撑与后处理语义高度熟悉；对网络实现细节不作主要裁决。

### Summary Assessment

本文选择了一个 AM 论文中经常被支撑体积或悬垂面积掩盖的问题：支撑接触附近是否给有限尺寸工具留下了进入空间。作者没有把支撑生成、移除力学和可达性混为一谈，相关工作也正确承认可接近支撑体积、Surfel CNN、DeepMill 和 PARC 的先行贡献。以盲腔和窄缝解释“接触量不等于接近空间”是有效的 DfAM 动机。需要大修的原因是，论文标题和多处叙述使用“支撑接触区”，实际数据对象却是按 45° 阈值选出的下朝三角面质心；没有运行支撑生成器，也没有证明这些面在具体工艺/构建参数下形成真实接触。该代理可以成立，但应始终被称为“潜在支撑接触区代理”，并增加至少一个与真实或标准支撑生成结果的几何对照。其次，模型和标签固定在 +z 构建方向、单一半径和单一悬垂阈值，图 2 虽强调方向依赖，实验却没有方向敏感性或重定向泛化。Thingi10K 的网格闭合、法向和可制造性筛选也缺少领域统计。最后，没有真实支撑移除或 CAM 碰撞对照并不必然使几何代理失效，但会限制“后处理风险”只能是设计前端假设。论文在边界表达上已有良好基础；若把代理语义、方向条件、网格质量和应用证据进一步补强，领域价值会更可信。

## Strengths

### S1: 清楚区分支撑量与接近空间

受控等接触量案例以及全量相关统计共同说明，材料/面积类指标不能直接替代工具进入空间；这是对 DfAM 评价维度的有意义补充。

**Evidence Anchor:** `figure: Fig. 6 — matched-contact examples and Spearman statistics`

### S2: 没有把几何代理冒充真实去支撑认证

论文反复说明不建模基板、支撑间遮挡、去除顺序、夹具、切削力和材料行为，这一边界符合当前数据能支持的结论。

**Evidence Anchor:** `text: §3.2 "不可外推为真实车间中的可行性认证"`

### S3: 相关工作对领域先行研究的态度准确

IMF、DeepMill、PARC 和 Surfel CNN 被用于划分对象和泛化单元，而不是被贬低或错误声明“首创”。

**Evidence Anchor:** `table: Table 1 — object, tool condition, generalization unit and output comparison`

### S4: 固定跨域子集暴露了野网格条件

将 Thingi10K 作为恒定测试源而非训练数据，可以检查从较规则 CAD 到更复杂网格的分布变化，且正文没有把固定子集结果外推为普遍域不变性。

**Evidence Anchor:** `text: §5.4 "本次固定子集上未观察到退化"`

## Weaknesses

### W1: “支撑接触区”与实际提取对象之间仍有语义缺口

**Problem:** 式（1）把所有满足法向阈值的下朝面定义为支撑接触区代理，采样是每个三角面的质心；管线没有生成支撑实体，也没有判断某下朝面是否因自支撑、热设计、扫描策略或支撑优化而实际接触支撑。

**Evidence Anchor:** `equation: Eq. (1) — support-contact proxy equals downward-facing overhang samples`

**Why it matters:** AM 读者通常把“support-contact region”理解为支撑与零件真正相连的区域。若所有下朝面都被当作接触区，数据中可能包含不会布置支撑的面，也可能遗漏由具体支撑策略形成的离散接触。

**Suggestion:** 题目、摘要、图注和结论统一使用“潜在支撑接触区代理”或“下朝悬垂接触候选区”。新增一组小规模对照：选择一个公开或可复现的支撑生成器，报告代理面与实际支撑接触面的覆盖率/精确率；若不新增实验，必须把“真实接触区”相关措辞全部收窄并将这一差距列为第一局限。

**Severity:** Major

**Confidence:** 5 — core expertise: AM support semantics

### W2: 构建方向被定义为输入，却在实验中完全冻结

**Problem:** 图 2 强调同一零件改变构建方向会改变接触区，问题定义也把 $\hat d$ 列为输入，但数据、标签和网络均固定在 +z 构建方向；网络本身不接收 $\hat d$。没有报告旋转/方向敏感性，也没有说明换方向需重新提取、重标和重训。

**Evidence Anchor:** `figure: Fig. 2 — two build orientations contrasted without a corresponding quantitative experiment`

**Why it matters:** 构建方向是 AM 支撑需求最关键的设计变量之一。若论文强调方向依赖，却不检验模型对方向变化的行为，DfAM 读者可能误以为 SAF 可直接用于方向比较或优化。

**Suggestion:** 明确声明本文只评价一个预先给定且固定的构建方向，不执行方向优化。理想修复是选取若干零件、若干离散旋转，重新提取接触区并报告代理统计/预测变化；最低修复是在方法和结论中写明换方向要重体素化、重提取，当前网络不保证旋转等变。

**Severity:** Major

**Confidence:** 5 — core expertise: build-orientation effects

### W3: 单一悬垂阈值和单一工具尺度不足以支撑一般 AM 场景

**Problem:** 主结果固定 $45^\circ$ 悬垂阈值和归一半径 0.05。论文没有给出 40°/50° 或不同半径下接触区规模、不可达比例和预测稳定性；不同 AM 工艺、材料和支撑策略的临界角并不相同。

**Evidence Anchor:** `text: §5.1 "工具半径为 0.05，悬垂角阈值为 45°"`

**Why it matters:** 本文可以研究标准化几何代理，但不能让一个固定设置代表金属 AM 的全部设备和材料。缺少敏感性结果会限制结果的领域可迁移性。

**Suggestion:** 至少对一组代表性零件重算 40°/45°/50° 与两个工具半径，报告标签分布和相关结论是否保持；模型若不条件化，则明确每个配置需独立训练。敏感性扫只验证代理稳健性，不应被写成材料工艺结论。

**Severity:** Major

**Confidence:** 4 — core expertise: DfAM parameter sensitivity

### W4: 野网格质量与法向清理的领域影响报告不足

**Problem:** 论文报告 Fusion 丢弃 11,573 个、Thingi10K 丢弃 4,321 个疑似翻面点，但没有按零件给出闭合性、非流形、退化面、连通分量和被丢弃比例分布。基于广义缠绕数的占据可缓解缠绕问题，却不能保证任意开放/自交网格具有正确的实体语义。

**Evidence Anchor:** `dataset: §4.3 — discarded-normal counts for Fusion and Thingi10K`

**Why it matters:** Thingi10K 被用作跨域证据，若筛选后只留下较容易体素化或法向较一致的子集，0.889 不能代表一般打印网格。

**Suggestion:** 在补充表中报告原始候选数、有效物化率、面数范围、闭合/非流形比例、每件丢弃点分位数和排除原因；把“跨域”限定为“在该固定、通过几何前端筛选的双类子集上”。

**Severity:** Major

**Confidence:** 4 — core expertise: AM mesh preprocessing and data validity

### W5: 后处理风险的领域效用尚未由独立任务验证

**Problem:** 论文用几何 oracle 产生标签，再用网络预测同一标签；没有与实际支撑去除、CAM 工具碰撞检查、专家可达性标注或后处理时间/失败记录比较。

**Evidence Anchor:** `absence: Experiments and Discussion — expected an independent AM post-processing or CAM accessibility validation; checked §5.2--§5.5, §6 and evidence manifest`

**Why it matters:** 当前结果能证明网络逼近代理，也能证明代理不同于接触量和零半径射线；它尚不能证明代理与真实去支撑困难之间具有多大关联。

**Suggestion:** 若暂时无法做物理实验，可增加一个可复现的独立几何验证层：在少量零件上使用不同实现的精确工具扫掠或 CAM 碰撞检查，并由领域专家盲审案例排序。正文把应用结论改成“候选筛查信号”，将真实效用列为待验证假设。

**Severity:** Major

**Confidence:** 5 — core expertise: translational validity in AM

### W6: 支撑移除文献仍可更接近真实接触与后处理

**Problem:** 参考文献很好地覆盖了可接近支撑、支撑检测和制造可达性，但围绕接触界面、支撑去除方式和实际后处理约束的来源较少，领域动机主要由综述和自动去支撑论文承担。

**Evidence Anchor:** `absence: §2.1 and References — expected additional support-interface/removal evidence; checked citations [1]--[7] and discussion`

**Why it matters:** 对象创新依赖“接触区是独立而重要的后处理对象”，需要更直接的领域证据支撑，而不仅是一般支撑负担。

**Suggestion:** 在确定目标期刊后，补充 2--4 篇可核验的金属 AM 支撑接触/移除研究，说明不同工具和支撑界面如何改变可接近要求；不能核验的文献不要加入。

**Severity:** Minor

**Confidence:** 4 — core expertise: AM support-removal literature

## Detailed Comments

### Title & Abstract

建议把“支撑接触区”改为“潜在支撑接触区”或在题目后半明确“下朝悬垂面代理”。摘要应写出固定构建方向和单一归一工具半径，以防读者把模型理解为通用工具条件网络。

### Introduction and Literature

“支撑量并非无用，而是不能替代几何可接近性”的表述准确。可进一步区分三件事：支撑是否需要、支撑实际放在哪里、放置后的接触能否被工具接近。本文只直接处理第三件事的候选几何层。

### Methodology

45° 是统一比较的工程假设，不是金属 PBF 的普遍材料常数。应给出构建方向坐标约定、方向半球与工具接近方向的物理解释。球工具适合表达某些磨头/刀端的包络，但不代表刀柄和长工具；建议在图 3 旁增加“球端代理而非完整工具”的标识。

### Results

跨域结果值得保留，但“Thingi10K 双类子集”需要更透明的形成流程和排除统计。等接触量案例是领域解释图，不应作为真实支撑布置证据；当前图注已经接近这一边界。

### Discussion

局限节内容完整，建议把“潜在接触区不等于实际接触区”提升为第一条，而不是只写“不是对真实支撑形貌的重建”。后续研究优先级应是代理与真实/软件生成支撑接触的对应，而不仅是更复杂的网络。

## Questions for Authors

1. 式（1）提取的下朝面中，有多少最终会在任一标准支撑生成策略下形成真实支撑接触？
2. 若同一零件旋转 90° 或改变悬垂阈值，现有网络需要哪些重算或重训步骤？
3. Thingi10K 固定 137 件子集从原始候选到最终样本经历了哪些排除，是否偏向闭合或易体素化网格？
4. 作者能否提供一个独立 CAM/专家案例验证，说明 SAF 排序与实际工具接近判断具有一致趋势？

## Minor Issues

### Terminology

- “支撑接触区”“接触区代理”“下朝悬垂面”需形成固定术语层级。
- “后处理工具”建议注明当前更接近球端/磨头包络，而不是一般切削刀具全几何。
- “金属 AM”属于应用背景，实验未使用材料属性；摘要中不宜暗示材料特异性结果。

### Figures

- 图 2 可在图注加入“只说明方向依赖，不评价方向优劣”。
- 图 3 可画出被忽略的刀柄/夹具为灰色虚线轮廓，并标“未建模”，帮助工程读者理解边界。

## Dimension Scores

| Dimension | Score | Descriptor | Notes |
|---|---:|---|---|
| Originality (20%) | 72 | Adequate | 接触候选区代理有领域增量，需与真实接触语义更严格区分 |
| Methodological Rigor (25%) | 69 | Adequate | 几何链路清楚，方向/阈值/网格敏感性不足 |
| Evidence Sufficiency (25%) | 63 | Adequate | 计算证据充分，缺少独立 AM/CAM 效用验证 |
| Argument Coherence (15%) | 80 | Strong | 论证边界较克制，术语仍有语义滑移 |
| Writing Quality (15%) | 80 | Strong | 领域表达清楚，代理层级需统一 |
| Literature Integration | 72 | Adequate | 近邻方法覆盖好，真实接触/去除文献略薄 |
| **Weighted Average** | **71.0** | **Major Revision** | 可发表潜力存在，需补强代理有效性和条件范围 |

