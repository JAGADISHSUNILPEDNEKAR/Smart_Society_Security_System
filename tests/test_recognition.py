"""
Unit tests for YuNet detector, SFace recognizer, embedding operations, and FaceMatcher.
"""

import pytest
import numpy as np
import cv2
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
from recognition.matcher import FaceMatcher
from database.db import DatabaseManager
from admin.resident_manager import ResidentManager
from config.settings import DecisionState

def test_embedding_serialization():
    """Verifies float32 128-d vector roundtrip through byte serialization."""
    vec = np.random.randn(128).astype(np.float32)
    vec = vec / np.linalg.norm(vec)

    raw_blob = serialize_embedding(vec)
    assert len(raw_blob) == 128 * 4 # 512 bytes

    restored = deserialize_embedding(raw_blob)
    assert restored.shape == (128,)
    assert restored.dtype == np.float32
    assert np.allclose(vec, restored, atol=1e-6)

def test_cosine_similarity_properties():
    """Validates mathematical properties of cosine similarity."""
    v1 = np.random.randn(128).astype(np.float32)
    v1 = v1 / np.linalg.norm(v1)

    # Identical vectors -> similarity = 1.0
    sim_self = compute_cosine_similarity(v1, v1)
    assert pytest.approx(sim_self, abs=1e-5) == 1.0

    # Opposite vectors -> similarity = -1.0
    sim_opp = compute_cosine_similarity(v1, -v1)
    assert pytest.approx(sim_opp, abs=1e-5) == -1.0

def test_aggregate_embeddings():
    """Tests centroid aggregation of multi-angle biometric samples."""
    v1 = np.array([1.0, 0.0, 0.0] + [0.0]*125, dtype=np.float32)
    v2 = np.array([0.0, 1.0, 0.0] + [0.0]*125, dtype=np.float32)

    centroid = aggregate_embeddings([v1, v2])
    assert centroid.shape == (128,)
    # Norm must be 1.0
    assert pytest.approx(np.linalg.norm(centroid), abs=1e-5) == 1.0
    # Equidistant from both v1 and v2
    sim1 = compute_cosine_similarity(centroid, v1)
    sim2 = compute_cosine_similarity(centroid, v2)
    assert pytest.approx(sim1, abs=1e-5) == pytest.approx(sim2, abs=1e-5)

def test_threshold_policy():
    """Verifies 3-tier access classification logic."""
    policy = ThresholdPolicy(threshold_high=0.363, threshold_low=0.280)

    # 1. High confidence -> ALLOWED
    d1, _ = policy.classify(0.650, is_active=True)
    assert d1 == DecisionState.ALLOWED

    # 2. Uncertain band -> VERIFICATION_REQUIRED
    d2, _ = policy.classify(0.315, is_active=True)
    assert d2 == DecisionState.VERIFICATION_REQUIRED

    # 3. Below low -> REJECTED
    d3, _ = policy.classify(0.180, is_active=True)
    assert d3 == DecisionState.REJECTED

    # 4. Inactive resident -> REJECTED even with high similarity
    d4, r4 = policy.classify(0.850, is_active=False)
    assert d4 == DecisionState.REJECTED
    assert "inactive" in r4.lower()

def test_face_matcher_with_database():
    """Tests FaceMatcher loading, vector matching, and unknown identity rejection."""
    db = DatabaseManager(":memory:")
    db.init_db()
    res_mgr = ResidentManager(db)

    # Seed 2 residents with orthogonal embeddings
    v_alice = np.zeros(128, dtype=np.float32)
    v_alice[0] = 1.0
    v_bob = np.zeros(128, dtype=np.float32)
    v_bob[1] = 1.0

    res_mgr.register_resident("RES-A", "Alice Smith", "Apt 101", embeddings=[v_alice])
    res_mgr.register_resident("RES-B", "Bob Jones", "Apt 102", embeddings=[v_bob])

    matcher = FaceMatcher(db, ThresholdPolicy(threshold_high=0.363, threshold_low=0.280))

    # Query with Alice's vector + slight noise
    query_alice = v_alice.copy()
    query_alice[2] = 0.05
    query_alice = query_alice / np.linalg.norm(query_alice)

    match_a = matcher.match(query_alice)
    assert match_a.decision == DecisionState.ALLOWED
    assert match_a.resident_id == "RES-A"
    assert match_a.full_name == "Alice Smith"
    assert match_a.similarity_score > 0.90

    # Query with completely unknown face (orthogonal to Alice and Bob)
    query_unknown = np.zeros(128, dtype=np.float32)
    query_unknown[10] = 1.0
    match_u = matcher.match(query_unknown)
    assert match_u.decision == DecisionState.REJECTED
    assert match_u.full_name == "UNKNOWN PERSON"

