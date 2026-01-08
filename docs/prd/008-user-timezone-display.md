# PRD: User Timezone Display

**Issue**: TBD
**Status**: Draft
**Created**: 2026-01-07
**Last Updated**: 2026-01-07

---

## Executive Summary

Display all timestamps in the web UI in the user's local timezone using browser-based detection. Backend continues storing timestamps in UTC (current behavior), while the frontend formats dates for display using the device's timezone. This approach requires minimal changes, no backend modifications, and provides immediate value without waiting for a user account system.

---

## Background

### Current State

**Backend:**
- Timestamps stored in PostgreSQL using `datetime.utcnow()` (UTC-naive)
- API responses serialize timestamps to ISO 8601 format (e.g., `"2025-12-30T10:30:00"`)
- No timezone suffix in responses (implicitly UTC)

**Frontend:**
- Basic `formatDate()` function in `ConnectorList.tsx` using `toLocaleString()`
- No centralized date formatting utility
- No relative time display ("2 hours ago")
- Format depends entirely on browser locale

**Key Files:**
- `backend/src/models/collection.py` - `created_at`, `updated_at` fields
- `backend/src/models/connector.py` - `created_at`, `updated_at`, `last_validated` fields
- `frontend/src/components/connectors/ConnectorList.tsx` - inline `formatDate()` function

### Problem Statement

1. **No centralized formatting**: Date formatting is duplicated across components
2. **Inconsistent display**: Different components may format dates differently
3. **No relative times**: Users see absolute timestamps instead of human-friendly "2 hours ago"
4. **No timezone clarity**: Users don't know if times are local or UTC

---

## Goals

### Primary Goals

1. **Browser-Based Timezone**: Display all timestamps in the user's device timezone automatically
2. **Centralized Utility**: Create reusable date formatting functions for consistency
3. **Human-Friendly Display**: Support relative time formatting ("2 hours ago")
4. **Minimal Changes**: Frontend-only implementation, no backend or database changes

### Non-Goals (v1)

1. **User Timezone Preferences**: No stored timezone preference (requires user accounts)
2. **Backend Changes**: No modifications to timestamp storage or API responses
3. **Timezone Selector**: No UI for manually selecting a timezone

---

## User Personas

### Primary: Photo Collection Manager (Alex)
- **Need**: Understand when collections were last updated in their local time
- **Pain Point**: Timestamps display without timezone context
- **Goal**: See "Last updated: Today at 3:45 PM" instead of "2025-12-30T15:45:00"

---

## Requirements

### Functional Requirements

#### FR1: Centralized Date Formatting Utility
- **FR1.1**: Create `frontend/src/utils/dateFormatting.ts` with reusable functions
- **FR1.2**: Support absolute date/time formatting with configurable options
- **FR1.3**: Support relative time formatting ("2 minutes ago", "yesterday")
- **FR1.4**: Handle null/undefined dates gracefully (return "Never" or similar)
- **FR1.5**: Use browser's `Intl` API for locale-aware formatting

#### FR2: Consistent Date Display
- **FR2.1**: All components displaying timestamps MUST use the centralized utility
- **FR2.2**: Replace inline `formatDate()` functions with utility imports
- **FR2.3**: Default format: Medium date style with short time (e.g., "Jan 7, 2026, 3:45 PM")

#### FR3: Relative Time Support
- **FR3.1**: Provide `formatRelativeTime()` function for "time ago" display
- **FR3.2**: Use `Intl.RelativeTimeFormat` for locale-aware relative times
- **FR3.3**: Components MAY choose between absolute and relative display based on context

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1**: Date formatting MUST NOT cause visible UI lag
- **NFR1.2**: No external date library required (use native `Intl` APIs)

#### NFR2: Compatibility
- **NFR2.1**: Support all modern browsers (Chrome, Firefox, Safari, Edge)
- **NFR2.2**: Graceful fallback if `Intl` APIs unavailable (use `toLocaleString()`)

#### NFR3: Testing
- **NFR3.1**: Unit tests for all formatting functions
- **NFR3.2**: Test edge cases (null dates, invalid dates, different locales)

---

## Technical Approach

### Implementation Strategy

**Browser Timezone Detection:**
```typescript
// Browser automatically provides timezone via Intl API
Intl.DateTimeFormat().resolvedOptions().timeZone
// Returns: "America/New_York", "Europe/London", etc.
```

**No Backend Changes Required:**
- Backend continues storing UTC timestamps
- API responses remain unchanged (ISO 8601 format)
- Frontend handles all timezone conversion during display

### Proposed Utility API

