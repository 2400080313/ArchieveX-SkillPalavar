"""
ArchiveX - Archive Recommendations & Actionable Insights View
"""
import streamlit as st
import pandas as pd
from config import S3_PRICING

def render_recommendations(data: dict):
    st.subheader("🎯 Archive Intelligence & Tier Recommendations")
    st.caption("Context-aware recommendations driven by object inactivity age, payload size thresholds, and semantics.")

    df: pd.DataFrame = data["dataframe"]
    if df.empty or "Recommendation" not in df.columns:
        st.warning("No recommendation data calculated.")
        return

    rec_groups = df.groupby("Recommendation")

    # High-level summary tabs
    rec_types = [
        ("DEEP_ARCHIVE", "❄️ Glacier Deep Archive", "#ef4444", "Lowest cost storage ($0.00099/GB-mo). Ideal for compliance & backups > 180 days with rare retrieval (12-48h)."),
        ("GLACIER_FLEXIBLE", "🧊 Glacier Flexible Retrieval", "#f97316", "Low cost archive ($0.0036/GB-mo). Bulk retrievals are completely free. Ideal for data > 90 days."),
        ("INTELLIGENT_TIERING", "🧠 S3 Intelligent-Tiering", "#8b5cf6", "Zero retrieval fees and automatic tiering. Perfect for variable access patterns on objects >= 128 KB."),
        ("STANDARD_IA", "⚡ S3 Standard-IA", "#10b981", "Lower storage cost ($0.0125/GB-mo) with millisecond access. Ideal for data > 30 days accessed monthly."),
        ("KEEP_STANDARD", "🛡️ Keep in S3 Standard", "#3b82f6", "Fresh objects (<30d) or small objects (<128KB) where transition fees negate storage savings.")
    ]

    for rec_key, title, color, desc in rec_types:
        subset = df[df["Recommendation"] == rec_key]
        count = len(subset)
        total_size_gb = (subset["Size"].sum() / (1024**3)) if count > 0 else 0.0

        # Estimate savings
        if rec_key == "DEEP_ARCHIVE":
            savings_mo = total_size_gb * (S3_PRICING["STANDARD"]["storage_per_gb_month"] - S3_PRICING["DEEP_ARCHIVE"]["storage_per_gb_month"])
        elif rec_key == "GLACIER_FLEXIBLE":
            savings_mo = total_size_gb * (S3_PRICING["STANDARD"]["storage_per_gb_month"] - S3_PRICING["GLACIER"]["storage_per_gb_month"])
        elif rec_key == "INTELLIGENT_TIERING":
            savings_mo = total_size_gb * (S3_PRICING["STANDARD"]["storage_per_gb_month"] - S3_PRICING["INTELLIGENT_TIERING"]["avg_blended_rate"])
        elif rec_key == "STANDARD_IA":
            savings_mo = total_size_gb * (S3_PRICING["STANDARD"]["storage_per_gb_month"] - S3_PRICING["STANDARD_IA"]["storage_per_gb_month"])
        else:
            savings_mo = 0.0

        with st.expander(f"{title} ({count:,} objects • {total_size_gb:.2f} GB • Est. Mo. Savings: ${savings_mo:,.2f})", expanded=(rec_key == "DEEP_ARCHIVE" and count > 0)):
            st.markdown(f"**Tier Overview:** {desc}")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Objects in Group", f"{count:,}")
            with c2:
                st.metric("Volume (GB)", f"{total_size_gb:,.2f} GB")
            with c3:
                st.metric("Monthly Net Savings", f"${savings_mo:,.2f}")
            with c4:
                st.metric("Annual Run-Rate Savings", f"${savings_mo * 12:,.2f}")

            if count > 0:
                st.markdown("##### Candidate Object Sample")
                sample_df = subset[["Key", "Size", "AgeDays", "StorageClass", "ArchiveScore"]].head(10).copy()
                sample_df["SizeMB"] = (sample_df["Size"] / (1024 * 1024)).round(2)
                st.dataframe(
                    sample_df[["Key", "SizeMB", "AgeDays", "StorageClass", "ArchiveScore"]].rename(columns={
                        "SizeMB": "Size (MB)",
                        "AgeDays": "Age (Days)",
                        "StorageClass": "Current Class",
                        "ArchiveScore": "Readiness Score"
                    }),
                    use_container_width=True
                )
