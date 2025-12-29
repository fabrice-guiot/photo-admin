# Data Model: Remote Photo Collections and Analysis Persistence

**Feature**: 004-remote-photos-persistence
**Date**: 2025-12-29
**Status**: Phase 1 Design

## Overview

This document defines the SQLAlchemy data models for the photo-admin web application, covering all entities identified in the feature specification. The schema uses PostgreSQL with JSONB columns for flexible storage of analysis results, pipeline configurations, and nested configuration values.

**Key Design Decisions** (from research.md):
- PostgreSQL 12+ with JSONB columns and GIN indexes for efficient querying
- Fernet encryption for remote collection credentials (stored as encrypted strings)
- Schema versioning in analysis results for tool evolution
- State machine transitions for Collection (Live/Closed/Archived) and AnalysisResult (pending/running/completed/failed)

## Entity Relationship Diagram

```text
┌─────────────┐         ┌─────────────┐         ┌──────────────────┐
│  Connector  │1──────n│ Collection  │1──────n│ AnalysisResult   │
│             │         │             │         │                  │
│ - id        │         │ - id        │         │ - id             │
│ - name      │         │ - name      │         │ - collection_id  │
│ - type      │         │ - type      │         │ - tool           │
│ - credentials│        │ - location  │         │ - pipeline_id    │
│   (encrypted)│        │ - state     │         │ - results (JSONB)│
│ - ...       │         │ - connector_id        │ - report_html    │
└─────────────┘         │ - ...       │         │ - status         │
                        └─────────────┘         └──────────────────┘
                                                       │
                                                       │n (nullable)
                                                       │
┌─────────────┐         ┌──────────────────┐         ┌──────────────────┐
│Configuration│         │ PipelineHistory  │n──────1│  Pipeline        │
│             │         │                  │         │                  │
│ - id        │         │ - id             │         │ - id             │
│ - key       │         │ - pipeline_id    │         │ - name           │
│ - value     │         │ - version.       │         │ - config (JSONB) │
│   (JSONB)   │         │ - config (JSONB) │         │ - is_active      │
│ - ...       │         │ - changed_at     │         │ - version        │
└─────────────┘         └──────────────────┘         └──────────────────┘
```

**Relationships**:
- Connector → Collection (1:n, RESTRICT delete - cannot delete connector with active collections)
- Collection → AnalysisResult (1:n, cascade delete)
- Pipeline → AnalysisResult (1:n, nullable foreign key, no cascade)
- Pipeline → PipelineHistory (1:n, cascade delete)

## SQLAlchemy Models

### 1. Connector Model

Represents authentication credentials for accessing remote storage systems. Multiple collections can share one connector.

```python
# backend/src/models/connector.py

from sqlalchemy import Column, Integer, String, DateTime, Enum, JSONB, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

class ConnectorType(enum.Enum):
    """Remote storage connector type"""
    S3 = "s3"
    GCS = "gcs"
    SMB = "smb"

class Connector(Base):
    """Remote storage connector model"""
    __tablename__ = "connectors"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core fields
    name = Column(String(255), unique=True, nullable=False, index=True)
    # Example names: "Personal AWS Account", "Work GCS Project", "NAS Storage"

    type = Column(Enum(ConnectorType), nullable=False, index=True)

    # Credentials (encrypted with Fernet)
    credentials = Column(Text, nullable=False)  # Encrypted JSON string
    # Example decrypted values by type:
    # S3: {"aws_access_key_id": "...", "aws_secret_access_key": "...", "region": "us-west-2"}
    # GCS: {"service_account_json": "{...}"}
    # SMB: {"username": "...", "password": "...", "domain": "..."}

    # Connection metadata
    metadata_json = Column(JSONB, nullable=True)  # Type-specific connection parameters
    # Example S3 metadata: {"endpoint_url": "https://custom-s3.example.com", "use_ssl": true}
    # Example GCS metadata: {"project_id": "my-project"}
    # Example SMB metadata: {"server": "nas.example.com", "port": 445}

    # Status tracking
    is_active = Column(Boolean, default=True)  # Allow disabling without deletion
    last_validated = Column(DateTime, nullable=True)  # Last successful connection test
    last_error = Column(Text, nullable=True)  # Last connection error message

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    collections = relationship(
        "Collection",
        back_populates="connector",
        lazy="dynamic"  # Enable filtering in queries
    )

    # Indexes
    __table_args__ = (
        Index("idx_connector_type", "type"),  # Filter by connector type
        Index("idx_connector_active", "is_active"),  # Filter active connectors
    )

    def __repr__(self):
        return f"<Connector(id={self.id}, name='{self.name}', type={self.type})>"
```

**Design Rationale**:
- **Credential Reuse**: Multiple collections (e.g., 50 S3 buckets) share one connector → one set of credentials
- **Easier Key Rotation**: Master key rotation only re-encrypts Connector table (not every Collection)
- **Clearer Organization**: Users can see which collections share the same cloud account
- **Future-Proof**: Enables connector-level access control for multi-user support

**Constraints**:
- `name` must be unique (UNIQUE constraint) - user-friendly identifier
- `type` must be valid enum value (S3, GCS, SMB)
- `credentials` required and must be encrypted
- `is_active` allows soft-delete (disable without removing collections)

---

### 2. Collection Model

Represents a photo storage location (local filesystem or remote cloud storage).

