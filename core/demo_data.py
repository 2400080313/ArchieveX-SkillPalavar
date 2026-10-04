"""
ArchiveX - Enterprise Demo Data Generator
Generates realistic, rich enterprise S3 bucket data with varied storage classes,
ages, sizes, tags, and lifecycle states to demonstrate ArchiveX capabilities without AWS credentials.
"""
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import pandas as pd

DEMO_BUCKETS = [
    {
        "name": "enterprise-prod-db-backups-us-east-1",
        "region": "us-east-1",
        "description": "Daily and monthly automated database dumps (PostgreSQL, MySQL, Cassandra).",
        "environment": "Production",
        "owner": "DataPlatform-Team",
        "primary_type": "database_backups"
    },
    {
        "name": "fintech-audit-logs-compliance-2023-2026",
        "region": "us-east-1",
        "description": "Regulatory transaction logs, audit trails, and immutable ledger snapshots.",
        "environment": "Compliance-Locked",
        "owner": "Security-Governance",
        "primary_type": "compliance_logs"
    },
    {
        "name": "media-streaming-transcoded-master-assets",
        "region": "us-west-2",
        "description": "Transcoded 4K/1080p ProRes masters, audio stems, and customer media.",
        "environment": "Production",
        "owner": "Content-Ops",
        "primary_type": "media_assets"
    },
    {
        "name": "ecommerce-web-assets-cdn-origin",
        "region": "us-east-1",
        "description": "Frontend static bundles, product images, thumbnail cache, and assets.",
        "environment": "Production",
        "owner": "Frontend-Team",
        "primary_type": "static_web"
    },
    {
        "name": "iot-fleet-telemetry-raw-ingestion",
        "region": "eu-west-1",
        "description": "Connected device telemetry streams, sensor batch exports, and parquet tables.",
        "environment": "Telemetry",
        "owner": "IoT-Architecture",
        "primary_type": "iot_telemetry"
    }
]

def generate_bucket_objects(bucket_name: str, count: int = 250, seed: int = 42) -> List[Dict[str, Any]]:
    """Generates synthetic S3 objects adhering to realistic enterprise operational patterns."""
    rng = random.Random(seed + hash(bucket_name) % 10000)
    now = datetime.now(timezone.utc)
    objects = []
    
    bucket_info = next((b for b in DEMO_BUCKETS if b["name"] == bucket_name), DEMO_BUCKETS[0])
    b_type = bucket_info["primary_type"]
    
    if b_type == "database_backups":
        prefixes = ["backups/postgres/prod_cluster/", "backups/mysql/billing_db/", "backups/snapshots/monthly/", "snapshots/dr_wal_logs/"]
        exts = [".sql.gz", ".tar.gz", ".bak", ".dump", ".wal.zst"]
        classes = ["STANDARD", "STANDARD", "STANDARD", "STANDARD_IA"]
        size_range = (500 * 1024 * 1024, 65 * 1024 * 1024 * 1024) # 500MB to 65GB
        age_range_days = (15, 850)
        
    elif b_type == "compliance_logs":
        prefixes = ["audit/financial_ledger/2023/", "audit/financial_ledger/2024/", "audit/compliance/pci_dss/", "audit/access_logs/"]
        exts = [".jsonl.gz", ".parquet", ".csv.gz", ".log.gz"]
        classes = ["STANDARD", "STANDARD_IA", "GLACIER"]
        size_range = (40 * 1024 * 1024, 8 * 1024 * 1024 * 1024) # 40MB to 8GB
        age_range_days = (90, 1100)
        
    elif b_type == "media_assets":
        prefixes = ["masters/4k_prores/", "audio/stems_multitrack/", "renders/vfx_passes/", "archive/raw_footage/"]
        exts = [".mov", ".mxf", ".wav", ".mp4", ".braw"]
        classes = ["STANDARD", "INTELLIGENT_TIERING", "STANDARD_IA", "GLACIER_IR"]
        size_range = (250 * 1024 * 1024, 45 * 1024 * 1024 * 1024) # 250MB to 45GB
        age_range_days = (5, 600)
        
    elif b_type == "static_web":
        prefixes = ["cdn/v2.1/js/", "cdn/v2.1/css/", "catalog/products/hires/", "thumbnails/cache/"]
        exts = [".js", ".css", ".webp", ".png", ".jpg", ".svg"]
        classes = ["STANDARD", "STANDARD"]
        size_range = (8 * 1024, 4 * 1024 * 1024) # 8KB to 4MB (Small objects!)
        age_range_days = (1, 120)
        
    else: # iot_telemetry
        prefixes = ["telemetry/raw/stream_a/", "telemetry/raw/stream_b/", "batch_parquet/hourly/", "device_dumps/crashed/"]
        exts = [".parquet", ".json.gz", ".avro", ".bin"]
        classes = ["STANDARD", "STANDARD", "STANDARD_IA"]
        size_range = (90 * 1024, 350 * 1024 * 1024) # 90KB to 350MB
        age_range_days = (2, 450)

    for i in range(count):
        prefix = rng.choice(prefixes)
        ext = rng.choice(exts)
        size_bytes = rng.randint(size_range[0], size_range[1])
        age_days = rng.randint(age_range_days[0], age_range_days[1])
        last_modified = now - timedelta(days=age_days, hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
        storage_class = rng.choice(classes)
        
        # Realistic key naming
        key_id = f"obj_{last_modified.strftime('%Y%m%d')}_{i:05d}{ext}"
        key = f"{prefix}{key_id}"
        
        # Tags
        tags = {
            "Environment": bucket_info["environment"],
            "ManagedBy": "ArchiveX-Automation",
            "Project": bucket_info["owner"]
        }
        if "compliance" in key.lower() or "audit" in key.lower():
            tags["RetentionClass"] = "SEC-17a-4"
        elif "backup" in key.lower():
            tags["BackupType"] = rng.choice(["Full", "Incremental", "Differential"])
            
        objects.append({
            "Key": key,
            "Size": size_bytes,
            "LastModified": last_modified.isoformat(),
            "LastModified_dt": last_modified,
            "AgeDays": age_days,
            "StorageClass": storage_class,
            "ETag": f'"{rng.getrandbits(128):032x}"',
            "BucketName": bucket_name,
            "Tags": tags,
            "IsGlacierRestored": False
        })

    return objects

def get_demo_dataset() -> Dict[str, Any]:
    """Returns all demo buckets and their combined objects."""
    all_objects = []
    bucket_summaries = []
    
    for bucket in DEMO_BUCKETS:
        objs = generate_bucket_objects(bucket["name"], count=220)
        total_size = sum(o["Size"] for o in objs)
        all_objects.extend(objs)
        bucket_summaries.append({
            "name": bucket["name"],
            "region": bucket["region"],
            "description": bucket["description"],
            "environment": bucket["environment"],
            "owner": bucket["owner"],
            "object_count": len(objs),
            "total_size_bytes": total_size,
            "total_size_gb": total_size / (1024**3),
            "total_size_tb": total_size / (1024**4)
        })
        
    df = pd.DataFrame(all_objects)
    return {
        "buckets": bucket_summaries,
        "objects": all_objects,
        "dataframe": df
    }
