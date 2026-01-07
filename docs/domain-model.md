# Photo-Admin Domain Model

**Version:** 1.0.0
**Last Updated:** 2026-01-07
**Status:** Living Document

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Application Vision](#application-vision)
3. [Technical Standards](#technical-standards)
4. [Entity Classification](#entity-classification)
5. [Implemented Entities](#implemented-entities)
6. [Planned Entities](#planned-entities)
7. [Entity Relationships](#entity-relationships)
8. [Data Architecture Principles](#data-architecture-principles)
9. [Appendices](#appendices)

---

## Executive Summary

This document defines the domain model for the Photo-Admin application, a comprehensive toolbox designed to help photographers manage their daily workflows, organize photo collections, and gain insights through analytics. It serves as the authoritative reference for all current and future development efforts.

The domain model is divided into two categories:
- **Implemented Entities**: Currently available in the codebase (Branch: `007-remote-photos-completion`)
- **Planned Entities**: Future entities that will be implemented in upcoming epics

---

## Application Vision

### Primary Goals

1. **Operational Support**: Help photographers run upcoming events smoothly through calendar management, logistics tracking, and workflow automation.

2. **Historical Organization**: Provide tools to record, catalog, and organize historical photo collections (events that occurred before adopting the application).

### Secondary Goals

3. **Analytics & Insights**: Aggregate data from activities and photos to generate actionable analytics:
   - Camera usage trends and maintenance scheduling
   - Event scheduling conflict detection
   - Workflow efficiency metrics
   - Equipment utilization patterns

### Target Users

- **Professional Photographers**: Studio owners, event photographers, sports/wildlife photographers
- **Hobbyist Photographers**: Enthusiasts managing personal photo collections
- **Photography Teams**: Organizations with multiple photographers sharing resources

---

## Technical Standards

### Universal Identifiers (Issue #42)

All user-facing entities MUST implement Universal Unique Identifiers following these specifications:

| Aspect | Specification |
|--------|---------------|
| **UUID Version** | UUIDv7 (time-ordered for database efficiency) |
| **External Format** | Crockford's Base32 with entity-type prefixes |
| **Internal Storage** | Binary UUID (16 bytes) for foreign keys |
| **Database PKs** | Auto-increment integers for internal joins |

**Prefix Convention:**

| Entity Type | Prefix | Example External ID |
|-------------|--------|---------------------|
| Collection | `col_` | `col_01HGW2BBG0000000000000000` |
| Connector | `con_` | `con_01HGW2BBG0000000000000001` |
| Pipeline | `pip_` | `pip_01HGW2BBG0000000000000002` |
| Event | `evt_` | `evt_01HGW2BBG0000000000000003` |
| User | `usr_` | `usr_01HGW2BBG0000000000000004` |
| Team | `tea_` | `tea_01HGW2BBG0000000000000005` |
| Camera | `cam_` | `cam_01HGW2BBG0000000000000006` |
| Album | `alb_` | `alb_01HGW2BBG0000000000000007` |
| Image | `img_` | `img_01HGW2BBG0000000000000008` |
| Location | `loc_` | `loc_01HGW2BBG0000000000000009` |
| Organizer | `org_` | `org_01HGW2BBG000000000000000A` |
| Performer | `prf_` | `prf_01HGW2BBG000000000000000B` |
| Result | `res_` | `res_01HGW2BBG000000000000000C` |
| Agent | `agt_` | `agt_01HGW2BBG000000000000000D` |

**Implementation Reference:** [puidv7-js](https://github.com/puidv7/puidv7-js)

### Multi-Tenancy Model

The application implements team-based data isolation:

- Users belong to exactly one Team (with a default personal team for solo users)
- All data queries are automatically scoped to the user's Team
- Cross-team data sharing is explicitly prohibited at the database level

---

## Entity Classification

### Implementation Status Legend

| Status | Icon | Description |
|--------|------|-------------|
| Implemented | :white_check_mark: | Available in current codebase |
| Planned | :construction: | Designed, awaiting implementation |
| Conceptual | :thought_balloon: | Early design phase |

### Entity Overview

| Entity | Status | Category | Priority |
|--------|--------|----------|----------|
| [Collection](#collection) | :white_check_mark: | Storage | - |
| [Connector](#connector) | :white_check_mark: | Storage | - |
| [Pipeline](#pipeline) | :white_check_mark: | Workflow | - |
| [PipelineHistory](#pipelinehistory) | :white_check_mark: | Workflow | - |
| [AnalysisResult](#analysisresult) | :white_check_mark: | Workflow | - |
| [Configuration](#configuration) | :white_check_mark: | System | - |
| [Event](#event) | :construction: | Calendar | High (#39) |
| [User](#user) | :construction: | Identity | High |
| [Team](#team) | :construction: | Identity | High |
| [Camera](#camera) | :construction: | Equipment | Medium |
| [Album](#album) | :construction: | Content | Medium |
| [Image](#image) | :construction: | Content | Medium |
| [Location/Venue](#locationvenue) | :construction: | Reference | Medium |
| [Organizer](#organizer) | :construction: | Reference | Low |
| [Performer](#performer) | :construction: | Reference | Low |
| [Category](#category) | :construction: | Reference | Low |
| [Agent](#agent) | :thought_balloon: | Infrastructure | Future |

---

## Implemented Entities

### Collection

**Purpose:** Represents a physical storage location containing photo files.

**Current Location:** `backend/src/models/collection.py`

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `connector_id` | Integer | FK(connectors.id), nullable | Reference to remote connector |
| `pipeline_id` | Integer | FK(pipelines.id), nullable | Assigned pipeline (SET NULL on delete) |
| `pipeline_version` | Integer | nullable | Pinned pipeline version |
| `name` | String(255) | unique, not null | User-friendly display name |
| `type` | Enum | not null | `LOCAL`, `S3`, `GCS`, `SMB` |
| `location` | String(1024) | not null | Path or bucket location |
| `state` | Enum | not null, default=LIVE | `LIVE`, `CLOSED`, `ARCHIVED` |
| `cache_ttl` | Integer | nullable | Override default cache TTL (seconds) |
| `is_accessible` | Boolean | not null, default=true | Connection status |
| `last_error` | Text | nullable | Most recent error message |
| `metadata_json` | Text | nullable | User-defined metadata (JSON) |
| `storage_bytes` | BigInteger | nullable | Total storage in bytes |
| `file_count` | Integer | nullable | Total number of files |
| `image_count` | Integer | nullable | Number of images after grouping |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null, auto-update | Last modification timestamp |

**State-Based Cache TTL Defaults:**

| State | Default TTL | Rationale |
|-------|-------------|-----------|
| `LIVE` | 3,600s (1 hour) | Active work, frequent changes |
| `CLOSED` | 86,400s (24 hours) | Finished work, infrequent changes |
| `ARCHIVED` | 604,800s (7 days) | Long-term storage, infrastructure monitoring |

**Location Format by Type:**

| Type | Format | Example |
|------|--------|---------|
| `LOCAL` | Absolute filesystem path | `/photos/2026/january` |
| `S3` | bucket-name/optional/prefix | `my-photos-bucket/raw/2026` |
| `GCS` | bucket-name/optional/prefix | `my-gcs-bucket/collections` |
| `SMB` | /share-path/optional/prefix | `/photos-share/archive` |

**Relationships:**
- Many-to-one with Connector (RESTRICT on delete)
- Many-to-one with Pipeline (SET NULL on delete)
- One-to-many with AnalysisResult (CASCADE delete)

---

### Connector

**Purpose:** Stores encrypted authentication credentials for remote storage systems.

**Current Location:** `backend/src/models/connector.py`

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `name` | String(255) | unique, not null | User-friendly name |
| `type` | Enum | not null | `S3`, `GCS`, `SMB` |
| `credentials` | Text | not null | Encrypted JSON credentials |
| `metadata_json` | Text | nullable | User-defined metadata |
| `is_active` | Boolean | not null, default=true | Active status |
| `last_validated` | DateTime | nullable | Last successful connection test |
| `last_error` | Text | nullable | Last connection error |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null, auto-update | Last modification timestamp |

**Credentials Format (Decrypted JSON):**

```json
// S3
{
  "aws_access_key_id": "AKIA...",
  "aws_secret_access_key": "...",
  "region": "us-west-2",
  "endpoint_url": null  // Optional for S3-compatible storage
}

// GCS
{
  "service_account_json": "{...}"  // Full service account JSON
}

// SMB
{
  "server": "192.168.1.100",
  "share": "photos",
  "username": "photographer",
  "password": "...",
  "domain": null  // Optional
}
```

**Design Rationale:**
- **Credential Reuse:** Multiple collections share one connector (e.g., 50 S3 buckets)
- **Key Rotation:** Master key rotation only re-encrypts Connector table
- **Future-Proof:** Enables connector-level access control for multi-user support

---

### Pipeline

**Purpose:** Defines photo processing workflow as a directed graph of nodes and edges.

**Current Location:** `backend/src/models/pipeline.py`

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `name` | String(255) | unique, not null | Display name |
| `description` | Text | nullable | Purpose/usage description |
| `nodes_json` | JSONB | not null | Node definitions array |
| `edges_json` | JSONB | not null | Edge connections array |
| `version` | Integer | not null, default=1 | Current version number |
| `is_active` | Boolean | not null, default=false | Available for use |
| `is_default` | Boolean | not null, default=false | Default for tool execution |
| `is_valid` | Boolean | not null, default=false | Structure validation passed |
| `validation_errors` | JSONB | nullable | Validation error messages |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null, auto-update | Last modification timestamp |

**Node Types:**

| Type | Purpose | Key Properties |
|------|---------|----------------|
| `capture` | Entry point for camera captures | `camera_id_pattern`, `counter_pattern` |
| `file` | Represents a file extension stage | `extension`, `optional` |
| `process` | Processing step (HDR, BW, etc.) | `suffix`, `description` |
| `pairing` | Groups related files | `inputs` (array of node IDs) |
| `branching` | Conditional path selection | `condition`, `value` |
| `termination` | End state classification | `name`, `classification` |

**Node Structure Example:**
```json
[
  {"id": "capture_1", "type": "capture", "properties": {"camera_id_pattern": "[A-Z0-9]{4}"}},
  {"id": "file_raw", "type": "file", "properties": {"extension": ".dng", "optional": false}},
  {"id": "file_xmp", "type": "file", "properties": {"extension": ".xmp", "optional": false}},
  {"id": "process_hdr", "type": "process", "properties": {"suffix": "-HDR"}},
  {"id": "done", "type": "termination", "properties": {"classification": "CONSISTENT"}}
]
```

**Edge Structure Example:**
```json
[
  {"from": "capture_1", "to": "file_raw"},
  {"from": "file_raw", "to": "process_hdr"},
  {"from": "process_hdr", "to": "done"}
]
```

**Constraints:**
- Only ONE pipeline can have `is_default=true` (application-enforced)
- Default pipeline MUST be active (`is_default` implies `is_active`)

---

### PipelineHistory

**Purpose:** Immutable audit trail of pipeline version changes.

**Current Location:** `backend/src/models/pipeline_history.py`

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `pipeline_id` | Integer | FK(pipelines.id), not null | Parent pipeline |
| `version` | Integer | not null | Version number snapshot |
| `nodes_json` | JSONB | not null | Node state at this version |
| `edges_json` | JSONB | not null | Edge state at this version |
| `change_summary` | String(500) | nullable | Description of changes |
| `changed_by` | String(255) | nullable | User who made the change |
| `created_at` | DateTime | not null | Version creation timestamp |

**Constraints:**
- `(pipeline_id, version)` is unique
- Records are NEVER modified after creation
- CASCADE delete when parent pipeline is deleted

---

### AnalysisResult

**Purpose:** Stores execution history and results for analysis tools.

**Current Location:** `backend/src/models/analysis_result.py`

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `collection_id` | Integer | FK(collections.id), nullable | Target collection |
| `tool` | String(50) | not null | Tool name |
| `pipeline_id` | Integer | FK(pipelines.id), nullable | Pipeline used |
| `pipeline_version` | Integer | nullable | Pipeline version at execution |
| `status` | Enum | not null | `COMPLETED`, `FAILED`, `CANCELLED` |
| `started_at` | DateTime | not null | Execution start |
| `completed_at` | DateTime | not null | Execution end |
| `duration_seconds` | Float | not null | Execution duration |
| `results_json` | JSONB | not null | Structured results data |
| `report_html` | Text | nullable | Pre-rendered HTML report |
| `error_message` | Text | nullable | Error details if failed |
| `files_scanned` | Integer | nullable | Files processed count |
| `issues_found` | Integer | nullable | Issues detected count |
| `created_at` | DateTime | not null | Record creation timestamp |

**Tool Types:**

| Tool | Description | Requires Collection |
|------|-------------|---------------------|
| `photostats` | File statistics and orphan detection | Yes |
| `photo_pairing` | Filename pattern analysis | Yes |
| `pipeline_validation` | Pipeline structure validation | No (display-graph mode) |

---

### Configuration

**Purpose:** Persistent application settings as key-value pairs.

**Current Location:** `backend/src/models/configuration.py`

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `category` | String(50) | not null | Configuration category |
| `key` | String(255) | not null | Configuration key |
| `value_json` | JSONB | not null | Configuration value |
| `description` | Text | nullable | Human-readable description |
| `source` | Enum | not null, default=DATABASE | `DATABASE`, `YAML_IMPORT` |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null, auto-update | Last modification timestamp |

**Configuration Categories:**

| Category | Example Keys | Value Type |
|----------|--------------|------------|
| `extensions` | `photo_extensions`, `metadata_extensions`, `require_sidecar` | Array[String] |
| `cameras` | Camera ID (e.g., `AB3D`) | Object with `name`, `serial_number` |
| `processing_methods` | Method code (e.g., `HDR`) | String description |

---

## Planned Entities

### Event

**Priority:** High (Issue #39)
**Target Epic:** 008-events-calendar

**Purpose:** Calendar-based photography event management.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `uuid` | UUID | unique, not null | External identifier |
| `team_id` | Integer | FK(teams.id), not null | Owning team |
| `title` | String(255) | not null | Event title |
| `description` | Text | nullable | Event description |
| `start_time` | DateTime | not null | Event start |
| `end_time` | DateTime | not null | Event end |
| `is_all_day` | Boolean | not null, default=false | All-day event flag |
| `location_id` | Integer | FK(locations.id), nullable | Event venue |
| `category_id` | Integer | FK(categories.id), nullable | Event category |
| `organizer_id` | Integer | FK(organizers.id), nullable | Event organizer |
| `status` | Enum | not null | Event lifecycle status |
| `attendance` | Enum | not null | `PLANNED`, `SKIPPED`, `ATTENDED` |
| `requires_ticket` | Boolean | not null, default=false | Ticket required |
| `has_ticket` | Boolean | nullable | Ticket acquired |
| `requires_time_off` | Boolean | not null, default=false | Time off required |
| `has_time_off` | Boolean | nullable | Time off approved |
| `requires_lodging` | Boolean | not null, default=false | Lodging required |
| `has_lodging` | Boolean | nullable | Lodging booked |
| `requires_travel` | Boolean | not null, default=false | Travel required |
| `has_travel` | Boolean | nullable | Travel arranged |
| `deadline` | DateTime | nullable | Workflow deadline |
| `notes` | Text | nullable | Additional notes |
| `metadata_json` | JSONB | nullable | Custom metadata |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null | Last modification |

**Status Values:**

| Status | Description | Color Hint |
|--------|-------------|------------|
| `FUTURE` | Upcoming event | Blue |
| `IN_PROGRESS` | Currently happening | Green |
| `COMPLETED` | Event finished | Gray |
| `CANCELLED` | Event cancelled | Red |

**Attendance Values:**

| Value | Description | Calendar Color |
|-------|-------------|----------------|
| `PLANNED` | Intend to attend | Default |
| `SKIPPED` | Decided not to attend | Muted/Gray |
| `ATTENDED` | Actually attended | Success/Green |

**Multi-Day Event Handling:**
- Multi-day calendar selections auto-generate individual session Events
- Each session can have different attendees
- Sessions linked via `parent_event_id` for series management

**Relationships:**
- Many-to-one with Team (tenant isolation)
- Many-to-one with Location (optional)
- Many-to-one with Category (optional)
- Many-to-one with Organizer (optional)
- Many-to-many with Performer (with status: `CONFIRMED`, `CANCELLED`)
- Many-to-many with User (attendees)
- One-to-many with Album

---

### User

**Priority:** High
**Target Epic:** 008 or 009

**Purpose:** Individual photographer identity and authentication.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `uuid` | UUID | unique, not null | External identifier |
| `team_id` | Integer | FK(teams.id), not null | Primary team membership |
| `email` | String(255) | unique, not null | Login email |
| `display_name` | String(255) | not null | Display name |
| `avatar_url` | String(1024) | nullable | Profile image URL |
| `is_active` | Boolean | not null, default=true | Account active |
| `preferences_json` | JSONB | nullable | User preferences |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null | Last modification |

---

### Team

**Priority:** High
**Target Epic:** 008 or 009

**Purpose:** Multi-tenancy boundary for data isolation.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `uuid` | UUID | unique, not null | External identifier |
| `name` | String(255) | unique, not null | Team name |
| `slug` | String(100) | unique, not null | URL-safe identifier |
| `is_personal` | Boolean | not null, default=false | Personal team (solo user) |
| `settings_json` | JSONB | nullable | Team-level settings |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null | Last modification |

**Design Notes:**
- Every user has a personal team created automatically at registration
- Personal teams are hidden from team-switching UI
- All entities are scoped to exactly one team

---

### Camera

**Priority:** Medium
**Target Epic:** 009 or later

**Purpose:** Physical camera equipment tracking and usage analytics.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `uuid` | UUID | unique, not null | External identifier |
| `team_id` | Integer | FK(teams.id), not null | Owning team |
| `camera_id` | String(4) | not null | 4-character camera ID from files |
| `serial_number` | String(100) | nullable | Manufacturer serial number |
| `make` | String(100) | nullable | Manufacturer (Canon, Sony, etc.) |
| `model` | String(100) | nullable | Model name (EOS R5, A7R IV, etc.) |
| `nickname` | String(100) | nullable | User-assigned name |
| `purchase_date` | Date | nullable | When acquired |
| `total_actuations` | Integer | nullable | Estimated shutter count |
| `maintenance_threshold` | Integer | nullable | Actuations before service |
| `notes` | Text | nullable | Equipment notes |
| `metadata_json` | JSONB | nullable | Custom metadata |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null | Last modification |

**Usage Tracking:**
- Actuation counts estimated from image counters and gaps
- Maintenance alerts when approaching threshold
- Historical usage correlated with events

**Disambiguation:**
- Same `camera_id` may appear in multiple events with different physical cameras
- Combination of `camera_id` + Event + Photographer identifies physical camera
- Serial number (from EXIF when available) provides definitive identification

---

### Album

**Priority:** Medium
**Target Epic:** 009 or later

**Purpose:** Logical grouping of images from an Event or session.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `uuid` | UUID | unique, not null | External identifier |
| `team_id` | Integer | FK(teams.id), not null | Owning team |
| `event_id` | Integer | FK(events.id), nullable | Source event |
| `collection_id` | Integer | FK(collections.id), nullable | Primary storage |
| `name` | String(255) | not null | Album name |
| `description` | Text | nullable | Album description |
| `cover_image_id` | Integer | FK(images.id), nullable | Cover thumbnail |
| `image_count` | Integer | nullable | Cached image count |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null | Last modification |

**Collection Relationship:**
- Ideally 1:1 with Collection, but real-world is messier
- Picker tool helps users link Collection images to Albums
- Track image movement between Collections to preserve history

---

### Image

**Priority:** Medium
**Target Epic:** 009 or later

**Purpose:** Individual photo asset with metadata.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `uuid` | UUID | unique, not null | External identifier |
| `team_id` | Integer | FK(teams.id), not null | Owning team |
| `album_id` | Integer | FK(albums.id), nullable | Parent album |
| `collection_id` | Integer | FK(collections.id), not null | Storage location |
| `camera_id` | String(4) | not null | Source camera ID |
| `counter` | String(4) | not null | Image counter from filename |
| `capture_timestamp` | DateTime | nullable | When photo was taken |
| `file_path` | String(1024) | not null | Path within collection |
| `file_size` | BigInteger | nullable | File size in bytes |
| `exif_json` | JSONB | nullable | Extracted EXIF metadata |
| `xmp_json` | JSONB | nullable | XMP sidecar metadata |
| `workflow_node_id` | String(100) | nullable | Current pipeline position |
| `workflow_status` | Enum | nullable | Processing status |
| `created_at` | DateTime | not null | Record creation |
| `updated_at` | DateTime | not null | Last modification |

**Unique Image Identification:**
- Natural key: `camera_id` + `counter` + `capture_timestamp`
- Handles filename suffix variations (processing outputs, numeric differentiators)

**Metadata Reading Strategy:**
- Live collections: Full EXIF/XMP extraction
- Archived collections: Timestamp estimation from event date, user refinement
- Group optimization: Extract from one file (e.g., JPG), apply to related files

---

### Location/Venue

**Priority:** Medium
**Target Epic:** 008-events-calendar

**Purpose:** Event venues and shooting locations.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `uuid` | UUID | unique, not null | External identifier |
| `team_id` | Integer | FK(teams.id), not null | Owning team |
| `name` | String(255) | not null | Location name |
| `address` | Text | nullable | Street address |
| `city` | String(100) | nullable | City |
| `state` | String(100) | nullable | State/Province |
| `country` | String(100) | nullable | Country |
| `latitude` | Decimal(10,7) | nullable | GPS latitude |
| `longitude` | Decimal(10,7) | nullable | GPS longitude |
| `category_id` | Integer | FK(categories.id), nullable | Matched category |
| `rating` | Integer | nullable | 1-5 star rating |
| `rating_lighting` | Integer | nullable | Lighting conditions rating |
| `rating_access` | Integer | nullable | Access/parking rating |
| `rating_equipment` | Integer | nullable | Available equipment rating |
| `notes` | Text | nullable | Location notes |
| `metadata_json` | JSONB | nullable | Custom metadata |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null | Last modification |

---

### Organizer

**Priority:** Low
**Target Epic:** 008-events-calendar

**Purpose:** Event organizers for relationship management.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `uuid` | UUID | unique, not null | External identifier |
| `team_id` | Integer | FK(teams.id), not null | Owning team |
| `name` | String(255) | not null | Organizer name |
| `contact_name` | String(255) | nullable | Primary contact |
| `contact_email` | String(255) | nullable | Contact email |
| `contact_phone` | String(50) | nullable | Contact phone |
| `website` | String(1024) | nullable | Website URL |
| `category_id` | Integer | FK(categories.id), nullable | Primary category |
| `rating` | Integer | nullable | 1-5 star rating |
| `notes` | Text | nullable | Organizer notes |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null | Last modification |

**Rating Purpose:**
- Helps prioritize when schedule conflicts arise
- Historical track record affects future event selection

---

### Performer

**Priority:** Low
**Target Epic:** 008-events-calendar

**Purpose:** Photo subjects (models, demo teams, wildlife species, etc.).

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `uuid` | UUID | unique, not null | External identifier |
| `team_id` | Integer | FK(teams.id), not null | Owning team |
| `name` | String(255) | not null | Performer name |
| `type` | String(100) | nullable | Performer type (model, aircraft, animal) |
| `description` | Text | nullable | Description |
| `reference_images` | JSONB | nullable | Sample image references |
| `website` | String(1024) | nullable | Website/social URL |
| `notes` | Text | nullable | Notes |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null | Last modification |

**Event Association:**
- Many-to-many with Event
- Junction table includes `status`: `CONFIRMED`, `CANCELLED`, `TENTATIVE`

---

### Category

**Priority:** Low
**Target Epic:** 008-events-calendar

**Purpose:** Photography categories/styles for classification.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `uuid` | UUID | unique, not null | External identifier |
| `team_id` | Integer | FK(teams.id), nullable | Owning team (null = system-wide) |
| `name` | String(100) | not null | Category name |
| `icon` | String(50) | nullable | Icon identifier |
| `color` | String(7) | nullable | Hex color code |
| `is_system` | Boolean | not null, default=false | System-provided category |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null | Last modification |

**Default Categories:**
- Sports
- Wildlife
- Portrait
- Landscape
- Air Show
- Wedding
- Event (generic)
- Street
- Architecture
- Macro

---

### Agent

**Priority:** Future
**Target Epic:** 010+

**Purpose:** Local workers for accessing physical storage and offloading computation.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | Internal identifier |
| `uuid` | UUID | unique, not null | External identifier |
| `team_id` | Integer | FK(teams.id), not null | Owning team |
| `name` | String(255) | not null | Agent name |
| `hostname` | String(255) | nullable | Machine hostname |
| `status` | Enum | not null | `ONLINE`, `OFFLINE`, `ERROR` |
| `last_heartbeat` | DateTime | nullable | Last check-in |
| `capabilities_json` | JSONB | nullable | Supported operations |
| `api_key_hash` | String(255) | not null | Authentication key hash |
| `created_at` | DateTime | not null | Creation timestamp |
| `updated_at` | DateTime | not null | Last modification |

**Use Cases:**
- Access local filesystem Collections without cloud upload
- Access SMB shares from local network
- Offload expensive async jobs (image analysis, EXIF extraction)
- Enable hybrid cloud/local architecture

---

## Entity Relationships

### Current State (Implemented)

```
                                    ┌─────────────────┐
                                    │  Configuration  │
                                    │  (standalone)   │
                                    └─────────────────┘

┌─────────────────┐     1:*        ┌─────────────────┐
│    Connector    │◄───────────────│   Collection    │
│  (credentials)  │                │   (storage)     │
└─────────────────┘                └────────┬────────┘
                                            │
                                     CASCADE│ 1:*
                                            ▼
┌─────────────────┐     1:*        ┌─────────────────┐
│    Pipeline     │◄───────────────│ AnalysisResult  │
│   (workflow)    │    SET NULL    │   (results)     │
└────────┬────────┘                └─────────────────┘
         │
  CASCADE│ 1:*
         ▼
┌─────────────────┐
│ PipelineHistory │
│   (versions)    │
└─────────────────┘
```

### Future State (Full Domain)

```
┌──────────────┐
│     Team     │◄─────────────────────────────────────────────┐
└──────┬───────┘                                              │
       │                                                      │
       │ 1:*                                                  │
       ▼                                                      │
┌──────────────┐    *:*     ┌──────────────┐    1:*    ┌──────┴───────┐
│     User     │◄──────────►│    Event     │──────────►│    Album     │
└──────────────┘  attendees └──────┬───────┘           └──────┬───────┘
                                   │                          │
         ┌─────────────────────────┼──────────────────────────┤
         │                         │                          │
         ▼ *:1                     ▼ *:1                      ▼ 1:*
┌──────────────┐          ┌──────────────┐            ┌──────────────┐
│   Location   │          │   Category   │            │    Image     │
└──────────────┘          └──────────────┘            └──────┬───────┘
         │                         │                          │
         │                         ▼ *:1                      │
         │                ┌──────────────┐                    │
         └───────────────►│   Organizer  │                    │
                          └──────────────┘                    │
                                                              │
┌──────────────┐    *:*     ┌──────────────┐                  │
│  Performer   │◄──────────►│    Event     │                  │
└──────────────┘            └──────────────┘                  │
                                                              │
┌──────────────┐    1:*     ┌──────────────┐    1:*           │
│  Connector   │───────────►│  Collection  │◄─────────────────┘
└──────────────┘            └──────┬───────┘
                                   │
                            CASCADE│ 1:*
                                   ▼
┌──────────────┐    1:*     ┌──────────────┐
│   Pipeline   │───────────►│AnalysisResult│
└──────┬───────┘  SET NULL  └──────────────┘
       │
CASCADE│ 1:*
       ▼
┌──────────────┐
│PipelineHistory│
└──────────────┘

┌──────────────┐          ┌──────────────┐
│    Camera    │          │    Agent     │
│ (standalone) │          │  (future)    │
└──────────────┘          └──────────────┘
```

---

## Data Architecture Principles

### 1. Tenant Isolation

Every user-created entity belongs to exactly one Team. Database queries MUST include team filtering:

```python
# Correct: Always filter by team
collections = db.query(Collection).filter(Collection.team_id == current_user.team_id)

# Incorrect: Missing team filter (security vulnerability)
collections = db.query(Collection).all()
```

### 2. Soft Delete vs. Hard Delete

| Entity Type | Delete Strategy | Rationale |
|-------------|-----------------|-----------|
| Configuration | Hard delete | No historical value |
| Collection | Hard delete + CASCADE results | Storage management |
| Connector | RESTRICT if collections exist | Prevent orphans |
| Pipeline | Soft delete (is_active=false) | Preserve historical results |
| Event | Soft delete | Historical record |
| User | Soft delete (is_active=false) | Audit trail |

### 3. Timestamp Management

All entities include:
- `created_at`: Set once at creation (server-side default)
- `updated_at`: Auto-updated on modification (database trigger)

### 4. JSONB Usage Guidelines

Use JSONB for:
- User-defined metadata (`metadata_json`)
- Flexible structures that evolve (`settings_json`, `preferences_json`)
- Extracted data (`exif_json`, `xmp_json`)

Avoid JSONB for:
- Core business attributes (use proper columns)
- Frequently queried fields (use indexed columns)
- Relationship data (use proper foreign keys)

### 5. External Integration Points

| Integration | Entity | Purpose |
|-------------|--------|---------|
| TripIt | Trip (future) | Travel planning for non-local events |
| S3/GCS/SMB | Connector | Remote storage access |
| ML/AI Services | Image | Subject identification, quality assessment |

---

## Appendices

### A. Migration Roadmap

| Phase | Entities | Dependencies |
|-------|----------|--------------|
| Current | Collection, Connector, Pipeline, AnalysisResult, Configuration | - |
| Phase 1 | Team, User | Auth system |
| Phase 2 | Event, Category, Location | Team, User |
| Phase 3 | Album, Image | Event, Collection |
| Phase 4 | Camera, Organizer, Performer | Team |
| Phase 5 | Agent | Team, Infrastructure |

### B. API Endpoint Conventions

All entities follow RESTful conventions:

```
GET    /api/{entity}s          - List (with pagination, filtering)
POST   /api/{entity}s          - Create
GET    /api/{entity}s/{id}     - Read
PUT    /api/{entity}s/{id}     - Update
DELETE /api/{entity}s/{id}     - Delete
GET    /api/{entity}s/stats    - KPI statistics for TopHeader
```

### C. Related Issues

| Issue | Title | Relevance |
|-------|-------|-----------|
| #39 | Add Events repo with React Calendar | Event entity detailed requirements |
| #42 | Add UUID to every relevant object | UUID standard (UUIDv7 + Crockford Base32) |
| #24 | Remote Photo collections persistence | Collection and AnalysisResult foundation |
| #40 | Import S3 Collections from inventory | Collection bulk import |
| #52 | Auto-trigger Collection refresh | Collection state management |

### D. Glossary

| Term | Definition |
|------|------------|
| **Actuation** | Single shutter activation (camera usage metric) |
| **Collection** | Physical storage location containing photo files |
| **Connector** | Authentication credentials for remote storage |
| **Pipeline** | Directed graph defining photo processing workflow |
| **Sidecar** | Metadata file (.xmp) accompanying a photo file |
| **Tenant** | Isolated data boundary (Team) |
| **Termination** | Pipeline end state (classification of image processing outcome) |

---

*This document is maintained as a living reference. Updates should be made when:*
- *New entities are implemented*
- *Entity attributes change significantly*
- *New issues affect domain design*
