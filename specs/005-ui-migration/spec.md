# Feature Specification: UI Migration to Modern Design System

**Feature Branch**: `005-ui-migration`
**Created**: 2026-01-01
**Status**: Draft
**Input**: User description: "Issue #34: make sure to take into account all the research material already documented in /specs/004-remote-photos-persistence/ui-migration.md and /spec/004-remote-photos-persistence/ui-style-proposal in the repo."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Modern Dark Theme Experience (Priority: P1)

Users can access the photo collection management interface with a modern, professional dark theme that provides clear visual hierarchy and is comfortable for extended viewing sessions.

**Why this priority**: The visual redesign is the core value proposition of this feature. Without the dark theme and modern layout, the migration provides no user benefit.

**Independent Test**: Can be fully tested by loading any page in the application and verifying the dark theme is applied consistently with proper contrast ratios, and delivers immediate visual improvement over the Material-UI interface.

**Acceptance Scenarios**:

1. **Given** a user opens the application, **When** they navigate to any page, **Then** they see a consistent dark theme with proper color hierarchy (background, card, primary, accent colors)
2. **Given** a user views the sidebar, **When** they look at menu items, **Then** active items are clearly distinguished from inactive items with accent colors
3. **Given** a user reads text content, **When** viewing in different lighting conditions, **Then** all text maintains readable contrast (WCAG AA compliance)
4. **Given** a user interacts with buttons and controls, **When** hovering over interactive elements, **Then** they see smooth visual feedback with appropriate hover states

---

### User Story 2 - Sidebar Navigation (Priority: P1)

Users can navigate the application using a persistent sidebar that shows all available sections and clearly indicates the current location.

**Why this priority**: Navigation is fundamental - without it, users cannot access different parts of the application. This is an MVP requirement.

**Independent Test**: Can be fully tested by loading the application and clicking through all sidebar menu items to verify routing works correctly, and delivers the core navigation experience.

**Acceptance Scenarios**:

1. **Given** a user opens the application, **When** they view the sidebar, **Then** they see all menu items (Dashboard, Workflows, Collections, Assets, Analytics, Team, Settings) with appropriate icons
2. **Given** a user is on the Collections page, **When** they view the sidebar, **Then** the Collections menu item is highlighted with an accent background
3. **Given** a user clicks a sidebar menu item, **When** the navigation completes, **Then** the corresponding page loads and the sidebar highlights the new active item
4. **Given** a user views the sidebar, **When** they look at the organization branding section, **Then** they see the "PA" logo and "Photo Admin" text clearly displayed
5. **Given** a user scrolls the menu items, **When** there are many items, **Then** the menu area scrolls while the logo and footer remain fixed

---

### User Story 3 - Top Header with Context (Priority: P1)

Users can see contextual information about the current page and system status in a top header that displays page title, key metrics, and user profile access.

**Why this priority**: The header provides critical context and access to user functions. Part of the core layout that defines the user experience.

**Independent Test**: Can be fully tested by navigating to any page and verifying the header shows correct page title and placeholder metrics, and delivers essential page context.

**Acceptance Scenarios**:

1. **Given** a user navigates to Collections page, **When** they view the top header, **Then** they see the page icon and title "Photo Collections" on the left
2. **Given** a user views the top header, **When** on the Collections page, **Then** they see collection count and storage metrics displayed
3. **Given** a user views the top header, **When** they look at the right section, **Then** they see a notifications bell icon and user profile with initials
4. **Given** a user hovers over the profile button, **When** the mouse enters the area, **Then** they see a subtle hover state indicating interactivity

---

### User Story 4 - Collections List View (Priority: P2)

Users can view and filter their photo collections in a table with tabs for different collection views and filters for state, type, and accessibility.

**Why this priority**: This is the primary content view for collection management. Critical for users but can be tested after layout is established.

**Independent Test**: Can be fully tested by loading the Collections page and interacting with tabs, filters, and table to verify all display and filtering features work, and delivers the core data browsing experience.

**Acceptance Scenarios**:

