"""数据：带标签样本记录、程序化已知答案件，以及 Fusion360 / Thingi10K 的 ingest 与统一数据集读写。"""

from .procedural import (
    VoxelCase,
    blind_cavity_case,
    down_facing_points,
    flagship_pair,
    make_dataset,
    open_downface_case,
    slab_with_blind_hole,
)
from .records import LabeledModel, both_class, split_by_model

__all__ = [
    "LabeledModel", "VoxelCase", "blind_cavity_case", "both_class", "down_facing_points", "flagship_pair",
    "make_dataset", "open_downface_case", "slab_with_blind_hole", "split_by_model",
]
