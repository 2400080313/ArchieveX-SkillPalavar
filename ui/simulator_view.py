"""
ArchiveX - Cost & ROI Simulator View
Interactive S3 financial modeling with retrieval sensitivity, break-even analysis, and multi-year ROI charts.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from core.cost_engine import simulate_cost_transition
from config import S3_PRICING

def render_simulator(data: dict):
    st.subheader("💰 Interactive S3 Cost & ROI Simulator")
    st.caption("Model lifecycle transitions, factoring in one-time transition request charges, monitoring fees, and retrieval sensitivity.")

    # Defaults from current bucket dataset if available
    df: pd.DataFrame = data["dataframe"]
    default_gb = float(df["Size"].sum() / (1024**3)) if not df.empty else 1000.0
    default_count = len(df) if not df.empty else 10000

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    with col_ctrl1:
        storage_gb = st.number_input("Total Storage Volume (GB)", min_value=1.0, max_value=5000000.0, value=max(round(default_gb, 1), 100.0), step=100.0)
        object_count = st.number_input("Object Count", min_value=10, max_value=100000000, value=max(default_count, 1000), step=1000)

    with col_ctrl2:
        source_class = st.selectbox("Current Source Storage Class", options=list(S3_PRICING.keys()), index=0, format_func=lambda k: S3_PRICING[k]["name"])
        target_class = st.selectbox("Target Optimization Class", options=[k for k in S3_PRICING.keys() if k != source_class], index=len(S3_PRICING) - 2, format_func=lambda k: S3_PRICING[k]["name"])

    with col_ctrl3:
        retrieval_pct = st.slider("Monthly Retrieval Rate (% of data retrieved)", min_value=0.0, max_value=100.0, value=2.0, step=0.5)
        monthly_retrieval_gb = (retrieval_pct / 100.0) * storage_gb
        st.caption(f"Estimated retrieval: {monthly_retrieval_gb:,.1f} GB / month")
        duration_months = st.slider("Simulation Horizon (Months)", min_value=3, max_value=36, value=12, step=3)

    # Run Simulation
    sim_result = simulate_cost_transition(
        total_size_gb=storage_gb,
        object_count=object_count,
        source_class=source_class,
        target_class=target_class,
        monthly_retrieval_gb=monthly_retrieval_gb,
        duration_months=duration_months
    )

    st.markdown("---")

    # Financial Scorecard
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    with sc1:
        st.metric("Baseline Monthly", f"${sim_result['current_monthly_storage']:,.2f}")
    with sc2:
        st.metric("Optimized Monthly", f"${sim_result['target_total_monthly']:,.2f}", f"-{sim_result['savings_percent']:.1f}%")
    with sc3:
        st.metric("Monthly Net Savings", f"${sim_result['monthly_savings']:,.2f}")
    with sc4:
        st.metric("One-time Transition Fee", f"${sim_result['one_time_transition_fee']:,.2f}")
    with sc5:
        be_days = sim_result['breakeven_days']
        be_str = f"{be_days} days" if be_days > 0 else "Immediate" if sim_result['one_time_transition_fee'] == 0 else "Negative ROI"
        st.metric("Break-even Horizon", be_str)

    # Warnings for retrieval or small files
    if sim_result["monthly_retrieval_cost"] > sim_result["target_monthly_storage"]:
        st.warning(f"⚠️ High Retrieval Cost Alert: Monthly retrieval fees (${sim_result['monthly_retrieval_cost']:,.2f}) exceed storage fees. If access is frequent, consider S3 Intelligent-Tiering which has ZERO retrieval charges.")

    # Cumulative Projection Chart
    st.subheader(f"📈 Cumulative Cost Comparison ({duration_months}-Month Horizon)")
    months = sim_result["projection"]["months"]
    curr_cum = sim_result["projection"]["current_cumulative"]
    tgt_cum = sim_result["projection"]["target_cumulative"]
    net_sav = sim_result["projection"]["net_savings_cumulative"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[f"Month {m}" for m in months],
        y=curr_cum,
        name=f"Current ({S3_PRICING[source_class]['name']})",
        line=dict(color="#ef4444", width=3, dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=[f"Month {m}" for m in months],
        y=tgt_cum,
        name=f"Optimized ({S3_PRICING[target_class]['name']})",
        line=dict(color="#10b981", width=3)
    ))
    fig.add_trace(go.Bar(
        x=[f"Month {m}" for m in months],
        y=net_sav,
        name="Cumulative Net Savings",
        marker_color="rgba(59, 130, 246, 0.4)"
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#cbd5e1"),
        height=380,
        margin=dict(t=20, b=20, l=20, r=20),
        xaxis=dict(title="Timeline", showgrid=False),
        yaxis=dict(title="Cumulative USD ($)", showgrid=True, gridcolor="#334155"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary Takeaway
    st.success(f"**Financial Verdict:** Transitioning {storage_gb:,.1f} GB ({object_count:,} objects) to {S3_PRICING[target_class]['name']} yields **${sim_result['total_net_savings']:,.2f} in net savings** over {duration_months} months with an estimated ROI of **{sim_result['roi_percent']:.1f}%**.")
