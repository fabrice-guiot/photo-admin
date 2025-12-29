# Feature Specification: Remote Photo Collections and Analysis Persistence

**Feature Branch**: `004-remote-photos-persistence`
**Created**: 2025-12-29
**Status**: Draft
**Input**: User description: "Issue #24, based on the PRD available in docs/prd/004-remote-photos-persistence.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Multiple Collections Through Web Interface (Priority: P1)

Professional photographer Alex manages 10+ photo collections across local drives and cloud storage (AWS S3, Google Drive). Currently, Alex must manually run CLI tools on each mounted drive and cannot track which collections have been analyzed or when.

**Why this priority**: This is the core value proposition - enabling users to centralize collection management and track analysis history. Without this, users cannot move beyond one-off CLI executions.

**Independent Test**: Can be fully tested by creating/editing/deleting collections through web UI and verifying they persist across browser sessions. Delivers immediate value by providing a centralized inventory of photo locations.

**Acceptance Scenarios**:

1. **Given** user has no collections, **When** they create a local collection with name "Wedding 2024", path "/photos/weddings/2024", and state "Live", **Then** collection appears in list with 1-hour cache refresh rate and persists after browser refresh
2. **Given** user has existing collections, **When** they create a remote S3 collection with URI "s3://my-bucket/photos", AWS credentials, and state "Archived", **Then** system validates credentials, shows collection as "accessible", and sets 7-day cache refresh rate
3. **Given** user has a collection, **When** they edit the collection name, location, or state (Live/Closed/Archived), **Then** changes save immediately, analysis history remains linked to the collection, and cache TTL updates to match new state
4. **Given** user views a remote collection, **When** they click manual refresh button, **Then** system invalidates cache immediately and fetches current file listing from remote storage
5. **Given** user has a collection with no analysis results and no active jobs, **When** they delete it, **Then** collection is removed permanently
6. **Given** user has a collection with analysis results or queued/running jobs, **When** they attempt to delete it, **Then** system shows warning about deleting historical data and/or cancelling active jobs and requires confirmation
7. **Given** user views collection list, **When** a remote collection becomes inaccessible (network failure, credential expiry), **Then** collection shows "inaccessible" status with actionable error message
8. **Given** user has a Live collection, **When** they change state to Closed, **Then** cache refresh rate automatically adjusts from 1 hour to 24 hours

---

### User Story 2 - Execute Analysis Tools and Store Results (Priority: P1)

Alex wants to run PhotoStats, Photo Pairing, and Pipeline Validation on all collections monthly to identify orphaned files, track camera usage, and validate processing workflows. Currently, results are lost after HTML report generation, preventing trend analysis.

**Why this priority**: Without persistent results storage, users cannot track degradation trends or compare analysis over time - a key pain point from the PRD.

**Independent Test**: Can be fully tested by running any analysis tool on a collection, verifying results are stored in database, and regenerating HTML reports from stored data. Delivers value by preserving analysis history.

**Acceptance Scenarios**:

1. **Given** user selects a collection and PhotoStats tool, **When** they trigger analysis, **Then** system shows real-time progress (files scanned, issues found) and stores results upon completion
2. **Given** analysis is running, **When** user navigates away from progress page, **Then** analysis continues in background and user can return to check status
3. **Given** analysis completes successfully, **When** user views results, **Then** system displays HTML report using existing Jinja2 templates with timestamped filename
4. **Given** analysis fails due to collection inaccessibility, **When** failure occurs, **Then** system stores error details and allows user to retry with updated credentials
5. **Given** user has multiple analysis results for same collection, **When** they view history, **Then** results are sorted by execution date with tool type, status, and quick summary
6. **Given** user views past analysis result, **When** they request report, **Then** system generates HTML report from stored data (not re-running analysis)

---

### User Story 3 - Configure Photo Processing Pipelines Through Forms (Priority: P2)

Workflow-focused photographer Taylor tracks photos through processing stages (RAW → DNG → Edit → Archive). Currently, editing pipeline definitions in YAML is error-prone and difficult to visualize.

**Why this priority**: Pipeline configuration is complex and critical for Pipeline Validation tool users. Form-based editing reduces errors and improves usability, but is secondary to basic collection management and tool execution.

**Independent Test**: Can be fully tested by creating/editing pipelines through web forms, validating structure, and using them with Pipeline Validation tool. Delivers value by making pipeline configuration accessible to non-technical users.

**Acceptance Scenarios**:

