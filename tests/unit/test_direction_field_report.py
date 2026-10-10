"""Schema-level checks for the 方向级场 per-seed evidence envelope."""


def test_direction_field_run_record_preserves_denominators_metrics_and_label_provenance():
    from support_accessibility.eval.run_reports import build_seed_run_record

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


def test_direction_field_report_retains_the_per_seed_runs_alongside_headline_metrics():
    from support_accessibility.eval.run_reports import build_direction_field_report

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

    report = build_direction_field_report(
        data="${SAF_DATA_ROOT}/processed/fusion360",
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