```python
# backend/src/models/collection.py

from sqlalchemy import Column, Integer, String, DateTime, Enum, JSONB, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

class CollectionType(enum.Enum):
    """Collection storage type"""
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    SMB = "smb"

class CollectionState(enum.Enum):
    """Collection lifecycle state (determines cache TTL)"""
    LIVE = "Live"        # Active work: 1-hour cache TTL (default 3600s)
    CLOSED = "Closed"    # Infrequent changes: 24-hour cache TTL (default 86400s)
    ARCHIVED = "Archived"  # Infrastructure monitoring: 7-day cache TTL (default 604800s)

class Collection(Base):
    """Photo collection model"""
    __tablename__ = "collections"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    connector_id = Column(
        Integer,
        ForeignKey("connectors.id", ondelete="RESTRICT"),
        nullable=True,  # NULL for local collections, required for remote
        index=True
    )

    # Core fields
    name = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(Enum(CollectionType), nullable=False)
    location = Column(Text, nullable=False)  # Filesystem path or URI (s3://bucket/prefix, gs://bucket/path, smb://share/path)
    state = Column(Enum(CollectionState), nullable=False, default=CollectionState.LIVE)

    # Cache configuration
    cache_ttl = Column(Integer, nullable=True)  # User-override for cache TTL (seconds), NULL = use state default

    # Status tracking
    is_accessible = Column(Boolean, default=True)
    last_error = Column(Text, nullable=True)  # Last accessibility error message

    # Metadata
    metadata_json = Column(JSONB, nullable=True)  # User-defined metadata (tags, notes)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    connector = relationship("Connector", back_populates="collections")

    analysis_results = relationship(
        "AnalysisResult",
        back_populates="collection",
        cascade="all, delete-orphan",  # Delete results when collection deleted
        lazy="dynamic"  # Enable filtering in queries
    )

    # Indexes
    __table_args__ = (
        Index("idx_collection_state", "state"),  # Filter by state
        Index("idx_collection_type", "type"),    # Filter by type
        Index("idx_collection_accessible", "is_accessible"),  # Filter inaccessible collections
    )

    def get_effective_cache_ttl(self) -> int:
        """Get cache TTL (user override or state default)"""
        if self.cache_ttl is not None:
            return self.cache_ttl

        # State defaults (from research.md Task 3)
        STATE_TTL_DEFAULTS = {
            CollectionState.LIVE: 3600,      # 1 hour
            CollectionState.CLOSED: 86400,   # 24 hours
            CollectionState.ARCHIVED: 604800 # 7 days
        }
        return STATE_TTL_DEFAULTS[self.state]

    def __repr__(self):
        return f"<Collection(id={self.id}, name='{self.name}', type={self.type}, state={self.state})>"
```

**State Transition Rules**:
- Live → Closed: Cache TTL changes from 1hr to 24hr (if no user override)
- Closed → Archived: Cache TTL changes from 24hr to 7 days (if no user override)
- Any state can be set manually by user
- State transition invalidates existing cache entries

**Constraints**:
- `name` must be unique (UNIQUE constraint)
- `type` must be valid enum value
- `state` must be valid enum value
- `cache_ttl` if provided must be positive integer
- `connector_id` required for remote types (S3, GCS, SMB), NULL for LOCAL
- `connector_id` uses RESTRICT on delete (cannot delete connector if collections reference it)

---

### 3. AnalysisResult Model

Represents a single execution of an analysis tool (PhotoStats, Photo Pairing, Pipeline Validation).

```python
# backend/src/models/analysis_result.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSONB, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

class ToolType(enum.Enum):
    """Analysis tool type"""
    PHOTOSTATS = "photostats"
    PHOTO_PAIRING = "photo_pairing"
    PIPELINE_VALIDATION = "pipeline_validation"

class AnalysisStatus(enum.Enum):
    """Analysis execution status"""
    PENDING = "pending"      # Job queued but not started
    RUNNING = "running"      # Job currently executing
    COMPLETED = "completed"  # Job finished successfully
    FAILED = "failed"        # Job failed with error
    CANCELLED = "cancelled"  # Job cancelled by user

class AnalysisResult(Base):
    """Analysis execution result model"""
    __tablename__ = "analysis_results"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    collection_id = Column(Integer, ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id", ondelete="SET NULL"), nullable=True, index=True)
    # pipeline_id: NULL for PhotoStats/Photo Pairing, populated for Pipeline Validation

    # Tool identification
    tool = Column(Enum(ToolType), nullable=False, index=True)

    # Execution tracking
    job_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID for job queue
    status = Column(Enum(AnalysisStatus), nullable=False, default=AnalysisStatus.PENDING, index=True)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Results storage (JSONB with schema versioning)
    results = Column(JSONB, nullable=True)  # Full analysis output (NULL while pending/running)
    schema_version = Column(String(20), nullable=True)  # e.g., "1.0.0" for version tracking

    # Pre-generated HTML report (TEXT for large content)
    report_html = Column(Text, nullable=True)  # Generated using Jinja2 templates

    # Error handling
    error_message = Column(Text, nullable=True)  # Error details if status=FAILED

    # Progress tracking (updated during execution)
    progress = Column(JSONB, nullable=True, default={})
    # Example: {"files_scanned": 1500, "issues_found": 12, "stage": "Scanning photos", "percent_complete": 30}

    # Relationships
    collection = relationship("Collection", back_populates="analysis_results")
    pipeline = relationship("Pipeline", back_populates="analysis_results")

    # Indexes
    __table_args__ = (
        Index("idx_analysis_collection_tool", "collection_id", "tool"),  # Filter by collection+tool
        Index("idx_analysis_executed_desc", "executed_at", postgresql_ops={"executed_at": "DESC"}),  # Recent first
        Index("idx_analysis_results_gin", "results", postgresql_using="gin"),  # JSONB queries (trend analysis)
    )

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, tool={self.tool}, status={self.status}, collection_id={self.collection_id})>"
```

**JSONB Schema Examples** (by tool):

