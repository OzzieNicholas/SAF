# SAF 项目进度与交接记录（record.md）

> 更新：2026-07-11。用途：离开后随时回来，看这一份就能明白"做了什么 / 现在在哪 / 接下来做什么"。
> 这份是**给人看的地图**；机器可读的权威状态永远是 `python tests/gate.py`（跑一下就知道全局），"为什么"永远看 `charter/decisions.md`（D-000..D-010）。

---

## 0. 30 秒 orientation（你在这里）

- **SAF = Support Accessibility Field**。目标：发一篇论文——金属增材制造**支撑接触区**的"工具几何可达性"代理评价 + 形状条件神经预测。几何/AI 题、DfAM 前端，**不做**材料/打印实验。
- **纪律（你定的）**：先把"尺子"（工作流 + oracle 判定器）造好、**严格验证对**，再做实验。**至今全程在造尺子，一次真正的实验都没做。**
- **现在造到哪**：治理骨架 ✓、oracle 核心 ✓、能吃真实网格 ✓、能从"网格+构建方向"提取支撑接触区 ✓。
- **⚠️ 回来第一件事**：有一条测试红着（`test_scale_invariance`，是个"假绿"被抓出真反例）。先处理它 → 见 **§3**。

---

## 1. 回来怎么快速上手

**环境**：conda env 名 `saf`（Python 3.12，conda-forge）。miniforge 装在 `D:\Miniforge\Install`。
- conda 在非交互 shell 里不在 PATH → 用**绝对路径的 python**最稳：
  `D:\Miniforge\Install\envs\saf\python.exe`
- 交互 PowerShell 里可以 `conda activate saf` 后直接 `python ...`。

**一条命令看全局（你的仪表盘）**：
```powershell
& "D:\Miniforge\Install\envs\saf\python.exe" D:\Work\SAF\tests\gate.py
```
→ 打印 JSON 裁决：`overall`（GREEN/RED）+ `summary{PASS,PENDING}` + 每条 `acceptance` 检查。退出码 0=绿 1=红。**现在是 RED**（几何/实验还没做完，正常）。

**跑测试**：
```powershell
& "D:\Miniforge\Install\envs\saf\python.exe" -m pytest D:\Work\SAF\tests -q
```

**看"为什么这么定"**：`charter/decisions.md`（只增不改的决策台账，D-000..D-010）。
**看"哪条决策对应哪条测试"**：`charter/README.md`（治理地图/映射表）。

---

## 2. 现在的状态快照（2026-07-11）

- **gate**：`overall: RED`，`{PASS:16, PENDING:6}`。
- **pytest**：**15 passed, 1 FAILED（test_scale_invariance）, 4 skipped**。
  - 注意：gate 里 `scale_invariance` 显示 PASS（它用固定 8 个种子，运气好），但 pytest 用 Hypothesis 随机搜索抓到了反例 → FAILED。所以 gate 的 scale 绿也是"假绿"。

**已经绿的（尺子造好并验证的部分）**：
- 治理机检 `test_charter`（决策 schema / 参考在位 / 无残留旧名 / params 键）
- 环境门 `test_env`（igl/numpy/scipy/trimesh + py≥3.12，环境不对当场红）
- oracle 已知答案 `test_known_answers`（盲腔=不可达、开阔下朝面=可达）
- 差分对拍 `test_differential`（体素口径 == 独立暴力参考，信任 oracle 的命门）
- 网格前端 `test_mesh_frontend`（真实网格 → igl 判内外 → occupancy，复现已知答案，IoU=1.0）
- 支撑接触区 `test_support_contact`（网格+d → 下朝悬垂面 S(P,d)：提取/方向依赖/阈值/端到端全链）

**还红/待做（PENDING 或 skip）**：
- `scale_invariance`（**假绿，见 §3**）、`radius_monotonic`（已证伪 D-008）、`direction_monotonic`（需 oracle 支持显式方向集）、`rotation_equivariance`（移交真实网格）、`mesh_sanity`（数据管线未接）、预算门/回归门（后续）。

---

## 3. ⚠️ 回来第一件事：处理 scale 测试（唯一未决动作）

