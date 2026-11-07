"""
Face Feature Extraction Module using OpenCV SFace.
Generates 128-dimensional dense biometric feature embeddings from aligned face crops.
"""

from pathlib import Path
from typing import Optional
import logging
import cv2
import numpy as np

from config.settings import CONFIG, FaceRecognizerConfig
from recognition.detector import DetectedFace

logger = logging.getLogger(__name__)

class FaceRecognizer:
    """SFace deep face recognition feature extractor."""

    def __init__(self, config: Optional[FaceRecognizerConfig] = None):
        self.config = config or CONFIG.recognizer
        model_path = Path(self.config.model_path)

        if not model_path.exists():
            raise FileNotFoundError(
                f"SFace model file not found at: {model_path}. "
                "Please run 'python download_models.py' to download required models."
            )

        self._recognizer = cv2.FaceRecognizerSF.create(
            model=str(model_path),
            config=""
        )
        logger.info(f"SFace FaceRecognizer initialized from {model_path.name}")

    def align_and_crop(self, image: np.ndarray, face: DetectedFace) -> np.ndarray:
        """
        Aligns and crops detected face using 5 facial landmarks into standardized 112x112 RGB image.
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid image input for align_and_crop")

        # alignCrop requires 15-element raw detection array from YuNet
        aligned_face = self._recognizer.alignCrop(image, face.raw_detection)
        return aligned_face

    def extract_embedding(self, image: np.ndarray, face: DetectedFace) -> np.ndarray:
        """
        Aligns detected face and generates 128-dimensional normalized float32 embedding vector.
        Output shape: (128,)
        """
        aligned = self.align_and_crop(image, face)
        raw_feat = self._recognizer.feature(aligned) # Shape: (1, 128)
        feat = raw_feat.flatten().astype(np.float32)

        # Ensure L2 unit normalization
        norm = np.linalg.norm(feat)
        if norm > 1e-6:
            feat = feat / norm
        return feat

    def extract_from_aligned(self, aligned_face: np.ndarray) -> np.ndarray:
        """Extracts 128-d embedding directly from a pre-aligned 112x112 face crop."""
        raw_feat = self._recognizer.feature(aligned_face)
        feat = raw_feat.flatten().astype(np.float32)
        norm = np.linalg.norm(feat)
        if norm > 1e-6:
            feat = feat / norm
        return feat

