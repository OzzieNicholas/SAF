# decisions

<!-- 裁决台账。实质不可改、修辞可策展（政策见 D-014）：每条决策的结论与依据实质一经接受不回改,
     被推翻只能新增一条并标注 supersede（不回删）；失效路径/机器路径/迁移期黑话/外部名/日期/笔误等修辞可就地策展,历史归 git。
     课题状态靠这份 + git log,不另开总览；时间归 git,决策不写日期。
     格式:## D-00N <一句话结论> / - 裁决 / - 依据 / - 状态 -->

## D-000  迁移到"结构化课题 + 门先于码"，docs/ 编号散文退役为只读参考

- 裁决：SAF 从 `docs/` 编号散文范式迁移到结构化课题布局（治理台账 + 验收门 + 实现包 + 产物目录）；操作真源从"散文同步"改为"决策台账 + 会跑的门"。`docs/0_–3_` 的操作性内容蒸馏进治理层；`docs/` 物理保留、退役为**只读参考**，不再作操作真源，不 renumber、不新增 `docs/4_`。
- 依据：不建文档群、不靠散文同步规格；一个事实一个家。
- 状态：接受（命名/布局细节后由 D-006 收敛为 src-layout；范式实质——结构化、门先于码、旧编号文档退役——仍有效）

## D-001  可达性主判据 = 语义 C（多方向直线插入无碰撞）

- 裁决：点 p 可达 ⟺ 存在某方向，工具沿直线从无穷远逼近 p 而不碰撞；任意方向皆碰撞则不可达。弃语义 A（局部可容纳，盲腔误判可达）、弃语义 B 作主判据（连通路径，踩运动规划边界，仅进阶讨论）。
- 依据：`docs/1_§10` 三判据对照（盲腔判例）；DeepMill[R6] 不可达点定义；IMF[R3] 多朝向最优碰撞测度同族。
- 状态：接受

## D-002  基板不建模；工具从下半球任意方向逼近；oracle 只计零件本体遮挡（=遮挡下界）

- 裁决：碰撞场景**不放地面/基板**；对下朝支撑接触点，工具可从外侧（下半球）任意方向逼近；oracle 仅以零件本体几何为遮挡体。给出的是遮挡**下界**。
- 依据：语义 C 下若引入基板会挡住整个下半球，使所有下朝面翻为不可达、标签性质反转；本课题定位几何代理、工具近似手工/打磨（常在拆板后）；是 `docs/1_§12`、`docs/3_§6.8`"遮挡下界"局限的**显式化**（原局限清单未点明基板，此条补齐）。
- 状态：接受（**须写入论文局限**：仅零件本体遮挡下界，未建模基板、支撑间相互遮挡与移除顺序）

## D-003  oracle 实现口径 = 体素/距离场腐蚀（工具半径摊销）+ 边界带精确胶囊细化

- 裁决：在体素/距离场上计算——对实体做一次无符号距离变换，阈值 r 得"腐蚀自由场"；点 p 沿方向 v 可达 ⟺ 从 p+r·v 沿 v 到无穷远的射线整段落在腐蚀自由场（= 栅格 ray-march）。半径对所有点一次摊销。栅格分辨率决定不了的薄层判为"边界不确定"，用精确胶囊-网格求交细化。禁用裸网格逐点逐方向胶囊求交作主口径（10⁹–10¹⁰ 量级）。
- 依据：与 IMF Minkowski 腐蚀同源（`docs/2_§5.2`、`docs/1_§10.1` 语义 B 描述）；把预算从"每点每方向一次胶囊测试"塌成"一次距离变换 + 廉价栅格步进"，GPU 友好；边界带机制解释了三层标签中的"边界不确定"（`docs/1_§12.1`）。
- 状态：接受（连续数值 voxel_res / epsilon / 方向数见 `conf/params.yaml`，为**临时值**，阶段"标签质量审核"六项趋势通过后另立 decisions 冻结）

## D-004  第一版标签 = 二分类可达/不可达

- 裁决：MVP 用二分类；分档可达性、截断余量、连续有符号余量为进阶，第一层不稳定不进更高层。
- 依据：`docs/3_§6.4`——更易审核、与 baseline 比较、形成闭环，不被追问余量物理意义。
- 状态：接受

## D-005  工具 = 球模型、方向灵活

- 裁决：主实验用球模型、方向相对灵活（近似手工/打磨）。方向受限工具（特定角度铣削/切割头）判据收窄为"受限方向集合内是否存在无碰撞直线插入"，作进阶变体，不进 MVP。
- 依据：`docs/1_§10.5` / `docs/3_§3.6`。
- 状态：接受

## D-006  语义化重命名 + 收敛为标准 src-layout（supersede D-000 的命名部分）

- 裁决：把 D-000 的结构收敛为主流 src-layout：治理散文归 `charter/`（problem/constraints/decisions/…）；验收层 `tests/acceptance/`（性质/变形/差分/已知答案）+ `tests/gate.py`（棘轮门）；唯一 py 包 `src/support_accessibility/`；配置 `conf/params.yaml`（Hydra）。并把验收层从占位升级为"决策↔性质"映射骨架（见 `charter/README.md` 映射表）+ 文档机检 `tests/acceptance/test_charter.py`。
- 依据：命名去黑话（读者语言）；多个 py 根收敛为"一个包 + tests/"，根保持浅（主流 src-layout / Cookiecutter-DS / Hydra）；把文档断言机检升级到"机检科学决策"。
- 状态：接受（supersede D-000 的**命名/布局**部分；D-000 的范式实质仍有效）

## D-007  开发环境 = conda-forge + Python 3.12（env 名 sfa）

- 裁决：用 conda（miniforge）建环境 `sfa`：python=3.12 + conda-forge 的 igl/numpy/scipy/trimesh/pytest/hypothesis。**canonical 源 = `environment.yml`**（`conda env create -f environment.yml` 可复现）；`pyproject.toml` 只列抽象 pip 依赖(numpy/scipy/trimesh)+dev(pytest/hypothesis)，不列 igl。运行期由 `tests/acceptance/test_env.py` 的 `env_ready` 门守护。
- 依据：igl（libigl）的 generalized winding number 判内外、scipy 距离变换是 oracle 口径（D-002/D-003）的直接依赖；几何栈在 conda-forge 上装最省事（pip 的 libigl 轮子易踩坑）；把环境写成机器可读 + 会检查的门，消除"环境歧义"。env 名沿用创建时的 `sfa`（后经 D-012 更正为 `saf`）。
- 状态：接受（命名部分由 D-012 supersede 为 `saf`）

