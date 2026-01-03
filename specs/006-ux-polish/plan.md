# Implementation Plan: UX Polish Epic

**Branch**: `006-ux-polish` | **Date**: 2026-01-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-ux-polish/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This Epic bundles three GitHub issues (#37, #38, #41) into a cohesive UX enhancement package:

1. **Topband KPIs (Issue #37)**: Add aggregate statistics endpoints and display cards on Collections/Connectors pages
2. **Collection Search (Issue #38)**: Add text search capability to filter collections by name
3. **Responsive Menu Collapse (Issue #41)**: Add manual collapse control for sidebar on tablet-sized screens

The technical approach leverages existing infrastructure: FastAPI backend with SQLAlchemy/PostgreSQL, React frontend with TypeScript and Tailwind CSS.

## Technical Context

**Language/Version**: Python 3.10+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy (backend); React 18.3.1, Tailwind CSS, Lucide Icons (frontend)
**Storage**: PostgreSQL 12+ with existing collections/connectors tables
**Testing**: pytest (backend), Vitest/React Testing Library (frontend)
**Target Platform**: Web application (modern browsers)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: KPI load <1s, search results <500ms, collapse animation <300ms
**Constraints**: SQL injection protection required for search, debounced search input
**Scale/Scope**: Small enhancement epic - 2 API endpoints, 3 UI features

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- [x] **Independent CLI Tools**: N/A - This is a web application feature, not a CLI tool. Does not conflict with CLI tool architecture.
- [x] **Testing & Quality**: Tests planned for both backend (pytest) and frontend. Coverage targets specified in spec.
- [x] **User-Centric Design**:
  - For analysis tools: N/A (not an analysis tool)
  - Are error messages clear and actionable? Yes - edge cases specify user-friendly fallbacks
  - Is the implementation simple (YAGNI)? Yes - simple aggregation queries, basic text search, CSS transitions
  - Is structured logging included for observability? Yes - existing logging patterns will be followed
- [x] **Shared Infrastructure**: N/A for PhotoAdminConfig - this is the web UI/API layer
- [x] **Simplicity**: Yes - each feature has minimal complexity:
  - KPIs: Simple COUNT/SUM SQL aggregations
  - Search: ILIKE with parameterized query
  - Collapse: Local storage + CSS transitions

**Violations/Exceptions**: None. All features align with simplicity-first development philosophy.

## Project Structure

### Documentation (this feature)

```text
specs/006-ux-polish/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── collections.py     # Existing - add search param + stats endpoint
│   │   └── connectors.py      # Existing - add stats endpoint
│   ├── services/
│   │   └── collection_service.py  # Existing - add search filter logic
│   └── schemas/
│       └── collection.py      # Existing - add KPI response schemas
└── tests/
    └── unit/
        ├── test_api_collections.py  # Add search + stats tests
        └── test_api_connectors.py   # Add stats tests

frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx        # Modify - add collapse control + pin button
│   │   │   └── MainLayout.tsx     # Modify - add collapse state management
│   │   ├── collections/
│   │   │   └── CollectionList.tsx # Modify - add search input
│   │   └── ui/
│   │       └── kpi-card.tsx       # New - reusable KPI card component
│   ├── pages/
│   │   ├── CollectionsPage.tsx    # Modify - add KPIs + search
│   │   └── ConnectorsPage.tsx     # Modify - add KPIs
│   ├── hooks/
│   │   ├── useCollections.ts      # Modify - add search param + stats fetch
│   │   ├── useConnectors.ts       # Modify - add stats fetch
│   │   └── useSidebarCollapse.ts  # New - localStorage + collapse state
│   └── contracts/
│       └── api/
│           ├── collection-api.ts  # Modify - add stats types
│           └── connector-api.ts   # Modify - add stats types
└── tests/
    └── components/
        └── layout/
            └── Sidebar.test.tsx   # Add collapse behavior tests
```

**Structure Decision**: Uses existing web application structure. No new directories beyond the new hooks and UI component files.

## Complexity Tracking

> No violations. All features follow simplicity-first approach.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | - | - |
