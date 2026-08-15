# Stage 3 Peer Review Report — Journal-Fit Reviewer

## Manuscript Information

- **Title:** 金属增材制造支撑接触区的有限工具几何可达性评价与形状条件神经预测
- **Manuscript ID:** anonymous
- **Review date:** 2026-08-15
- **Review round:** Round 1 / Stage 3

## Reviewer Information

### Reviewer Role

Journal-Fit Reviewer（稳定角色名：`EIC`）

### Reviewer Identity

负责计算制造与几何建模稿件的 CAD 期刊副编辑，熟悉支撑可达性、CAM 碰撞分析、几何深度学习和 DfAM；以 `Computer-Aided Design` 的计算制造/几何读者作为压力测试基准，不把其投稿政策当作既定事实。

### Review Focus

从编辑视角评价研究问题是否属于计算制造/CAD 读者关心的范围，贡献是否超出已有可达性学习工作的简单换场景，以及题目、摘要、图表、结果和结论是否形成可信且不过度承诺的整体叙事。

## Overall Assessment

### Recommendation

**Major Revision**

### Confidence Score

4/5 — 主要判断属于计算制造与几何学习范围；对具体期刊的栏目政策仅作未冻结的定位参照。

### Summary Assessment

本文把金属增材制造支撑接触区抽象为一个有限球工具、多方向直线逼近的几何代理，并用两级标签器和形状条件网络在 Fusion 360 Gallery、Thingi10K 及程序化数据上预测点级和方向级风险。稿件最大的优点是边界写得比常见的“智能制造”论文克制：它明确说明只建模零件本体遮挡，不把结果称为工艺认证；同时给出图表、基线、消融、跨域测试和失败带分析。问题在于，面向 CAD 期刊的核心贡献仍没有被压缩成一个足够锋利、可与 DeepMill、PARC 和可接近支撑研究直接区分的命题。当前“闭环”叙事把新问题定义、标签实现和已有形状条件网络组合在一起，但没有独立证据说明该组合相对于现有可达性方法提供了什么不可替代的研究价值。另有若干实验措辞和适用范围需要收紧，尤其是主试验的交叉验证命名、固定工具/方向配置与更一般的可达性表述之间的距离。建议大修：重写贡献和研究问题，明确论文是代理定义与跨模型 surrogate benchmark，补充或至少系统讨论与最近邻方法的可比验证，并把所有性能数字按其运行设置分层呈现。修订后论文有机会成为一篇扎实的专业方法稿，但目前尚不宜直接接收。

## Strengths

### S1: 问题边界清楚且与结果一致

论文明确把 SAF 限定为“仅考虑零件本体遮挡的几何代理”，并在讨论中列出基板、刀柄、夹具、路径和材料行为不在模型内。这使读者能正确理解结果的证据等级，而不是把 F1 误读为生产可行性。

**Evidence Anchor:** `text: §6 "输出是后处理几何风险的下界代理，不是生产放行或工艺认证结论"`

### S2: 证据链的可读性明显高于单一性能表

图 1、图 3、图 4、图 7--10 依次覆盖问题语义、标签链路、预测、跨域和失效分布；这为编辑和审稿人追踪“定义—标签—模型—结果—局限”提供了完整入口。

**Evidence Anchor:** `figure: Fig. 1--Fig. 10 — workflow, criterion, oracle audit, prediction and failure views`

### S3: 研究对象和数据角色有明确分工

Fusion 360、Thingi10K 和程序化数据分别承担主数据、固定跨域测试和受控辅助信号，且正文没有把三者混写为同一来源的泛化证据。

**Evidence Anchor:** `table: Table 3 — data source, split and role columns`

## Weaknesses

### W1: 核心贡献相对于近邻可达性学习工作的独立增量仍不够锋利

**Problem:** 论文正确承认 DeepMill 已实现跨模型、工具条件的神经制造可达性，PARC 已表达制造可达性场；SAF 的新增内容主要是把对象限定为 AM 支撑接触区、构造一个代理 oracle，并沿用形状条件解码范式。当前贡献列表把“定义对象、实现标签链路、训练网络”并列为三项贡献，却没有给出一个可检验的命题说明为什么这一组合在 CAD 领域形成超出应用迁移的独立方法贡献。

**Evidence Anchor:** `text: §2.3 "本文的工作重点是将一个明确的 DfAM 几何代理对象、稳定的自动标注链路和跨模型预测组织为闭环"`

**Why it matters:** 对高门槛 CAD 读者而言，应用对象的缩窄本身可能是有价值的，但必须说明新对象带来的算法、评测或设计决策能力；否则容易被判断为已有神经可达性框架的领域化重述。

**Suggestion:** 将主贡献改写为一个明确的研究问题和可证伪假设，例如“在支撑接触区代理上，有限工具语义是否产生射线基线无法解释的风险结构，以及形状条件查询是否能在零件级留出上复现该结构”。补充与 DeepMill/PARC 的可比维度（对象、监督、泛化单位、工具条件、输出和成本），并把不能公平复现的部分明确列为未比较，而不是仅用表 1 做分类对照。

**Severity:** Major

**Confidence:** 4 — core expertise: computational manufacturing editorial assessment

### W2: “投稿级”整体定位仍依赖未冻结的期刊与应用标准

