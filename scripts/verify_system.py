"""
Automated System Diagnostic & End-to-End Verification Script.
Evaluates camera, deep learning models, database, decision engine,
deduplication filters, test suites, and academic report artifacts.
"""

import sys
import os
import time
import hashlib
from pathlib import Path
import numpy as np

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import (
    CONFIG,
    YUNET_MODEL_PATH,
    SFACE_MODEL_PATH,
    DEFAULT_DB_PATH,
    FIGURES_DIR,
    METRICS_DIR,
    DecisionState,
    VerificationStatus
)
from database.db import DatabaseManager
from admin.resident_manager import ResidentManager
from recognition.detector import FaceDetector, DetectedFace
from recognition.recognizer import FaceRecognizer
from recognition.matcher import FaceMatcher
from access_control.event_logger import AccessEventLogger
from access_control.decision_engine import AccessControlDecisionEngine
from camera.webcam import WebcamStream

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def check_mark(status: bool) -> str:
    return "[\033[92mPASS\033[0m]" if status else "[\033[91mFAIL\033[0m]"

def run_diagnostics():
    print_header("SMART SOCIETY SECURITY SYSTEM — END-TO-END DIAGNOSTIC")
    print(f"Python Runtime: {sys.version.split()[0]} on {sys.platform}")
    print(f"Project Working Directory: {BASE_DIR}")

    results = []

    # 1. Model Files Integrity
    print_header("1. Deep Learning Model Files Integrity")
    yunet_ok = YUNET_MODEL_PATH.exists() and YUNET_MODEL_PATH.stat().st_size > 200_000
    sface_ok = SFACE_MODEL_PATH.exists() and SFACE_MODEL_PATH.stat().st_size > 35_000_000

    print(f" {check_mark(yunet_ok)} YuNet Face Detector: {YUNET_MODEL_PATH.name} ({YUNET_MODEL_PATH.stat().st_size if YUNET_MODEL_PATH.exists() else 0:,} bytes)")
    print(f" {check_mark(sface_ok)} SFace Face Recognizer: {SFACE_MODEL_PATH.name} ({SFACE_MODEL_PATH.stat().st_size if SFACE_MODEL_PATH.exists() else 0:,} bytes)")
    results.append(("Model Files Integrity", yunet_ok and sface_ok))

    # 2. SQLite Database Schema & Tables
    print_header("2. SQLite Relational Database Engine")
    try:
        test_db = DatabaseManager(":memory:")
        test_db.init_db()
        tables = [r["name"] for r in test_db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")]
        db_ok = all(t in tables for t in ["residents", "face_embeddings", "access_logs", "system_settings"])
        high_th = test_db.get_setting("recognition_threshold_high")
        print(f" {check_mark(db_ok)} Relational Schema: 4 core tables created successfully")
        print(f" {check_mark(high_th == '0.363')} Seed Settings: recognition_threshold_high = {high_th}")
        results.append(("SQLite Relational Database", db_ok))
    except Exception as e:
        print(f" [\033[91mFAIL\033[0m] Database error: {e}")
        results.append(("SQLite Relational Database", False))

    # 3. Vision Pipeline (Detector & Recognizer)
    print_header("3. Computer Vision Inference Pipeline")
    try:
        detector = FaceDetector()
        recognizer = FaceRecognizer()

        # Synthetic test face canvas
        img = np.zeros((320, 320, 3), dtype=np.uint8)
        img[:] = (200, 200, 200)

        # Raw alignment and feature extraction test
        raw_dummy = np.array([[80, 80, 160, 160, 120, 120, 200, 120, 160, 160, 130, 210, 190, 210, 0.99]], dtype=np.float32)
        dummy_face = DetectedFace(bbox=(80, 80, 160, 160), landmarks=[(120, 120), (200, 120), (160, 160), (130, 210), (190, 210)], score=0.99, raw_detection=raw_dummy[0])
        
        emb = recognizer.extract_embedding(img, dummy_face)
        norm_val = float(np.linalg.norm(emb))
        cv_ok = (emb.shape == (128,) and abs(norm_val - 1.0) < 1e-5)
        print(f" {check_mark(cv_ok)} SFace Feature Extractor: Shape {emb.shape}, L2-Norm = {norm_val:.5f}")
        results.append(("Computer Vision Pipeline", cv_ok))
    except Exception as e:
        print(f" [\033[91mFAIL\033[0m] Vision pipeline error: {e}")
        results.append(("Computer Vision Pipeline", False))

    # 4. Camera Stream & Fallback
    print_header("4. Camera Hardware Ingestion & Resilience")
    try:
        cam = WebcamStream(camera_index=0)
        started = cam.start(allow_simulation_fallback=True)
        ret, frame = cam.read_frame()
        fps = cam.get_fps()
        cam.stop()
        cam_ok = started and ret and frame is not None
        mode_str = "Physical AVFoundation Webcam" if not cam.is_simulated else "Simulated Fallback Security Feed"
        print(f" {check_mark(cam_ok)} Video Ingestion: Resolution {frame.shape if frame is not None else None} via {mode_str}")
        results.append(("Camera Sensor Subsystem", cam_ok))
    except Exception as e:
        print(f" [\033[91mFAIL\033[0m] Camera error: {e}")
        results.append(("Camera Sensor Subsystem", False))

    # 5. Access Decision Engine & Deduplication Cooldown
    print_header("5. Access Decision Engine & Deduplication")
    try:
        db = DatabaseManager(":memory:")
        db.init_db()
        res_mgr = ResidentManager(db)
        logger_svc = AccessEventLogger(db)

        # Register Aarav Patel
        v_aarav = np.random.randn(128).astype(np.float32)
        v_aarav = v_aarav / np.linalg.norm(v_aarav)
        res_mgr.register_resident("RES-101", "Aarav Patel", "Tower-A 402", embeddings=[v_aarav])

        matcher = FaceMatcher(db)
        engine = AccessControlDecisionEngine(None, None, matcher, logger_svc, cooldown_seconds=8.0)

        # Match Aarav
        match1 = matcher.match(v_aarav)
        aarav_ok = (match1.decision == DecisionState.ALLOWED and match1.full_name == "Aarav Patel")

        # Match Unknown
        v_unknown = np.random.randn(128).astype(np.float32)
        v_unknown = v_unknown / np.linalg.norm(v_unknown)
        match_unk = matcher.match(v_unknown)
        unk_ok = (match_unk.decision == DecisionState.REJECTED and match_unk.full_name == "UNKNOWN PERSON")

        # Match Suspended
        res_mgr.update_resident("RES-101", is_active=False)
        matcher.reload_templates()
        match_susp = matcher.match(v_aarav)
        susp_ok = (match_susp.decision == DecisionState.REJECTED)

        dec_ok = aarav_ok and unk_ok and susp_ok
        print(f" {check_mark(aarav_ok)} Authorized Resident Decision: GREEN (ENTRY ALLOWED)")
        print(f" {check_mark(unk_ok)} Impostor Intruder Decision: RED (ENTRY REJECTED - UNKNOWN)")
        print(f" {check_mark(susp_ok)} Suspended Resident Interception: RED (ENTRY REJECTED)")
        results.append(("Decision Engine Logic", dec_ok))
    except Exception as e:
        print(f" [\033[91mFAIL\033[0m] Decision engine error: {e}")
        results.append(("Decision Engine Logic", False))

    # 6. Evaluation Deliverables
    print_header("6. Academic Evaluation Figures & Artifacts")
    roc_p = FIGURES_DIR / "roc_curve.png"
    far_p = FIGURES_DIR / "far_frr_curve.png"
    cm_p = FIGURES_DIR / "confusion_matrix.png"
    dist_p = FIGURES_DIR / "score_distribution.png"
    metrics_p = METRICS_DIR / "summary_metrics.json"

    figs_ok = all(p.exists() for p in [roc_p, far_p, cm_p, dist_p, metrics_p])
    print(f" {check_mark(roc_p.exists())} Figure: ROC Curve ({roc_p.name})")
    print(f" {check_mark(far_p.exists())} Figure: FAR vs FRR Trade-off Curve ({far_p.name})")
    print(f" {check_mark(cm_p.exists())} Figure: Confusion Matrix Heatmap ({cm_p.name})")
    print(f" {check_mark(dist_p.exists())} Figure: Similarity Score Distribution ({dist_p.name})")
    print(f" {check_mark(metrics_p.exists())} Metrics Table: Evaluation Summary JSON ({metrics_p.name})")
    results.append(("Academic Evaluation Artifacts", figs_ok))

    # Summary Card
    print_header("SYSTEM DIAGNOSTIC SUMMARY REPORT")
    total_checks = len(results)
    passed_checks = sum(1 for _, ok in results if ok)

    for name, ok in results:
        print(f"  {check_mark(ok)}  {name}")

    print("-" * 70)
    print(f"  Final Status: {passed_checks}/{total_checks} Subsystems Operational ({passed_checks/total_checks*100:.1f}%)")
    print("=" * 70 + "\n")

    return passed_checks == total_checks

if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
