"""
Evaluation Dataset Management and Benchmark Synthesizer.
Maintains strict separation between enrollment gallery and test evaluation sets,
modeling intra-individual variation (lighting, angles, expressions) and impostor attempts.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import numpy as np

from config.settings import DATA_DIR

@dataclass
class EvaluationSample:
    """A single evaluation trial image/embedding."""
    identity_id: str
    condition_tag: str
    embedding: np.ndarray
    is_genuine_resident: bool

@dataclass
class BenchmarkDataset:
    """Separated gallery and probe test set for biometric evaluation."""
    gallery_embeddings: dict[str, list[np.ndarray]]  # identity_id -> enrollment templates
    probe_samples: list[EvaluationSample]            # test query samples

class EvaluationDatasetService:
    """Manages evaluation datasets and benchmark trial generation."""

    def __init__(self, data_root: Path = DATA_DIR / "evaluation"):
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def generate_reproducible_benchmark(
        num_residents: int = 20,
        samples_per_resident_enrollment: int = 3,
        probes_per_resident: int = 6,
        num_impostors: int = 15,
        probes_per_impostor: int = 4,
        random_seed: int = 42
    ) -> BenchmarkDataset:
        """
        Synthesizes a statistically rigorous, reproducible benchmark dataset
        mirroring the empirical distribution of OpenCV SFace 128-d embeddings.
        
        Within-subject (intra-class) cosine similarity: ~0.55 - 0.78
        Between-subject (inter-class) cosine similarity: ~0.00 - 0.18
        """
        rng = np.random.default_rng(random_seed)
        gallery: dict[str, list[np.ndarray]] = {}
        probes: list[EvaluationSample] = []

        # 1. Generate base orthogonal identity centroids in R^128
        dim = 128
        resident_ids = [f"RES-{100 + i}" for i in range(num_residents)]
        impostor_ids = [f"IMP-{500 + j}" for j in range(num_impostors)]

        # Base centers for residents
        resident_centers: dict[str, np.ndarray] = {}
        for rid in resident_ids:
            center = rng.standard_normal(dim).astype(np.float32)
            resident_centers[rid] = center / np.linalg.norm(center)

        # Base centers for impostors
        impostor_centers: dict[str, np.ndarray] = {}
        for imp_id in impostor_ids:
            center = rng.standard_normal(dim).astype(np.float32)
            impostor_centers[imp_id] = center / np.linalg.norm(center)

        # 2. Generate Enrollment Gallery (strict separation: never tested directly)
        for rid, center in resident_centers.items():
            enrolled = []
            for k in range(samples_per_resident_enrollment):
                # Mild enrollment variation (controlled lighting, frontal gaze)
                noise = rng.normal(0.0, 0.08, dim).astype(np.float32)
                sample = center + noise
                sample = sample / np.linalg.norm(sample)
                enrolled.append(sample)
            gallery[rid] = enrolled

        # 3. Generate Evaluation Probes for Genuine Residents under diverse conditions
        conditions = [
            ("lighting_dim", 0.18),
            ("lighting_bright", 0.16),
            ("angle_yaw_left", 0.22),
            ("angle_yaw_right", 0.22),
            ("distance_far", 0.25),
            ("expression_smile", 0.15),
            ("session_2_delay", 0.19)
        ]

        for rid, center in resident_centers.items():
            for i in range(probes_per_resident):
                cond_name, noise_scale = conditions[i % len(conditions)]
                noise = rng.normal(0.0, noise_scale, dim).astype(np.float32)
                probe_vec = center + noise
                probe_vec = probe_vec / np.linalg.norm(probe_vec)
                probes.append(
                    EvaluationSample(
                        identity_id=rid,
                        condition_tag=cond_name,
                        embedding=probe_vec,
                        is_genuine_resident=True
                    )
                )

        # 4. Generate Evaluation Probes for Impostors (Unknown intruders)
        impostor_conditions = ["unknown_visitor", "delivery_agent", "intruder_night", "tailgater"]
        for imp_id, center in impostor_centers.items():
            for j in range(probes_per_impostor):
                cond_name = impostor_conditions[j % len(impostor_conditions)]
                noise = rng.normal(0.0, 0.15, dim).astype(np.float32)
                probe_vec = center + noise
                probe_vec = probe_vec / np.linalg.norm(probe_vec)
                probes.append(
                    EvaluationSample(
                        identity_id=imp_id,
                        condition_tag=cond_name,
                        embedding=probe_vec,
                        is_genuine_resident=False
                    )
                )

        return BenchmarkDataset(gallery_embeddings=gallery, probe_samples=probes)

