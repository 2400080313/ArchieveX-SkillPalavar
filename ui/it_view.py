"""
ArchiveX - S3 Intelligent-Tiering Deep-Dive View
Evaluates suitability, small-object guardrails, monitoring fees, and multi-tier movement.
"""
import streamlit as st
import plotly.express as px
import pandas as pd
from core.intelligent_tiering import analyze_intelligent_tiering_suitability

def render_intelligent_tiering(data: dict):
    st.subheader("🧠 Amazon S3 Intelligent-Tiering Optimization Center")
    st.caption("Deep analytics on automated tiering suitability, monitoring fee impact, and small-object guardrails.")

    df: pd.DataFrame = data["dataframe"]
    if df.empty:
        st.warning("No bucket data loaded.")
        return

    analysis = analyze_intelligent_tiering_suitability(df)

    # Suitability Banner
    rating = analysis["suitability_rating"]
    if "EXCELLENT" in rating:
        st.success(f"**Suitability Rating: {rating}** — {analysis['recommendation']}")
    elif "POOR" in rating:
        st.error(f"**Suitability Rating: {rating}** — {analysis['recommendation']}")
    else:
        st.info(f"**Suitability Rating: {rating}** — {analysis['recommendation']}")

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Eligible Objects (≥128 KB)", f"{analysis['eligible_objects']:,}")
    with m2:
        st.metric("Ineligible Small (<128 KB)", f"{analysis['ineligible_small_objects']:,}", f"{analysis['small_object_percentage']}% of objects", delta_color="inverse")
    with m3:
        st.metric("Monthly Monitoring Fee", f"${analysis['monitoring_fee_monthly']:,.3f}", "$0.0025/1k objects")
    with m4:
        st.metric("Net Monthly Savings", f"${analysis['net_monthly_savings']:,.2f}", f"↓ {analysis['savings_percentage']}%")

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("📊 Projected Tier Distribution")
        tier_data = analysis["tier_breakdown"]
        tier_df = pd.DataFrame([
            {"Tier": k, "VolumeGB": v["gb"], "Cost": v["cost"]}
            for k, v in tier_data.items()
        ])

        fig_tier = px.bar(
            tier_df,
            x="Tier",
            y="VolumeGB",
            color="Tier",
            color_discrete_sequence=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]
        )
        fig_tier.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#cbd5e1"),
            height=300,
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=False,
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="Volume (GB)", showgrid=True, gridcolor="#334155")
        )
        st.plotly_chart(fig_tier, use_container_width=True)

    with col_chart2:
        st.subheader("💡 Why S3 Intelligent-Tiering?")
        st.markdown("""
        - **Zero Retrieval Fees:** Unlike Standard-IA and Glacier, there are **no data retrieval fees** when objects are accessed.
        - **Automatic Downtiering:** Inactive objects slide down from Frequent ($0.023) to Infrequent ($0.0125) at 30 days, Archive Instant ($0.004) at 90 days, and Deep Archive ($0.00099) at 180 days.
        - **Immediate Uplift:** Any read immediately brings the object back to the Frequent Access tier at low millisecond latency.
        - **Small Object Guardrail:** Objects <128 KB are never monitored or charged monitoring fees, remaining at S3 Standard rates without penalty.
        """)

    # Small Object Density Guardrail Box
    if analysis["small_object_percentage"] > 25.0:
        st.warning(f"⚠️ **Guardrail Notice:** {analysis['small_object_percentage']}% of objects in this bucket are smaller than 128 KB. If you migrate this bucket to S3 Intelligent-Tiering, these {analysis['ineligible_small_objects']:,} small objects will NOT be tiered down and will continue to incur S3 Standard rates. Consider archiving small files into consolidated `.tar.gz` or `.parquet` bundles before transition.")