```json
// PhotoStats (schema_version: "1.0.0")
{
  "schema_version": "1.0.0",
  "tool": "photostats",
  "summary": {
    "total_files": 5000,
    "orphaned_files_count": 12,
    "missing_sidecars_count": 3,
    "cameras_found": ["AB3D", "CD5E"]
  },
  "orphaned_files": ["AB3D0001.jpg", "AB3D0002.tiff"],
  "missing_sidecars": ["AB3D0003.cr3"],
  "camera_breakdown": {
    "AB3D": {"total": 2500, "orphaned": 5},
    "CD5E": {"total": 2500, "orphaned": 7}
  }
}

// Photo Pairing (schema_version: "1.0.0")
{
  "schema_version": "1.0.0",
  "tool": "photo_pairing",
  "summary": {
    "total_files": 3000,
    "camera_groups": 2,
    "processing_methods": ["HDR", "BW", "Pano"],
    "validation_status": "PARTIAL"
  },
  "camera_groups": [
    {
      "camera_id": "AB3D",
      "camera_name": "Canon EOS R5",
      "file_count": 1500,
      "processing_breakdown": {"HDR": 800, "BW": 500, "Pano": 200}
    }
  ],
  "processing_methods": {
    "HDR": {"count": 800, "description": "High Dynamic Range"},
    "BW": {"count": 500, "description": "Black and White"}
  }
}

// Pipeline Validation (schema_version: "1.0.0")
{
  "schema_version": "1.0.0",
  "tool": "pipeline_validation",
  "pipeline_id": 5,
  "pipeline_name": "Standard Workflow",
  "summary": {
    "total_image_groups": 500,
    "consistent_count": 450,
    "partial_count": 40,
    "inconsistent_count": 10,
    "consistency_percentage": 90.0
  },
  "validation_details": {
    "CONSISTENT": 450,
    "PARTIAL": 40,
    "INCONSISTENT": 10
  },
  "archival_readiness": {
    "Archive": {"ready": 450, "not_ready": 50},
    "Delete": {"ready": 0, "not_ready": 0}
  },
  "image_groups": [
    {
      "group_id": "AB3D0001",
      "status": "CONSISTENT",
      "files": ["AB3D0001.dng", "AB3D0001-HDR.jpg", "AB3D0001.xmp"]
    }
  ]
}
```

**Status State Transitions**:
```text
PENDING → RUNNING → COMPLETED
                 ↓
                FAILED

PENDING → CANCELLED (if job cancelled before execution)
```

**Cascade Behavior**:
- Collection deleted → All AnalysisResults deleted (CASCADE)
- Pipeline deleted → AnalysisResult.pipeline_id set to NULL (SET NULL)

---

### 4. Configuration Model

Represents global configuration settings (photo extensions, camera mappings, processing methods).

```python
# backend/src/models/configuration.py

from sqlalchemy import Column, Integer, String, DateTime, JSONB, Text
from datetime import datetime

class Configuration(Base):
    """Global configuration key-value store"""
    __tablename__ = "configurations"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Configuration key (unique identifier)
    key = Column(String(255), unique=True, nullable=False, index=True)
    # Examples: "photo_extensions", "metadata_extensions", "camera_mappings", "processing_methods"

    # Configuration value (JSONB for nested structures)
    value = Column(JSONB, nullable=False)
    # Supports lists, dicts, nested objects

    # Documentation
    description = Column(Text, nullable=True)

    # Metadata
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Configuration(key='{self.key}', value={self.value})>"
```

**Configuration Key Examples**:

```python
# photo_extensions
{
  "key": "photo_extensions",
  "value": [".dng", ".cr3", ".tiff", ".jpg"],
  "description": "Recognized photo file extensions"
}

# metadata_extensions
{
  "key": "metadata_extensions",
  "value": [".xmp"],
  "description": "Sidecar metadata file extensions"
}

# camera_mappings
{
  "key": "camera_mappings",
  "value": {
    "AB3D": [
      {
        "name": "Canon EOS R5",
        "serial_number": "12345"
      }
    ],
    "CD5E": [
      {
        "name": "Nikon Z9",
        "serial_number": "67890"
      }
    ]
  },
  "description": "Camera ID to device mapping"
}

# processing_methods
{
  "key": "processing_methods",
  "value": {
    "HDR": "High Dynamic Range",
    "BW": "Black and White",
    "Pano": "Panorama Stitching"
  },
  "description": "Processing method descriptions"
}
```

**Constraints**:
- `key` must be unique (UNIQUE constraint)
- `value` must be valid JSONB (not NULL)

**Migration from YAML**:
- YAML config.yaml structure directly maps to Configuration rows
- Top-level YAML keys become Configuration.key
- YAML values (lists, dicts) become Configuration.value (JSONB)

---

### 5. Pipeline Model

Represents a photo processing workflow definition (nodes and edges).

```python
# backend/src/models/pipeline.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSONB, Text
from sqlalchemy.orm import relationship
from datetime import datetime

class Pipeline(Base):
    """Photo processing pipeline definition"""
    __tablename__ = "pipelines"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core fields
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Pipeline structure (JSONB for nodes and edges)
    config = Column(JSONB, nullable=False)
    # Schema: {"nodes": {...}, "edges": [...]}

    # Activation status (only one active pipeline at a time)
    is_active = Column(Boolean, default=False, nullable=False, index=True)

    # Versioning
    version = Column(Integer, default=1, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    history = relationship(
        "PipelineHistory",
        back_populates="pipeline",
        cascade="all, delete-orphan",  # Delete history when pipeline deleted
        order_by="PipelineHistory.version.desc()",  # Recent versions first
        lazy="dynamic"
    )
    analysis_results = relationship(
        "AnalysisResult",
        back_populates="pipeline",
        lazy="dynamic"
    )

    # Indexes
    __table_args__ = (
        Index("idx_pipeline_active", "is_active"),  # Query active pipeline
    )

    def __repr__(self):
        return f"<Pipeline(id={self.id}, name='{self.name}', version={self.version}, is_active={self.is_active})>"
```

**Pipeline Config Schema** (JSONB):

