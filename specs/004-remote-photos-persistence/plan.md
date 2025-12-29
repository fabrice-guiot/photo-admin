# Implementation Plan: Remote Photo Collections and Analysis Persistence

**Branch**: `004-remote-photos-persistence` | **Date**: 2025-12-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-remote-photos-persistence/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Extend photo-admin from local-only CLI tools to a database-backed web application supporting remote photo collections (AWS S3, Google Cloud Storage, SMB/CIFS) with persistent storage of analysis results. Provides React-based web UI for collection management, pipeline configuration, tool execution, and historical trend analysis while maintaining CLI tool compatibility through database fallback to YAML.

**Key Technical Components**:
- **Backend**: FastAPI with PostgreSQL (JSONB for flexible analysis results)
- **Frontend**: React with form-based pipeline editor (v2: React Flow graph editor)
- **Remote Storage**: boto3 (S3), google-cloud-storage (GCS), smbprotocol (SMB)
- **Persistence**: SQLAlchemy ORM with Alembic migrations
- **Real-time Updates**: WebSocket for analysis progress
- **CLI Integration**: Database-first with YAML fallback

## Technical Context

**Language/Version**: Python 3.10+ (backend), JavaScript ES6+ (frontend)
**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy, Alembic, boto3, google-cloud-storage, smbprotocol, pydantic, cryptography, uvicorn
- Frontend: React, React Router, Axios, Recharts/Victory, Material-UI/Ant Design
- Shared: PyYAML (import/export), Jinja2 (report generation), pytest

**Storage**: PostgreSQL 12+ with JSONB columns (collections, configurations, pipelines, analysis_results, pipeline_history)

**Testing**:
- Backend: pytest with database fixtures
- Frontend: Jest/React Testing Library
- Integration: End-to-end tests with real database

**Target Platform**:
- Backend: Cross-platform (Linux, macOS, Windows) via Python 3.10+
- Frontend: Modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Deployment: localhost for v1 (no authentication required)

**Project Type**: Web application (backend + frontend)

**Performance Goals**:
- Collection listing: <2s for 100 collections
- Historical queries: <1s for 1000+ results
- Analysis execution: within 10% of CLI performance
- HTML report generation: <500ms for 1000+ issues
- Remote cache: 80% reduction in API calls

**Constraints**:
- Local-only deployment (no multi-user, no authentication)
- CLI tool performance within 10% of current
- Existing YAML config import with 100% fidelity
- Cross-platform file encoding (explicit UTF-8)
- Database transactions for data consistency

**Scale/Scope**:
- 100+ collections per user
- 1M+ files per collection (remote)
- 1000+ historical analysis results
- Complex pipelines (20+ nodes with branching/pairing)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- [x] **Independent CLI Tools**: This feature EXTENDS existing CLI tools (PhotoStats, Photo Pairing, Pipeline Validation) to read from database with YAML fallback. Existing tools remain standalone and functional.
- [x] **Testing & Quality**: Comprehensive test coverage planned (>80% backend, integration tests, end-to-end). Tests will be written alongside implementation.
- [x] **User-Centric Design**:
  - [x] HTML reports: Reuses existing Jinja2 templates for consistency
  - [x] Error messages: FR-040 stores error details, UI provides actionable guidance
  - [x] Simplicity (YAGNI): Uses FastAPI BackgroundTasks for v1 (defers Celery/RQ until needed)
  - [x] Structured logging: Backend logging for API requests, tool execution, errors
- [x] **Shared Infrastructure**: Uses PhotoAdminConfig, respects existing config schema, maintains standard file locations
- [x] **Simplicity**: Straightforward FastAPI + React architecture, avoids premature abstractions (no complex frameworks)

**Violations/Exceptions**: See Complexity Tracking section below

## Project Structure

### Documentation (this feature)

