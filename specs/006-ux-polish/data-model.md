# Data Model: UX Polish Epic

**Branch**: `006-ux-polish`
**Created**: 2026-01-03

## Overview

This document defines the data model changes and new entities required for the UX Polish Epic features.

---

## Schema Changes

### Collection Model Extensions

Add three new columns to support KPI aggregation:

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `storage_bytes` | `BigInteger` | Yes | `NULL` | Total storage used in bytes |
| `file_count` | `Integer` | Yes | `NULL` | Total number of files in collection |
| `image_count` | `Integer` | Yes | `NULL` | Number of images after grouping |

**Rationale**: Storing aggregated values avoids expensive runtime calculations. These values are populated during collection scan/refresh operations.

**Migration**: Alembic migration to add columns with NULL defaults (backward compatible).

```python
# Collection model additions
storage_bytes = Column(BigInteger, nullable=True)  # Bytes, can exceed 2^31
file_count = Column(Integer, nullable=True)
image_count = Column(Integer, nullable=True)
```

### Connector Model

No changes required. Existing fields support KPI calculations:
- `is_active`: Boolean for active connector count
- Implicit count of all records for total connectors

---

## Response Schemas

### CollectionStatsResponse

New schema for Collection KPI endpoint response:

```python
class CollectionStatsResponse(BaseModel):
    """Aggregated statistics for all collections."""
    total_collections: int
    storage_used_bytes: int
    storage_used_formatted: str  # e.g., "2.5 TB"
    file_count: int
    image_count: int
```

**Field Descriptions**:
- `total_collections`: Count of all collections (regardless of state)
- `storage_used_bytes`: Sum of `storage_bytes` across all collections
- `storage_used_formatted`: Human-readable storage (bytes → KB → MB → GB → TB)
- `file_count`: Sum of `file_count` across all collections
- `image_count`: Sum of `image_count` across all collections

### ConnectorStatsResponse

New schema for Connector KPI endpoint response:

```python
class ConnectorStatsResponse(BaseModel):
    """Aggregated statistics for all connectors."""
    total_connectors: int
    active_connectors: int
```

**Field Descriptions**:
- `total_connectors`: Count of all connectors
- `active_connectors`: Count of connectors where `is_active=true`

---

## Entity Relationships

```
┌──────────────────────────────────────────────────────────────┐
│                         Collections                           │
├──────────────────────────────────────────────────────────────┤
│ id (PK)                                                       │
│ name                                                          │
│ type (LOCAL/S3/GCS/SMB)                                      │
│ state (LIVE/CLOSED/ARCHIVED)                                 │
│ location                                                      │
│ connector_id (FK → connectors.id)                            │
│ is_accessible                                                 │
│ storage_bytes [NEW]        ← KPI aggregation                 │
│ file_count [NEW]           ← KPI aggregation                 │
│ image_count [NEW]          ← KPI aggregation                 │
│ ...                                                           │
└──────────────────────────────────────────────────────────────┘
                    │
                    │ many-to-one
                    ▼
┌──────────────────────────────────────────────────────────────┐
│                         Connectors                            │
├──────────────────────────────────────────────────────────────┤
│ id (PK)                                                       │
│ name                                                          │
│ type (S3/GCS/SMB)                                            │
│ is_active                  ← KPI filter                      │
│ ...                                                           │
└──────────────────────────────────────────────────────────────┘
```

---

## Frontend State Entities

### SidebarCollapseState

Stored in browser localStorage:

```typescript
interface SidebarCollapseState {
  isManuallyCollapsed: boolean
}
```

**Storage Key**: `sidebar-collapsed`
**Default Value**: `false`
**Persistence**: Survives page refresh and browser restart

---

## Search Query Model

No database changes. Search is a query parameter on existing list endpoint:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search` | `string` | No | Case-insensitive partial match on collection name |

**Constraints**:
- Maximum length: 100 characters
- Special characters allowed but escaped in query
- Empty string treated as "no filter"

---

## Aggregation Queries

### Collection Stats Query

```sql
SELECT
    COUNT(*) as total_collections,
    COALESCE(SUM(storage_bytes), 0) as storage_used_bytes,
    COALESCE(SUM(file_count), 0) as file_count,
    COALESCE(SUM(image_count), 0) as image_count
FROM collections;
```

### Connector Stats Query

```sql
SELECT
    COUNT(*) as total_connectors,
    COUNT(*) FILTER (WHERE is_active = true) as active_connectors
FROM connectors;
```

---

## Validation Rules

### Collection Model (Extended)

| Field | Validation |
|-------|------------|
| `storage_bytes` | >= 0 when not NULL |
| `file_count` | >= 0 when not NULL |
| `image_count` | >= 0, <= file_count when both not NULL |

### Search Query Parameter

| Rule | Description |
|------|-------------|
| Length | 0-100 characters |
| Characters | Any UTF-8 characters allowed |
| SQL Injection | Prevented via parameterized queries |

---

## State Transitions

### Collection Statistics Population

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Created        │──────│  Accessible     │──────│  Scanned        │
│  (stats NULL)   │      │  (test passed)  │      │  (stats filled) │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                                           │
                                                           ▼
                                              ┌─────────────────────┐
                                              │  Refreshed          │
                                              │  (stats updated)    │
                                              └─────────────────────┘
```

Statistics are populated during:
1. Accessibility test (initial creation)
2. Cache refresh operation
3. Manual "Refresh Collection" action

---

## Migration Plan

### Phase 1: Schema Migration

1. Create Alembic migration for new columns
2. Run migration (adds nullable columns)
3. No data backfill needed (NULL is valid state)

### Phase 2: Code Updates

1. Update Collection model with new fields
2. Update accessibility test to populate stats
3. Update cache refresh to populate stats
4. Add stats endpoints to API

### Phase 3: Frontend Integration

1. Add stats hooks and API calls
2. Create KPI card components
3. Integrate into pages
