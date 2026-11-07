"""Face recognition and biometric matching package."""
from recognition.detector import FaceDetector, DetectedFace
from recognition.recognizer import FaceRecognizer
from recognition.embeddings import (
    serialize_embedding,
    deserialize_embedding,
    compute_cosine_similarity,
    compute_euclidean_distance,
    aggregate_embeddings
)
from recognition.threshold import ThresholdPolicy
from recognition.matcher import FaceMatcher, MatchResult

__all__ = [
    "FaceDetector",
    "DetectedFace",
    "FaceRecognizer",
    "serialize_embedding",
    "deserialize_embedding",
    "compute_cosine_similarity",
    "compute_euclidean_distance",
    "aggregate_embeddings",
    "ThresholdPolicy",
    "FaceMatcher",
    "MatchResult"
]

