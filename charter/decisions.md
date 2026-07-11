# decisions

<!-- 裁决记录。只增不改。旧裁决被推翻时,新增一条并标注 supersede,永不回改旧条目。
     课题状态就靠这份 + git log + DVC,不另开总览。
     格式:## D-00N <一句话结论> / - 日期 / - 裁决 / - 依据 / - 状态 -->

## D-000  采用《运行协议》课题结构（Path C 完全迁移），docs/ 退役为参考

- 日期：2026-07-10
- 裁决：SAF 从 `docs/` 编号散文范式迁移到运行协议课题结构（`research/ harness/ src/ tests/ runs/ plans/`）。`docs/0_–3_` 的操作性内容蒸馏进 `research/`（problem-card / evidence / 本文件）+ `constitution.md` + `params.yaml` + `harness/`；`docs/` 物理保留、人工管理，退役为**只读参考**，不再作操作真源，不 renumber、不新增 `docs/4_`。
- 依据：`method/运行协议.md` §5（从 00–06 编号文档迁移清单）/ §6（不建文档群、不靠散文同步规格）；用户 2026-07-10 选择 C。
- 状态：接受

## D-001  可达性主判据 = 语义 C（多方向直线插入无碰撞）

- 日期：2026-07-10
- 裁决：点 p 可达 ⟺ 存在某方向，工具沿直线从无穷远逼近 p 而不碰撞；任意方向皆碰撞则不可达。弃语义 A（局部可容纳，盲腔误判可达）、弃语义 B 作主判据（连通路径，踩运动规划边界，仅进阶讨论）。
- 依据：`reference/1_§10` 三判据对照（盲腔判例）；DeepMill[R6] 不可达点定义；IMF[R3] 多朝向最优碰撞测度同族。
- 状态：接受

## D-002  基板不建模；工具从下半球任意方向逼近；oracle 只计零件本体遮挡（=遮挡下界）

- 日期：2026-07-10
- 裁决：碰撞场景**不放地面/基板**；对下朝支撑接触点，工具可从外侧（下半球）任意方向逼近；oracle 仅以零件本体几何为遮挡体。给出的是遮挡**下界**。
- 依据：语义 C 下若引入基板会挡住整个下半球，使所有下朝面翻为不可达、标签性质反转；本课题定位几何代理、工具近似手工/打磨（常在拆板后）；是 `reference/1_§12`、`reference/3_§6.8`"遮挡下界"局限的**显式化**（原局限清单未点明基板，此条补齐）。
- 状态：接受（**须写入论文局限**：仅零件本体遮挡下界，未建模基板、支撑间相互遮挡与移除顺序）

## D-003  oracle 实现口径 = 体素/距离场腐蚀（工具半径摊销）+ 边界带精确胶囊细化

- 日期：2026-07-10
- 裁决：在体素/距离场上计算——对实体做一次无符号距离变换，阈值 r 得"腐蚀自由场"；点 p 沿方向 v 可达 ⟺ 从 p+r·v 沿 v 到无穷远的射线整段落在腐蚀自由场（= 栅格 ray-march）。半径对所有点一次摊销。栅格分辨率决定不了的薄层判为"边界不确定"，用精确胶囊-网格求交细化。禁用裸网格逐点逐方向胶囊求交作主口径（10⁹–10¹⁰ 量级）。
- 依据：与 IMF Minkowski 腐蚀同源（`reference/2_§5.2`、`reference/1_§10.1` 语义 B 描述）；把预算从"每点每方向一次胶囊测试"塌成"一次距离变换 + 廉价栅格步进"，GPU 友好；边界带机制解释了三层标签中的"边界不确定"（`reference/1_§12.1`）。
- 状态：接受（连续数值 voxel_res / epsilon / 方向数见 `conf/params.yaml`，为**临时值**，阶段"标签质量审核"六项趋势通过后另立 decisions 冻结）

## D-004  第一版标签 = 二分类可达/不可达

- 日期：2026-07-10
- 裁决：MVP 用二分类；分档可达性、截断余量、连续有符号余量为进阶，第一层不稳定不进更高层。
- 依据：`reference/3_§6.4`——更易审核、与 baseline 比较、形成闭环，不被追问余量物理意义。
- 状态：接受

## D-005  工具 = 球模型、方向灵活

- 日期：2026-07-10
- 裁决：主实验用球模型、方向相对灵活（近似手工/打磨）。方向受限工具（特定角度铣削/切割头）判据收窄为"受限方向集合内是否存在无碰撞直线插入"，作进阶变体，不进 MVP。
- 依据：`reference/1_§10.5` / `reference/3_§3.6`。
- 状态：接受

## D-006  语义化重命名 + 收敛为标准 Python 布局（supersede D-000 的命名部分）

- 日期：2026-07-11
- 裁决：把 D-000 起的协议结构改名为语义清晰、收敛为主流 src-layout —— `research/`→`charter/`（problem-card→problem）；根 `constitution.md`→`charter/constraints.md`；`docs/`→`charter/reference/`（退役富参考）；`workflow/`→`method/`（研发方法论中枢）；`harness/` 溶入 `tests/acceptance/`（性质/变形/差分/已知答案）+ `tests/gate.py`（棘轮门）+ `src/support_accessibility/eval/`（指标）；包名 `saf`→`src/support_accessibility/`（唯一 py 包）；`params.yaml`→`conf/params.yaml`。并把验收层从占位升级为"决策↔性质"映射骨架（见 `charter/README.md` 映射表），加文档机检 `tests/acceptance/test_charter.py`。
- 依据：命名去黑话（读者语言）；三个 py 根（harness+src+tests）收敛为"一个包 + tests/"，根保持浅（主流 src-layout / Cookiecutter-DS / Hydra）；把 ffm §9 文档机检升级到"机检科学决策"。用户 2026-07-11 确认 `charter`、其余按推荐。
- 状态：接受（supersede D-000 的**命名/布局**部分；D-000 的范式实质——协议结构、门先于码、旧编号文档退役——仍有效）

## D-007  开发环境 = conda-forge + Python 3.12（env 名 sfa）

- 日期：2026-07-11
- 裁决：用 conda（miniforge，`D:\Miniforge\Install`）建环境 `sfa`：python=3.12 + conda-forge 的 igl/numpy/scipy/trimesh/pytest/hypothesis。**canonical 源 = `environment.yml`**（`conda env create -f environment.yml` 可复现）；`pyproject.toml` 只列抽象 pip 依赖(numpy/scipy/trimesh)+dev(pytest/hypothesis)，不列 igl。运行期由 `tests/acceptance/test_env.py` 的 `env_ready` 门守护。
- 依据：igl（libigl）的 generalized winding number 判内外、scipy 距离变换是 oracle 口径（D-002/D-003）的直接依赖；几何栈在 conda-forge 上装最省事（pip 的 libigl 轮子易踩坑）；把环境写成机器可读 + 会检查的门，消除"环境歧义"。env 名沿用创建时的 `sfa`（与项目名 SAF 大小写不同，治理里以 `sfa` 为准）。
- 状态：接受
