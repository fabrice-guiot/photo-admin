"""
Abstract base class for remote storage adapters.

Defines the interface for accessing remote storage systems (S3, GCS, SMB).
All concrete adapters must implement list_files() and test_connection() methods.

Design Pattern: Strategy pattern for pluggable storage backends
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple


class StorageAdapter(ABC):
    """
    Abstract base class for remote storage adapters.

    Provides a common interface for accessing different remote storage systems.
    Concrete implementations handle protocol-specific details (boto3, google-cloud-storage, smbprotocol).

    Methods:
        list_files(): List all files in the storage location
        test_connection(): Validate credentials and connectivity

    Usage:
        >>> adapter = S3Adapter(credentials)
        >>> files = adapter.list_files(location="bucket-name/prefix")
        >>> success, message = adapter.test_connection()
    """

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize storage adapter with credentials.

        Args:
            credentials: Decrypted credentials dictionary
                S3: {"aws_access_key_id": "...", "aws_secret_access_key": "...", "region": "us-west-2"}
                GCS: {"service_account_json": "..."}
                SMB: {"server": "...", "share": "...", "username": "...", "password": "..."}
        """
        self.credentials = credentials

    @abstractmethod
    def list_files(self, location: str) -> List[str]:
        """
        List all files at the specified location.

        Args:
            location: Storage location path
                S3: "bucket-name/optional/prefix"
                GCS: "bucket-name/optional/prefix"
                SMB: "/share-path/optional/prefix"

        Returns:
            List of file paths relative to location

        Raises:
            ConnectionError: If cannot connect to remote storage
            PermissionError: If credentials lack necessary permissions
            ValueError: If location is invalid

        Example:
            >>> files = adapter.list_files("my-bucket/photos")
            >>> print(files)
            ['photo1.jpg', 'photo2.dng', 'subfolder/photo3.jpg']
        """
        pass

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to remote storage and validate credentials.

        Performs a lightweight operation to verify:
        - Credentials are valid
        - Network connectivity exists
        - Required permissions are present

        Returns:
            Tuple of (success: bool, message: str)
                success: True if connection successful, False otherwise
                message: Success message or error description

        Example:
            >>> success, message = adapter.test_connection()
            >>> if success:
            >>>     print(f"Connected: {message}")
            >>> else:
            >>>     print(f"Failed: {message}")
        """
        pass
