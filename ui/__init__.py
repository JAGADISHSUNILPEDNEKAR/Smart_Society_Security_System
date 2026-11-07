"""UI package for Smart Society Security System."""
from ui.styles import get_custom_css
from ui.components import (
    render_header,
    render_metric_card,
    render_decision_badge,
    render_gate_decision_banner
)
from ui.dashboard import (
    render_live_monitor_tab,
    render_residents_tab,
    render_audit_logs_tab,
    render_settings_tab,
    render_evaluation_tab
)

__all__ = [
    "get_custom_css",
    "render_header",
    "render_metric_card",
    "render_decision_badge",
    "render_gate_decision_banner",
    "render_live_monitor_tab",
    "render_residents_tab",
    "render_audit_logs_tab",
    "render_settings_tab",
    "render_evaluation_tab"
]

