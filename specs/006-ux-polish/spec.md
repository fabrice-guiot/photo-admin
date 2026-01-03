# Feature Specification: UX Polish Epic

**Feature Branch**: `006-ux-polish`
**Created**: 2026-01-03
**Status**: Draft
**Input**: Epic bundling three UX enhancements with backend dependencies: Issue #37 (Topband KPIs), Issue #38 (Collection Search), Issue #41 (Menu Collapse)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Dashboard KPI Metrics (Priority: P1)

An administrator opens the Collections or Connectors page and immediately sees key performance indicators displayed at the top of the page. These metrics provide an at-a-glance summary of the system state without requiring the user to scroll or navigate elsewhere. The KPIs remain constant regardless of any filters applied on the page, showing totals for the entire system.

**Why this priority**: KPIs provide immediate visibility into system health and capacity. Users need to understand the overall state of their photo management system at a glance, which is the most common use case when landing on these pages.

**Independent Test**: Can be fully tested by navigating to Collections/Connectors pages and verifying KPI values match expected aggregated data. Delivers immediate value by showing system overview.

**Acceptance Scenarios**:

1. **Given** the Collections page loads, **When** the user views the topband area, **Then** they see four KPI cards: Total Collections (count), Storage Used (formatted size in GB/TB), Number of Files (total count), and Number of Images (count after grouping)
2. **Given** the Connectors page loads, **When** the user views the topband area, **Then** they see two KPI cards: Active Connectors (count where active=true) and Total Connectors (count of all connectors)
3. **Given** the user applies filters on the Collections page, **When** the filtered results change, **Then** the KPI values remain unchanged showing system-wide totals
4. **Given** a new collection is created, **When** the user returns to the Collections page, **Then** the KPIs reflect the updated totals

---

### User Story 2 - Search Collections by Name (Priority: P2)

An administrator with many collections wants to quickly find a specific collection without scrolling through a long list. They type part of the collection name into a search field, and the list immediately filters to show only matching collections.

**Why this priority**: Search is essential for usability as the number of collections grows. It directly impacts daily workflow efficiency and is a standard expectation in list views.

**Independent Test**: Can be tested by entering search text and verifying the collection list filters correctly. Delivers value by enabling fast navigation to specific collections.

**Acceptance Scenarios**:

1. **Given** the Collections page displays a search input field, **When** the user types a partial name, **Then** the collection list filters to show only collections with names containing the search text (case-insensitive)
2. **Given** a search term is entered, **When** the user clears the search field, **Then** all collections are displayed again
3. **Given** special characters are entered in the search field, **When** the search is performed, **Then** the system handles them safely without errors (protected against injection attacks)
4. **Given** no collections match the search term, **When** the search is performed, **Then** an appropriate empty state message is displayed

---

### User Story 3 - Collapse Sidebar on Tablet (Priority: P3)

A user on a tablet device in landscape mode wants more screen space for the main content area. They click a collapse button on the sidebar border to minimize the menu to a hamburger-style overlay, gaining additional horizontal space. They can later restore the full sidebar by clicking a pin button.

**Why this priority**: Tablet optimization improves the experience for mobile-oriented users but is not as critical as core functionality. The current responsive design already works; this enhancement provides additional control.

**Independent Test**: Can be tested by using the collapse/pin actions on a tablet-width viewport and verifying menu behavior. Delivers value by providing better screen real estate management.

**Acceptance Scenarios**:

1. **Given** the user is on a screen above the mobile breakpoint but below desktop optimal width, **When** they click the collapse arrow on the sidebar border, **Then** the sidebar collapses to hamburger mode as if on a mobile device
2. **Given** the sidebar is manually collapsed (hamburger mode visible), **When** the user opens the hamburger menu, **Then** they see both a Close button and a Pin button
3. **Given** the hamburger menu is open after manual collapse, **When** the user clicks the Pin button, **Then** the sidebar returns to its normal expanded state and the collapse control reappears
4. **Given** the user is on a screen below the mobile breakpoint, **When** they view the sidebar, **Then** the manual collapse arrow is not visible (hamburger is already the default behavior)
5. **Given** the user manually collapses the sidebar, **When** they resize to a larger screen, **Then** the collapsed state persists until they explicitly pin it back

---

### Edge Cases

