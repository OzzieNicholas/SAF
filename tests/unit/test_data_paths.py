"""数据路径解析：优先级、相对默认值，以及逻辑引用不泄漏本机路径。"""


def test_data_paths_follow_config_priority_and_logical_refs_are_portable(monkeypatch, tmp_path):
    from support_accessibility.runtime import data_paths
    from support_accessibility.runtime.data_paths import logical_data_ref, resolve_data_paths

    config = tmp_path / "configs"
    config.mkdir()
    (config / "paths.yaml").write_text(
        "data_root: base\nlayout:\n  fusion360: raw/fusion\n  thingi10k: raw/thingi\n  processed: processed\n",
        encoding="utf-8")
    monkeypatch.setattr(data_paths, "CONFIG_DIR", config)
    for name in ("SAF_DATA_ROOT", "SAF_FUSION360_ROOT", "SAF_THINGI_ROOT"):
        monkeypatch.delenv(name, raising=False)

    # 默认值：相对路径以仓库根为基准
    assert resolve_data_paths().data_root == data_paths.REPO_ROOT / "base"

    # paths.local.yaml 覆盖默认值，环境变量覆盖本地配置，参数覆盖环境变量
    (config / "paths.local.yaml").write_text("data_root: local_root\n", encoding="utf-8")
    assert resolve_data_paths().data_root == data_paths.REPO_ROOT / "local_root"
    monkeypatch.setenv("SAF_DATA_ROOT", str(tmp_path / "env_root"))
    assert resolve_data_paths().data_root == tmp_path / "env_root"
    paths = resolve_data_paths(tmp_path / "arg_root")
    assert paths.data_root == tmp_path / "arg_root"
    assert paths.processed_root("procedural") == tmp_path / "arg_root" / "processed" / "procedural"

    # 逻辑引用不泄漏本机路径
    assert logical_data_ref(paths.processed_root("procedural"), paths) == "dataset://procedural"
    assert logical_data_ref(paths.fusion360_root / "a.obj", paths) == "source://fusion360_gallery/reconstruction/a.obj"
    assert str(tmp_path) not in logical_data_ref(tmp_path / "secret" / "mesh.obj", paths)


def test_layout_entries_may_be_absolute(monkeypatch, tmp_path):
    from support_accessibility.runtime import data_paths

    config = tmp_path / "configs"
    config.mkdir()
    (config / "paths.yaml").write_text(
        "data_root: base\nlayout:\n  fusion360: raw/fusion\n  thingi10k: raw/thingi\n  processed: processed\n",
        encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    (config / "paths.local.yaml").write_text(f"layout:\n  fusion360: {elsewhere.as_posix()}\n", encoding="utf-8")
    monkeypatch.setattr(data_paths, "CONFIG_DIR", config)
    for name in ("SAF_DATA_ROOT", "SAF_FUSION360_ROOT", "SAF_THINGI_ROOT"):
        monkeypatch.delenv(name, raising=False)

    paths = data_paths.resolve_data_paths()
    assert paths.fusion360_root == elsewhere
    assert paths.thingi_root == data_paths.REPO_ROOT / "base" / "raw" / "thingi"


def test_frozen_parameters_match_the_registered_values():
    from support_accessibility.runtime.frozen_params import FROZEN

    assert (FROZEN.n_directions, FROZEN.epsilon_voxels, FROZEN.overhang_deg, FROZEN.resolution, FROZEN.radius_world) \
        == (128, 1.5, 45.0, 48, 0.05)
