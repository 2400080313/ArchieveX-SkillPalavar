"""
Unit tests for S3 Lifecycle Generator & Dry-Run Inspector
"""
import pytest
import json
import pandas as pd
from core.lifecycle_gen import (
    build_lifecycle_rule,
    generate_lifecycle_policy_json,
    generate_lifecycle_policy_xml,
    generate_terraform_snippet,
    dry_run_lifecycle_policy
)

def test_build_lifecycle_rule():
    rule = build_lifecycle_rule(
        rule_id="Test-Archive-Rule",
        prefix="backups/",
        min_object_size=131072,
        days_to_ia=30,
        days_to_glacier=90,
        days_to_deep_archive=180,
        days_to_expire=730
    )

    assert rule["ID"] == "Test-Archive-Rule"
    assert rule["Status"] == "Enabled"
    assert "And" in rule["Filter"]
    assert rule["Filter"]["And"]["Prefix"] == "backups/"
    assert rule["Filter"]["And"]["ObjectSizeGreaterThan"] == 131072
    assert len(rule["Transitions"]) == 3
    assert rule["Expiration"]["Days"] == 730

def test_generate_lifecycle_policy_json():
    rule = build_lifecycle_rule(rule_id="JsonRule", prefix="logs/")
    policy_str = generate_lifecycle_policy_json([rule])
    
    parsed = json.loads(policy_str)
    assert "Rules" in parsed
    assert len(parsed["Rules"]) == 1
    assert parsed["Rules"][0]["ID"] == "JsonRule"

def test_dry_run_lifecycle_policy():
    rule = build_lifecycle_rule(
        rule_id="BackupRule",
        prefix="backups/",
        min_object_size=131072, # 128KB
        days_to_ia=30,
        days_to_glacier=90,
        days_to_deep_archive=180
    )
    
    sample_data = [
        {"Key": "backups/db1.bak", "AgeDays": 200, "Size": 5 * 1024 * 1024, "StorageClass": "STANDARD"},
        {"Key": "backups/small.bak", "AgeDays": 200, "Size": 50 * 1024, "StorageClass": "STANDARD"}, # <128KB
        {"Key": "other/file.txt", "AgeDays": 200, "Size": 5 * 1024 * 1024, "StorageClass": "STANDARD"}
    ]
    df = pd.DataFrame(sample_data)

    result = dry_run_lifecycle_policy(df, [rule])
    
    assert result["total_evaluated"] == 3
    assert result["affected_count"] == 1 # Only backups/db1.bak
    assert result["small_objects_protected"] == 1 # backups/small.bak protected
    assert result["transitions_by_tier"].get("DEEP_ARCHIVE") == 1