```json
{
  "nodes": {
    "capture1": {
      "type": "Capture",
      "properties": {}
    },
    "file1": {
      "type": "File",
      "properties": {
        "file_extension": ".dng"
      }
    },
    "process1": {
      "type": "Process",
      "properties": {
        "processing_method": "HDR"
      }
    },
    "pairing1": {
      "type": "Pairing",
      "properties": {
        "separator": "-"
      }
    },
    "branching1": {
      "type": "Branching",
      "properties": {
        "branch_type": "alternate"
      }
    },
    "term1": {
      "type": "Termination",
      "properties": {
        "termination_type": "Archive"
      }
    }
  },
  "edges": [
    {
      "source": "capture1",
      "target": "file1"
    },
    {
      "source": "file1",
      "target": "process1"
    },
    {
      "source": "process1",
      "target": "pairing1"
    },
    {
      "source": "pairing1",
      "target": "branching1"
    },
    {
      "source": "branching1",
      "target": "term1"
    }
  ]
}
```

**Activation Rules**:
- Only one pipeline can have `is_active=True` at a time
- Activating a pipeline sets all other pipelines to `is_active=False`
- Pipeline Validation tool uses the active pipeline by default

**Versioning Strategy**:
- Each save increments `version` field
- Previous version saved to PipelineHistory table
- Version history enables rollback and change tracking

---

### 6. PipelineHistory Model

Represents historical versions of pipeline configurations.

```python
# backend/src/models/pipeline.py (continued)

class PipelineHistory(Base):
    """Pipeline configuration version history"""
    __tablename__ = "pipeline_history"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    pipeline_id = Column(Integer, ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False, index=True)

    # Version tracking
    version = Column(Integer, nullable=False)

    # Historical config snapshot
    config = Column(JSONB, nullable=False)  # Copy of Pipeline.config at this version

    # Change metadata
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    change_notes = Column(Text, nullable=True)  # Optional user-provided change description

    # Relationships
    pipeline = relationship("Pipeline", back_populates="history")

    # Indexes
    __table_args__ = (
        Index("idx_pipeline_history_pipeline_version", "pipeline_id", "version"),  # Unique version per pipeline
        UniqueConstraint("pipeline_id", "version", name="uq_pipeline_version"),
    )

    def __repr__(self):
        return f"<PipelineHistory(id={self.id}, pipeline_id={self.pipeline_id}, version={self.version})>"
```

**Usage**:
- Before updating Pipeline.config, copy current config to PipelineHistory
- Increment Pipeline.version
- Save new config to Pipeline.config

**Example Workflow**:
1. User edits pipeline (v1 → v2)
2. Backend creates PipelineHistory record: `{pipeline_id: 5, version: 1, config: {...}, changed_at: NOW()}`
3. Backend updates Pipeline: `{id: 5, version: 2, config: {...new config...}}`

---

## Database Indexes

### Primary Indexes (Performance Optimization)

```sql
-- Collection indexes
CREATE INDEX idx_collection_state ON collections(state);
CREATE INDEX idx_collection_type ON collections(type);
CREATE INDEX idx_collection_accessible ON collections(is_accessible);
CREATE UNIQUE INDEX idx_collection_name ON collections(name);

-- AnalysisResult indexes
CREATE INDEX idx_analysis_collection ON analysis_results(collection_id);
CREATE INDEX idx_analysis_tool ON analysis_results(tool);
CREATE INDEX idx_analysis_status ON analysis_results(status);
CREATE INDEX idx_analysis_job_id ON analysis_results(job_id);
CREATE INDEX idx_analysis_collection_tool ON analysis_results(collection_id, tool);
CREATE INDEX idx_analysis_executed_desc ON analysis_results(executed_at DESC);

-- JSONB GIN index for trend analysis queries
CREATE INDEX idx_analysis_results_gin ON analysis_results USING GIN (results);

-- Configuration indexes
CREATE UNIQUE INDEX idx_configuration_key ON configurations(key);

-- Pipeline indexes
CREATE UNIQUE INDEX idx_pipeline_name ON pipelines(name);
CREATE INDEX idx_pipeline_active ON pipelines(is_active);

-- PipelineHistory indexes
CREATE INDEX idx_pipeline_history_pipeline ON pipeline_history(pipeline_id);
CREATE UNIQUE INDEX uq_pipeline_version ON pipeline_history(pipeline_id, version);
```

### Query Performance Targets (from NFR1.2)

- Collection listing: <2s for 100 collections
- Historical result queries: <1s for 1000+ results
- Trend analysis (JSONB queries): <1s for 10+ executions

### GIN Index Usage Examples

```sql
-- Find all PhotoStats results with orphaned_files_count > 10
SELECT id, collection_id, executed_at,
       (results->'summary'->>'orphaned_files_count')::int as count
FROM analysis_results
WHERE tool = 'photostats'
  AND (results->'summary'->>'orphaned_files_count')::int > 10;

-- Trend analysis: orphaned files over time for collection
SELECT executed_at,
       (results->'summary'->>'orphaned_files_count')::int as count
FROM analysis_results
WHERE collection_id = ? AND tool = 'photostats' AND status = 'completed'
ORDER BY executed_at DESC
LIMIT 10;
```

---

## Schema Migration Notes (Alembic)

### Initial Migration (v1)

