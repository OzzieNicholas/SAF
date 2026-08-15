# SAF 参考文献与引用语境核验记录

核验日期：2026-08-15  
适用文稿：`deliverables/paper/paper.md`  
规范书目：`deliverables/paper/latex/references.bib`  
核验范围：18/18 条书目存在性与字段准确性，15/15 个正文引用语境，全部正文—书目双向映射

## 1. 核验规则

1. 每条保留文献必须支撑正文中的明确论证角色，不为凑数量或迎合未知期刊加入礼节性引文。
2. A0 使用 Semantic Scholar API 作辅助批量检查；A1 使用 DOI 注册系统或 arXiv 官方记录确认存在性；A2 逐字段核对题名、完整作者、载体、年份、卷期、页码或文章号、DOI/稳定标识。
3. 出版社页面受验证码、超时或反自动化策略限制时，不把“页面未打开”误记为“书目不存在”，也不声称读取了受阻全文。
4. Phase B 不以题名相似代替语义支持：正文主张必须落在来源题名、摘要、官方页面或可访问预印本实际覆盖的范围内。
5. `references.bib` 不含推测字段、`et al.`、占位符或未核实的中文候选；Crossref 查询只发送公开 DOI，不发送稿件正文、实验数据或私有文件。

## 2. A0 辅助 API 结果

Semantic Scholar DOI/arXiv 批量查询仅在前 7 个请求得到结构化响应，后续持续返回 HTTP 429。为避免把“先成功的条目”选择性包装成完整核验，A0 的本轮整体状态记为 `API_UNAVAILABLE (rate limited)`，不使用其部分响应承担存在性裁决。18 条文献全部继续执行 A1 和 A2。未启用外部模型交叉核验，也未向任何外部模型上传未发表稿件或稿件元数据。

## 3. A1 存在性与 A2 字段准确性

下表“查询”是本轮实际采用的精确标识查询；Crossref 链接返回 DOI 注册元数据，arXiv 链接返回官方记录。所有 A1 条目均为 `VERIFIED`，无 `NOT_FOUND` 或 `MISMATCH`。

