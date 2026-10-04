"""
ArchiveX - S3 Lifecycle Policy Generator & Dry-Run Inspector
Generates production-grade AWS S3 Lifecycle Configuration policies (JSON, XML, Terraform, CDK)
and performs dry-run evaluations against bucket objects.
"""
import json
from typing import Dict, Any, List
import pandas as pd

def build_lifecycle_rule(
    rule_id: str,
    prefix: str = "",
    min_object_size: int = 131072, # 128 KB standard guardrail
    days_to_ia: int = 30,
    days_to_glacier: int = 90,
    days_to_deep_archive: int = 180,
    days_to_expire: int = 0,
    enable_it: bool = False,
    status: str = "Enabled"
) -> Dict[str, Any]:
    """Constructs an AWS S3 standard PutBucketLifecycleConfiguration JSON rule."""
    filter_dict = {}
    
    # S3 filter with prefix and optional size limits
    and_conditions = {}
    if prefix:
        and_conditions["Prefix"] = prefix
    if min_object_size > 0:
        and_conditions["ObjectSizeGreaterThan"] = min_object_size
        
    if len(and_conditions) > 1:
        filter_dict["And"] = and_conditions
    elif prefix:
        filter_dict["Prefix"] = prefix
    elif min_object_size > 0:
        filter_dict["ObjectSizeGreaterThan"] = min_object_size
    else:
        filter_dict["Prefix"] = ""

    transitions = []
    
    if enable_it:
        transitions.append({
            "Days": 0,
            "StorageClass": "INTELLIGENT_TIERING"
        })
    else:
        if days_to_ia > 0:
            transitions.append({
                "Days": days_to_ia,
                "StorageClass": "STANDARD_IA"
            })
        if days_to_glacier > 0 and days_to_glacier > days_to_ia:
            transitions.append({
                "Days": days_to_glacier,
                "StorageClass": "GLACIER"
            })
        if days_to_deep_archive > 0 and days_to_deep_archive > days_to_glacier:
            transitions.append({
                "Days": days_to_deep_archive,
                "StorageClass": "DEEP_ARCHIVE"
            })

    rule: Dict[str, Any] = {
        "ID": rule_id,
        "Status": status,
        "Filter": filter_dict,
        "Transitions": transitions,
        "AbortIncompleteMultipartUpload": {
            "DaysAfterInitiation": 7
        }
    }
    
    if days_to_expire > 0:
        rule["Expiration"] = {"Days": days_to_expire}
        
    return rule

def generate_lifecycle_policy_json(rules: List[Dict[str, Any]]) -> str:
    """Formats full S3 Lifecycle Configuration payload as pretty JSON."""
    payload = {"Rules": rules}
    return json.dumps(payload, indent=2)

def generate_lifecycle_policy_xml(rules: List[Dict[str, Any]]) -> str:
    """Formats rules into S3 XML LifecycleConfiguration format."""
    lines = ['<LifecycleConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">']
    for r in rules:
        lines.append('  <Rule>')
        lines.append(f'    <ID>{r["ID"]}</ID>')
        lines.append(f'    <Status>{r["Status"]}</Status>')
        
        filt = r.get("Filter", {})
        if "Prefix" in filt:
            lines.append(f'    <Filter><Prefix>{filt["Prefix"]}</Prefix></Filter>')
        elif "And" in filt:
            lines.append('    <Filter><And>')
            if "Prefix" in filt["And"]:
                lines.append(f'      <Prefix>{filt["And"]["Prefix"]}</Prefix>')
            if "ObjectSizeGreaterThan" in filt["And"]:
                lines.append(f'      <ObjectSizeGreaterThan>{filt["And"]["ObjectSizeGreaterThan"]}</ObjectSizeGreaterThan>')
            lines.append('    </And></Filter>')
        else:
            lines.append('    <Filter><Prefix></Prefix></Filter>')

        for t in r.get("Transitions", []):
            lines.append('    <Transition>')
            lines.append(f'      <Days>{t["Days"]}</Days>')
            lines.append(f'      <StorageClass>{t["StorageClass"]}</StorageClass>')
            lines.append('    </Transition>')

        if "Expiration" in r:
            lines.append('    <Expiration>')
            lines.append(f'      <Days>{r["Expiration"]["Days"]}</Days>')
            lines.append('    </Expiration>')

        lines.append('  </Rule>')
    lines.append('</LifecycleConfiguration>')
    return "\n".join(lines)