1. **Given** user has no pipelines, **When** they create a new pipeline with name "Standard Workflow", **Then** system provides form to add nodes (Capture, File, Process, Pairing, Branching, Termination)
2. **Given** user is editing a pipeline, **When** they add a Processing node with method "HDR", **Then** system validates the processing method exists in configuration or prompts to create it interactively
3. **Given** user has defined pipeline nodes, **When** they save pipeline, **Then** system validates structure (no orphaned nodes, no cycles, valid property references)
4. **Given** pipeline validation fails, **When** user views errors, **Then** system highlights specific issues (e.g., "Node 'Edit' has no incoming edges") with guidance on fixing
5. **Given** user has a valid pipeline, **When** they activate it, **Then** pipeline becomes the default for Pipeline Validation tool and deactivates any previously active pipeline
6. **Given** user has an active pipeline, **When** they run Pipeline Validation on a collection, **Then** tool uses the active pipeline configuration and stores validation results (CONSISTENT/PARTIAL/INCONSISTENT breakdowns)
7. **Given** user edits an active pipeline, **When** they save changes, **Then** system creates new version and updates change history with timestamp

---

### User Story 4 - Track Analysis Trends Over Time (Priority: P2)

Archive manager Jamie validates photo archive integrity across network-attached storage. Currently, Jamie must manually organize and compare HTML reports to identify if collections are degrading over time.

**Why this priority**: Historical trend analysis is a key differentiator from CLI-only tools, but depends on having multiple analysis results first (from User Story 2).

**Independent Test**: Can be fully tested by running same tool multiple times on a collection and viewing trend charts. Delivers value by surfacing patterns invisible in single-execution reports.

**Acceptance Scenarios**:

1. **Given** user has run PhotoStats 3+ times on same collection, **When** they view trend analysis, **Then** system displays chart showing orphaned files count over time
2. **Given** user views Photo Pairing trends, **When** chart loads, **Then** system shows camera usage distribution changes across executions
3. **Given** user views Pipeline Validation trends, **When** chart loads, **Then** system shows CONSISTENT/PARTIAL/INCONSISTENT ratios over time with archival readiness metrics
4. **Given** user hovers over data point on trend chart, **When** tooltip appears, **Then** it shows execution date, specific metric value, and link to full report
5. **Given** user has collections with different analysis frequencies, **When** they filter trend view, **Then** system allows date range selection and comparison between collections

---

### User Story 5 - Migrate Existing Configuration to Database (Priority: P3)

Existing CLI tool users have photo extensions, metadata extensions, camera mappings, and pipeline definitions stored in YAML configuration files. They need seamless migration to database-backed configuration.

**Why this priority**: Critical for backward compatibility and user adoption, but only matters after web interface is functional (P1/P2 stories).

**Independent Test**: Can be fully tested by importing existing config.yaml file and verifying all settings are accessible through web UI and CLI tools. Delivers value by preserving user investment in configuration.

**Acceptance Scenarios**:

1. **Given** user has existing config/config.yaml file, **When** they start web interface for first time, **Then** system detects YAML and prompts to import configuration
2. **Given** user confirms import, **When** import runs, **Then** system migrates photo_extensions, metadata_extensions, camera_mappings, processing_methods, and pipeline definitions to database, showing conflict resolution UI for any conflicting keys with side-by-side comparison
3. **Given** configuration is in database, **When** user runs CLI tool (PhotoStats, Photo Pairing), **Then** tool reads configuration from database with fallback to YAML if database unavailable
4. **Given** user edits configuration in web UI, **When** they save changes, **Then** updates apply immediately to both web interface and CLI tools
5. **Given** user has database configuration, **When** they export to YAML, **Then** system generates config.yaml file matching original format for portability

---

### Edge Cases

- ✓ **Mid-analysis network failure**: Discard all partial analysis progress and record failure metadata (failure reason, timestamp, error details) for debugging. User must retry analysis after fixing network/credential issues (see FR-040)
- ✓ **Concurrent analysis executions**: New requests are queued sequentially per collection with queue position and estimated start time displayed to user (see FR-043)
- ✓ **Collection deletion with active jobs**: Cancel all queued/running jobs and delete collection with confirmation dialog warning about active jobs being cancelled (see FR-005)
- How does system handle extremely large collections (1M+ files) for remote storage API rate limits?
- What happens when pipeline configuration changes while Pipeline Validation is running?
- How does system handle collection state transitions (Live → Closed → Archived) when cached data exists with previous TTL?
- ✓ **YAML import conflicts**: Show conflict resolution UI with side-by-side comparison for conflicting keys, allowing user to choose which values to keep (see FR-021)
- How does system handle analysis results from different tool versions (schema evolution)?
- What happens when Jinja2 template rendering fails for stored results (corrupted data, template changes)?
- How does system handle database connection failures during CLI tool execution?
- ✓ **Manual refresh cost control**: Show warning only if file count exceeds configurable threshold (default 100K files), otherwise refresh immediately (see FR-013a)

