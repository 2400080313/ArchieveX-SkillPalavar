"""
ArchiveX - Configuration and S3 Pricing Constants
Centralized settings, AWS storage class rates, minimum duration, and thresholds.
"""
import os
from typing import Dict, Any

# Application Metadata
APP_NAME = "ArchiveX"
APP_TAGLINE = "Intelligent Amazon S3 Archive & Lifecycle Decision Support Platform"
APP_VERSION = "2.4.0-hackathon"

def get_config_val(key: str, default: Any = None) -> Any:
    """Safely retrieves a configuration value from Streamlit secrets or OS environment."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

# Default AWS Settings
DEFAULT_REGION = get_config_val("AWS_DEFAULT_REGION", "us-east-1")
DEMO_MODE_DEFAULT = True

# Standard AWS S3 Pricing (us-east-1 reference rates per GB-month)
S3_PRICING: Dict[str, Dict[str, Any]] = {
    "STANDARD": {
        "name": "S3 Standard",
        "storage_per_gb_month": 0.0230,
        "retrieval_per_gb": 0.0,
        "min_days": 0,
        "min_size_kb": 0,
        "monitoring_per_1k": 0.0,
        "color": "#3b82f6",  # Blue
        "description": "General-purpose storage for frequently accessed data with low latency."
    },
    "INTELLIGENT_TIERING": {
        "name": "S3 Intelligent-Tiering",
        "storage_per_gb_month": 0.0230,  # Base frequent rate (moves down to 0.0125, 0.004, 0.00099)
        "avg_blended_rate": 0.0135,      # Typical blended rate in active tiering
        "retrieval_per_gb": 0.0,
        "min_days": 30,
        "min_size_kb": 128,
        "monitoring_per_1k": 0.0025,     # $0.0025 per 1,000 objects >= 128KB
        "color": "#8b5cf6",  # Purple
        "description": "Automatic cost savings by shifting data across tiers without operational overhead."
    },
    "STANDARD_IA": {
        "name": "S3 Standard-IA",
        "storage_per_gb_month": 0.0125,
        "retrieval_per_gb": 0.010,
        "min_days": 30,
        "min_size_kb": 128,
        "monitoring_per_1k": 0.0,
        "color": "#10b981",  # Emerald
        "description": "For data accessed less frequently, but requiring rapid access when needed."
    },
    "ONEZONE_IA": {
        "name": "S3 One Zone-IA",
        "storage_per_gb_month": 0.0100,
        "retrieval_per_gb": 0.010,
        "min_days": 30,
        "min_size_kb": 128,
        "monitoring_per_1k": 0.0,
        "color": "#06b6d4",  # Cyan
        "description": "Lower-cost option for re-creatable infrequently accessed data stored in a single AZ."
    },
    "GLACIER_IR": {
        "name": "S3 Glacier Instant Retrieval",
        "storage_per_gb_month": 0.0040,
        "retrieval_per_gb": 0.030,
        "min_days": 90,
        "min_size_kb": 128,
        "monitoring_per_1k": 0.0,
        "color": "#f59e0b",  # Amber
        "description": "Archive storage delivering lowest-cost storage with millisecond access."
    },
    "GLACIER": {
        "name": "S3 Glacier Flexible Retrieval",
        "storage_per_gb_month": 0.0036,
        "retrieval_per_gb": 0.010,       # Standard retrieval
        "min_days": 90,
        "min_size_kb": 0,
        "monitoring_per_1k": 0.0,
        "color": "#f97316",  # Orange
        "description": "Low-cost archive for data requiring retrieval in minutes to hours."
    },
    "DEEP_ARCHIVE": {
        "name": "S3 Glacier Deep Archive",
        "storage_per_gb_month": 0.00099, # Under $1 / TB / month
        "retrieval_per_gb": 0.020,
        "min_days": 180,
        "min_size_kb": 0,
        "monitoring_per_1k": 0.0,
        "color": "#ef4444",  # Red
        "description": "Lowest cost storage class in the cloud for long-term retention & compliance (7-10+ yrs)."
    }
}

# Request and Transition S3 Costs (per 1,000 requests)
REQUEST_PRICING = {
    "PUT_COPY_POST_LIST": 0.005,      # $0.005 per 1,000 requests
    "GET_SELECT": 0.0004,             # $0.0004 per 1,000 requests
    "TRANSITION_STANDARD_IA": 0.01,
    "TRANSITION_GLACIER": 0.03,
    "TRANSITION_DEEP_ARCHIVE": 0.05,
    "TRANSITION_INTELLIGENT": 0.0025
}

# Archive Scoring Thresholds
SCORING_WEIGHTS = {
    "age": 0.35,          # How old is the object
    "size": 0.25,         # Is it large enough to avoid per-object overhead
    "prefix_pattern": 0.20, # Does prefix/suffix match backup/log/archive/raw
    "current_tier": 0.10, # Currently in expensive tier (S3 Standard)
    "tag_signals": 0.10   # Tags indicating retention/compliance/expiry
}

# Known Archive/Log Patterns for Heuristics
ARCHIVE_PREFIX_PATTERNS = [
    "backup", "backups", "archive", "archives", "dump", "db_backup",
    "snapshot", "historical", "cold", "raw-logs", "audit", "compliance",
    "telemetry", "export", "batch", "parquet", "cdr", "financial-records"
]

ACTIVE_PREFIX_PATTERNS = [
    "live", "current", "active", "assets", "static", "images", "web",
    "public", "thumbnails", "cache", "sessions", "hot"
]

EXTENSION_PATTERNS = {
    "archive_friendly": [".tar", ".gz", ".zip", ".7z", ".bak", ".sql", ".dump", ".parquet", ".csv.gz", ".log", ".jsonl"],
    "active_friendly": [".html", ".js", ".css", ".png", ".jpg", ".svg", ".ico", ".woff2"]
}
