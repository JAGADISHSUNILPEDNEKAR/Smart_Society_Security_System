"""
Threshold Optimization and Error Rate Evaluation Suite.
Performs fine-grained threshold sweeps, determines Equal Error Rate (EER),
and computes trade-offs between False Acceptance and False Rejection.
"""

from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve, auc

from evaluation.dataset import BenchmarkDataset, EvaluationSample
from evaluation.metrics import compute_biometric_metrics, BiometricMetrics
from recognition.embeddings import compute_cosine_similarity

@dataclass
class ProbeTrialResult:
    """Outcome of matching a single probe against the enrolled gallery."""
    identity_id: str
    is_genuine: bool
    condition: str
    best_match_id: str
    best_similarity: float

class ThresholdExperimentRunner:
    """Executes identification trials and sweeps similarity thresholds."""

    def __init__(self, benchmark: BenchmarkDataset):
        self.benchmark = benchmark
        self._gallery_matrix: dict[str, np.ndarray] = {
            rid: np.vstack(samples) for rid, samples in benchmark.gallery_embeddings.items()
        }

    def run_all_probe_trials(self) -> list[ProbeTrialResult]:
        """Matches all probe samples against the enrolled gallery to extract max similarity scores."""
        results = []
        for probe in self.benchmark.probe_samples:
            best_id = ""
            best_sim = -1.0
            q_vec = probe.embedding

            for rid, enrolled_mat in self._gallery_matrix.items():
                sims = np.dot(enrolled_mat, q_vec)
                max_res_sim = float(np.max(sims))
                if max_res_sim > best_sim:
                    best_sim = max_res_sim
                    best_id = rid

            results.append(
                ProbeTrialResult(
                    identity_id=probe.identity_id,
                    is_genuine=probe.is_genuine_resident,
                    condition=probe.condition_tag,
                    best_match_id=best_id,
                    best_similarity=best_sim
                )
            )
        return results

    def sweep_thresholds(
        self,
        start: float = 0.10,
        stop: float = 0.85,
        step: float = 0.02
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """
        Sweeps similarity threshold across range, computing FAR, FRR, and F1.
        Returns a DataFrame and a dictionary identifying the Equal Error Rate (EER)
        and high-security operating thresholds.
        """
        trials = self.run_all_probe_trials()
        thresholds = np.arange(start, stop + 1e-5, step)

        rows = []
        for tau in thresholds:
            y_true = []
            y_pred = []
            for t in trials:
                # Ground truth: 1 if genuine resident, 0 if impostor
                yt = 1 if t.is_genuine else 0
                # System decision: 1 (ALLOWED) if score >= tau AND matched correct resident ID
                yp = 1 if (t.best_similarity >= tau and t.best_match_id == t.identity_id) else 0

                y_true.append(yt)
                y_pred.append(yp)

            metrics = compute_biometric_metrics(y_true, y_pred)
            rows.append({
                "threshold": round(float(tau), 3),
                "accuracy": metrics.accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score,
                "far": metrics.false_acceptance_rate,
                "frr": metrics.false_rejection_rate,
                "tp": metrics.true_positives,
                "tn": metrics.true_negatives,
                "fp": metrics.false_positives,
                "fn": metrics.false_negatives
            })

        df = pd.DataFrame(rows)

        # 1. Identify Equal Error Rate (EER) where |FAR - FRR| is minimal
        df["err_diff"] = (df["far"] - df["frr"]).abs()
        eer_row = df.loc[df["err_diff"].idxmin()].to_dict()
        eer_val = round(float((eer_row["far"] + eer_row["frr"]) / 2.0), 4)

        # 2. Identify High-Security Operating Point (FAR <= 0.01 / 1%)
        sec_candidates = df[df["far"] <= 0.01]
        sec_row = sec_candidates.loc[sec_candidates["frr"].idxmin()].to_dict() if not sec_candidates.empty else eer_row

        # 3. Calculate ROC AUC
        y_scores = [t.best_similarity for t in trials]
        y_labels = [1 if t.is_genuine else 0 for t in trials]
        fpr_arr, tpr_arr, _ = roc_curve(y_labels, y_scores)
        roc_auc = float(auc(fpr_arr, tpr_arr))

        summary = {
            "eer_threshold": eer_row["threshold"],
            "eer_value": eer_val,
            "recommended_security_threshold": sec_row["threshold"],
            "security_far": sec_row["far"],
            "security_frr": sec_row["frr"],
            "roc_auc": round(roc_auc, 4),
            "total_probes": len(trials),
            "genuine_probes": sum(1 for t in trials if t.is_genuine),
            "impostor_probes": sum(1 for t in trials if not t.is_genuine)
        }

        return df, summary

