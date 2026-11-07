"""
Real-Time Access Control Decision Engine.
Coordinates face detection, feature extraction, biometric matching, visual annotation,
event deduplication cooldown, and manual security guard override.
"""

from dataclasses import dataclass
from typing import Optional
import time
import logging
import cv2
import numpy as np

from config.settings import DecisionState, VerificationStatus, CONFIG
from recognition.detector import FaceDetector, DetectedFace
from recognition.recognizer import FaceRecognizer
from recognition.matcher import FaceMatcher, MatchResult
from access_control.event_logger import AccessEventLogger

logger = logging.getLogger(__name__)

# BGR Color Constants
COLOR_ALLOWED = (0, 220, 0)         # Vibrant Green
COLOR_REJECTED = (0, 0, 230)        # Bold Red
COLOR_VERIFICATION = (0, 215, 255)  # Amber / Yellow
COLOR_NEUTRAL = (180, 180, 180)     # Gray

@dataclass
class FaceAccessDecision:
    """Access control decision for a single face detected in a frame."""
    face: DetectedFace
    match: MatchResult
    color: tuple[int, int, int]
    logged: bool
    log_id: Optional[int]

@dataclass
class FrameProcessingResult:
    """Consolidated access decision result for an entire video frame."""
    annotated_frame: np.ndarray
    face_decisions: list[FaceAccessDecision]
    primary_decision: Optional[DecisionState]
    primary_name: Optional[str]
    processing_time_ms: float

class AccessControlDecisionEngine:
    """Core decision engine governing residential access permissions."""

    def __init__(
        self,
        detector: FaceDetector,
        recognizer: FaceRecognizer,
        matcher: FaceMatcher,
        logger_service: AccessEventLogger,
        cooldown_seconds: float = 8.0
    ):
        self.detector = detector
        self.recognizer = recognizer
        self.matcher = matcher
        self.logger_service = logger_service
        self.cooldown_seconds = cooldown_seconds
        # Cooldown map: key -> last_logged_timestamp
        self._last_logged_time: dict[str, float] = {}

    def set_cooldown(self, seconds: float) -> None:
        """Configures entry deduplication cooldown window."""
        self.cooldown_seconds = max(1.0, float(seconds))
        logger.info(f"Access event deduplication window set to {self.cooldown_seconds}s")

    def process_frame(self, frame: np.ndarray) -> FrameProcessingResult:
        """
        Processes a single camera video frame:
        1. Detects faces
        2. Computes embeddings
        3. Matches against enrolled resident templates
        4. Applies security thresholds & deduplication
        5. Renders visual feedback (GREEN/RED/YELLOW) on frame
        """
        start_t = time.time()
        if frame is None or frame.size == 0:
            return FrameProcessingResult(
                annotated_frame=np.zeros((480, 640, 3), dtype=np.uint8),
                face_decisions=[],
                primary_decision=None,
                primary_name=None,
                processing_time_ms=0.0
            )

        annotated = frame.copy()
        faces = self.detector.detect(frame)
        face_decisions: list[FaceAccessDecision] = []

        now = time.time()

        for face in faces:
            try:
                embedding = self.recognizer.extract_embedding(frame, face)
                match = self.matcher.match(embedding)
            except Exception as e:
                logger.error(f"Error during face embedding/match: {e}")
                continue

            # Assign color and label based on decision
            if match.decision == DecisionState.ALLOWED:
                color = COLOR_ALLOWED
                label = f"ALLOWED: {match.full_name}"
                subtext = f"Apt {match.apartment_number} | Sim: {match.similarity_score:.2f}"
                dedup_key = f"res_{match.resident_id}"
            elif match.decision == DecisionState.VERIFICATION_REQUIRED:
                color = COLOR_VERIFICATION
                label = "VERIFICATION REQUIRED"
                subtext = f"{match.full_name} | Sim: {match.similarity_score:.2f} (Check ID)"
                dedup_key = f"verify_{match.resident_id}"
            else:
                color = COLOR_REJECTED
                label = "ENTRY REJECTED: UNKNOWN"
                subtext = f"Sim: {match.similarity_score:.2f} | Access Denied"
                dedup_key = f"unknown_{round(face.x, -2)}_{round(face.y, -2)}"

            # Deduplication cooldown check
            last_time = self._last_logged_time.get(dedup_key, 0.0)
            logged = False
            log_id = None

            if (now - last_time) >= self.cooldown_seconds:
                # Deduplication window elapsed: commit entry attempt to database audit trail
                v_status = (
                    VerificationStatus.PENDING_REVIEW
                    if match.decision == DecisionState.VERIFICATION_REQUIRED
                    else VerificationStatus.AUTOMATIC
                )
                log_id = self.logger_service.log_event(
                    decision=match.decision,
                    detected_name=match.full_name,
                    resident_id=match.resident_id,
                    apartment_number=match.apartment_number,
                    similarity_score=match.similarity_score,
                    verification_status=v_status,
                    reason=match.reason
                )
                self._last_logged_time[dedup_key] = now
                logged = True

            # Draw visual box and banner
            annotated = FaceDetector.draw_face_annotations(
                annotated,
                face=face,
                color=color,
                label=label,
                subtext=subtext
            )

            face_decisions.append(
                FaceAccessDecision(
                    face=face,
                    match=match,
                    color=color,
                    logged=logged,
                    log_id=log_id
                )
            )

        elapsed_ms = (time.time() - start_t) * 1000.0

        # Draw overall gate decision banner at top of frame
        primary_dec = None
        primary_name = None
        if face_decisions:
            # Primary face is the largest / foremost face in frame
            primary = face_decisions[0]
            primary_dec = primary.match.decision
            primary_name = primary.match.full_name
            self._draw_gate_banner(annotated, primary.match.decision, primary.match.full_name, primary.color)

        return FrameProcessingResult(
            annotated_frame=annotated,
            face_decisions=face_decisions,
            primary_decision=primary_dec,
            primary_name=primary_name,
            processing_time_ms=round(elapsed_ms, 1)
        )

    def manual_guard_override(
        self,
        log_id: int,
        approve: bool,
        notes: Optional[str] = None
    ) -> bool:
        """Allows active security guard to manually approve or deny access."""
        new_status = VerificationStatus.MANUALLY_APPROVED if approve else VerificationStatus.MANUALLY_REJECTED
        new_decision = DecisionState.ALLOWED if approve else DecisionState.REJECTED
        override_note = f"Guard Override: {'APPROVED' if approve else 'REJECTED'}"
        if notes:
            override_note += f" - {notes}"

        success = self.logger_service.update_verification_status(
            log_id=log_id,
            new_status=new_status,
            new_decision=new_decision,
            notes=override_note
        )
        logger.info(f"Manual security guard override on log #{log_id}: Success={success}")
        return success

    @staticmethod
    def _draw_gate_banner(
        frame: np.ndarray,
        decision: DecisionState,
        name: str,
        color: tuple[int, int, int]
    ) -> None:
        """Draws prominent security gate decision bar across top of live video."""
        h, w = frame.shape[:2]
        banner_h = 42

        # Semi-transparent top bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, banner_h), (25, 25, 25), -1)
        cv2.rectangle(overlay, (0, 0), (8, banner_h), color, -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Status text
        status_text = f"● {decision.value}: {name.upper()}"
        cv2.putText(
            frame,
            status_text,
            (18, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            color,
            2,
            cv2.LINE_AA
        )