## D-008  半径单调性证伪：point-touch 语义C 下不成立（经验发现）

- 裁决：不把"半径单调"（r↑→不可达集/区域只增不减）当作 oracle 不变量。原六项趋势审核的"工具半径↑→不可达区域不反常减少"criterion（见 `docs/1_§12.1`、`docs/3_§6.6`）收窄为**仅受限腔体几何适用**；一般/开放几何不成立，其行为待真实网格上复核。`test_properties::test_radius_monotonic` 不接绿（skip）。
- 依据：在 `sfa` 内对随机 occupancy 实测——per-point 违反率 label 44/200、**暴力参考 reference_label 也违反 33/300**（故非 voxel bug，是语义本身性质）；aggregate 不可达数随 r 递减（85→44）。几何原因：point-touch 下大球能从更远处够到开放面上的点，小球反因贴近表面被挡。受限案例（已知答案件盲腔）仍直觉成立（r↑→更难进→不可达）。
- 状态：接受（语义 D-001 暂不改——random speckle 非真实网格；是否因此细化"工具-可达"模型待真实几何证据。本条只如实记录并暂不接 radius 不变量）

## D-009  网格前端口径：mesh → occupancy（igl fast winding number）+ 无 CSG 用 numpy V/F 堆叠

- 裁决：真实网格 → 占据栅格用 `igl.fast_winding_number(V,F,栅格中心) > 0.5` 判内外（D-007 选定 igl 的落地）。多实体件用 **numpy 手动 V/F 堆叠**（`np.vstack` 顶点 + 面索引偏移；winding number 对不相交实体可加），**禁用 `trimesh.util.concatenate` / `apply_translation`**——本 env 下二者原生崩溃（0xC06D）。默认 resolution=48、pad=0.2；占据以 (occ, lo, pitch) 表达，查询点世界坐标经 `world_to_voxel` 转体素喂 oracle。
- 依据：实测——igl 判内外正确（box solidify fill=0.375 与解析一致）；全链 box→solidify→oracle 复现"下朝面=accessible、两盒窄间隙=inaccessible"；无 manifold3d/blender 故不能布尔挖洞；trimesh concat/translate 稳定崩溃、numpy 堆叠稳定。
- 状态：接受（本片仅 mesh→occupancy + 已知答案复现；支撑接触区提取【法向·d 悬垂】、真实数据集接入属后续小片）

## D-010  支撑接触区提取判据：下朝悬垂面 S(P,d) = { n·d̂ < -cos(θc) }

- 裁决：给网格(V,F)+构建方向 d，支撑接触区代理 S(P,d) = 外法向 n 满足 `n·d̂ < -cos(radians(θc))` 的面集合，θc=`overhang_angle_deg`=45（conf/params.yaml）。外法向用 numpy cross（探针验证与 trimesh outward 一致），MVP 用悬垂面**质心**作支撑接触点；评价可达性时质心沿外法向外移 ~2 体素到自由侧作查询点。S 随 d 变（docs §9.2）。
- 依据：docs §9.1 定义"外法向与 d 夹角超阈值 ⟺ 局部倾角<自支撑临界角"；探针（box）：d=+z→底面2面(n·d=-1)、d=+x→-x面、tilt 45°边界干净、numpy cross==trimesh outward、无崩溃。
- 状态：接受（本片仅提取 + box 验证；真实网格法向缠绕修复、更密表面采样、真实数据集属后续小片）

## D-011  尺度不变经整数上采样证伪：分辨率依赖、非严格不变量（经验发现）

- 裁决：不把"尺度不变"（整数上采样 k×，label 不变）当作 oracle 不变量。`test_properties::test_scale_invariance` 不接绿（skip），`checks()` 记 pending。真实分辨率稳定性留待足够细的真实网格复核。（本条起决策不再写日期——身份靠 ID、因果靠 supersede、时间归 git；去日期与生成式状态的完整治理范式详见 D-012、D-014。）
- 依据：Hypothesis 随机搜索抓到反例（如 seed=91102904）——粗网格(N³)判 accessible，2× 上采样(2N³)判 inaccessible，且 r±ε 邻域全程不一致（robust 违反、非边界噪声）。根因：粗网格漏判"欠分辨薄特征"（误判可达），细网格纠正为不可达；故"尺度不变"实为分辨率稳定性，粗网格不够细时会真错。与 radius（D-008）同类：以为是不变量、实则不是。此前的绿是运气（有限种子未撞上）。
- 状态：接受（语义 D-001 暂不改——合成 speckle 非真实网格；是否因此细化"工具-可达"模型待真实几何证据。本条只如实记录并暂不接 scale 不变量）

## D-012  治理基础设施化 + 命名/文档/CI 口径（supersede D-007 命名部分；退役 charter/reference/ 期望）

- 裁决（本次治理重设计逐项冻结）：
  1) **环境改名 `sfa`→`saf`**（对齐项目名 SAF）。canonical 源 environment.yml `name: saf`；**supersede D-007 的命名部分**（D-007 正文的 `sfa` 作历史 token 保留）。
  2) **富参考家 = 顶层 `docs/`**（已 git 跟踪）：`test_charter::check_reference_docs` 认 `docs/`，`check_no_stale_paths` 去 `docs/` token；**退役 gitignored `charter/reference/` 期望**（本机可留镜像，clean clone/CI 以 docs/ 为准）。
  3) **CI = conda/environment.yml 忠实栈**：`.github/workflows/gate.yml` 用 setup-micromamba 建 `saf` 跑 gate+pytest；CI 成败以 **pytest**（回归信号）为准，`gate.py` 全程 RED（budget/regression 恒 PENDING）只作 job-summary 展示、不决定 CI。
  4) **决策去日期**（D-011 起）：身份靠 ID、因果靠 supersede、时间归 git；`check_decisions_schema` 不再要求"日期"子串。
  5) **状态生成、非手抄**：`gate.py --format md` 渲染 STATUS（CI 写 `$GITHUB_STEP_SUMMARY`，本地 `--format md`）；`charter/README.md` 映射表**删手写"现状"列**，状态一律回落门。
  6) **未决触发册** `charter/open.md`（前置条件→义务、无日期）：`test_open` 接进门——未决项 surfaced 为门项、机器可判者附注休眠/可闭合（人肉提醒→门提醒）。
  7) **完整性入门**：`test_charter::check_decisions_covered`——每条 D-0NN 须被验收层引用或在结构 allowlist（D-000/004/006/012），杜绝孤儿决策。
  8) **record.md 退役**为非权威指针（状态跑门 / 为什么看 decisions / 地图看 charter/README / 未决看 open.md）；权威三分工不变。