```typescript
// frontend/src/utils/dateFormatting.ts

/**
 * Format a date/time string for display in user's local timezone
 */
export function formatDateTime(
  dateString: string | null | undefined,
  options?: Intl.DateTimeFormatOptions
): string

/**
 * Format a date/time as relative time ("2 hours ago", "yesterday")
 */
export function formatRelativeTime(
  dateString: string | null | undefined
): string

/**
 * Format date only (no time component)
 */
export function formatDate(
  dateString: string | null | undefined,
  options?: Intl.DateTimeFormatOptions
): string

/**
 * Format time only (no date component)
 */
export function formatTime(
  dateString: string | null | undefined,
  options?: Intl.DateTimeFormatOptions
): string
```

### Files to Create/Modify

**New Files:**
1. `frontend/src/utils/dateFormatting.ts` - Core utility functions
2. `frontend/src/utils/__tests__/dateFormatting.test.ts` - Unit tests

**Modified Files:**
1. `frontend/src/components/connectors/ConnectorList.tsx` - Replace inline `formatDate()`
2. Any other components displaying timestamps (to be identified during implementation)

---

## Implementation Plan

### Phase 1: Core Utility (Priority: P1)

**Tasks:**
1. Create `frontend/src/utils/dateFormatting.ts` with core functions
2. Implement `formatDateTime()` with configurable options
3. Implement `formatRelativeTime()` using `Intl.RelativeTimeFormat`
4. Implement `formatDate()` and `formatTime()` convenience functions
5. Add null/undefined handling with sensible defaults
6. Write comprehensive unit tests

### Phase 2: Component Migration (Priority: P1)

**Tasks:**
1. Identify all components displaying timestamps
2. Replace `ConnectorList.tsx` inline `formatDate()` with utility import
3. Update any other identified components
4. Verify consistent display across the application

### Phase 3: Documentation (Priority: P2)

**Tasks:**
1. Add JSDoc comments to all utility functions
2. Update CLAUDE.md with date formatting guidelines (if significant)

---

## Alternative Approaches Considered

### Option A: User Account with Timezone Preference
- **Pros**: Consistent across devices, explicit user control
- **Cons**: Requires user management system, significant implementation effort
- **Decision**: Deferred until user accounts are implemented

### Option B: External Date Library (date-fns, dayjs)
- **Pros**: Rich functionality, well-tested
- **Cons**: Additional dependency, bundle size increase
- **Decision**: Rejected - native `Intl` APIs sufficient for requirements

### Option C: Backend Timezone Conversion
- **Pros**: Consistent formatting server-side
- **Cons**: Requires timezone parameter in API calls, more complex
- **Decision**: Rejected - browser-based approach simpler and more flexible

---

## Success Metrics

1. **M1**: All timestamp displays use centralized utility (100% adoption)
2. **M2**: No inline date formatting functions remain in components
3. **M3**: Unit test coverage >90% for dateFormatting.ts
4. **M4**: Timestamps display correctly in multiple browser locales

---

## Risks and Mitigation

### Risk 1: Browser Timezone Detection Failures
- **Impact**: Low - fallback to UTC display
- **Probability**: Very Low (Intl API widely supported)
- **Mitigation**: Graceful fallback using basic `toLocaleString()`

### Risk 2: Inconsistent Display Across Browsers
- **Impact**: Low - cosmetic differences only
- **Probability**: Low
- **Mitigation**: Use standard `Intl` options, test in multiple browsers

---

## Future Enhancements

1. **User Timezone Preference**: When user accounts are added, allow storing preferred timezone
2. **Timezone Indicator**: Optionally show timezone abbreviation (e.g., "3:45 PM EST")
3. **Relative Time Thresholds**: Configurable thresholds for when to show relative vs absolute
4. **Server-Side Rendering**: If SSR is added, handle timezone on server with client hydration

---

## Appendix

### Browser Support for Intl APIs

| Browser | Intl.DateTimeFormat | Intl.RelativeTimeFormat |
|---------|---------------------|-------------------------|
| Chrome  | 24+                 | 71+                     |
| Firefox | 29+                 | 65+                     |
| Safari  | 10+                 | 14+                     |
| Edge    | 12+                 | 79+                     |

All target browsers fully support required APIs.

### Example Output

| Input (UTC)              | formatDateTime()           | formatRelativeTime() |
|--------------------------|----------------------------|----------------------|
| `2026-01-07T15:45:00`    | Jan 7, 2026, 10:45 AM (EST)| 2 hours ago          |
| `2026-01-06T20:00:00`    | Jan 6, 2026, 3:00 PM (EST) | yesterday            |
| `null`                   | Never                      | Never                |
| `undefined`              | Never                      | Never                |

---

## Revision History

- **2026-01-07 (v1.0)**: Initial draft
