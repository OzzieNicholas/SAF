"""Statistics serialization used by the submission manuscript."""


def test_score_distribution_reports_quantiles_iqr_and_zero_fraction():
    from deliverables.paper.pipeline.qa.review_metrics import summarize_score_distribution

    result = summarize_score_distribution([0.0, 0.5, 1.0])

    assert result == {
        "count": 3,
        "mean": 0.5,
        "std": 0.408248290463863,
        "median": 0.5,
        "q1": 0.25,
        "q3": 0.75,
        "iqr": 0.5,
        "zero_fraction": 1 / 3,
    }


def test_empty_score_distribution_exposes_missing_quantiles_instead_of_zero_scores():
    from deliverables.paper.pipeline.qa.review_metrics import summarize_score_distribution

    result = summarize_score_distribution([])

    assert result == {
        "count": 0,
        "mean": None,
        "std": None,
        "median": None,
        "q1": None,
        "q3": None,
        "iqr": None,
        "zero_fraction": None,
    }