```text
specs/004-remote-photos-persistence/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── openapi.yaml    # OpenAPI 3.0 spec for REST API
│   └── websocket.md    # WebSocket protocol documentation
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Web application structure (backend + frontend)

backend/
├── src/
│   ├── models/                    # SQLAlchemy models
│   │   ├── connector.py          # Connector, ConnectorType enum (credentials storage)
│   │   ├── collection.py         # Collection, CollectionState enum
│   │   ├── configuration.py      # Configuration key-value
│   │   ├── pipeline.py           # Pipeline, PipelineHistory
│   │   └── analysis_result.py    # AnalysisResult, ToolType enum
│   ├── services/                  # Business logic
│   │   ├── connector_service.py  # Connector CRUD, credential encryption, connection testing
│   │   ├── collection_service.py # Collection CRUD, accessibility checks
│   │   ├── config_service.py     # Config import/export, migration
│   │   ├── pipeline_service.py   # Pipeline CRUD, validation, versioning
│   │   ├── tool_service.py       # Tool execution, job queue
│   │   └── remote/               # Remote storage adapters
│   │       ├── base.py           # Abstract storage adapter
│   │       ├── s3_adapter.py     # AWS S3 integration
│   │       ├── gcs_adapter.py    # Google Cloud Storage
│   │       └── smb_adapter.py    # SMB/CIFS network shares
│   ├── api/                       # FastAPI routes
│   │   ├── collections.py        # Collection endpoints
│   │   ├── config.py             # Configuration endpoints
│   │   ├── pipelines.py          # Pipeline endpoints
│   │   ├── tools.py              # Tool execution endpoints
│   │   └── results.py            # Results visualization endpoints
│   ├── db/                        # Database setup
│   │   ├── database.py           # SQLAlchemy engine, session
│   │   └── migrations/           # Alembic migration scripts
│   ├── schemas/                   # Pydantic schemas for validation
│   │   ├── collection.py         # CollectionCreate, CollectionUpdate
│   │   ├── pipeline.py           # PipelineCreate, PipelineUpdate
│   │   └── analysis.py           # AnalysisRequest, AnalysisResponse
│   ├── utils/                     # Shared utilities
│   │   ├── crypto.py             # Credential encryption/decryption
│   │   ├── cache.py              # File listing cache manager
│   │   └── logging_config.py     # Structured logging setup
│   └── main.py                    # FastAPI application entry point
├── tests/
│   ├── unit/                      # Unit tests
│   │   ├── test_models.py        # Model validation
│   │   ├── test_services.py      # Service logic
│   │   └── test_adapters.py      # Remote storage adapters
│   ├── integration/               # Integration tests
│   │   ├── test_api.py           # API endpoint integration
│   │   └── test_database.py      # Database operations
│   └── e2e/                       # End-to-end tests
│       └── test_workflows.py     # Full user workflows
├── alembic.ini                    # Alembic configuration
├── requirements.txt               # Python dependencies
└── README.md                      # Backend documentation

frontend/
├── src/
│   ├── components/                # React components
│   │   ├── collections/          # Collection management
│   │   │   ├── CollectionList.jsx
│   │   │   ├── CollectionForm.jsx
│   │   │   └── CollectionStatus.jsx
│   │   ├── pipelines/            # Pipeline editor
│   │   │   ├── PipelineList.jsx
│   │   │   ├── PipelineFormEditor.jsx
│   │   │   └── NodeEditor.jsx
│   │   ├── tools/                # Tool execution
│   │   │   ├── ToolSelector.jsx
│   │   │   └── ProgressMonitor.jsx
│   │   ├── results/              # Results visualization
│   │   │   ├── ResultList.jsx
│   │   │   ├── TrendChart.jsx
│   │   │   └── ReportViewer.jsx
│   │   └── common/               # Shared components
│   │       ├── ConfirmDialog.jsx
│   │       └── ErrorBoundary.jsx
│   ├── pages/                     # Top-level pages
│   │   ├── CollectionsPage.jsx   # Collection management
│   │   ├── PipelinesPage.jsx     # Pipeline configuration
│   │   ├── ToolsPage.jsx         # Tool execution
│   │   ├── ResultsPage.jsx       # Results & trends
│   │   └── ConfigPage.jsx        # Configuration editor
│   ├── services/                  # API client
│   │   ├── api.js                # Axios instance
│   │   ├── collections.js        # Collection API calls
│   │   ├── pipelines.js          # Pipeline API calls
│   │   └── websocket.js          # WebSocket client
│   ├── hooks/                     # Custom React hooks
│   │   ├── useCollections.js     # Collection state
│   │   └── useAnalysisProgress.js # Progress monitoring
│   ├── utils/                     # Frontend utilities
│   │   └── formatters.js         # Date, number formatting
│   └── App.jsx                    # Main application
├── tests/
│   └── components/                # Component tests
│       └── CollectionForm.test.jsx
├── package.json                   # Node dependencies
└── README.md                      # Frontend documentation

# CLI tool updates (repository root)
photo_stats.py                     # Extended: DB-first config, YAML fallback, result storage
photo_pairing.py                   # Extended: DB-first config, YAML fallback, result storage
pipeline_validation.py             # Extended: Read active pipeline from DB, validate against graph, store results
setup_master_key.py                # NEW: Interactive tool to generate and configure master encryption key
web_server.py                      # NEW: CLI command to start FastAPI server (validates master key on startup)

# Shared utilities (extended and new)
utils/
├── config_manager.py              # Extended: DatabaseConfigAdapter + YAMLConfigAdapter with fallback
├── filename_parser.py             # Extended: Validate properties against DB processing_methods
└── pipeline_processor.py          # NEW: Core pipeline graph engine (CRITICAL)
    ├── PipelineGraph              # Graph representation with nodes/edges
    ├── validate_structure()       # Cycle detection, orphaned nodes, property validation
    ├── generate_preview()         # Expected filename generation from graph traversal
    ├── validate_collection()      # Match files to pipeline (CONSISTENT/PARTIAL/INCONSISTENT)
    └── calculate_readiness()      # Archival readiness metrics per termination type

# Configuration & templates (existing)
config/
├── template-config.yaml           # YAML template (unchanged)
└── config.yaml                    # User config (gitignored)

templates/                         # Jinja2 templates (existing)
├── base.html.j2                   # Base template with Chart.js
├── photostats.html.j2             # PhotoStats report
└── photo_pairing.html.j2          # Photo Pairing report
```

