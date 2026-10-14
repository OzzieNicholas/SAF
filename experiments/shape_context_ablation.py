#!/usr/bin/env python3
"""消融：形状上下文的价值。四个变体在同一固定留出集上的不可达 F1（多训练种子均值 ± 标准差）：
  no_shape  —— 仅归一坐标、无占据特征（形状盲）
  local     —— 单层 3×3×3 卷积（感受野 3）
  lite      —— 三层 3×3×3 卷积（感受野 7，= 主网络 ConvONet-lite；直接读 holdout_model 的权重）
  pooled    —— 卷积 + 两次 MaxPool（感受野更大但特征更粗）
训练制度、切分、轮数与种子均与 experiments/holdout_model.py 相同，因此 lite 行与基线表中的形状条件网络是同一组模型。

用法：python experiments/shape_context_ablation.py
"""
import argparse

from support_accessibility.runtime.console import setup_console
from support_accessibility.runtime.data_paths import resolve_data_paths

setup_console()

VARIANTS = ("no_shape", "local", "lite", "pooled")


def make_variant(variant, feat=32, hidden=64):
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    class AblationNet(nn.Module):
        def __init__(self):
            super().__init__()
            if variant == "no_shape":
                self.enc, din = None, 3
            elif variant == "local":
                self.enc, din = nn.Sequential(nn.Conv3d(1, feat, 3, padding=1), nn.ReLU(inplace=True)), feat + 3
            elif variant == "pooled":
                self.enc = nn.Sequential(nn.Conv3d(1, 16, 3, padding=1), nn.ReLU(inplace=True), nn.MaxPool3d(2),
                                         nn.Conv3d(16, feat, 3, padding=1), nn.ReLU(inplace=True), nn.MaxPool3d(2),
                                         nn.Conv3d(feat, feat, 3, padding=1), nn.ReLU(inplace=True))
                din = feat + 3
            else:
                raise ValueError(variant)
            self.dec = nn.Sequential(nn.Linear(din, hidden), nn.ReLU(inplace=True),
                                     nn.Linear(hidden, hidden), nn.ReLU(inplace=True), nn.Linear(hidden, 1))

        def forward(self, occ, gc):
            if self.enc is None:
                return self.dec(gc).view(-1)
            fv = self.enc(occ)
            s = F.grid_sample(fv, gc.view(1, -1, 1, 1, 3), align_corners=True, padding_mode="border")
            return self.dec(torch.cat([s.view(fv.shape[1], -1).t(), gc], 1)).view(-1)

    return AblationNet


def main():
    ap = argparse.ArgumentParser(description="消融：形状上下文价值（四变体，多训练种子）")
    paths = resolve_data_paths()
    ap.add_argument("--fusion", default=str(paths.processed_root("fusion360")))
    ap.add_argument("--procedural", default=str(paths.processed_root("procedural")))
    ap.add_argument("--out", default=None, help="结果路径；默认 artifacts/runs/shape_context_ablation/result.json（试跑请指定其他路径，避免覆盖证据）")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from holdout_model import holdout_split, load_holdout_models, predict_proba, train_convonet   # 同目录脚本
    from support_accessibility.runtime.run_records import write_result
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility import eval as E

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    fus, _ = load_dataset(a.fusion)
    proc, _ = load_dataset(a.procedural)
    ftr, _fva, fte = holdout_split(fus)
    nets = load_holdout_models(dev)
    seeds = [s for s, _n, _c in nets]
    epochs = int(nets[0][2]["epochs"])
    G = np.concatenate([np.asarray(m.labels, bool) for m in fte])

    def pooled_f1(net):
        P = np.concatenate([predict_proba(net, m, dev) >= 0.5 for m in fte])
        return float(E.f1_inaccessible(P, G))

    by_seed = {"lite": [pooled_f1(net) for _s, net, _c in nets]}
    for variant in ("no_shape", "local", "pooled"):
        by_seed[variant] = []
        for seed in seeds:
            net = train_convonet(ftr + proc, epochs, seed, dev, net_factory=make_variant(variant), log=False)
            by_seed[variant].append(pooled_f1(net))
            print(f"variant={variant} seed={seed} f1={by_seed[variant][-1]:.4f}", flush=True)

    report = {"device": dev, "epochs": epochs, "training_seeds": seeds,
              "train_models": len(ftr), "test_models": len(fte), "order": list(VARIANTS),
              "lite_source": "holdout_model weights",
              "f1": {v: round(float(np.mean(by_seed[v])), 4) for v in VARIANTS},
              "f1_std": {v: round(float(np.std(by_seed[v])), 4) for v in VARIANTS},
              "f1_by_seed": {v: [round(x, 4) for x in by_seed[v]] for v in VARIANTS}}
    report = write_result("shape_context_ablation", report, a.out, (a.fusion, a.procedural))
    print("ABLATION_RESULT " + json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
