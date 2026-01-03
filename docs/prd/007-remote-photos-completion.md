# PRD: Remote Photo Collections - Completion Epic

**Issue**: TBD (continuation of #24)
**Status**: Draft
**Created**: 2026-01-03
**Last Updated**: 2026-01-03
**Original PRD**: [004-remote-photos-persistence.md](./004-remote-photos-persistence.md)
**Related Features**:
- 004-remote-photos-persistence (Phases 1-3 complete)
- 005-ui-migration (complete)
- 006-ux-polish (complete)

---

## Executive Summary

This PRD completes the Remote Photo Collections and Analysis Persistence feature (original #24), implementing the remaining functionality after successful UI modernization. The foundation (database, connectors, collections management) is complete. This epic adds analysis tool execution, pipeline management, trend visualization, and configuration migration - transforming photo-admin from a CLI-only toolset into a full-featured web application.

### What's Already Complete

**Infrastructure (Phases 1-3):**
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ FastAPI backend with WebSocket support
- ✅ Connector management (S3, GCS, SMB with credential encryption)
- ✅ Collection management (local and remote)
- ✅ Modern UI with shadcn/ui, Tailwind CSS, TypeScript
- ✅ Responsive layout with sidebar navigation and topband KPIs
- ✅ Comprehensive test coverage (>80% backend, >75% frontend)

**What This PRD Delivers:**
- Analysis tool execution (PhotoStats, Photo Pairing, Pipeline Validation)
- Pipeline configuration management through forms
- Historical trend analysis across executions
- YAML configuration migration to database
- Production-ready polish and documentation

---

## Background

### Current State

The photo-admin application now has:
- **Modern Web UI**: Fully migrated to shadcn/ui + Tailwind CSS + TypeScript (005-ui-migration)
- **Database Foundation**: PostgreSQL with connectors and collections tables
- **CLI Tools**: PhotoStats, Photo Pairing, Pipeline Validation still operate as standalone scripts
- **Remote Collections**: S3, GCS, and SMB connector support with encrypted credentials
- **UX Polish**: TopHeader KPIs, search functionality, responsive sidebar (006-ux-polish)

### Strategic Interruption

Development of feature 004 was strategically paused after Phase 3 to prevent UI debt:
1. Initial UI (Material-UI) didn't meet quality standards during MVP testing
2. Decision made (documented in `specs/004-remote-photos-persistence/ui-migration.md`) to modernize UI before implementing more features
3. Features 005 (UI Migration) and 006 (UX Polish) completed successfully
4. Result: Solid foundation ready for remaining functionality

### Problem Statement

Despite excellent infrastructure, users still cannot:
1. **Execute Analysis Tools** via web interface - must use CLI
2. **Store Analysis Results** persistently - no historical tracking
3. **Manage Pipelines** through forms - must edit YAML manually
4. **View Trends** over time - no comparison across executions
5. **Migrate Configuration** from YAML to database - inconsistent state

---

## Goals

### Primary Goals

1. **Tool Execution**: Run PhotoStats, Photo Pairing, Pipeline Validation from web UI with real-time progress
2. **Result Persistence**: Store analysis results with HTML reports for historical access
3. **Pipeline Management**: Create/edit/validate pipelines through forms (replacing manual YAML editing)
4. **Trend Analysis**: Visualize metrics over time (orphaned files, camera usage, pipeline consistency)
5. **Configuration Migration**: Import existing YAML config into database with conflict resolution

### Secondary Goals

1. **CLI Integration**: Existing tools read from database (with YAML fallback)
2. **Production Ready**: Security hardening, performance optimization, documentation
3. **Developer Experience**: Comprehensive testing, clear architecture, maintainability

### Non-Goals (v1)

1. **Visual Pipeline Editor**: Form-based only (React Flow graph editor deferred to v2)
2. **User Authentication**: Localhost deployment assumes single user
3. **Real-Time Collaboration**: One user at a time sufficient
4. **Mobile Application**: Responsive web UI only

---

## User Personas

### Primary: Professional Photographer (Alex)
- **Current Pain**: Must run CLI tools manually on each collection, no trend visibility
- **Desired Outcome**: Run analysis on all collections from dashboard, track degradation over time
- **This Epic Delivers**: Web-based tool execution, historical result storage, trend charts

### Secondary: Photo Archive Manager (Jamie)
- **Current Pain**: Cannot compare PhotoStats results across monthly runs
- **Desired Outcome**: Monthly trend report showing which archives are deteriorating
- **This Epic Delivers**: Result history with trend visualization, exportable reports

### Tertiary: Workflow-Focused Photographer (Taylor)
- **Current Pain**: Manually editing YAML pipelines is error-prone, hard to validate
- **Desired Outcome**: Visual pipeline configuration with immediate validation feedback
- **This Epic Delivers**: Form-based pipeline editor with validation, filename preview

---

## User Stories (Remaining from Original PRD)

### User Story 2: Execute Analysis Tools and Store Results (Priority: P1) 🎯 MVP

**As** a photo collection manager
**I want to** run PhotoStats, Photo Pairing, and Pipeline Validation from the web interface
**So that** I can analyze collections without using the command line and access results later

**Acceptance Criteria:**
- Run any tool on any collection with one click
- See real-time progress (files scanned, issues found)
- View results immediately after completion
- Access historical results from previous runs
- Download HTML reports for offline viewing

**Independent Test:** Run PhotoStats on a collection, navigate away, return later to view stored results without re-running

---

### User Story 3: Configure Photo Processing Pipelines Through Forms (Priority: P2)

**As** a workflow-focused photographer
**I want to** create and edit pipelines through web forms instead of YAML
**So that** I can avoid syntax errors and visualize expected filenames before running validation

**Acceptance Criteria:**
- Create pipelines with nodes (Capture, File, Process, Pairing, Branching, Termination)
- Add edges connecting nodes
- Validate structure (detect cycles, orphaned nodes, invalid references)
- Preview expected filenames for a given pipeline
- Activate a pipeline for use with Pipeline Validation tool
- View version history showing changes over time

**Independent Test:** Create pipeline through forms, validate structure, activate it, verify Pipeline Validation tool uses it

---

### User Story 4: Track Analysis Trends Over Time (Priority: P2)

**As** a photo archive manager
**I want to** view trend charts comparing metrics across multiple executions
**So that** I can identify which collections are degrading and when issues started

**Acceptance Criteria:**
- View orphaned file count trends for PhotoStats
- View camera usage distribution trends for Photo Pairing
- View pipeline consistency ratio trends (CONSISTENT/PARTIAL/INCONSISTENT)
- Filter trends by date range
- Compare multiple collections on the same chart

**Independent Test:** Run PhotoStats 3+ times on same collection, view trend chart showing orphaned files over time

---

### User Story 5: Migrate Existing Configuration to Database (Priority: P3)

**As** a current photo-admin CLI user
**I want to** import my existing YAML configuration into the database
**So that** I can use the web interface without losing my custom settings

**Acceptance Criteria:**
- Import config.yaml with one click
- Resolve conflicts between database and YAML values through UI
- CLI tools read configuration from database
- CLI tools fall back to YAML if database unavailable
- Export database configuration back to YAML format

**Independent Test:** Import config.yaml with conflicting keys, resolve conflicts through UI, verify CLI tools read from database

---

## Requirements

### Functional Requirements (Additional to Original PRD)

#### Tool Execution with Modern UI

- **FR-100**: Tool execution UI MUST use shadcn/ui components (Button, Dialog, Progress, Badge)
- **FR-101**: Progress monitor MUST display real-time updates via WebSocket with Tailwind-styled animations
- **FR-102**: Result list MUST use shadcn/ui Table with sorting, pagination, and TypeScript types
- **FR-103**: HTML reports MUST be viewable in shadcn/ui Dialog or separate tab

#### Pipeline Management with Modern UI

- **FR-104**: Pipeline form editor MUST use shadcn/ui Form with react-hook-form + Zod validation
- **FR-105**: Node editor MUST provide type-specific property fields matching TypeScript interfaces
- **FR-106**: Validation errors MUST display with shadcn/ui Alert components and actionable guidance
- **FR-107**: Pipeline list MUST show active badge using shadcn/ui Badge component

#### Trend Visualization

- **FR-108**: Trend charts MUST integrate Recharts with Tailwind CSS theming (existing dependency)
- **FR-109**: Charts MUST use CSS variables from design system (--chart-1 through --chart-5)
- **FR-110**: Date range filters MUST use shadcn/ui DatePicker or Select components

#### Configuration Migration

- **FR-111**: Conflict resolver UI MUST use shadcn/ui Card for side-by-side comparison
- **FR-112**: Import dialog MUST use shadcn/ui Dialog with File upload via Input type="file"
- **FR-113**: Config editor MUST support inline editing with real-time validation

### Non-Functional Requirements (Enhanced)

#### NFR6: Modern UI Consistency
- **NFR6.1**: All new components MUST follow shadcn/ui patterns established in 005-ui-migration
- **NFR6.2**: All new components MUST use TypeScript with strict type checking
- **NFR6.3**: All styling MUST use Tailwind CSS classes (no CSS-in-JS)
- **NFR6.4**: All new pages MUST integrate with TopHeader KPI pattern (from 006-ux-polish)

#### NFR7: Testing (Constitution Compliance)
- **NFR7.1**: Backend test coverage MUST exceed 80% (pytest + pytest-cov)
- **NFR7.2**: Frontend test coverage MUST exceed 75% (Vitest + React Testing Library)
- **NFR7.3**: All API endpoints MUST have unit tests
- **NFR7.4**: All UI components MUST have component tests
- **NFR7.5**: Integration tests MUST cover full user flows

---

## Technical Approach

### Updated Architecture

```
┌─────────────────────────────────────────────────────┐
│     Modern React Frontend (shadcn/ui + TS)          │
│  - TopHeader with dynamic KPIs (HeaderStatsContext) │
│  - Sidebar navigation with collapse (responsive)    │
│  - Tool Execution Dashboard (WebSocket progress)    │
│  - Results & Trend Visualization (Recharts)         │
│  - Pipeline Editor (react-hook-form + Zod)          │
│  - Config Migration (conflict resolution UI)        │
└─────────────────┬───────────────────────────────────┘
                  │ REST API + WebSocket
┌─────────────────▼───────────────────────────────────┐
│        Python Backend (FastAPI) - EXISTING          │
│  - Collection Service ✅                            │
│  - Connector Service ✅                             │
│  - Tool Execution Service (NEW)                     │
│  - Pipeline Service (NEW)                           │
│  - Config Service (NEW)                             │
│  - Result Service (NEW)                             │
│  - Report Generation (Jinja2 templates - EXISTING)  │
└─────────────────┬───────────────────────────────────┘
                  │ SQLAlchemy ORM
┌─────────────────▼───────────────────────────────────┐
│            PostgreSQL Database                      │
│  - connectors ✅                                    │
│  - collections ✅                                   │
│  - analysis_results (NEW)                           │
│  - pipelines (NEW)                                  │
│  - pipeline_history (NEW)                           │
│  - configurations (NEW)                             │
└─────────────────────────────────────────────────────┘
```

### Technology Stack (Current State)

**Backend (Unchanged):**
- Python 3.10+
- FastAPI (async support, WebSocket)
- SQLAlchemy + Alembic (migrations)
- PostgreSQL 12+ with JSONB
- boto3 (S3), google-cloud-storage (GCS), smbprotocol (SMB)
- Jinja2 (HTML report generation)

**Frontend (Updated in 005-ui-migration):**
- React 18.3.1
- TypeScript 5.x
- Vite 6.0.5
- shadcn/ui + Radix UI
- Tailwind CSS v4
- react-hook-form + Zod
- Recharts 2.15.0 (data visualization)
- Lucide React (icons)

**Testing:**
- Backend: pytest, pytest-cov, pytest-mock, pytest-asyncio
- Frontend: Vitest, React Testing Library, MSW (API mocking)

---

## Implementation Plan

### Phase 4: User Story 2 - Tool Execution (Priority: P1) 🎯 MVP

**Duration**: 3-4 weeks
**Tasks**: 91 tasks from original tasks.md (T119-T192q)

**Backend (47 tasks):**
1. AnalysisResult model (JSONB results, report_html storage)
2. ToolService (enqueue, execute, progress tracking)
3. ResultService (list, get, delete, export)
4. WebSocket progress endpoint
5. Integration with existing CLI tools (PhotoStats, Photo Pairing, Pipeline Validation)
6. Comprehensive testing (unit + integration)

**Frontend (27 tasks):**
1. ToolSelector component (shadcn/ui Buttons)
2. ProgressMonitor component (WebSocket integration, Tailwind animations)
3. ResultList component (shadcn/ui Table, filters, pagination)
4. ReportViewer component (iframe with shadcn/ui Dialog)
5. ToolsPage and ResultsPage with TopHeader KPI integration
6. Comprehensive testing (component + integration)

**CLI Integration (7 tasks):**
1. Extend PhotoAdminConfig to support database connection
2. Database-first with YAML fallback logic
3. Update all CLI tools to use unified config

**Testing (10 tasks):**
- Backend: ToolService, ResultService, API endpoints, WebSocket
- Frontend: Hooks, components, user flows

**Checkpoint**: Users can run tools via web UI, monitor progress, view stored results with >80% backend and >75% frontend test coverage

---

### Phase 5: User Story 3 - Pipeline Management (Priority: P2)

**Duration**: 2-3 weeks
**Tasks**: 70 tasks from original tasks.md (T193-T248n)

**Backend (34 tasks):**
1. Pipeline model (config JSONB, version, is_active)
2. PipelineHistory model (change tracking)
3. PipelineService (CRUD, validation, activation, versioning)
4. StructureValidator integration (cycle detection, orphaned nodes)
5. FilenamePreviewGenerator (expected filenames for pipeline)
6. Import/export YAML functionality
7. Comprehensive testing

**Frontend (28 tasks):**
1. PipelineList component (shadcn/ui Table, active badge)
2. PipelineFormEditor component (react-hook-form + Zod)
3. NodeEditor component (type-specific property forms)
4. Validation error display (shadcn/ui Alert)
5. Filename preview (modal with expected outputs)
6. Version history view
7. PipelinesPage with TopHeader integration
8. Comprehensive testing

**Testing (8 tasks):**
- Backend: PipelineService, validation, activation, YAML import/export
- Frontend: Form validation, node editing, activation flow

**Checkpoint**: Users can manage pipelines through forms, validate structure, preview filenames with >80% backend and >75% frontend test coverage

---

### Phase 6: User Story 4 - Trend Analysis (Priority: P2)

**Duration**: 1-2 weeks
**Tasks**: 19 tasks from original tasks.md (T249-T261f)

**Backend (6 tasks):**
1. Trend analysis endpoint (metric extraction from JSONB)
2. Support PhotoStats metrics (orphaned_files_count)
3. Support Photo Pairing metrics (camera_usage)
4. Support Pipeline Validation metrics (consistency ratios)
5. Comprehensive testing

**Frontend (10 tasks):**
1. TrendChart component (Recharts + Tailwind theming)
2. PhotoStats trend: line chart (orphaned files over time)
3. Photo Pairing trend: multi-line chart (camera usage)
4. Pipeline Validation trend: stacked area chart (consistency ratios)
5. Date range filter (shadcn/ui Select or DatePicker)
6. Collection comparison mode
7. ResultsPage "Trends" tab
8. Comprehensive testing

**Testing (3 tasks):**
- Backend: Trend endpoint, JSONB queries, metric extraction
- Frontend: Chart rendering, interactions, filtering

**Checkpoint**: Users can view trends across executions with >80% backend and >75% frontend test coverage

---

### Phase 7: User Story 5 - Configuration Migration (Priority: P3)

**Duration**: 2 weeks
**Tasks**: 52 tasks from original tasks.md (T262-T302k)

**Backend (21 tasks):**
1. Configuration model (key-value JSONB)
2. ConfigService (get, update, import YAML, export YAML)
3. Conflict detection (compare database vs YAML)
4. Session-based conflict resolution (1-hour expiry)
5. Comprehensive testing

**Frontend (24 tasks):**
1. ConfigPage (inline editing for extensions, cameras, methods)
2. ConflictResolver component (side-by-side comparison with shadcn/ui Card)
3. Import dialog (file upload with shadcn/ui Dialog)
4. Export functionality
5. First-run import prompt
6. Comprehensive testing

**Testing (7 tasks):**
- Backend: ConfigService, conflict detection, session management, YAML format
- Frontend: Conflict resolution, import flow, config editing

**Checkpoint**: Users can migrate YAML config with conflict resolution, CLI tools use database with >80% backend and >75% frontend test coverage

---

### Phase 8: Production Polish (Priority: P1)

**Duration**: 1-2 weeks
**Tasks**: 33 tasks from original tasks.md (T303-T335)

**Documentation (8 tasks):**
1. Backend README (setup, migrations, environment)
2. Frontend README (setup, component library)
3. Root README update (web application overview)
4. CLAUDE.md update (reflect new features, remove outdated info)
5. Quickstart guide (developer onboarding)
6. User documentation

**Security (7 tasks):**
1. Rate limiting (slowapi middleware)
2. Request size limits (file uploads)
3. CSRF protection headers
4. SQL injection validation (verify SQLAlchemy ORM usage)
5. Input sanitization (XSS prevention)
6. Credential access audit logging

**Performance (7 tasks):**
1. Database connection pooling tuning
2. Query optimization (indexes verification)
3. JSONB query optimization (GIN indexes)
4. API caching (config endpoint)
5. Lazy loading (collection file listings)
6. Frontend pagination optimization
7. WebSocket message frequency tuning

**Code Quality (5 tasks):**
1. Backend linter (ruff check)
2. Frontend linter (eslint)
3. UTF-8 encoding validation
4. Error handling consistency
5. Sensitive data logging review

**Validation (6 tasks):**
1. Quickstart validation (fresh install)
2. User story independence verification
3. CLI database-first verification
4. CLI YAML fallback verification
5. Performance target verification
6. Cache effectiveness verification

**Checkpoint**: Production-ready application with comprehensive documentation and security hardening

---

## Phase Dependencies

### Critical Path
1. ✅ **Phase 1-3 (Complete)**: Foundation, infrastructure, collections/connectors
2. 🎯 **Phase 4 (P1 - MVP Core)**: Tool execution - REQUIRED for value delivery
3. **Phase 5 (P2)**: Pipelines - Depends on Phase 4 for Pipeline Validation integration
4. **Phase 6 (P2)**: Trends - Depends on Phase 4 for AnalysisResult data
5. **Phase 7 (P3)**: Config migration - Independent, can run parallel to Phase 5-6
6. **Phase 8 (P1)**: Polish - After all features complete

### Parallel Opportunities
- **Phase 5 + Phase 7** can proceed in parallel (no dependencies)
- **Phase 6** requires Phase 4 complete (needs AnalysisResult model)
- Within each phase, tasks marked [P] in original tasks.md can run parallel

---

## Success Metrics

### Adoption Metrics
- **M1**: 80% of PhotoStats users switch to web interface within 1 month
- **M2**: 60% of Pipeline Validation users switch from YAML editing to forms within 2 months
- **M3**: 50% of users access historical results at least once per week

### Performance Metrics
- **M4**: Tool execution time within 10% of CLI performance
- **M5**: 95% of WebSocket progress updates delivered within 500ms
- **M6**: Trend chart rendering completes within 1 second for 100+ data points
- **M7**: Pipeline validation feedback displays within 2 seconds

### Quality Metrics
- **M8**: Zero data loss incidents in production usage
- **M9**: Test coverage >80% backend, >75% frontend (constitution compliance)
- **M10**: Pipeline configuration errors reduced by 70% vs manual YAML editing
- **M11**: All Lighthouse scores >90 (performance, accessibility, best practices)

---

## Risks and Mitigation

### Risk 1: WebSocket Scalability
- **Impact**: Medium - Concurrent tool executions may degrade performance
- **Probability**: Medium (if many users)
- **Mitigation**: Job queue limits concurrent executions; background worker pattern; WebSocket message throttling

### Risk 2: Large Result Sets (JSONB)
- **Impact**: Medium - Very large analysis results may slow queries
- **Probability**: Low (results typically <1MB)
- **Mitigation**: JSONB GIN indexing; result pagination; lazy loading for details

### Risk 3: Pipeline Validation Complexity
- **Impact**: High - Incorrect validation logic could allow invalid pipelines
- **Probability**: Low (extensive testing planned)
- **Mitigation**: Comprehensive unit tests for StructureValidator; integration tests with real pipeline configs; YAML import validation

### Risk 4: CLI Tool Breaking Changes
- **Impact**: High - Alienates existing users
- **Probability**: Low (YAML fallback maintained)
- **Mitigation**: Database-first with YAML fallback; extensive integration testing; phased rollout

### Risk 5: UI Consistency Drift
- **Impact**: Low - New components may not match 005/006 design system
- **Probability**: Medium
- **Mitigation**: Strict adherence to shadcn/ui patterns; code review checklist; design system documentation

---

## Open Questions

1. **Job Queue Persistence**: Should job queue persist to database or remain in-memory? (Trade-off: durability vs simplicity)
2. **Pipeline Graph Complexity**: What's the maximum number of nodes to support in v1? (Impacts form UX design)
3. **Result Retention**: Should old results auto-delete after X days? (Storage management)
4. **Export Formats**: Beyond HTML reports, should we support CSV/JSON export?
5. **Notification System**: Should tool completion trigger browser notifications?
6. **Multi-Pipeline Activation**: Allow multiple active pipelines or enforce single active?

---

## Testing Strategy

### Coverage Targets (Constitution Compliance)
- **Backend**: >80% for services, models, API endpoints (pytest-cov)
- **Frontend**: >75% for components, hooks, pages (Vitest + React Testing Library)
- **Overall**: >75% project-wide coverage

### Test Types
1. **Unit Tests**: Individual functions, components, services
2. **Integration Tests**: Full workflows (create → execute → view results)
3. **API Tests**: All endpoints with success/error cases
4. **WebSocket Tests**: Connection, progress, completion events
5. **Type Tests**: TypeScript compilation catches type errors
6. **Accessibility Tests**: ARIA, keyboard navigation, color contrast

### Testing Infrastructure (Existing)
- Backend: pytest + pytest-cov + pytest-mock + pytest-asyncio
- Frontend: Vitest + React Testing Library + MSW + jest-dom
- Test fixtures in conftest.py (backend) and setup.js (frontend)
- MSW handlers for API mocking
- Custom test utilities (test-utils.tsx for providers)

---

## Timeline Estimate

### Aggressive (Single Developer)
- **Phase 4**: 3 weeks (91 tasks - MVP critical)
- **Phase 5**: 2.5 weeks (70 tasks)
- **Phase 6**: 1 week (19 tasks)
- **Phase 7**: 2 weeks (52 tasks)
- **Phase 8**: 1.5 weeks (33 tasks)
- **Total**: ~10 weeks (2.5 months)

### Conservative (with Buffer)
- **Phase 4**: 4 weeks
- **Phase 5**: 3 weeks
- **Phase 6**: 1.5 weeks
- **Phase 7**: 2.5 weeks
- **Phase 8**: 2 weeks
- **Total**: ~13 weeks (3.25 months)

### Parallel Team (2 Developers)
- **Phase 4**: 3 weeks (both developers)
- **Phase 5 + 7**: 2.5 weeks (parallel work)
- **Phase 6**: 1 week
- **Phase 8**: 1.5 weeks
- **Total**: ~8 weeks (2 months)

---

## Future Enhancements (Post-Completion)

### v2.0: Visual Pipeline Editor
- React Flow integration for drag-and-drop pipeline creation
- Auto-layout algorithms for complex pipelines
- Real-time validation with visual feedback
- Minimap for large pipeline navigation

### v2.1: Advanced Analytics
- Anomaly detection in trends (sudden spikes)
- Predictive alerts (storage running out)
- Comparative analysis across collections
- Custom metric definitions

### v2.2: Multi-User Support
- User authentication (local or OAuth)
- Role-based access control
- Shared workspaces
- Concurrent editing with conflict resolution

### v2.3: Automation
- Scheduled analysis runs (cron-like)
- Webhook notifications on completion
- Auto-remediation workflows
- Integration with external tools (Slack, email)

---

## Dependencies

### External Dependencies
- PostgreSQL 12+ instance (already configured)
- Cloud storage accounts for testing (S3, GCS - optional)
- Master encryption key (PHOTO_ADMIN_MASTER_KEY env var - already setup)

### Internal Dependencies
- ✅ Phases 1-3 complete (connectors, collections, modern UI)
- ✅ Pipeline processor infrastructure (utils/pipeline_processor.py)
- ✅ Existing CLI tools (photo_stats.py, photo_pairing.py)
- ✅ Jinja2 templates (templates/photostats.html.j2, photo_pairing.html.j2)
- ✅ shadcn/ui design system (from 005-ui-migration)
- ✅ TopHeader KPI pattern (from 006-ux-polish)

---

## Appendix

### Related Documents
- **Original PRD**: [004-remote-photos-persistence.md](./004-remote-photos-persistence.md)
- **Original Tasks**: `specs/004-remote-photos-persistence/tasks.md` (Phases 4-8)
- **UI Migration Strategy**: `specs/004-remote-photos-persistence/ui-migration.md`
- **UI Migration Complete**: `specs/005-ui-migration/IMPLEMENTATION_SUMMARY.md`
- **UX Polish Complete**: `specs/006-ux-polish/spec.md`

### Key Architectural Decisions
1. **Database-First with YAML Fallback**: Maintains CLI compatibility while enabling web features
2. **Form-Based Pipeline Editor (v1)**: Simpler implementation, defer visual graph to v2
3. **Single Active Pipeline**: Enforces consistency, reduces user confusion
4. **Pre-Generated HTML Reports**: Store report_html in database for fast access
5. **WebSocket for Progress**: Better UX than polling, acceptable for localhost deployment

### Technology Choices Locked In
- **shadcn/ui + Tailwind**: Modern UI established in 005-ui-migration, all new components must follow
- **TypeScript**: All new frontend code must be TypeScript with strict checking
- **react-hook-form + Zod**: Form validation pattern established, continue for consistency
- **Recharts**: Already integrated, use for trend visualization
- **Vitest + RTL**: Testing pattern established, maintain for consistency

---

## Revision History
- **2026-01-03 (v1)**: Initial draft based on remaining tasks from 004-remote-photos-persistence
  - Updated for modern UI stack (shadcn/ui, Tailwind, TypeScript)
  - Integrated with completed features 005-ui-migration and 006-ux-polish
  - Focused on Phases 4-8 from original tasks.md
  - Added TopHeader KPI integration requirements
  - Enhanced testing strategy for constitution compliance