```python
# backend/src/db/migrations/versions/001_initial_schema.py

def upgrade():
    # Create collections table
    op.create_table(
        'collections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.Enum('local', 's3', 'gcs', 'smb', name='collectiontype'), nullable=False),
        sa.Column('location', sa.Text(), nullable=False),
        sa.Column('state', sa.Enum('Live', 'Closed', 'Archived', name='collectionstate'), nullable=False),
        sa.Column('cache_ttl', sa.Integer(), nullable=True),
        sa.Column('credentials', sa.Text(), nullable=True),
        sa.Column('is_accessible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create analysis_results table
    op.create_table(
        'analysis_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('pipeline_id', sa.Integer(), nullable=True),
        sa.Column('tool', sa.Enum('photostats', 'photo_pairing', 'pipeline_validation', name='tooltype'), nullable=False),
        sa.Column('job_id', sa.String(36), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='analysisstatus'), nullable=False),
        sa.Column('executed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('results', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('schema_version', sa.String(20), nullable=True),
        sa.Column('report_html', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('progress', sa.dialects.postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )

    # Create configurations table
    op.create_table(
        'configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )

    # Create pipelines table
    op.create_table(
        'pipelines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create pipeline_history table
    op.create_table(
        'pipeline_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pipeline_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('config', sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('change_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pipeline_id', 'version', name='uq_pipeline_version')
    )

    # Create all indexes (see "Database Indexes" section above)

def downgrade():
    op.drop_table('pipeline_history')
    op.drop_table('pipelines')
    op.drop_table('configurations')
    op.drop_table('analysis_results')
    op.drop_table('collections')
    # Drop enums
    op.execute('DROP TYPE IF EXISTS collectiontype')
    op.execute('DROP TYPE IF EXISTS collectionstate')
    op.execute('DROP TYPE IF EXISTS tooltype')
    op.execute('DROP TYPE IF EXISTS analysisstatus')
```

### Schema Evolution Strategy

**JSONB Schema Versioning**:
- All JSONB columns with variable schemas include `schema_version` field
- Backend services check version when parsing results
- Forward compatibility: Ignore unknown fields
- Backward compatibility: Provide defaults for missing fields

**Migration Examples**:

```python
# Example: Add new field to PhotoStats results schema (v1.0.0 → v1.1.0)

def upgrade():
    # No migration needed! JSONB schema versioning handles this:
    # 1. Tool starts emitting schema_version "1.1.0" with new field
    # 2. Old results (v1.0.0) remain queryable
    # 3. Backend handles both versions gracefully
    pass

# Example: Add new enum value to CollectionType (e.g., "azure")

def upgrade():
    # Add new enum value
    op.execute("ALTER TYPE collectiontype ADD VALUE 'azure'")

# Example: Add new column to Collection model

def upgrade():
    op.add_column('collections', sa.Column('file_count_cache', sa.Integer(), nullable=True))
    op.create_index('idx_collection_file_count', 'collections', ['file_count_cache'])
```

---

## Constraints and Validation

### Database-Level Constraints

```sql
-- Collections
ALTER TABLE collections ADD CONSTRAINT chk_cache_ttl_positive CHECK (cache_ttl IS NULL OR cache_ttl > 0);

-- AnalysisResult
ALTER TABLE analysis_results ADD CONSTRAINT chk_completed_at_after_started
  CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at);

-- Pipeline
ALTER TABLE pipelines ADD CONSTRAINT chk_version_positive CHECK (version > 0);

-- PipelineHistory
ALTER TABLE pipeline_history ADD CONSTRAINT chk_version_positive CHECK (version > 0);
```

### Application-Level Validation (Pydantic)

See `contracts/openapi.yaml` for Pydantic schema definitions.

---

## Cross-Platform Encoding

**CRITICAL**: All file operations and database text encoding MUST use UTF-8 (Constitution: Cross-Platform File Encoding).

```python
# Example: Store report_html
with open(report_path, 'r', encoding='utf-8') as f:
    report_html = f.read()
    analysis_result.report_html = report_html

# Example: Write exported YAML
with open(output_path, 'w', encoding='utf-8') as f:
    yaml.safe_dump(config_data, f, allow_unicode=True)
```

---

## Pipeline Processor (`utils/pipeline_processor.py`)

**Critical Shared Component**: The pipeline processor is the core engine for all pipeline graph operations, used by both backend API and CLI tools. This enforces the Constitution principle of shared infrastructure.

### Purpose

Provides centralized logic for:
1. Pipeline structure validation (cycles, orphaned nodes, invalid references)
2. Filename preview generation (expected files per pipeline)
3. Collection validation (match files to pipeline graph)
4. Archival readiness calculation (completion metrics)

### Core Classes

#### 1. PipelineGraph

Represents pipeline configuration as a traversable directed graph.

```python
from typing import Dict, List, Set, Optional
from dataclasses import dataclass

@dataclass
class Node:
    """Represents a pipeline node"""
    id: str
    type: str  # Capture, File, Process, Pairing, Branching, Termination
    properties: Dict[str, any]  # Node-specific properties

@dataclass
class Edge:
    """Represents a pipeline edge"""
    source_id: str
    target_id: str
    properties: Dict[str, any]  # Edge-specific properties

class PipelineGraph:
    """Pipeline configuration as directed graph"""

    def __init__(self, config: dict):
        """
        Initialize from pipeline config JSONB.

        Args:
            config: Pipeline config with 'nodes' and 'edges' keys
        """
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.adjacency: Dict[str, Set[str]] = {}  # node_id -> set of child node_ids
        self.reverse_adjacency: Dict[str, Set[str]] = {}  # node_id -> set of parent node_ids

        self._parse_config(config)

    def _parse_config(self, config: dict):
        """Parse JSONB config into graph structure"""
        # Build nodes map
        for node_data in config['nodes']:
            node = Node(
                id=node_data['id'],
                type=node_data['type'],
                properties=node_data.get('properties', {})
            )
            self.nodes[node.id] = node

        # Build edges and adjacency lists
        for edge_data in config['edges']:
            edge = Edge(
                source_id=edge_data['source'],
                target_id=edge_data['target'],
                properties=edge_data.get('properties', {})
            )
            self.edges.append(edge)

            # Update adjacency
            if edge.source_id not in self.adjacency:
                self.adjacency[edge.source_id] = set()
            self.adjacency[edge.source_id].add(edge.target_id)

            # Update reverse adjacency
            if edge.target_id not in self.reverse_adjacency:
                self.reverse_adjacency[edge.target_id] = set()
            self.reverse_adjacency[edge.target_id].add(edge.source_id)

    def get_children(self, node_id: str) -> Set[str]:
        """Get child node IDs"""
        return self.adjacency.get(node_id, set())

    def get_parents(self, node_id: str) -> Set[str]:
        """Get parent node IDs"""
        return self.reverse_adjacency.get(node_id, set())

    def get_nodes_by_type(self, node_type: str) -> List[Node]:
        """Get all nodes of a specific type"""
        return [node for node in self.nodes.values() if node.type == node_type]

    def topological_sort(self) -> Optional[List[str]]:
        """
        Perform topological sort using Kahn's algorithm.

        Returns:
            Sorted node IDs if graph is acyclic, None if cycles exist
        """
        in_degree = {node_id: len(self.get_parents(node_id)) for node_id in self.nodes}
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        sorted_nodes = []

        while queue:
            node_id = queue.pop(0)
            sorted_nodes.append(node_id)

            for child_id in self.get_children(node_id):
                in_degree[child_id] -= 1
                if in_degree[child_id] == 0:
                    queue.append(child_id)

        # If all nodes processed, no cycles
        return sorted_nodes if len(sorted_nodes) == len(self.nodes) else None

    def dfs_from_nodes(self, start_nodes: List[str]) -> Set[str]:
        """
        Depth-first search from starting nodes.

        Args:
            start_nodes: List of node IDs to start from

        Returns:
            Set of all reachable node IDs
        """
        visited = set()

        def dfs(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            for child_id in self.get_children(node_id):
                dfs(child_id)

        for node_id in start_nodes:
            dfs(node_id)

        return visited
```