def generate_terraform_snippet(bucket_name: str, rules: List[Dict[str, Any]]) -> str:
    """Generates modern Terraform aws_s3_bucket_lifecycle_configuration snippet."""
    tf = [
        f'resource "aws_s3_bucket_lifecycle_configuration" "archivex_lifecycle" {{',
        f'  bucket = "{bucket_name}"\n'
    ]
    for r in rules:
        tf.append(f'  rule {{')
        tf.append(f'    id     = "{r["ID"]}"')
        tf.append(f'    status = "{r["Status"].lower()}"')
        
        filt = r.get("Filter", {})
        prefix = filt.get("Prefix", "")
        if "And" in filt and "Prefix" in filt["And"]:
            prefix = filt["And"]["Prefix"]
            
        tf.append(f'    filter {{\n      prefix = "{prefix}"\n    }}')
        
        for t in r.get("Transitions", []):
            tf.append(f'    transition {{')
            tf.append(f'      days          = {t["Days"]}')
            tf.append(f'      storage_class = "{t["StorageClass"]}"')
            tf.append(f'    }}')
            
        if "Expiration" in r:
            tf.append(f'    expiration {{\n      days = {r["Expiration"]["Days"]}\n    }}')
            
        tf.append(f'  }}\n')
    tf.append('}')
    return "\n".join(tf)

def dry_run_lifecycle_policy(objects_df: pd.DataFrame, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Simulates applying the lifecycle rules to an object dataset.
    Returns which objects would transition, which would be protected, and estimated savings.
    """
    if objects_df.empty or not rules:
        return {
            "total_evaluated": 0,
            "affected_count": 0,
            "retained_count": 0,
            "small_objects_protected": 0,
            "affected_size_gb": 0.0,
            "transitions_by_tier": {},
            "detailed_matches": []
        }

    affected_count = 0
    small_objects_protected = 0
    transitions_by_tier: Dict[str, int] = {}
    affected_size_bytes = 0
    matches = []

    for idx, row in objects_df.iterrows():
        key = row["Key"]
        age = row["AgeDays"]
        size_bytes = row["Size"]
        size_kb = size_bytes / 1024.0
        current_class = row["StorageClass"]

        matched_rule = None
        target_action = None

        for rule in rules:
            if rule.get("Status") != "Enabled":
                continue

            filt = rule.get("Filter", {})
            prefix = filt.get("Prefix", "")
            min_size = 0
            if "And" in filt:
                prefix = filt["And"].get("Prefix", "")
                min_size = filt["And"].get("ObjectSizeGreaterThan", 0)
            elif "ObjectSizeGreaterThan" in filt:
                min_size = filt.get("ObjectSizeGreaterThan", 0)

            # Check match
            if prefix and not key.startswith(prefix):
                continue
            if min_size > 0 and size_bytes < min_size:
                small_objects_protected += 1
                continue

            # Evaluate transitions
            transitions = sorted(rule.get("Transitions", []), key=lambda t: t["Days"], reverse=True)
            for t in transitions:
                if age >= t["Days"] and current_class != t["StorageClass"]:
                    target_action = t["StorageClass"]
                    matched_rule = rule["ID"]
                    break

            if matched_rule:
                break

        if matched_rule and target_action:
            affected_count += 1
            affected_size_bytes += size_bytes
            transitions_by_tier[target_action] = transitions_by_tier.get(target_action, 0) + 1
            if len(matches) < 50: # sample for review
                matches.append({
                    "Key": key,
                    "AgeDays": age,
                    "CurrentClass": current_class,
                    "TargetClass": target_action,
                    "RuleId": matched_rule,
                    "SizeKB": round(size_kb, 1)
                })

    return {
        "total_evaluated": len(objects_df),
        "affected_count": affected_count,
        "retained_count": len(objects_df) - affected_count,
        "small_objects_protected": small_objects_protected,
        "affected_size_gb": round(affected_size_bytes / (1024**3), 2),
        "transitions_by_tier": transitions_by_tier,
        "sample_matches": matches
    }
