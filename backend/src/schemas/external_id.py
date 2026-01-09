"""
Pydantic schemas for external ID validation and response formatting.

These schemas provide validation for external ID strings and serve as
base classes for entity response schemas.
"""

import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

# Crockford Base32 pattern (excludes I, L, O, U)
EXTERNAL_ID_PATTERN = re.compile(
    r"^(col|con|pip|res)_[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{26}$",
    re.IGNORECASE
)


class ExternalIdField(BaseModel):
    """
    Schema mixin providing external_id field validation.

    The external_id field is validated to ensure:
    1. Correct format: {prefix}_{26-char base32}
    2. Valid prefix (col, con, pip, res)
    3. Valid Crockford Base32 characters

    Example:
        class MyEntityResponse(ExternalIdField):
            name: str
    """

    external_id: Annotated[
        str,
        Field(
            description="External identifier in format {prefix}_{base32_uuid}",
            examples=["col_01HGW2BBG0000000000000000"],
            min_length=30,  # 3 (prefix) + 1 (_) + 26 (base32)
            max_length=30,
        )
    ]

    @field_validator("external_id", mode="before")
    @classmethod
    def validate_external_id_format(cls, v: str) -> str:
        """Validate external ID format."""
        if v is None:
            return v

        if not isinstance(v, str):
            raise ValueError("External ID must be a string")

        if not EXTERNAL_ID_PATTERN.match(v):
            raise ValueError(
                f"Invalid external ID format: {v}. "
                f"Expected format: {{prefix}}_{{26-char base32}}"
            )

        return v.lower()  # Normalize to lowercase


class ExternalIdResponse(BaseModel):
    """
    Base response schema including external_id.

    All entity response schemas should either inherit from this
    or include the external_id field.

    Example:
        class CollectionResponse(ExternalIdResponse):
            id: int
            name: str
            # ... other fields
    """

    external_id: str = Field(
        ...,
        description="External identifier in format {prefix}_{base32_uuid}",
        examples=["col_01HGW2BBG0000000000000000"]
    )

    model_config = {"from_attributes": True}


class ExternalIdRequest(BaseModel):
    """
    Request schema for endpoints accepting external IDs.

    Use this for path/query parameters that require an external ID.

    Example:
        @router.get("/{external_id}")
        async def get_by_external_id(
            external_id: ExternalIdRequest = Depends()
        ):
            ...
    """

    external_id: Annotated[
        str,
        Field(
            description="External identifier",
            examples=["col_01HGW2BBG0000000000000000"],
            pattern=r"^(col|con|pip|res)_[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{26}$"
        )
    ]


# Type aliases for clarity in annotations
ExternalId = Annotated[
    str,
    Field(
        description="External identifier in format {prefix}_{base32_uuid}",
        min_length=30,
        max_length=30
    )
]

# Specific entity external ID types with prefix validation
CollectionExternalId = Annotated[
    str,
    Field(
        description="Collection external identifier",
        pattern=r"^col_[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{26}$"
    )
]

ConnectorExternalId = Annotated[
    str,
    Field(
        description="Connector external identifier",
        pattern=r"^con_[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{26}$"
    )
]

PipelineExternalId = Annotated[
    str,
    Field(
        description="Pipeline external identifier",
        pattern=r"^pip_[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{26}$"
    )
]

AnalysisResultExternalId = Annotated[
    str,
    Field(
        description="Analysis result external identifier",
        pattern=r"^res_[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{26}$"
    )
]
