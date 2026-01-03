# Implementation Plan: UI Migration to Modern Design System

**Branch**: `005-ui-migration` | **Date**: 2026-01-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-ui-migration/spec.md`

## Summary

Migrate the Photo Admin web frontend from Material-UI to shadcn/ui with Tailwind CSS and TypeScript. This migration transforms the existing connector and collection management interface (implemented in Feature 004 Phase 3) into a modern, professional dark-themed application with improved developer experience and reduced bundle size. The migration maintains 100% functional parity while establishing a modern design system for future features.

**Strategic Decision**: Migrate NOW (after Phase 3, before implementing Phases 4-7 of Feature 004) to minimize scope (11 components vs 25+ later) and ensure all future features inherit the modern stack from day one.

**Technical Approach**: Hybrid migration strategy that preserves React 18.3.1 + Vite architecture while replacing only the UI layer and adding TypeScript. This avoids the complexity of a full Next.js migration while delivering immediate value through improved design and bundle size reduction (~500KB).

## Technical Context

**Language/Version**: TypeScript 5.x (migration from JavaScript ES6+), React 18.3.1
**Primary Dependencies**:
- UI: shadcn/ui + Radix UI primitives, Tailwind CSS v4.1.9
- Forms: react-hook-form, Zod validation
- Icons: Lucide React
- Utils: clsx, tailwind-merge
- Build: Vite 6.0.5 (unchanged)

**Storage**: N/A (frontend only, uses existing PostgreSQL backend API)
**Testing**: Vitest + React Testing Library (unchanged), target coverage >75%
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge - last 2 versions), desktop-first (1280px+), basic responsive mobile support
**Project Type**: Web application (frontend only migration)
**Performance Goals**:
- First Contentful Paint <1.5s
- Bundle size reduction ~500KB (from ~800KB to ~300KB)
- Interactive elements respond <100ms
- Form validation <200ms

**Constraints**:
- MUST maintain 100% functional parity with Material-UI version
- MUST preserve all existing API integration
- MUST maintain test coverage >75%
- MUST complete TypeScript migration without blocking development

**Scale/Scope**:
- 2 pages (Connectors, Collections)
- 11 components (6 feature components, 2 hooks, navigation components)
- ~11 test files
- Migration-only (no new features)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- [x] **Independent CLI Tools**: N/A - This is a frontend web application, not a CLI tool. Constitution principle applies to Python CLI tools in the toolbox (PhotoStats, Photo Pairing). Web frontend is exempt from this requirement.

- [x] **Testing & Quality**:
  - ✅ Tests are planned - all existing Vitest tests will be migrated
  - ✅ Test framework configured - Vitest + React Testing Library already set up
  - ✅ Test coverage addressed - MUST maintain >75% coverage (FR-024)
  - ✅ Tests independently runnable - Vitest configuration supports this

- [x] **User-Centric Design**:
  - N/A HTML report generation (web app, not analysis tool)
  - ✅ Error messages clear and actionable - FR-018 requires clear error display
  - ✅ Implementation is simple (YAGNI) - Migration-only, no premature abstractions, reusing shadcn/ui components
  - N/A Structured logging (frontend uses console logging, backend handles structured logs)

- [x] **Shared Infrastructure**: N/A - This is a web frontend, not a Python CLI tool. Frontend has its own infrastructure (React components, hooks, services) separate from Python CLI tools.

- [x] **Simplicity**:
  - ✅ Simplest approach - Hybrid migration (keep React + Vite, change only UI layer) vs full Next.js rewrite
  - ✅ No premature abstractions - Using shadcn/ui components directly, no custom component library
  - ✅ Minimal dependencies - Only essential libraries (shadcn/ui, Tailwind, react-hook-form, Zod)

**Violations/Exceptions**: None. All principles apply to Python CLI tools. Web frontend follows appropriate web development standards while adhering to general quality and simplicity principles.

## Project Structure

### Documentation (this feature)

```text
specs/005-ui-migration/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output - Migration strategy decisions
├── data-model.md        # Phase 1 output - Component hierarchy and type definitions
├── quickstart.md        # Phase 1 output - Developer setup guide
├── contracts/           # Phase 1 output - Component prop interfaces
└── checklists/
    └── requirements.md  # Spec quality validation
```

### Source Code (repository root)

```text
# Web application structure (Option 2)
backend/
├── src/
│   ├── models/         # Unchanged - existing database models
│   ├── services/       # Unchanged - existing business logic
│   └── api/            # Unchanged - existing FastAPI endpoints
└── tests/              # Unchanged - existing backend tests