1. **Given** a user is on the Collections page, **When** they view the page header, **Then** they see "Collections" title and a "NEW COLLECTION" button
2. **Given** a user views the Collections page, **When** they look at the tabs, **Then** they see "All Collections", "Recently Accessed", and "Archived" tabs with the active tab highlighted
3. **Given** a user clicks a tab, **When** the click completes, **Then** the tab becomes active with a primary-colored bottom border
4. **Given** a user views the filters section, **When** they interact with dropdowns, **Then** they can filter by State (All, Live, Closed, Archived) and Type (All, Local, S3, GCS, SMB)
5. **Given** a user views the filters section, **When** they check the "Accessible Only" checkbox, **Then** the filter is applied to show only accessible collections
6. **Given** a user views the collections table, **When** they look at the rows, **Then** each collection shows name, type badge, state badge, status indicator, and action buttons
7. **Given** a user hovers over action buttons (Info, Refresh, Edit, Delete), **When** hovering, **Then** they see appropriate hover states and tooltips

---

### User Story 5 - Form Components with Validation (Priority: P2)

Users can create and edit connectors and collections using modern forms with inline validation, dynamic field visibility, and clear error messages.

**Why this priority**: Forms enable data creation/editing. Important but secondary to viewing existing data. Can be tested independently of other stories.

**Independent Test**: Can be fully tested by opening create/edit dialogs and submitting forms with valid and invalid data to verify validation and submission, and delivers the data management capability.

**Acceptance Scenarios**:

1. **Given** a user clicks "NEW CONNECTOR", **When** the dialog opens, **Then** they see a form with fields for name, type selection, and dynamic credential fields
2. **Given** a user selects a connector type (S3, GCS, SMB), **When** the selection changes, **Then** the form shows type-specific credential fields
3. **Given** a user enters invalid data, **When** they attempt to submit, **Then** they see inline validation errors with clear messages
4. **Given** a user fills all required fields correctly, **When** they submit the form, **Then** the form validates, submits data, and closes on success
5. **Given** a user creates a collection, **When** selecting type as "S3", **Then** they see a connector dropdown populated with available S3 connectors
6. **Given** a user creates a LOCAL collection, **When** the form loads, **Then** the connector field is hidden automatically
7. **Given** a user clicks "Test Connection" on a connector form, **When** the test runs, **Then** they see a loading spinner followed by success/error feedback

---

### User Story 6 - Type Safety and Developer Experience (Priority: P3)

Developers working on the frontend code benefit from TypeScript type checking, preventing common errors and improving code maintainability.

**Why this priority**: While valuable for long-term maintenance, TypeScript doesn't directly impact end users. Can be implemented gradually.

**Independent Test**: Can be fully tested by running TypeScript compiler and verifying no type errors, and delivers improved code quality for future development.

**Acceptance Scenarios**:

1. **Given** a developer runs `npm run type-check`, **When** compilation completes, **Then** there are no TypeScript errors
2. **Given** a developer imports a component, **When** they use it in code, **Then** IDE autocomplete suggests correct prop names and types
3. **Given** a developer calls an API service function, **When** typing the call, **Then** TypeScript enforces correct parameter types and return type expectations
4. **Given** a developer modifies a type definition, **When** dependent code has mismatches, **Then** the TypeScript compiler reports errors at build time

---

### User Story 7 - Responsive Design (Priority: P3)

Users can access the application on different screen sizes (mobile, tablet, desktop) with layouts that adapt appropriately.

**Why this priority**: Nice to have for broader accessibility, but desktop is the primary use case for photo administration. Can be added after core features work.

**Independent Test**: Can be fully tested by viewing the application at different viewport widths and verifying layout adjusts appropriately, and delivers multi-device support.

**Acceptance Scenarios**:

1. **Given** a user accesses the app on a mobile device (375px width), **When** they view the interface, **Then** the sidebar collapses or transforms to a hamburger menu
2. **Given** a user views a table on mobile, **When** the table is wider than the screen, **Then** the table scrolls horizontally within its container
3. **Given** a user accesses the app on a tablet (768px width), **When** they view the layout, **Then** all content remains readable and interactive
4. **Given** a user views the app on an ultra-wide monitor (2560px+), **When** content loads, **Then** content areas have reasonable max-widths to maintain readability