**问题**：`tests/acceptance/test_properties.py::test_scale_invariance`（清单5 写的，最近这批**没碰它**，所以**不是回归**）被 Hypothesis 随机种子抓出**真反例**：
```
seed=2453, N=13, r=1.11:  粗网格(13³)=accessible  细网格(2×=26³)=inaccessible
（r-0.5 到 r+0.25 全程 DIFF——robust 不一致，不是边界噪声）
```
**根因**：粗网格漏判了一个"欠分辨的薄特征"（误判成可达），2× 上采样后细网格纠正成不可达。所以"尺度不变"其实是**分辨率稳定性**，粗网格不够细时会真错——**和 radius（D-008）同一类：以为是不变量、其实不是**。清单5 那次绿是运气（40 个种子没撞上）。

**建议做法（照当初处理 radius/D-008 的同一套，小改，几分钟）**：
1. `test_properties.py`：`test_scale_invariance` 从硬断言改成 `raise SkipTest("分辨率依赖，非严格不变量，见 D-011")`；`checks()` 里 `scale_invariance` 项从 result 改成 `pending(...)` 指向 D-011。
2. `charter/decisions.md`：append **D-011**——"scale-via-upsampling 是分辨率稳定性、非严格不变量；粗网格会误判欠分辨特征；真实分辨率稳定性留待足够细的真实网格复核；不作硬不变量"。
3. `charter/README.md`：映射表把 D-005 尺度不变那行从 **GREEN** 改成 "证伪/分辨率依赖（D-011）"。
4. 跑 gate + pytest 复验：预期 gate `{PASS:15, PENDING:7}`、pytest `15 passed, 5 skipped`（scale 从 fail 变 skip）。

（做完这个，suite 就恢复"全绿或明确 pending"的诚实状态。）

---

## 4. SAF 是什么（项目定位）

- **一句话**：在单个公开三维零件上，识别构建方向 d 决定的**支撑接触区**（下朝悬垂面代理），评价这些表面点在简化工具（球）条件下的几何可接近性，并用形状条件神经场在未见模型上预测——为 DfAM 前端提供不同于"支撑体积/过悬面积"的后处理几何风险维度。
- **与近邻工作**：方法与 DeepMill[R6] 同源（不声称超越）；创新锚在**评价对象**（AM 支撑接触区**表面**）+ AM 后处理语义。详见 `charter/evidence.md` 与 `charter/reference/`。
- **发表定位**：普通中文期刊 / 中等英文应用期刊；不是顶刊顶会。

---

## 5. 项目结构（哪些东西住哪）

```
D:\Work\SAF\
├── charter/                 治理散文 + 地图（这是"为什么"和"规则"的家）
│   ├── README.md            ★ 治理地图：三层强度 + 决策↔测试映射 + 修改触发
│   ├── problem.md           问题定义（目标/硬约束/非目标/指标/样例）
│   ├── decisions.md         ★ 决策台账 D-000..D-010（只增不改，"为什么"全在这）
│   ├── evidence.md          文献证据（来源↔问题）
│   ├── constraints.md       6 条铁律（几何代理非认证 / 企业隔离 / …）
│   └── reference/           退役的原始富文档（0_背景/0_执行路线/1_选题/2_文献/3_实验），只读参考
├── method/                  研发方法论中枢（运行协议等），手动管理、gitignored
├── src/support_accessibility/   唯一 python 包
│   ├── oracle/__init__.py   ★ 几何 oracle：语义C 体素腐蚀口径（label + 暴力参考 reference_label）
│   ├── data/
│   │   ├── __init__.py       程序化解析已知答案件（blind_cavity_case / open_downface_case）
│   │   ├── mesh.py           网格前端：mesh_to_occupancy（igl 判内外）+ box_vf/stack_vf + 两个网格已知答案件
│   │   └── overhang.py       支撑接触区提取：support_contact_faces（下朝悬垂面 S(P,d)）
│   ├── eval/__init__.py      指标（桩，待实现）
│   ├── models/  viz/         占位（神经网络 / 可视化，后续）
├── tests/
│   ├── acceptance/           ★ 验收层（"harness"）：每条对应一条决策
│   │   ├── test_env.py            环境门
│   │   ├── test_charter.py        文档机检（治理自检，纯文本，现在就绿）
│   │   ├── test_known_answers.py  oracle 已知答案（解析件）
│   │   ├── test_differential.py   体素 vs 暴力参考对拍（Hypothesis）
│   │   ├── test_properties.py     变形性质（scale/radius/dir/rot；radius证伪、scale待证伪）
│   │   ├── test_invariants.py     mesh_sanity（桩）
│   │   ├── test_mesh_frontend.py  网格→occupancy 复现已知答案
│   │   └── test_support_contact.py 支撑接触区提取
│   ├── gate.py              ★ 棘轮门：汇总所有 checks() → JSON 裁决 + 退出码
│   └── conftest.py          让 pytest 找到 src 包
├── conf/params.yaml         Hydra 配置（连续数值：方向数/半径/分辨率/悬垂角，都是临时值待标定）
├── environment.yml          conda 环境 canonical 源（conda env create -f environment.yml）
├── pyproject.toml  CLAUDE.md  README.md
├── runs/ plans/ data/       空占位（实验产物 / Superpowers计划 / 数据）
└── record.md                本文件
```

