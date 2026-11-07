"""
Unit tests for DatabaseManager, schema enforcement, cascading deletes, and audit logs.
"""

import pytest
import numpy as np
from database.db import DatabaseManager
from admin.resident_manager import ResidentManager
from access_control.event_logger import AccessEventLogger
from config.settings import DecisionState, VerificationStatus
from recognition.embeddings import serialize_embedding, deserialize_embedding

@pytest.fixture
def test_db():
    """Provides a clean in-memory SQLite database instance with initialized schema."""
    db = DatabaseManager(":memory:")
    db.init_db()
    return db

def test_schema_initialization(test_db):
    """Verifies all required tables, indexes, and initial settings exist."""
    tables = [r["name"] for r in test_db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")]
    assert "residents" in tables
    assert "face_embeddings" in tables
    assert "access_logs" in tables
    assert "system_settings" in tables

    # Verify seeded system settings
    high_th = test_db.get_setting("recognition_threshold_high")
    assert high_th == "0.363"
    assert test_db.get_setting("cooldown_seconds") == "8.0"

def test_resident_crud(test_db):
    """Tests creating, querying, updating, and listing residents."""
    mgr = ResidentManager(test_db)

    # 1. Register resident
    record = mgr.register_resident(
        resident_id="RES-001",
        full_name="Rajesh Kumar",
        apartment_number="Flat 301",
        contact_number="+91-9988776655",
        consent_given=True,
        notes="Owner"
    )
    assert record is not None
    assert record.resident_id == "RES-001"
    assert record.full_name == "Rajesh Kumar"
    assert record.is_active is True
    assert record.consent_given is True

    # 2. Duplicate ID prevention
    with pytest.raises(ValueError):
        mgr.register_resident(
            resident_id="RES-001",
            full_name="Duplicate Name",
            apartment_number="Flat 302"
        )

    # 3. Update resident details
    updated = mgr.update_resident("RES-001", apartment_number="Flat 305", is_active=False)
    assert updated.apartment_number == "Flat 305"
    assert updated.is_active is False

    # 4. Search residents
    results = mgr.list_residents(search_query="Rajesh")
    assert len(results) == 1
    assert results[0].resident_id == "RES-001"

def test_biometric_template_cascading_delete(test_db):
    """Ensures foreign key ON DELETE CASCADE deletes biometric templates when resident is removed."""
    mgr = ResidentManager(test_db)

    dummy_emb = np.random.randn(128).astype(np.float32)
    dummy_emb = dummy_emb / np.linalg.norm(dummy_emb)

    mgr.register_resident(
        resident_id="RES-002",
        full_name="Priya Nair",
        apartment_number="Flat 102",
        embeddings=[dummy_emb, dummy_emb]
    )

    embs = mgr.get_resident_embeddings("RES-002")
    assert len(embs) == 2
    # Verify templates count in DB table
    count_before = test_db.fetch_one("SELECT COUNT(*) as c FROM face_embeddings WHERE resident_id = 'RES-002'")["c"]
    assert count_before == 2

    # Delete resident
    deleted = mgr.delete_resident("RES-002")
    assert deleted is True

    # Biometric templates must be cascaded and wiped
    count_after = test_db.fetch_one("SELECT COUNT(*) as c FROM face_embeddings WHERE resident_id = 'RES-002'")["c"]
    assert count_after == 0

def test_access_logger(test_db):
    """Tests access event logging, filtering, and today statistics."""
    res_mgr = ResidentManager(test_db)
    logger_svc = AccessEventLogger(test_db)

    # First register residents to satisfy referential integrity
    res_mgr.register_resident("RES-001", "Rajesh Kumar", "Flat 301")
    res_mgr.register_resident("RES-002", "Priya Nair", "Flat 102")

    # Log 3 events
    id1 = logger_svc.log_event(
        decision=DecisionState.ALLOWED,
        detected_name="Rajesh Kumar",
        resident_id="RES-001",
        apartment_number="Flat 301",
        similarity_score=0.78,
        verification_status=VerificationStatus.AUTOMATIC
    )
    id2 = logger_svc.log_event(
        decision=DecisionState.REJECTED,
        detected_name="UNKNOWN PERSON",
        resident_id=None,
        similarity_score=0.12,
        verification_status=VerificationStatus.AUTOMATIC
    )
    id3 = logger_svc.log_event(
        decision=DecisionState.VERIFICATION_REQUIRED,
        detected_name="Priya Nair",
        resident_id="RES-002",
        apartment_number="Flat 102",
        similarity_score=0.31,
        verification_status=VerificationStatus.PENDING_REVIEW
    )

    assert id1 > 0 and id2 > 0 and id3 > 0

    # Statistics check
    stats = logger_svc.get_today_statistics()
    assert stats["total"] == 3
    assert stats["allowed"] == 1
    assert stats["rejected"] == 1
    assert stats["verification"] == 1

    # Guard override check
    overridden = logger_svc.update_verification_status(
        log_id=id3,
        new_status=VerificationStatus.MANUALLY_APPROVED,
        new_decision=DecisionState.ALLOWED,
        notes="Security guard verified ID"
    )
    assert overridden is True
    updated_rec = logger_svc.filter_logs(limit=10)[0] # Most recent
    assert updated_rec.decision == DecisionState.ALLOWED
    assert updated_rec.verification_status == VerificationStatus.MANUALLY_APPROVED
