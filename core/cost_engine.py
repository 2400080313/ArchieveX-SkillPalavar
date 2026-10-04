"""
ArchiveX - Cost & ROI Simulation Engine
Accurately models Amazon S3 monthly storage, transition, monitoring, and retrieval costs
across all storage classes with break-even timeline and ROI projections.
"""
from typing import Dict, Any, List
import pandas as pd
from config import S3_PRICING, REQUEST_PRICING

def calculate_object_monthly_cost(size_bytes: int, storage_class: str) -> float:
    """Calculates the baseline monthly storage cost for a single object in USD."""
    size_gb = size_bytes / (1024 ** 3)
    rate = S3_PRICING.get(storage_class, S3_PRICING["STANDARD"])["storage_per_gb_month"]
    return size_gb * rate

def simulate_cost_transition(
    total_size_gb: float,
    object_count: int,
    source_class: str = "STANDARD",
    target_class: str = "DEEP_ARCHIVE",
    monthly_retrieval_gb: float = 0.0,
    duration_months: int = 12
) -> Dict[str, Any]:
    """
    Simulates the financial impact of transitioning storage from source_class to target_class.
    Includes transition fees, monthly storage, monitoring fees, and retrieval sensitivity.
    """
    src_rate = S3_PRICING.get(source_class, S3_PRICING["STANDARD"])["storage_per_gb_month"]
    tgt_config = S3_PRICING.get(target_class, S3_PRICING["DEEP_ARCHIVE"])
    tgt_rate = tgt_config["storage_per_gb_month"]
    retrieval_rate = tgt_config["retrieval_per_gb"]
    monitoring_rate_per_1k = tgt_config.get("monitoring_per_1k", 0.0)

    # 1. Baseline Current Monthly Storage Cost
    current_monthly_storage = total_size_gb * src_rate

    # 2. Target Monthly Storage Cost
    # If target is Intelligent-Tiering, estimate blended rate or standard rate
    if target_class == "INTELLIGENT_TIERING":
        target_monthly_storage = total_size_gb * tgt_config.get("avg_blended_rate", 0.0135)
    else:
        target_monthly_storage = total_size_gb * tgt_rate

    # 3. Target Monthly Monitoring Fees (e.g. Intelligent-Tiering: $0.0025 / 1000 objects)
    monthly_monitoring_fee = (object_count / 1000.0) * monitoring_rate_per_1k

    # 4. Target Monthly Retrieval Cost
    monthly_retrieval_cost = monthly_retrieval_gb * retrieval_rate

    # Total Target Monthly
    target_total_monthly = target_monthly_storage + monthly_monitoring_fee + monthly_retrieval_cost
    monthly_savings = current_monthly_storage - target_total_monthly

    # 5. One-time Transition Request Fees
    # S3 charges per 1,000 requests for lifecycle transitions
    if target_class in ["GLACIER", "GLACIER_IR"]:
        trans_fee_per_1k = REQUEST_PRICING["TRANSITION_GLACIER"]
    elif target_class == "DEEP_ARCHIVE":
        trans_fee_per_1k = REQUEST_PRICING["TRANSITION_DEEP_ARCHIVE"]
    elif target_class == "STANDARD_IA":
        trans_fee_per_1k = REQUEST_PRICING["TRANSITION_STANDARD_IA"]
    elif target_class == "INTELLIGENT_TIERING":
        trans_fee_per_1k = REQUEST_PRICING["TRANSITION_INTELLIGENT"]
    else:
        trans_fee_per_1k = 0.0

    one_time_transition_fee = (object_count / 1000.0) * trans_fee_per_1k

    # 6. Break-even Duration
    if monthly_savings > 0:
        breakeven_months = one_time_transition_fee / monthly_savings
        breakeven_days = int(breakeven_months * 30.4)
    else:
        breakeven_months = -1
        breakeven_days = -1

    # 7. Multi-month Projections
    current_cumulative = [current_monthly_storage * m for m in range(1, duration_months + 1)]
    target_cumulative = [one_time_transition_fee + (target_total_monthly * m) for m in range(1, duration_months + 1)]
    savings_cumulative = [c - t for c, t in zip(current_cumulative, target_cumulative)]

    total_net_savings = savings_cumulative[-1] if savings_cumulative else 0.0
    roi_percent = ((total_net_savings / (one_time_transition_fee + (target_total_monthly * duration_months))) * 100) if (one_time_transition_fee + (target_total_monthly * duration_months)) > 0 else 0.0
    savings_percent = ((monthly_savings / current_monthly_storage) * 100) if current_monthly_storage > 0 else 0.0

    return {
        "source_class": source_class,
        "target_class": target_class,
        "total_size_gb": total_size_gb,
        "object_count": object_count,
        "current_monthly_storage": current_monthly_storage,
        "target_monthly_storage": target_monthly_storage,
        "monthly_monitoring_fee": monthly_monitoring_fee,
        "monthly_retrieval_cost": monthly_retrieval_cost,
        "target_total_monthly": target_total_monthly,
        "monthly_savings": monthly_savings,
        "savings_percent": savings_percent,
        "one_time_transition_fee": one_time_transition_fee,
        "breakeven_days": breakeven_days,
        "duration_months": duration_months,
        "total_net_savings": total_net_savings,
        "roi_percent": roi_percent,
        "projection": {
            "months": list(range(1, duration_months + 1)),
            "current_cumulative": current_cumulative,
            "target_cumulative": target_cumulative,
            "net_savings_cumulative": savings_cumulative
        }
    }

