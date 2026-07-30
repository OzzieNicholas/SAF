# 论文图件流水线（paper/figures/）

写作指引 §4.1 的 10 幅图，脚本在此目录，产物 PNG(300dpi) + PDF(矢量) 落 `paper/figures/`。
统一样式见 `style.py`（中文 SimHei、配色语义 **不可达=红/可达=蓝/不确定=灰**、离屏 pyvista 主题）；
数据/渲染助手见 `_data.py`。所有依赖真实数据/模型的图均可由脚本从数据集 + 缓存 checkpoint 复现。

## 依赖

- `environment.yml` 的 `saf` 环境（含 pip 段 matplotlib 3.11 + pyvista 0.48 + vtk）。离屏渲染需 GPU/OpenGL。
- Fusion 原网格根：`E:/Fusion360Gallery/reconstruction`（`--root`，图2/7/9/10b 精网格渲染用；gitignore）。
- 缓存 checkpoint / 中间产物（`runs/`，DVC/gitignore，机器 emit）：
  - `runs/figures/ckpt_point.pt` ← `_train_ckpt.py`（点级模型，1200 件/150 轮，留出 seed=0）— 图7。
  - `runs/figures/ckpt_dir.pt` ← `_train_dir_ckpt.py`（方向级模型，占据口径，250 件/120 轮）— 图9。
  - `runs/failure_audit/{failure.json,fig10_worst.npz}` ← `failure_cases.py --max-models 400` — 图10。

## 图件清单

| 图 | 脚本 | 类型 | 数据源 |
|---|---|---|---|
| 图1 总体框架 | `fig01_framework.py` | 示意 | 无（纯 matplotlib 矢量） |
| 图2 方向依赖 S(P,d) | `fig02_direction_dependence.py` | pyvista | Fusion 件 + `overhang.support_contact_faces`（两构建方向面积保真高亮） |
| 图3 判据示意 | `fig03_criterion.py` | 示意 | 无（2D 剖面三联） |
| 图4 两级判定器 | `fig04_two_stage.py` | 示意 | (a) 真 scipy EDT 距离场；(b) 胶囊–三角示意 |
| 图5 网络结构 | `fig05_network.py` | 示意 | 无（维数照 `models/convonet.py`） |
| 图6 面积⊥可达 | `fig06_area_vs_access.py` | pyvista+mpl | `flagship_pair` 对照对 + `fusion360_full` 散点 + `eval.spearman` |
| 图7 预测热图 | `fig07_prediction_heatmap.py` | pyvista+mpl | `ckpt_point.pt` + `fusion360_full` 留出件 + `--root` 网格 |
| 图8 基线+消融 | `fig08_baselines_ablation.py` | mpl | `runs/baselines/latest.json` + `results.md` 消融常量 |
| 图9 方向级场 | `fig09_direction_field.py` | mpl+pyvista | `ckpt_dir.pt` + oracle 方向标签 + `--root` 网格 |
| 图10 失败案例 | `fig10_failure.py` | mpl+pyvista | `runs/failure_audit/{failure.json,fig10_worst.npz}`（同 `results.md` 失败案例行源） |

## 全量重生（顺序：先缓存后出图）

```bash
source "D:/Miniforge/Install/etc/profile.d/conda.sh" && conda activate saf
# 1) 缓存 checkpoint / 中间产物（各约 10–60min；勿并发）
python tools/figures/_train_ckpt.py --max-models 1200 --epochs 150
python tools/figures/_train_dir_ckpt.py --max-models 250 --epochs 120
python tools/failure_cases.py --max-models 400          # 复现 results.md 失败案例行 + 落图10数据
# 2) 出图（无先后依赖，可逐条跑）
for f in 01_framework 02_direction_dependence 03_criterion 04_two_stage 05_network \
         06_area_vs_access 07_prediction_heatmap 08_baselines_ablation \
         09_direction_field 10_failure; do
  python tools/figures/fig${f}.py
done
```

## 注记

- 配色红线（写作指引 §1.2）：不可达=红、可达=蓝、不确定=灰（红绿色盲友好）；图2 支撑接触区高亮用橙（避开红/蓝语义）。
- 图7/9 的 checkpoint 为**图件专用**（子集/较短训练，出可读预测即可，非 benchmark）；主指标以 `results.md` / `runs/` 正式评测为准。
- 图10 的失败分箱由 `failure_cases.py` 计算（cuDNN 非确定，逐次训练略有浮动）；图与 `results.md` 失败案例行同源，数值以最近一次 emit 的 `runs/failure_audit/failure.json` 为准。
