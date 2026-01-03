# Research: UX Polish Epic

**Branch**: `006-ux-polish`
**Created**: 2026-01-03
**Status**: Complete

## Overview

This document captures research findings for the three features in the UX Polish Epic. Since the existing codebase provides clear patterns and no NEEDS CLARIFICATION markers were identified, this research focuses on confirming best practices and documenting implementation approaches.

---

## Issue #37: Topband KPIs

### Research Question: How to aggregate collection/connector statistics efficiently?

**Decision**: Use SQLAlchemy aggregate queries with dedicated `/stats` endpoints

**Rationale**:
- The existing Collection and Connector models provide all necessary fields for aggregation
- Dedicated endpoints allow independent caching (KPIs cached longer than list data)
- Simple COUNT/SUM aggregations are efficient on indexed columns
- Collection model already has `is_accessible` and state fields indexed

**Alternatives Considered**:
1. **Include stats in list response**: Rejected - couples KPI caching with list pagination
2. **Materialized views**: Rejected - over-engineering for expected data volumes
3. **Client-side aggregation**: Rejected - inefficient, requires fetching all records

### Research Question: What KPI values can be computed from existing data?

**Finding**: Based on Collection model analysis:

| KPI | Data Source | Computation |
|-----|-------------|-------------|
| Total Collections | `collections` table | `COUNT(*)` |
| Storage Used | Not currently stored | NEEDS SCHEMA UPDATE |
| Number of Files | Not currently stored | NEEDS SCHEMA UPDATE |
| Number of Images | Not currently stored (requires grouping) | NEEDS SCHEMA UPDATE |
| Active Connectors | `connectors.is_active` | `COUNT(*) WHERE is_active=true` |
| Total Connectors | `connectors` table | `COUNT(*)` |

**Important Discovery**: The Collection model does NOT currently store `storage_used`, `file_count`, or `image_count` fields. These values would need to be:
1. Added as columns to the Collection model, OR
2. Computed dynamically from cached file listings (expensive), OR
3. Stored during collection scan/refresh operations

**Recommendation**: Add `storage_bytes`, `file_count`, and `image_count` columns to Collection model. Populate during accessibility test and cache refresh operations. This aligns with simplicity principle and avoids expensive runtime aggregations.

---

## Issue #38: Collection Search

### Research Question: Best practice for text search with SQL injection protection?

**Decision**: Use SQLAlchemy's `ilike()` with parameterized queries

**Rationale**:
- SQLAlchemy automatically parameterizes queries when using ORM methods
- `ilike()` provides case-insensitive LIKE matching (PostgreSQL-specific but portable)
- Existing `list_collections()` method already uses query builder pattern
- Input length limiting provides defense-in-depth

**Implementation Pattern**:
```python
# Safe - SQLAlchemy parameterizes automatically
query = query.filter(Collection.name.ilike(f"%{search}%"))
```

**Alternatives Considered**:
1. **Full-text search (pg_trgm, GIN indexes)**: Rejected - over-engineering for collection name search
2. **Elasticsearch**: Rejected - massive over-engineering for simple name filtering
3. **Client-side filtering**: Rejected - doesn't scale, doesn't work with pagination

### Research Question: Should search be debounced on frontend or rate-limited on backend?

**Decision**: Frontend debouncing (300ms) with no backend rate limiting

**Rationale**:
- Debouncing prevents excessive API calls during typing
- Backend rate limiting adds complexity without proportional benefit
- Single-user admin tool doesn't need protection against abuse
- 300ms debounce is standard UX pattern

---

## Issue #41: Responsive Menu Collapse

### Research Question: Current mobile breakpoint and responsive behavior?

**Finding**: Based on Sidebar.tsx analysis:
- Mobile breakpoint uses Tailwind's `md:` prefix (768px)
- Below 768px: Sidebar hidden, hamburger menu in TopHeader
- Above 768px: Sidebar always visible
- State management via `isMobileMenuOpen` in MainLayout

**Decision**: Add intermediate "tablet" state using localStorage for manual collapse

**Implementation Pattern**:
```typescript
// useSidebarCollapse hook
const [isManuallyCollapsed, setIsManuallyCollapsed] = useLocalStorage('sidebar-collapsed', false)

// Sidebar shows collapse arrow only when:
// - Screen width > 768px (md breakpoint)
// - User hasn't already collapsed it
```

### Research Question: How to position collapse control on sidebar border?

**Decision**: Absolute-positioned arrow button on right edge of sidebar

**Rationale**:
- Follows common UI pattern (VS Code, Notion, etc.)
- Non-intrusive when not needed
- Clear affordance for interaction
- Animate rotation for visual feedback (ChevronLeft → ChevronRight)

**Visual Design**:
```
┌──────────────┬─────────────────────────────────┐
│              │◀                                │
│   Sidebar    │   Main Content                  │
│              │                                 │
└──────────────┴─────────────────────────────────┘
                ^
                Collapse arrow on sidebar border
```

---

## Schema Changes Required

Based on research, the following schema changes are needed for Issue #37:

### Collection Model Additions

| Field | Type | Description |
|-------|------|-------------|
| `storage_bytes` | `BigInteger` | Total storage in bytes (nullable, populated during scan) |
| `file_count` | `Integer` | Total number of files (nullable, populated during scan) |
| `image_count` | `Integer` | Number of images after grouping (nullable, populated during scan) |
| `last_scanned_at` | `DateTime` | Already exists - used for "Recently Scanned" |

**Migration**: Alembic migration to add three columns with NULL defaults.

**Population Strategy**: Update these fields during:
1. Initial accessibility test (count files)
2. Cache refresh operation (full scan)
3. Manual "Refresh Collection" action

---

## Frontend Dependencies Audit

### Existing Dependencies (no changes needed)
- `lucide-react`: Already used for icons (will use ChevronLeft, Pin icons)
- `@/lib/utils`: cn() utility for conditional classNames
- `localStorage`: Native browser API for collapse state

### No New Dependencies Required
All features can be implemented with existing dependencies.

---

## Summary

| Feature | Research Status | Schema Changes | New Dependencies |
|---------|-----------------|----------------|------------------|
| KPIs | Complete | 3 new columns on Collection | None |
| Search | Complete | None | None |
| Collapse | Complete | None | None |

All research questions resolved. Ready for Phase 1 design.
