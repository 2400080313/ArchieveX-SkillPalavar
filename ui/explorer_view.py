"""
ArchiveX - Bucket Explorer View
Interactive object browser, multi-facet search, granular filters, and object metadata inspection.
"""
import streamlit as st
import pandas as pd
from ui.components import get_storage_class_badge, get_recommendation_badge, get_score_badge
from core.copilot import ArchiveCopilot

def render_explorer(data: dict):
    st.subheader("🔍 Amazon S3 Bucket Explorer & Inspector")
    st.caption("Deep-dive into S3 object keys, metadata tags, storage classes, and individual archive readiness scores.")

    df: pd.DataFrame = data["dataframe"]
    if df.empty:
        st.warning("No object metadata loaded.")
        return

    # Filter & Search Controls Row
    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
    with f_col1:
        search_query = st.text_input("Search Object Keys or Prefixes", placeholder="e.g. backup, .parquet, 2024, audit...")
    with f_col2:
        classes = sorted(df["StorageClass"].unique().tolist())
        selected_classes = st.multiselect("Storage Class Filter", options=classes, default=classes)
    with f_col3:
        recs = sorted(df["Recommendation"].unique().tolist()) if "Recommendation" in df.columns else []
        selected_recs = st.multiselect("Recommendation Filter", options=recs, default=recs)

    # Secondary Filter Row
    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        min_age, max_age = int(df["AgeDays"].min()), int(df["AgeDays"].max())
        age_range = st.slider("Object Inactivity Age (Days)", min_value=min_age, max_value=max(max_age, 30), value=(min_age, max_age))
    with s_col2:
        score_range = st.slider("Archive Readiness Score Filter", min_value=0, max_value=100, value=(0, 100))
    with s_col3:
        size_filter = st.selectbox(
            "Payload Size Filter",
            options=["All Sizes", "Small Objects (< 128 KB)", "Medium (128 KB - 100 MB)", "Large (> 100 MB)", "Very Large (> 1 GB)"]
        )

    # Apply Filtering
    filtered_df = df.copy()

    if search_query:
        q = search_query.strip().lower()
        filtered_df = filtered_df[filtered_df["Key"].str.lower().str.contains(q)]

    if selected_classes:
        filtered_df = filtered_df[filtered_df["StorageClass"].isin(selected_classes)]

    if selected_recs and "Recommendation" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Recommendation"].isin(selected_recs)]

    filtered_df = filtered_df[
        (filtered_df["AgeDays"] >= age_range[0]) & 
        (filtered_df["AgeDays"] <= age_range[1])
    ]

    if "ArchiveScore" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["ArchiveScore"] >= score_range[0]) & 
            (filtered_df["ArchiveScore"] <= score_range[1])
        ]

    if size_filter == "Small Objects (< 128 KB)":
        filtered_df = filtered_df[filtered_df["Size"] < 131072]
    elif size_filter == "Medium (128 KB - 100 MB)":
        filtered_df = filtered_df[(filtered_df["Size"] >= 131072) & (filtered_df["Size"] <= 100 * 1024 * 1024)]
    elif size_filter == "Large (> 100 MB)":
        filtered_df = filtered_df[filtered_df["Size"] > 100 * 1024 * 1024]
    elif size_filter == "Very Large (> 1 GB)":
        filtered_df = filtered_df[filtered_df["Size"] > 1024 * 1024 * 1024]

    st.markdown(f"**Found {len(filtered_df):,} matching objects** (Total filtered volume: {(filtered_df['Size'].sum() / (1024**3)):.2f} GB)")

    # Data Table View
    display_df = filtered_df.copy()
    display_df["SizeMB"] = (display_df["Size"] / (1024 * 1024)).round(2)
    display_df["FormattedSize"] = display_df["SizeMB"].apply(lambda mb: f"{mb/1024:.2f} GB" if mb >= 1024 else f"{mb:.2f} MB" if mb >= 0.1 else f"{mb*1024:.1f} KB")
    
    cols_to_show = ["Key", "FormattedSize", "StorageClass", "AgeDays", "ArchiveScore", "Recommendation", "Urgency"]
    valid_cols = [c for c in cols_to_show if c in display_df.columns]
    
    st.dataframe(
        display_df[valid_cols].rename(columns={
            "FormattedSize": "Size",
            "StorageClass": "Storage Class",
            "AgeDays": "Age (Days)",
            "ArchiveScore": "Score",
            "Recommendation": "Recommended Target"
        }),
        use_container_width=True,
        height=320
    )

    # Object Inspection Panel
    st.markdown("---")
    st.subheader("🔬 Deep Object Metadata & Rationale Inspector")
    
    if not filtered_df.empty:
        selected_key = st.selectbox("Select an object to inspect:", options=filtered_df["Key"].tolist()[:100])
        obj_row = filtered_df[filtered_df["Key"] == selected_key].iloc[0]
        
        ins_col1, ins_col2 = st.columns([1, 1])
        with ins_col1:
            st.markdown(f"**Object Key:** `{obj_row['Key']}`")
            st.markdown(f"**Bucket:** `{obj_row.get('BucketName', 'N/A')}`")
            st.markdown(f"**Size:** {obj_row['FormattedSize']} ({obj_row['Size']:,} bytes)")
            st.markdown(f"**Current Storage Class:** `{obj_row['StorageClass']}`")
            st.markdown(f"**Age:** {obj_row['AgeDays']} days (Last Modified: {obj_row['LastModified']})")
            st.markdown(f"**Tags:** `{obj_row.get('Tags', {})}`")

        with ins_col2:
            st.markdown(f"**Archive Readiness Score:** `{obj_row.get('ArchiveScore', 0):.0f} / 100`")
            st.markdown(f"**Recommended Storage Class:** `{obj_row.get('Recommendation', 'KEEP_STANDARD')}`")
            st.markdown(f"**Urgency:** `{obj_row.get('Urgency', 'INFO')}`")
            st.info(f"**Architectural Rationale:**\n{obj_row.get('Rationale', 'No rationale available.')}")

        # Quick Copilot Explanation button
        copilot = ArchiveCopilot()
        explanation = copilot.explain_object_recommendation(
            obj=obj_row.to_dict(),
            score_info={
                "recommendation": obj_row.get("Recommendation"),
                "score": obj_row.get("ArchiveScore")
            }
        )
        st.markdown(f"""
        <div class="chat-bot-bubble">
            <strong>🤖 {copilot.engine_mode} Analysis:</strong><br>
            "{explanation}"
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Adjust filters to display objects for inspection.")
