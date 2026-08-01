#!/usr/bin/env python3
"""失败案例分析（阶段8；需 torch）。神经二分预测 vs oracle 在**留出真实件**上何处/为何误判。

训 ConvONet-lite 二分头（镜像 H3 制度），留出集上定位 pred≠gold 的点，按**几何难度**刻画：
每点可达方向数 n_viable（oracle direction_labels，D-024）——n_viable 小=勉强可达/临界=最难。
产出：整体 F1、误判率、假正(FP:判不可达实可达)/假负(FN:判可达实不可达)拆分、按 n_viable 分箱误判率，
+ 误判最多的几件审计 PNG（occ 剪影 + 误判掩码）。self-add src。

用法：
  conda run -n saf python tools/failure_cases.py --fusion data/processed/fusion360_full --max-models 400
"""
import argparse
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_ROOT), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

for _s in (sys.stdout, sys.stderr):            # Windows GBK 控制台防崩：⟹/⟺ 等非 GBK 字符（仿 tests/gate.py）
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def both_class(ms):
    import numpy as np
    return [m for m in ms if np.asarray(m.labels).size and np.asarray(m.labels).any() and (~np.asarray(m.labels)).any()]


def main():
    ap = argparse.ArgumentParser(description="失败案例分析（阶段8）")
    ap.add_argument("--fusion", default="data/processed/fusion360_full")
    ap.add_argument("--procedural", default="data/processed/procedural_v1")
    ap.add_argument("--max-models", type=int, default=400, help="截取 fusion both-class 前 N 件（可解性）")
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seeds", type=int, default=5, help="训练种子数：按种子聚合误判分箱 mean±std（减小小样本噪声，稳住 FP/FN 与分箱结论）")
    ap.add_argument("--n-directions", type=int, default=128)
    ap.add_argument("--outdir", default=None, help="审计 PNG 输出目录（默认 scratch 内）")
    ap.add_argument("--top-audit", type=int, default=4)
    ap.add_argument("--figure-case", default="116082_b59d8605_0002",
                    help="图10固定留出案例；必须属于本次首种子测试集")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data import split_by_model
    from support_accessibility.oracle import SupportAccessibilityOracle
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    from support_accessibility import eval as E, viz as VIZ

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    fus, _ = load_dataset(a.fusion)
    proc, _ = load_dataset(a.procedural)
    fus_bc = both_class(fus)[:a.max_models]
    ftr, _fva, fte = split_by_model(fus_bc, frac_train=0.6, frac_val=0.2, seed=a.seed)
    fte = [m for m in fte if m.points.shape[0] > 0]
    print(f"device={dev} fusion_bc={len(fus_bc)} train={len(ftr)} test={len(fte)}", flush=True)

    def prep(m):
        occ = torch.as_tensor(np.asarray(m.occ, np.float32)).view(1, 1, *m.occ.shape).to(dev)
        return occ, to_grid_coords(m.points, m.occ.shape).to(dev)

    # oracle 每点 n_viable（难度代理）——**种子无关**，只算一次（昂贵的方向 ray-march；oracle 每件构一次复用 EDT）
    def _nviable(m):
        o = SupportAccessibilityOracle(m.occ, {"n_directions": a.n_directions})
        return np.array([int(o.direction_labels(p, m.radius).sum()) for p in m.points])
    nv_by = {m.name: _nviable(m) for m in fte}
    NV = np.concatenate([nv_by[m.name] for m in fte])
    G = np.concatenate([np.asarray(m.labels, bool) for m in fte])
    bins = {"0": NV == 0, "1-2": (NV >= 1) & (NV <= 2), "3-5": (NV >= 3) & (NV <= 5), "6+": NV >= 6}

    def train_predict(seed):
        """按种子从头训一个点级网络，返回留出集逐件预测。cudnn 确定；grid_sample 反向 CUDA 微噪由多种子聚合吸收。"""
        np.random.seed(seed); torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        net = ConvONetLite().to(dev)
        opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
        lossf = torch.nn.BCEWithLogitsLoss()
        data = [(prep(m), torch.as_tensor(np.asarray(m.labels, np.float32)).to(dev)) for m in (ftr + proc)]
        for _ in range(a.epochs):
            for i in torch.randperm(len(data)):
                (occ, gc), y = data[i]
                opt.zero_grad(); lossf(net(occ, gc), y).backward(); opt.step()
        net.eval()
        preds = {}
        with torch.no_grad():
            for m in fte:
                occ, gc = prep(m)
                preds[m.name] = (torch.sigmoid(net(occ, gc)) >= 0.5).cpu().numpy()
        return preds

    seeds = list(range(a.seed, a.seed + a.seeds))
    metrics, preds0 = [], None                                 # 逐种子标量 + 分箱率；preds0=首种子（审计/图10 定位）
    for si in seeds:
        preds = train_predict(si)
        P = np.concatenate([preds[m.name] for m in fte])
        err = P != G
        rec = {"error": float(err.mean()), "fp": float((P & ~G).mean()), "fn": float((~P & G).mean()),
               "f1": float(E.f1_inaccessible(P, G))}
        for k, v in bins.items():
            rec[f"bin_{k}"] = float(err[v].mean()) if v.any() else float("nan")
        metrics.append(rec)
        if si == seeds[0]:
            preds0 = preds
        print(f"seed{si} err={rec['error']:.3f} fp={rec['fp']:.3f} fn={rec['fn']:.3f} f1={rec['f1']:.3f}", flush=True)

    def ms(key):
        arr = np.array([r[key] for r in metrics], float)
        return round(float(np.nanmean(arr)), 3), round(float(np.nanstd(arr)), 3)

    # 首种子最糟件（审计 PNG + fig10 npz）
    per_model0 = [(m.name, int((preds0[m.name] != np.asarray(m.labels, bool)).sum()),
                   preds0[m.name] != np.asarray(m.labels, bool), m) for m in fte]
    outdir = a.outdir or os.path.join(_ROOT, "..", "runs", "failure_audit")
    emitted = []
    try:
        os.makedirs(outdir, exist_ok=True)
        for name, ne, emask, m in sorted(per_model0, key=lambda t: -t[1])[:a.top_audit]:
            if ne == 0:
                continue
            p = os.path.join(outdir, f"fail_{name}_{ne}err.png")
            VIZ.accessibility_montage(m.occ, m.points, emask, p)
            emitted.append(os.path.basename(p))
    except Exception as e:
        emitted = [f"(PNG 跳过：{str(e)[:50]})"]

    err_m, err_s = ms("error"); fp_m, fp_s = ms("fp"); fn_m, fn_s = ms("fn"); f1_m, f1_s = ms("f1")
    rep = {
        "test_models": len(fte), "test_points": int(G.size), "seeds": a.seeds,
        "f1_inaccessible": f1_m, "f1_inaccessible_std": f1_s,
        "error_rate": err_m, "error_rate_std": err_s,
        "false_pos_rate": fp_m, "false_pos_rate_std": fp_s,
        "false_neg_rate": fn_m, "false_neg_rate_std": fn_s,
        "gold_inacc_frac": round(float(G.mean()), 3),
        "error_rate_by_nviable": {k: ms(f"bin_{k}")[0] for k in bins},
        "error_rate_by_nviable_std": {k: ms(f"bin_{k}")[1] for k in bins},
        "nviable_share": {k: round(float(v.mean()), 3) for k, v in bins.items()},
        "audit_pngs": emitted, "audit_dir": os.path.normpath(outdir),
    }
    print("FAILURE_ANALYSIS " + json.dumps(rep))

    # —— 图件数据落盘（附加，不改判定口径）：聚合 rep + 首种子最糟件逐点 FP/FN/n_viable，供 tools/figures/fig10 ——
    try:
        json.dump(rep, open(os.path.join(outdir, "failure.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        case = next((item for item in per_model0 if item[0] == a.figure_case), None)
        if case is None:
            raise RuntimeError(f"figure case is not in the held-out set: {a.figure_case}")
        cname, cerrors, _cmask, cm = case
        cp = preds0[cname]; cg = np.asarray(cm.labels, bool)
        np.savez(os.path.join(outdir, "fig10_case.npz"), name=cname, points=cm.points,
                 fp=(cp & ~cg), fn=(~cp & cg), gold=cg, nviable=nv_by[cname],
                 error_count=int(cerrors), split="test", seed=int(seeds[0]))
        rep["figure_case"] = {"name": cname, "errors": int(cerrors), "split": "test"}
        json.dump(rep, open(os.path.join(outdir, "failure.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    except Exception as e:
        raise RuntimeError(f"fig10 artifact generation failed: {e}") from e


if __name__ == "__main__":
    main()
