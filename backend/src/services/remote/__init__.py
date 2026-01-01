"""
Remote storage adapters for accessing S3, GCS, and SMB storage systems.

This package provides a unified interface for accessing different remote storage backends
through the StorageAdapter abstract base class.

Adapters:
- S3Adapter: Amazon S3 and S3-compatible storage (boto3)
- GCSAdapter: Google Cloud Storage (google-cloud-storage)
- SMBAdapter: SMB/CIFS network shares (smbprotocol)

Usage:
    >>> from backend.src.services.remote import S3Adapter
    >>> credentials = {"aws_access_key_id": "...", "aws_secret_access_key": "..."}
    >>> adapter = S3Adapter(credentials)
    >>> files = adapter.list_files("bucket-name/prefix")
    >>> success, message = adapter.test_connection()
"""

from backend.src.services.remote.base import StorageAdapter
from backend.src.services.remote.s3_adapter import S3Adapter
from backend.src.services.remote.gcs_adapter import GCSAdapter
from backend.src.services.remote.smb_adapter import SMBAdapter

__all__ = [
    "StorageAdapter",
    "S3Adapter",
    "GCSAdapter",
    "SMBAdapter",
]
