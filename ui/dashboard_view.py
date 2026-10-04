"""
ArchiveX - Dashboard View
Executive summary, high-level KPIs, storage class distribution, and cost reduction overview.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from ui.styles import render_story_pipeline
from ui.components import render_kpi_card, get_storage_class_badge, get_recommendation_badge, get_score_badge
from config import S3_PRICING

def render_dashboard(data: dict):
    st.markdown(render_story_pipeline(), unsafe_allow_html=True)

    # Hackathon Banner
    st.markdown("""
    <div class="guardrail-box">
        <strong>💡 AWS Storage Hackathon Value Proposition:</strong><br>
        <em>"ArchiveX does not replace Amazon S3's native storage optimization capabilities. It makes them easier to understand, monitor, and operationalize through an intelligent decision-support layer."</em>
    </div>
    """, unsafe_allow_html=True)

    df: pd.DataFrame = data["dataframe"]
    if df.empty:
        st.warning("No S3 object data available. Please select a bucket or load demo data.")
        return

    # Calculate Summary Stats
    total_size_bytes = df["Size"].sum()
    total_size_gb = total_size_bytes / (1024**3)
    total_size_tb = total_size_gb / 1024.0
    total_objects = len(df)
    
    # Financials
    cost_summary = data.get("cost_summary", {})
    curr_monthly = cost_summary.get("current_monthly_cost", 0.0)
    pot_monthly_savings = cost_summary.get("potential_monthly_savings", 0.0)
    pot_annual_savings = cost_summary.get("potential_annual_savings", 0.0)
    savings_pct = (pot_monthly_savings / curr_monthly * 100) if curr_monthly > 0 else 0.0

    avg_score = df["ArchiveScore"].mean() if "ArchiveScore" in df.columns else 0.0

    # Top KPI Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        size_display = f"{total_size_tb:.2f} TB" if total_size_tb >= 1.0 else f"{total_size_gb:.1f} GB"
        render_kpi_card("Total Managed Storage", size_display, f"{total_objects:,} objects")
    with col2:
        render_kpi_card("Current Monthly Cost", f"${curr_monthly:,.2f}", "S3 Baseline")
    with col3:
        render_kpi_card("Potential Mo. Savings", f"${pot_monthly_savings:,.2f}", f"↓ {savings_pct:.1f}% reduction")
    with col4:
        render_kpi_card("Projected Annual ROI", f"${pot_annual_savings:,.2f}", "12-month net benefit")
    with col5:
        render_kpi_card("Archive Readiness", f"{avg_score:.1f} / 100", "Fleet-wide index")

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row 1: Storage Class Breakdown & Age Distribution
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("📦 Storage Class Breakdown")
        class_grp = df.groupby("StorageClass")["Size"].sum().reset_index()
        class_grp["SizeGB"] = class_grp["Size"] / (1024**3)
        class_grp["ClassName"] = class_grp["StorageClass"].apply(lambda sc: S3_PRICING.get(sc, {}).get("name", sc))
        
        color_map = {S3_PRICING.get(sc, {}).get("name", sc): S3_PRICING.get(sc, {}).get("color", "#94a3b8") for sc in class_grp["StorageClass"]}

        fig_class = px.pie(
            class_grp,
            values="SizeGB",
            names="ClassName",
            color="ClassName",
            color_discrete_map=color_map,
            hole=0.45,
        )
        fig_class.update_traces(textposition='inside', textinfo='percent+label')
        fig_class.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=300,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#cbd5e1")
        )
        st.plotly_chart(fig_class, use_container_width=True)

    with col_chart2:
        st.subheader("⏳ Object Age Inactivity Tiers")
        # Binning by S3 Lifecycle Milestones
        bins = [-1, 30, 90, 180, 365, 99999]
        labels = ["< 30 Days (Active)", "30-90 Days (IA)", "90-180 Days (Glacier IR)", "180-365 Days (Deep)", "> 365 Days (Legacy)"]
        df["AgeCategory"] = pd.cut(df["AgeDays"], bins=bins, labels=labels)
        age_grp = df.groupby("AgeCategory", observed=False)["Size"].sum().reset_index()
        age_grp["SizeGB"] = age_grp["Size"] / (1024**3)

        fig_age = px.bar(
            age_grp,
            x="AgeCategory",
            y="SizeGB",
            color="AgeCategory",
            color_discrete_sequence=["#3b82f6", "#10b981", "#f59e0b", "#f97316", "#ef4444"]
        )
        fig_age.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=300,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#cbd5e1"),
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="Volume (GB)", showgrid=True, gridcolor="#334155")
        )
        st.plotly_chart(fig_age, use_container_width=True)

    # Charts Row 2: Optimization Recommendation Distribution
    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        st.subheader("🎯 Archive Target Recommendations")
        if "Recommendation" in df.columns:
            rec_grp = df.groupby("Recommendation")["Size"].sum().reset_index()
            rec_grp["SizeGB"] = rec_grp["Size"] / (1024**3)
            fig_rec = px.bar(
                rec_grp,
                x="SizeGB",
                y="Recommendation",
                orientation='h',
                color="Recommendation",
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_rec.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=260,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#cbd5e1"),
                xaxis=dict(title="Target Volume (GB)", showgrid=True, gridcolor="#334155"),
                yaxis=dict(title="")
            )
            st.plotly_chart(fig_rec, use_container_width=True)

    with col_chart4:
        st.subheader("📊 Archive Readiness Score Distribution")
        if "ArchiveScore" in df.columns:
            fig_hist = px.histogram(
                df,
                x="ArchiveScore",
                nbins=20,
                color_discrete_sequence=["#8b5cf6"]
            )
            fig_hist.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=260,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#cbd5e1"),
                xaxis=dict(title="Score (0 = Keep Hot, 100 = Immediate Cold Archive)", range=[0, 100]),
                yaxis=dict(title="Object Count", showgrid=True, gridcolor="#334155")
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    # Priority Action Table
    st.subheader("🚨 Priority Optimization Candidates")
    st.caption("Top objects stored in S3 Standard with high archive readiness scores (>75) generating excess storage spend.")
    
    top_candidates = df[
        (df["StorageClass"] == "STANDARD") & 
        (df["ArchiveScore"] >= 75)
    ].sort_values(by=["Size", "ArchiveScore"], ascending=[False, False]).head(8)

    if not top_candidates.empty:
        display_rows = []
        for _, row in top_candidates.iterrows():
            size_mb = row["Size"] / (1024 * 1024)
            size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.1f} MB"
            display_rows.append({
                "Object Key": row["Key"],
                "Size": size_str,
                "Age": f"{row['AgeDays']} days",
                "Current Class": row["StorageClass"],
                "Score": f"{row['ArchiveScore']:.0f}/100",
                "Recommended Tier": row["Recommendation"],
                "Urgency": row.get("Urgency", "HIGH")
            })
        st.dataframe(pd.DataFrame(display_rows), use_container_width=True)
    else:
        st.success("No high-priority unoptimized objects detected in S3 Standard.")
