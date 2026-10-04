"""
Unit tests for ArchiveX Cost & ROI Simulator Engine
"""
import pytest
from core.cost_engine import calculate_object_monthly_cost, simulate_cost_transition, summarize_bucket_cost_profile
import pandas as pd

def test_object_monthly_cost():
    """Verify S3 standard cost for 100 GB."""
    bytes_100gb = 100 * (1024 ** 3)
    cost = calculate_object_monthly_cost(bytes_100gb, "STANDARD")
    assert round(cost, 2) == 2.30 # $0.023 * 100

def test_simulate_transition_to_deep_archive():
    """Verify savings and break-even for transitioning 10 TB (10,240 GB) and 5,000 objects to Deep Archive."""
    sim = simulate_cost_transition(
        total_size_gb=10240.0,
        object_count=5000,
        source_class="STANDARD",
        target_class="DEEP_ARCHIVE",
        monthly_retrieval_gb=0.0,
        duration_months=12
    )

    assert sim["current_monthly_storage"] > 200.0
    assert sim["target_monthly_storage"] < 15.0 # ~ $10.13
    assert sim["monthly_savings"] > 200.0
    assert sim["savings_percent"] > 90.0
    assert sim["one_time_transition_fee"] == (5000 / 1000.0) * 0.05 # $0.25
    assert sim["breakeven_days"] <= 3 # Recovers within days
    assert sim["total_net_savings"] > 2400.0

def test_summarize_bucket_cost_profile():
    data = [
        {"Key": "obj1.bak", "Size": 10 * (1024**3), "StorageClass": "STANDARD", "Recommendation": "DEEP_ARCHIVE"},
        {"Key": "obj2.log", "Size": 10 * (1024**3), "StorageClass": "STANDARD_IA", "Recommendation": "STANDARD_IA"}
    ]
    df = pd.DataFrame(data)
    summary = summarize_bucket_cost_profile(df)
    
    assert summary["total_objects"] == 2
    assert summary["total_size_gb"] == 20.0
    assert summary["current_monthly_cost"] > 0
    assert summary["potential_monthly_savings"] > 0