**治理三件套记法**：`gate`=现在到哪（跑命令）、`decisions.md`=为什么（读台账）、`README.md`=地图（决策↔测试）。

---

## 6. 已经做了什么（按批次 / "小片"）

我们把工作切成**小片**逐个做，每片都：进计划模式 → 动手前探针核查（避免认知偏差）→ 小计划审批 → 执行 → 事后核验（gate/pytest + 范围检查）。已完成：

| 批次 | 做了什么 | 对应决策 |
|---|---|---|
| 清单1–2（结构/环境） | 从"编号散文文档"迁到 charter/tests/src 结构；命名语义化；建 gate + 文档机检；环境入治理（environment.yml + env_ready 门）| D-000, D-006, D-007 |
| 清单3–4（oracle 最小） | oracle 体素腐蚀口径 label + 暴力参考；程序化已知答案件；盲腔=不可达、开阔下朝面=可达 变绿 | D-001..D-005 |
| 清单5（变形/差分） | 差分对拍（Hypothesis）变绿；**radius 单调性证伪**（暴力参考也违反）；scale 当时变绿（后发现是假绿）| D-008 |
| 清单8-1（网格前端） | mesh → occupancy（igl fast_winding_number>0.5）；box 复现已知答案，IoU=1.0；**发现 trimesh concat/translate 原生崩溃 → 改 numpy V/F 堆叠** | D-009 |
| 清单8-2（支撑接触区） | 网格+构建方向 d → 下朝悬垂面 S(P,d)（n·d̂<-cos45）；提取/方向依赖/阈值/端到端全绿 | D-010 |

---

## 7. 冻结的决策 D-000..D-010（契约 + 关键发现）

一句话一条（细节读 `charter/decisions.md`）：
- **D-000** 采用运行协议课题结构（旧编号文档退役为 reference）。
- **D-001** 可达性主判据 = 语义C（存在方向，工具球沿直线从无穷远逼近该点不碰撞）。
- **D-002** 基板不建模；工具从下半球逼近；只算零件本体遮挡（=遮挡下界）。
- **D-003** oracle 口径 = 体素/距离场腐蚀（半径摊销）+ 边界带细化。
- **D-004** 第一版标签 = 二分类可达/不可达。
- **D-005** 工具 = 球模型、方向灵活。
- **D-006** 语义化重命名 + 收敛标准 Python 布局（supersede D-000 命名部分）。
- **D-007** 开发环境 = conda-forge + Python 3.12，env 名 `saf`。
- **D-008** ⚠️ **半径单调性证伪**：point-touch 语义C 下"r↑→不可达↑"不成立（暴力参考也违反，非 bug）。radius 不作不变量。
- **D-009** ⚠️ 网格前端口径：igl fast_winding_number>0.5；**无 CSG → numpy V/F 堆叠**；**禁用 trimesh concat/translate（本 env 原生崩溃 0xC06D）**。
- **D-010** 支撑接触区提取：S(P,d) = 外法向 `n·d̂ < -cos(θc)` 的面（θc=overhang_angle_deg=45）；外法向用 numpy cross；质心作接触点。
- **（待记）D-011** scale 分辨率依赖、非严格不变量（见 §3）。

---

## 8. 接下来的路线图（还剩什么）

**立即**：处理 scale（§3）。

**仍在"造尺子"（Tier-1，实验之前必须做完）**：
1. **六项趋势审核**落地（标签质量门）+ **预算门**（D0 实测 oracle 单点单方向成本→外推，超预算先换口径再降采样）。
2. **指标实现**（`src/.../eval`：不可达类 F1 / IoU / 面积误差 / 方向排序）+ `mesh_sanity`。
3. **真实数据集接入**（网格前端剩余部分）：ABC / Thingi10K 加载（trimesh.load）→ solidify → 支撑接触区 → 可达性。这也是 D-008/scale/rotation 在**真实几何上复核**的场子。可能要装 `manifold3d`（做带洞腔体网格）。
4. **DVC + Hydra** 接线（可复现 runs）。
5. **定义"工作流完成 DoD"**：gate 在哪些条件下算"尺子造好、可以开实验"（除回归门外全绿）。

