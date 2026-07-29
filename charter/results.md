# results — 结果账本（复现器背书）

> 唯一的"假设/实验 → 指标 → 数值 → 样本 → 复现命令"之家。**权威数字以此为准**（`tools/` 复现器实测输出）；
> 与 roadmap 早期散文估计不符处以本表为准（早期估计来自未追踪的探索脚本，已被提交复现器取代）。
> 定性结论不变；数值经复现器校准。跑法用壳内激活（见 CLAUDE.md「怎么跑」）。冻结口径 = D-021（n_dir=128 等）。

| 假设/实验 | 指标 | 数值 | 样本 | 复现命令 / 产物 |
|---|---|---|---|---|
| **H1** 支撑面积⊥可达 | Spearman ρ(支撑面积【=下朝面计数代理，非真面积】 vs 不可达占比) | **0.27**（全群体）/ **−0.17**（两类件）——**弱相关**，支撑面积**不预示**可达性 | 8590 件 / 1621 两类 | `tools/eval_h1.py --data data/processed/fusion360_full` |
| **E1** 面积⊥可达 存在性 | 同支撑面积、可达性相反 | 各 64 下朝点，可达 **100% vs 0%** | 旗舰对 2 件 | `data.flagship_pair`；`test_data::flagship_pair_area_perp_access` |
| **H2** 工具尺寸不可忽略 | 射线可见但工具够不到 占比 | 真实 **4.8%** / 程序化 **29.3%**（非零→半径改变可达性） | Fusion 600 件（gold+rv 均 128 口径）/ 程序化 120 件（rv@128 vs gold@32，实测等价 ~0.09% 差） | `tools/eval_h2.py` |
| **H3** 跨模型预测 | 未见件 不可达 F1（vs 多数类/几何基线） | **0.910±0.006**（tiny numpy 0.75；> E4 基线，见 E4 行） | Fusion both-class 1621，5-split CV | `tools/train_convonet.py --fusion data/processed/fusion360_full --seeds 5` |
| **E4** 基线对照 | 几何基线 F1 | ray-visibility ≈ **0.71**（本机 80 留出件；跨域 OOD 0.725） | 见 H3/H5/回归 | `tools/regression_check.py`（基线半）/ `tools/eval_h5.py` |
| **H5** 跨域鲁棒 | 域内 vs OOD F1 | 域内 **0.915±0.005** / 跨域 Thingi **0.908±0.005**（掉幅 0.006）> 基线 0.725 | Fusion 留出 vs Thingi 149 both-class/46.8k 点，3 seed | `tools/eval_h5.py` |
| **E5** 方向级可达性场 | per-dir F1 / dir-set IoU / 方向排序 | per-dir **0.894±0.004** / IoU **0.875** / Top-1 命中 **0.97**·Top-3 0.98·prec@3 0.96；多数类基线 0.000 | Fusion 500 件/26.3k 点，3 seed，n_dir→D=64 | `tools/eval_e5.py --data data/processed/fusion360_full --max-models 500` |
| **E8** 神经 vs oracle 效率 | 每点耗时比 | 神经 **~120×** 快（oracle ~4ms/点 vs 神经 ~0.035ms/点，含 GPU；墙钟计时随机 ±，两次实测 115–121×；oracle 仅计逐点 label、未含 EDT 预算→ speedup 为**下界**） | Fusion 30 件/1337 点 | `tools/eval_e8.py` |
| **消融** 形状上下文价值 | 四变体 不可达 F1 | no_shape **0.50** ≪ local(RF3) **0.84** < lite(RF7) **~0.91** > pooled **0.81**（形状必需、中等 RF 最优；lite≈H3；CUDA 训练 ±小抖动） | Fusion 400 件，1 seed，60 epoch | `tools/eval_ablation.py` |
| **标签审核**（D-025，命门） | 差分 robust / res-稳定 / 分布 | robust 差分不一致 **0.25%** / res48-96 稳定 **97.7%** / inacc 5.6%·两类件 19% | Fusion 400 采样点 / 25 件 res | `tools/audit_labels.py --write`；`gate.py::label_audit_gate` |
| **回归门**（D-026） | 神经 vs 几何基线 配对 bootstrap CI | 神经 **0.915** vs 基线 **0.712**，配对差 95%CI **[0.24,0.43]>0** 显著胜 | Fusion 80 留出件，2000 bootstrap | `tools/regression_check.py`；`runs/regression/latest.json` |
| **预算门**（D-026） | 全量标签构建外推 | D0=0.0596ms → **0.69h ≤ 4h** | 40 件实测 D0 | `gate.py::budget_gate`（D-026） |

## 局限（论文诚实局限，均有据）

- **代理非认证**：oracle 是几何可达性代理（语义 C），非物理/工艺认证；遮挡下界（只计零件本体，D-002）。
- **标签噪声**：真实标签差分 robust 不一致 0.25%、res48↔96 稳定仅 **97.7%**（~2.3% 点跨分辨率翻）——已量化（D-025），非零。
- **类别不平衡**：Fusion **81% 件全可达 / 仅 19% 两类件**（1621/8590）；不可达是稀有类（占比 5.6%）。
- **H1 面积口径**：'支撑面积'实为**下朝面计数代理**（非真三角面积；面积均匀采样未实现，见 conf/params.yaml sampling 注 / D-028）。离线真面积对照（1500 件、旧口径标签）：真面积 ρ=**0.16**(全)/**0.11**(两类) **< 计数代理 0.27/0.26**——**H1"面积弱预测可达"在真面积下更成立、非代理伪影**；面积加权指标属未来工作。
- **口径漂移（D-028）**：现有 `fusion360_full` 及全部 headline 数字（H1/H3/H5/E5…）对应**旧网格前端口径**；离线扫得旧口径下 **5.81% 点落在实体内**（其中 2.24% "实体内却判可达"高度指示翻面伪下朝面）。D-028 已加固（缠绕安全外移三态 + ceil 修正 + ingest 确定性），但**未重物化**——重物化 + 重签收（命门）后方切换，且新数据不与现字节一致。
- **数据代表性**：Fusion 棱柱几何为主、无自由曲面；8625 设计中成功物化 8590 件。
- **跨域子采样**：Thingi 每件 max_points=400 + max_faces=80000（D-022）——跨域指标是子采样无偏估计。
- **E5 口径**：方向标签用**占据口径**（无 D-020 细化）；方向级标签若作 headline 训练源，**尚待作者签收**（D-024）。
- **辅助信号口径**：程序化 procedural_v1 用 **n_dir=32**（受控已知答案辅助信号，粗口径、略偏保守），与 Fusion 训练件的冻结 128 口径不同；混入训练（ftr+proc），但**所有 headline 指标皆在 128 口径的 Fusion/Thingi 测试集评估**，故影响有界。全量 128-口径 procedural 重建 + 复跑属可选后续。
- **H4 应用价值 / E8 效率**：仅覆盖推理效率（E8）+ 方向场（E5）；半径扫描 / 工具条件插值属未来工作（docs/3 §14.3），非本工程。E8 的 ~120× 按 **docs/3 §9.6 收窄**为**训练后条件扫掠摊销的量级示意**——"神经比逐点几何快"本身非本文新发现，且比值含实现因素（oracle 侧为逐点 Python 循环）。