- 依据：本会话实证——① 云端数秒复现 saf 环境、gate+pytest 全跑（几何全绿、solidify IoU=1.000），验证器可移植上 CI；② record.md 手抄状态/地图/理据违反 charter 自立"一个事实一个家、指针不复制"，且实测漂移（写 test_charter GREEN 而 clean clone 为红、scale 写 GREEN 实为假绿）；③ 命名 sfa 系笔误。用户确认全取推荐项（追加决策 / conda 栈 / docs 家 / 去日期）。
- 状态：接受（判定语义/oracle 口径 D-001..D-005/D-009/D-010 分毫未动；本条只碰治理·工具·CI·文档层。§6 的 `open.md`/`test_open` 后由 D-013 更名为 `deferred.md`/`test_deferred`）

## D-013  动作与规范纳入治理：Conventional Commits + 分支生命周期 + 治理文件命名（有牙）

- 裁决：
  1) **Commit 规范** = Conventional Commits `<type>(<scope>): <主题>`，type∈{feat,fix,refactor,test,docs,ci,gov,data,exp,chore,revert}（用 `feat` 非 `add`）。
  2) **分支** = `<type>/<slug>`；豁免 main/默认分支与 `claude/*`（harness agent 分支）。生命周期：一分支一事 → CI 绿 → PR（模板）→ 评审 → **squash-and-merge** → 删分支；main 保护 require-CI-green（GitHub 侧开关）。
  3) **治理文件命名**：名直呈角色；`open.md`→`deferred.md`（decisions 的未决半）；**删退役的 `record.md`**（"record"滑向日记——状态看门、地图看 README）。原则见 conventions.md §3。
  4) **强制有牙**：`tools/check_conventions.py`（纯 stdlib，spec 唯一之家）= CI `conventions.yml` + 可选本地 hooks；自 conventions.md 引入起强制，之前 bootstrap 提交祖父豁免（不改写历史）。`tests/gate.py` 守工作树真相、本规范守 git 历史，分工不混。
  5) **workflow-done-DoD 定义**（闭合 deferred 该项的义务）：exit = 除 budget/regression 门外 gate 全绿 + conventions CI 绿 + gate.yml CI 绿。当前未达（几何/数据/指标多项 PENDING），deferred 该条保留、义务已明。
- 依据：用户要求"一切动作与规范都进治理"，并指出 open.md 等命名不清；沿用治理"有牙、一个事实一个家、读者语言"原则；三个实现选择由用户委托取最推荐（Conventional Commits / squash / CI+hooks）。
- 状态：接受（判定语义/oracle 口径未动；本条只碰治理·工具·CI·文档层。commit 规范自本条引入起强制，之前提交祖父豁免）

## D-014  台账策展政策：实质不可改、修辞可策展（放松 D-000 起的"只增不改"）

- 裁决：`decisions.md` 从严格"只增不改/永不回改"放松为**"实质不可改、修辞可策展"**——每条决策的**结论与依据实质**一经接受不回改，被推翻只能新增一条 + supersede（不回删）；但**失效路径、机器特定路径、迁移期黑话、外部工具名、日期、笔误**等修辞层可就地清理，历史由 git 保全。据此对 D-000..D-013 做一次策展：去日期；`reference/N_…`→`docs/N_…`（citation 指针，富参考家 = docs/，见 D-012）；去 `D:\…` 绝对路径；去 `ffm §9`/`运行协议`/`Path C`/`清单N` 迁移考古（D-000、D-006 精简为耐久实质）。**oracle 判定语义 D-001..D-005 / D-009 / D-010 的裁决实质分毫未动**；ID 不 renumber、supersede 链不断；D-007/D-008 的 `sfa`、D-012/D-013 的 `open.md` 等"经 supersede 记录的历史名"按既定保留。
- 依据：严格只增不改会让台账累积失效指针与迁移噪声（本会话实证：`reference/` 指向已不存在的目录、`D:\…` 机器路径、外部项目名 `ffm`、逐条日期），与治理自立的"读者语言、一个事实一个家、时间归 git"相冲。把"不可回改"精确到**实质**层：既护住科学决策不可篡改，又让台账保持可读、不漂移；真实历史全在 git，无损。
- 状态：接受（本条只碰台账修辞层 + 本策展批次；判定语义/oracle 口径未动）

## D-015  主线 = oracle 真值 + 形状条件神经跨模型预测；几何启发式作对照基线（闭合 geometry-vs-neural-mainline）

- 裁决：课题主线 = "几何 oracle 生成可达性真值 → 形状条件神经场在**未见模型**上预测"这条完整管线；几何启发式（支撑面积、无工具半径射线可见性、局部规则）居**对照基线**位而非竞争主线位。神经预测采成熟方法（非首创，DeepMill 在先）；贡献在问题定义（AM 支撑接触区可达性）+ oracle 口径 + 跨模型预测落地与基线对照。
- 依据：闭合 deferred「geometry-vs-neural-mainline」——触发（几何验收全 PASS）已到、义务（重议主线）由用户认可推荐达成；evidence.md 定位（神经采用非首创、空白在对象层）；H1/H2 要求几何基线作对照以证问题非平凡，故基线入"对照"位。Phase-1 薄纵切给了可行性证据（程序化留出件不可达 F1≈1.0，胜多数类基线），但那是**受控干净任务**、非最终 benchmark；主线真凭据待基线对照 + 更硬几何 + 真实数据。
- 状态：接受（判定语义/oracle 口径未动；本条定研究主线与基线角色，不改任何几何判据）

## D-016  数据架构 = 原料(外部只读)→流水线→统一 processed 数据集；程序化件为首个物化源