frontend/
├── src/
│   ├── components/     # MIGRATED - React components
│   │   ├── layout/     # NEW - Sidebar, TopHeader, MainLayout
│   │   ├── connectors/ # MIGRATED - ConnectorList, ConnectorForm
│   │   ├── collections/# MIGRATED - CollectionList, CollectionForm, CollectionStatus, FiltersSection
│   │   └── ui/         # NEW - shadcn/ui components (Button, Table, Dialog, etc.)
│   ├── pages/          # MIGRATED - ConnectorsPage, CollectionsPage
│   ├── hooks/          # MIGRATED - useConnectors, useCollections
│   ├── services/       # MIGRATED - api.ts, connectors.ts, collections.ts
│   ├── types/          # NEW - TypeScript type definitions
│   │   ├── index.ts    # Barrel exports
│   │   ├── connector.ts# Connector types
│   │   └── collection.ts# Collection types
│   ├── lib/            # NEW - Utility functions
│   │   └── utils.ts    # cn() helper, class utilities
│   ├── App.tsx         # MIGRATED - Root component with MainLayout
│   ├── main.tsx        # MIGRATED - Entry point
│   └── globals.css     # NEW - Tailwind directives + design tokens
├── tests/
│   ├── components/     # MIGRATED - Component tests
│   ├── hooks/          # MIGRATED - Hook tests
│   └── integration/    # MIGRATED - Integration tests
├── tailwind.config.js  # NEW - Tailwind configuration
├── postcss.config.js   # NEW - PostCSS configuration
├── tsconfig.json       # NEW - TypeScript configuration
└── vite.config.ts      # UPDATED - TypeScript support, path aliases
```

**Structure Decision**: Using existing web application structure (frontend + backend). This is a frontend-only migration - the backend directory remains completely unchanged. All work occurs in the `frontend/` directory, migrating JavaScript files to TypeScript and replacing Material-UI components with shadcn/ui components.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations to track. All constitution principles that apply to web applications are satisfied.

## Phase 0: Outline & Research

### Research Questions

Based on the comprehensive migration plan already documented in `/specs/004-remote-photos-persistence/ui-migration.md`, most technical decisions have been made. The research phase will consolidate these decisions and verify remaining unknowns:

1. **Design System Verification**: Confirm shadcn/ui component API compatibility with Vite (already verified in migration plan)
2. **TypeScript Migration Strategy**: Document incremental TypeScript adoption approach (strict vs gradual typing)
3. **Form Library Integration**: Verify react-hook-form + Zod integration patterns for dynamic forms
4. **Testing Strategy**: Document approach for updating tests with new component selectors
5. **CSS Variables Browser Support**: Verify Tailwind CSS v4 + CSS variables work in target browsers

### Research Output Structure

`research.md` will consolidate the strategic decisions from the existing migration plan:

- **UI Library Choice**: shadcn/ui + Radix UI (rationale: copy-paste architecture, Tailwind integration, tree-shakeable)
- **CSS Framework**: Tailwind CSS v4 (rationale: utility-first, design token system, better DX than CSS-in-JS)
- **Form Management**: react-hook-form + Zod (rationale: type-safe validation, performance, React 18 compatibility)
- **TypeScript Approach**: Incremental migration with gradual strictness (rationale: avoid blocking progress, refine types over time)
- **Testing Updates**: Component-by-component test migration alongside implementation (rationale: avoid big-bang, maintain coverage)

## Phase 1: Design & Contracts

### Data Model

The frontend data model consists of TypeScript interfaces for entities and form schemas:

**Core Entities** (from spec.md Key Entities):
- `Connector`: name, type (S3/GCS/SMB), active status, credentials (type-specific)
- `Collection`: name, type (LOCAL/S3/GCS/SMB), state (LIVE/CLOSED/ARCHIVED), location, connector_id, accessibility, cache_ttl
- `DesignToken`: CSS variable definitions (colors, spacing, radii)
- `FormSchema`: Zod validation schemas for forms

**Component Props**: TypeScript interfaces for all component props

**API Response Types**: Typed responses for all API calls

### API Contracts

Frontend migration does NOT change backend API contracts. All existing REST endpoints remain unchanged:

**Existing Backend API** (unchanged):
```
GET    /api/connectors
POST   /api/connectors
GET    /api/connectors/{id}
PUT    /api/connectors/{id}
DELETE /api/connectors/{id}
POST   /api/connectors/{id}/test