| # | BibTeX 键 | A1 精确查询与证据 | A1 | A2 逐字段结果 |
|---:|---|---|---|---|
| 1 | `jiang2018support` | `GET DOI 10.3390/jmmp2040064` → [Crossref](https://api.crossref.org/works/10.3390/jmmp2040064) | VERIFIED | 题名、Jiang/Xu/Stringer、期刊、2018、2(4)、文章 64、DOI 一致。MDPI 页面本轮超时，未声称读取全文。 |
| 2 | `nelaturi2019automatic` | `GET DOI 10.1016/j.cad.2019.05.030` → [Crossref](https://api.crossref.org/works/10.1016/j.cad.2019.05.030)；[arXiv:1904.12117](https://arxiv.org/abs/1904.12117) | VERIFIED | 完整作者、题名、Computer-Aided Design、2019、115、135--146、DOI 一致。 |
| 3 | `mirzendehdel2021orientation` | `GET DOI 10.1016/j.cag.2021.07.011` → [Crossref](https://api.crossref.org/works/10.1016/j.cag.2021.07.011) | VERIFIED | 三位作者、题名、Computers & Graphics、2021、99、247--258、DOI 一致。 |
| 4 | `mirzendehdel2022topology` | `GET DOI 10.1016/j.cad.2021.103117` → [Crossref](https://api.crossref.org/works/10.1016/j.cad.2021.103117)；[arXiv:2107.07686](https://arxiv.org/abs/2107.07686) | VERIFIED | 三位作者、题名、Computer-Aided Design、2022、142、文章 103117、DOI 一致。 |
| 5 | `huang2019surfel` | `GET DOI 10.1007/s00170-019-03792-1` → [Crossref](https://api.crossref.org/works/10.1007/s00170-019-03792-1)；[Springer](https://link.springer.com/article/10.1007/s00170-019-03792-1) | VERIFIED | 完整作者、题名、期刊、2019、105(9)、3593--3604、DOI 与 Springer 页面一致。 |
| 6 | `zhong2025deepmill` | `GET DOI 10.1145/3721238.3730657` → [Crossref](https://api.crossref.org/works/10.1145/3721238.3730657)；[arXiv:2502.06093](https://arxiv.org/abs/2502.06093) | VERIFIED | 完整作者、题名、SIGGRAPH Conference Papers '25、2025、1--11、DOI 一致；ACM 页面受 Cloudflare 限制。 |
| 7 | `harabin2023deep` | `GET DOI 10.1016/j.cad.2023.103556` → [Crossref](https://api.crossref.org/works/10.1016/j.cad.2023.103556)；[arXiv:2409.02115](https://arxiv.org/abs/2409.02115) | VERIFIED | 三位作者、题名、Computer-Aided Design、2023、163、文章 103556、DOI 一致。 |
| 8 | `park2019deepsdf` | `GET DOI 10.1109/CVPR.2019.00025` → [Crossref](https://api.crossref.org/works/10.1109/CVPR.2019.00025) | VERIFIED | 完整作者、题名、CVPR 2019、165--174、DOI 一致。 |
| 9 | `mescheder2019occupancy` | `GET DOI 10.1109/CVPR.2019.00459` → [Crossref](https://api.crossref.org/works/10.1109/CVPR.2019.00459) | VERIFIED | 完整作者、题名、CVPR 2019、4455--4465、DOI 一致。 |
| 10 | `peng2020convonet` | `GET DOI 10.1007/978-3-030-58580-8_31` → [Crossref](https://api.crossref.org/works/10.1007/978-3-030-58580-8_31)；[Springer](https://link.springer.com/chapter/10.1007/978-3-030-58580-8_31) | VERIFIED | 完整作者、题名、ECCV 2020、523--540、DOI 一致；采用正式会议版本而非重复引用预印本。 |
| 11 | `willis2021fusion` | `GET DOI 10.1145/3450626.3459818` → [Crossref](https://api.crossref.org/works/10.1145/3450626.3459818) | VERIFIED | 完整作者、TOG、2021、40(4)、1--24、DOI 一致；Crossref 将主标题与副标题分字段保存，合并后与 BibTeX 一致。 |
| 12 | `zhou2016thingi10k` | `id_list=1605.04797` → [arXiv Atom](https://export.arxiv.org/api/query?id_list=1605.04797)；[arXiv:1605.04797v2](https://arxiv.org/abs/1605.04797) | VERIFIED | Zhou/Jacobson、题名、2016、v2、稳定 URL 一致；该条无 DOI，访问日期统一为 2026-08-15。 |
| 13 | `li2024cdf` | `GET DOI 10.15607/RSS.2024.XX.131` → [Crossref](https://api.crossref.org/works/10.15607/RSS.2024.XX.131) | VERIFIED | 完整作者、题名、Robotics: Science and Systems XX、2024、DOI 一致；RSS 落地链接异常不影响 DOI 注册记录。 |
| 14 | `qu2025inf3dp` | `GET DOI 10.1145/3763354` → [Crossref](https://api.crossref.org/works/10.1145/3763354) | VERIFIED | 完整作者、题名、ACM TOG、2025、44(6)、1--18、DOI 一致。 |
| 15 | `dutta2026implicit` | `GET DOI 10.1016/j.cad.2026.104086` → [Crossref](https://api.crossref.org/works/10.1016/j.cad.2026.104086) | VERIFIED | DOI 于 2026-05-19 注册；完整作者、题名、Computer-Aided Design、卷 198、文章 104086 一致。名义出版月为 2026-09，投稿前须再次核对最终卷期。 |
| 16 | `wang2017ocnn` | `GET DOI 10.1145/3072959.3073608` → [Crossref](https://api.crossref.org/works/10.1145/3072959.3073608) | VERIFIED | 完整作者、TOG、2017、36(4)、1--11、DOI 一致；Crossref 分开的题名/副题合并后与 BibTeX 一致。 |
| 17 | `koch2019abc` | `GET DOI 10.1109/CVPR.2019.00983` → [Crossref](https://api.crossref.org/works/10.1109/CVPR.2019.00983) | VERIFIED | 完整作者、题名、CVPR 2019、9593--9603、DOI 一致。 |
| 18 | `wu2021deepcad` | `GET DOI 10.1109/ICCV48922.2021.00670` → [Crossref](https://api.crossref.org/works/10.1109/ICCV48922.2021.00670) | VERIFIED | Wu/Xiao/Zheng、题名、ICCV 2021、6752--6762、DOI 一致。 |

## 4. Phase B 引用语境核验

正文共有 15 个实质性引用簇，全部核验，覆盖率 100%（高于 Stage 2.5 的 30% 要求）。`SUPPORTED` 表示来源实际覆盖正文的限定主张，不表示本文方法或结果因此获得外部验证。

| ID | 正文位置与引文 | 被核验主张 | 语境证据 | 判断 |
|---|---|---|---|---|
| B01 | 引言第 1 段 [1] | 支撑带来材料、时间和后处理负担 | Jiang 综述题名、摘要与主题范围 | SUPPORTED |
| B02 | 引言第 1 段 [2] | 自动去支撑需考虑接触区接近和工具—零件碰撞 | Nelaturi 正式题名与 arXiv 摘要 | SUPPORTED |
| B03 | 引言第 3 段 [3--4] | 可接近支撑体积和多轴去支撑是理论前身 | 两篇正式题名、摘要与研究对象 | SUPPORTED |
| B04 | 引言第 3 段 [5--7] | Surfel CNN、DeepMill、单形状隐式可达性分别构成神经近邻 | Springer 页面、DeepMill/Harabin 摘要及正式书目 | SUPPORTED |
| B05 | 相关工作 2.1 [1--2] | 支撑代价与后处理碰撞关系 | 与 B01/B02 相同来源，正文已限定为几何接近性 | SUPPORTED |
| B06 | 相关工作 2.2 [3--4] | 可接近支撑进入方向选择和拓扑设计 | 正式题名、摘要、研究对象 | SUPPORTED |
| B07 | 相关工作 2.3 [5--7] | 三类近邻工作的对象、工具条件和泛化单元不同 | 可访问摘要和正式元数据；未作优劣排序 | SUPPORTED |
| B08 | 相关工作 2.4 [8--10] | 连续隐式查询与卷积形状条件范式 | DeepSDF、Occupancy Networks、ConvONet 正式题名/摘要与 Springer 页面 | SUPPORTED |
| B09 | 相关工作 2.4 [11--12] | Fusion 和 Thingi10K 是本文两类公开几何来源 | 两篇数据集论文的正式题名、摘要和数据描述 | SUPPORTED |
| B10 | 相关工作 2.4 [13--15] | 距离/隐式场用于配置空间查询和多轴过程规划 | RSS、INF-3DP、Dutta 正式题名和注册摘要信息 | SUPPORTED |
| B11 | 相关工作 2.4 [16--18] | O-CNN 提供稀疏八叉树表示，ABC/DeepCAD 提供 CAD 数据构造参照 | 正式题名与摘要；原“证明敏感性”措辞已收窄 | SUPPORTED AFTER NARROWING |
| B12 | 表 1 [3--7] | 最近邻工作的对象和输出分类 | 与 B03/B04/B06/B07 一致；表注明确不排序 | SUPPORTED |
| B13 | 相关工作结尾 [6--7] | 本文不主张最早神经可达性，且跨模型切分不同于逐形状训练 | DeepMill 与 Harabin 摘要/方法定位 | SUPPORTED |
| B14 | 方法 4.4 [10] | 网络采用卷积特征体加点查询的形状条件思想 | ConvONet 正式章节页面与摘要 | SUPPORTED |
| B15 | 表 3 [11--12] | 数据源名称、公开属性和实验角色 | 数据集论文 + 本项目物化清单；项目计数不由外部论文承担 | SUPPORTED |

## 5. Ghost citation 与双向一致性

- 正文使用 18 个唯一文献编号，LaTeX 使用同一组 18 个唯一 BibTeX 键；`references.bib` 也恰有 18 个条目。
- 18 条书目全部至少被正文一个实质性语境引用；不存在只进书目表、不进正文的 ghost citation。
- 正文不存在指向缺失书目的编号或键；LaTeX 编译无 undefined citation。
- 未发现 `TBD`、`TODO`、`待补`、`unknown`、虚构 URL、虚构 DOI，或以 `et al.` 代替完整 BibTeX 作者字段。
- 中文 Markdown 参考文献顺序与 LaTeX 的 GB/T 7714 数字顺序一致；Thingi10K 访问日期已统一为 2026-08-15。

## 6. 检索过但未采用

| 候选 | 决定 | 理由 |
|---|---|---|
| 王磊、卢秉恒：《我国增材制造技术与产业发展研究》 | 不采用 | 宏观产业背景不能直接支撑接触区几何问题，已有更直接的支撑综述。 |
| 李昂等：《金属增材制造技术的关键因素及发展方向》 | 不采用 | 与核心几何判据关系较弱，候选记录页码不完整。 |
| 《增材制造自支撑设计综述》 | 不采用 | 候选记录缺作者、卷期和页码，未取得权威完整书目。 |
| 刘博宇、王向明等：《面向金属增材制造的拓扑优化设计研究进展》 | 不采用 | 正文已有更直接的可接近支撑拓扑优化原始论文，候选作者列表未核全。 |
| 未定位目标期刊的“礼节性引用” | 不采用 | 目标期刊尚未选择；投稿策略不能替代论证相关性。 |

## 7. 核验结论与限制

18/18 条参考文献 A1 `VERIFIED`，A2 字段一致；15/15 个实质性引用簇均得到来源支持，其中 B11 在审计中主动收窄后通过。未发现伪造、错配、拼接书目、ghost citation 或正文主张超出来源范围的剩余问题。

本记录使用 DOI 注册元数据、arXiv 官方记录、可访问出版社页面和公开摘要，不把受阻页面视为已读全文。Semantic Scholar 因 429 限流未作为裁决依据；Crossref/网页核验也不能替代作者在正式投稿前对每篇原文的最终人工复核。
