"""Evaluation and benchmarking package."""
from evaluation.dataset import EvaluationDatasetService, BenchmarkDataset, EvaluationSample
from evaluation.metrics import compute_biometric_metrics, BiometricMetrics
from evaluation.threshold_experiments import ThresholdExperimentRunner, ProbeTrialResult
from evaluation.generate_report import generate_full_evaluation_report

__all__ = [
    "EvaluationDatasetService",
    "BenchmarkDataset",
    "EvaluationSample",
    "compute_biometric_metrics",
    "BiometricMetrics",
    "ThresholdExperimentRunner",
    "ProbeTrialResult",
    "generate_full_evaluation_report"
]

