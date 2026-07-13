# conventions — 动作与规范（治理）

<!-- 一切"动作"的规范：commit / 分支 / 合并 / 删除，以及治理文件命名。
     原则同治理其余部分：规范要"有牙"——违规让 CI 变红（tools/check_conventions.py），而非散文（会漂移）。
     可执行权威 = tools/check_conventions.py（spec 唯一之家）；本文件是理据与生命周期散文。冻结见 decisions D-013。 -->

## 1. Commit 规范（Conventional Commits）

`<type>(<scope>): <主题>` —— scope 可选 = 模块（oracle/data/eval/models/viz/charter/tests/ci…）；主题祈使句、简洁。

| type | 用途 | type | 用途 |
|---|---|---|---|
| `feat` | 新能力 / 新对象 | `ci` | CI / 工具 / 构建 |
| `fix` | 修正错误 / 证伪 | `gov` | 治理（决策 / charter / 规范 / deferred） |
| `refactor` | 重构（行为不变，如改名） | `data` | 数据 / 标签（SAF 专属） |
| `test` | 验收 / 测试 | `exp` | 实验 run（Tier-3 专属） |
| `docs` | 文档（charter 散文 / docs/ / README） | `chore` | 杂项 |
| `revert` | 回滚 | | |

正文（可选）说清"为什么 / 影响"；末尾按仓库约定附 Co-Authored-By / Claude-Session trailer。

## 2. 分支命名 + 生命周期

- **命名**：`<type>/<slug>`，slug 小写连字符，如 `fix/scale-false-green`、`gov/git-conventions`、`feat/oracle-metrics`。
- **豁免**：`main` / 默认分支；`claude/*`（harness 为 agent 会话指定的分支，非人工选择——本会话即用之）。
- **生命周期**：从最新 `main` 起分支 → 干活（**一分支一件连贯事** = 一个 slice/feature）→ 本地 gate + 规范校验绿 → push → 开 PR（套模板）→ CI 绿 + 评审 → **合** → **合并后删分支**。
- **合并策略 = squash-and-merge**：main 每 PR 一条提交，历史线性、易 bisect/revert；slice 细节留在 PR 里。故**一个 PR = 一件连贯事**（别把无关改动塞一个 PR）。squash 提交标题也须合 §1（GitHub 以 PR 标题作 squash 主题）。
- **main 保护**（GitHub 仓库设置，你侧开关；本文件只记明）：require CI green 才可合；开 auto-delete-on-merge。

## 3. 治理文件命名原则

每个 `charter/` 文件名直呈其角色，读者语言、无黑话：

| 文件 | 角色 |
|---|---|
| `problem.md` | 做什么 / 硬约束 / 非目标 |
| `constraints.md` | 不可破的铁律 |
| `decisions.md` | **已冻结**决策台账（只增不改） |
| `deferred.md` | **未决**决策 + 触发条件（decisions 的"未决半"；接进门，到期在 gate 现身） |
| `evidence.md` | 文献证据 |
| `conventions.md` | 本文件：动作与规范 |
| `README.md` | 治理地图 / 索引 |

台账成对：`decisions.md`（已决）↔ `deferred.md`（未决）。避免 `record/log/open` 这类不点明角色、易滑向日记的名字（`record.md` 已退役删除——状态看门、地图看 README、为什么看 decisions）。

## 4. 强制（牙）

- **权威**：`tools/check_conventions.py`（纯 stdlib，规范 spec 唯一之家）——校验 commit 主题 + 分支名；规范**自 `charter/conventions.md` 引入的提交起**向后强制，之前的 bootstrap 提交祖父豁免（不改写历史）。
- **CI**：`.github/workflows/conventions.yml` 每 push / PR 跑它 → 违规 = 红。
- **本地（可选，快失败）**：`hooks/{commit-msg,pre-push}` + `hooks/install.sh`（`sh hooks/install.sh` 装进 `.git/hooks`），同一校验器背书。
- **分工**：`tests/gate.py` 守"工作树 / 代码 / 决策"的真相；本规范守"git 历史 / 动作"。两者都是 CI 上的门，关注点不同（一个事实一个家）。
