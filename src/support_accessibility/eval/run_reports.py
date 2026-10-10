"""实验运行记录的序列化：方向级场的逐种子证据与汇总报告。"""


def build_seed_run_record(
    *,
    seed,
    n_train_models,
    n_test_models,
    n_train_points,
    n_test_points,
    n_directions,
    test_refined_models,
    test_occupancy_fallback_models,
    split_rule,
    metrics,
):
    """Serialize the denominator-aware evidence for one direction-field holdout seed."""
    required_metrics = (
        "dir_f1",
        "dir_set_iou",
        "recovered_binary_f1",
        "majority_dir_baseline_f1",
        "topk_hit_top1",
        "topk_hit_top3",
        "topk_precision_at3",
    )
    return {
        "seed": int(seed),
        "split_rule": str(split_rule),
        "n_train_models": int(n_train_models),
        "n_test_models": int(n_test_models),
        "n_train_points": int(n_train_points),
        "n_test_points": int(n_test_points),
        "n_directions": int(n_directions),
        "n_train_direction_labels": int(n_train_points) * int(n_directions),
        "n_test_direction_labels": int(n_test_points) * int(n_directions),
        "test_refined_models": int(test_refined_models),
        "test_occupancy_fallback_models": int(test_occupancy_fallback_models),
        **{name: float(metrics[name]) for name in required_metrics},
    }


def build_direction_field_report(
    *,
    data,
    seeds,
    epochs,
    device,
    n_directions,
    n_models,
    target_mode,
    refined_models,
    occupancy_fallback,
    rows,
):
    """Build a direction-field envelope without discarding the seed-level evidence."""
    import numpy as np

    rows = list(rows)
    if not rows:
        raise ValueError("at least one seed run is required")
    arr = np.asarray([
        [
            row["dir_f1"],
            row["dir_set_iou"],
            row["recovered_binary_f1"],
            row["majority_dir_baseline_f1"],
            row["topk_hit_top1"],
            row["topk_hit_top3"],
            row["topk_precision_at3"],
        ]
        for row in rows
    ], dtype=float)
    return {
        "data": data,
        "seeds": int(seeds),
        "epochs": int(epochs),
        "device": device,
        "D_dirs": int(n_directions),
        "models": int(n_models),
        "target_mode": target_mode,
        "refined_models": int(refined_models),
        "occupancy_fallback": int(occupancy_fallback),
        "dir_f1_mean": round(float(arr[:, 0].mean()), 3),
        "dir_f1_std": round(float(arr[:, 0].std()), 3),
        "dir_setiou_mean": round(float(arr[:, 1].mean()), 3),
        "recovered_binary_f1_mean": round(float(arr[:, 2].mean()), 3),
        "majority_dir_baseline_f1": round(float(arr[:, 3].mean()), 3),
        "topk_hit_top1_mean": round(float(arr[:, 4].mean()), 3),
        "topk_hit_top3_mean": round(float(arr[:, 5].mean()), 3),
        "topk_precision_at3_mean": round(float(arr[:, 6].mean()), 3),
        "runs": rows,
    }
