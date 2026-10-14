#!/usr/bin/env python3
"""固定留出模型：在固定零件切分上用多个训练种子各训练一次点级网络，保存权重与逐件预测，供下游共用。

协议：Fusion 前 400 件两类件，切分种子 0 按零件 0.6/0.2/0.2 切分（切分对所有训练种子相同），
训练集为训练切分加全部程序化件，80 轮。训练种子 0..N-1 只改变初始化与样本顺序。
基线对照、回归门、消融、失败分析、精度–耗时前沿、全分布筛查、方向评价与结果图件都读这同一组权重，
同一模型在全文各处只有一组分数（均值 ± 种子间标准差）。

产出 artifacts/runs/holdout_model/：
  seed<k>.pt    第 k 个训练种子的权重与切分名单
  result.json   运行信封 + 每个种子的留出集指标与逐件预测概率

用法：
  python experiments/holdout_model.py --seeds 5
"""
import argparse
import os

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths
from support_accessibility.runtime.run_records import RUN_ROOT

setup_console()

KIND = "holdout_model"
SPLIT_SEED = 0
MAX_MODELS = 400


def holdout_split(fusion):
    """固定留出协议的切分：前 MAX_MODELS 件两类件，按零件 0.6/0.2/0.2（切分种子 SPLIT_SEED）。返回 (train, val, test)。"""
    from support_accessibility.data import both_class, split_by_model
    return split_by_model(both_class(fusion)[:MAX_MODELS], frac_train=0.6, frac_val=0.2, seed=SPLIT_SEED)


def model_path(seed, run_dir=None):
    return os.path.join(run_dir or os.path.join(RUN_ROOT, KIND), f"seed{int(seed)}.pt")


def available_seeds(run_dir=None):
    """已训练的种子编号（升序）。"""
    import re
    root = run_dir or os.path.join(RUN_ROOT, KIND)
    found = [int(m.group(1)) for f in os.listdir(root) if (m := re.fullmatch(r"seed(\d+)\.pt", f))]
    return sorted(found)


def load_holdout_model(seed=0, device="cpu", run_dir=None):
    """读取一个训练种子的权重，返回 (net, checkpoint dict)。"""
    import torch
    from support_accessibility.models.convonet import ConvONetLite
    ckpt = torch.load(model_path(seed, run_dir), map_location=device)
    net = ConvONetLite().to(device)
    net.load_state_dict(ckpt["state_dict"])
    net.eval()
    return net, ckpt


def load_holdout_models(device="cpu", run_dir=None):
    """全部训练种子的 [(seed, net, ckpt)]。"""
    return [(s, *load_holdout_model(s, device, run_dir)) for s in available_seeds(run_dir)]


def predict_proba(net, model, device):
    """单个零件全部接触点的不可达概率 (K,)。"""
    import numpy as np
    import torch
    from support_accessibility.models.convonet import to_grid_coords
    occ = torch.as_tensor(np.asarray(model.occ, np.float32)).view(1, 1, *model.occ.shape).to(device)
    gc = to_grid_coords(model.points, model.occ.shape).to(device)
    with torch.no_grad():
        return torch.sigmoid(net(occ, gc)).cpu().numpy().reshape(-1)


def _direction_labels_task(task):
    from support_accessibility.data.dataset import load_model
    from support_accessibility.data.fusion360 import direction_labels
    name, npz_path, radius, mesh_path = task
    return direction_labels(load_model(npz_path, name, radius), mesh_path)


def refined_direction_labels(parts, fusion_dir, fusion_root, workers=8):
    """零件名 → 方向级标签 (K, D)（True 为可达），多进程生成；并核对「全部方向被挡」与点级标签逐点一致。"""
    from concurrent.futures import ProcessPoolExecutor
    import numpy as np
    from support_accessibility.data.dataset import rel_npz_path
    from support_accessibility.data.fusion360 import iter_final_designs
    mesh_of = dict(iter_final_designs(fusion_root))
    tasks = [(m.name, os.path.join(fusion_dir, rel_npz_path(m.name)), float(m.radius), mesh_of[m.name])
             for m in parts]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        viable = dict(zip([m.name for m in parts], pool.map(_direction_labels_task, tasks)))
    for m in parts:
        if not np.array_equal(~viable[m.name].any(axis=1), np.asarray(m.labels, bool)):
            raise RuntimeError(f"{m.name}: 方向级标签与点级标签不一致")
    return viable


def mean_std(values):
    """训练种子间的 (均值, 标准差)，保留 4 位小数。"""
    import numpy as np
    return round(float(np.mean(values)), 4), round(float(np.std(values)), 4)


