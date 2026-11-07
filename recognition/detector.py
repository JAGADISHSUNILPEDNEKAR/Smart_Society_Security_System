"""
Face Detection Module using OpenCV YuNet.
Detects human faces, extracts bounding boxes, 5 facial landmarks, and confidence scores.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging
import cv2
import numpy as np

from config.settings import CONFIG, FaceDetectorConfig

logger = logging.getLogger(__name__)

@dataclass
class DetectedFace:
    """Represents a single face detected by YuNet."""
    bbox: tuple[int, int, int, int]           # (x, y, w, h)
    landmarks: list[tuple[float, float]]     # 5 landmarks: right_eye, left_eye, nose, right_mouth, left_mouth
    score: float                             # Confidence score [0.0, 1.0]
    raw_detection: np.ndarray                # 15-element array required for SFace alignCrop

    @property
    def x(self) -> int:
        return self.bbox[0]

    @property
    def y(self) -> int:
        return self.bbox[1]

    @property
    def w(self) -> int:
        return self.bbox[2]

    @property
    def h(self) -> int:
        return self.bbox[3]

    @property
    def area(self) -> int:
        return self.w * self.h


class FaceDetector:
    """YuNet Face Detector wrapper with dynamic resolution adaptation."""

    def __init__(self, config: Optional[FaceDetectorConfig] = None):
        self.config = config or CONFIG.detector
        model_path = Path(self.config.model_path)

        if not model_path.exists():
            raise FileNotFoundError(
                f"YuNet model file not found at: {model_path}. "
                "Please run 'python download_models.py' to download required models."
            )

        self._current_input_size = self.config.input_size
        self._detector = cv2.FaceDetectorYN.create(
            model=str(model_path),
            config="",
            input_size=self._current_input_size,
            score_threshold=self.config.score_threshold,
            nms_threshold=self.config.nms_threshold,
            top_k=self.config.top_k
        )
        logger.info(f"YuNet FaceDetector initialized from {model_path.name}")

    def detect(self, image: np.ndarray) -> list[DetectedFace]:
        """
        Detects faces in an RGB/BGR image.
        Returns a list of DetectedFace objects sorted by size (largest first).
        """
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]

        # Dynamically update detector input size to match current frame dimensions
        if (w, h) != self._current_input_size:
            self._detector.setInputSize((w, h))
            self._current_input_size = (w, h)

        _, raw_faces = self._detector.detect(image)

        if raw_faces is None or len(raw_faces) == 0:
            return []

        detected_faces: list[DetectedFace] = []
        for face_arr in raw_faces:
            # Face array contains 15 elements:
            # [0:4] = x, y, w, h
            # [4:14] = 5 landmarks (x, y) for re, le, nt, rcm, lcm
            # [14] = confidence score
            box_x = max(0, int(face_arr[0]))
            box_y = max(0, int(face_arr[1]))
            box_w = min(w - box_x, int(face_arr[2]))
            box_h = min(h - box_y, int(face_arr[3]))
            score = float(face_arr[14])

            # Discard detections smaller than minimum size
            if box_w < self.config.min_face_size or box_h < self.config.min_face_size:
                continue

            landmarks = [
                (float(face_arr[4]), float(face_arr[5])),   # Right Eye
                (float(face_arr[6]), float(face_arr[7])),   # Left Eye
                (float(face_arr[8]), float(face_arr[9])),   # Nose Tip
                (float(face_arr[10]), float(face_arr[11])), # Right Mouth Corner
                (float(face_arr[12]), float(face_arr[13]))  # Left Mouth Corner
            ]

            detected_faces.append(
                DetectedFace(
                    bbox=(box_x, box_y, box_w, box_h),
                    landmarks=landmarks,
                    score=score,
                    raw_detection=face_arr
                )
            )

        # Sort largest face first (prominent candidate in front of security gate)
        detected_faces.sort(key=lambda f: f.area, reverse=True)
        return detected_faces

    @staticmethod
    def draw_face_annotations(
        image: np.ndarray,
        face: DetectedFace,
        color: tuple[int, int, int] = (0, 255, 0),
        label: Optional[str] = None,
        subtext: Optional[str] = None
    ) -> np.ndarray:
        """Draws bounding box, landmarks, and identification banner on the image."""
        annotated = image.copy()
        x, y, w, h = face.bbox

        # 1. Bounding box with corner accents
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
        corner_len = min(20, w // 4, h // 4)
        thickness = 3
        # Top-Left
        cv2.line(annotated, (x, y), (x + corner_len, y), color, thickness)
        cv2.line(annotated, (x, y), (x, y + corner_len), color, thickness)
        # Top-Right
        cv2.line(annotated, (x + w, y), (x + w - corner_len, y), color, thickness)
        cv2.line(annotated, (x + w, y), (x + w, y + corner_len), color, thickness)
        # Bottom-Left
        cv2.line(annotated, (x, y + h), (x + corner_len, y + h), color, thickness)
        cv2.line(annotated, (x, y + h), (x, y + h - corner_len), color, thickness)
        # Bottom-Right
        cv2.line(annotated, (x + w, y + h), (x + w - corner_len, y + h), color, thickness)
        cv2.line(annotated, (x + w, y + h), (x + w, y + h - corner_len), color, thickness)

        # 2. Draw landmarks
        for lx, ly in face.landmarks:
            cv2.circle(annotated, (int(lx), int(ly)), 2, (0, 255, 255), -1)

        # 3. Text label background banner
        if label:
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.55
            text_thickness = 2
            (tw, th), _ = cv2.getTextSize(label, font, font_scale, text_thickness)
            banner_h = th + 10
            banner_w = max(tw + 12, w)
            banner_y1 = max(0, y - banner_h)
            banner_y2 = y

            cv2.rectangle(annotated, (x, banner_y1), (x + banner_w, banner_y2), color, -1)
            cv2.putText(
                annotated,
                label,
                (x + 6, y - 6),
                font,
                font_scale,
                (0, 0, 0),
                text_thickness,
                cv2.LINE_AA
            )

        # 4. Optional subtext below bounding box
        if subtext:
            cv2.putText(
                annotated,
                subtext,
                (x, y + h + 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1,
                cv2.LINE_AA
            )

        return annotated

