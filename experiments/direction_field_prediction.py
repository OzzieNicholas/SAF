#!/usr/bin/env python3
"""方向级模型：在固定留出协议上预测每个接触点在各逼近方向上是否被挡，并评价方向推荐。

切分与点级主模型相同（Fusion 前 400 件两类件，切分种子 0，训练 240 件、测试 80 件）。程序化零件没有
三角网格，无法生成边界带精确细化的方向标签，因此不参与方向级训练。方向标签由两级判定器逐方向给出
（64 个下半球方向，细化口径；重建的占据栅格须与数据集逐比特一致）。网络结构与点级网络相同，只把
输出改为 64 个被挡 logit；5 个训练种子、80 轮。

测试集上的指标：
  逐方向 F1（被挡为正类）、逐点可达方向集 IoU、由「全部方向被挡」复原的点级 F1；
  方向推荐的 Top-1 / Top-3 命中率与 precision@3，只在至少有一个可达方向的点上统计，
  并与两条非学习基线对照：随机排序（解析期望）与按训练集各方向可达频率排序（全局方向先验）。

用法：
  python experiments/direction_field_prediction.py --seeds 5 --workers 8
"""
import argparse
import math

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths

setup_console()


def ranking_metrics(scores, viable):
    """方向推荐：(Top-1 命中率, Top-3 命中率, precision@3)，只在有可达方向的点上统计。"""
    from support_accessibility import eval as E
    return (E.topk_direction_hit_rate(scores, viable, 1), E.topk_direction_hit_rate(scores, viable, 3),
            E.topk_direction_precision(scores, viable, 3))


def random_ranking_expectation(viable):
    """随机排序的解析期望：Top-1 与 precision@3 均为可达方向占比，Top-3 为三个方向中至少一个可达的概率。"""
    import numpy as np
    D = viable.shape[1]
    n = viable.sum(axis=1)[viable.any(axis=1)].astype(int)
    top1 = float(np.mean(n / D))
    top3 = float(np.mean([1.0 - math.comb(D - k, 3) / math.comb(D, 3) for k in n]))
    return top1, top3, top1


def main():
    paths = resolve_data_paths()
    ap = argparse.ArgumentParser(description="方向级模型（固定留出协议，多训练种子）")
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--root", default=str(paths.fusion360_root), help="Fusion 原始网格目录（生成细化方向标签）")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--workers", type=int, default=8, help="并行生成方向标签的进程数")
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/direction_field_prediction/result.json")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from holdout_model import holdout_split, mean_std, refined_direction_labels, train_convonet   # 同目录脚本
    from support_accessibility import eval as E
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords
    from support_accessibility.runtime.run_records import write_result

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    train, _val, test = holdout_split(load_dataset(a.fusion)[0])
    viable = refined_direction_labels(train + test, a.fusion, a.root, a.workers)
    D = next(iter(viable.values())).shape[1]
    print(f"device={dev} D={D} train={len(train)} test={len(test)}", flush=True)

    train_viable = np.concatenate([viable[m.name] for m in train])
    test_viable = np.concatenate([viable[m.name] for m in test])
    eligible = test_viable.any(axis=1)
    prior_scores = np.broadcast_to(train_viable.mean(axis=0), test_viable.shape)

    runs = []
    for seed in range(a.seeds):
        net = train_convonet(train, a.epochs, seed, dev, net_factory=lambda: ConvONetLite(out_dim=D),
                             targets=[~viable[m.name] for m in train], log=False)
        logits = []
        with torch.no_grad():
            for m in test:
                occ = torch.as_tensor(np.asarray(m.occ, np.float32)).view(1, 1, *m.occ.shape).to(dev)
                logits.append(net(occ, to_grid_coords(m.points, m.occ.shape).to(dev)).cpu().numpy().reshape(-1, D))
        logits = np.concatenate(logits)
        blocked_pred, blocked = logits >= 0.0, ~test_viable
        ious = [1.0 if not (pv | gv).any() else (pv & gv).sum() / (pv | gv).sum()
                for pv, gv in zip(~blocked_pred, test_viable)]
        top1, top3, prec3 = ranking_metrics(-logits, test_viable)
        runs.append({"seed": seed,
                     "direction_f1": E.f1_inaccessible(blocked_pred.ravel(), blocked.ravel()),
                     "viable_set_iou": float(np.mean(ious)),
                     "recovered_point_f1": E.f1_inaccessible(blocked_pred.all(axis=1), blocked.all(axis=1)),
                     "top1_hit": top1, "top3_hit": top3, "precision_at3": prec3})
        print(" ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in runs[-1].items()), flush=True)

    random_top1, random_top3, random_prec3 = random_ranking_expectation(test_viable)
    prior_top1, prior_top3, prior_prec3 = ranking_metrics(prior_scores, test_viable)
    summary = {k: dict(zip(("mean", "std"), mean_std([r[k] for r in runs])))
               for k in runs[0] if k != "seed"}
    rep = write_result("direction_field_prediction", {
        "device": dev, "training_seeds": list(range(a.seeds)), "epochs": a.epochs, "n_directions": D,
        "protocol": "holdout_model split (first 400 both-class Fusion parts, split seed 0); "
                    "train = Fusion train split only (procedural parts have no mesh for refined labels)",
        "label_semantics": "two-stage refined direction labels; occupancy verified bit-exact",
        "n_train_models": len(train), "n_test_models": len(test), "n_test_points": int(test_viable.shape[0]),
        "eligible_fraction": round(float(eligible.mean()), 4),
        "direction_viable_rate_eligible": round(float(test_viable[eligible].mean()), 4),
        "network": summary,
        "random_baseline": {"top1_hit": round(random_top1, 4), "top3_hit": round(random_top3, 4),
                            "precision_at3": round(random_prec3, 4)},
        "global_prior_baseline": {"top1_hit": round(prior_top1, 4), "top3_hit": round(prior_top3, 4),
                                  "precision_at3": round(prior_prec3, 4)},
        "runs": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in runs],
    }, a.out, (a.fusion, a.root))
    print("DIRECTION_FIELD " + json.dumps({k: v for k, v in rep.items() if k != "runs"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