def seeded(seed):
    """固定 numpy / torch 随机源并启用确定性 cuDNN（grid_sample 反向在 CUDA 上仍有微小非确定性）。"""
    import numpy as np
    import torch
    np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def train_convonet(train_models, epochs, seed, device, net_factory=None, targets=None, log=True):
    """按固定协议训练一个网络（Adam 1e-3、权重衰减 1e-4、BCE、一件一批）。返回训练好的网络。

    targets 缺省为各零件的点级不可达标签；方向级模型传入每件 (K, D) 的被挡标签。
    """
    import numpy as np
    import torch
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    seeded(seed)
    net = (net_factory or ConvONetLite)().to(device)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
    lossf = torch.nn.BCEWithLogitsLoss()
    data = []
    for i, m in enumerate(train_models):
        occ = torch.as_tensor(np.asarray(m.occ, np.float32)).view(1, 1, *m.occ.shape).to(device)
        y = m.labels if targets is None else targets[i]
        data.append((occ, to_grid_coords(m.points, m.occ.shape).to(device),
                     torch.as_tensor(np.asarray(y, np.float32)).to(device)))
    for epoch in range(epochs):
        net.train()
        total = 0.0
        for i in torch.randperm(len(data)):
            occ, gc, y = data[i]
            opt.zero_grad()
            loss = lossf(net(occ, gc), y)
            loss.backward()
            opt.step()
            total += float(loss)
        if log and (epoch + 1) % 20 == 0:
            print(f"  seed {seed} epoch {epoch + 1} loss={total / len(data):.4f}", flush=True)
    net.eval()
    return net


def main():
    ap = argparse.ArgumentParser(description="固定留出模型：多训练种子，供下游实验和图件共用")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--procedural", default=str(paths.processed_root("procedural")))
    ap.add_argument("--seeds", type=int, default=5, help="训练种子数（0..N-1）；切分固定为种子 0")
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--out-dir", default=None, help="输出目录；默认 artifacts/runs/holdout_model（试跑请指定其他目录）")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from support_accessibility.runtime.run_records import write_result
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility import eval as E

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    fus, _ = load_dataset(a.fusion)
    proc, _ = load_dataset(a.procedural)
    ftr, fva, fte = holdout_split(fus)
    print(f"device={dev} train={len(ftr)}(+proc {len(proc)}) val={len(fva)} test={len(fte)}", flush=True)
    out_dir = a.out_dir or os.path.join(RUN_ROOT, KIND)
    os.makedirs(out_dir, exist_ok=True)
    for stale in [f for f in os.listdir(out_dir) if f.endswith(".pt")]:
        os.remove(os.path.join(out_dir, stale))

    runs = []
    for seed in range(a.seeds):
        net = train_convonet(ftr + proc, a.epochs, seed, dev)
        torch.save({"state_dict": net.state_dict(), "seed": seed, "split_seed": SPLIT_SEED, "epochs": a.epochs,
                    "max_models": MAX_MODELS, "train_names": [m.name for m in ftr],
                    "val_names": [m.name for m in fva], "test_names": [m.name for m in fte]},
                   model_path(seed, out_dir))
        per_model, P, G = [], [], []
        for m in fte:
            prob = predict_proba(net, m, dev)
            gold = np.asarray(m.labels, bool)
            P.append(prob >= 0.5); G.append(gold)
            per_model.append({"name": m.name, "n_points": int(gold.size),
                              "f1": float(E.f1_inaccessible(prob >= 0.5, gold)),
                              "iou": float(E.iou_inaccessible(prob >= 0.5, gold)),
                              "prob": [round(float(v), 5) for v in prob]})
        f1s = np.array([r["f1"] for r in per_model])
        P, G = np.concatenate(P), np.concatenate(G)
        runs.append({"seed": seed, "pooled_f1": round(float(E.f1_inaccessible(P, G)), 4),
                     "pooled_iou": round(float(E.iou_inaccessible(P, G)), 4),
                     "part_f1_mean": round(float(f1s.mean()), 4), "part_f1_median": round(float(np.median(f1s)), 4),
                     "weights": os.path.basename(model_path(seed, out_dir)), "per_model": per_model})
        print(f"seed {seed}: pooled F1 {runs[-1]['pooled_f1']} part-mean {runs[-1]['part_f1_mean']}", flush=True)

    pooled = np.array([r["pooled_f1"] for r in runs]); part = np.array([r["part_f1_mean"] for r in runs])
    rep = write_result(KIND, {
        "device": dev, "seeds": a.seeds, "split_seed": SPLIT_SEED, "epochs": a.epochs, "max_models": MAX_MODELS,
        "protocol": "first 400 both-class Fusion parts; model-level 0.6/0.2/0.2 split with split seed 0; "
                    "train = train split + all procedural parts; training seeds 0..N-1",
        "n_train_models": len(ftr), "n_procedural": len(proc), "n_test_models": len(fte),
        "n_test_points": int(sum(m.points.shape[0] for m in fte)),
        "pooled_f1_mean": round(float(pooled.mean()), 4), "pooled_f1_std": round(float(pooled.std()), 4),
        "part_f1_mean_mean": round(float(part.mean()), 4), "part_f1_mean_std": round(float(part.std()), 4),
        "runs": runs,
    }, os.path.join(out_dir, "result.json"), (a.fusion, a.procedural))
    print("HOLDOUT_MODEL " + json.dumps({k: v for k, v in rep.items() if k != "runs"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
