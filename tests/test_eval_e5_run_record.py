"""Schema-level checks for the E5 per-seed evidence envelope."""


def test_e5_run_record_preserves_denominators_metrics_and_label_provenance():
    from tools.eval_e5 import build_seed_run_record

    result = build_seed_run_record(
        seed=7,
        n_train_models=9,
        n_test_models=4,
        n_train_points=90,
        n_test_points=40,
        n_directions=64,
        test_refined_models=3,
        test_occupancy_fallback_models=1,
        split_rule="model-level random 70/30 holdout; seed=7",
        metrics={
            "dir_f1": 0.81,
            "dir_set_iou": 0.72,
            "recovered_binary_f1": 0.68,
            "majority_dir_baseline_f1": 0.41,
            "topk_hit_top1": 0.79,
            "topk_hit_top3": 0.92,
            "topk_precision_at3": 0.73,
        },
    )

    assert result == {
        "seed": 7,
        "split_rule": "model-level random 70/30 holdout; seed=7",
        "n_train_models": 9,
        "n_test_models": 4,
        "n_train_points": 90,
        "n_test_points": 40,
        "n_directions": 64,
        "n_train_direction_labels": 5760,
        "n_test_direction_labels": 2560,
        "test_refined_models": 3,
        "test_occupancy_fallback_models": 1,
        "dir_f1": 0.81,
        "dir_set_iou": 0.72,
        "recovered_binary_f1": 0.68,
        "majority_dir_baseline_f1": 0.41,
        "topk_hit_top1": 0.79,
        "topk_hit_top3": 0.92,
        "topk_precision_at3": 0.73,
    }


def test_e5_report_retains_the_per_seed_runs_alongside_headline_metrics():
    from tools.eval_e5 import build_e5_report

    seed_run = {
        "seed": 0,
        "n_train_models": 9,
        "n_test_models": 4,
        "n_train_points": 90,
        "n_test_points": 40,
        "n_directions": 64,
        "n_train_direction_labels": 5760,
        "n_test_direction_labels": 2560,
        "test_refined_models": 4,
        "test_occupancy_fallback_models": 0,
        "split_rule": "model-level random 70/30 holdout; seed=0",
        "dir_f1": 0.81,
        "dir_set_iou": 0.72,
        "recovered_binary_f1": 0.68,
        "majority_dir_baseline_f1": 0.41,
        "topk_hit_top1": 0.79,
        "topk_hit_top3": 0.92,
        "topk_precision_at3": 0.73,
    }

    report = build_e5_report(
        data="data/processed/fusion360_full",
        seeds=1,
        epochs=1,
        device="cuda",
        n_directions=64,
        n_models=13,
        target_mode="refined(D-020)",
        refined_models=13,
        occupancy_fallback=0,
        rows=[seed_run],
    )

    assert report["dir_f1_mean"] == 0.81
    assert report["dir_f1_std"] == 0.0
    assert report["runs"] == [seed_run]
