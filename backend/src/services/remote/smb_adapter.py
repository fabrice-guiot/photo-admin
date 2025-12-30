"""
SMB/CIFS network share adapter implementation.

Provides access to SMB/CIFS network shares using smbprotocol library.
Implements retry logic for transient network failures.
"""

import time
from typing import List, Dict, Any, Tuple

from smbclient import (
    register_session,
    listdir,
    stat,
    SMBConnectionClosed,
    SMBAuthenticationError,
    SMBOSError
)

from backend.src.services.remote.base import StorageAdapter
from backend.src.utils.logging_config import get_logger


logger = get_logger("services")


class SMBAdapter(StorageAdapter):
    """
    SMB/CIFS network share adapter.

    Implements remote file access for SMB/CIFS network shares (Windows shares, NAS, Samba).
    Uses smbprotocol library with retry logic for network reliability.

    Credentials Format:
        {
            "server": "192.168.1.100" or "nas.local",
            "share": "photos",
            "username": "user",
            "password": "pass",
            "port": 445  # Optional, defaults to 445
        }

    Features:
        - Retry logic for transient network failures (3 attempts)
        - Recursive directory traversal
        - Session management and connection pooling
        - Comprehensive error handling with actionable messages

    Usage:
        >>> credentials = {"server": "nas.local", "share": "photos", "username": "user", "password": "pass"}
        >>> adapter = SMBAdapter(credentials)
        >>> files = adapter.list_files("/2024/vacation")
        >>> success, msg = adapter.test_connection()
    """

    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0  # seconds
    BACKOFF_MULTIPLIER = 2.0

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize SMB adapter with credentials.

        Args:
            credentials: Dictionary with server, share, username, password, and optional port

        Raises:
            ValueError: If required credential keys are missing
        """
        super().__init__(credentials)

        # Validate required credentials
        required = ["server", "share", "username", "password"]
        for key in required:
            if key not in credentials:
                raise ValueError(f"Missing required credential: {key}")

        self.server = credentials["server"]
        self.share = credentials["share"]
        self.username = credentials["username"]
        self.password = credentials["password"]
        self.port = credentials.get("port", 445)

        # Register SMB session for connection pooling
        try:
            register_session(
                server=self.server,
                username=self.username,
                password=self.password,
                port=self.port
            )
        except Exception as e:
            raise ValueError(f"Failed to register SMB session: {str(e)}")

    def _list_directory_recursive(self, path: str) -> List[str]:
        """
        Recursively list all files in a directory.

        Args:
            path: SMB path in UNC format (//server/share/path)

        Returns:
            List of file paths relative to the share root
        """
        files = []

        try:
            entries = listdir(path)

            for entry in entries:
                full_path = f"{path}/{entry}"

                # Get file stats to determine if it's a file or directory
                try:
                    file_stat = stat(full_path)

                    # Check if it's a directory (mode & 0o040000)
                    if file_stat.st_mode & 0o040000:
                        # Recursively list subdirectory
                        files.extend(self._list_directory_recursive(full_path))
                    else:
                        # It's a file, add to list (remove //server/share/ prefix)
                        relative_path = full_path.replace(f"//{self.server}/{self.share}/", "")
                        files.append(relative_path)

                except SMBOSError as e:
                    # Skip files/dirs we can't access
                    logger.warning(
                        f"Cannot access SMB path: {full_path}",
                        extra={"error": str(e)}
                    )
                    continue

        except SMBOSError as e:
            logger.error(f"Error listing SMB directory: {path}", extra={"error": str(e)})
            raise

        return files

    def list_files(self, location: str) -> List[str]:
        """
        List all files in SMB share/path.

        Implements recursive directory traversal with retry logic.

        Args:
            location: SMB path relative to share (e.g., "/2024/vacation" or "")

        Returns:
            List of file paths relative to share root

        Raises:
            ConnectionError: If cannot connect after retries
            PermissionError: If credentials lack access permissions
            ValueError: If location is invalid

        Example:
            >>> files = adapter.list_files("/photos/2024")
            >>> print(files)
            ['photos/2024/IMG_001.jpg', 'photos/2024/IMG_002.dng']
        """
        # Build UNC path: //server/share/location
        location = location.lstrip("/")  # Remove leading slash
        unc_path = f"//{self.server}/{self.share}"
        if location:
            unc_path = f"{unc_path}/{location}"

        files = []

        for attempt in range(self.MAX_RETRIES):
            try:
                files = self._list_directory_recursive(unc_path)

                logger.info(
                    f"Listed {len(files)} files from SMB",
                    extra={
                        "server": self.server,
                        "share": self.share,
                        "location": location,
                        "file_count": len(files)
                    }
                )
                return files

            except SMBAuthenticationError as e:
                logger.error("SMB authentication failed", extra={"server": self.server, "error": str(e)})
                raise PermissionError(
                    f"SMB authentication failed for {self.server}/{self.share}. "
                    f"Check username and password: {str(e)}"
                )

            except SMBConnectionClosed as e:
                # Retry connection errors
                if attempt < self.MAX_RETRIES - 1:
                    backoff = self.INITIAL_BACKOFF * (self.BACKOFF_MULTIPLIER ** attempt)
                    logger.warning(
                        f"SMB list_files attempt {attempt + 1} failed, retrying in {backoff}s",
                        extra={"error": str(e), "server": self.server}
                    )
                    time.sleep(backoff)

                    # Re-register session after connection closed
                    try:
                        register_session(
                            server=self.server,
                            username=self.username,
                            password=self.password,
                            port=self.port
                        )
                    except Exception as re_reg_error:
                        logger.error(f"Failed to re-register SMB session: {str(re_reg_error)}")
                else:
                    logger.error(f"SMB list_files failed after {self.MAX_RETRIES} attempts")
                    raise ConnectionError(
                        f"Failed to list SMB share {self.server}/{self.share} "
                        f"after {self.MAX_RETRIES} attempts. Last error: {str(e)}"
                    )

            except SMBOSError as e:
                logger.error(f"SMB file system error: {str(e)}", extra={"path": unc_path})
                if "No such file or directory" in str(e):
                    raise ValueError(f"SMB path not found: {unc_path}")
                elif "Permission denied" in str(e):
                    raise PermissionError(f"Access denied to SMB path: {unc_path}")
                else:
                    raise ConnectionError(f"SMB error: {str(e)}")

            except Exception as e:
                logger.error(f"SMB unexpected error: {str(e)}", extra={"server": self.server})
                raise ConnectionError(f"Unexpected error accessing SMB share: {str(e)}")

        return files

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test SMB connection by listing the share root.

        Validates credentials and network connectivity.

        Returns:
            Tuple of (success: bool, message: str)

        Example:
            >>> success, message = adapter.test_connection()
            >>> print(f"SMB connection: {message}")
        """
        try:
            # List root of share to test connection (lightweight operation)
            unc_path = f"//{self.server}/{self.share}"
            entries = listdir(unc_path)
            entry_count = len(entries)

            logger.info(
                "SMB connection test successful",
                extra={"server": self.server, "share": self.share, "entry_count": entry_count}
            )
            return True, f"Connected to SMB share //{self.server}/{self.share}. Found {entry_count} items."

        except SMBAuthenticationError as e:
            logger.error("SMB authentication failed", extra={"server": self.server, "error": str(e)})
            return False, f"Authentication failed. Check username and password: {str(e)}"

        except SMBConnectionClosed as e:
            logger.error("SMB connection closed", extra={"server": self.server, "error": str(e)})
            return False, f"Cannot connect to SMB server {self.server}. Check server address and port {self.port}: {str(e)}"

        except SMBOSError as e:
            logger.error("SMB file system error", extra={"server": self.server, "error": str(e)})
            if "No such file or directory" in str(e):
                return False, f"SMB share '{self.share}' not found on server {self.server}"
            elif "Permission denied" in str(e):
                return False, f"Access denied to share '{self.share}'. Check permissions."
            else:
                return False, f"SMB error: {str(e)}"

        except Exception as e:
            logger.error("SMB connection test unexpected error", extra={"server": self.server, "error": str(e)})
            return False, f"Unexpected error testing SMB connection: {str(e)}"