#### 2. StructureValidator

Validates pipeline graph structure (FR-028).

```python
from typing import List, Dict

class ValidationError:
    """Represents a validation error"""
    def __init__(self, error_type: str, message: str, node_ids: List[str] = None):
        self.error_type = error_type
        self.message = message
        self.node_ids = node_ids or []

class StructureValidator:
    """Validates pipeline structure"""

    def __init__(self, graph: PipelineGraph, config_service=None):
        """
        Initialize validator.

        Args:
            graph: Pipeline graph to validate
            config_service: Service for checking processing_methods (optional)
        """
        self.graph = graph
        self.config_service = config_service

    def validate(self) -> List[ValidationError]:
        """
        Validate entire pipeline structure.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for cycles
        cycles = self.detect_cycles()
        if cycles:
            errors.append(ValidationError(
                'cycle',
                f'Graph contains {len(cycles)} cycle(s)',
                cycles
            ))

        # Check for orphaned nodes
        orphaned = self.find_orphaned_nodes()
        if orphaned:
            errors.append(ValidationError(
                'orphaned_nodes',
                f'Found {len(orphaned)} orphaned node(s): {", ".join(orphaned)}',
                orphaned
            ))

        # Check for dead-end nodes
        dead_ends = self.find_dead_ends()
        if dead_ends:
            errors.append(ValidationError(
                'dead_ends',
                f'Found {len(dead_ends)} node(s) with no path to termination',
                dead_ends
            ))

        # Validate node-specific constraints
        node_errors = self.validate_nodes()
        errors.extend(node_errors)

        # Validate property references
        if self.config_service:
            ref_errors = self.validate_property_references()
            errors.extend(ref_errors)

        return errors

    def detect_cycles(self) -> List[str]:
        """
        Detect cycles using topological sort.

        Returns:
            List of node IDs involved in cycles
        """
        sorted_nodes = self.graph.topological_sort()
        if sorted_nodes is None:
            # Cycles exist - find nodes not in any valid sort
            all_nodes = set(self.graph.nodes.keys())
            # Return nodes that couldn't be sorted
            return list(all_nodes)  # Simplified - full impl would trace cycles
        return []

    def find_orphaned_nodes(self) -> List[str]:
        """
        Find nodes unreachable from Capture nodes.

        Returns:
            List of orphaned node IDs
        """
        capture_nodes = [n.id for n in self.graph.get_nodes_by_type('Capture')]
        if not capture_nodes:
            return list(self.graph.nodes.keys())  # All orphaned if no Capture

        reachable = self.graph.dfs_from_nodes(capture_nodes)
        all_nodes = set(self.graph.nodes.keys())
        orphaned = all_nodes - reachable

        return list(orphaned)

    def find_dead_ends(self) -> List[str]:
        """
        Find nodes with no path to Termination.

        Returns:
            List of dead-end node IDs
        """
        termination_nodes = [n.id for n in self.graph.get_nodes_by_type('Termination')]
        if not termination_nodes:
            # All non-termination nodes are dead-ends
            return [n.id for n in self.graph.nodes.values() if n.type != 'Termination']

        # Reverse DFS from Termination nodes
        reverse_graph_adjacency = self.graph.reverse_adjacency
        visited = set()

        def reverse_dfs(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            for parent_id in self.graph.get_parents(node_id):
                reverse_dfs(parent_id)

        for term_id in termination_nodes:
            reverse_dfs(term_id)

        all_nodes = set(self.graph.nodes.keys())
        dead_ends = all_nodes - visited

        return list(dead_ends)

    def validate_nodes(self) -> List[ValidationError]:
        """
        Validate node-specific constraints.

        Returns:
            List of validation errors
        """
        errors = []

        for node in self.graph.nodes.values():
            if node.type == 'Capture':
                # Must be root (no incoming edges)
                if self.graph.get_parents(node.id):
                    errors.append(ValidationError(
                        'invalid_capture',
                        f'Capture node "{node.id}" has incoming edges',
                        [node.id]
                    ))

            elif node.type == 'File':
                # Must have extension property
                if 'extension' not in node.properties:
                    errors.append(ValidationError(
                        'missing_extension',
                        f'File node "{node.id}" missing extension property',
                        [node.id]
                    ))

            elif node.type == 'Process':
                # Must have processing_method property
                if 'processing_method' not in node.properties:
                    errors.append(ValidationError(
                        'missing_processing_method',
                        f'Process node "{node.id}" missing processing_method property',
                        [node.id]
                    ))

            elif node.type == 'Pairing':
                # Must have exactly 2 incoming edges
                parents = self.graph.get_parents(node.id)
                if len(parents) != 2:
                    errors.append(ValidationError(
                        'invalid_pairing',
                        f'Pairing node "{node.id}" has {len(parents)} parents (expected 2)',
                        [node.id]
                    ))

            elif node.type == 'Branching':
                # Must have 2+ outgoing edges
                children = self.graph.get_children(node.id)
                if len(children) < 2:
                    errors.append(ValidationError(
                        'invalid_branching',
                        f'Branching node "{node.id}" has {len(children)} children (expected 2+)',
                        [node.id]
                    ))

            elif node.type == 'Termination':
                # Must be leaf (no outgoing edges)
                if self.graph.get_children(node.id):
                    errors.append(ValidationError(
                        'invalid_termination',
                        f'Termination node "{node.id}" has outgoing edges',
                        [node.id]
                    ))

        return errors

    def validate_property_references(self) -> List[ValidationError]:
        """
        Validate that processing_methods exist in configuration.

        Returns:
            List of validation errors
        """
        errors = []

        # Get valid processing methods from config
        valid_methods = self.config_service.get_processing_methods()

        for node in self.graph.nodes.values():
            if node.type == 'Process':
                method = node.properties.get('processing_method')
                if method and method not in valid_methods:
                    errors.append(ValidationError(
                        'invalid_processing_method',
                        f'Process node "{node.id}" references unknown method "{method}"',
                        [node.id]
                    ))

        return errors
```

