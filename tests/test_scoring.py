"""
Unit tests for ArchiveX Archive Readiness Scoring & Recommendation Engine
"""
import pytest
from core.scoring import calculate_archive_score

def test_backup_deep_archive_recommendation():
    """An old, large database backup in S3 Standard should receive high score and DEEP_ARCHIVE recommendation."""
    obj = {
        "Key": "backups/postgres/prod_db_2023.dump.gz",
        "Size": 10 * 1024 * 1024 * 1024, # 10 GB
        "AgeDays": 412,
        "StorageClass": "STANDARD",
        "Tags": {"Environment": "Production"}
    }
    result = calculate_archive_score(obj)
    
    assert result["score"] >= 80.0
    assert result["recommendation"] == "DEEP_ARCHIVE"
    assert result["urgency"] == "HIGH"
    assert "strong long-term archive candidate" in result["rationale"] or "S3 Glacier Deep Archive" in result["rationale"]

def test_small_object_under_128kb_protection():
    """Objects < 128 KB should receive KEEP_STANDARD to protect against minimum capacity billing overhead."""
    obj = {
        "Key": "icons/avatar.png",
        "Size": 12 * 1024, # 12 KB (below 128 KB)
        "AgeDays": 150,
        "StorageClass": "STANDARD",
        "Tags": {}
    }
    result = calculate_archive_score(obj)
    
    assert result["recommendation"] == "KEEP_STANDARD"
    assert result["size_flag"] == "UNDER_128KB_OVERHEAD"
    assert "128 KB" in result["rationale"]

def test_active_recent_object():
    """Recent active frontend assets should stay in S3 Standard."""
    obj = {
        "Key": "cdn/static/main.bundle.js",
        "Size": 2 * 1024 * 1024, # 2 MB
        "AgeDays": 10,
        "StorageClass": "STANDARD",
        "Tags": {}
    }
    result = calculate_archive_score(obj)
    
    assert result["score"] < 40.0
    assert result["recommendation"] == "KEEP_STANDARD"

def test_already_optimized_deep_archive():
    """Objects already in DEEP_ARCHIVE should be recognized as OPTIMIZED."""
    obj = {
        "Key": "compliance/audit_2020.tar.gz",
        "Size": 5 * 1024 * 1024 * 1024,
        "AgeDays": 800,
        "StorageClass": "DEEP_ARCHIVE",
        "Tags": {}
    }
    result = calculate_archive_score(obj)
    
    assert result["recommendation"] == "OPTIMIZED"
    assert "already stored" in result["rationale"]
