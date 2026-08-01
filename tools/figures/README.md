# 论文图件流水线

本目录生成 `paper/figures/` 中 10 幅主图。每幅图仅维护一套 `175 mm` 全栏版式，导出 600 dpi PNG 与字体嵌入 PDF；`85 mm` 仅由 QA contact sheet 作缩小压力测试。图题/图注唯一源稿为 `paper/figures/captions.md`。

## 不变量

- 颜色：蓝=可达，红=不可达，紫=FN，橙=支撑接触区或 FP，灰=零件；同一面板内橙色不得复用语义。
- 最小有效字号 7.5 pt；标题 8.4–8.8 pt。图内不放说明段落、白底文字框或压在 CAD/数据上的文字。
- 定性结果必须由 `_data.map_processed_faces` 按 D-028 逐项映射回原始三角面；点数、顺序或体素坐标不一致即失败。
- 结果图不以程序化几何或 Oracle 标签冒充网络输出；缺少原网格、检查点或评测产物时明确失败。
- `examples.py` 是案例 ID 与相机的唯一清单；图 1、7、9 对 Fusion 检查点留出身份运行时 fail-closed。

## 固定案例

| 图 | 数据源与案例 | 身份/用途 |
|---|---|---|
| 1 | Fusion `23632_5c8e8093_0000`、`23954_a8c09819_0000`、`101190_cfdcb477_0001:27` | 标签、点级留出推理、D-020 方向留出推理 |
| 2 | Fusion `119907_90a6e5af_0000` | +Z/+Y 真实支撑接触面 |
| 6 | Fusion `62955_58bbef9f_0000` / `137290_d81443d2_0000` | 同为 84 个保留面；面积接近、不可达率显著不同 |
| 7 | Fusion `138499_e52099a3_0000` / Thingi10K `1028708` | 检查点留出 / 跨域 test |
| 9 | Fusion `101190_cfdcb477_0001:27` | D-020 refined、混合方向、Top-1 正确、一致率 90.6% |
| 10 | Fusion `116082_b59d8605_0002` | 固定代表性高误差 test 案例，不称绝对最坏件 |

默认原网格根为：

- Fusion：`E:/Fusion360Gallery/reconstruction`
- Thingi10K：`E:/Thingi10K/raw_meshes`

可在相应图脚本中用 `--root` / `--thingi-root` 覆盖。原网格缺失时不使用程序化替代。

## 权威中间产物

| 产物 | 生成工具 | 消费图 |
|---|---|---|
| `runs/figures/ckpt_point.pt` | `tools/figures/_train_ckpt.py` | 1、7 |
| `runs/figures/ckpt_dir.pt` | `tools/figures/_train_dir_ckpt.py` | 1、9 |
| `runs/true_area/latest.json` | `tools/eval_true_area.py` | 6 |
| `runs/baselines/latest.json` | `tools/eval_baselines.py` | 8a |
| `runs/ablation/latest.json` | `tools/eval_ablation.py` | 8b |
| `runs/failure_audit/{failure.json,fig10_case.npz}` | `tools/failure_cases.py --figure-case ...` | 10 |

`latest.json` 保存生成图所需的逐模型值，而不是由图脚本重新硬编码。GPU 训练存在小幅种子/运行时波动；一次成稿必须统一使用同一组产物并同步 `paper/draft.md`、`paper/写作指引.md` 和图注。

## 重生成

以下命令在仓库根目录执行。昂贵的训练/评测产物已经存在时可直接从第 2 步开始。

```powershell
# 1) 中间产物；顺序执行，不并发训练
conda run -n saf python tools/figures/_train_ckpt.py --max-models 1200 --epochs 150
conda run -n saf python tools/figures/_train_dir_ckpt.py --root E:/Fusion360Gallery/reconstruction --max-models 250 --epochs 120
conda run -n saf python tools/eval_true_area.py --root E:/Fusion360Gallery/reconstruction
conda run -n saf python tools/eval_baselines.py --max-models 400 --epochs 80
conda run -n saf python tools/eval_ablation.py --max-models 400 --epochs 60
conda run -n saf python tools/failure_cases.py --max-models 400 --figure-case 116082_b59d8605_0002

# 2) 十图顺序重生成
$scripts = @(
  'fig01_framework.py', 'fig02_direction_dependence.py', 'fig03_criterion.py',
  'fig04_two_stage.py', 'fig05_network.py', 'fig06_area_vs_access.py',
  'fig07_prediction_heatmap.py', 'fig08_baselines_ablation.py',
  'fig09_direction_field.py', 'fig10_failure.py'
)
foreach ($script in $scripts) {
  conda run -n saf python (Join-Path 'tools/figures' $script)
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# 3) 面映射测试与严格图件 QA
conda run -n saf pytest tests/acceptance/test_figure_face_mapping.py -q
conda run -n saf python tools/figures/qa_figures.py --strict
```

## QA 输出

每个脚本在 `runs/figure_qa/fig*.json` 写入布局诊断。`qa_figures.py` 进一步检查：

- PNG 像素尺寸、600 dpi 物理尺寸、空白图与异常边缘留白；
- PDF 页面尺寸、字体嵌入和 Type 3 字体；
- 最小字号、非白名单文字碰撞、文字越界；
- CAD 占用率和需要语义色的面板覆盖率；
- 10 幅图是否一一对应 PNG/PDF。

`paper/figures/contact_sheet.png` 左列按 175 mm 原尺度组织，右列为 85 mm 缩小预览。自动 QA 通过后仍须人工检查轮廓、ROI、颜色、标注和证据关系；contact sheet 不属于论文主图。