## Requirements *(mandatory)*

### Functional Requirements

#### Collection Management

- **FR-001**: System MUST allow users to create collections with unique name, type (local/remote), location (filesystem path or URI), and state (Live/Closed/Archived)
- **FR-002**: System MUST support local filesystem paths and remote URI schemes (s3://, gs://, smb://)
- **FR-003**: System MUST validate collection accessibility at creation time and display status (accessible/inaccessible) in collection list
- **FR-004**: System MUST allow users to edit collection name, location, and credentials
- **FR-005**: System MUST allow users to delete collections with confirmation prompt if analysis results exist or if queued/running analysis jobs exist (jobs will be cancelled upon deletion)
- **FR-006**: System MUST persist collection definitions across application restarts

#### Remote Collection Access

- **FR-007**: System MUST integrate with AWS S3 API for remote collection access
- **FR-008**: System MUST integrate with Google Cloud Storage API for remote collection access
- **FR-009**: System MUST support SMB/CIFS network share access for remote collections
- **FR-010**: System MUST securely store remote collection credentials (API keys, OAuth tokens) with encryption
- **FR-011**: System MUST cache remote file listings to reduce API calls and improve performance
- **FR-012**: System MUST handle network failures gracefully with retry logic (exponential backoff up to 3 retries)
- **FR-013**: System MUST invalidate file listing cache based on collection state: Live collections (1 hour default), Closed collections (24 hours default), Archived collections (7 days default), with user-configurable override per collection
- **FR-013a**: System MUST provide manual refresh control in collection UI allowing users to force immediate cache invalidation, with cost warning displayed if file count exceeds configurable threshold (default 100K files)

#### Database Persistence

- **FR-014**: System MUST store collection definitions in database with fields: id, name, type, location, state (Live/Closed/Archived), cache_ttl (user-configurable), credentials (encrypted), metadata, created_at, updated_at
- **FR-015**: System MUST store analysis execution results with fields: id, collection_id, tool, pipeline_id (nullable), executed_at, results (JSON), report_html, status, error_message
- **FR-016**: System MUST store configuration settings in database with key-value structure supporting nested objects (photo_extensions, metadata_extensions, camera_mappings, processing_methods)
- **FR-017**: System MUST store pipeline definitions in database with fields: id, name, description, config (JSON nodes/edges), is_active, version, created_at, updated_at
- **FR-018**: System MUST store pipeline change history with fields: id, pipeline_id, version, config (JSON), changed_at, change_notes
- **FR-019**: System MUST use database transactions to ensure data consistency during analysis execution (prevent partial results on failure)
- **FR-020**: System MUST support querying historical analysis results filtered by collection, tool, date range, and status

#### Configuration Management

- **FR-021**: System MUST import existing YAML configuration (config/config.yaml) into database on first run with conflict resolution UI showing side-by-side comparison for conflicting keys, allowing user to choose which values to keep
- **FR-022**: System MUST provide web UI for editing photo extensions, metadata extensions, camera mappings, and processing methods
- **FR-023**: System MUST export database configuration to YAML format for CLI tool compatibility
- **FR-024**: System MUST apply configuration changes immediately without requiring application restart
- **FR-025**: System MUST preserve interactive prompts for unknown camera IDs and processing methods (PhotoAdminConfig behavior)

#### Pipeline Configuration Management

- **FR-026**: System MUST provide form-based editor for creating and editing pipeline configurations
- **FR-027**: System MUST support all node types: Capture, File, Process, Pairing, Branching, Termination
- **FR-028**: System MUST validate pipeline structure on save: no orphaned nodes, no cycles, valid property references
- **FR-029**: System MUST display validation errors with specific node/edge details and actionable guidance
- **FR-030**: System MUST support activating one pipeline as default for Pipeline Validation tool (deactivating others)
- **FR-031**: System MUST preview expected filenames for a given pipeline configuration (based on pipeline graph traversal)
- **FR-032**: System MUST import pipeline definitions from YAML format
- **FR-033**: System MUST export pipeline definitions to YAML format matching existing schema
- **FR-034**: System MUST version pipeline configurations automatically on each save with incremental version numbers
- **FR-035**: System MUST record change history for pipelines including timestamp and optional change notes

#### Tool Execution

- **FR-036**: System MUST allow users to trigger PhotoStats, Photo Pairing, and Pipeline Validation from web interface on any collection
- **FR-037**: System MUST display real-time progress updates during analysis execution (files scanned, issues found, current stage)
- **FR-038**: System MUST allow analysis to run in background while user navigates to other pages
- **FR-039**: System MUST store analysis results in database upon successful completion
- **FR-040**: System MUST store error details in database when analysis fails (failure reason, timestamp, error details) and discard any partial analysis progress to maintain data consistency
- **FR-041**: System MUST allow users to select active pipeline before running Pipeline Validation
- **FR-042**: System MUST generate HTML reports using existing Jinja2 templates for web display and download
- **FR-043**: System MUST prevent concurrent analysis executions on same collection by queueing new requests sequentially and displaying queue position with estimated start time to user

#### Result Visualization

- **FR-044**: System MUST display list of historical analysis results sorted by execution date (newest first)
- **FR-045**: System MUST allow filtering analysis history by collection, tool type, date range, and status
- **FR-046**: System MUST regenerate HTML reports from stored results without re-running analysis
- **FR-047**: System MUST display trend charts comparing metrics across multiple executions (orphaned files, camera usage, pipeline validation ratios)
- **FR-048**: System MUST show Pipeline Validation results with CONSISTENT/PARTIAL/INCONSISTENT breakdowns per image group
- **FR-049**: System MUST display archival readiness metrics per termination type for Pipeline Validation results

#### CLI Tool Integration

- **FR-050**: System MUST allow existing CLI tools (PhotoStats, Photo Pairing, Pipeline Validation) to read configuration from database
- **FR-051**: System MUST provide fallback to YAML configuration when database is unavailable for CLI tools
- **FR-052**: System MUST provide CLI command to start web server
- **FR-053**: System MUST maintain CLI tool performance within 10% of current YAML-based execution times

### Key Entities

- **Collection**: Represents a photo storage location (local or remote). Attributes: name, type (local/s3/gcs/smb), location (path/URI), state (Live/Closed/Archived), cache_ttl (time-to-live for file listing cache), credentials (encrypted), accessibility status, metadata, creation/update timestamps
- **AnalysisResult**: Represents a single execution of an analysis tool. Attributes: collection reference, tool type (PhotoStats/Photo Pairing/Pipeline Validation), pipeline reference (nullable), execution timestamp, results (nested JSON), HTML report, status (completed/failed/running), error message
- **Configuration**: Represents global settings. Attributes: key (unique identifier), value (nested JSON supporting lists/objects), description, update timestamp
- **Pipeline**: Represents a photo processing workflow definition. Attributes: name (unique), description, config (nodes and edges as JSON graph), active status (boolean), version number, creation/update timestamps
- **PipelineHistory**: Represents historical versions of pipelines. Attributes: pipeline reference, version number, config snapshot (JSON), change timestamp, change notes

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create and manage collections through web interface in under 1 minute per collection
- **SC-002**: Collection listing loads within 2 seconds for up to 100 collections
- **SC-003**: Historical analysis result queries return within 1 second for databases with 1000+ stored results
- **SC-004**: Remote collection file listing caching reduces redundant API calls by 80% compared to uncached access
- **SC-005**: 90% of users successfully create and activate a pipeline through form-based editor on first attempt (compared to 40% success rate with manual YAML editing)
- **SC-006**: Pipeline validation errors reduce by 70% when using form-based editor compared to manual YAML editing
- **SC-007**: Users can view analysis trends across 10+ executions within 3 seconds
- **SC-008**: YAML configuration import completes without data loss for 100% of valid configuration files
- **SC-009**: Analysis execution time remains within 10% of CLI tool performance for same collection
- **SC-010**: HTML report generation from stored results completes within 500ms for reports with 1000+ issues
- **SC-011**: System handles network failures for remote collections without corrupting database state in 100% of test cases
- **SC-012**: Users can run monthly analysis on all collections (10+) and identify degradation trends without manual report organization
- **SC-013**: 80% of CLI tool users try web interface within 1 month of release
- **SC-014**: Support tickets related to pipeline configuration errors reduce by 60% after form-based editor release

## Assumptions

1. **Database Selection**: PostgreSQL with JSONB columns provides optimal balance of structure (collections, config) and flexibility (analysis results). SQLAlchemy ORM with Alembic migrations handles schema evolution.
2. **Backend Framework**: FastAPI provides async support for non-blocking remote storage access, automatic OpenAPI documentation, and WebSocket support for real-time progress updates.
3. **Frontend Framework**: React provides component-based architecture suitable for modular UI (collections, pipelines, results, trends).
4. **Remote Storage Libraries**: boto3 (AWS S3), google-cloud-storage (GCS), smbprotocol (SMB/CIFS) provide official/stable APIs. Consider fsspec for unified filesystem abstraction.
5. **Credential Encryption**: Python cryptography library provides Fernet symmetric encryption for storing remote credentials.
6. **Single Active Pipeline**: System enforces only one active pipeline at a time for Pipeline Validation to avoid user confusion about which pipeline is being used.
7. **Cache Invalidation Strategy**: Collection state determines default cache TTL - Live collections (1 hour, active work in progress), Closed collections (24 hours, infrequent changes), Archived collections (7 days, infrastructure monitoring only). User-configurable per collection with manual refresh override. This balances API quota limits with appropriate data freshness per collection lifecycle.
8. **Background Job Processing**: FastAPI BackgroundTasks sufficient for v1 analysis execution; Celery/RQ deferred to future if complex job management needed.
9. **Report Storage**: Pre-generate and store HTML reports in database to avoid Jinja2 template compatibility issues when templates evolve.
10. **Deployment Model**: Local-only deployment (localhost) for v1 - no user authentication, multi-user support, or remote deployment.
11. **Browser Compatibility**: Modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+) with ES6+ support.
12. **Platform Support**: Cross-platform (Linux, macOS, Windows) maintaining Python 3.10+ compatibility.

