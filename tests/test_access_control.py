"""
Unit tests for AccessControlDecisionEngine, deduplication cooldown, and guard overrides.
"""

import pytest
import numpy as np
import time
from database.db import DatabaseManager
from admin.resident_manager import ResidentManager
from access_control.event_logger import AccessEventLogger
from access_control.decision_engine import AccessControlDecisionEngine
from recognition.detector import FaceDetector, DetectedFace
from recognition.recognizer import FaceRecognizer
from recognition.matcher import FaceMatcher
from config.settings import DecisionState, VerificationStatus

class MockDetector:
    """Mock detector that returns a pre-configured DetectedFace for fast unit testing."""
    def __init__(self, face_to_return=None):
        self.face = face_to_return

    def detect(self, image):
        return [self.face] if self.face else []

class MockRecognizer:
    """Mock recognizer returning controlled 128-d vectors."""
    def __init__(self, vector):
        self.vector = vector

    def extract_embedding(self, image, face):
        return self.vector

def test_decision_engine_deduplication():
    """Verifies that repetitive frames of the same resident are deduplicated during cooldown."""
    db = DatabaseManager(":memory:")
    db.init_db()
    res_mgr = ResidentManager(db)
    logger_svc = AccessEventLogger(db)

    # Register resident
    v = np.zeros(128, dtype=np.float32)
    v[0] = 1.0
    res_mgr.register_resident("RES-10", "Dev Patel", "Flat 101", embeddings=[v])

    matcher = FaceMatcher(db)
    raw_dummy = np.zeros(15, dtype=np.float32)
    dummy_face = DetectedFace(bbox=(10, 10, 80, 80), landmarks=[(0,0)]*5, score=0.95, raw_detection=raw_dummy)

    mock_det = MockDetector(dummy_face)
    mock_rec = MockRecognizer(v)

    engine = AccessControlDecisionEngine(
        detector=mock_det,
        recognizer=mock_rec,
        matcher=matcher,
        logger_service=logger_svc,
        cooldown_seconds=10.0 # 10 second deduplication window
    )

    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # 1. First frame -> Must log event
    res1 = engine.process_frame(fake_frame)
    assert len(res1.face_decisions) == 1
    assert res1.face_decisions[0].logged is True
    assert res1.primary_decision == DecisionState.ALLOWED

    # Verify 1 entry in DB
    assert len(logger_svc.get_recent_logs()) == 1

    # 2. Second frame immediately after -> Deduplication active, MUST NOT log duplicate entry
    res2 = engine.process_frame(fake_frame)
    assert len(res2.face_decisions) == 1
    assert res2.face_decisions[0].logged is False # Deduplicated!
    assert res2.primary_decision == DecisionState.ALLOWED

    # DB count must still be 1!
    assert len(logger_svc.get_recent_logs()) == 1

def test_guard_override_workflow():
    """Verifies manual security guard override transitions."""
    db = DatabaseManager(":memory:")
    db.init_db()
    logger_svc = AccessEventLogger(db)

    # Log an uncertain event requiring verification
    log_id = logger_svc.log_event(
        decision=DecisionState.VERIFICATION_REQUIRED,
        detected_name="Uncertain Resident",
        similarity_score=0.32,
        verification_status=VerificationStatus.PENDING_REVIEW
    )

    rec = logger_svc.get_recent_logs()[0]
    assert rec.decision == DecisionState.VERIFICATION_REQUIRED
    assert rec.verification_status == VerificationStatus.PENDING_REVIEW

    # Guard approves entry after ID inspection
    engine = AccessControlDecisionEngine(None, None, None, logger_svc)
    success = engine.manual_guard_override(log_id, approve=True, notes="Guard checked society ID card")
    assert success is True

    # Record must be updated
    updated_rec = logger_svc.get_recent_logs()[0]
    assert updated_rec.decision == DecisionState.ALLOWED
    assert updated_rec.verification_status == VerificationStatus.MANUALLY_APPROVED
    assert "Guard checked society ID card" in updated_rec.reason

