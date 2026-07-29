#!/usr/bin/env python3
"""E8 复现器：神经推理 vs oracle 打标的**每点耗时比**（H4 应用价值的效率半）。
对一组真实件，计时 oracle.label(逐点体素判定) 与 ConvONet-lite 前向(整件一次、均摊到点)，报比值。
推理成本与权重无关，故用未训练网络计时（架构决定成本）。冻结口径 n_dir=128。self-add src。

用法：conda run -n saf python tools/eval_e8.py
"""
import argparse
import os
import sys
import time

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


def main():
    ap = argparse.ArgumentParser(description="E8 神经推理 vs oracle 打标 每点耗时比")
    ap.add_argument("--data", default="data/processed/fusion360_full")
    ap.add_argument("--n-directions", type=int, default=128)
    ap.add_argument("--models", type=int, default=30)
    a = ap.parse_args()

    import json
    import numpy as np
    import torch
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.oracle import SupportAccessibilityOracle
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    ms, _ = load_dataset(a.data)
    sample = [m for m in ms if m.points.shape[0] > 0][:a.models]
    net = ConvONetLite().to(dev).eval()

    # warm up neural (CUDA 首次前向含编译开销)
    with torch.no_grad():
        m0 = sample[0]
        occ0 = torch.as_tensor(np.asarray(m0.occ, np.float32)).view(1, 1, *m0.occ.shape).to(dev)
        net(occ0, to_grid_coords(m0.points, m0.occ.shape).to(dev))
        if dev == 'cuda':
            torch.cuda.synchronize()

    t_oracle = t_neural = n_pts = 0.0
    with torch.no_grad():
        for m in sample:
            r = float(m.radius); n = m.points.shape[0]
            o = SupportAccessibilityOracle(m.occ, {"n_directions": a.n_directions})
            t0 = time.perf_counter()
            for p in m.points:
                o.label(p, r)
            t_oracle += time.perf_counter() - t0
            occ = torch.as_tensor(np.asarray(m.occ, np.float32)).view(1, 1, *m.occ.shape).to(dev)
            gc = to_grid_coords(m.points, m.occ.shape).to(dev)
            t1 = time.perf_counter()
            net(occ, gc)
            if dev == 'cuda':
                torch.cuda.synchronize()
            t_neural += time.perf_counter() - t1
            n_pts += n
    per_oracle = t_oracle / n_pts * 1e3
    per_neural = t_neural / n_pts * 1e3
    print("E8_RESULT " + json.dumps({
        "device": dev, "n_directions": a.n_directions, "models": len(sample), "points": int(n_pts),
        "oracle_ms_per_point": round(per_oracle, 5), "neural_ms_per_point": round(per_neural, 5),
        "speedup_neural_over_oracle": round(per_oracle / per_neural, 1),
        "note": "神经整件一次前向均摊到点；含 GPU。推理成本与权重无关，用未训练网络计时。oracle 仅计逐点 label、未含 EDT 预算（构造在计时外）→ speedup 为保守下界。",
    }))


if __name__ == "__main__":
    main()