## Dependencies

### External Services
- Cloud storage accounts (AWS S3, Google Cloud Storage) for remote collection testing
- PostgreSQL database server (version 12+ recommended for JSONB improvements)

### New Python Libraries
- FastAPI (web framework)
- SQLAlchemy (ORM for database abstraction)
- Alembic (database migration versioning)
- boto3 (AWS S3 integration)
- google-cloud-storage (Google Cloud Storage integration)
- smbprotocol (SMB/CIFS network share integration)
- pydantic (data validation for API requests)
- cryptography (credential encryption with Fernet)
- uvicorn (ASGI server for FastAPI)
- psycopg2-binary (PostgreSQL adapter)

### Frontend Dependencies
- React (UI framework)
- React Router (client-side routing)
- Axios (HTTP client for API communication)
- Recharts or Victory (data visualization for trend charts)
- Material-UI or Ant Design (component library for consistent UI)
- WebSocket client library (for real-time progress updates)

### Existing Dependencies (Reused)
- PyYAML (config import/export)
- Jinja2 (HTML report generation)
- pytest (testing framework)

## Clarifications

### Session 2025-12-29

- Q: When a user tries to run an analysis tool on a collection that already has an analysis job running, how should the system respond? → A: Queue the new request and notify user of queue position (e.g., "Analysis queued. Position: 2. Estimated start: 5 minutes")
- Q: When a remote collection becomes inaccessible mid-analysis due to network timeout or credential revocation, how should the system handle the partial results and recovery? → A: Discard all analysis progress but record failure metadata (failure reason, timestamp, error details) for debugging
- Q: When a user deletes a collection that has queued or running analysis jobs, what should happen to those jobs? → A: Cancel all queued/running jobs and delete collection with confirmation dialog warning about active jobs being cancelled
- Q: When a user imports a YAML configuration that conflicts with existing database settings, what should the merge strategy be? → A: Show conflict resolution UI with side-by-side comparison, let user choose which values to keep per conflicting key
- Q: When a user manually refreshes an Archived collection with a large file count, should the system provide a warning or confirmation? → A: Show warning only if file count exceeds configurable threshold (default 100K files), otherwise refresh immediately

## Related Issues and References

### Related Issues
- Issue #24: Support for remote Photo collections and longer term persistence

### References
- PRD: docs/prd/004-remote-photos-persistence.md
- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- PostgreSQL JSONB Documentation: https://www.postgresql.org/docs/current/datatype-json.html
- boto3 S3 Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
- React Documentation: https://react.dev/
