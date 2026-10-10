#!/usr/bin/env python3
"""Train the Figure 9 directional model using the final D-020 label semantics.

The emitted checkpoint records its held-out set and one deterministic showcase
point.  Figure 9 refuses checkpoints without the D-020 refined label semantics.
"""
import argparse
import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("MKL_THREADING_LAYER", "SEQUENTIAL")
os.environ.setdefault("OMP_NUM_THREADS", "1")
from support_accessibility.runtime.data_paths import REPO_ROOT, resolve_data_paths

ROOT = str(REPO_ROOT)


def both_class(models):
    import numpy as np
    return [model for model in models if np.asarray(model.labels).size
            and np.asarray(model.labels).any() and (~np.asarray(model.labels)).any()]


def main():
    import numpy as np
    import torch
    from paper.pipeline.figure_scripts import figure_data as D
    from paper.pipeline.figure_scripts import figure_cases as X
    from support_accessibility.data.dataset import load_dataset
    from support_accessibility.data import split_by_model
    from support_accessibility.oracle import SupportAccessibilityOracle
    from support_accessibility.models.convonet import ConvONetLite, to_grid_coords

    parser = argparse.ArgumentParser()
    parser.add_argument("--max-models", type=int, default=250)
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--n-directions", type=int, default=128)
    parser.add_argument("--root", default=str(resolve_data_paths().fusion360_root))
    args = parser.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    fusion, _ = load_dataset(str(resolve_data_paths().processed_root("fusion360")))
    models = both_class(fusion)[:args.max_models]
    train_models, _valid_models, test_models = split_by_model(models, frac_train=.6, frac_val=.2, seed=0)
    target_cache = {}
    direction_set = None

    def refined_targets(model):
        nonlocal direction_set
        if model.name in target_cache:
            return target_cache[model.name]
        mesh = D.load_fusion_mesh(model.name, args.root)
        if mesh is None:
            raise FileNotFoundError(f"Missing Fusion mesh required for refined Figure 9 labels: {model.name}")
        Vn, F, occ, lo, pitch = mesh
        if occ.shape != model.occ.shape or not np.array_equal(occ, np.asarray(model.occ, bool)):
            raise RuntimeError(f"Mesh occupancy mismatch for {model.name}; refusing to fall back to occupancy labels")
        oracle = SupportAccessibilityOracle(model.occ, {"n_directions": args.n_directions},
                                            mesh=(Vn, F, lo, pitch))
        viable = np.stack([oracle.direction_labels(point, model.radius) for point in model.points])
        if direction_set is None:
            direction_set = np.asarray(oracle.dirs, np.float32)
        target_cache[model.name] = (~viable).astype(np.float32)
        return target_cache[model.name]

    print(f"device={device}; D-020 refined targets: train={len(train_models)} test={len(test_models)}", flush=True)
    training_data = []
    for position, model in enumerate(train_models, start=1):
        blocked = refined_targets(model)
        occ = torch.as_tensor(np.asarray(model.occ, np.float32)).view(1, 1, *model.occ.shape).to(device)
        coords = to_grid_coords(model.points, model.occ.shape).to(device)
        training_data.append((occ, coords, torch.as_tensor(blocked).to(device)))
        if position % 10 == 0 or position == len(train_models):
            print(f"refined training labels {position}/{len(train_models)}", flush=True)
    output_dim = int(direction_set.shape[0])
    torch.manual_seed(0)
    network = ConvONetLite(out_dim=output_dim).to(device)
    optimizer = torch.optim.Adam(network.parameters(), lr=1e-3, weight_decay=1e-4)
    loss = torch.nn.BCEWithLogitsLoss()
    for epoch in range(args.epochs):
        for index in torch.randperm(len(training_data)):
            occ, coords, blocked = training_data[int(index)]
            optimizer.zero_grad()
            loss(network(occ, coords), blocked).backward()
            optimizer.step()
        if (epoch + 1) % 30 == 0:
            print(f"epoch={epoch + 1}/{args.epochs}", flush=True)

    # Revalidate the immutable publication example instead of changing it when
    # small backend differences alter the ordering of otherwise valid cases.
    network.eval()
    fixed = next((model for model in test_models if model.name == X.DIRECTION_FIELD.name), None)
    if fixed is None:
        raise RuntimeError(f"Fixed Figure 9 example is not held out: {X.DIRECTION_FIELD.name}")
    with torch.no_grad():
        blocked = refined_targets(fixed).astype(bool)
        index = X.DIRECTION_FIELD_POINT_INDEX
        if not 0 <= index < len(fixed.points):
            raise RuntimeError(f"Fixed Figure 9 point is out of range: {index}")
        occ = torch.as_tensor(np.asarray(fixed.occ, np.float32)).view(1, 1, *fixed.occ.shape).to(device)
        coords = to_grid_coords(fixed.points[index:index + 1], fixed.occ.shape).to(device)
        probability = torch.sigmoid(network(occ, coords)).detach().cpu().numpy().ravel()
    directions = ~blocked[index]
    fraction = float(directions.mean())
    agreement = float(((probability >= .5) == blocked[index]).mean())
    top1 = bool(directions[int(np.argmin(probability))])
    if not (.30 <= fraction <= .60 and top1 and agreement >= .85):
        raise RuntimeError(
            f"Fixed Figure 9 example failed constraints: viable={fraction:.3f}, "
            f"agreement={agreement:.3f}, top1={top1}"
        )
    name = fixed.name
    outdir = os.path.join(ROOT, "artifacts", "cache", "figures"); os.makedirs(outdir, exist_ok=True)
    torch.save({"state_dict": network.state_dict(), "D": output_dim, "dirs": direction_set,
                "n_directions": args.n_directions, "test_names": [model.name for model in test_models],
                "label_semantics": "d020_refined", "showcase": {"name": name, "idx": int(index),
                "viable_fraction": fraction, "agreement": agreement, "top1_correct": top1},
                "seed": 0, "max_models": args.max_models, "epochs": args.epochs},
               os.path.join(outdir, "direction_checkpoint.pt"))
    print(f"SAVED direction_checkpoint.pt showcase={name}:{index} viable={fraction:.3f} "
          f"agreement={agreement:.3f}", flush=True)


if __name__ == "__main__":
    main()
