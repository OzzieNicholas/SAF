"""冻结的标签口径（D-021）：唯一来源是 ``configs/oracle_params.yaml``。

代码里所有「方向数、边界带宽、分辨率、工具半径、悬垂阈值」的默认值都从这里取，不再各处硬编码。
改动这些数值必须先在决策台账新增 supersede 条目，再改 yaml。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .data_paths import CONFIG_DIR


@dataclass(frozen=True)
class FrozenParams:
    n_directions: int        # 全局候选逼近方向数（取下半球后约一半）
    epsilon_voxels: float    # 边界带宽（体素），带内交给精确胶囊求交定夺
    overhang_deg: float      # 悬垂角阈值（度）：n·d̂ < -cos(阈值) 的面计入支撑接触区
    resolution: int          # 占据栅格最长边的体素数
    radius_world: float      # 球工具半径（归一尺度，零件最长边 = 1）


def load_frozen_params(path: str | Path | None = None) -> FrozenParams:
    with Path(path or CONFIG_DIR / "oracle_params.yaml").open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    return FrozenParams(
        n_directions=int(raw["oracle"]["n_directions"]),
        epsilon_voxels=float(raw["oracle"]["epsilon_voxels"]),
        overhang_deg=float(raw["geometry"]["overhang_angle_deg"]),
        resolution=int(raw["data"]["resolution"]),
        radius_world=float(raw["data"]["radius_world"]),
    )


FROZEN = load_frozen_params()
