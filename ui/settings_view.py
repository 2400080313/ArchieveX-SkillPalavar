"""
ArchiveX - Settings & AWS Configuration View
Manages authentication credentials, demo mode toggles, bucket targets, and safety guardrails.
"""
import streamlit as st
import os
from core.aws_client import S3ClientManager
from core.demo_data import DEMO_BUCKETS

def render_settings(data: dict):
    st.subheader("⚙️ Settings & AWS Configuration")
    st.caption("Manage authentication, switch between Demo Mode and Live AWS S3, and verify connectivity.")

    # Mode Selector
    st.markdown("#### Operational Mode")
    current_is_demo = st.session_state.get("is_demo_mode", True)
    new_is_demo = st.toggle("Enable Demo Mode (No AWS credentials required)", value=current_is_demo)
    if new_is_demo != current_is_demo:
        st.session_state["is_demo_mode"] = new_is_demo
        st.rerun()

    if new_is_demo:
        st.info("💡 **Demo Mode is ACTIVE:** ArchiveX is running on synthetic enterprise datasets (backups, logs, media, iot). No AWS charges will be incurred.")
        st.markdown("##### Select Demo Bucket Profile")
        b_names = [b["name"] for b in DEMO_BUCKETS]
        curr_b = st.session_state.get("selected_bucket", b_names[0])
        idx = b_names.index(curr_b) if curr_b in b_names else 0
        selected = st.selectbox("Active Enterprise Demo Bucket", options=b_names, index=idx)
        if selected != curr_b:
            st.session_state["selected_bucket"] = selected
            st.rerun()

        # Display selected bucket metadata
        b_info = next(b for b in DEMO_BUCKETS if b["name"] == selected)
        st.markdown(f"""
        - **Description:** {b_info['description']}
        - **Workload Type:** `{b_info['primary_type']}`
        - **Environment:** `{b_info['environment']}`
        - **Data Custodian:** `{b_info['owner']}`
        """)

    else:
        st.warning("⚠️ **Live AWS Mode is ACTIVE:** ArchiveX will connect to your real AWS S3 environment.")
        st.markdown("##### AWS Credentials & Region")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            access_key = st.text_input("AWS Access Key ID", value=os.getenv("AWS_ACCESS_KEY_ID", ""), type="password")
            secret_key = st.text_input("AWS Secret Access Key", value=os.getenv("AWS_SECRET_ACCESS_KEY", ""), type="password")
        with col_c2:
            session_token = st.text_input("AWS Session Token (Optional for IAM Roles/SSO)", value=os.getenv("AWS_SESSION_TOKEN", ""), type="password")
            region = st.selectbox("AWS Region", options=["us-east-1", "us-east-2", "us-west-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-1", "ap-northeast-1"], index=0)

        # Connection Test Button
        if st.button("🔌 Test AWS Connection", type="primary"):
            with st.spinner("Connecting to AWS STS & S3..."):
                client = S3ClientManager(
                    aws_access_key=access_key or None,
                    aws_secret_key=secret_key or None,
                    aws_session_token=session_token or None,
                    region_name=region
                )
                test_res = client.test_connection()
                if test_res.get("success"):
                    st.success(f"Connected to AWS Account `{test_res.get('account')}`! (ARN: `{test_res.get('arn')}`)")
                    # Save to session
                    st.session_state["aws_access_key"] = access_key
                    st.session_state["aws_secret_key"] = secret_key
                    st.session_state["aws_session_token"] = session_token
                    st.session_state["aws_region"] = region
                else:
                    st.error(f"Connection Failed: {test_res.get('message')}")

    st.markdown("---")
    st.markdown("#### Optional LLM Copilot Configuration")
    st.caption("Provide an API key to augment ArchiveX Copilot. If omitted, ArchiveX transparently uses the deterministic Rule-based Archive Assistant.")
    
    col_llm1, col_llm2 = st.columns(2)
    with col_llm1:
        gemini_key = st.text_input("Google Gemini API Key (Optional)", value=os.getenv("GEMINI_API_KEY", ""), type="password")
    with col_llm2:
        openai_key = st.text_input("OpenAI API Key (Optional)", value=os.getenv("OPENAI_API_KEY", ""), type="password")

    if st.button("Save AI Settings"):
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
        st.success("AI Configuration updated successfully.")
