"""
Report and Visualization Generator for Smart Society Security Evaluation.
Produces publication-quality figures, ROC curves, FAR/FRR curves,
confusion matrices, and performance metric tables.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg") # Non-interactive headless backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc

from config.settings import FIGURES_DIR, METRICS_DIR
from evaluation.dataset import EvaluationDatasetService
from evaluation.metrics import compute_biometric_metrics
from evaluation.threshold_experiments import ThresholdExperimentRunner

def generate_full_evaluation_report(
    figures_dir: Path = FIGURES_DIR,
    metrics_dir: Path = METRICS_DIR,
    num_residents: int = 20,
    random_seed: int = 42
) -> dict:
    """Runs complete evaluation suite, generates all charts and metric files."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating reproducible benchmark for {num_residents} enrolled residents...")
    benchmark = EvaluationDatasetService.generate_reproducible_benchmark(
        num_residents=num_residents,
        samples_per_resident_enrollment=3,
        probes_per_resident=6,
        num_impostors=15,
        probes_per_impostor=4,
        random_seed=random_seed
    )

    runner = ThresholdExperimentRunner(benchmark)
    trials = runner.run_all_probe_trials()
    sweep_df, summary = runner.sweep_thresholds()

    # Save threshold sweep table
    sweep_path = metrics_dir / "threshold_sweep.csv"
    sweep_df.to_csv(sweep_path, index=False)
    print(f"Saved threshold sweep to {sweep_path}")

    # Set aesthetics for plots
    sns.set_theme(style="whitegrid", font="sans-serif")
    palette = sns.color_palette("deep")

    # 1. FAR vs FRR Trade-off Curve
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    ax.plot(sweep_df["threshold"], sweep_df["far"] * 100, label="False Acceptance Rate (FAR %)", color="#d9534f", linewidth=2.5)
    ax.plot(sweep_df["threshold"], sweep_df["frr"] * 100, label="False Rejection Rate (FRR %)", color="#0275d8", linewidth=2.5)

    eer_th = summary["eer_threshold"]
    eer_v = summary["eer_value"] * 100
    ax.axvline(eer_th, color="#5cb85c", linestyle="--", linewidth=1.5, label=f"EER Threshold ({eer_th:.3f})")
    ax.scatter([eer_th], [eer_v], color="#5cb85c", s=70, zorder=5)

    rec_th = 0.363 # Recommended SFace default threshold
    ax.axvline(rec_th, color="#f0ad4e", linestyle=":", linewidth=1.8, label=f"Recommended Threshold ({rec_th:.3f})")

    ax.set_title("Biometric Error Rate Trade-off: FAR vs. FRR", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Cosine Similarity Threshold", fontsize=12)
    ax.set_ylabel("Error Rate (%)", fontsize=12)
    ax.set_ylim(-1, 101)
    ax.legend(loc="center right", frameon=True)
    fig.tight_layout()
    far_frr_path = figures_dir / "far_frr_curve.png"
    fig.savefig(far_frr_path)
    plt.close(fig)
    print(f"Saved FAR vs FRR plot to {far_frr_path}")

    # 2. ROC Curve
    y_scores = [t.best_similarity for t in trials]
    y_labels = [1 if t.is_genuine else 0 for t in trials]
    fpr, tpr, _ = roc_curve(y_labels, y_scores)
    roc_auc = auc(fpr, tpr)

    fig, ax = plt.subplots(figsize=(7, 6), dpi=300)
    ax.plot(fpr, tpr, color="#2c3e50", linewidth=2.5, label=f"SFace ROC (AUC = {roc_auc:.4f})")
    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1.2, label="Random Chance (AUC = 0.5000)")
    ax.set_title("Receiver Operating Characteristic (ROC) Curve", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=12)
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=12)
    ax.set_xlim([-0.01, 1.01])
    ax.set_ylim([-0.01, 1.01])
    ax.legend(loc="lower right", frameon=True)
    fig.tight_layout()
    roc_path = figures_dir / "roc_curve.png"
    fig.savefig(roc_path)
    plt.close(fig)
    print(f"Saved ROC plot to {roc_path}")

    # 3. Confusion Matrix at Recommended Operating Threshold (0.363)
    y_pred_rec = [
        1 if (t.best_similarity >= rec_th and t.best_match_id == t.identity_id) else 0
        for t in trials
    ]
    rec_metrics = compute_biometric_metrics(y_labels, y_pred_rec)

    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    cm = np.array(rec_metrics.confusion_matrix)
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        ax=ax,
        xticklabels=["Denied (Unknown)", "Granted (Allowed)"],
        yticklabels=["Actual Impostor", "Actual Resident"],
        annot_kws={"size": 16, "fontweight": "bold"}
    )
    ax.set_title(f"Confusion Matrix (Threshold = {rec_th})", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Predicted Access Decision", fontsize=12)
    ax.set_ylabel("Ground Truth Identity", fontsize=12)
    fig.tight_layout()
    cm_path = figures_dir / "confusion_matrix.png"
    fig.savefig(cm_path)
    plt.close(fig)
    print(f"Saved Confusion Matrix plot to {cm_path}")

    # 4. Score Distribution Histogram (Genuine vs Impostor)
    genuine_scores = [t.best_similarity for t in trials if t.is_genuine]
    impostor_scores = [t.best_similarity for t in trials if not t.is_genuine]

    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.hist(impostor_scores, bins=25, alpha=0.65, color="#d9534f", label="Impostor (Unknown) Scores", density=True)
    ax.hist(genuine_scores, bins=25, alpha=0.65, color="#0275d8", label="Genuine Resident Scores", density=True)
    ax.axvline(rec_th, color="#2c3e50", linestyle="--", linewidth=2.0, label=f"Decision Boundary ({rec_th})")
    ax.set_title("Cosine Similarity Score Distributions", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Cosine Similarity Score", fontsize=12)
    ax.set_ylabel("Probability Density", fontsize=12)
    ax.legend(loc="upper right", frameon=True)
    fig.tight_layout()
    dist_path = figures_dir / "score_distribution.png"
    fig.savefig(dist_path)
    plt.close(fig)
    print(f"Saved Score Distribution plot to {dist_path}")

    # 5. Condition Breakdown Analysis
    condition_stats = []
    for cond in sorted(set(t.condition for t in trials if t.is_genuine)):
        cond_trials = [t for t in trials if t.condition == cond]
        c_true = [1] * len(cond_trials)
        c_pred = [1 if (t.best_similarity >= rec_th and t.best_match_id == t.identity_id) else 0 for t in cond_trials]
        c_metrics = compute_biometric_metrics(c_true, c_pred)
        condition_stats.append({
            "condition": cond,
            "trials": len(cond_trials),
            "correct_allowed": c_metrics.true_positives,
            "false_rejected": c_metrics.false_negatives,
            "recall_tar": round(c_metrics.recall * 100, 2),
            "mean_similarity": round(float(np.mean([t.best_similarity for t in cond_trials])), 4)
        })

    cond_df = pd.DataFrame(condition_stats)
    cond_path = metrics_dir / "condition_breakdown.csv"
    cond_df.to_csv(cond_path, index=False)
    print(f"Saved condition breakdown to {cond_path}")

    # Summary payload
    summary.update({
        "recommended_threshold": rec_th,
        "operating_accuracy": rec_metrics.accuracy,
        "operating_precision": rec_metrics.precision,
        "operating_recall": rec_metrics.recall,
        "operating_f1": rec_metrics.f1_score,
        "operating_far": rec_metrics.false_acceptance_rate,
        "operating_frr": rec_metrics.false_rejection_rate,
        "confusion_matrix": rec_metrics.confusion_matrix,
        "conditions_evaluated": condition_stats
    })

    summary_path = metrics_dir / "summary_metrics.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved evaluation summary to {summary_path}")

    return summary

if __name__ == "__main__":
    generate_full_evaluation_report()

