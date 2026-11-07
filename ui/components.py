"""
UI Components and Visual Formatters for Smart Society Security System.
Renders metric cards, status badges, alert banners, and camera controls.
"""

import streamlit as st
from config.settings import DecisionState, VerificationStatus

def render_header(society_name: str, subtitle: str = "AI-Powered Face Recognition & Biometric Access Control"):
    """Renders the top SOC header banner."""
    st.markdown(
        f"""
        <div class="soc-header">
            <h1>🛡️ {society_name}</h1>
            <p>{subtitle} | Operational Terminal</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_metric_card(title: str, value: int | str, color_hex: str = "#f8fafc"):
    """Renders an individual statistics card."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="title">{title}</div>
            <div class="value" style="color: {color_hex};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_decision_badge(decision: DecisionState | str) -> str:
    """Returns HTML for an inline decision status badge."""
    val = decision.value if isinstance(decision, DecisionState) else str(decision)
    if val == DecisionState.ALLOWED.value:
        return f'<span class="badge-allowed">✔ {val}</span>'
    elif val == DecisionState.VERIFICATION_REQUIRED.value:
        return f'<span class="badge-verification">⚠ {val}</span>'
    else:
        return f'<span class="badge-rejected">✖ {val}</span>'

def render_gate_decision_banner(
    decision: DecisionState | None,
    name: str | None,
    apt: str | None = None,
    score: float | None = None
):
    """Renders prominent top gate visual decision box."""
    if decision is None:
        st.markdown(
            """
            <div class="gate-decision-box gate-idle">
                👁 GATE STANDBY — MONITORING PASSAGEWAY
            </div>
            """,
            unsafe_allow_html=True
        )
    elif decision == DecisionState.ALLOWED:
        info = f": {name.upper()}" if name else ""
        sub = f" (Apartment {apt})" if apt else ""
        sc = f" [Score: {score:.2f}]" if score is not None else ""
        st.markdown(
            f"""
            <div class="gate-decision-box gate-allowed">
                ✔ ENTRY ALLOWED{info}{sub}{sc}
            </div>
            """,
            unsafe_allow_html=True
        )
    elif decision == DecisionState.VERIFICATION_REQUIRED:
        info = f": {name.upper()}" if name else ""
        sc = f" [Score: {score:.2f}]" if score is not None else ""
        st.markdown(
            f"""
            <div class="gate-decision-box gate-verification">
                ⚠ VERIFICATION REQUIRED{info}{sc} — MANUAL REVIEW MANDATED
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        info = f": {name.upper()}" if name else ""
        sc = f" [Score: {score:.2f}]" if score is not None else ""
        st.markdown(
            f"""
            <div class="gate-decision-box gate-rejected">
                ✖ ENTRY REJECTED{info}{sc} — UNAUTHORIZED ACCESS ATTEMPT
            </div>
            """,
            unsafe_allow_html=True
        )

