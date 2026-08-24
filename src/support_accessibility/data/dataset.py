"""统一 processed 数据集：物化器 + 载入器（D-016）。

把可信的**程序化源**（make_dataset）物化成统一 on-disk 记录；具体输出位置由
``tools/data_paths.py`` 解析到外部 ``E:/Work/Data/Temporary/SAF``，本包不决定仓库内路径：
  <out>/models/<name>.npz   每模型 np.savez_compressed{occ(bool 3D), points(f4 (K,3)), labels(bool (K,))}
  <out>/manifest.csv        每模型一行全部标量元数据（单一之家；含 split/radius 供复原）
  <out>/dataset.json        数据集级 provenance（build 参数 + 切分统计；无时间戳→ manifest/json 字节可复现）

复用 data.make_dataset / split_by_model / LabeledModel（不重造）；Fusion360/Thingi 按同格式接入
（source 字段 {procedural,fusion360,thingi10k}，见 governance/decisions.md D-023）。单位=**体素**（对齐 oracle 口径与
make_dataset）；configs/params.yaml 归一单位的"单位桥"属真实网格接入（deferred）。
numpy 在函数内 import（沿袭 data 包约定：模块级只 stdlib，`import dataset` 不依赖 numpy）。
"""

import csv
import json
import os

RECORD_SCHEMA_VERSION = 1
MANIFEST = "manifest.csv"
DATASET_JSON = "dataset.json"
MODELS_DIR = "models"
COLUMNS = ["name", "source", "split", "npz_path", "occ_shape", "n_points",
           "n_inaccessible", "inaccessible_frac", "radius", "n_directions", "seed"]


def _rel_npz(name):
    return f"{MODELS_DIR}/{name}.npz"


def save_model(rec, path):
    """LabeledModel → np.savez_compressed{occ,points,labels}（体素单位）。"""
    import numpy as np
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(path,
                        occ=np.asarray(rec.occ, dtype=bool),
                        points=np.asarray(rec.points, dtype=np.float32),
                        labels=np.asarray(rec.labels, dtype=bool))


def load_model(path, name, radius):
    """(.npz, name, radius) → LabeledModel。"""
    import numpy as np
    from support_accessibility.data import LabeledModel
    with np.load(path) as z:
        return LabeledModel(name=name, occ=z["occ"].astype(bool),
                            points=z["points"].astype(np.float32),
                            labels=z["labels"].astype(bool), radius=float(radius))


def build_procedural(out_dir, n_models=16, N=28, max_points=24, radius=3.0,
                     n_directions=128, seed=0, frac_train=0.6, frac_val=0.2):
    """程序化件 → 物化统一数据集（幂等：清 out_dir/models 旧 .npz 后重写 + manifest + dataset.json）。返回 out_dir。

    按模型三切 train/val/test（D-016 切分 {train,val,test}）。val 为预留 held-out：超参先验固定、当前工具未在 val 上调参。
    """
    import numpy as np
    from support_accessibility.data import make_dataset, split_by_model
    models = make_dataset(n_models=n_models, N=N, max_points=max_points,
                          radius=radius, n_directions=n_directions, seed=seed)
    tr, va, te = split_by_model(models, frac_train=frac_train, frac_val=frac_val, seed=seed)
    split_of = {m.name: "train" for m in tr}
    split_of.update({m.name: "val" for m in va})
    split_of.update({m.name: "test" for m in te})

    models_dir = os.path.join(out_dir, MODELS_DIR)
    if os.path.isdir(models_dir):                       # 幂等：只清本目录 .npz，不动其它
        for fn in os.listdir(models_dir):
            if fn.endswith(".npz"):
                os.remove(os.path.join(models_dir, fn))
    os.makedirs(models_dir, exist_ok=True)

    rows = []
    for m in models:
        rel = _rel_npz(m.name)
        save_model(m, os.path.join(out_dir, rel))
        lab = np.asarray(m.labels, dtype=bool)
        n_pts, n_inacc = int(lab.size), int(lab.sum())
        rows.append({
            "name": m.name, "source": "procedural", "split": split_of[m.name],
            "npz_path": rel, "occ_shape": "x".join(map(str, m.occ.shape)),
            "n_points": n_pts, "n_inaccessible": n_inacc,
            "inaccessible_frac": (n_inacc / n_pts) if n_pts else 0.0,
            "radius": float(m.radius), "n_directions": int(n_directions), "seed": int(seed),
        })

    with open(os.path.join(out_dir, MANIFEST), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    meta = {
        "schema_version": RECORD_SCHEMA_VERSION, "source": "procedural",
        "record_keys": ["occ", "points", "labels"], "units": "voxel",
        "build_params": {"n_models": n_models, "N": N, "max_points": max_points,
                         "radius": radius, "n_directions": n_directions, "seed": seed,
                         "frac_train": frac_train, "frac_val": frac_val},
        "split": {"n_train": len(tr), "n_val": len(va), "n_test": len(te)},
    }
    with open(os.path.join(out_dir, DATASET_JSON), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, sort_keys=True)
    return out_dir


def load_dataset(root):
    """root → (list[LabeledModel], list[dict] manifest 行)。按 manifest 顺序复原。"""
    with open(os.path.join(root, MANIFEST), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    models = [load_model(os.path.join(root, r["npz_path"]), r["name"], r["radius"]) for r in rows]
    return models, rows
