#!/usr/bin/env python3
"""消融复现器：形状上下文的价值（H3 主线的对照）。四变体跨模型预测不可达 F1：
  no_shape  —— 仅归一坐标、无 occ 特征（形状盲）
  local     —— 单层 3×3 卷积（小感受野 RF≈3，只见局部）
  lite      —— 三层 3×3（RF≈7，= ConvONetLite 主线）
  pooled    —— 卷积 + 两次 MaxPool（大感受野但粗、丢局部精度）；**设 occ 各维 ≥4**（两次池化后不塌为 0；
              both-class 件实测 min 维=4，成立；极薄件由 both_class 过滤天然排除）
镜像 H3 训练制度（split 0.6/0.2/0.2）。self-add src；需 torch。

用法：conda run -n saf python tools/eval_ablation.py --max-models 400 --epochs 60
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
    ap = argparse.ArgumentParser(description="消融：形状上下文价值（四变体 F1）")
    ap.add_argument("--fusion", default="data/processed/fusion360_full")
    ap.add_argument("--procedural", default="data/processed/procedural_v1")
    ap.add_argument("--max-models", type=int, default=400)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="runs/ablation/latest.json")
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data import split_by_model
    from support_accessibility.models.convonet import to_grid_coords
    from support_accessibility import eval as E

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'

    class AblationNet(nn.Module):
        def __init__(self, variant, feat=32, hidden=64):
            super().__init__()
            self.variant = variant
            if variant == 'no_shape':
                self.enc, din = None, 3
            elif variant == 'local':
                self.enc, din = nn.Sequential(nn.Conv3d(1, feat, 3, padding=1), nn.ReLU(inplace=True)), feat + 3
            elif variant == 'lite':
                self.enc = nn.Sequential(nn.Conv3d(1, 16, 3, padding=1), nn.ReLU(inplace=True),
                                         nn.Conv3d(16, feat, 3, padding=1), nn.ReLU(inplace=True),
                                         nn.Conv3d(feat, feat, 3, padding=1), nn.ReLU(inplace=True)); din = feat + 3
            elif variant == 'pooled':
                self.enc = nn.Sequential(nn.Conv3d(1, 16, 3, padding=1), nn.ReLU(inplace=True), nn.MaxPool3d(2),
                                         nn.Conv3d(16, feat, 3, padding=1), nn.ReLU(inplace=True), nn.MaxPool3d(2),
                                         nn.Conv3d(feat, feat, 3, padding=1), nn.ReLU(inplace=True)); din = feat + 3
            else:
                raise ValueError(variant)
            self.dec = nn.Sequential(nn.Linear(din, hidden), nn.ReLU(inplace=True),
                                     nn.Linear(hidden, hidden), nn.ReLU(inplace=True), nn.Linear(hidden, 1))

        def forward(self, occ, gc):
            if self.enc is None:
                return self.dec(gc).view(-1)
            fv = self.enc(occ)
            s = F.grid_sample(fv, gc.view(1, -1, 1, 1, 3), align_corners=True, padding_mode='border')
            s = s.view(fv.shape[1], -1).t()
            return self.dec(torch.cat([s, gc], 1)).view(-1)

    fus, _ = load_dataset(a.fusion)
    proc, _ = load_dataset(a.procedural)
    fus_bc = both_class(fus)[:a.max_models]
    ftr, _fva, fte = split_by_model(fus_bc, frac_train=0.6, frac_val=0.2, seed=a.seed)
    fte = [m for m in fte if m.points.shape[0] > 0]

    def prep(m):
        occ = torch.as_tensor(np.asarray(m.occ, np.float32)).view(1, 1, *m.occ.shape).to(dev)
        return occ, to_grid_coords(m.points, m.occ.shape).to(dev), torch.as_tensor(np.asarray(m.labels, np.float32)).to(dev)

    train = [prep(m) for m in (ftr + proc)]
    test = [(prep(m), np.asarray(m.labels, bool)) for m in fte]
    lossf = torch.nn.BCEWithLogitsLoss()
    res = {}
    for variant in ('no_shape', 'local', 'lite', 'pooled'):
        torch.manual_seed(a.seed)
        net = AblationNet(variant).to(dev)
        opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
        for _ in range(a.epochs):
            for i in torch.randperm(len(train)):
                occ, gc, y = train[i]
                opt.zero_grad(); lossf(net(occ, gc), y).backward(); opt.step()
        net.eval()
        pr, go = [], []
        with torch.no_grad():
            for (occ, gc, _y), gold in test:
                pr.append((torch.sigmoid(net(occ, gc)) >= 0.5).cpu().numpy()); go.append(gold)
        res[variant] = round(E.f1_inaccessible(np.concatenate(pr), np.concatenate(go)), 3)
        print(f"variant={variant} f1={res[variant]}", flush=True)

    report = {"schema_version": 1, "device": dev, "epochs": a.epochs,
              "max_models": a.max_models, "seed": a.seed,
              "train_models": len(ftr), "test_models": len(fte),
              "f1": res,
              "order": ["no_shape", "local", "lite", "pooled"]}
    output = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=1)
    print("ABLATION_RESULT " + json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
