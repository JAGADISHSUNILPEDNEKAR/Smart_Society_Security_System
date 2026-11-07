"""
UI Styling and Custom CSS for Smart Society Security System.
Provides a modern, high-contrast Security Operations Center (SOC) theme.
"""

def get_custom_css() -> str:
    """Returns CSS styles for Streamlit."""
    return """
    <style>
    /* Global font and background enhancements */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Header styling */
    .soc-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 1.2rem 1.6rem;
        border-radius: 10px;
        border-left: 5px solid #3b82f6;
        margin-bottom: 1.5rem;
        color: white;
    }
    .soc-header h1 {
        font-size: 1.7rem;
        font-weight: 700;
        margin: 0;
        color: #f8fafc;
    }
    .soc-header p {
        font-size: 0.9rem;
        color: #94a3b8;
        margin: 0.3rem 0 0 0;
    }

    /* Status Badges */
    .badge-allowed {
        background-color: rgba(34, 197, 94, 0.15);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.4);
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-rejected {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-verification {
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }

    /* Metric Cards */
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-card .title {
        font-size: 0.8rem;
        text-transform: uppercase;
        color: #94a3b8;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    .metric-card .value {
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 0.3rem;
        color: #f8fafc;
    }

    /* Big Gate Decision Banner */
    .gate-decision-box {
        padding: 1.2rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
        font-size: 1.3rem;
        letter-spacing: 0.05em;
    }
    .gate-allowed {
        background-color: rgba(34, 197, 94, 0.2);
        border: 2px solid #22c55e;
        color: #4ade80;
    }
    .gate-rejected {
        background-color: rgba(239, 68, 68, 0.2);
        border: 2px solid #ef4444;
        color: #f87171;
    }
    .gate-verification {
        background-color: rgba(245, 158, 11, 0.2);
        border: 2px solid #f59e0b;
        color: #fbbf24;
    }
    .gate-idle {
        background-color: rgba(100, 116, 139, 0.2);
        border: 1px solid #475569;
        color: #cbd5e1;
    }

    /* Privacy Alert Notice */
    .privacy-notice {
        background-color: rgba(59, 130, 246, 0.1);
        border-left: 4px solid #3b82f6;
        padding: 0.8rem 1rem;
        border-radius: 4px;
        font-size: 0.85rem;
        color: #bfdbfe;
        margin-bottom: 1rem;
    }
    </style>
    """