#### 3. FilenamePreviewGenerator

Generates expected filenames from pipeline graph (FR-031).

```python
class FilenamePreviewGenerator:
    """Generates expected filename patterns from pipeline"""

    def __init__(self, graph: PipelineGraph):
        self.graph = graph

    def generate_preview(self, camera_id: str = "XXXX", counter: str = "0001") -> Dict[str, List[str]]:
        """
        Generate expected filenames per termination type.

        Args:
            camera_id: Example camera ID for preview
            counter: Example counter for preview

        Returns:
            Dict mapping termination_type -> list of expected filename patterns
        """
        previews = {}

        # Find all paths from Capture to Termination
        capture_nodes = self.graph.get_nodes_by_type('Capture')

        for capture in capture_nodes:
            paths = self._find_all_paths(capture.id)

            for path in paths:
                filename = self._apply_path_transformations(path, camera_id, counter)

                # Get termination type
                term_node = self.graph.nodes[path[-1]]
                term_type = term_node.properties.get('type', 'default')

                if term_type not in previews:
                    previews[term_type] = []
                previews[term_type].append(filename)

        return previews

    def _find_all_paths(self, start_node_id: str) -> List[List[str]]:
        """Find all paths from start node to Termination nodes"""
        paths = []

        def dfs(node_id: str, current_path: List[str]):
            current_path = current_path + [node_id]
            node = self.graph.nodes[node_id]

            if node.type == 'Termination':
                paths.append(current_path)
                return

            for child_id in self.graph.get_children(node_id):
                dfs(child_id, current_path)

        dfs(start_node_id, [])
        return paths

    def _apply_path_transformations(self, path: List[str], camera_id: str, counter: str) -> str:
        """Apply node transformations to generate filename"""
        filename = f"{camera_id}{counter}"
        properties = []

        for node_id in path:
            node = self.graph.nodes[node_id]

            if node.type == 'File':
                # Add extension at end
                extension = node.properties.get('extension', '.jpg')
                # Don't add yet - accumulate first

            elif node.type == 'Process':
                # Add processing method property
                method = node.properties.get('processing_method', 'PROC')
                properties.append(method)

            elif node.type == 'Pairing':
                # Add pairing variant (e.g., -2 for second file)
                variant = node.properties.get('variant', '2')
                properties.append(variant)

        # Build final filename
        if properties:
            filename += '-' + '-'.join(properties)

        # Add extension (from last File node in path)
        for node_id in reversed(path):
            node = self.graph.nodes[node_id]
            if node.type == 'File':
                extension = node.properties.get('extension', '.jpg')
                filename += extension
                break

        return filename
```

#### 4. CollectionValidator

Validates collection files against pipeline (FR-048).

