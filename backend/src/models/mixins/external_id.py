"""
External ID mixin for SQLAlchemy models.

Provides UUID-based external identifiers for user-facing entities.
Uses UUIDv7 (time-ordered) with Crockford's Base32 encoding for URL-safe,
human-readable identifiers.

External ID Format: {prefix}_{base32_uuid}
Examples:
    - col_01HGW2BBG0000000000000000 (Collection)
    - con_01HGW2BBG0000000000000001 (Connector)
    - pip_01HGW2BBG0000000000000002 (Pipeline)
    - res_01HGW2BBG0000000000000003 (AnalysisResult)
"""

import uuid as uuid_module
from typing import ClassVar

import base32_crockford
from sqlalchemy import Column, LargeBinary
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid_extensions import uuid7


class ExternalIdMixin:
    """
    Mixin providing external ID (UUID) support for entities.

    Adds:
    - uuid: Binary UUID column (UUIDv7, time-ordered)
    - external_id: Property returning prefixed Base32 string
    - parse_external_id: Class method to decode external ID strings

    Usage:
        class MyEntity(Base, ExternalIdMixin):
            EXTERNAL_ID_PREFIX = "mye"
            # ... other columns

        entity = MyEntity()
        print(entity.external_id)  # mye_01HGW2BBG...

    Entity Prefixes:
        - col: Collection
        - con: Connector
        - pip: Pipeline
        - res: AnalysisResult
    """

    # Abstract: Subclasses must define their 3-character prefix
    EXTERNAL_ID_PREFIX: ClassVar[str]

    # UUID column definition
    # PostgreSQL: Native UUID type for efficiency
    # SQLite: LargeBinary(16) for test compatibility
    uuid = Column(
        PG_UUID(as_uuid=True).with_variant(LargeBinary(16), "sqlite"),
        nullable=False,
        unique=True,
        index=True,
        default=lambda: uuid7()
    )

    @property
    def external_id(self) -> str:
        """
        Get the full external ID with prefix.

        Returns:
            External ID in format {prefix}_{base32_uuid}
            Example: col_01HGW2BBG0000000000000000

        Note:
            The UUID is encoded using Crockford's Base32 encoding which:
            - Is case-insensitive
            - Excludes confusing characters (I, L, O, U)
            - Is URL-safe without encoding
        """
        if self.uuid is None:
            return None

        # Handle both UUID objects and bytes (SQLite compatibility)
        if isinstance(self.uuid, bytes):
            uuid_bytes = self.uuid
        else:
            uuid_bytes = self.uuid.bytes

        encoded = base32_crockford.encode(int.from_bytes(uuid_bytes, "big"))
        # Pad to 26 characters (full UUIDv7 encoding)
        encoded = encoded.zfill(26)
        return f"{self.EXTERNAL_ID_PREFIX}_{encoded.lower()}"

    @classmethod
    def parse_external_id(cls, external_id: str) -> uuid_module.UUID:
        """
        Parse an external ID string to a UUID object.

        Args:
            external_id: External ID string (e.g., "col_01HGW2BBG...")

        Returns:
            UUID object

        Raises:
            ValueError: If the external ID format is invalid or prefix doesn't match
        """
        if not external_id:
            raise ValueError("External ID cannot be empty")

        expected_prefix = f"{cls.EXTERNAL_ID_PREFIX}_"
        if not external_id.lower().startswith(expected_prefix.lower()):
            raise ValueError(
                f"Invalid prefix for {cls.__name__}. "
                f"Expected '{cls.EXTERNAL_ID_PREFIX}', got '{external_id.split('_')[0]}'"
            )

        # Extract the encoded part after the prefix
        encoded_part = external_id[len(expected_prefix):]

        if len(encoded_part) != 26:
            raise ValueError(
                f"Invalid external ID length. Expected 26 characters after prefix, "
                f"got {len(encoded_part)}"
            )

        try:
            # Decode from Crockford Base32 (case-insensitive)
            uuid_int = base32_crockford.decode(encoded_part.upper())
            uuid_bytes = uuid_int.to_bytes(16, "big")
            return uuid_module.UUID(bytes=uuid_bytes)
        except (ValueError, OverflowError) as e:
            raise ValueError(f"Invalid external ID encoding: {e}")

    @classmethod
    def get_uuid_from_external_id(cls, external_id: str) -> uuid_module.UUID:
        """
        Alias for parse_external_id for backward compatibility.

        Args:
            external_id: External ID string

        Returns:
            UUID object
        """
        return cls.parse_external_id(external_id)
