"""十幅主图的生成脚本与共享模块。

``FIGURE_NAMES`` 是图件的唯一清单，按正文中的出现顺序排列。每个名字同时是生成脚本名、
``paper/figures/`` 中的输出文件名和正文中的图片链接名。
共享模块：``journal_style``（期刊样式与导出）、``cad_render``（零件渲染与幽灵视图）、
``figure_data``（网格加载与样本面映射）、``figure_cases``（固定案例）、``figure_qa``（布局与文件质量检查）。
"""

FIGURE_NAMES = (
    "criterion_schematic",
    "method_overview",
    "labeler_schematic",
    "proxy_failure",
    "method_comparison",
    "result_gallery",
    "screening_figure",
    "cost_accuracy_frontier",
    "orientation_case",
    "failure_direction",
)