- 裁决：项目数据分三层——① 原料（程序化=种子配方；ABC/Thingi=外部只读网格，路径经本地配置不入库）；② 流水线（合格性→归一→体素化→下朝点提取→oracle 打标→装配/按模型切分）；③ 统一 processed 数据集：每模型一个 `.npz`{occ,points,labels} + `manifest.csv`（全标量元数据，单一之家）+ `dataset.json`（provenance，无时间戳，保证字节可复现）；源标签 {procedural,abc,thingi10k} + 切分 {train,val,test}（Thingi10K 恒 test）。首片只物化**程序化源**（oracle 造即知答案、可信、无矩阵乘、本地可验），落 `data/processed/`；ABC 接入、Thingi 接入、DVC 编排、路径配置作未决项（见 `deferred.md`），触发到齐再建。统一记录格式经本片冻结，ABC/Thingi 须对齐。
- 依据：铁律#6 标签先于模型——oracle 在真实/薄/脏网格上有效性未证（`point-touch-refine`），故本片不接真实数据；实测 ABC 现仅 3 薄板样例（非真 ABC 数据集）、Thingi 为跨域测试专用且需缠绕修复，均未就绪；DVC 未装、Hydra 未接线、`params.yaml` 仅文档——首片用纯可复现 CLI + 验收门即可复现，DVC 待昂贵/真实源落地再引入才有价值；复用 `LabeledModel`/`make_dataset`/`split_by_model`/oracle，不重造。
- 状态：接受（判定语义/oracle 口径 D-001..D-010 未动；本条定数据架构与首片边界，结构决策）

## D-017  主数据源 = Fusion 360 Gallery reconstruction 网格（仅网格用途）；ABC 退为可选背景（extend D-016 source 枚举）

- 裁决：公开 CAD 主源从 ABC[R18] 换为 **Fusion 360 Gallery reconstruction 数据集[R20] 的三角网格（.obj）**——只用其最终零件网格，**不使用** sketch/extrude 构造序列（.json）与 B-Rep（.smt/.step），故 `docs/2 §9.3`「勿沦为 CAD 序列建模」之虑不触发。D-016 的 source 枚举 {procedural, abc, thingi10k} **扩为** {procedural, fusion360, abc, thingi10k}；ABC 从「主训练源」降为「可选/背景」（其接入未决项由 fusion360-ingest 取代，见 deferred）。Thingi10K 角色不变（恒 test 跨域）。
- 依据：ABC 下载不便（用户实测多次不成）；Fusion 360 Gallery reconstruction = 8,625 个 sketch+extrude 生成的干净 CAD 实体，含拉伸挖出的凹槽/盲孔/通孔（正是支撑接触区可达性想要的受限特征），每设计带 .obj 三角网格（面按 B-Rep face ID 标注），单位 cm、经 geometry.normalize 归一后无量纲差；CAD 派生通常水密流形，比 Thingi10K 少缠绕修复。局限：棱柱几何为主、无自由曲面（下朝面多为平面+凹槽天花板）——须写入论文数据代表性；可能多体（按 `docs/3 §4.8` 筛单体或 numpy 堆叠占据）。仅用网格不碰构造序列，故非 CAD 序列建模。
- 状态：接受（判定语义/oracle 口径 D-001..D-010 未动；本条只碰数据源与 D-016 source 枚举，结构决策。R18/R20 角色更新见 evidence.md）

## D-018  命门人签收 + 无外部评审替代（新增铁律 #7）

- 裁决：把「命门门」显式化为需**人签收**的门——命门 = { 判定语义（D-001..）、真实网格上的标签质量、企业隔离/不过度声称的边界纪律 }；自动化（含 agent 循环）只在**独立可信门**（构造即知答案件、差分对拍等，其真值不依赖被测物）下迭代到绿，**不得关闭命门**（防「假绿」，D-011 教训）。因本课题**无导师/合作者**充当 oracle 定义评审，命门签收的替代 = **文档化可视化审计（viz 热图 montage）+ 机器可判的趋势门证据**，由作者本人据实签收；未签收的真实网格标签**不进训练集**（铁律 #6 的落地）。新增 constraints.md 铁律 #7。
- 依据：工作流审查结论——SAF 治理本身即「决策→会跑的门→码→棘轮」这套动作规范，采用只需补「命门人签收」一条并明写反假绿；用户确认无外部评审，故以厚可视化 + 趋势证据替代人评审。viz 是此签收的仪器（本批补齐），故属命门前置。
- 状态：接受（判定语义/oracle 口径未动；治理层决策，无专属性质，由 test_charter 结构 allowlist 守护）

## D-019  新增 charter/roadmap.md 作研发弧位置图（现状看门、状态不手写）

- 裁决：新增 `charter/roadmap.md`，**唯一拥有**「研发弧阶段标签（阶段0–10 / E0–E8 逻辑标签）＋一行当前位置＋推进/降级分支」；其余一律指针委托——现状→`tests/gate.py`（`--format md` STATUS）、未决义务→`deferred.md`、裁决→`decisions.md`、弧富全本→退役只读 `docs/0`（指向、不复活为操作真源、不删）。roadmap **不手写任何门状态**（禁门图标 / 独立裁决词 / 状态列头），只在**阶段边界**更新。配套 wiring：`README.md` 阅读顺序 + 决策↔性质映射加指针；`conventions.md §3` 文件-角色表加行；`test_charter::check_roadmap` 守护（纳入 `check_no_stale_paths` 扫描 ＋ 断言无手写状态 token；引用 D-019 故非孤儿，非结构 allowlist）。
- 依据：`docs/0`（弧富全本）经 D-000/D-012 退役只读、又被 `check_reference_docs` 钉住存在（不可删、不可复活为操作真源）；`deferred.md` 结构上只存未决半（闭合即删），表达不了当前位置；`gate` STATUS 是唯一活现状，但不表达「弧上哪」这一编辑判断。三者皆无「我在弧上哪」之家 → 循「一个事实一个家」给它薄家，以「指针不复制／状态看门不手写」守住不重蹈 `record.md`（D-012§8 / D-013§3 的假绿·日记）覆辙。属治理结构新增，循 D-012/13/14 冻结模式。
- 状态：接受（判定语义/oracle 口径 D-001..D-010 未动；本条只碰治理结构层，由 `test_charter::check_roadmap` ＋ 引用守护，非孤儿）。

## D-020  D-003 边界带精确胶囊-网格细化落地（有网格三态、无网格二分不变）

