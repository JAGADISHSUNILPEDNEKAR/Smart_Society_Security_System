"""
Configuration settings for the Smart Society Security System.
Centralizes paths, model hyperparameters, threshold defaults, and system constants.
"""

from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import os

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
METRICS_DIR = REPORTS_DIR / "metrics"

DEFAULT_DB_PATH = DATABASE_DIR / "smart_society.db"

# Deep Learning Model Paths
YUNET_MODEL_PATH = MODELS_DIR / "face_detection_yunet_2023mar.onnx"
SFACE_MODEL_PATH = MODELS_DIR / "face_recognition_sface_2021dec.onnx"

# Ensure essential runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)

class DecisionState(str, Enum):
    """Access control decision states."""
    ALLOWED = "ENTRY ALLOWED"
    REJECTED = "ENTRY REJECTED"
    VERIFICATION_REQUIRED = "VERIFICATION REQUIRED"

class VerificationStatus(str, Enum):
    """Access log verification review status."""
    AUTOMATIC = "AUTOMATIC"
    MANUALLY_APPROVED = "MANUALLY_APPROVED"
    MANUALLY_REJECTED = "MANUALLY_REJECTED"
    PENDING_REVIEW = "PENDING_REVIEW"

@dataclass(frozen=True)
class FaceDetectorConfig:
    """Hyperparameters for YuNet face detector."""
    model_path: Path = YUNET_MODEL_PATH
    score_threshold: float = 0.80   # Filter low confidence false positives
    nms_threshold: float = 0.30     # Non-maximum suppression threshold
    top_k: int = 5000               # Max detections prior to NMS
    input_size: tuple[int, int] = (320, 320)
    min_face_size: int = 50         # Minimum face width/height in pixels

@dataclass(frozen=True)
class FaceRecognizerConfig:
    """Hyperparameters for SFace face recognizer."""
    model_path: Path = SFACE_MODEL_PATH
    embedding_dimension: int = 128
    cosine_threshold_high: float = 0.363  # SFace recommended genuine match threshold
    cosine_threshold_low: float = 0.280   # Below this is strictly unknown/rejected

@dataclass(frozen=True)
class AccessControlConfig:
    """Access control rules and timing constraints."""
    cooldown_seconds: float = 8.0         # Deduplication window for identical identity
    unknown_cooldown_seconds: float = 4.0 # Deduplication window for unknown rejections
    max_recent_logs_display: int = 50
    society_name: str = "Greenfield Heights Residential Society"

@dataclass(frozen=True)
class SystemConfig:
    """Global system configuration container."""
    db_path: Path = DEFAULT_DB_PATH
    detector: FaceDetectorConfig = FaceDetectorConfig()
    recognizer: FaceRecognizerConfig = FaceRecognizerConfig()
    access: AccessControlConfig = AccessControlConfig()

# Global default instance
CONFIG = SystemConfig()