GET    /api/collections
POST   /api/collections
GET    /api/collections/{id}
PUT    /api/collections/{id}
DELETE /api/collections/{id}
POST   /api/collections/{id}/test
```

**Frontend Contracts** (NEW - TypeScript interfaces):
- Component prop interfaces in `/contracts/components/`
- API response type definitions in `/contracts/api/`
- Form schema definitions in `/contracts/forms/`

### Quickstart

`quickstart.md` will provide developer onboarding:

1. Prerequisites (Node.js, npm)
2. Install new dependencies (`npm install`)
3. TypeScript configuration overview
4. Running dev server (`npm run dev`)
5. Running tests (`npm test`)
6. Type checking (`npm run type-check`)
7. Component library usage (shadcn/ui CLI)
8. Adding new shadcn components (`npx shadcn@latest add <component>`)

## Phase 2: Task Planning (via /speckit.tasks)

Task planning will be handled by the `/speckit.tasks` command. The implementation will follow the 6-phase structure documented in `/specs/004-remote-photos-persistence/ui-migration.md`:

**PHASE 0: Setup & Infrastructure** (8 hours)
- Install Tailwind CSS, shadcn/ui, TypeScript
- Configure design tokens and CSS variables
- Set up path aliases and build tools

**PHASE 1: Layout Migration** (15 hours)
- Build Sidebar, TopHeader, MainLayout components
- Update App.tsx with new layout
- Implement navigation state management

**PHASE 2: Connectors Page Migration** (18 hours)
- Migrate ConnectorList, ConnectorForm, ConnectorsPage
- Update useConnectors hook to TypeScript
- Update connectors service with types

**PHASE 3: Collections Page Migration** (18 hours)
- Migrate CollectionList, CollectionForm, CollectionStatus, FiltersSection
- Implement tab navigation
- Update useCollections hook and collections service

**PHASE 4: Shared Services & Utils Migration** (6 hours)
- Update API service with TypeScript
- Create shared type definitions
- Update main.tsx and index files

**PHASE 5: Testing Migration** (18 hours)
- Update test infrastructure for TypeScript
- Migrate all component, hook, and integration tests
- Verify test coverage >75%

**PHASE 6: Polish & Quality Assurance** (12 hours)
- Dark theme implementation verification
- Bundle size optimization
- Accessibility audit (keyboard nav, ARIA, contrast)
- Responsive design testing
- Remove old MUI dependencies
- Documentation updates

**Total Estimated Effort**: 95 hours (3 weeks for 1 developer)

## Migration Strategy

### Approach

**Hybrid Migration** (NOT full framework rewrite):
- **KEEP**: React 18.3.1, Vite 6.0.5, React Router, Axios, Vitest
- **REPLACE**: Material-UI → shadcn/ui, Emotion → Tailwind CSS, JavaScript → TypeScript

**Rationale** (from migration plan):
- Faster migration (3 weeks vs 6-8 weeks for Next.js)
- Lower risk (keep familiar React patterns)
- Immediate value (modern UI without framework rewrite)
- Progressive enhancement (can migrate to Next.js later if needed)

### Risk Mitigation

**Component API Differences**:
- Follow migration plan with gradual replacement
- Update tests alongside components
- Comprehensive testing before deployment

**TypeScript Complexity**:
- Incremental adoption (allow `any` initially, refine later)
- Type errors should not block development
- Focus on core business logic types first

**Test Update Effort**:
- Migrate tests component-by-component
- Buffer time in estimates
- Maintain test coverage throughout

**Scope Creep**:
- Strict "migration only" rule
- No new features during migration
- Defer enhancements to separate features

## Success Metrics

From spec.md Success Criteria:

**Performance**:
- Bundle size: ~500KB reduction (800KB → 300KB)
- First Contentful Paint: <1.5s
- Interactive response: <100ms
- Form validation: <200ms

**Quality**:
- TypeScript: 0 compilation errors
- Test coverage: >75%
- Lighthouse accessibility: ≥90
- Browser compatibility: 95% consistency (Chrome, Firefox, Safari, Edge)

**User Experience**:
- Same or fewer clicks for all tasks
- WCAG AA contrast ratios (4.5:1 normal, 3:1 large text)
- Keyboard navigation fully functional
- Page navigation: <2 seconds

## Dependencies

**Prerequisite Features**:
- ✅ Feature 004 Phase 3 complete (connector + collection management MVP with tests)

**External Dependencies**:
- shadcn/ui + Radix UI
- Tailwind CSS v4.1.9
- TypeScript 5.x
- react-hook-form
- Zod
- Lucide React
- clsx, tailwind-merge

**Internal Dependencies**:
- Backend API unchanged (PostgreSQL + FastAPI)
- Existing test infrastructure (Vitest + React Testing Library)

## Out of Scope

**Explicitly Excluded** (from spec.md):
- Next.js framework migration
- New pages beyond navigation placeholders (Dashboard, Workflows, Assets, Analytics, Team, Settings)
- User authentication backend integration
- Notifications backend
- Light theme and theme switching
- Feature 004 Phases 4-7 migration (Tool Execution, Pipeline Forms, Trend Charts, Config Migration UI)
- Internationalization (i18n)
- Custom component development beyond shadcn/ui
- Advanced animations/transitions
- Advanced mobile UX (basic responsive only)

## Reference Materials

**Primary Resources**:
- `/specs/004-remote-photos-persistence/ui-migration.md` - Complete 6-phase migration plan with task breakdown
- `/specs/004-remote-photos-persistence/ui-style-proposal/` - Reference implementation with design tokens, components, and visual examples
- `/specs/005-ui-migration/spec.md` - Feature specification with user stories and requirements

**Technical Documentation**:
- shadcn/ui docs: https://ui.shadcn.com
- Tailwind CSS v4 docs: https://tailwindcss.com
- react-hook-form docs: https://react-hook-form.com
- Zod docs: https://zod.dev

## Notes

- This is a **migration-only** feature - no functional changes to existing features
- All task estimates from ui-migration.md are preserved in Phase 2 planning
- Strategic decision to migrate NOW (11 components) vs LATER (25+ components) saves 185-255 hours
- 64 future tasks in Phases 4-7 will inherit modern stack without migration overhead
