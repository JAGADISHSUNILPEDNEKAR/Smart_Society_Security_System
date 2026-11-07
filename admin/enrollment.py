"""
Biometric Enrollment and Image Quality Verification Module.
Validates illumination, focus sharpness, single-face constraints,
and generates enrolled biometric templates.
"""

from dataclasses import dataclass
from typing import Optional
import logging
import cv2
import numpy as np

from recognition.detector import FaceDetector, DetectedFace
from recognition.recognizer import FaceRecognizer

logger = logging.getLogger(__name__)

@dataclass
class QualityValidationResult:
    """Outcome of pre-enrollment biometric quality check."""
    is_valid: bool
    reason: str
    brightness: float
    sharpness: float
    face: Optional[DetectedFace] = None

class BiometricEnrollmentService:
    """Manages facial image quality inspection and template generation."""

    def __init__(self, detector: FaceDetector, recognizer: FaceRecognizer):
        self.detector = detector
        self.recognizer = recognizer

    def validate_image_quality(self, image: np.ndarray) -> QualityValidationResult:
        """
        Validates frame quality:
        1. Non-empty image
        2. Adequate illumination (no severe under/over-exposure)
        3. Sufficient optical sharpness (no motion blur)
        4. Exactly one human face in the frame
        5. Minimum face bounding box dimensions
        6. Detection confidence threshold
        """
        if image is None or image.size == 0:
            return QualityValidationResult(
                is_valid=False,
                reason="Empty or unreadable image frame",
                brightness=0.0,
                sharpness=0.0
            )

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # 1. Illumination check (mean pixel brightness)
        brightness = float(np.mean(gray))
        if brightness < 35.0:
            return QualityValidationResult(
                is_valid=False,
                reason=f"Frame is too dark (brightness: {brightness:.1f} < 35). Please improve lighting.",
                brightness=brightness,
                sharpness=0.0
            )
        if brightness > 235.0:
            return QualityValidationResult(
                is_valid=False,
                reason=f"Frame is overexposed (brightness: {brightness:.1f} > 235). Please avoid direct glare.",
                brightness=brightness,
                sharpness=0.0
            )

        # 2. Focus sharpness check (Laplacian variance)
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if sharpness < 25.0:
            return QualityValidationResult(
                is_valid=False,
                reason=f"Image is blurry (sharpness: {sharpness:.1f} < 25). Please hold still.",
                brightness=brightness,
                sharpness=sharpness
            )

        # 3. Face detection check
        faces = self.detector.detect(image)
        if len(faces) == 0:
            return QualityValidationResult(
                is_valid=False,
                reason="No face detected. Please face the camera directly.",
                brightness=brightness,
                sharpness=sharpness
            )
        if len(faces) > 1:
            return QualityValidationResult(
                is_valid=False,
                reason=f"Multiple faces detected ({len(faces)}). Exactly one resident must be in frame during enrollment.",
                brightness=brightness,
                sharpness=sharpness
            )

        target_face = faces[0]

        # 4. Minimum face size check
        if target_face.w < 60 or target_face.h < 60:
            return QualityValidationResult(
                is_valid=False,
                reason=f"Face is too far from camera ({target_face.w}x{target_face.h} px). Please move closer.",
                brightness=brightness,
                sharpness=sharpness,
                face=target_face
            )

        # 5. Detection score check
        if target_face.score < 0.80:
            return QualityValidationResult(
                is_valid=False,
                reason=f"Face detection confidence too low ({target_face.score:.2f} < 0.80).",
                brightness=brightness,
                sharpness=sharpness,
                face=target_face
            )

        return QualityValidationResult(
            is_valid=True,
            reason="Face quality acceptable for biometric enrollment",
            brightness=brightness,
            sharpness=sharpness,
            face=target_face
        )

    def extract_enrollment_embedding(
        self,
        image: np.ndarray
    ) -> tuple[bool, str, Optional[np.ndarray], Optional[DetectedFace]]:
        """
        Validates quality and returns 128-d normalized biometric embedding vector.
        """
        validation = self.validate_image_quality(image)
        if not validation.is_valid or validation.face is None:
            return False, validation.reason, None, None

        try:
            embedding = self.recognizer.extract_embedding(image, validation.face)
            return True, "Embedding extracted successfully", embedding, validation.face
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return False, f"Embedding extraction error: {e}", None, validation.face

