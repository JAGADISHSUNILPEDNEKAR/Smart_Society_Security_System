"""
Biometric Vector Matcher Module.
Performs fast matrix-accelerated cosine similarity search against enrolled resident templates.
"""

from dataclasses import dataclass
from typing import Optional
import logging
import numpy as np

from database.db import DatabaseManager
from recognition.embeddings import deserialize_embedding
from recognition.threshold import ThresholdPolicy
from config.settings import DecisionState, CONFIG

logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """Detailed result of biometric matching."""
    resident_id: Optional[str]
    full_name: str
    apartment_number: Optional[str]
    similarity_score: float
    decision: DecisionState
    reason: str
    is_active: bool
    is_genuine_resident: bool

class FaceMatcher:
    """Manages cached resident biometric templates and performs vectorized matching."""

    def __init__(self, db: DatabaseManager, policy: Optional[ThresholdPolicy] = None):
        self.db = db
        self.policy = policy or ThresholdPolicy(
            threshold_high=float(self.db.get_setting("recognition_threshold_high", "0.363")),
            threshold_low=float(self.db.get_setting("recognition_threshold_low", "0.280"))
        )
        # Template cache:
        # self._template_matrix: np.ndarray shape (N, 128)
        # self._metadata: list[dict] where each index maps to resident_id, name, apartment, is_active
        self._template_matrix: Optional[np.ndarray] = None
        self._metadata: list[dict] = []
        self.reload_templates()

    def update_policy(self, threshold_high: float, threshold_low: float) -> None:
        """Dynamically updates active recognition thresholds."""
        self.policy = ThresholdPolicy(threshold_high=threshold_high, threshold_low=threshold_low)
        self.db.set_setting("recognition_threshold_high", f"{threshold_high:.3f}")
        self.db.set_setting("recognition_threshold_low", f"{threshold_low:.3f}")
        logger.info(f"Thresholds updated: High={threshold_high:.3f}, Low={threshold_low:.3f}")

    def reload_templates(self) -> int:
        """
        Reloads all enrolled resident embeddings from database into an in-memory matrix.
        Returns total number of loaded templates.
        """
        query = """
            SELECT 
                r.resident_id,
                r.full_name,
                r.apartment_number,
                r.is_active,
                e.embedding_blob
            FROM face_embeddings e
            JOIN residents r ON e.resident_id = r.resident_id
        """
        rows = self.db.fetch_all(query)
        if not rows:
            self._template_matrix = None
            self._metadata = []
            logger.info("No enrolled templates in database.")
            return 0

        vectors = []
        meta = []
        for row in rows:
            try:
                vec = deserialize_embedding(row["embedding_blob"])
                vectors.append(vec)
                meta.append({
                    "resident_id": row["resident_id"],
                    "full_name": row["full_name"],
                    "apartment_number": row["apartment_number"],
                    "is_active": bool(row["is_active"])
                })
            except Exception as e:
                logger.error(f"Error deserializing template for resident {row['resident_id']}: {e}")

        if vectors:
            self._template_matrix = np.vstack(vectors) # Shape: (N, 128)
            self._metadata = meta
            logger.info(f"Loaded {len(vectors)} biometric templates for {len(set(m['resident_id'] for m in meta))} residents.")
        else:
            self._template_matrix = None
            self._metadata = []

        return len(self._metadata)

    def match(self, query_embedding: np.ndarray) -> MatchResult:
        """
        Matches a 128-d query face embedding against all enrolled resident templates.
        Returns the best candidate MatchResult.
        """
        if self._template_matrix is None or len(self._metadata) == 0:
            return MatchResult(
                resident_id=None,
                full_name="UNKNOWN PERSON",
                apartment_number=None,
                similarity_score=0.0,
                decision=DecisionState.REJECTED,
                reason="No resident biometric templates enrolled in system",
                is_active=False,
                is_genuine_resident=False
            )

        query = np.asarray(query_embedding, dtype=np.float32).flatten()
        norm = np.linalg.norm(query)
        if norm > 1e-6:
            query = query / norm

        # Compute cosine similarities in parallel via matrix-vector multiplication
        # Since templates and query are unit normalized: dot product == cosine similarity
        similarities = np.dot(self._template_matrix, query) # Shape: (N,)

        # Aggregate max similarity per distinct resident
        resident_scores: dict[str, dict] = {}
        for idx, sim in enumerate(similarities):
            m = self._metadata[idx]
            rid = m["resident_id"]
            sim_val = float(sim)
            if rid not in resident_scores or sim_val > resident_scores[rid]["similarity"]:
                resident_scores[rid] = {
                    "resident_id": rid,
                    "full_name": m["full_name"],
                    "apartment_number": m["apartment_number"],
                    "is_active": m["is_active"],
                    "similarity": sim_val
                }

        # Find best candidate across all enrolled residents
        best_candidate = max(resident_scores.values(), key=lambda x: x["similarity"])
        best_sim = best_candidate["similarity"]
        is_active = best_candidate["is_active"]

        decision, reason = self.policy.classify(best_sim, is_active=is_active)

        if decision == DecisionState.ALLOWED:
            return MatchResult(
                resident_id=best_candidate["resident_id"],
                full_name=best_candidate["full_name"],
                apartment_number=best_candidate["apartment_number"],
                similarity_score=best_sim,
                decision=decision,
                reason=reason,
                is_active=is_active,
                is_genuine_resident=True
            )
        elif decision == DecisionState.VERIFICATION_REQUIRED:
            return MatchResult(
                resident_id=best_candidate["resident_id"],
                full_name=f"{best_candidate['full_name']} (UNCONFIRMED)",
                apartment_number=best_candidate["apartment_number"],
                similarity_score=best_sim,
                decision=decision,
                reason=reason,
                is_active=is_active,
                is_genuine_resident=True
            )
        else:
            return MatchResult(
                resident_id=None if is_active else best_candidate["resident_id"],
                full_name="UNKNOWN PERSON" if is_active else f"{best_candidate['full_name']} (SUSPENDED)",
                apartment_number=None if is_active else best_candidate["apartment_number"],
                similarity_score=best_sim,
                decision=decision,
                reason=reason,
                is_active=is_active,
                is_genuine_resident=False
            )

