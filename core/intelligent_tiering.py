"""
ArchiveX - S3 Intelligent-Tiering Analysis & Optimization Engine
Evaluates suitability for S3 Intelligent-Tiering, detects small-object overhead,
and simulates automatic tier movements across Frequent, Infrequent, Archive Instant, and Deep Archive tiers.
"""
from typing import Dict, Any, List
import pandas as pd
from config import S3_PRICING

def analyze_intelligent_tiering_suitability(objects_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluates whether an S3 dataset or bucket is a prime candidate for S3 Intelligent-Tiering.
    Identifies 128KB eligibility and calculates monitoring fees vs potential savings.
    """
    if objects_df.empty:
        return {
            "eligible_objects": 0,
            "ineligible_small_objects": 0,
            "eligible_size_gb": 0.0,
            "ineligible_size_gb": 0.0,
            "monitoring_fee_monthly": 0.0,
            "net_monthly_savings": 0.0,
            "suitability_rating": "N/A",
            "tier_breakdown": {}
        }

    total_count = len(objects_df)
    small_obj_mask = (objects_df["Size"] < 131072) # < 128 KB
    eligible_df = objects_df[~small_obj_mask]
    ineligible_df = objects_df[small_obj_mask]

    eligible_count = len(eligible_df)
    ineligible_count = len(ineligible_df)

    eligible_size_gb = eligible_df["Size"].sum() / (1024**3)
    ineligible_size_gb = ineligible_df["Size"].sum() / (1024**3)

    # AWS monitoring charge is $0.0025 per 1,000 objects >= 128 KB
    monitoring_fee_monthly = (eligible_count / 1000.0) * S3_PRICING["INTELLIGENT_TIERING"]["monitoring_per_1k"]

    # Simulating distribution across Intelligent-Tiering automatic tiers based on age distribution:
    # - < 30 days: Frequent Access Tier ($0.023/GB)
    # - 30 to 90 days: Infrequent Access Tier ($0.0125/GB)
    # - 90 to 180 days: Archive Instant Access Tier ($0.0040/GB)
    # - > 180 days: Deep Archive Access Tier ($0.00099/GB)
    frequent_df = eligible_df[eligible_df["AgeDays"] < 30]
    infrequent_df = eligible_df[(eligible_df["AgeDays"] >= 30) & (eligible_df["AgeDays"] < 90)]
    archive_instant_df = eligible_df[(eligible_df["AgeDays"] >= 90) & (eligible_df["AgeDays"] < 180)]
    deep_archive_df = eligible_df[eligible_df["AgeDays"] >= 180]

    freq_gb = frequent_df["Size"].sum() / (1024**3)
    infreq_gb = infrequent_df["Size"].sum() / (1024**3)
    arch_inst_gb = archive_instant_df["Size"].sum() / (1024**3)
    deep_gb = deep_archive_df["Size"].sum() / (1024**3)

    # Cost in S3 Standard (Baseline)
    standard_cost = eligible_size_gb * S3_PRICING["STANDARD"]["storage_per_gb_month"]

    # Cost in S3 Intelligent-Tiering
    it_cost = (
        (freq_gb * 0.0230) +
        (infreq_gb * 0.0125) +
        (arch_inst_gb * 0.0040) +
        (deep_gb * 0.00099)
    ) + monitoring_fee_monthly

    gross_savings = standard_cost - (it_cost - monitoring_fee_monthly)
    net_savings = standard_cost - it_cost
    savings_percent = ((net_savings / standard_cost) * 100) if standard_cost > 0 else 0.0

    # Suitability Rating
    small_ratio = ineligible_count / total_count if total_count > 0 else 0
    if small_ratio > 0.65:
        suitability = "POOR (High Small Object Density)"
        recommendation = "Over 65% of objects are under 128KB. Intelligent-Tiering does not tier objects <128KB. Consider S3 Lifecycle tar/zip batching before tiering."
    elif net_savings > 10.0 and savings_percent > 30:
        suitability = "EXCELLENT"
        recommendation = "Ideal candidate. Unpredictable or aging access patterns benefit from zero retrieval fees and automatic tiering to Deep Archive."
    elif net_savings > 0:
        suitability = "GOOD"
        recommendation = "Positive net savings after accounting for the $0.0025/1k monitoring fee. Recommended for general workloads."
    else:
        suitability = "NEUTRAL"
        recommendation = "Data is primarily fresh (<30 days). Keep in S3 Standard or re-evaluate in 60 days."

    return {
        "total_objects": total_count,
        "eligible_objects": eligible_count,
        "ineligible_small_objects": ineligible_count,
        "small_object_percentage": round(small_ratio * 100, 1),
        "eligible_size_gb": round(eligible_size_gb, 2),
        "ineligible_size_gb": round(ineligible_size_gb, 2),
        "monitoring_fee_monthly": round(monitoring_fee_monthly, 3),
        "baseline_standard_cost": round(standard_cost, 2),
        "projected_it_cost": round(it_cost, 2),
        "gross_monthly_savings": round(gross_savings, 2),
        "net_monthly_savings": round(net_savings, 2),
        "savings_percentage": round(savings_percent, 1),
        "suitability_rating": suitability,
        "recommendation": recommendation,
        "tier_breakdown": {
            "Frequent Access (<30d)": {"gb": round(freq_gb, 2), "rate": 0.023, "cost": round(freq_gb * 0.023, 2)},
            "Infrequent Access (30-90d)": {"gb": round(infreq_gb, 2), "rate": 0.0125, "cost": round(infreq_gb * 0.0125, 2)},
            "Archive Instant (90-180d)": {"gb": round(arch_inst_gb, 2), "rate": 0.0040, "cost": round(arch_inst_gb * 0.004, 2)},
            "Deep Archive Access (>180d)": {"gb": round(deep_gb, 2), "rate": 0.00099, "cost": round(deep_gb * 0.00099, 2)}
        }
    }