def summarize_bucket_cost_profile(objects_df: pd.DataFrame) -> Dict[str, Any]:
    """Generates an aggregate S3 financial summary from an objects DataFrame."""
    if objects_df.empty:
        return {
            "total_objects": 0,
            "total_size_gb": 0.0,
            "current_monthly_cost": 0.0,
            "potential_monthly_savings": 0.0,
            "class_distribution": {},
            "recommendation_distribution": {}
        }

    total_size_bytes = objects_df["Size"].sum()
    total_size_gb = total_size_bytes / (1024 ** 3)
    total_objects = len(objects_df)

    # Current Monthly Cost
    class_groups = objects_df.groupby("StorageClass")["Size"].sum()
    current_cost = 0.0
    class_dist = {}

    for s_class, bytes_val in class_groups.items():
        gb_val = bytes_val / (1024 ** 3)
        rate = S3_PRICING.get(s_class, S3_PRICING["STANDARD"])["storage_per_gb_month"]
        monthly = gb_val * rate
        current_cost += monthly
        class_dist[s_class] = {
            "size_gb": round(gb_val, 2),
            "monthly_cost": round(monthly, 2),
            "count": int((objects_df["StorageClass"] == s_class).sum())
        }

    # Potential optimized cost if recommendations applied
    potential_savings = 0.0
    rec_dist = {}
    if "Recommendation" in objects_df.columns:
        for rec, group in objects_df.groupby("Recommendation"):
            rec_size_gb = group["Size"].sum() / (1024 ** 3)
            rec_dist[rec] = {
                "count": len(group),
                "size_gb": round(rec_size_gb, 2)
            }
            # Calculate savings delta if Standard was transitioned
            if rec == "DEEP_ARCHIVE":
                diff_rate = S3_PRICING["STANDARD"]["storage_per_gb_month"] - S3_PRICING["DEEP_ARCHIVE"]["storage_per_gb_month"]
                potential_savings += rec_size_gb * diff_rate
            elif rec == "GLACIER_FLEXIBLE":
                diff_rate = S3_PRICING["STANDARD"]["storage_per_gb_month"] - S3_PRICING["GLACIER"]["storage_per_gb_month"]
                potential_savings += rec_size_gb * diff_rate
            elif rec == "INTELLIGENT_TIERING":
                diff_rate = S3_PRICING["STANDARD"]["storage_per_gb_month"] - S3_PRICING["INTELLIGENT_TIERING"]["avg_blended_rate"]
                potential_savings += rec_size_gb * diff_rate
            elif rec == "STANDARD_IA":
                diff_rate = S3_PRICING["STANDARD"]["storage_per_gb_month"] - S3_PRICING["STANDARD_IA"]["storage_per_gb_month"]
                potential_savings += rec_size_gb * diff_rate

    return {
        "total_objects": total_objects,
        "total_size_gb": round(total_size_gb, 2),
        "current_monthly_cost": round(current_cost, 2),
        "potential_monthly_savings": round(potential_savings, 2),
        "potential_annual_savings": round(potential_savings * 12, 2),
        "class_distribution": class_dist,
        "recommendation_distribution": rec_dist
    }