- 裁决：实现 D-003 早冻结但未落地的"边界带精确胶囊-网格求交细化"。口径：体素腐蚀 ray-march 给每方向最小净空 clearance；**无网格**（程序化合成占据）→ 二分（任一 clearance>r 即可达，与细化前逐比特一致、程序化管线不退绿）；**有网格**（真实 CAD，传 V,F,lo,pitch）→ 三态——clearance>r+ε 明确可逃逸→可达；含糊方向（clearance>r-ε）交精确胶囊测试（半无穷射线到三角网格最小距离 ≤ r_world，无离散误差）定夺，任一无碰撞→可达；皆碰→不可达。细化给真值而非隔离，故不出 UNCERTAIN。ε=epsilon_voxels（conf/params.yaml）。原语 `src/…/oracle/capsule.py`（Ericson 点-三角/段-段最近点 + Möller–Trumbore 穿越），判定 `decide_label`。
- 依据：真实 CAD 下 point-touch 语义在物理临界点（工具半径≈局部特征尺度）体素标签 res-不收敛（实测固定世界查询点、res 48↔96↔192 翻 ~10-13%，与 D-011 同族）；纯提高分辨率不收敛且单卡成本高。精确细化验证：同样本细化后 res 48/96/192 标签一致率 **1.000**（纯体素 0.865/0.899）——边界点精确、res-无关，故**低基础分辨率 + 细化即得 res-稳定训练级标签**，缓解单卡预算。语义 C（D-001）与遮挡下界（D-002）分毫未动，本条只落地 D-003 的细化机制并定其操作口径。命门相关（改 label 输出口径），须作者据实**人签收**（铁律 #7）：本批已 TDD（capsule 5 + decide 5 已知答案）+ 真实 CAD res-稳定验证；真实网格标签按冻结参重采并签收后方进训练。
- 状态：接受（判定语义 D-001/D-002 未动；落地 D-003 并定操作口径；守护性质 `test_capsule` 接门）

## D-021  params-freeze：冻结 conf/params.yaml 标签口径数值（n_dir=128 / res=48+细化 / radius=0.05 / overhang=45 / ε=1.5）

- 裁决：标签质量门（六项趋势 + D-020 精确细化）通过后，冻结 oracle/标签口径连续数值（原 params.yaml "临时值"）：`oracle.n_directions=128`（真实几何收敛，128-vs-256=0.982，64 尚差 5%）；`oracle.epsilon_voxels=1.5`（D-020 边界带宽）；`data.resolution=48` + **精确细化开**（D-020 令 res 48/96/192 标签一致 1.000 → 低基础 res 即训练级、单卡省）；`data.radius_world=0.05`（H2 验证工具尺寸要紧）；`geometry.overhang_angle_deg=45`（D-010）。`oracle.voxel_res=256` 作废/被 data.resolution+细化取代；`sampling.contact_points_per_model` / `tool.radii` 多值 / `labels.emit_uncertain_band` 属未来采样/敏感性扫，非本次冻结（保留待用）。
- 依据：闭合 deferred「params-freeze」——触发（六项趋势审核通过）已达：程序化六项趋势守门 + 真实数据 n_dir/res 收敛证据（D-020）+ 训练级标签人签收（D-018）。铁律 #6「标签先于模型」的正式落点：这些值一经冻结即为口径一部分，改动须新增 decisions supersede（同 D-003 连续数值条款）。已按冻结值重采真实标签并训出 H3（ConvONet-lite 未见真实件 F1=0.847±0.039）。
- 状态：接受（判定语义 D-001..D-010 未动；本条冻结连续数值，结构决策，无专属性质，由 test_charter 结构 allowlist 守护）

## D-022  D-020 实现加固（野网格可跑）+ H5 Thingi 接入采样上限（判定口径 D-001..D-021 未动）

- 裁决：为跨域 H5（Thingi10K 野网格）落地三处**实现层**改动，判定语义/口径分毫不动：
  (a) **精确胶囊细化预算** `precompute_mesh(V,F)`：把网格常量（三角/质心/外接半径/顶点包围球）每模型算一次、供该模型所有点×方向的 refine 复用（原每调用重算——对 Fusion ~400 面无碍，对 Thingi 上万面是主开销）。包围球定 far ≥ 精确 far（max‖V−origin‖），段更长只多覆盖同一半无穷射线、不引偏轴伪触——**逐比特等价**，非口径改。
  (b) **退化三角跳过**：胶囊求交跳过零面积（重合/共线顶点）三角——其边长²/面积² 恒为 Ericson 最近点原语各除法的分母，退化即除零（Thingi 野网格常见重复/共线顶点，clean CAD 无此）。零面积=度量零面、无面可触，跳过即实现 D-020 的 intended 口径（本就不与零面积面求交），对 clean CAD（Fusion/程序化）标签**零改动**。
  (c) **H5 Thingi 接入采样上限**（测试集构建，非 oracle 口径）：`build_thingi` 每模型接触点上限 `max_points=400`（密扫描件下朝面上万，全标 × n_dir × 细化不可解；确定性无放回子采样 `_select_points` 是逐点 F1 无偏估计）+ 面数上限 `max_faces=80000`（超高面 res48 占据已降采样、跳过以控 O(面数) 剪枝成本）。Thingi **恒 split=test、绝不进训练**（D-016/docs §4.6），故上限属跨域测试集范围选择、不触 oracle/标签口径冻结（D-021）。
- 依据：H5 要在野外 OOD 网格上评形状条件预测的跨域鲁棒性。(a)(b) 是让 D-020 精确细化在野网格上**可跑且不崩**的实现加固（性能 + 数值稳健），非语义变更——故不 supersede D-003/D-020，只加固实现，由既有性质守护逐比特/clean-CAD 不变。(c) 是测试集构建的可解性选择（单卡预算），Thingi 恒 test 故不与训练标签口径冲突。H5 结果：ConvONet-lite（训于 Fusion both-class + 程序化）域内留出 F1 0.915±0.005、跨域 Thingi（149 both-class 件 / 46.8k 点）F1 0.908±0.005（掉幅 0.006、在噪声内），远胜几何射线可见性基线 0.725——形状条件可达性代理跨域泛化。
- 状态：接受（判定语义/口径 D-001..D-021 未动；实现加固 + 测试集采样，守护性质 `test_capsule`(precompute_equiv / degenerate_skip) + `test_thingi`(_select_points) 接门）

## D-023  数据源定为三源（Fusion360 / Thingi10K / 程序化）——ABC 彻底弃用（supersede D-017「ABC 退为可选背景」）

