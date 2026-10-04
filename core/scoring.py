"""
ArchiveX - Archive Scoring & Recommendation Engine
Calculates multi-factor Archive Readiness Scores (0-100) and actionable S3 storage class recommendations.
"""
from typing import Dict, Any, Tuple
from config import ARCHIVE_PREFIX_PATTERNS, ACTIVE_PREFIX_PATTERNS, EXTENSION_PATTERNS

def calculate_archive_score(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a composite Archive Readiness Score (0-100) based on age, object size,
    prefix heuristics, current storage class, and file type.
    """
    key = obj.get("Key", "")
    size_bytes = obj.get("Size", 0)
    age_days = obj.get("AgeDays", 0)
    current_tier = obj.get("StorageClass", "STANDARD")
    tags = obj.get("Tags", {})
    
    key_lower = key.lower()
    size_kb = size_bytes / 1024.0
    size_mb = size_kb / 1024.0

    # 1. Age Factor (0 - 40 points)
    if age_days >= 365:
        age_score = 40.0
    elif age_days >= 180:
        age_score = 35.0
    elif age_days >= 90:
        age_score = 25.0
    elif age_days >= 30:
        age_score = 15.0
    elif age_days >= 14:
        age_score = 5.0
    else:
        age_score = 0.0

    # 2. Size Factor (0 - 25 points)
    # AWS S3 standard-IA and Glacier have minimum billable size (128 KB)
    # Very small files penalized to avoid negative ROI on transition requests
    if size_kb < 128:
        size_score = 2.0  # High overhead warning
        size_flag = "SMALL_OBJECT_OVERHEAD"
    elif size_mb >= 50:
        size_score = 25.0 # Ideal for archive
        size_flag = "LARGE_PAYLOAD_OPTIMAL"
    elif size_mb >= 5:
        size_score = 20.0
    elif size_kb >= 512:
        size_score = 15.0
    else:
        size_score = 10.0
        size_flag = "MODERATE_SIZE"

    # 3. Semantic / Pattern Factor (0 - 20 points)
    pattern_score = 10.0 # Neutral baseline
    is_archive_pattern = any(p in key_lower for p in ARCHIVE_PREFIX_PATTERNS)
    is_active_pattern = any(p in key_lower for p in ACTIVE_PREFIX_PATTERNS)
    
    has_archive_ext = any(key_lower.endswith(ext) for ext in EXTENSION_PATTERNS["archive_friendly"])
    has_active_ext = any(key_lower.endswith(ext) for ext in EXTENSION_PATTERNS["active_friendly"])
    
    if is_archive_pattern or has_archive_ext:
        pattern_score = 20.0
    elif is_active_pattern or has_active_ext:
        pattern_score = 0.0

    # 4. Current Tier Factor (0 - 15 points)
    if current_tier == "STANDARD":
        tier_score = 15.0 # Max savings opportunity
    elif current_tier in ["STANDARD_IA", "ONEZONE_IA"]:
        tier_score = 10.0 # Moderate savings remaining
    elif current_tier == "INTELLIGENT_TIERING":
        tier_score = 6.0  # Already automated
    elif current_tier == "GLACIER_IR":
        tier_score = 4.0
    elif current_tier in ["GLACIER", "DEEP_ARCHIVE"]:
        tier_score = 0.0  # Already cold
    else:
        tier_score = 5.0

    # Composite Score
    total_score = round(age_score + size_score + pattern_score + tier_score, 1)
    total_score = max(0.0, min(100.0, total_score))

    # Determine Recommendation & Rationale
    recommendation, urgency, rationale = determine_recommendation(
        total_score=total_score,
        age_days=age_days,
        size_kb=size_kb,
        current_tier=current_tier,
        is_archive_pattern=is_archive_pattern or has_archive_ext,
        is_active_pattern=is_active_pattern or has_active_ext,
        tags=tags
    )

    return {
        "score": total_score,
        "recommendation": recommendation,
        "urgency": urgency,
        "rationale": rationale,
        "breakdown": {
            "age_score": age_score,
            "size_score": size_score,
            "pattern_score": pattern_score,
            "tier_score": tier_score
        },
        "size_flag": "UNDER_128KB_OVERHEAD" if size_kb < 128 else "STANDARD_OR_LARGE"
    }

def determine_recommendation(
    total_score: float,
    age_days: int,
    size_kb: float,
    current_tier: str,
    is_archive_pattern: bool,
    is_active_pattern: bool,
    tags: Dict[str, str]
) -> Tuple[str, str, str]:
    """Generates precise tier target and actionable rationale."""
    if current_tier == "DEEP_ARCHIVE":
        return "OPTIMIZED", "NONE", "Object is already stored in S3 Glacier Deep Archive (lowest possible storage class rate)."

    if current_tier == "GLACIER" and age_days > 180 and is_archive_pattern:
        return "DEEP_ARCHIVE", "LOW", f"Object has resided in Glacier for {age_days} days. Moving to Deep Archive will reduce monthly storage cost by ~72%."

    if size_kb < 128:
        return "KEEP_STANDARD", "INFO", f"Object size ({size_kb:.1f} KB) is below S3's 128 KB minimum billable capacity threshold for Glacier and IA. Transitioning would incur fee penalties without net savings."

    if is_active_pattern and age_days < 90:
        return "KEEP_STANDARD", "LOW", "Object key pattern matches active web/cache assets with ongoing low-latency read requirements."

    # Long retention / compliance / cold backups
    if age_days >= 180 and (is_archive_pattern or tags.get("RetentionClass")):
        return "DEEP_ARCHIVE", "HIGH", f"High-confidence archive candidate. Inactive for {age_days} days with cold/backup metadata. S3 Glacier Deep Archive saves up to 95.7% compared to S3 Standard."

    if age_days >= 90:
        if is_archive_pattern:
            return "GLACIER_FLEXIBLE", "HIGH", f"Age of {age_days} days exceeds typical active restore window. Recommend S3 Glacier Flexible Retrieval (standard or bulk retrieval)."
        else:
            return "INTELLIGENT_TIERING", "MEDIUM", f"Age is {age_days} days with unknown access regularity. S3 Intelligent-Tiering automatically monitors and tiers down without retrieval risk."

    if age_days >= 30:
        return "STANDARD_IA", "MEDIUM", f"Age is {age_days} days. Eligible for S3 Standard-IA (Infrequent Access) for ~45% storage cost reduction."

    return "KEEP_STANDARD", "LOW", f"Object is young ({age_days} days old). Keep in S3 Standard during active lifecycle phase."
