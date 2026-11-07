"""
Threshold Engine for Biometric Access Control Decisions.
Maps cosine similarity scores to discrete access decisions:
- ENTRY ALLOWED (GREEN)
- VERIFICATION REQUIRED (YELLOW)
- ENTRY REJECTED (RED)
"""

from dataclasses import dataclass
from config.settings import DecisionState, CONFIG

@dataclass
class ThresholdPolicy:
    """Configurable recognition thresholds."""
    threshold_high: float = 0.363   # Confident genuine match
    threshold_low: float = 0.280    # Strict boundary below which face is UNKNOWN

    def classify(self, similarity: float, is_active: bool = True) -> tuple[DecisionState, str]:
        """
        Evaluates similarity score and resident active status to determine access decision.
        """
        # Security Rule: Inactive or suspended residents are NEVER granted entry
        if not is_active:
            return DecisionState.REJECTED, "Resident account is suspended / inactive"

        if similarity >= self.threshold_high:
            return DecisionState.ALLOWED, f"High confidence match ({similarity:.3f} >= {self.threshold_high:.3f})"
        elif similarity >= self.threshold_low:
            return DecisionState.VERIFICATION_REQUIRED, (
                f"Borderline similarity ({similarity:.3f} between "
                f"{self.threshold_low:.3f} and {self.threshold_high:.3f}) - Security check required"
            )
        else:
            return DecisionState.REJECTED, (
                f"No confident match ({similarity:.3f} < {self.threshold_low:.3f}) - Unknown Individual"
            )