**Structure Decision**: Web application structure (backend + frontend) selected because this feature adds a React-based web UI with FastAPI backend while maintaining CLI tool compatibility. Backend and frontend are separate for independent development (NFR4.3). Existing CLI tools updated to support database-first configuration with YAML fallback.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multi-project structure (backend + frontend) | Web UI is a primary requirement (FR-044 to FR-049, User Stories 1-4). Cannot achieve persistent storage, remote collections, and trend visualization with CLI-only tools. | Single CLI project insufficient: requires database-backed web interface for collection management, real-time progress updates (WebSocket), and historical trend visualization. |
| PostgreSQL database dependency | Persistent storage is core requirement (FR-014 to FR-020). YAML files cannot support: concurrent access, complex queries, historical trend analysis, or transactional consistency. | File-based storage (YAML/JSON) rejected: Cannot handle concurrent analysis jobs, historical queries (<1s for 1000+ results per NFR1.2), or ACID transactions for partial failure handling (FR-019). |
| FastAPI framework (vs extending CLI) | REST API + WebSocket required for web frontend. Existing CLI tools cannot provide: real-time progress updates, concurrent job management, or browser-based UI. | Extending CLI tools rejected: Cannot provide web UI, WebSocket progress, or concurrent job queue. FastAPI BackgroundTasks simpler than Celery/RQ for v1. |
| React frontend framework | Form-based pipeline editor (FR-026 to FR-035), trend charts (FR-047), and interactive collection management (FR-001 to FR-006) require component-based UI with state management. | Server-rendered HTML rejected: Cannot provide real-time progress updates, interactive pipeline editing, or client-side trend chart filtering without full page reloads. |
| Remote storage adapters (boto3, GCS, SMB) | Remote collection support is primary requirement (FR-007 to FR-013, User Story 1). Local filesystem insufficient for cloud storage (S3, GCS) or network shares (SMB/CIFS). | Local-only rejected: Core user pain point is inability to analyze remote collections (PRD Problem Statement #1). Cannot achieve SC-014 (50% remote collections) without remote adapters. |

## Phase 0: Research & Technical Decisions

**Goal**: Resolve all technical unknowns and validate technology choices before design phase.

### Research Tasks

The following research tasks will be executed to resolve technical decisions documented in the PRD:

1. **Database Schema Design for JSONB Analysis Results**
   - **Question**: How to structure JSONB columns for PhotoStats, Photo Pairing, and Pipeline Validation results with different schemas?
   - **Research**: PostgreSQL JSONB indexing strategies, schema versioning approaches, query performance for nested data
   - **Decision Criteria**: Query performance (<1s for 1000+ results), schema evolution support, index efficiency

2. **Credential Encryption Strategy**
   - **Question**: How to securely encrypt/decrypt AWS S3, GCS, and SMB credentials in database?
   - **Research**: Python cryptography library (Fernet), key management options, encryption-at-rest best practices
   - **Decision Criteria**: Security (no plaintext), key rotation support, cross-platform compatibility

3. **File Listing Cache Implementation**
   - **Question**: How to cache remote file listings with collection-aware TTL (1hr/24hr/7day)?
   - **Research**: In-memory caching (dict with TTL), Redis for persistence, cache invalidation strategies
   - **Decision Criteria**: 80% API call reduction (SC-004), simple implementation for v1, TTL per collection

4. **Job Queue for Concurrent Analysis**
   - **Question**: FastAPI BackgroundTasks vs Celery/RQ for analysis job queue?
   - **Research**: FastAPI async task patterns, queue position tracking, cancellation support
   - **Decision Criteria**: Queue with position display (Clarification #1), job cancellation (Clarification #3), v1 simplicity

5. **YAML Import Conflict Resolution UI**
   - **Question**: How to build side-by-side comparison UI for YAML import conflicts?
   - **Research**: React diff components, nested object comparison, user selection persistence
   - **Decision Criteria**: Clear UX (Clarification #4), handles nested objects (camera_mappings), atomic transactions

6. **WebSocket Protocol for Progress Updates**
   - **Question**: How to stream real-time progress (files scanned, issues found) via WebSocket?
   - **Research**: FastAPI WebSocket patterns, progress event schema, reconnection handling
   - **Decision Criteria**: Real-time updates (FR-037), works with background jobs, handles disconnects

7. **Pipeline Validation Integration**
   - **Question**: How to validate pipeline structure (cycles, orphaned nodes) and generate filename previews?
   - **Research**: Graph cycle detection algorithms, topological sort for validation, filename generation from graph traversal
   - **Decision Criteria**: Validates all node types (FR-027), detects cycles/orphans (FR-028), preview accuracy (FR-031)

8. **CLI Tool Database Integration**
   - **Question**: How to extend PhotoAdminConfig to read from database with YAML fallback?
   - **Research**: SQLAlchemy connection patterns, fallback logic, database unavailability handling
   - **Decision Criteria**: <10% performance overhead (FR-053), seamless fallback (FR-051), no breaking changes

**Output**: `research.md` with decisions, rationale, and alternatives for each research task

## Phase 1: Design & Contracts

**Prerequisites**: `research.md` complete with all technical decisions resolved

### Data Model Design

**Goal**: Create comprehensive data model covering all entities from spec

**Tasks**:
1. **Extract entities** from spec.md Key Entities section:
   - Collection (with state: Live/Closed/Archived, cache_ttl)
   - AnalysisResult (with status: completed/failed/running)
   - Configuration (key-value with JSONB)
   - Pipeline (with is_active, version)
   - PipelineHistory (version tracking)

2. **Define SQLAlchemy models** with:
   - Field types (VARCHAR, INTEGER, JSONB, TIMESTAMP)
   - Relationships (foreign keys, cascades)
   - Validation rules from functional requirements
   - Indexes for query performance (collection queries, result filtering)

3. **Document state transitions**:
   - Collection state: Live → Closed → Archived (with cache TTL changes)
   - Analysis status: pending → running → completed/failed
   - Pipeline activation: deactivate others when activating one

4. **Schema migration strategy**:
   - Alembic versioning
   - JSONB schema evolution for analysis results
   - Backward compatibility with existing YAML

**Output**: `data-model.md` with SQLAlchemy models, relationships, state machines, indexes

### API Contract Design

**Goal**: Define REST API and WebSocket contracts from functional requirements

**Tasks**:
1. **Generate OpenAPI 3.0 specification**:
   - Collections endpoints (POST, GET, PUT, DELETE, POST /test)
   - Configuration endpoints (GET, PUT, POST /import, GET /export)
   - Pipelines endpoints (CRUD, POST /validate, POST /activate, GET /preview, GET /history, POST /import, GET /{id}/export)
   - Tools endpoints (POST for each tool, GET /status/{job_id})
   - Results endpoints (GET list with filters, GET /{id}, GET /{id}/report, DELETE /{id})

2. **Define Pydantic schemas** for request/response validation:
   - CollectionCreate (name, type, location, state, credentials)
   - CollectionUpdate (name, location, state, cache_ttl)
   - PipelineCreate (name, description, config)
   - AnalysisRequest (collection_id, tool, pipeline_id)
   - AnalysisResponse (id, status, progress, results)

3. **Document WebSocket protocol** for real-time progress:
   - Connection: `/api/tools/progress/{job_id}`
   - Events: `progress`, `complete`, `error`
   - Message schema: `{event, data: {files_scanned, issues_found, stage}}`

4. **Error response schemas**:
   - 400 Bad Request (validation errors)
   - 404 Not Found (collection/pipeline/result not found)
   - 409 Conflict (concurrent job, YAML import conflicts)
   - 500 Internal Server Error (database/remote storage failures)

**Output**: `contracts/openapi.yaml` (OpenAPI 3.0 spec), `contracts/websocket.md` (WebSocket protocol)

### Quickstart Documentation

**Goal**: Create getting started guide for developers

**Tasks**:
1. **Setup instructions**:
   - PostgreSQL installation and database creation
   - Python environment setup (backend)
   - Node.js environment setup (frontend)
   - Environment variables (.env files)

2. **Local development workflow**:
   - Database migrations (alembic upgrade head)
   - Start backend server (uvicorn)
   - Start frontend dev server (npm start)
   - Run tests (pytest, jest)

3. **First-time user flow**:
   - YAML config import on first run
   - Create first collection
   - Run analysis tool
   - View results and trends

**Output**: `quickstart.md` with setup steps, development workflow, first-time user guide

### Pipeline Processor Design

**Goal**: Design the core pipeline graph engine shared between backend and CLI tools

**Critical Component**: `utils/pipeline_processor.py` is the central engine for all pipeline operations. This must be shared infrastructure (Constitution principle) to ensure consistency between web UI validation and CLI tool execution.

**Used By**:
- Backend API: `/api/pipelines/{id}/validate`, `/api/pipelines/{id}/preview`, `/api/tools/pipeline_validation`
- CLI tool: `pipeline_validation.py` (primary consumer)
- Potentially: `photo_pairing.py` (for pairing node logic)

**Core Classes**:

1. **PipelineGraph**
   - Parse pipeline config JSONB into traversable graph structure
   - Represent nodes: Capture, File, Process, Pairing, Branching, Termination
   - Represent edges with properties and parent-child relationships
   - Provide graph traversal methods (DFS, topological sort)

2. **NodeValidator**
   - Validate node-specific constraints:
     - Capture: Must be root (no incoming edges)
     - File: Must have extension property
     - Process: Must reference valid processing method from config
     - Pairing: Must have exactly 2 incoming edges
     - Branching: Must have 2+ outgoing edges
     - Termination: Must be leaf (no outgoing edges)

3. **StructureValidator**
   - **Cycle detection**: Topological sort algorithm (from research.md)
   - **Orphaned node detection**: DFS to find unreachable nodes from Capture
   - **Dead-end detection**: Nodes with no path to Termination
   - **Property reference validation**: Check processing_methods exist in database/config

4. **FilenamePreviewGenerator**
   - Graph traversal from Capture → Termination nodes
   - Apply node transformations:
     - Capture: `{camera_id}{counter}` (e.g., "AB3D0001")
     - File: Add extension (e.g., ".dng")
     - Process: Add processing method property (e.g., "-HDR")
     - Pairing: Generate paired variant (e.g., "-2")
     - Branching: Follow all branch paths
   - Output: List of expected filename patterns per termination type

5. **CollectionValidator**
   - Match actual files (from collection scan) against pipeline graph
   - Group files by base filename (camera ID + counter)
   - Classify image groups:
     - **CONSISTENT**: All expected files present per pipeline graph
     - **PARTIAL**: Some pipeline nodes completed, others missing
     - **INCONSISTENT**: Files don't match any valid pipeline path
   - Track which nodes each image group has completed
   - Generate detailed validation report (per FR-048)

6. **ReadinessCalculator**
   - Calculate archival readiness per termination type (FR-049)
   - Metrics:
     - Total image groups
     - Groups reaching each termination type
     - Percentage complete per termination
     - Missing files preventing completion
   - Used for trend analysis and dashboard visualization

**Key Algorithms** (from research.md Task 7):

```python
# Cycle detection using topological sort
def detect_cycles(graph: PipelineGraph) -> List[List[str]]:
    """Returns list of cycles found in graph"""
    # Kahn's algorithm for topological sort
    # If unable to process all nodes, cycles exist

# Orphaned node detection
def find_orphaned_nodes(graph: PipelineGraph) -> List[str]:
    """Returns nodes unreachable from Capture nodes"""
    # DFS from all Capture nodes
    # Nodes not visited are orphaned

# Filename generation
def generate_expected_filenames(graph: PipelineGraph) -> Dict[str, List[str]]:
    """Generate expected filenames per termination type"""
    # Traverse all paths from Capture to Termination
    # Apply transformations at each node
    # Return map of termination_type → [expected_patterns]
```

**Integration Points**:

```python
# Backend API usage
from utils.pipeline_processor import PipelineGraph, StructureValidator

@router.post("/api/pipelines/{id}/validate")
async def validate_pipeline(pipeline_id: int):
    pipeline = await get_pipeline(pipeline_id)
    graph = PipelineGraph(pipeline.config)
    validator = StructureValidator(graph)

    errors = validator.validate()  # Returns cycles, orphans, invalid refs
    return {"valid": len(errors) == 0, "errors": errors}

# CLI tool usage
from utils.pipeline_processor import PipelineGraph, CollectionValidator

def validate_collection(collection_path: str, pipeline_config: dict):
    graph = PipelineGraph(pipeline_config)
    files = scan_collection(collection_path)
    validator = CollectionValidator(graph, files)

    results = validator.validate()  # Returns CONSISTENT/PARTIAL/INCONSISTENT
    return results
```

**Testing Strategy**:
- Unit tests for each algorithm (cycle detection, orphan detection, filename generation)
- Integration tests with real pipeline configs from YAML
- Edge cases: empty pipelines, single-node pipelines, complex branching
- Performance tests: Large pipelines (20+ nodes), large collections (10K+ files)

**Output**: Design documented in `data-model.md` Pipeline Processor section

### Agent Context Update

**Goal**: Update agent context file with new technologies from this plan

**Task**: Run `.specify/scripts/bash/update-agent-context.sh claude` to add:
- FastAPI (backend framework)
- PostgreSQL with JSONB (database)
- SQLAlchemy + Alembic (ORM + migrations)
- React (frontend framework)
- boto3, google-cloud-storage, smbprotocol (remote storage)

**Output**: `.specify/memory/agent-context-claude.md` (updated with new tech, preserving manual additions)

## Phase 2: Task Generation

**Prerequisites**: Phase 1 complete (data-model.md, contracts/, quickstart.md)

**This phase is handled by `/speckit.tasks` command (NOT part of `/speckit.plan`)**

The tasks will be generated based on:
- 53 functional requirements from spec.md
- Data model from data-model.md
- API contracts from contracts/
- PRD migration strategy (6 phases over 12 weeks)
- Edge case clarifications from spec.md

**Output**: `tasks.md` (created by `/speckit.tasks`, not this command)

## Next Steps

1. ✅ **Phase 0 Complete**: Execute research tasks and document decisions in `research.md`
2. ⏳ **Phase 1 In Progress**: Generate data-model.md, contracts/, quickstart.md
3. ⏳ **Phase 1 Final**: Run update-agent-context.sh to sync agent memory
4. ⏳ **Phase 2**: Run `/speckit.tasks` to generate implementation tasks
5. ⏳ **Implementation**: Begin Phase 1 tasks (Database Layer per PRD)
