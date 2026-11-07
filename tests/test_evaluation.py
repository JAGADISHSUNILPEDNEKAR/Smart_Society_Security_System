"""
Unit tests for evaluation metrics, FAR/FRR definitions, and benchmark synthesis.
"""

import pytest
import numpy as np
from evaluation.metrics import compute_biometric_metrics
from evaluation.dataset import EvaluationDatasetService
from evaluation.threshold_experiments import ThresholdExperimentRunner

def test_biometric_metrics_calculation():
    """Validates mathematical computation of FAR, FRR, Precision, Recall, and Accuracy."""
    # Simulated scenario:
    # 10 genuine residents: 8 correctly ALLOWED (TP=8), 2 falsely REJECTED (FN=2)
    # 10 impostors: 9 correctly REJECTED (TN=9), 1 falsely ALLOWED (FP=1)
    y_true = [1]*10 + [0]*10
    y_pred = [1]*8 + [0]*2 + [0]*9 + [1]*1

    metrics = compute_biometric_metrics(y_true, y_pred)

    assert metrics.total_trials == 20
    assert metrics.true_positives == 8
    assert metrics.true_negatives == 9
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 2

    # Accuracy = (8 + 9) / 20 = 17 / 20 = 0.85
    assert pytest.approx(metrics.accuracy, abs=1e-4) == 0.85
    # Precision = 8 / (8 + 1) = 8 / 9 = 0.8889
    assert pytest.approx(metrics.precision, abs=1e-4) == 0.8889
    # Recall = 8 / (8 + 2) = 8 / 10 = 0.80
    assert pytest.approx(metrics.recall, abs=1e-4) == 0.80

    # FAR = FP / (FP + TN) = 1 / (1 + 9) = 1 / 10 = 0.10 (10%)
    assert pytest.approx(metrics.false_acceptance_rate, abs=1e-4) == 0.10
    # FRR = FN / (FN + TP) = 2 / (2 + 8) = 2 / 10 = 0.20 (20%)
    assert pytest.approx(metrics.false_rejection_rate, abs=1e-4) == 0.20

    # Confusion matrix: [[TN, FP], [FN, TP]]
    assert metrics.confusion_matrix == [[9, 1], [2, 8]]

def test_benchmark_separation_and_sweep():
    """Verifies strict separation between gallery and probe sets without data leakage."""
    benchmark = EvaluationDatasetService.generate_reproducible_benchmark(
        num_residents=5,
        samples_per_resident_enrollment=2,
        probes_per_resident=3,
        num_impostors=3,
        probes_per_impostor=2,
        random_seed=123
    )

    # 1. Check gallery size
    assert len(benchmark.gallery_embeddings) == 5
    for rid, samples in benchmark.gallery_embeddings.items():
        assert len(samples) == 2

    # 2. Check probe size: 5*3 genuine + 3*2 impostors = 21 probes
    assert len(benchmark.probe_samples) == 21
    genuine_probes = [p for p in benchmark.probe_samples if p.is_genuine_resident]
    impostor_probes = [p for p in benchmark.probe_samples if not p.is_genuine_resident]
    assert len(genuine_probes) == 15
    assert len(impostor_probes) == 6

    # 3. Test threshold sweep runner
    runner = ThresholdExperimentRunner(benchmark)
    sweep_df, summary = runner.sweep_thresholds(start=0.2, stop=0.6, step=0.1)
    assert not sweep_df.empty
    assert "far" in sweep_df.columns
    assert "frr" in sweep_df.columns
    assert "roc_auc" in summary
    assert summary["roc_auc"] > 0.80