- 裁决：项目数据源**收敛为三**，ABC 从「可选/背景」进一步**彻底弃用、不再接入**：① **程序化生成**（种子配方，oracle 造即知答案的受控信号集/控制变量）；② **Fusion 360 Gallery reconstruction**（[R20]，主 CAD 网格源，仅用 .obj 三角网格，D-017）；③ **Thingi10K**（[R19]，野外打印网格，跨域鲁棒性测试，恒 split=test，D-022）。据此 D-016/D-017 的 source 枚举 **{procedural, fusion360, abc, thingi10k} → {procedural, fusion360, thingi10k}**（去 abc）。本条 **supersede D-017 内「ABC 退为可选背景 / 未决项待立」那半**（D-017 的 Fusion360=主源那半不变）；D-016 数据架构三层不变，只是原料层不含 ABC。
- 依据：用户明示 ABC 数据源已无且不打算用（下载不便，Fusion360 已充分替代主 CAD 源角色）。ABC 在本仓从无接入代码（仅注释/证据/未决备注提及），故弃用=撤引用 + 撤未决备注，无代码删除。三源已各就位并经验证：程序化（D-016 首片物化 + 六项趋势门）、Fusion360（D-017/D-021，8625 设计/成功物化 8590 件 + H3 F1 0.910）、Thingi10K（D-022，300 件 + H5 跨域 0.908）。铁律 #5「只在公开/程序化数据上工作」实质不变，仅枚举例从 ABC 换 Fusion360。
- 状态：接受（判定语义/oracle 口径 D-001..D-010 未动；数据源范围结构决策，无专属性质，由 test_charter 结构 allowlist 守护；R18 ABC 角色更新见 evidence.md，per-源接入仍由 test_dataset/test_fusion360/test_thingi 守护）

## D-024  方向级可达性场（E5）：oracle 输出扩为每方向可达向量，extend D-004（二分 = any-归约）

- 裁决：把 oracle 输出从**点级二分**（D-004）扩为**方向级可达性场**——对固定下半球逼近方向集（`lower_hemisphere_dirs(n)`，n=128→D=64 方向），每点输出每方向是否可达的向量。**判据分毫不变**（同 D-001..D-003/D-005：clearance>r，有网格三态含糊交精确细化 D-020），只是**不 OR 归约**、保留每方向结果。`oracle.direction_labels(p,r)` + `decide_direction_labels`；模型侧 `ConvONetLite` 加 `out_dim`（=D，默认 1 向后兼容 H3/H5）。**核心不变量**：`any(direction_labels) == (label==ACCESSIBLE)`——二分口径 D-004 是本场的 any-归约，既有二分标签/模型不受影响。
- 依据：项目命名的「Support Accessibility **Field**」本义即方向级；点级二分是其 any-归约特例。用户明示走 E5（命门=oracle 输出口径变更，铁律 #7，已据实点头）。因判据（D-001..D-003/D-005）与二分语义（D-004）皆未动、本条只**扩输出粒度**，故 **extend 而非 supersede**：既有性质（known_answers/differential/capsule）继续守护判据，新性质 `test_direction_field` 守护「逐方向判定 + OR-归约不变量 + 已知答案 + 模型方向头」。**E5 结果**（方向级 ConvONet-lite 跨模型预测，方向目标用占据口径 direction_labels，`tools/eval_e5.py`）：程序化 per-direction F1 0.999 / dir-set IoU 0.993；**真实 Fusion CAD（500 件 / 26.3k 点）per-direction F1 0.894±0.004 / dir-set IoU 0.875**。关键：per-direction **多数类基线 F1=0.000**（每方向多数皆"可达"、"被挡"是稀有类）——模型在稀有"被挡方向"上得 0.894，非靠先验。复原点级二分 F1 0.795（占据口径下"全方向皆挡"的 AND-归约，较专用二分头 H3=0.910 略噪，属预期：64 个含噪逐方向预测求 AND）。
- 状态：接受（判据 D-001..D-003/D-005 + 二分语义 D-004 未动；本条扩输出粒度为方向场，守护性质 `test_direction_field` 接门；命门经用户点头 develop——方向级标签若作 headline 训练源，训练前作者据实签收，同 D-018）

## D-025  真实标签有效性审核客观化：量化审核替代人工视觉签收（supersede D-018 发放机制）

- 裁决：D-018「命门人签收」的**证据机制**从"作者视觉审 audit 图"改为**客观量化审核** `tools/audit_labels.py`。真实网格标签有效性由三条可量化性质裁定，写入 dataset.json 的 `label_audit` 块并据此置 `human_signoff`（非人工视觉）：(a) 差分 robust_mismatch_rate（纯体素 oracle vs 暴力参考，**D-003 边界带容忍**）≤ 0.01；(b) res-稳定 res48_vs_res96_agreement ≥ 0.95；(c) 分布 inacc∈[0.01,0.9] 且有两类件。细化层由 `test_capsule` 精确原语守护。人的角色从"逐集视觉审"降为**一次性认可这套阈值**（本决策即认可）。
- 依据（含"度"的判断，锚定论文任务）：oracle 是显式几何**代理**（语义 C），物理精确是非目标；论文诉求 H1(可达⊥支撑面积)/H2(半径要紧)/H3·H5·E5(神经预测代理) 皆**对小幅标签噪声鲁棒**（H1 弱相关 \|ρ\|≤0.27 与大效应不翻；F1 0.91 远低于 res-噪声上限、非绑定约束——失败分析证误判恰集中在该边界带）。故"最佳度"= 可验证口径正确(差分 robust≈0) + res-稳定到结论鲁棒(97.7%) + **量化如实报告为局限**，比过度声称"完美标签"更可信；再拔高(res 96 重标 8625)将破 D-021 res=48 冻结、耗数小时单卡、重跑全实验，**换不来任何结论变化**——劣。视觉审主观、不可复现、易造假绿（fusion360_full 曾由一次性扩量脚本写 human_signoff=True 却无审计图=假绿；生产 ingest 本就写 false）。D-018 实质（命门须硬证据、不得假绿、无外部评审替代）**不变**，仅证据从视觉换量化+可复现。**fusion360_full 审核（400 采样点 / 25 件 res-稳定，n_dir=128）**：差分 robust 不一致 **0.25%**（边界带容忍 2.5%）｜res48-96 稳定 **97.7%**（1258 点）｜细化改动带 21%｜分布 inacc 5.6% / 两类件 19% / 单类件 81% → **verdict PASS**，label_audit 证据入 dataset.json。
- 状态：接受（作者授权我据论文任务代为裁定；判定语义/口径 D-001..D-005 未动，仅改 D-018 证据机制；守护 `tools/audit_labels.py` + `test_differential`/`test_capsule`/`test_label_quality`）

