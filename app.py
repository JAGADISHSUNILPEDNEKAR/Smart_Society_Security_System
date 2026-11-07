"""
Smart Society Security System — Main Application Entry Point.
AI-Powered Face Recognition & Biometric Access Control for Residential Societies.
"""

import streamlit as st
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("smart_society")

# 1. Page Configuration (Must be first Streamlit command)
st.set_page_config(
    page_title="Smart Society Security System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from config.settings import (
    CONFIG,
    DEFAULT_DB_PATH,
    YUNET_MODEL_PATH,
    SFACE_MODEL_PATH
)
from database.db import DatabaseManager
from recognition.detector import FaceDetector
from recognition.recognizer import FaceRecognizer
from recognition.matcher import FaceMatcher
from access_control.event_logger import AccessEventLogger
from access_control.decision_engine import AccessControlDecisionEngine
from admin.resident_manager import ResidentManager
from admin.enrollment import BiometricEnrollmentService
from camera.webcam import WebcamStream
from ui.styles import get_custom_css
from ui.components import render_header
from ui.dashboard import (
    render_live_monitor_tab,
    render_residents_tab,
    render_audit_logs_tab,
    render_settings_tab,
    render_evaluation_tab
)

# Apply Custom CSS styling
st.markdown(get_custom_css(), unsafe_allow_html=True)

# 2. Singleton Service Initialization with Streamlit Caching
@st.cache_resource
def get_database_manager() -> DatabaseManager:
    """Initializes and returns the singleton DatabaseManager."""
    db = DatabaseManager(DEFAULT_DB_PATH)
    db.init_db()
    return db

@st.cache_resource
def get_computer_vision_services():
    """Initializes and returns FaceDetector, FaceRecognizer, and WebcamStream."""
    detector = FaceDetector()
    recognizer = FaceRecognizer()
    webcam = WebcamStream(camera_index=0)
    return detector, recognizer, webcam

# Initialize core services
db = get_database_manager()
detector, recognizer, webcam = get_computer_vision_services()

if "matcher" not in st.session_state:
    st.session_state.matcher = FaceMatcher(db)

matcher = st.session_state.matcher
res_mgr = ResidentManager(db)
logger_svc = AccessEventLogger(db)
enrollment_svc = BiometricEnrollmentService(detector, recognizer)

cooldown_sec = float(db.get_setting("cooldown_seconds", "8.0"))
decision_engine = AccessControlDecisionEngine(
    detector=detector,
    recognizer=recognizer,
    matcher=matcher,
    logger_service=logger_svc,
    cooldown_seconds=cooldown_sec
)

# 3. Sidebar Navigation & Status Panel
society_name = db.get_setting("society_name", "Greenfield Heights Residential Society")

with st.sidebar:
    st.title("🛡️ Access Control")
    st.caption("v1.0.0 — Security Terminal")

    st.markdown("---")
    nav_selection = st.radio(
        "Navigation Menu:",
        [
            "📹 Live Gate Monitor",
            "👥 Resident Directory",
            "📜 Access Logs & Audit",
            "⚙️ Security Settings",
            "📊 Accuracy & Evaluation"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("#### 🟢 Operational Status")
    st.write(f"- **System**: ONLINE")
    st.write(f"- **Detector**: YuNet ONNX")
    st.write(f"- **Recognizer**: SFace 128-d")
    st.write(f"- **Database**: SQLite (WAL)")

    active_res = len(res_mgr.list_residents(active_only=True))
    st.write(f"- **Enrolled Gallery**: {active_res} active")

    st.markdown("---")
    st.caption("Academic Evaluation Prototype © 2026. Designed for Smart Society Security Access Control.")

# 4. Main View Header and Router
render_header(society_name)

if nav_selection == "📹 Live Gate Monitor":
    render_live_monitor_tab(
        db=db,
        res_mgr=res_mgr,
        logger_svc=logger_svc,
        decision_engine=decision_engine,
        enrollment_svc=enrollment_svc,
        webcam=webcam
    )
elif nav_selection == "👥 Resident Directory":
    render_residents_tab(
        res_mgr=res_mgr,
        enrollment_svc=enrollment_svc,
        matcher=matcher
    )
elif nav_selection == "📜 Access Logs & Audit":
    render_audit_logs_tab(logger_svc=logger_svc)
elif nav_selection == "⚙️ Security Settings":
    render_settings_tab(
        db=db,
        matcher=matcher,
        decision_engine=decision_engine
    )
elif nav_selection == "📊 Accuracy & Evaluation":
    render_evaluation_tab()