**之后才是"做实验"（Tier-3，你说的"实质性实验"）**：规模化生标签 → baseline（支撑面积/射线可见性/局部规则/无形状条件/逐零件）→ 训形状条件网络 → 评估 → 消融。

**留待真实网格复核的遗留**：radius（D-008）、scale（D-011）、rotation/direction 性质、真实网格法向缠绕修复（trimesh fix_normals）。

---

## 9. 环境与坑（gotchas，省得再踩）

- **python 路径**：`D:\Miniforge\Install\envs\saf\python.exe`。conda 不在非交互 shell PATH。
- **PowerShell `>` 重定向写的是 UTF-16** → 直接 `json.load` 会 UnicodeDecodeError。要么 subprocess 抓 stdout、要么管道，别用 `>` 存 JSON 再读。
- **trimesh.util.concatenate / apply_translation 在本 env 原生崩溃（0xC06D）**。合并多实体/平移一律用 numpy（`np.vstack` 顶点 + 面索引偏移；平移用坐标加法）。`trimesh.creation.box` / `.face_normals` 本身没问题。
- **内联 python 探针要 `print(..., flush=True)`**，否则长时间原生调用崩溃/结束时缓冲输出会丢，看着像"127 无输出"。
- **oracle 半径/点是体素单位**；世界坐标要经 `mesh.world_to_voxel(p, lo, pitch)` 转、半径要 `/pitch`。
- **占据栅格 vs 解析件**：oracle 工作在 occupancy 上；程序化解析件（data/__init__）和真实网格（data/mesh）都产 occupancy 喂它。

---

## 10. 还没定的岔路（你要拍的板）

- **几何优先 vs 神经优先主线**（parked）：现在默认"神经预测为主线、几何评价为降级"。曾讨论过反过来（先保几何/benchmark 一篇、神经作升级），更贴你的几何强项 + 中文期刊目标。等 oracle 全绿后可重议。
- **point-touch 语义（D-001）是否要细化**：radius（D-008）和 scale（D-011）都显示 point-touch 在合成几何上有反直觉行为。**暂不改**（合成 speckle 非真实网格）；等真实网格证据再决定是否细化"工具-可达"模型。

---

## 11. git / commit 状态

- 已提交到 `c9cc338 "workflow"`（含清单1–5 的成果）。
- **清单8-1 + 8-2 的 8 处改动已 staged（git add 过）但未 commit**：`charter/README.md`、`charter/decisions.md`、`src/…/data/mesh.py`、`src/…/data/overhang.py`、`tests/acceptance/__init__.py`、`tests/acceptance/test_mesh_frontend.py`、`tests/acceptance/test_support_contact.py`、`tests/gate.py`。
- commit 由你手动做（我不碰 commit）。建议：先做 §3 的 scale 修复，让 suite 诚实，再一起 commit。commit 前可 `git add -A` 收齐。

---

## 12. 关键文件指针

- 最近一次计划（清单8-2 的完整计划）：`C:\Users\Administrator\.claude\plans\1-2-quirky-kite.md`
- 原始设计全文（问题/文献/实验/执行路线，非常详）：`charter/reference/{0_背景与边界, 0_执行路线与阶段门, 1_选题与研究定位, 2_文献矩阵与相关工作, 3_实验闭环设计}.md`
- 支撑接触区定义原文：`charter/reference/1_选题与研究定位.md` §9。
- 判定语义三判据选定：`charter/reference/1_选题与研究定位.md` §10。

---

## 13. 我们的工作节奏（回来照这个继续）

每做一小片：
1. 进计划模式；
2. **动手前探针核查**（在 saf 里跑只读探针，验证设计、避免认知偏差——历史上多次靠这个抓出错误假设：radius 证伪、trimesh 崩溃、scale 假绿）；
3. 写**小**计划（切小片，别一次吃太大），审批；
4. 执行；
5. **事后核验**：gate + pytest 数字对齐预期 + 范围检查（find -mmin 隔离本片，确认没波及计划外文件）；
6. 汇报**开头一句话 orientation**（在造尺子的哪块、离实验几步）。

> 一句话收尾：你现在有一把已经验证到"能吃真实网格、能提取支撑接触区"的尺子；回来先修那条 scale 假绿（§3），然后就可以往"接真实数据集"走了。**离做实验还有几步，但每步都踩实了。**
