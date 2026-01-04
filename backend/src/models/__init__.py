"""
SQLAlchemy models for photo-admin application.

This module provides the declarative base class and imports all models
to ensure they are registered with SQLAlchemy's metadata.
"""

import enum
from sqlalchemy.orm import declarative_base

# Create the declarative base class
# All models will inherit from this Base class
Base = declarative_base()


# ============================================================================
# Shared Enums
# ============================================================================


class ResultStatus(enum.Enum):
    """Status of an analysis result after tool execution."""
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ToolType(enum.Enum):
    """Available analysis tools."""
    PHOTOSTATS = "photostats"
    PHOTO_PAIRING = "photo_pairing"
    PIPELINE_VALIDATION = "pipeline_validation"


# Import all models here so they are registered with Base.metadata
# This is required for Alembic autogenerate to detect models

# Connector and Collection models (User Story 1)
from backend.src.models.connector import Connector, ConnectorType
from backend.src.models.collection import Collection, CollectionType, CollectionState

# Future models (will be imported as they are created):
# from backend.src.models.configuration import Configuration
# from backend.src.models.pipeline import Pipeline, PipelineHistory
# from backend.src.models.analysis_result import AnalysisResult

# Export Base and all models
__all__ = [
    "Base",
    "Connector",
    "ConnectorType",
    "Collection",
    "CollectionType",
    "CollectionState",
    "ResultStatus",
    "ToolType",
]
