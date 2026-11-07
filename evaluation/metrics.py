"""
Biometric Evaluation Metrics Module.
Calculates Accuracy, Precision, Recall, F1, False Acceptance Rate (FAR),
False Rejection Rate (FRR), and Confusion Matrices.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class BiometricMetrics:
    """Standard access control biometric evaluation metrics."""
    total_trials: int
    genuine_trials: int
    impostor_trials: int
    true_positives: int    # TP: Resident recognized and ALLOWED
    true_negatives: int    # TN: Impostor recognized as unknown and REJECTED
    false_positives: int   # FP: Impostor falsely ALLOWED (Security breach)
    false_negatives: int   # FN: Genuine resident falsely REJECTED (False alarm)
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_acceptance_rate: float  # FAR = FP / (FP + TN)
    false_rejection_rate: float   # FRR = FN / (FN + TP)
    true_acceptance_rate: float   # TAR = 1 - FRR
    true_rejection_rate: float    # TRR = 1 - FAR
    confusion_matrix: list[list[int]] # [[TN, FP], [FN, TP]]

def compute_biometric_metrics(
    y_true: list[int] | np.ndarray,      # 1 = Genuine Resident, 0 = Impostor / Unknown
    y_pred: list[int] | np.ndarray       # 1 = ALLOWED, 0 = REJECTED
) -> BiometricMetrics:
    """
    Computes comprehensive biometric access evaluation metrics from binary trial outcomes.
    """
    yt = np.asarray(y_true, dtype=int)
    yp = np.asarray(y_pred, dtype=int)

    if len(yt) != len(yp):
        raise ValueError(f"Length mismatch: y_true ({len(yt)}) vs y_pred ({len(yp)})")

    tp = int(np.sum((yt == 1) & (yp == 1)))
    tn = int(np.sum((yt == 0) & (yp == 0)))
    fp = int(np.sum((yt == 0) & (yp == 1)))
    fn = int(np.sum((yt == 1) & (yp == 0)))

    total = len(yt)
    genuine_trials = tp + fn
    impostor_trials = tn + fp

    accuracy = float((tp + tn) / total) if total > 0 else 0.0
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    # FAR: Impostors falsely accepted
    far = float(fp / impostor_trials) if impostor_trials > 0 else 0.0
    # FRR: Genuine residents falsely rejected
    frr = float(fn / genuine_trials) if genuine_trials > 0 else 0.0

    tar = 1.0 - frr
    trr = 1.0 - far

    # Confusion matrix structure:
    # Row 0: Actual Impostor [Predicted Impostor (TN), Predicted Resident (FP)]
    # Row 1: Actual Resident [Predicted Impostor (FN), Predicted Resident (TP)]
    cm = [
        [tn, fp],
        [fn, tp]
    ]

    return BiometricMetrics(
        total_trials=total,
        genuine_trials=genuine_trials,
        impostor_trials=impostor_trials,
        true_positives=tp,
        true_negatives=tn,
        false_positives=fp,
        false_negatives=fn,
        accuracy=round(accuracy, 4),
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1_score=round(f1, 4),
        false_acceptance_rate=round(far, 4),
        false_rejection_rate=round(frr, 4),
        true_acceptance_rate=round(tar, 4),
        true_rejection_rate=round(trr, 4),
        confusion_matrix=cm
    )

