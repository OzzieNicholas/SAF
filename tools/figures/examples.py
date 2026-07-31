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


FIG02 = Example("fusion", "23954_a8c09819_0000", "Fusion CAD", 1.42, -12.0, 8.0)

# Chosen deterministically from fusion360_full: identical support-contact point
# counts (77) with the largest accessibility gap among exact count matches.
FIG06_PAIR = (
    Example("fusion", "23035_6087bb57_0000", "接近全可达", 1.52, -18.0, 8.0),
    Example("fusion", "134918_d66774a6_0000", "接近全不可达", 1.52, -18.0, 8.0),
)

# Both Fusion examples are members of ckpt_point.pt's declared held-out set.
FIG07 = (
    Example("fusion", "49896_6387ac02_0000", "Fusion A", 1.48, -12.0, 6.0),
    Example("fusion", "23630_84ec484d_0000", "Fusion B", 1.48, 10.0, 6.0),
    Example("thingi", "100035", "Thingi10K", 1.48, -10.0, 8.0),
)


def assert_checkpoint_holdout(checkpoint, example, figure):
    """Fail closed when a qualitative Fusion example is not an unseen item."""
    if example.source != "fusion":
        return
    held_out = set(checkpoint.get("test_names", ()))
    if example.name not in held_out:
        raise RuntimeError(
            f"{figure}: {example.name} is not in the checkpoint's declared held-out set"
        )
