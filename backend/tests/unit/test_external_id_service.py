"""
Unit tests for ExternalIdService.

Tests cover:
- UUID generation
- External ID encoding/decoding
- Format validation
- Identifier parsing (numeric vs external)
- Error handling
"""

import uuid

import pytest

from backend.src.services.external_id import (
    ExternalIdService,
    ENTITY_PREFIXES,
    EXTERNAL_ID_PATTERN,
)


class TestExternalIdGeneration:
    """Tests for UUID generation."""

    def test_generate_uuid_returns_uuid(self):
        """Test that generate_uuid returns a UUID object."""
        result = ExternalIdService.generate_uuid()
        assert isinstance(result, uuid.UUID)

    def test_generate_uuid_is_unique(self):
        """Test that generated UUIDs are unique."""
        uuids = [ExternalIdService.generate_uuid() for _ in range(100)]
        assert len(set(uuids)) == 100

    def test_generate_uuid_is_version_7(self):
        """Test that generated UUIDs are version 7 (time-ordered)."""
        result = ExternalIdService.generate_uuid()
        # UUIDv7 has version bits set to 0111 (7)
        assert result.version == 7


class TestExternalIdEncoding:
    """Tests for external ID encoding."""

    def test_encode_uuid_with_valid_prefix(self):
        """Test encoding with valid entity prefixes."""
        test_uuid = ExternalIdService.generate_uuid()

        for prefix in ENTITY_PREFIXES.keys():
            result = ExternalIdService.encode_uuid(test_uuid, prefix)
            assert result.startswith(f"{prefix}_")
            assert len(result) == 30  # 3 (prefix) + 1 (_) + 26 (base32)

    def test_encode_uuid_is_lowercase(self):
        """Test that encoded external IDs are lowercase."""
        test_uuid = ExternalIdService.generate_uuid()
        result = ExternalIdService.encode_uuid(test_uuid, "col")
        assert result == result.lower()

    def test_encode_uuid_invalid_prefix(self):
        """Test that invalid prefix raises ValueError."""
        test_uuid = ExternalIdService.generate_uuid()

        with pytest.raises(ValueError) as exc_info:
            ExternalIdService.encode_uuid(test_uuid, "xyz")

        assert "Invalid prefix" in str(exc_info.value)

    def test_encode_uuid_bytes(self):
        """Test encoding UUID from bytes."""
        test_uuid = ExternalIdService.generate_uuid()
        result = ExternalIdService.encode_uuid(test_uuid.bytes, "col")
        assert result.startswith("col_")
        assert len(result) == 30