**Problem:** 稿件同时使用 CAD、DfAM、几何学习和后处理风险四套读者语汇，但没有一个优先读者和明确的主问题句。匿名稿不需要填写期刊，却仍需要在引言开头告诉读者这是几何代理 benchmark、AM 设计方法，还是神经表示方法。

**Evidence Anchor:** `absence: §1 Introduction — expected one-sentence primary research question and primary readership; checked title, abstract, contributions and section roadmap`

**Why it matters:** 读者无法判断应以几何判据的新颖性、AM 语义的有效性还是网络泛化来评价论文，编辑初筛时容易把稿件送到不匹配的审稿组合。

**Suggestion:** 在引言末尾增加一个单句 RQ 和一个“本文不解决什么”的短段；摘要首句明确主贡献是“定义并验证代理”，网络是第二层 surrogate，而不是泛化的工具规划器。

**Severity:** Minor

**Confidence:** 4 — core expertise: journal positioning and manuscript structure

### W3: 结果的高可读性掩盖了模型可迁移范围很窄这一事实

**Problem:** 结果给出 0.886、0.889 和 0.957 等很强的数字，但主模型固定了工具半径、悬垂阈值、构建方向和 64 个离散方向；正文虽在方法节列出这些值，却没有在摘要和贡献定位中显式说明网络不能直接换工具或换构建方向。

**Evidence Anchor:** `text: §5.1 "工具半径为 0.05，悬垂角阈值为 45°"`

**Why it matters:** 编辑和工程读者可能把“finite-tool”理解为工具条件可输入、可迁移的模型，而实际网络是固定配置上的形状条件分类器。

**Suggestion:** 将标题/摘要中的表述收窄为“在固定代理配置下的形状条件预测”，或增加多半径/多方向条件化实验并把半径和构建方向作为输入。至少应在摘要中写出“本文网络未对工具半径或构建方向参数化”。

**Severity:** Major

**Confidence:** 4 — core expertise: scope-to-claim editorial audit

## Detailed Comments

### Title & Abstract

题目准确但略大；“有限工具几何可达性”容易被理解为通用工具规划。摘要的限制声明很好，应把“固定半径、离散方向和固定构建方向”前移到结果句附近，并把“independent regression check”解释为独立运行而非独立真值。

### Introduction

动机、盲腔和窄缝例子有效。建议把 RQ、假设和论文单位（点/方向/零件）集中成一段，减少“后处理风险”与“支撑量互补”在多处重复。

### Literature Review

文献定位总体诚实，主动否认“首创”是优点。但仅有分类表还不足以支撑方法增量；应增加一段“哪些比较不能做、为什么不能做”，避免读者将表 1 当作性能比较。

### Methodology / Research Design

方法叙述清楚，公式和图 4 对编辑判断很有帮助。建议把网络的固定配置、实际感受野和训练数据混合比例放到方法摘要表中，以便快速判断是否为工具条件模型。

### Results / Findings

表 5--6 的结果分层意识较好。应把主结果的随机重复留出与真正 K 折交叉验证区分，并在正文中把 80 件基线子集的选择规则和代表性限制写得更醒目。

### Discussion / Conclusion

讨论已经主动限制外推，结论基本匹配证据。仍需把“提供风险观察维度”与“验证了后处理风险”的措辞严格分开，并说明没有真实去除实验时，应用意义属于设计筛查假设而非已验证收益。

### References

18 条文献对方法稿是可接受的，且近邻工作选择合理。投稿前应根据最终期刊补充其读者熟悉的 AM 支撑移除或 CAD 可达性综述，但不应为了凑数量加入礼节性引文。

## Questions for Authors

1. 如果把 DeepMill/PARC 视为方法参照而非竞争基线，本文可被单独检验的核心假设究竟是什么？
2. 网络是否能在不重新训练的情况下改变工具半径、构建方向或离散方向集？如果不能，标题和摘要是否应显式收窄？
3. 论文希望读者把 SAF 用作排序、筛查还是几何复核触发器？三者的输出阈值和责任边界是否应分别说明？

## Minor Issues

### Figures and Tables

- 图 8 同时展示多个运行口径，建议在图内或图注中用更强的视觉分隔标出“同集比较”和“独立回归”。
- 表 3 可增加“全不可达件”一列；当前 82% 全可达与 18.1% 双类件已能推导，但读者不应自行补算。

### Language / Layout

- “场”“风险场”“可达性场”建议在首次出现处统一为一个主术语，避免编辑将其理解为连续物理场。
- 英文摘要中 `ray-visible but unreachable by the finite tool` 应注明是固定离散方向集下的代理统计。

## Dimension Scores

| Dimension | Score | Descriptor | Notes |
|---|---:|---|---|
| Originality (20%) | 70 | Adequate | 对象和闭环新，但与既有神经可达性方法的独立增量需更尖锐 |
| Methodological Rigor (25%) | 70 | Adequate | 证据链完整，交叉验证命名和固定条件范围需修正 |
| Evidence Sufficiency (25%) | 72 | Adequate | 数据、图表和失败分析充分；缺少独立任务效用验证 |
| Argument Coherence (15%) | 82 | Strong | 论证链清楚，贡献定位仍可压缩 |
| Writing Quality (15%) | 80 | Strong | 中文技术表达成熟，部分概念重复 |
| **Weighted Average** | **74.8** | **Major Revision** | 主要阻碍是贡献定位和泛化范围，而非稿件结构崩溃 |

