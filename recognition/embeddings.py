"""
Biometric Embedding Serialization and Vector Operations.
Provides BLOB conversion for SQLite, L2 normalization, cosine similarity,
and multi-sample template aggregation.
"""

import numpy as np
from typing import Optional

def serialize_embedding(embedding: np.ndarray) -> bytes:
    """Serializes 128-d float32 numpy array into raw byte string for SQLite storage."""
    vec = np.asarray(embedding, dtype=np.float32).flatten()
    if vec.shape[0] != 128:
        raise ValueError(f"Expected 128-dimensional embedding, got {vec.shape[0]}")
    return vec.tobytes()

def deserialize_embedding(blob: bytes) -> np.ndarray:
    """Deserializes SQLite BLOB back into normalized 128-d float32 numpy array."""
    if not blob or len(blob) != 128 * 4: # 128 * 4 bytes = 512 bytes
        raise ValueError(f"Invalid embedding BLOB length: {len(blob) if blob else 0} bytes (expected 512)")
    arr = np.frombuffer(blob, dtype=np.float32).copy()
    norm = np.linalg.norm(arr)
    if norm > 1e-6:
        arr = arr / norm
    return arr

def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Computes cosine similarity between two 128-d embedding vectors."""
    v1 = np.asarray(vec1, dtype=np.float32).flatten()
    v2 = np.asarray(vec2, dtype=np.float32).flatten()

    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 < 1e-6 or norm2 < 1e-6:
        return 0.0

    dot = float(np.dot(v1, v2) / (norm1 * norm2))
    # Clip to valid cosine range [-1.0, 1.0] to guard against tiny float precision drift
    return max(-1.0, min(1.0, dot))

def compute_euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Computes normalized Euclidean (L2) distance between two embeddings."""
    v1 = np.asarray(vec1, dtype=np.float32).flatten()
    v2 = np.asarray(vec2, dtype=np.float32).flatten()
    return float(np.linalg.norm(v1 - v2))

def aggregate_embeddings(embeddings_list: list[np.ndarray]) -> np.ndarray:
    """
    Computes normalized centroid template from multiple enrolled biometric samples
    (e.g., frontal, tilt-left, tilt-right, smiling).
    """
    if not embeddings_list:
        raise ValueError("Cannot aggregate empty embeddings list")

    stack = np.vstack([np.asarray(e, dtype=np.float32).flatten() for e in embeddings_list])
    mean_vec = np.mean(stack, axis=0)
    norm = np.linalg.norm(mean_vec)
    if norm > 1e-6:
        mean_vec = mean_vec / norm
    return mean_vec