---

### Edge Cases

- What happens when a user has disabled JavaScript and CSS variables are not supported?
- How does the system handle browser theme preferences (prefers-color-scheme: light)?
- What happens when a very long collection name or error message exceeds its container width?
- How does the interface handle loading states when API responses are delayed?
- What happens when there are zero collections or connectors to display (empty states)?
- How does keyboard navigation work for users who cannot use a mouse?
- What happens when a user rapidly clicks filter controls multiple times?
- How does the system handle network errors during form submission?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace Material-UI components with shadcn/ui components throughout the application
- **FR-002**: System MUST apply a consistent dark theme using CSS variables defined in the design system
- **FR-003**: System MUST provide a sidebar navigation component with logo, menu items, active state highlighting, and version footer
- **FR-004**: System MUST provide a top header component with page title, contextual metrics, notifications icon, and user profile
- **FR-005**: System MUST maintain all existing functionality of connector management (create, edit, delete, test connection, filtering)
- **FR-006**: System MUST maintain all existing functionality of collection management (create, edit, delete, test connection, filtering, state/type selection)
- **FR-007**: System MUST implement tab navigation on Collections page with "All Collections", "Recently Accessed", and "Archived" tabs
- **FR-008**: System MUST provide filter controls for collection state (All, Live, Closed, Archived) and type (All, Local, S3, GCS, SMB)
- **FR-009**: System MUST implement an "Accessible Only" checkbox filter for collections
- **FR-010**: System MUST display collection status with visual indicators (green for accessible, red for not accessible)
- **FR-011**: System MUST show type badges for collections (Local, S3, GCS, SMB) with distinct visual styling
- **FR-012**: System MUST show state badges for collections (Live, Closed, Archived) with distinct visual styling
- **FR-013**: System MUST implement form validation using react-hook-form and Zod schemas
- **FR-014**: System MUST show dynamic credential fields in connector forms based on selected connector type
- **FR-015**: System MUST hide connector selection field when collection type is LOCAL
- **FR-016**: System MUST show connector dropdown for collection types S3, GCS, and SMB
- **FR-017**: System MUST provide loading states for asynchronous operations (form submission, test connection, data fetching)
- **FR-018**: System MUST display error messages clearly when operations fail
- **FR-019**: System MUST provide success feedback using toast notifications
- **FR-020**: System MUST implement hover states for all interactive elements (buttons, links, table rows)
- **FR-021**: System MUST use Lucide icons consistently throughout the interface
- **FR-022**: System MUST convert all JavaScript files to TypeScript with proper type annotations
- **FR-023**: System MUST define TypeScript interfaces for all data entities (Connector, Collection, etc.)
- **FR-024**: System MUST maintain test coverage above 75% during migration
- **FR-025**: System MUST preserve all existing API integration and data handling logic
- **FR-026**: System MUST implement keyboard navigation support for all interactive elements
- **FR-027**: System MUST provide ARIA labels for accessibility on icon-only buttons
- **FR-028**: System MUST implement focus indicators that are visible for keyboard navigation
- **FR-029**: System MUST use Tailwind CSS for all styling, removing Emotion/CSS-in-JS
- **FR-030**: System MUST maintain component architecture with separation of pages, components, hooks, and services

### Key Entities

- **Connector**: Represents a remote storage connection with properties including name, type (S3/GCS/SMB), active status, and type-specific credentials
- **Collection**: Represents a photo collection with properties including name, type (LOCAL/S3/GCS/SMB), state (LIVE/CLOSED/ARCHIVED), location, connector reference (for remote types), accessibility status, and optional cache TTL
- **Design Token**: CSS variables defining the visual design system including colors (background, foreground, primary, accent, border, etc.), spacing, and border radius
- **Form Schema**: Validation rules for connector and collection forms using Zod, defining required fields, format validation, and conditional requirements

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete all existing connector and collection management tasks with the same number of clicks or fewer compared to the Material-UI version
- **SC-002**: All text content achieves WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text) in the dark theme
- **SC-003**: Application bundle size reduces by approximately 500KB after removing Material-UI dependencies
- **SC-004**: First Contentful Paint improves to under 1.5 seconds
- **SC-005**: All interactive elements respond to hover and focus states within 100ms
- **SC-006**: TypeScript compilation completes without errors
- **SC-007**: Test suite maintains coverage above 75% with all tests passing
- **SC-008**: Users can navigate the entire application using only keyboard controls
- **SC-009**: Forms validate input and display error messages within 200ms of user interaction
- **SC-010**: 95% of UI components render consistently across Chrome, Firefox, Safari, and Edge browsers
- **SC-011**: Lighthouse accessibility score achieves 90 or higher
- **SC-012**: Users can identify the current page and navigate to any other section within 2 seconds

