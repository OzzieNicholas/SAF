# 论文图件流水线

本目录生成 `paper/figures/` 中的十幅主图。每幅图的脚本名、输出文件名和正文图片链接名相同，名单以 [`__init__.py`](__init__.py) 中的 `FIGURE_NAMES` 为准。图件按最终印刷尺寸排版（双栏 175 mm、单栏 85 mm），导出 600 dpi PNG 与字体嵌入的 PDF；图题和图注写在源稿 `paper/manuscript/论文正文.md` 中，图内只保留面板标号与必要标注。

## 图件与脚本

| 正文图号 | 名称（脚本与输出文件） | 论点 | 数据 |
|---|---|---|---|
| 图 1 | `criterion_schematic` | 有限球工具多方向直线逼近判据 | 二维剖面上按判据计算的扫掠 |
| 图 2 | `method_overview` | 离线几何标注与在线形状条件预测 | 留出零件渲染 + `holdout_model` |
| 图 3 | `labeler_schematic` | 两级几何判定：距离场步进与按净空分流 | 二维占据栅格上实际计算的距离场 |
| 图 4 | `proxy_failure` | 零半径射线与接触面积遗漏的风险 | `tool_radius_effect`、`orientation_evaluation` |
| 图 5 | `method_comparison` | 固定留出集上的方法对照与消融 | `baseline_comparison`、`shape_context_ablation` |
| 图 6 | `result_gallery` | 留出零件上的预测（按 F1 等距选件） | `holdout_model` + 原网格 |
| 图 7 | `screening_figure` | 全部未见零件上的设计筛查 | `screening_evaluation` |
| 图 8 | `cost_accuracy_frontier` | 精度与单件耗时 | `cost_accuracy_frontier` |
| 图 9 | `orientation_case` | 候选构建方向的评价示例 | `orientation_evaluation` + 原网格 |
| 图 10 | `failure_direction` | 误差位置与方向推荐 | `failure_analysis`、`direction_field_prediction`、`direction_field_audit` |

## 模块

| 模块 | 职责 |
|---|---|
| `journal_style.py` | 中文期刊样式（宋体 + Times New Roman、6 号字、变量斜体）、语义色与导出；导出前写布局诊断 |
| `cad_render.py` | 不透明零件渲染与「幽灵视图」：被遮挡的关键面以半透明色块和虚线轮廓透出外壁 |
| `figure_data.py` | 网格加载、按 D-028 把样本点映射回原始三角面、相机与裁边助手 |
| `figure_style.py` | PyVista 离屏渲染主题（`figure_data` 使用） |
| `figure_cases.py` | 按名称指定的固定案例与数据根 |
| `figure_qa.py` | 布局诊断汇总、像素与 PDF 检查、contact sheet |

## 不变量

- 语义色：浅蓝 = 可达，红 = 不可达，橙 = 误报，深紫 = 漏报，灰 = 零件本体；误差面另加深色轮廓，灰度打印仍可辨。
- 图内文字不小于 7.5 pt；中文宋体、数字与字母 Times New Roman、变量斜体。图中不用 mathtext（它不支持字体回退，与汉字混排会缺字），变量由 `journal_style.var()` 生成 Unicode 数学斜体字符。
- 结果数值只从 `artifacts/runs/` 的运行产物读取，脚本内不写任何结果数字。
- 定性结果必须由 `figure_data.map_processed_faces` 按 D-028 逐点映射回原始三角面；点数、顺序或体素坐标不一致即失败。
- 定性案例按固定规则选取（画廊：按逐件 F1 等距；方向示例：接触面积选错方向且风险差异最大），不按观感挑选；按名称指定的案例须属于留出集。
- 截断纵轴只用于点图，柱状图从 0 起。

## 重生成

以下命令在仓库根目录、已激活 `saf` 环境下执行。

```bash
# 1) 图件依赖的实验结果（holdout_model 须先于其余各项）
python tools/reproduce_experiments.py --only holdout_model,baseline_comparison,shape_context_ablation,failure_analysis,cost_accuracy_frontier,screening_evaluation,orientation_evaluation
python -m paper.pipeline.audits.freeze_evidence

# 2) 十幅图（顺序执行，不并发）
for name in criterion_schematic method_overview labeler_schematic proxy_failure method_comparison \
            result_gallery screening_figure cost_accuracy_frontier orientation_case failure_direction; do
  python -m paper.pipeline.figure_scripts.$name
done

# 3) 面映射测试与严格图件 QA
python -m pytest tests/acceptance/test_figure_face_mapping.py -q
python -m paper.pipeline.figure_scripts.figure_qa --strict
```

## QA 输出

每幅图在 `artifacts/runs/figure_qa/<名称>.json` 写入布局诊断（字号、同一坐标区内的文字重叠、文字越界）。`figure_qa.py` 汇总为 `report.json`，并检查 PNG 的 600 dpi 与空白、PDF 字体嵌入与 Type 3 字体、PDF 完整性，以及 `FIGURE_NAMES` 中的十幅图是否都有同名 PNG/PDF。`artifacts/cache/figures/contact_sheet.png` 是 175 mm 原尺度与 85 mm 缩小预览的对照，可删除。自动 QA 通过后仍须人工检查轮廓、颜色、标注和证据关系。