## D-026  预算门 + 回归门激活（阶段5 指标固化；两道量化门从 PENDING-by-design 落为实测/实验裁定）

- 裁决：把 `tests/gate.py` 中长期 PENDING 的两道门落地为量化裁定：
  **预算门**（D-003 体素口径）：冻结实测 **D0=0.0596ms**（40 件 fusion360_full 纯体素单点单方向）× MVP 规模（8625 件×38 点×128 方向×1 半径，D-021 冻结参）→ `eval.extrapolate_oracle_cost` 全量构建 **0.69h ≤ 上限 4h**（~6× 余量）→ PASS。**机器无关**（用冻结 D0 非 live 计时，避免 gate 依赖机速/不可复现），守护**规模膨胀**（改 `_BUDGET_SCALE` 至不可负担即红）；D0 换机/改口径重测须更新 `_D0_REF_MS` + append。
  **回归门**（模型级配对 + bootstrap CI）：`tools/regression_check.py` 训神经二分 + 射线可见性基线（E4），留出件上每件配对 F1，bootstrap over 件（2000×）得配对差 95%CI；下界 >0 → 神经**显著不劣于最强几何基线** → PASS。产出 `runs/regression/latest.json`（机器 emit、gitignore），gate 读之裁决；裸克隆无产出 → PENDING、跑实验后棘轮（诚实活检、非假绿）。**实测（80 留出件/2000 bootstrap）**：神经 F1 **0.915** vs 基线 **0.712**，配对差均值 0.336、**95%CI [0.241, 0.432] > 0** → 显著胜 → PASS。
- 依据：两门 D-013 早列"阶段5指标固化后启用"；现指标已固化（H1/H2/H3/H5/E5/E4/E8 全坐实），触发达。预算门用冻结 D0 而非 live 计时——gate 不应依赖机速（不可复现）；回归门读实验 emit 而非零安装重训——torch/数据不在零安装 gate 内，读机器产出是诚实活检（无产出即 PENDING、非造假绿）。二者皆不触判定口径。
- 状态：接受（作者授权据工程判断代裁；判定语义/口径 D-001..D-005 未动；预算门 self-contained，回归门守护性质 = `tools/regression_check.py` + `runs/regression/latest.json` 产出）

## D-027  引入 N/A 终态 + 工程 DoD 达成（门达 GREEN；refine D-013 §5 的 DoD 表述）

- 裁决：验收门加**终态 N/A**（`acceptance/__init__.py::na`）——某性质经检验**判定为非不变量**或**已被他处覆盖**时记 N/A：可见、附理由，**非 PASS**（不声称性质成立）、**非 PENDING**（不声称尚未做）、**不阻塞 DoD**。据此重分类长期 PENDING：`scale_invariance`(D-011 证伪)、`radius_monotonic`(D-008 证伪)、`rotation_equivariance`(D-005 体素重采样伪影) → **N/A 非不变量**；`mesh_sanity` → **N/A 已覆盖**（occ 正确性 `test_mesh_frontend` + 退化面 D-022 + 标签审核 D-025 + ingest §4.8）。`tests/gate.py` 的 GREEN 判据改为**无 FAIL 且无 PENDING**（N/A 允许）。全部未决义务闭合 → `deferred.md` 空册（`test_deferred` 记 PASS）。
- 依据：D-013 §5 定 DoD="除 budget/regression 外 gate 全绿"，但把**证伪的非不变量**与**尚未做的项**都记 PENDING，混同了两种语义——证伪的性质不是"尺子没造好"，是"这猜想经检验为假"；混同致门永远 RED、"做完"无清晰信号。加 N/A 区分二者：GREEN = 无真失败(FAIL)、无待办(PENDING)；N/A 是诚实终态（比 PENDING 更实、比 PASS 更诚，绝非把红刷绿）。现预算/回归门 PASS（D-026）、命门标签签收客观化（D-025）、全部计划实验坐实（H1/H2/H3/H5/E1/E4/E5/E8+消融），未决义务全闭合——**工程 DoD 达成、门 GREEN**。（论文=阶段9–10，归作者。）
- 状态：接受（作者授权收尾代裁；判定语义/口径 D-001..D-005 未动，仅治理门状态词 + DoD 表述；棘轮不减——真 FAIL/新 PENDING 仍即 RED）

## D-028  网格前端加固（extend D-009/D-010）：ingest 确定性 + 栅格维度 ceil 修正 + 缠绕安全外移（三态，含丢弃口径与计数）

- 裁决：对真实网格前端做三处**实现层加固**，判定语义 D-001..D-005 分毫未动，只 extend D-009（mesh→occupancy）与 D-010（下朝接触点提取）：
  1) **ingest 确定性**：`iter_final_designs` 目录遍历改 `sorted(os.walk(...))`（配既有 `sorted(files)`），跨机产出序稳定 → `split_by_model` 分配可复现。
  2) **栅格维度 ceil 修正**（D-009）：`mesh_to_occupancy` 的 `ns = ceil((hi-lo)/pitch)` 改 `max(1, ceil(· − 1e-9))`——消最大轴浮点过冲（个别输入/平台把 res 判成 res+1、破字节可复现）+ 零厚度轴不塌成空栅格；clean 立方体各轴仍 = res。
  3) **缠绕安全外移**（D-010，`mesh.nudge_to_free` 三态）：占据用 igl 缠绕数（对缠绕稳健），下朝面法向用 np.cross（缠绕敏感），二者不一致时旧的「质心沿外法向 +2 体素」可能把查询点落进实体。新口径按落点分三态——**free**（+n 自由，同旧）；**confined**（+n 实体且 −n 也实体 = 深窄槽/两体窄隙里的真下朝面 → 返回 +n 点、同旧口径、oracle 判不可达，**保留稀有不可达正类**）；**flipped**（+n 实体但 −n 自由 = 法向翻转、该面真外法向朝上并非下朝面、被悬垂判据误纳 S(P,d) → **丢弃**）。丢弃数计入 dataset.json `nudge_discarded_flipped_normal`（**不静默删除**，对齐 `docs/3 §13.3`）；fusion/thingi 同口径 + 空点集守卫（全丢→跳过件、保 (K,3) 契约）。命门审核 `audit_labels` 的 res-稳定腿同步走 nudge_to_free（审的即 ingest 实际产点），其 verdict 收紧为「须有 res-稳定腿」（缺 --root→verdict False，与拒写 signoff 一致）。
