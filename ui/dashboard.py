"""
Dashboard Controllers and View Renderers for Smart Society Security System.
Implements the 5 core operational panels:
1. Live Gate Monitor
2. Resident Management & Enrollment
3. Access History & Audit Trail
4. System & Security Settings
5. Academic Evaluation & Analytics
"""

import time
import json
from pathlib import Path
from typing import Optional
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from config.settings import (
    DecisionState,
    VerificationStatus,
    FIGURES_DIR,
    METRICS_DIR,
    DATABASE_DIR,
    REPORTS_DIR
)
from database.db import DatabaseManager
from admin.resident_manager import ResidentManager
from admin.enrollment import BiometricEnrollmentService
from camera.webcam import WebcamStream
from access_control.decision_engine import AccessControlDecisionEngine
from access_control.event_logger import AccessEventLogger
from ui.components import (
    render_header,
    render_metric_card,
    render_decision_badge,
    render_gate_decision_banner
)
from evaluation.generate_report import generate_full_evaluation_report

# -------------------------------------------------------------
# 1. LIVE GATE MONITOR TAB
# -------------------------------------------------------------
def render_live_monitor_tab(
    db: DatabaseManager,
    res_mgr: ResidentManager,
    logger_svc: AccessEventLogger,
    decision_engine: AccessControlDecisionEngine,
    enrollment_svc: BiometricEnrollmentService,
    webcam: WebcamStream
):
    """Renders the Live Gate Security Monitor panel."""
    st.subheader("📹 Real-Time Security Gate Monitor")

    # Metrics Row
    stats = logger_svc.get_today_statistics()
    active_count = len(res_mgr.list_residents(active_only=True))

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        render_metric_card("Today Total Attempts", stats["total"], "#f8fafc")
    with m2:
        render_metric_card("Authorized (Allowed)", stats["allowed"], "#22c55e")
    with m3:
        render_metric_card("Rejected (Unknown)", stats["rejected"], "#ef4444")
    with m4:
        render_metric_card("Verification Pending", stats["verification"], "#f59e0b")
    with m5:
        render_metric_card("Active Residents", active_count, "#3b82f6")

    st.markdown("<br>", unsafe_allow_html=True)

    col_video, col_controls = st.columns([1.6, 1.0])

    with col_controls:
        st.markdown("#### ⚙️ Security Gate Controls")
        stream_mode = st.radio(
            "Video Input Source:",
            ["Laptop Webcam (Continuous)", "Browser Camera Snapshot", "Upload Test Frame / Incident Image"],
            index=0
        )

        st.markdown("---")
        st.markdown("#### 🚨 Manual Security Guard Override")
        st.caption("Review and override pending or uncertain access requests:")

        pending_logs = [l for l in logger_svc.get_recent_logs(limit=15) if l.verification_status == VerificationStatus.PENDING_REVIEW]

        if pending_logs:
            target_log = pending_logs[0]
            st.warning(f"Pending Review for: **{target_log.detected_name}** (#{target_log.log_id})")
            guard_notes = st.text_input("Security Guard Notes:", placeholder="Verified physical society ID badge")

            b_allow, b_reject = st.columns(2)
            with b_allow:
                if st.button("✔ Allow Entry (Override)", type="primary", use_container_width=True):
                    decision_engine.manual_guard_override(target_log.log_id, approve=True, notes=guard_notes)
                    st.success(f"Overridden: Access ALLOWED for {target_log.detected_name}")
                    st.rerun()
            with b_reject:
                if st.button("✖ Reject Entry", use_container_width=True):
                    decision_engine.manual_guard_override(target_log.log_id, approve=False, notes=guard_notes)
                    st.error(f"Overridden: Access REJECTED for {target_log.detected_name}")
                    st.rerun()
        else:
            st.info("No access events currently requiring manual review.")

    with col_video:
        if stream_mode == "Laptop Webcam (Continuous)":
            live_active = st.checkbox("🟢 Activate Continuous Video Stream", value=False)
            video_placeholder = st.empty()
            decision_placeholder = st.empty()

            if live_active:
                if not webcam.is_running:
                    webcam.start(allow_simulation_fallback=True)

                stop_btn = st.button("⏹ Stop Live Stream")
                while live_active and not stop_btn:
                    ret, frame = webcam.read_frame()
                    if not ret or frame is None:
                        st.error("Failed to read video frame.")
                        break

                    res = decision_engine.process_frame(frame)
                    rgb_frame = cv2.cvtColor(res.annotated_frame, cv2.COLOR_BGR2RGB)
                    video_placeholder.image(rgb_frame, channels="RGB", use_container_width=True)

                    if res.primary_decision:
                        sc = res.face_decisions[0].match.similarity_score if res.face_decisions else None
                        apt = res.face_decisions[0].match.apartment_number if res.face_decisions else None
                        with decision_placeholder:
                            render_gate_decision_banner(res.primary_decision, res.primary_name, apt, sc)
                    else:
                        with decision_placeholder:
                            render_gate_decision_banner(None, None)

                    time.sleep(0.04)
            else:
                if webcam.is_running:
                    webcam.stop()
                render_gate_decision_banner(None, None)
                st.info("Camera stream is on standby. Check 'Activate Continuous Video Stream' above to initiate real-time monitoring.")

        elif stream_mode == "Browser Camera Snapshot":
            cam_snap = st.camera_input("Capture Security Gate Verification Photo")
            if cam_snap is not None:
                pil_img = Image.open(cam_snap)
                frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

                res = decision_engine.process_frame(frame)
                sc = res.face_decisions[0].match.similarity_score if res.face_decisions else None
                apt = res.face_decisions[0].match.apartment_number if res.face_decisions else None
                render_gate_decision_banner(res.primary_decision, res.primary_name, apt, sc)

                rgb_annotated = cv2.cvtColor(res.annotated_frame, cv2.COLOR_BGR2RGB)
                st.image(rgb_annotated, channels="RGB", use_container_width=True)
                st.caption(f"Processed in {res.processing_time_ms} ms. Faces detected: {len(res.face_decisions)}")

        elif stream_mode == "Upload Test Frame / Incident Image":
            up_file = st.file_uploader("Upload gate camera snapshot (JPG/PNG):", type=["jpg", "jpeg", "png"])
            if up_file is not None:
                pil_img = Image.open(up_file)
                frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

                res = decision_engine.process_frame(frame)
                sc = res.face_decisions[0].match.similarity_score if res.face_decisions else None
                apt = res.face_decisions[0].match.apartment_number if res.face_decisions else None
                render_gate_decision_banner(res.primary_decision, res.primary_name, apt, sc)

                rgb_annotated = cv2.cvtColor(res.annotated_frame, cv2.COLOR_BGR2RGB)
                st.image(rgb_annotated, channels="RGB", use_container_width=True)
                st.caption(f"Processed in {res.processing_time_ms} ms. Faces detected: {len(res.face_decisions)}")

    st.markdown("---")
    st.markdown("#### 📋 Recent Gate Activity Feed")
    recent_logs = logger_svc.get_recent_logs(limit=8)
    if recent_logs:
        table_data = []
        for l in recent_logs:
            table_data.append({
                "Timestamp": l.timestamp,
                "Resident / Individual": l.detected_name,
                "Apartment": l.apartment_number or "—",
                "Similarity Score": f"{l.similarity_score:.3f}" if l.similarity_score is not None else "—",
                "Decision": l.decision.value,
                "Status": l.verification_status.value,
                "Reason": l.reason or ""
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
    else:
        st.caption("No gate activity recorded yet today.")

# -------------------------------------------------------------
# 2. RESIDENT MANAGEMENT TAB
# -------------------------------------------------------------
def render_residents_tab(
    res_mgr: ResidentManager,
    enrollment_svc: BiometricEnrollmentService,
    matcher
):
    """Renders the Resident Administration and Biometric Enrollment panel."""
    st.subheader("👥 Resident Management & Biometric Directory")

    all_residents = res_mgr.list_residents()
    st.caption(f"Total Enrolled Residents: **{len(all_residents)}** | Minimum target: 20 slots supported.")

    st.markdown(
        """
        <div class="privacy-notice">
            🔒 <strong>Biometric Privacy & Informed Consent Compliance</strong><br>
            Biometric facial templates are converted to 128-dimensional irreversible mathematical embeddings 
            and stored as encrypted binary blobs. Raw photographs are never permanently retained. 
            Voluntary consent is mandatory prior to biometric enrollment.
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.expander("➕ Register & Enroll New Resident", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            r_id = st.text_input("Resident ID *", placeholder="e.g., RES-121", key="new_r_id")
            r_name = st.text_input("Full Name *", placeholder="e.g., Ananya Sharma", key="new_r_name")
            r_apt = st.text_input("Apartment / Flat Number *", placeholder="e.g., Tower-B 704", key="new_r_apt")
        with c2:
            r_contact = st.text_input("Contact Phone Number (Optional)", placeholder="e.g., +91-9876543210", key="new_r_contact")
            r_notes = st.text_area("Administrative Notes", placeholder="Permanent resident, registered Nov 2026", key="new_r_notes")
            r_consent = st.checkbox("✔ Informed Biometric Consent Granted by Resident (Mandatory)", value=True, key="new_r_consent")

        st.markdown("##### 📸 Biometric Face Capture")
        enr_method = st.radio("Enrollment Capture Mode:", ["Browser Webcam Snapshot", "Upload Portrait Photo"], horizontal=True)

        enr_image = None
        if enr_method == "Browser Webcam Snapshot":
            cam_input = st.camera_input("Take Enrollment Portrait", key="enr_cam")
            if cam_input:
                pil_im = Image.open(cam_input)
                enr_image = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)
        else:
            up_photo = st.file_uploader("Upload clear frontal portrait:", type=["jpg", "png", "jpeg"], key="enr_file")
            if up_photo:
                pil_im = Image.open(up_photo)
                enr_image = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)

        # Quality Inspection Preview
        if enr_image is not None:
            val = enrollment_svc.validate_image_quality(enr_image)
            q1, q2 = st.columns([1, 1.2])
            with q1:
                # Show detected face overlay
                if val.face:
                    preview_annotated = FaceDetector.draw_face_annotations(
                        enr_image,
                        val.face,
                        color=(0, 220, 0),
                        label="FACE DETECTED"
                    )
                    st.image(cv2.cvtColor(preview_annotated, cv2.COLOR_BGR2RGB), channels="RGB", width=240)
                else:
                    st.image(cv2.cvtColor(enr_image, cv2.COLOR_BGR2RGB), channels="RGB", width=240)
            with q2:
                st.markdown("**Biometric Quality Inspection:**")
                if val.is_valid:
                    st.success("✔ Image quality passes biometric enrollment criteria.")
                else:
                    st.error(f"✖ Quality Rejected: {val.reason}")

                st.write(f"- Brightness: `{val.brightness:.1f}` (Permitted: 35 - 235)")
                st.write(f"- Focus Sharpness: `{val.sharpness:.1f}` (Permitted: >= 25)")
                if val.face:
                    st.write(f"- Face Dimensions: `{val.face.w}x{val.face.h}` px (Min: 60x60)")
                    st.write(f"- Detection Confidence: `{val.face.score:.2f}` (Min: 0.80)")

            if st.button("💾 Confirm & Save Resident Enrollment", type="primary", disabled=not val.is_valid):
                if not r_id or not r_name or not r_apt:
                    st.error("Please fill in Resident ID, Full Name, and Apartment number.")
                elif not r_consent:
                    st.error("Biometric enrollment cannot proceed without informed consent.")
                else:
                    try:
                        emb = enrollment_svc.recognizer.extract_embedding(enr_image, val.face)
                        res_mgr.register_resident(
                            resident_id=r_id,
                            full_name=r_name,
                            apartment_number=r_apt,
                            contact_number=r_contact,
                            embeddings=[emb],
                            consent_given=r_consent,
                            notes=r_notes
                        )
                        matcher.reload_templates()
                        st.success(f"Resident **{r_name}** ({r_id}) successfully registered!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Registration failed: {e}")

    # Search & Directory Table
    search_q = st.text_input("🔍 Search Directory (by Name, Apartment, or ID):", "")
    filtered_residents = res_mgr.list_residents(search_query=search_q if search_q else None)

    if filtered_residents:
        res_data = []
        for r in filtered_residents:
            res_data.append({
                "Resident ID": r.resident_id,
                "Full Name": r.full_name,
                "Apartment": r.apartment_number,
                "Phone": r.contact_number or "—",
                "Status": "ACTIVE" if r.is_active else "SUSPENDED",
                "Consent": "YES" if r.consent_given else "NO",
                "Templates": r.template_count,
                "Enrolled On": r.registration_date[:10]
            })
        st.dataframe(pd.DataFrame(res_data), use_container_width=True, hide_index=True)

        # Resident Detail & Actions Panel
        st.markdown("##### ⚙️ Resident Actions")
        selected_id = st.selectbox(
            "Select Resident to Edit / Deactivate / Delete:",
            [f"{r.resident_id} — {r.full_name} ({r.apartment_number})" for r in filtered_residents]
        )
        if selected_id:
            sel_rid = selected_id.split(" — ")[0]
            target_res = res_mgr.get_resident(sel_rid)
            if target_res:
                act_col1, act_col2, act_col3 = st.columns(3)
                with act_col1:
                    new_status = not target_res.is_active
                    btn_text = "Activate Resident" if not target_res.is_active else "Suspend / Deactivate"
                    if st.button(btn_text, key="toggle_status_btn"):
                        res_mgr.update_resident(sel_rid, is_active=new_status)
                        matcher.reload_templates()
                        st.success(f"Resident status updated to {'ACTIVE' if new_status else 'SUSPENDED'}")
                        st.rerun()
                with act_col2:
                    if st.button("🗑 Delete Resident & Biometrics", type="secondary", key="del_res_btn"):
                        res_mgr.delete_resident(sel_rid)
                        matcher.reload_templates()
                        st.warning(f"Resident {sel_rid} and biometric templates deleted.")
                        st.rerun()
                with act_col3:
                    st.caption(f"Biometric Templates Enrolled: **{target_res.template_count}**")
    else:
        st.info("No residents found matching the search criteria.")

# -------------------------------------------------------------
# 3. ACCESS HISTORY & AUDIT TRAIL TAB
# -------------------------------------------------------------
def render_audit_logs_tab(logger_svc: AccessEventLogger):
    """Renders the Access Logs and Historical Audit panel."""
    st.subheader("📜 Security Access Logs & Audit Trail")

    f1, f2, f3 = st.columns([1, 1, 1])
    with f1:
        decision_filter = st.selectbox("Filter by Decision:", ["ALL", "ENTRY ALLOWED", "ENTRY REJECTED", "VERIFICATION REQUIRED"])
    with f2:
        resident_id_filter = st.text_input("Filter by Resident ID:", placeholder="e.g. RES-101")
    with f3:
        max_rows = st.slider("Maximum records to display:", 20, 500, 100)

    logs = logger_svc.filter_logs(
        decision=decision_filter,
        resident_id=resident_id_filter if resident_id_filter else None,
        limit=max_rows
    )

    if logs:
        log_dicts = []
        for l in logs:
            log_dicts.append({
                "Log ID": l.log_id,
                "Timestamp": l.timestamp,
                "Resident ID": l.resident_id or "—",
                "Detected Name": l.detected_name,
                "Apartment": l.apartment_number or "—",
                "Similarity Score": f"{l.similarity_score:.3f}" if l.similarity_score is not None else "—",
                "Decision": l.decision.value,
                "Verification Status": l.verification_status.value,
                "Reason / Audit Notes": l.reason or ""
            })

        df = pd.DataFrame(log_dicts)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # CSV Download Button
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Audit Logs (CSV)",
            data=csv_data,
            file_name=f"smart_society_access_logs_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No access logs found matching the filter criteria.")

# -------------------------------------------------------------
# 4. SYSTEM & SECURITY SETTINGS TAB
# -------------------------------------------------------------
def render_settings_tab(
    db: DatabaseManager,
    matcher,
    decision_engine: AccessControlDecisionEngine
):
    """Renders the System Configuration and Security Thresholds panel."""
    st.subheader("⚙️ System Configuration & Security Thresholds")

    cur_high = float(db.get_setting("recognition_threshold_high", "0.363"))
    cur_low = float(db.get_setting("recognition_threshold_low", "0.280"))
    cur_cooldown = float(db.get_setting("cooldown_seconds", "8.0"))
    cur_society = db.get_setting("society_name", "Greenfield Heights Residential Society")

    st.markdown("##### 🎯 Biometric Matching Threshold Calibration")
    st.caption(
        "OpenCV SFace produces normalized 128-d embeddings. "
        "Standard genuine match threshold is **0.363**. "
        "Scores below the low threshold are strictly treated as **UNKNOWN PERSON**."
    )

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        new_high = st.slider(
            "High Security Threshold (ENTRY ALLOWED)",
            min_value=0.25,
            max_value=0.55,
            value=cur_high,
            step=0.01,
            help="Minimum cosine similarity required for automatic green entry authorization."
        )
    with col_t2:
        new_low = st.slider(
            "Low Boundary Threshold (VERIFICATION REQUIRED)",
            min_value=0.15,
            max_value=0.35,
            value=cur_low,
            step=0.01,
            help="Borderline zone between this and High Threshold mandates security guard review."
        )

    if new_low >= new_high:
        st.error("Low boundary threshold must be strictly less than High Security threshold!")

    st.markdown("##### ⏱ Deduplication Cooldown Window")
    new_cooldown = st.slider(
        "Entry-Event Deduplication Window (Seconds)",
        min_value=2.0,
        max_value=30.0,
        value=cur_cooldown,
        step=1.0,
        help="Prevents repeated logging of the same resident while continuously visible at the camera gate."
    )

    st.markdown("##### 🏢 Residential Society Information")
    new_society = st.text_input("Residential Society Name:", value=cur_society)

    if st.button("💾 Apply & Persist Settings", type="primary"):
        matcher.update_policy(new_high, new_low)
        decision_engine.set_cooldown(new_cooldown)
        db.set_setting("cooldown_seconds", f"{new_cooldown:.1f}")
        db.set_setting("society_name", new_society)
        st.success("System configuration updated and persisted to SQLite.")
        st.rerun()

    st.markdown("---")
    st.markdown("##### 🗄 Database Maintenance & Administrative Export")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("📦 Create Database Backup (.db)", use_container_width=True):
            backup_file = DATABASE_DIR / f"smart_society_backup_{time.strftime('%Y%m%d_%H%M%S')}.db"
            db.backup(backup_file)
            st.success(f"Atomic SQLite backup created: `{backup_file.name}`")
    with b2:
        if st.button("📄 Export Administrative Summary (JSON)", use_container_width=True):
            export_file = REPORTS_DIR / f"admin_summary_{time.strftime('%Y%m%d_%H%M%S')}.json"
            db.export_summary_json(export_file)
            st.success(f"Administrative summary exported to `{export_file.name}`")

# -------------------------------------------------------------
# 5. ACADEMIC EVALUATION & ANALYTICS TAB
# -------------------------------------------------------------
def render_evaluation_tab():
    """Renders the Academic Evaluation, Metrics, and Performance Visualizations panel."""
    st.subheader("📊 Recognition Accuracy & Experimental Evaluation")

    summary_file = METRICS_DIR / "summary_metrics.json"

    if st.button("🔄 Execute Fresh Benchmark Evaluation", type="primary"):
        with st.spinner("Running 180-trial evaluation across 20 enrolled identities and impostor probes..."):
            generate_full_evaluation_report()
            st.success("Benchmark completed and evaluation figures updated!")
            st.rerun()

    if summary_file.exists():
        with open(summary_file, "r") as f:
            summary = json.load(f)

        # Metric summary cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card("ROC AUC", f"{summary['roc_auc']:.4f}", "#3b82f6")
        with c2:
            render_metric_card("Precision", f"{summary['operating_precision']*100:.1f}%", "#22c55e")
        with c3:
            render_metric_card("False Acceptance (FAR)", f"{summary['operating_far']*100:.2f}%", "#22c55e" if summary['operating_far'] == 0 else "#ef4444")
        with c4:
            render_metric_card("Equal Error Rate (EER)", f"{summary['eer_value']*100:.2f}%", "#f59e0b")

        st.markdown("<br>", unsafe_allow_html=True)

        # Visualizations in 2x2 grid
        st.markdown("#### 📈 Performance Charts & Error Analysis")
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            far_frr_img = FIGURES_DIR / "far_frr_curve.png"
            if far_frr_img.exists():
                st.image(str(far_frr_img), caption="Figure 1: FAR vs. FRR Trade-off Curve", use_container_width=True)

        with row1_col2:
            roc_img = FIGURES_DIR / "roc_curve.png"
            if roc_img.exists():
                st.image(str(roc_img), caption="Figure 2: Receiver Operating Characteristic (ROC)", use_container_width=True)

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            cm_img = FIGURES_DIR / "confusion_matrix.png"
            if cm_img.exists():
                st.image(str(cm_img), caption=f"Figure 3: Confusion Matrix (Threshold = {summary.get('recommended_threshold', 0.363)})", use_container_width=True)

        with row2_col2:
            dist_img = FIGURES_DIR / "score_distribution.png"
            if dist_img.exists():
                st.image(str(dist_img), caption="Figure 4: Genuine vs Impostor Score Distributions", use_container_width=True)

        # Condition breakdown table
        st.markdown("#### 🔬 Robustness Across Environmental Conditions")
        cond_csv = METRICS_DIR / "condition_breakdown.csv"
        if cond_csv.exists():
            st.dataframe(pd.read_csv(cond_csv), use_container_width=True, hide_index=True)

        # Threshold Sweep Table
        with st.expander("🔍 View Complete Threshold Sweep Experiment Data"):
            sweep_csv = METRICS_DIR / "threshold_sweep.csv"
            if sweep_csv.exists():
                st.dataframe(pd.read_csv(sweep_csv), use_container_width=True, hide_index=True)
    else:
        st.info("No evaluation results generated yet. Click 'Execute Fresh Benchmark Evaluation' above.")

