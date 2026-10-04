"""
ArchiveX Core Module Package
"""
from core.scoring import calculate_archive_score
from core.cost_engine import simulate_cost_transition, summarize_bucket_cost_profile
from core.lifecycle_gen import build_lifecycle_rule, generate_lifecycle_policy_json, dry_run_lifecycle_policy
from core.intelligent_tiering import analyze_intelligent_tiering_suitability
from core.copilot import ArchiveCopilot
from core.aws_client import S3ClientManager
from core.demo_data import get_demo_dataset

__all__ = [
    "calculate_archive_score",
    "simulate_cost_transition",
    "summarize_bucket_cost_profile",
    "build_lifecycle_rule",
    "generate_lifecycle_policy_json",
    "dry_run_lifecycle_policy",
    "analyze_intelligent_tiering_suitability",
    "ArchiveCopilot",
    "S3ClientManager",
    "get_demo_dataset"
]
