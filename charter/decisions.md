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
