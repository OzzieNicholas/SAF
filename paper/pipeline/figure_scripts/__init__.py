"""十幅主图的生成脚本与共享模块。

``FIGURE_NAMES`` 是图件的唯一清单，按正文中的出现顺序排列。每个名字同时是生成脚本名、
``paper/figures/`` 中的输出文件名和正文中的图片链接名。
共享模块：``figure_style``（样式与导出）、``figure_data``（网格与渲染助手）、``figure_cases``（固定案例）、
``figure_qa``（布局与文件质量检查）；检查点由 ``train_point_checkpoint`` 与 ``train_direction_checkpoint`` 生成。
"""

FIGURE_NAMES = (
    "framework_overview",
    "direction_dependence",
    "reach_criterion",
    "two_stage_labeling",
    "network_architecture",
    "area_vs_accessibility",
    "prediction_heatmap",
    "baselines_ablation",
    "direction_field",
    "error_boundary",
)
