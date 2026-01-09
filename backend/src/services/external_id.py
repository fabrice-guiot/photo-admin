"""
External ID service for entity identification.

Provides utilities for generating, encoding, decoding, and validating
external identifiers used in URLs and API responses.

External ID Format: {prefix}_{base32_uuid}
- prefix: 3-character entity type identifier (col, con, pip, res)
- base32_uuid: 26-character Crockford Base32 encoded UUIDv7
"""

import re
import uuid

import base32_crockford
from uuid_extensions import uuid7

# Prefix mappings for entity types
ENTITY_PREFIXES = {
    "col": "Collection",
    "con": "Connector",
    "pip": "Pipeline",
    "res": "AnalysisResult",
}

# Crockford Base32 alphabet (excludes I, L, O, U to avoid confusion)
CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# Pattern for validating external IDs
# Format: {3-char prefix}_{26-char Crockford Base32}
EXTERNAL_ID_PATTERN = re.compile(
    r"^(col|con|pip|res)_[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{26}$",
    re.IGNORECASE
)


class ExternalIdService:
    """
    Service for external ID operations.

    Provides static methods for:
    - Generating new UUIDv7 values
    - Encoding UUIDs to external ID strings
    - Decoding external ID strings to UUIDs
    - Validating external ID format
    - Parsing identifiers (distinguishing external vs numeric IDs)
    """

    @staticmethod
    def generate_uuid() -> uuid.UUID:
        """
        Generate a new UUIDv7 value.

        UUIDv7 is time-ordered for better database indexing performance.

        Returns:
            New UUID object
        """
        return uuid7()

    @staticmethod
    def encode_uuid(uuid_value: uuid.UUID, prefix: str) -> str:
        """
        Encode a UUID to an external ID string.

        Args:
            uuid_value: UUID to encode
            prefix: Entity type prefix (col, con, pip, res)

        Returns:
            External ID string (e.g., "col_01HGW2BBG...")

        Raises:
            ValueError: If prefix is invalid
        """
        if prefix not in ENTITY_PREFIXES:
            raise ValueError(
                f"Invalid prefix '{prefix}'. "
                f"Valid prefixes: {', '.join(ENTITY_PREFIXES.keys())}"
            )

        # Convert UUID to integer and encode as Crockford Base32
        if isinstance(uuid_value, bytes):
            uuid_int = int.from_bytes(uuid_value, "big")
        else:
            uuid_int = int.from_bytes(uuid_value.bytes, "big")

        encoded = base32_crockford.encode(uuid_int)
        # Pad to 26 characters
        encoded = encoded.zfill(26)
        return f"{prefix}_{encoded.lower()}"

    @staticmethod
    def decode_external_id(external_id: str) -> tuple[str, uuid.UUID]:
        """
        Decode an external ID string to its components.

        Args:
            external_id: External ID string (e.g., "col_01HGW2BBG...")

        Returns:
            Tuple of (prefix, UUID)

        Raises:
            ValueError: If the external ID format is invalid
        """
        if not external_id:
            raise ValueError("External ID cannot be empty")

        if not EXTERNAL_ID_PATTERN.match(external_id):
            raise ValueError(
                f"Invalid external ID format: {external_id}. "
                f"Expected format: {{prefix}}_{{26-char base32}}"
            )

        prefix = external_id[:3].lower()
        encoded_part = external_id[4:]  # Skip "xxx_"

        try:
            uuid_int = base32_crockford.decode(encoded_part.upper())
            uuid_bytes = uuid_int.to_bytes(16, "big")
            return prefix, uuid.UUID(bytes=uuid_bytes)
        except (ValueError, OverflowError) as e:
            raise ValueError(f"Invalid external ID encoding: {e}")

    @staticmethod
    def validate_external_id(external_id: str, expected_prefix: str = None) -> bool:
        """
        Validate an external ID format.

        Args:
            external_id: External ID string to validate
            expected_prefix: Optional expected prefix for type checking

        Returns:
            True if valid, False otherwise
        """
        if not external_id:
            return False

        if not EXTERNAL_ID_PATTERN.match(external_id):
            return False

        if expected_prefix:
            prefix = external_id[:3].lower()
            return prefix == expected_prefix.lower()

        return True

    @staticmethod
    def get_entity_type(external_id: str) -> str | None:
        """
        Get the entity type name from an external ID.

        Args:
            external_id: External ID string

        Returns:
            Entity type name (Collection, Connector, etc.) or None if invalid
        """
        if not external_id or len(external_id) < 3:
            return None

        prefix = external_id[:3].lower()
        return ENTITY_PREFIXES.get(prefix)

    @staticmethod
    def is_numeric_id(identifier: str) -> bool:
        """
        Check if an identifier is a numeric ID.

        Args:
            identifier: ID string to check

        Returns:
            True if the identifier is numeric (integer)
        """
        if not identifier:
            return False
        return identifier.isdigit()

    @staticmethod
    def is_external_id(identifier: str) -> bool:
        """
        Check if an identifier is an external ID.

        Args:
            identifier: ID string to check

        Returns:
            True if the identifier matches external ID format
        """
        return ExternalIdService.validate_external_id(identifier)

    @staticmethod
    def parse_identifier(identifier: str, expected_prefix: str = None) -> tuple[str, int | uuid.UUID]:
        """
        Parse an identifier to determine its type and value.

        This method handles both numeric IDs (backward compatibility) and
        external IDs (new format). Useful for API endpoints that accept both.

        Args:
            identifier: ID string (numeric or external)
            expected_prefix: Expected prefix for external IDs (for validation)

        Returns:
            Tuple of (id_type, value) where:
            - id_type: "numeric" or "external"
            - value: int for numeric, UUID for external

        Raises:
            ValueError: If the identifier format is invalid
        """
        if not identifier:
            raise ValueError("Identifier cannot be empty")

        # Check if numeric ID
        if identifier.isdigit():
            return ("numeric", int(identifier))

        # Check if external ID
        if EXTERNAL_ID_PATTERN.match(identifier):
            if expected_prefix:
                prefix = identifier[:3].lower()
                if prefix != expected_prefix.lower():
                    raise ValueError(
                        f"External ID prefix mismatch. "
                        f"Expected '{expected_prefix}', got '{prefix}'"
                    )

            prefix, uuid_value = ExternalIdService.decode_external_id(identifier)
            return ("external", uuid_value)

        raise ValueError(
            f"Invalid identifier format: {identifier}. "
            f"Expected numeric ID or external ID ({{prefix}}_{{base32}})"
        )

    @staticmethod
    def parse_external_id(external_id: str, expected_prefix: str) -> uuid.UUID:
        """
        Parse an external ID string to UUID, validating the prefix.

        Convenience method for service layer lookups.

        Args:
            external_id: External ID string
            expected_prefix: Expected entity prefix

        Returns:
            UUID object

        Raises:
            ValueError: If format invalid or prefix doesn't match
        """
        id_type, value = ExternalIdService.parse_identifier(
            external_id, expected_prefix
        )

        if id_type != "external":
            raise ValueError(f"Expected external ID, got numeric: {external_id}")

        return value