class TestExternalIdDecoding:
    """Tests for external ID decoding."""

    def test_decode_roundtrip(self):
        """Test that encoding then decoding returns original UUID."""
        original_uuid = ExternalIdService.generate_uuid()

        for prefix in ENTITY_PREFIXES.keys():
            external_id = ExternalIdService.encode_uuid(original_uuid, prefix)
            decoded_prefix, decoded_uuid = ExternalIdService.decode_external_id(
                external_id
            )

            assert decoded_prefix == prefix
            assert decoded_uuid == original_uuid

    def test_decode_case_insensitive(self):
        """Test that decoding is case-insensitive."""
        test_uuid = ExternalIdService.generate_uuid()
        external_id = ExternalIdService.encode_uuid(test_uuid, "col")

        # Test uppercase
        prefix, decoded = ExternalIdService.decode_external_id(external_id.upper())
        assert decoded == test_uuid

        # Test mixed case
        mixed_case = "COL_" + external_id[4:].upper()
        prefix, decoded = ExternalIdService.decode_external_id(mixed_case)
        assert decoded == test_uuid

    def test_decode_empty_string_raises(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ExternalIdService.decode_external_id("")

        assert "cannot be empty" in str(exc_info.value)

    def test_decode_invalid_format_raises(self):
        """Test that invalid format raises ValueError."""
        invalid_ids = [
            "invalid",
            "col_123",  # Too short
            "col_" + "A" * 27,  # Too long
            "xxx_" + "A" * 26,  # Invalid prefix
            "col-" + "A" * 26,  # Wrong separator
        ]

        for invalid_id in invalid_ids:
            with pytest.raises(ValueError):
                ExternalIdService.decode_external_id(invalid_id)

    def test_decode_invalid_base32_raises(self):
        """Test that invalid Base32 characters raise ValueError."""
        # Contains 'I', 'L', 'O', 'U' which are not in Crockford Base32
        invalid_id = "col_ILLOOUU0000000000000000"

        with pytest.raises(ValueError):
            ExternalIdService.decode_external_id(invalid_id)


class TestExternalIdValidation:
    """Tests for external ID validation."""

    def test_validate_valid_external_ids(self):
        """Test validation of valid external IDs."""
        test_uuid = ExternalIdService.generate_uuid()

        for prefix in ENTITY_PREFIXES.keys():
            external_id = ExternalIdService.encode_uuid(test_uuid, prefix)
            assert ExternalIdService.validate_external_id(external_id) is True

    def test_validate_with_expected_prefix(self):
        """Test validation with expected prefix."""
        test_uuid = ExternalIdService.generate_uuid()
        external_id = ExternalIdService.encode_uuid(test_uuid, "col")

        # Correct prefix
        assert ExternalIdService.validate_external_id(external_id, "col") is True

        # Wrong prefix
        assert ExternalIdService.validate_external_id(external_id, "con") is False

    def test_validate_invalid_format(self):
        """Test validation of invalid formats."""
        invalid_ids = [
            "",
            None,
            "invalid",
            "col_123",
            "col_" + "A" * 27,
        ]

        for invalid_id in invalid_ids:
            assert ExternalIdService.validate_external_id(invalid_id) is False


class TestEntityTypeExtraction:
    """Tests for entity type extraction."""

    def test_get_entity_type_valid(self):
        """Test getting entity type from valid external IDs."""
        test_uuid = ExternalIdService.generate_uuid()

        for prefix, entity_type in ENTITY_PREFIXES.items():
            external_id = ExternalIdService.encode_uuid(test_uuid, prefix)
            result = ExternalIdService.get_entity_type(external_id)
            assert result == entity_type

    def test_get_entity_type_invalid(self):
        """Test getting entity type from invalid external IDs."""
        assert ExternalIdService.get_entity_type("") is None
        assert ExternalIdService.get_entity_type("xy") is None
        assert ExternalIdService.get_entity_type("xyz_123") is None


class TestIdentifierParsing:
    """Tests for identifier parsing."""

    def test_is_numeric_id(self):
        """Test numeric ID detection."""
        assert ExternalIdService.is_numeric_id("123") is True
        assert ExternalIdService.is_numeric_id("0") is True
        assert ExternalIdService.is_numeric_id("999999") is True

        assert ExternalIdService.is_numeric_id("") is False
        assert ExternalIdService.is_numeric_id("abc") is False
        assert ExternalIdService.is_numeric_id("col_123") is False

    def test_is_external_id(self):
        """Test external ID detection."""
        test_uuid = ExternalIdService.generate_uuid()
        external_id = ExternalIdService.encode_uuid(test_uuid, "col")

        assert ExternalIdService.is_external_id(external_id) is True
        assert ExternalIdService.is_external_id("123") is False
        assert ExternalIdService.is_external_id("invalid") is False

    def test_parse_identifier_numeric(self):
        """Test parsing numeric identifiers."""
        id_type, value = ExternalIdService.parse_identifier("123")

        assert id_type == "numeric"
        assert value == 123

    def test_parse_identifier_external(self):
        """Test parsing external identifiers."""
        test_uuid = ExternalIdService.generate_uuid()
        external_id = ExternalIdService.encode_uuid(test_uuid, "col")

        id_type, value = ExternalIdService.parse_identifier(external_id)

        assert id_type == "external"
        assert value == test_uuid

    def test_parse_identifier_with_expected_prefix(self):
        """Test parsing with expected prefix validation."""
        test_uuid = ExternalIdService.generate_uuid()
        external_id = ExternalIdService.encode_uuid(test_uuid, "col")

        # Correct prefix
        id_type, value = ExternalIdService.parse_identifier(external_id, "col")
        assert id_type == "external"

        # Wrong prefix
        with pytest.raises(ValueError) as exc_info:
            ExternalIdService.parse_identifier(external_id, "con")

        assert "prefix mismatch" in str(exc_info.value)

    def test_parse_identifier_empty_raises(self):
        """Test that empty identifier raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ExternalIdService.parse_identifier("")

        assert "cannot be empty" in str(exc_info.value)

    def test_parse_identifier_invalid_raises(self):
        """Test that invalid identifier raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ExternalIdService.parse_identifier("invalid_format")

        assert "Invalid identifier format" in str(exc_info.value)


class TestParseExternalId:
    """Tests for parse_external_id convenience method."""

    def test_parse_external_id_valid(self):
        """Test parsing valid external ID."""
        test_uuid = ExternalIdService.generate_uuid()
        external_id = ExternalIdService.encode_uuid(test_uuid, "col")

        result = ExternalIdService.parse_external_id(external_id, "col")
        assert result == test_uuid

    def test_parse_external_id_wrong_prefix_raises(self):
        """Test that wrong prefix raises ValueError."""
        test_uuid = ExternalIdService.generate_uuid()
        external_id = ExternalIdService.encode_uuid(test_uuid, "col")

        with pytest.raises(ValueError):
            ExternalIdService.parse_external_id(external_id, "con")

    def test_parse_external_id_numeric_raises(self):
        """Test that numeric ID raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ExternalIdService.parse_external_id("123", "col")

        assert "Expected external ID" in str(exc_info.value)


class TestExternalIdPattern:
    """Tests for the external ID regex pattern."""

    def test_pattern_matches_valid_ids(self):
        """Test pattern matches valid external IDs."""
        # Note: Crockford Base32 excludes I, L, O, U
        # Each base32 part must be exactly 26 characters
        valid_ids = [
            "col_01234567890abcdefghjkmnpqr",
            "con_ABCDEFGHJKMNPQRSTVWXYZ0123",
            "pip_01hg02bbg00000000000000002",
            "res_01HG02BBG00000000000000003",
        ]

        for valid_id in valid_ids:
            assert EXTERNAL_ID_PATTERN.match(valid_id) is not None

    def test_pattern_rejects_invalid_ids(self):
        """Test pattern rejects invalid external IDs."""
        invalid_ids = [
            "xxx_01234567890abcdefghjkmnpqr",  # Invalid prefix
            "col_0123456789",  # Too short
            "col_01234567890abcdefghjkmnpqrs",  # Too long
            "col-01234567890abcdefghjkmnpqr",  # Wrong separator
            "col_IIIIIIIIIIIIIIIIIIIIIIIIII",  # Contains I (not in Crockford)
            "col_LLLLLLLLLLLLLLLLLLLLLLLLLL",  # Contains L (not in Crockford)
            "col_OOOOOOOOOOOOOOOOOOOOOOOOOO",  # Contains O (not in Crockford)
            "col_UUUUUUUUUUUUUUUUUUUUUUUUUU",  # Contains U (not in Crockford)
        ]

        for invalid_id in invalid_ids:
            assert EXTERNAL_ID_PATTERN.match(invalid_id) is None