```python
from dataclasses import dataclass
from enum import Enum

class ImageGroupStatus(Enum):
    """Status of image group relative to pipeline"""
    CONSISTENT = "consistent"
    PARTIAL = "partial"
    INCONSISTENT = "inconsistent"

@dataclass
class ImageGroup:
    """Group of files with same base (camera_id + counter)"""
    base: str  # e.g., "AB3D0001"
    files: List[str]
    status: ImageGroupStatus
    completed_nodes: Set[str]
    missing_files: List[str]

class CollectionValidator:
    """Validates collection against pipeline"""

    def __init__(self, graph: PipelineGraph, files: List[str]):
        self.graph = graph
        self.files = files
        self.image_groups: Dict[str, ImageGroup] = {}

    def validate(self) -> Dict[str, any]:
        """
        Validate collection against pipeline.

        Returns:
            Validation results with CONSISTENT/PARTIAL/INCONSISTENT breakdowns
        """
        # Group files by base filename
        self._group_files()

        # Validate each group
        for group in self.image_groups.values():
            self._validate_group(group)

        # Calculate summary statistics
        summary = {
            'total_groups': len(self.image_groups),
            'consistent': sum(1 for g in self.image_groups.values() if g.status == ImageGroupStatus.CONSISTENT),
            'partial': sum(1 for g in self.image_groups.values() if g.status == ImageGroupStatus.PARTIAL),
            'inconsistent': sum(1 for g in self.image_groups.values() if g.status == ImageGroupStatus.INCONSISTENT),
            'groups': [self._serialize_group(g) for g in self.image_groups.values()]
        }

        return summary

    def _group_files(self):
        """Group files by base filename (camera_id + counter)"""
        from utils.filename_parser import FilenameParser

        for file in self.files:
            parsed = FilenameParser.parse_filename(file)
            if parsed:
                base = f"{parsed['camera_id']}{parsed['counter']}"
                if base not in self.image_groups:
                    self.image_groups[base] = ImageGroup(
                        base=base,
                        files=[],
                        status=ImageGroupStatus.INCONSISTENT,
                        completed_nodes=set(),
                        missing_files=[]
                    )
                self.image_groups[base].files.append(file)

    def _validate_group(self, group: ImageGroup):
        """Validate a single image group against pipeline"""
        # Determine which nodes this group has completed
        # by matching files against expected patterns
        # (Simplified - full implementation would trace paths)

        expected_files = self._get_expected_files_for_base(group.base)

        present = set(group.files)
        expected = set(expected_files.keys())

        if present == expected:
            group.status = ImageGroupStatus.CONSISTENT
            group.completed_nodes = set(expected_files.values())
        elif present & expected:  # Some overlap
            group.status = ImageGroupStatus.PARTIAL
            group.completed_nodes = {expected_files[f] for f in present & expected}
            group.missing_files = list(expected - present)
        else:
            group.status = ImageGroupStatus.INCONSISTENT

    def _get_expected_files_for_base(self, base: str) -> Dict[str, str]:
        """
        Get expected files for a base filename.

        Returns:
            Dict mapping expected_filename -> node_id that produces it
        """
        # Traverse pipeline and generate expected files
        # (Simplified placeholder - full impl uses FilenamePreviewGenerator logic)
        return {}

    def _serialize_group(self, group: ImageGroup) -> dict:
        """Serialize ImageGroup for JSON response"""
        return {
            'base': group.base,
            'files': group.files,
            'status': group.status.value,
            'completed_nodes': list(group.completed_nodes),
            'missing_files': group.missing_files
        }
```

#### 5. ReadinessCalculator

Calculates archival readiness metrics (FR-049).

```python
class ReadinessCalculator:
    """Calculates archival readiness per termination type"""

    def __init__(self, graph: PipelineGraph, validation_results: Dict[str, any]):
        self.graph = graph
        self.results = validation_results

    def calculate(self) -> Dict[str, any]:
        """
        Calculate archival readiness.

        Returns:
            Metrics per termination type
        """
        termination_nodes = self.graph.get_nodes_by_type('Termination')
        readiness = {}

        for term_node in termination_nodes:
            term_type = term_node.properties.get('type', 'default')

            # Count groups reaching this termination
            reaching = self._count_groups_reaching_node(term_node.id)
            total = self.results['total_groups']

            readiness[term_type] = {
                'total_groups': total,
                'complete_groups': reaching,
                'percentage': (reaching / total * 100) if total > 0 else 0,
                'incomplete_groups': total - reaching
            }

        return readiness

    def _count_groups_reaching_node(self, node_id: str) -> int:
        """Count image groups that have reached this node"""
        count = 0
        for group in self.results['groups']:
            if node_id in group['completed_nodes']:
                count += 1
        return count
```

### Testing Strategy

**Unit Tests** (`tests/unit/test_pipeline_processor.py`):
- PipelineGraph parsing and traversal
- Cycle detection algorithm (various graph structures)
- Orphaned node detection
- Filename generation for all node types
- Collection validation (CONSISTENT/PARTIAL/INCONSISTENT)

**Integration Tests** (`tests/integration/test_pipeline_validation.py`):
- Real pipeline configs from YAML
- Large pipelines (20+ nodes)
- Complex branching and pairing scenarios
- Edge cases: empty pipelines, single-node pipelines

**Performance Tests**:
- Large collections (10K+ files) validation time
- Complex pipeline (20+ nodes) validation time
- Target: <2s for pipeline structure validation

### Usage Examples

```python
# Example 1: Validate pipeline structure (Backend API)
from utils.pipeline_processor import PipelineGraph, StructureValidator

pipeline_config = {
    'nodes': [...],
    'edges': [...]
}

graph = PipelineGraph(pipeline_config)
validator = StructureValidator(graph, config_service)
errors = validator.validate()

if errors:
    return {"valid": False, "errors": [e.__dict__ for e in errors]}
else:
    return {"valid": True}

# Example 2: Generate filename preview (Backend API)
from utils.pipeline_processor import PipelineGraph, FilenamePreviewGenerator

graph = PipelineGraph(pipeline_config)
generator = FilenamePreviewGenerator(graph)
preview = generator.generate_preview(camera_id="AB3D", counter="0001")
# Returns: {"archive": ["AB3D0001-HDR.tiff"], "working": ["AB3D0001-HDR-2.dng"]}

# Example 3: Validate collection (CLI tool)
from utils.pipeline_processor import PipelineGraph, CollectionValidator

files = scan_directory(collection_path)  # List of filenames
graph = PipelineGraph(pipeline_config)
validator = CollectionValidator(graph, files)
results = validator.validate()

print(f"Total: {results['total_groups']}")
print(f"Consistent: {results['consistent']}")
print(f"Partial: {results['partial']}")
print(f"Inconsistent: {results['inconsistent']}")
```

---

## Summary

This data model provides:

- **Flexible analysis storage**: JSONB with schema versioning supports tool evolution
- **Efficient queries**: GIN indexes enable <1s trend analysis for 1000+ results
- **Data consistency**: Foreign key cascades and transactions prevent orphaned records
- **State management**: Clear state transitions for Collection and AnalysisResult
- **Audit trails**: Timestamps and version history for pipelines
- **Security**: Encrypted credentials for remote collections

**Next Steps**:
1. Review this data model for completeness
2. Proceed to API contract design (contracts/openapi.yaml)
3. Generate initial Alembic migration
4. Implement SQLAlchemy models with unit tests
