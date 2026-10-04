"""
ArchiveX - Reusable UI Components
"""
import streamlit as st
from config import S3_PRICING

def render_kpi_card(label: str, value: str, subtext: str = "", delta_color: str = "normal"):
    """Renders a styled KPI metric card."""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {f'<div class="kpi-subtext">{subtext}</div>' if subtext else ''}
    </div>
    """, unsafe_allow_html=True)

def get_storage_class_badge(storage_class: str) -> str:
    """Returns a styled HTML badge for an S3 storage class."""
    config = S3_PRICING.get(storage_class, S3_PRICING["STANDARD"])
    color = config.get("color", "#3b82f6")
    name = config.get("name", storage_class)
    return f"""<span style="background:{color}22; color:{color}; border:1px solid {color}88; padding:3px 8px; border-radius:6px; font-weight:600; font-size:0.75rem;">{name}</span>"""

def get_recommendation_badge(recommendation: str) -> str:
    """Returns a styled HTML badge for tier recommendations."""
    mapping = {
        "DEEP_ARCHIVE": ("#ef4444", "Glacier Deep Archive"),
        "GLACIER_FLEXIBLE": ("#f97316", "Glacier Flexible"),
        "GLACIER_IR": ("#f59e0b", "Glacier Instant"),
        "INTELLIGENT_TIERING": ("#8b5cf6", "Intelligent-Tiering"),
        "STANDARD_IA": ("#10b981", "Standard-IA"),
        "KEEP_STANDARD": ("#3b82f6", "Keep in Standard"),
        "OPTIMIZED": ("#64748b", "Already Optimized")
    }
    color, label = mapping.get(recommendation, ("#6b7280", recommendation))
    return f"""<span style="background:{color}20; color:{color}; border:1px solid {color}; padding:3px 8px; border-radius:6px; font-weight:600; font-size:0.75rem;">{label}</span>"""

def get_score_badge(score: float) -> str:
    """Returns a colored badge for an Archive Readiness Score (0-100)."""
    if score >= 80:
        color = "#ef4444" # Hot archive candidate
        label = "High Priority"
    elif score >= 50:
        color = "#f59e0b"
        label = "Medium"
    else:
        color = "#3b82f6"
        label = "Low"
    return f"""<span style="background:{color}22; color:{color}; border:1px solid {color}; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.75rem;">{score:.0f}/100 • {label}</span>"""