## Assumptions

- The existing React 18.3.1 and Vite setup remains unchanged (no migration to Next.js in this phase)
- The existing API backend remains unchanged and compatible with the migrated frontend
- All existing tests use Vitest and React Testing Library, which will continue to be used
- The dark theme is the default and primary theme (light theme support is optional for future iterations)
- The ui-style-proposal reference implementation provides accurate design specifications
- Desktop browsers (1280px+ viewport) are the primary target; mobile support is secondary
- User authentication and notifications are placeholder elements (no backend integration required yet)
- The sidebar menu structure matches the proposed design even though some pages don't exist yet
- shadcn/ui components are compatible with Vite (verified in research documentation)
- Tailwind CSS v4 is stable and production-ready
- All developers have access to the research materials in /specs/004-remote-photos-persistence/

## Dependencies

- Completion of Feature 004 Phase 3 (connector and collection management MVP with tests)
- shadcn/ui library and Radix UI primitives
- Tailwind CSS v4.1.9
- TypeScript 5.x compiler
- react-hook-form library for form management
- Zod library for schema validation
- Lucide React for icons
- clsx and tailwind-merge utilities for class name management

## Out of Scope

- Migration to Next.js framework (deferred to potential future feature)
- Implementation of Dashboard, Workflows, Assets, Analytics, Team, or Settings pages beyond navigation placeholders
- User authentication and session management backend integration
- Notifications backend and real-time notification delivery
- Light theme implementation and theme switching functionality
- Migration of Phases 4-7 of Feature 004 (Tool Execution, Pipeline Forms, Trend Charts, Config Migration UI)
- Performance optimization beyond bundle size reduction from dependency removal
- Internationalization (i18n) support
- Custom component development beyond shadcn/ui library
- Animation and transition effects beyond basic hover states
- Advanced responsive features like sidebar drawer for mobile (basic responsive is in scope, advanced mobile UX is out)

## Risk Assessment

### Technical Risks

- **Component API differences**: shadcn/ui components may have different APIs than Material-UI requiring significant code changes
  - *Mitigation*: Follow migration plan with gradual component-by-component replacement and comprehensive testing

- **TypeScript migration complexity**: Converting all JavaScript to TypeScript may reveal hidden bugs or type incompatibilities
  - *Mitigation*: Use incremental TypeScript adoption, starting with `any` types where needed and refining over time

- **Test update effort**: Updating tests for new component selectors and interactions may take longer than estimated
  - *Mitigation*: Buffer time in estimates, update tests alongside component migration to avoid big-bang approach

- **Browser compatibility**: CSS variables and Tailwind features may not work in older browsers
  - *Mitigation*: Target modern browsers only (last 2 versions), document browser support requirements

### Schedule Risks

- **Learning curve**: Team may need time to become proficient with new tools (shadcn/ui, Tailwind, TypeScript)
  - *Mitigation*: Pair programming, reference documentation, start with simpler components first

- **Scope creep**: Temptation to add new features during migration rather than maintaining parity
  - *Mitigation*: Strict adherence to "migration only" principle, defer enhancements to separate features

### User Impact Risks

- **Regression bugs**: Migration may introduce functional regressions that impact users
  - *Mitigation*: Comprehensive test coverage, QA testing before deployment, gradual rollout strategy

- **User confusion**: Interface changes may temporarily confuse existing users
  - *Mitigation*: Maintain functional parity, provide clear visual hierarchy, ensure all existing workflows remain intuitive
