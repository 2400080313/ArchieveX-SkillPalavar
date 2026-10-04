"""
ArchiveX - AWS S3 Integration Client
Handles authentication, safe read operations, dry-run guards, and confirmation-enforced modifications.
No credentials are hardcoded.
"""
import os
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError, EndpointConnectionError
from config import DEFAULT_REGION, get_config_val

class S3ClientManager:
    """Safe wrapper around AWS Boto3 SDK with guardrails and demo fallback."""
    
    def __init__(
        self,
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        region_name: Optional[str] = None
    ):
        self.region = region_name or get_config_val("AWS_DEFAULT_REGION", DEFAULT_REGION)
        self.aws_access_key = aws_access_key or get_config_val("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = aws_secret_key or get_config_val("AWS_SECRET_ACCESS_KEY")
        self.aws_session_token = aws_session_token or get_config_val("AWS_SESSION_TOKEN")
        self._s3_client = None
        self._sts_client = None

    def _get_session(self) -> boto3.Session:
        if self.aws_access_key and self.aws_secret_key:
            return boto3.Session(
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                aws_session_token=self.aws_session_token if self.aws_session_token else None,
                region_name=self.region
            )
        return boto3.Session(region_name=self.region)

    def get_s3(self):
        if not self._s3_client:
            session = self._get_session()
            self._s3_client = session.client("s3")
        return self._s3_client

    def get_sts(self):
        if not self._sts_client:
            session = self._get_session()
            self._sts_client = session.client("sts")
        return self._sts_client

    def test_connection(self) -> Dict[str, Any]:
        """Validates credentials via STS get_caller_identity."""
        try:
            sts = self.get_sts()
            identity = sts.get_caller_identity()
            return {
                "success": True,
                "account": identity.get("Account"),
                "arn": identity.get("Arn"),
                "user_id": identity.get("UserId"),
                "message": "AWS connection verified successfully."
            }
        except (NoCredentialsError, PartialCredentialsError):
            return {
                "success": False,
                "message": "No AWS credentials found. Please provide valid AWS credentials or use Demo Mode."
            }
        except ClientError as e:
            return {
                "success": False,
                "message": f"AWS ClientError: {e.response.get('Error', {}).get('Message', str(e))}"
            }
        except EndpointConnectionError:
            return {
                "success": False,
                "message": "Could not connect to AWS endpoint. Check network connection or region."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Unexpected error connecting to AWS: {str(e)}"
            }

    def list_buckets(self) -> List[Dict[str, Any]]:
        """Lists user's S3 buckets."""
        s3 = self.get_s3()
        response = s3.list_buckets()
        buckets = []
        for b in response.get("Buckets", []):
            buckets.append({
                "name": b["Name"],
                "creation_date": b["CreationDate"].isoformat(),
                "region": self.region
            })
        return buckets

    def list_objects(self, bucket_name: str, prefix: str = "", max_keys: int = 1000) -> List[Dict[str, Any]]:
        """Lists objects within a bucket up to max_keys."""
        s3 = self.get_s3()
        paginator = s3.get_paginator("list_objects_v2")
        results = []
        count = 0

        for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
            for item in page.get("Contents", []):
                results.append({
                    "Key": item["Key"],
                    "Size": item["Size"],
                    "LastModified": item["LastModified"].isoformat(),
                    "LastModified_dt": item["LastModified"],
                    "StorageClass": item.get("StorageClass", "STANDARD"),
                    "ETag": item.get("ETag", ""),
                    "BucketName": bucket_name
                })
                count += 1
                if count >= max_keys:
                    return results
        return results

    def get_bucket_lifecycle(self, bucket_name: str) -> Optional[Dict[str, Any]]:
        """Safely fetches existing lifecycle configuration."""
        s3 = self.get_s3()
        try:
            return s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NoSuchLifecycleConfiguration":
                return None
            raise

    def apply_lifecycle_policy(
        self,
        bucket_name: str,
        lifecycle_rules: List[Dict[str, Any]],
        confirmed: bool = False,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Applies a lifecycle policy to a live bucket.
        STRICT GUARDRAIL: Requires confirmed=True AND dry_run=False.
        """
        if dry_run or not confirmed:
            return {
                "status": "DRY_RUN_ONLY",
                "bucket": bucket_name,
                "rule_count": len(lifecycle_rules),
                "message": "Dry-run verification completed. No AWS modifications were made because confirmation was not explicitly authorized."
            }

        s3 = self.get_s3()
        try:
            s3.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration={"Rules": lifecycle_rules}
            )
            return {
                "status": "APPLIED_SUCCESSFULLY",
                "bucket": bucket_name,
                "rule_count": len(lifecycle_rules),
                "message": f"Successfully published {len(lifecycle_rules)} lifecycle rules to AWS bucket '{bucket_name}'."
            }
        except Exception as e:
            return {
                "status": "FAILED",
                "bucket": bucket_name,
                "error": str(e)
            }
