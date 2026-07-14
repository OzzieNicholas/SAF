"""物化数据集验收（D-016）：程序化件 build→落盘→load 复原，格式统一、非退化、标签=oracle。

守护 D-016 的统一 processed 数据集：`build_procedural` 写每模型 `.npz`{occ,points,labels} + `manifest.csv`
+ `dataset.json`；`load_dataset` 复原 `list[LabeledModel]` + manifest 行。区别于 test_data（守内存态
make_dataset），本模块守**物化后的产物**：round-trip 不损真值、按模型切分无泄漏、manifest 良构。
hermetic：build 到 tempfile 临时目录（不污染仓库、无矩阵乘、本地/CI 皆可跑）。缺依赖 → PENDING/skip。
"""

from unittest import SkipTest

from . import pending, result

_ARGS = dict(n_models=12, N=28, max_points=24, radius=3.0, n_directions=32, seed=0)
_COLS = ("name", "source", "split", "npz_path", "occ_shape", "n_points",
         "n_inaccessible", "inaccessible_frac", "radius", "n_directions", "seed")
_NAMES = ("ds_roundtrip", "ds_both_classes", "ds_split_by_model",
          "ds_labels_match_oracle", "ds_manifest_wellformed")


def _deps():
    import numpy, scipy  # noqa: F401
    from support_accessibility.data import dataset  # noqa: F401  （码补齐前 ImportError → 门 PENDING）
    from support_accessibility import oracle  # noqa: F401


def checks():
    try:
        _deps()
    except ImportError as e:
        return [pending(n, f"依赖未就绪：{e}", "D-016") for n in _NAMES]
    import tempfile
    import numpy as np
    from support_accessibility.data import dataset as DS
    from support_accessibility.oracle import SupportAccessibilityOracle
    out = []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            DS.build_procedural(tmp, **_ARGS)
            models, rows = DS.load_dataset(tmp)
            name2split = {r["name"]: r["split"] for r in rows}

            # ① round-trip：格式自洽
            shapes_ok = (len(models) == _ARGS["n_models"] and all(
                m.occ.ndim == 3 and m.occ.dtype == bool
                and m.points.ndim == 2 and m.points.shape[1] == 3
                and m.labels.shape[0] == m.points.shape[0]
                and np.asarray(m.labels).dtype == bool for m in models))
            out.append(result("ds_roundtrip", shapes_ok,
                              f"{len(models)} 件复原：(occ bool 3D, points (K,3), labels bool) 自洽", "D-016"))

            # ② 两类俱在（非退化）
            alllab = np.concatenate([m.labels for m in models])
            both = bool(alllab.any() and (~alllab).any())
            out.append(result("ds_both_classes", both,
                              f"不可达 {int(alllab.sum())}/{alllab.size}（两类俱在→非退化）", "D-016"))

            # ③ 按模型切分无泄漏
            tr = {n for n, s in name2split.items() if s == "train"}
            te = {n for n, s in name2split.items() if s == "test"}
            split_ok = (tr.isdisjoint(te) and len(te) > 0
                        and (tr | te) == {m.name for m in models})
            out.append(result("ds_split_by_model", split_ok,
                              f"train{len(tr)}/test{len(te)}：模型级无泄漏", "D-016"))

            # ④ 标签=oracle（物化未损真值）：取一含不可达件逐点复算
            m0 = next((m for m in models if m.labels.any()), models[0])
            o = SupportAccessibilityOracle(m0.occ, {"n_directions": _ARGS["n_directions"]})
            recomputed = np.array([o.label(p, m0.radius).value == "inaccessible" for p in m0.points])
            out.append(result("ds_labels_match_oracle",
                              bool(np.array_equal(recomputed, np.asarray(m0.labels))),
                              f"{m0.name}: 载入标签逐点复算=oracle（含 {int(m0.labels.sum())} 不可达）", "D-016"))

            # ⑤ manifest 良构
            cols_ok = bool(rows) and all(c in rows[0] for c in _COLS)
            count_ok = len(rows) == _ARGS["n_models"]
            frac_ok = all(abs(float(r["inaccessible_frac"]) * int(r["n_points"]) - int(r["n_inaccessible"])) < 1e-6
                          for r in rows if int(r["n_points"]) > 0)
            out.append(result("ds_manifest_wellformed", cols_ok and count_ok and frac_ok,
                              f"{len(rows)} 行·列齐={cols_ok}·占比自洽={frac_ok}", "D-016"))
    except Exception as e:
        out.append(result("ds_roundtrip", False, f"评估异常：{e}", "D-016"))
    return out


# —— pytest 入口（依赖就绪前 skip）——
def test_dataset_roundtrip_and_nondegenerate():
    """物化→复原：格式自洽、两类俱在（D-016）。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    import tempfile
    import numpy as np
    from support_accessibility.data import dataset as DS
    with tempfile.TemporaryDirectory() as tmp:
        DS.build_procedural(tmp, **_ARGS)
        models, _rows = DS.load_dataset(tmp)
    assert len(models) == _ARGS["n_models"]
    alllab = np.concatenate([m.labels for m in models])
    assert alllab.any() and (~alllab).any(), "物化数据集退化：只有一类"
    for m in models:
        assert m.occ.dtype == bool and m.points.shape[1] == 3
        assert m.labels.shape[0] == m.points.shape[0]


def test_dataset_split_no_leakage():
    """按模型切分，train/test 互斥（D-016 / H3 前提）。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    import tempfile
    from support_accessibility.data import dataset as DS
    with tempfile.TemporaryDirectory() as tmp:
        DS.build_procedural(tmp, **_ARGS)
        _models, rows = DS.load_dataset(tmp)
    tr = {r["name"] for r in rows if r["split"] == "train"}
    te = {r["name"] for r in rows if r["split"] == "test"}
    assert tr.isdisjoint(te) and len(te) > 0


def test_dataset_labels_match_oracle():
    """物化标签逐点=oracle（round-trip 不损真值，D-016）。"""
    try:
        _deps()
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    import tempfile
    import numpy as np
    from support_accessibility.data import dataset as DS
    from support_accessibility.oracle import SupportAccessibilityOracle
    with tempfile.TemporaryDirectory() as tmp:
        DS.build_procedural(tmp, **_ARGS)
        models, _rows = DS.load_dataset(tmp)
    m0 = next((m for m in models if m.labels.any()), models[0])
    o = SupportAccessibilityOracle(m0.occ, {"n_directions": _ARGS["n_directions"]})
    recomputed = np.array([o.label(p, m0.radius).value == "inaccessible" for p in m0.points])
    assert np.array_equal(recomputed, np.asarray(m0.labels))
