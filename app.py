"""
ArchiveX - Intelligent Amazon S3 Archive & Lifecycle Decision Support Platform
Main Streamlit Application Entrypoint
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone

from config import APP_NAME, APP_TAGLINE, APP_VERSION, S3_PRICING
from core.demo_data import DEMO_BUCKETS, generate_bucket_objects, get_demo_dataset
from core.scoring import calculate_archive_score
from core.cost_engine import summarize_bucket_cost_profile
from core.aws_client import S3ClientManager

from ui.styles import CUSTOM_CSS
from ui.dashboard_view import render_dashboard
from ui.explorer_view import render_explorer
from ui.recommendations_view import render_recommendations
from ui.simulator_view import render_simulator
from ui.lifecycle_view import render_lifecycle_builder
from ui.it_view import render_intelligent_tiering
from ui.copilot_view import render_copilot_interface
from ui.settings_view import render_settings

# Page Configuration
st.set_page_config(
    page_title=f"{APP_NAME} | AWS S3 Storage Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Custom Theme CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize Session State
if "is_demo_mode" not in st.session_state:
    st.session_state["is_demo_mode"] = True

if "selected_bucket" not in st.session_state:
    st.session_state["selected_bucket"] = DEMO_BUCKETS[0]["name"]

# Sidebar Navigation & Context Controls
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 10px 0;">
        <h2 style="margin:0; font-size: 1.8rem; font-weight:800; color: #f8fafc; letter-spacing: -0.02em;">
            📦 {APP_NAME}
        </h2>
        <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 500; margin-top:2px;">
            {APP_TAGLINE}
        </div>
        <div style="margin-top: 10px;">
            {'<span class="archivex-badge-demo">Demo Mode Active</span>' if st.session_state["is_demo_mode"] else '<span class="archivex-badge-live">Live AWS Mode</span>'}
            <span style="color:#64748b; font-size:0.75rem; margin-left:6px;">v{APP_VERSION}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Bucket Selector
    if st.session_state["is_demo_mode"]:
        bucket_names = [b["name"] for b in DEMO_BUCKETS]
        curr_b = st.session_state["selected_bucket"]
        idx = bucket_names.index(curr_b) if curr_b in bucket_names else 0
        selected_b = st.selectbox("Active Bucket", options=bucket_names, index=idx)
        if selected_b != curr_b:
            st.session_state["selected_bucket"] = selected_b
            st.rerun()
    else:
        st.markdown("**Live AWS Target Bucket:**")
        st.session_state["selected_bucket"] = st.text_input("Bucket Name", value=st.session_state.get("selected_bucket", "my-production-s3-bucket"))

    # Navigation Menu
    st.markdown("### Navigation")
    menu_options = [
        "📊 Executive Dashboard",
        "🔍 Bucket Explorer",
        "🎯 Archive Recommendations",
        "💰 Cost & ROI Simulator",
        "⚙️ S3 Lifecycle Builder",
        "🧠 S3 Intelligent-Tiering",
        "💬 ArchiveX Copilot",
        "🔧 Settings & AWS Setup"
    ]
    
    current_nav = st.radio("Go to:", options=menu_options, label_visibility="collapsed")

    st.markdown("---")

    # AWS Storage Class Quick Rates
    with st.expander("🏷️ AWS S3 Pricing Reference (us-east-1)", expanded=False):
        for k, v in S3_PRICING.items():
            st.markdown(f"• **{v['name']}**: `${v['storage_per_gb_month']:.4f}`/GB-mo")

    st.caption("AWS Storage Hackathon Edition • Decision-Support Layer")

# Data Loading & Enrichment Pipeline
@st.cache_data(show_spinner=False)
def load_and_score_bucket_data(bucket_name: str, is_demo: bool, aws_creds: dict = None) -> dict:
    """Loads objects and runs archive readiness scoring engine."""
    if is_demo:
        objects = generate_bucket_objects(bucket_name, count=250)
    else:
        # Live AWS S3
        client = S3ClientManager(
            aws_access_key=aws_creds.get("access_key") if aws_creds else None,
            aws_secret_key=aws_creds.get("secret_key") if aws_creds else None,
            aws_session_token=aws_creds.get("session_token") if aws_creds else None,
            region_name=aws_creds.get("region") if aws_creds else "us-east-1"
        )
        try:
            objects = client.list_objects(bucket_name, max_keys=1000)
            now = datetime.now(timezone.utc)
            for o in objects:
                # Add calculated age in days
                if "LastModified_dt" in o:
                    dt = o["LastModified_dt"]
                    o["AgeDays"] = max(0, (now - dt).days)
                else:
                    o["AgeDays"] = 30
        except Exception as e:
            objects = []

    # Score objects
    for obj in objects:
        score_res = calculate_archive_score(obj)
        obj["ArchiveScore"] = score_res["score"]
        obj["Recommendation"] = score_res["recommendation"]
        obj["Urgency"] = score_res["urgency"]
        obj["Rationale"] = score_res["rationale"]

    df = pd.DataFrame(objects)
    cost_summary = summarize_bucket_cost_profile(df)

    return {
        "current_bucket": bucket_name,
        "is_demo_mode": is_demo,
        "objects": objects,
        "dataframe": df,
        "cost_summary": cost_summary
    }

# Load Data
with st.spinner("Analyzing bucket storage patterns and scoring archive readiness..."):
    creds = {
        "access_key": st.session_state.get("aws_access_key"),
        "secret_key": st.session_state.get("aws_secret_key"),
        "session_token": st.session_state.get("aws_session_token"),
        "region": st.session_state.get("aws_region", "us-east-1")
    }
    app_data = load_and_score_bucket_data(
        st.session_state["selected_bucket"],
        st.session_state["is_demo_mode"],
        creds
    )

    # Attach live AWS client instance if configured
    if not st.session_state["is_demo_mode"]:
        app_data["aws_client"] = S3ClientManager(
            aws_access_key=creds["access_key"],
            aws_secret_key=creds["secret_key"],
            aws_session_token=creds["session_token"],
            region_name=creds["region"]
        )

# Render Selected View
try:
    if "Executive Dashboard" in current_nav:
        render_dashboard(app_data)
    elif "Bucket Explorer" in current_nav:
        render_explorer(app_data)
    elif "Archive Recommendations" in current_nav:
        render_recommendations(app_data)
    elif "Cost & ROI Simulator" in current_nav:
        render_simulator(app_data)
    elif "S3 Lifecycle Builder" in current_nav:
        render_lifecycle_builder(app_data)
    elif "S3 Intelligent-Tiering" in current_nav:
        render_intelligent_tiering(app_data)
    elif "ArchiveX Copilot" in current_nav:
        render_copilot_interface(app_data)
    elif "Settings & AWS Setup" in current_nav:
        render_settings(app_data)
except Exception as e:
    st.error(f"An unexpected error occurred while rendering the page: {str(e)}")
    st.exception(e)
