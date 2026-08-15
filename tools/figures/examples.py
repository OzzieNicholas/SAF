"""Immutable, auditable examples used by the publication figures.

Every qualitative result is tied to a named dataset item and a fixed camera.
Generators validate checkpoint holdout membership before producing an image.
"""
from dataclasses import dataclass


FUSION_ROOT = "E:/Fusion360Gallery/reconstruction"
THINGI_ROOT = "E:/Thingi10K/raw_meshes"


@dataclass(frozen=True)
class Example:
    source: str
    name: str
    label: str
    zoom: float = 1.45
    azimuth: float = 0.0
    elevation: float = 0.0
    roi_zoom: float = 2.15


FIG01_LABEL = Example("fusion", "23632_5c8e8093_0000", "几何标签案例", 1.42, -10.0, 7.0, 2.05)
FIG01_POINT = Example("fusion", "23954_a8c09819_0000", "点级留出件", 1.46, -12.0, 8.0, 2.25)
FIG02 = Example("fusion", "119907_90a6e5af_0000", "Fusion CAD", 1.40, -18.0, 10.0, 2.10)

# Chosen deterministically from fusion360_full: identical support-contact point
# counts (84) with the largest accessibility gap among exact count matches.
FIG06_PAIR = (
    Example("fusion", "62955_58bbef9f_0000", "全可达", 1.48, -18.0, 8.0, 2.20),
    Example("fusion", "137290_d81443d2_0000", "高不可达", 1.48, -12.0, 8.0, 2.20),
)

# Both Fusion examples are members of ckpt_point.pt's declared held-out set.
FIG07 = (
    Example("fusion", "138499_e52099a3_0000", "Fusion 留出件", 1.44, -12.0, 8.0, 2.15),
    Example("thingi", "1028708", "Thingi10K 跨域件", 1.42, -10.0, 8.0, 2.05),
)

FIG09 = Example("fusion", "115518_a1bf907b_0000", "方向级留出件", 1.50, -14.0, 7.0, 2.10)
FIG09_POINT_INDEX = 16
FIG10 = Example("fusion", "116082_b59d8605_0002", "代表性高误差留出件", 1.42, -18.0, 9.0, 2.30)


def assert_checkpoint_holdout(checkpoint, example, figure):
    """Fail closed when a qualitative Fusion example is not an unseen item."""
    if example.source != "fusion":
        return
    held_out = set(checkpoint.get("test_names", ()))
    if example.name not in held_out:
        raise RuntimeError(
            f"{figure}: {example.name} is not in the checkpoint's declared held-out set"
        )