- What happens when the database returns null values for storage or file counts? Display "0" or appropriate fallback.
- How does the system handle extremely long search queries? Truncate or limit input length to prevent performance issues.
- What happens if KPI aggregation takes too long? Show loading states for individual KPIs.
- How does collapse state persist across page navigation? Store preference locally.
- What if a user types rapidly in the search field? Debounce API calls to avoid excessive requests.

## Requirements *(mandatory)*

### Functional Requirements

#### Issue #37: Topband KPIs

- **FR-001**: System MUST provide an API endpoint for Collection KPIs returning: total_collections (count), storage_used (bytes), file_count (total), image_count (grouped)
- **FR-002**: System MUST provide an API endpoint for Connector KPIs returning: active_connectors (count), total_connectors (count)
- **FR-003**: KPI values MUST NOT be affected by any filter parameters applied to the list view
- **FR-004**: KPI API endpoints MUST be separate from the list endpoints to allow independent caching
- **FR-005**: Storage Used MUST be calculated as the sum of storage across all collections
- **FR-006**: Number of Images MUST represent the count after Image Group pairing logic is applied within each collection
- **FR-007**: Frontend MUST display KPIs in a card-based topband layout above the list view
- **FR-008**: KPI values MUST be formatted for human readability (e.g., "2.5 TB" instead of bytes)

#### Issue #38: Collection Search

- **FR-009**: System MUST add a search query parameter to the Collections list API endpoint
- **FR-010**: Search MUST filter collections by name using case-insensitive partial matching
- **FR-011**: Search parameter MUST be protected against SQL injection using parameterized queries
- **FR-012**: Frontend MUST display a search input field on the Collections page
- **FR-013**: Search MUST be performed on the backend to ensure consistent filtering with pagination
- **FR-014**: Empty search input MUST return all collections (no filter applied)
- **FR-015**: Search MUST work in combination with existing filters (state, type, accessible_only)

#### Issue #41: Responsive Menu Collapse

- **FR-016**: Sidebar MUST display a collapse control (arrow icon) on the border between menu and main content when screen width is above mobile breakpoint
- **FR-017**: Clicking the collapse control MUST transition the sidebar to hamburger/overlay mode
- **FR-018**: When in manually-collapsed mode, the hamburger menu MUST show both Close and Pin actions
- **FR-019**: Pin action MUST restore the sidebar to its normal expanded state
- **FR-020**: Collapse control MUST NOT be visible when screen is at or below mobile breakpoint
- **FR-021**: User's collapse preference MUST persist across page navigation within the same session
- **FR-022**: Collapse state MUST be stored locally (browser storage) to persist across browser refreshes

### Key Entities *(include if feature involves data)*

- **Collection Statistics**: Aggregated metrics for all collections (total count, storage, files, images)
- **Connector Statistics**: Aggregated metrics for all connectors (active count, total count)
- **Sidebar State**: User preference for collapsed/expanded state (local storage)
- **Search Query**: User-provided text string for filtering collections by name

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view all KPI metrics within 1 second of page load on both Collections and Connectors pages
- **SC-002**: Users can filter collections by name and see results within 500ms of typing
- **SC-003**: Search functionality handles 100+ character inputs without errors or performance degradation
- **SC-004**: Sidebar collapse action completes animation within 300ms
- **SC-005**: KPI values correctly reflect actual data counts verified against database queries
- **SC-006**: No security vulnerabilities detected in search functionality (parameterized queries confirmed)
- **SC-007**: Collapse state persists correctly across 10 consecutive page navigations
- **SC-008**: All three features work correctly on viewport widths from 768px to 1920px

## Assumptions

- The existing Collection model contains or can access storage_used data for aggregation
- Image grouping logic already exists and can be leveraged for the image count KPI
- The current responsive breakpoint for mobile hamburger menu is a known CSS value that can be referenced
- Local storage is available and acceptable for storing UI preferences
- The current API structure supports adding new endpoints and query parameters
- Frontend build process supports any required new dependencies for animations

## Dependencies

- Issue #37 (KPIs) depends on existing Collection and Connector data models
- Issue #38 (Search) depends on existing Collections API structure
- Issue #41 (Menu Collapse) depends on existing Sidebar component architecture
- Backend KPI endpoints must be implemented before frontend KPI display
- Search API parameter must be implemented before frontend search input

## Out of Scope

- Sorting collections by search relevance (simple partial matching only)
- KPI historical trends or graphs (static current values only)
- Remembering collapse preference across different devices
- Search suggestions or autocomplete
- Keyboard shortcuts for menu collapse