- 依据：命门相关（改 D-010 的接触点选取口径），铁律 #4 要求口径变更走 decisions 而非实现里悄改——本条补此登记。经验证据（`tools/` 离线扫 `fusion360_full` 8590 件 / 478,984 点）：**旧口径下 5.81% 点落在实体内**（27,843 = 17,117 inacc + 10,726 acc / 1368 件）；其中「实体内却判可达」的 10,726 点（2.24%）高度指示翻面伪下朝面（新口径丢弃），「实体内判不可达」的 17,117 点多为真窄隙正类（新口径保留）——故新口径**剔伪保真**、方向正确。判据语义 D-001..D-005/D-020 未动，`test_known_answers`/`test_differential`/`test_capsule` 继续守护。
- 状态：接受（判定语义 D-001..D-005 未动；本条 extend D-009/D-010 实现口径，守护性质 `test_mesh_frontend`(`mesh_nudge_to_free`/`mesh_occ_ceil_shape`, D-028) 接门）。**重物化完成记录**：① 已按本口径**重物化 `fusion360_full` + 命门重签收**（缠绕安全外移弃 **11,573** 翻面伪下朝面点=旧 2.42%，both-class 1621→**1553**；thingi_v1 弃 **4,321** 点、149→**137**；procedural 不受影响，非 mesh 路径）；重签收 verdict=True（robust 0.63% / res 97.28% / 两类 18.1%）。headline 主变化 **H3 0.910→0.882**（弃伪易样本后诚实值），余稳（H1/H2/E5/E8/消融/H5 定性不变）——新数字见 `results.md`，旧口径见 git 历史。② 相对旧口径不字节一致，三独立原因：walk 序变→split 分配变；ceil 修正→occ 形状可能变；nudge→点集变。

## D-029  控制平面与活动目录架构迁移

- 裁决：将活动治理入口统一为 `governance/`，项目通用控制平面规范置于 `docs/other/project-control-plane/`，并由 `governance/project.json` 声明 SAF 的路径、入口、检查器和能力适配。自动化与配置分别归 `tools/hooks/`、`configs/`；运行产物归 `artifacts/runs/`；论文交付物归 `deliverables/paper/`。旧目录名称不再作为活动架构路径。
- 依据：多项目复用需要稳定的控制平面契约，而产品代码、实验工具、数据和论文属于项目适配层；统一根目录能让 CI、门脚本、工具和协作者共享同一事实来源，降低路径耦合并支持按模块迁移/删除。通用规范只规定边界、事件、工作流、权限、证据和改进语义，不引入具体 Agent Runtime。
- 状态：接受（仅治理结构、路径和适配声明变化；`support_accessibility` 业务语义、冻结参数、实验结果和模型代码不变。历史决策中的旧路径文字保留为历史事实，不再作为活动引用；结构完整性由 `test_governance` 的 manifest/spec/path checks 守护）。

## D-030  研究输入、交付物与临时产物边界收缩

- 裁决：研究文献输入统一归 `docs/references/`，其中 `literature/` 保存论文 PDF、`references_cn.md` 保存候选书目；`deliverables/paper/` 只保存论文源稿、图件、构建源和最终交付物。仓库内的渲染/视觉 QA 临时目录 `tmp/` 退役并加入忽略规则。私人备忘 `method/` 仍保持非权威、非运行资产边界，不纳入本次内容改写。
- 依据：文献是研究输入而非论文输出，把它放在 `deliverables/` 会使输入、工作稿和发布物共享生命周期，造成误发布和删除耦合；`tmp/` 无活动引用且不可复现，不能成为项目资产。新边界只调整文件归属，不改变科学判定、实验结果、论文内容或私人备忘。
- 状态：接受（治理结构与资产生命周期决策；由 `test_governance` 的 manifest、交付物边界和私人备忘边界检查守护）。

## D-031  治理入口与运行产物生命周期收敛

- 裁决：删除仓库内未跟踪的个人 `method/` 目录；根级 Agent 规则统一为 `AGENTS.md`；`CLAUDE.md` 不再作为活动入口。运行产物按生命周期分为 retained evidence（`artifacts/runs/`）与可清理 cache（`artifacts/cache/`），结果写入 run envelope（run_id、输入摘要、工具版本、命令），缓存由受边界保护的 TTL 清理器管理。
- 依据：个人备忘不是项目控制平面资产，保留专用目录会形成第二套不可验证入口；运行结果既需要复现和审计，又不能让检查点、日志和候选图片无限积累。证据与缓存分离后，删除动作可以机械化而不影响 gate、论文和失败审计。
- 状态：接受（不改变 `support_accessibility` 业务语义、冻结参数、数据标签或实验结论；`test_governance`、结构检查器、artifact helper/prune 和 CI 共同守护）。

## D-032  工程中心、外部数据与论文下游包重构

- 裁决：SAF 工程保持绝对中心，工程入口固定为 `src/`、`tests/`、`tools/`、`configs/`、`governance/`；论文作为下游发布包聚合在 `deliverables/paper/`，分为 manuscript、pipeline、figures、outputs、evidence、reviews、zotero 和 ignored build。公共原始数据与 SAF 生成的 processed 数据全部移出仓库，默认布局为 `E:/Work/Data/{Fusion360Gallery,Thingi10K,Temporary/SAF}`，由 `tools/data_paths.py` 统一解析并可环境变量覆盖。DVC 元数据与仓库内数据阶段删除，论文文献 PDF改由 Zotero 集合 `几何可达与神经预测`（`F5ITM9M6`）只读提供；构建时生成 ignored BibTeX，Zotero 缺失或 citation key 不完整时论文门失败，工程门不受影响。工程 gate 与论文 gate 分离，canonical 论文图/PDF和轻量 evidence 可追踪，原始 run/cache、旧 archive、文献附件和临时编译物不追踪。
- 依据：工程代码需要在无论文资料、无外部数据和无 Zotero 的新克隆中独立测试；论文又需要一个聚合的下游事实源和可复核引用入口。把共享数据与文献附件留在项目外可避免跨项目重复、仓库膨胀和资料误发布；把论文 pipeline 放在 deliverables 下可集中管理而不让论文反向污染产品模块。Git 历史保留旧论文版本，不在当前树重复保留 archive 二进制。
- 状态：接受（只改变工程/论文/数据/文献资产边界与门职责，不改变 D-001..D-005 几何语义、冻结参数、标签定义或实验结论；由 `tools/data_paths.py`、`tests/gate.py`、论文 gate、Zotero contract 和结构/论文测试共同守护）。
