# 论文图件流水线

本目录生成 `paper/figures/` 中的十幅主图。每幅图的脚本名、输出文件名和正文图片链接名相同，名单以 [`__init__.py`](__init__.py) 中的 `FIGURE_NAMES` 为准。每幅图只维护一套 175 mm 全栏版式，导出 600 dpi PNG 与字体嵌入 PDF；85 mm 仅由 QA contact sheet 作缩小压力测试。图题和图注写在源稿 `paper/manuscript/论文正文.md` 中。

## 图件与脚本

| 正文图号 | 名称（脚本与输出文件） | 内容 |
|---|---|---|
| 图 1 | `framework_overview` | 几何标签、训练与未见零件推理的流程总览 |
| 图 2 | `direction_dependence` | 构建方向变化引起的支撑接触区变化 |
| 图 3 | `reach_criterion` | 有限球工具的多方向直线逼近判据 |
| 图 4 | `two_stage_labeling` | 两级几何判定器及其标签稳定性 |
| 图 5 | `network_architecture` | 形状条件预测网络结构 |
| 图 6 | `area_vs_accessibility` | 接触量与可达性不是同一维度 |
| 图 7 | `prediction_heatmap` | 未见零件上的点级预测 |
| 图 8 | `baselines_ablation` | 基线比较与受控消融 |
| 图 9 | `direction_field` | 方向级可达性场与推荐逼近方向 |
| 图 10 | `error_boundary` | 误差集中于几何边界带 |

## 模块

| 模块 | 职责 |
|---|---|
| `figure_style.py` | 颜色、字号、版式尺寸，以及 PNG/PDF 导出（PDF 先写临时文件，再核对长度与 `%%EOF` 后替换） |
| `figure_data.py` | 网格加载、按 D-028 把样本面映射回原始三角面、三维渲染助手 |
| `figure_cases.py` | 固定案例的 ID 与相机，是案例的唯一清单；常量名按图命名（如 `DIRECTION_FIELD`） |
| `figure_qa.py` | 布局诊断汇总、像素与 PDF 检查、contact sheet |
| `train_point_checkpoint.py` | 训练点级检查点（图 1、7 使用） |
| `train_direction_checkpoint.py` | 训练方向级检查点（图 1、9 使用） |

## 不变量

- 颜色：蓝=可达，红=不可达，紫=FN，橙=支撑接触区或 FP，灰=零件；同一面板内橙色不得复用语义。
- 最小有效字号 7.5 pt；标题 8.4–8.8 pt。图内不放说明段落、白底文字框或压在 CAD/数据上的文字。
- 定性结果必须由 `figure_data.map_processed_faces` 按 D-028 逐项映射回原始三角面；点数、顺序或体素坐标不一致即失败。
- 结果图不以程序化几何或 Oracle 标签冒充网络输出；缺少原网格、检查点或评测产物时明确失败。
- 图 1、7、9 对 Fusion 检查点的留出身份运行时 fail-closed。

## 固定案例

| 图 | 数据源与案例 | 身份/用途 |
|---|---|---|
| 1 | Fusion `23632_5c8e8093_0000`、`23954_a8c09819_0000`、`115518_a1bf907b_0000:16` | 标签、点级留出推理、D-020 方向留出推理 |
| 2 | Fusion `119907_90a6e5af_0000` | +Z/+Y 真实支撑接触面 |
| 6 | Fusion `62955_58bbef9f_0000` / `137290_d81443d2_0000` | 同为 84 个保留面；面积接近、不可达率显著不同 |
| 7 | Fusion `138499_e52099a3_0000` / Thingi10K `1028708` | 检查点留出 / 跨域 test |
| 9 | Fusion `115518_a1bf907b_0000:16` | D-020 refined、混合方向、Top-1 正确；具体一致率由图中检查点输出给出 |
| 10 | Fusion `116082_b59d8605_0002` | 固定代表性高误差 test 案例，不称绝对最坏件 |

原网格目录按 `configs/paths.yaml` 解析（见仓库根 README），可在相应图脚本中用 `--root` 覆盖。原网格缺失时不使用程序化替代。

## 权威中间产物

| 产物 | 生成工具 | 消费图 |
|---|---|---|
| `artifacts/cache/figures/point_checkpoint.pt` | `train_point_checkpoint.py` | 1、7 |
| `artifacts/cache/figures/direction_checkpoint.pt` | `train_direction_checkpoint.py` | 1、9 |
| `artifacts/runs/true_triangle_area_check/result.json` | `experiments/true_triangle_area_check.py` | 6 |
| `artifacts/runs/baseline_comparison/result.json` | `experiments/baseline_comparison.py` | 8 左 |
| `artifacts/runs/shape_context_ablation/result.json` | `experiments/shape_context_ablation.py` | 8 右 |
| `artifacts/runs/failure_analysis/{result.json,error_boundary_case.npz}` | `experiments/failure_analysis.py --figure-case ...` | 10 |

结果文件保存生成图所需的逐模型值，图脚本经证据清单读取，不重新硬编码。GPU 训练存在小幅种子和运行时波动；一次成稿必须统一使用同一组产物，并让 `paper/manuscript/论文正文.md` 的数字与之一致（由 `numeric_claims.yaml` 核对）。结果 JSON 和 QA 报告属于 `artifacts/runs/` 证据；检查点和 contact sheet 属于 `artifacts/cache/`，由 QA 完成后的 TTL 清理器处理。

## 重生成

以下命令在仓库根目录、已激活 `saf` 环境下执行。实验结果已经冻结进证据清单时，可跳过第 2 步。

```bash
# 1) 检查点（写入 artifacts/cache）
python -m paper.pipeline.figure_scripts.train_point_checkpoint --max-models 1200 --epochs 150
python -m paper.pipeline.figure_scripts.train_direction_checkpoint --max-models 250 --epochs 120

# 2) 图件所需的实验结果与证据清单
python tools/reproduce_experiments.py --only true_triangle_area_check,baseline_comparison,shape_context_ablation,failure_analysis
python -m paper.pipeline.audits.freeze_evidence

# 3) 十幅图（顺序执行，不并发）
for name in framework_overview direction_dependence reach_criterion two_stage_labeling network_architecture \
            area_vs_accessibility prediction_heatmap baselines_ablation direction_field error_boundary; do
  python -m paper.pipeline.figure_scripts.$name
done

# 4) 面映射测试与严格图件 QA
python -m pytest tests/acceptance/test_figure_face_mapping.py -q
python -m paper.pipeline.figure_scripts.figure_qa --strict
```

## QA 输出

每幅图在 `artifacts/runs/figure_qa/<名称>.json` 写入布局诊断。`figure_qa.py` 汇总为 `report.json`，并检查：

- PNG 像素尺寸、600 dpi 物理尺寸、空白图与异常边缘留白；
- PDF 页面尺寸、字体嵌入和 Type 3 字体；
- PDF 完整性（`pdf_integrity`）：逻辑文件长度应等于有效字节数，且以 `%%EOF` 结尾。该字段只报告，不阻断 QA；构建时图件会按有效字节暂存（见 `paper/pipeline/build_paper.py`）；
- 最小字号、非白名单文字碰撞、文字越界；
- CAD 占用率和需要语义色的面板覆盖率；
- `FIGURE_NAMES` 中的十幅图是否都有一对同名 PNG/PDF。

`artifacts/cache/figures/contact_sheet.png` 左列按 175 mm 原尺度组织，右列为 85 mm 缩小预览。它是可删除的 QA 临时物，不属于论文主图；自动 QA 通过后仍须人工检查轮廓、ROI、颜色、标注和证据关系。
