"""解析 SAF 的数据位置。

仓库只在 ``configs/paths.yaml`` 登记相对路径；机器相关的位置通过命令行、环境变量或
不入库的 ``configs/paths.local.yaml`` 提供，优先级见 ``configs/paths.yaml`` 头部说明。
各脚本只通过本模块取得路径，不自行拼接。
"""

from __future__ import annotations

from dataclasses import dataclass
import ntpath
import os
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO_ROOT / "configs"
PROCESSED_DATASETS = ("fusion360", "procedural", "thingi10k")


@dataclass(frozen=True)
class DataPaths:
    """数据根、处理后数据集的父目录，以及两个公开原始网格目录。"""

    data_root: Path
    processed_dir: Path
    fusion360_root: Path
    thingi_root: Path

    def processed_root(self, dataset: str) -> Path:
        """返回某个处理后数据集的目录 ``processed/<数据集>``。"""
        name = str(dataset).strip().replace("\\", "/").strip("/")
        if not name or name in {".", ".."} or ".." in name.split("/"):
            raise ValueError(f"invalid dataset name: {dataset!r}")
        return self.processed_dir / name


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle) or {}
    if not isinstance(value, dict):
        raise ValueError(f"path config must be a mapping: {path}")
    return value


def _as_path(raw: str | os.PathLike[str]) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def _merged_config() -> dict:
    """默认配置被本机覆盖配置逐层合并（layout 按键合并）。"""
    merged = _load_yaml(CONFIG_DIR / "paths.yaml")
    local = _load_yaml(CONFIG_DIR / "paths.local.yaml")
    layout = {**merged.get("layout", {}), **local.get("layout", {})}
    merged.update(local)
    merged["layout"] = layout
    return merged


def resolve_data_paths(data_root: str | os.PathLike[str] | None = None) -> DataPaths:
    """按「参数 > 环境变量 > paths.local.yaml > paths.yaml」解析数据位置。"""
    config = _merged_config()
    layout = config["layout"]
    root = _as_path(data_root or os.environ.get("SAF_DATA_ROOT") or config["data_root"])

    def under_root(key: str) -> Path:
        return _as_path(layout[key]) if Path(layout[key]).is_absolute() else root / layout[key]

    fusion = _as_path(os.environ.get("SAF_FUSION360_ROOT") or under_root("fusion360"))
    thingi = _as_path(os.environ.get("SAF_THINGI_ROOT") or under_root("thingi10k"))
    return DataPaths(root, under_root("processed"), fusion, thingi)


def _relative_to(path: Path, root: Path) -> str | None:
    """返回 POSIX 形式的相对路径；不要求二者存在。"""
    raw_path, raw_root = str(path), str(root)
    if ntpath.splitdrive(raw_path)[0] or ntpath.splitdrive(raw_root)[0]:
        path_norm = ntpath.normcase(ntpath.normpath(raw_path))
        root_norm = ntpath.normcase(ntpath.normpath(raw_root))
        try:
            relative = ntpath.relpath(path_norm, root_norm)
        except ValueError:
            return None
        if relative == ".." or relative.startswith("..\\"):
            return None
        return relative.replace("\\", "/")
    try:
        return path.resolve(strict=False).relative_to(root.resolve(strict=False)).as_posix()
    except ValueError:
        return None


def _looks_absolute(raw: str) -> bool:
    """在 POSIX 上也能识别 Windows 路径。"""
    return Path(raw).is_absolute() or ntpath.isabs(raw) or bool(ntpath.splitdrive(raw)[0])


def logical_data_ref(
    raw: str | os.PathLike[str] | None, paths: DataPaths | None = None
) -> str:
    """把本机数据路径转成可移植的逻辑引用，避免运行记录泄漏机器路径。

    处理后数据集写成 ``dataset://<名>``，原始网格写成 ``source://...``；
    无法识别的绝对路径统一折叠为 ``external://unidentified``。
    """
    if raw is None or str(raw) == "":
        return ""
    text = str(raw)
    if text.startswith(("dataset://", "source://", "external://")):
        return text.replace("\\", "/")
    if not _looks_absolute(text):
        return Path(text).as_posix()

    resolved = Path(text)
    paths = paths or resolve_data_paths()
    for dataset in PROCESSED_DATASETS:
        relative = _relative_to(resolved, paths.processed_root(dataset))
        if relative is not None:
            suffix = f"/{relative}" if relative != "." else ""
            return f"dataset://{dataset}{suffix}"
    for source, root in (
        ("fusion360_gallery/reconstruction", paths.fusion360_root),
        ("thingi10k/raw_meshes", paths.thingi_root),
    ):
        relative = _relative_to(resolved, root)
        if relative is not None:
            suffix = f"/{relative}" if relative != "." else ""
            return f"source://{source}{suffix}"
    return "external://unidentified"


def resolve_logical_data_ref(
    reference: str, paths: DataPaths | None = None
) -> Path | None:
    """把 ``dataset://`` 逻辑引用还原为本机路径（供门检查使用）。"""
    if not isinstance(reference, str) or not reference.startswith("dataset://"):
        return None
    parts = reference.removeprefix("dataset://").split("/")
    if not parts or parts[0] not in PROCESSED_DATASETS:
        return None
    return (paths or resolve_data_paths()).processed_root(parts[0]).joinpath(*parts[1:])
