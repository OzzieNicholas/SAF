"""Fusion 360 reconstruction 网格 ingest 验收（D-017）。

两半：
  ① 纯 stdlib（**裸环境就跑**）：OBJ 文本解析（quad 扇形三角化）、final 过滤（.obj 有同名 .json 兄弟）。
  ② 几何栈（缺 numpy/igl/trimesh → PENDING/skip）：box 合成网格端到端物化 → D-016 记录，
     source=fusion360、human_signoff=false（须经量化审核签收，D-025）。

守护 D-017 换主源的落地：真实 CAD 网格 load_obj→normalize→occupancy→下朝点→oracle 打标→统一 processed。
不断言具体标签值（那是 oracle 的活，见 test_known_answers/test_mesh_frontend），只断言管线结构自洽。
"""

from unittest import SkipTest

from . import pending, result
from tests.fixtures import known_answer_meshes as K

_OBJ = "v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nf 1 2 3 4\n"     # 单 quad → 扇形 2 三角


def _check_obj_parse():
    from support_accessibility.data.fusion360 import _parse_obj_text
    verts, faces = _parse_obj_text(_OBJ)
    ok = len(verts) == 4 and faces == [[0, 1, 2], [0, 2, 3]]
    return result("f360_obj_parse", ok, f"4 顶点、quad 扇形三角化→{faces}", "D-017")


def _check_final_filter():
    import os
    import tempfile
    from support_accessibility.data.fusion360 import iter_final_designs
    with tempfile.TemporaryDirectory() as d:
        # final：<id>_<hash>_<reconIdx>，有同名 .json 兄弟（存在标记，不解析内容）
        open(os.path.join(d, "p_a_c_0000.obj"), "w").close()
        open(os.path.join(d, "p_a_c_0000.json"), "w").close()
        # 中间拉伸步骤：两组 _NNNN、无 .json → 不产出
        open(os.path.join(d, "p_a_c_0000_0001.obj"), "w").close()
        open(os.path.join(d, "p_a_c_0000_0003.obj"), "w").close()
        open(os.path.join(d, "note.txt"), "w").close()
        # .json 无对应 .obj（孤儿）→ 不产出
        open(os.path.join(d, "orphan_0001.json"), "w").close()
        got = sorted(n for n, _ in iter_final_designs(d))
    return result("f360_final_filter", got == ["p_a_c_0000"], f"取 final（有 .json 兄弟）→{got}", "D-017")


def _check_ingest_box():
    import json
    import os
    import tempfile
    from support_accessibility.data import fusion360 as F, dataset as DS
    meshes = [(f"box_{i}", *K.box_vf((6.0, 6.0, 4.0 + i))) for i in range(3)]
    with tempfile.TemporaryDirectory() as tmp:
        F.build_from_meshes(meshes, tmp, resolution=40, n_directions=32)
        models, rows = DS.load_dataset(tmp)
        with open(os.path.join(tmp, DS.DATASET_JSON), encoding="utf-8") as f:
            meta = json.load(f)
    shapes_ok = all(m.occ.ndim == 3 and m.occ.dtype == bool and m.points.shape[1] == 3
                    and m.labels.shape[0] == m.points.shape[0] for m in models)
    src_ok = bool(rows) and all(r["source"] == "fusion360" for r in rows)
    signoff_ok = meta.get("human_signoff") is False
    ok = len(models) == 3 and shapes_ok and src_ok and signoff_ok
    return result("f360_ingest_box", ok,
                  f"{len(models)} 件物化·source=fusion360={src_ok}·human_signoff={meta.get('human_signoff')}", "D-017")


def _safe(fn):
    try:
        return fn()
    except Exception as e:
        return result(fn.__name__.replace("_check_", "f360_"), False, f"异常：{e}", "D-017")


def checks():
    out = [_safe(_check_obj_parse), _safe(_check_final_filter)]      # 纯 stdlib，恒跑
    try:
        import numpy, igl, trimesh  # noqa: F401
        from support_accessibility import oracle  # noqa: F401
    except ImportError as e:
        return out + [pending("f360_ingest_box", f"依赖未就绪：{e}", "D-017")]
    return out + [_safe(_check_ingest_box)]


# —— pytest 入口 ——
def test_obj_parse_and_final_filter():
    """纯 stdlib：OBJ quad 三角化 + final 设计过滤（无几何栈也应绿）。"""
    r1, r2 = _check_obj_parse(), _check_final_filter()
    assert r1["status"] == "PASS", r1["detail"]
    assert r2["status"] == "PASS", r2["detail"]


def test_ingest_box_end_to_end():
    """box 合成网格 → 统一 processed 记录（source=fusion360、human_signoff=false，D-017/D-018）。"""
    try:
        import numpy, igl, trimesh  # noqa: F401
        from support_accessibility import oracle  # noqa: F401
    except ImportError as e:
        raise SkipTest(f"依赖未就绪：{e}")
    r = _check_ingest_box()
    assert r["status"] == "PASS", r["detail"]
