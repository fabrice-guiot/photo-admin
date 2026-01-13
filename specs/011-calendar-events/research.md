# Research: Calendar of Events Feature

**Feature Branch**: `011-calendar-events`
**Research Date**: 2026-01-11
**Status**: Complete

## Research Tasks

| Task | Status | Decision |
|------|--------|----------|
| Geocoding service selection | Resolved | Nominatim + timezonefinder |
| Calendar library selection | Resolved | Custom CSS Grid + react-day-picker |
| Multi-day series pattern | Resolved | Hybrid parent-child (EventSeries + Event) |

---

## 1. Geocoding Service Selection

### Requirements
- Resolve street addresses to coordinates (lat/lng)
- Provide timezone information for locations
- Simple integration, minimal dependencies
- Free tier or low-cost for single photographer use
- Privacy-conscious (prefer services that don't require Google)

### Options Evaluated

| Service | Free Tier | Rate Limit | Timezone | Privacy | Accuracy |
|---------|-----------|------------|----------|---------|----------|
| **Nominatim** | Unlimited (self-hosted) / ~1,000/day public | 1 req/sec | No (needs separate lib) | Excellent | 70-80% |
| Mapbox | 100,000/month | No stated limit | No | Medium | ~95% |
| Google Maps | 10,000/month | 50 req/sec | Yes (via Timezone API) | Low | 99.9% |
| Azure Maps | 5,000/month | 500 req/sec | Yes | Medium | ~95% |
| HERE | 30,000-250,000/month | 5 req/sec | No | Medium | 95%+ |

### Decision: Nominatim + timezonefinder

**Rationale:**
1. **Free and open source** - No API keys, no billing, no surprise costs
2. **Privacy-first** - No tracking, no data collection, self-hostable
3. **Sufficient accuracy** - Event locations are typically well-known venues that geocode accurately
4. **Offline timezone lookup** - timezonefinder provides timezone from coordinates without additional API calls

**Alternatives Rejected:**
- **Google Maps**: Best accuracy but privacy concerns and requires billing account
- **Mapbox**: Cannot store results in database (temporary API limitation)
- **HERE**: Better accuracy but adds API dependency for minimal benefit

**Dependencies:**
```
geopy>=2.4.0          # Nominatim client with rate limiting
timezonefinder>=6.0.0 # Offline timezone lookup from coordinates
```

**Implementation Example:**
```python
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from timezonefinder import TimezoneFinder

class GeocodingService:
    def __init__(self):
        self._geolocator = Nominatim(user_agent="photo-admin/1.0")
        self._geocode = RateLimiter(self._geolocator.geocode, min_delay_seconds=1)
        self._tf = TimezoneFinder()

    def geocode_address(self, address: str) -> dict | None:
        location = self._geocode(address)
        if not location:
            return None

        timezone = self._tf.timezone_at(lat=location.latitude, lng=location.longitude)
        return {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "formatted_address": location.address,
            "timezone": timezone
        }
```

---

## 2. Calendar Library Selection

### Requirements
- TypeScript support with React 18.3.1
- Compatible with Tailwind CSS 4.x and shadcn/ui design system
- Custom event rendering (attendance status colors: Yellow, Red, Green)
- Month navigation
- Event click/hover handlers
- Accessible (WCAG compliant)
- Lightweight bundle size

### Options Evaluated

| Feature | react-big-calendar | FullCalendar | react-calendar | Custom CSS Grid |
|---------|-------------------|--------------|----------------|-----------------|
| **Bundle Size (gzip)** | ~30-40 KB | ~100 KB | ~10-15 KB | ~3-10 KB |
| **TypeScript Quality** | Moderate (DefinitelyTyped) | Excellent (native) | Good (included) | Full control |
| **Custom Event Rendering** | Excellent | Excellent | Not supported | Full control |
| **Tailwind Integration** | Workarounds needed | CSS overrides | Easy | Native |
| **shadcn/ui Compatibility** | Requires wrapper | Requires wrapper | Easy | Native |
| **WCAG Compliance** | Partial (open issues) | Good (v5.10+) | Basic | Via React Aria |
| **Maintenance** | Active (7mo since release) | Very active | Active | Self-maintained |

### Decision: Custom CSS Grid + react-day-picker

**Rationale:**
1. **Minimal bundle overhead** - Project already uses Tailwind 4.x and shadcn/ui; custom implementation adds only ~3-10 KB
2. **Native shadcn/ui integration** - shadcn Calendar component is built on react-day-picker; extending it is straightforward
3. **Design system consistency** - Attendance colors (Yellow/Red/Green) map directly to existing Badge variants
4. **Accessibility** - react-day-picker provides built-in accessibility; can enhance with React Aria if needed
5. **Single photographer use case** - Don't need advanced features like resource scheduling or drag-and-drop

**Alternatives Rejected:**
- **react-big-calendar**: Larger bundle, SASS-based theming conflicts with Tailwind, accessibility issues
- **FullCalendar**: Very large bundle (~100 KB), overkill for simple monthly view
- **react-calendar**: Not designed for event display, only date selection

**Dependencies:**
```
react-day-picker@9    # Already part of shadcn/ui Calendar
date-fns              # Already in project for date manipulation
```

**Implementation Approach:**
```tsx
// Extend shadcn Calendar with event rendering
import { Calendar } from '@/components/ui/calendar'
import { Badge } from '@/components/ui/badge'

// Attendance status color mapping (per design system)
const ATTENDANCE_STATUS_VARIANT = {
  planned: 'warning',      // Yellow/Amber
  skipped: 'destructive',  // Red
  attended: 'success'      // Green
}

function DayWithEvents({ date, events }) {
  const dayEvents = events.filter(e => isSameDay(e.date, date))

  return (
    <div className="relative">
      <span>{date.getDate()}</span>
      {dayEvents.map(event => (
        <Badge
          key={event.guid}
          variant={ATTENDANCE_STATUS_VARIANT[event.attendance]}
          className="w-full text-xs mt-1"
        >
          {event.title}
        </Badge>
      ))}
    </div>
  )
}
```

---

## 3. Multi-Day Event Series Pattern

### Requirements (from spec)
- When user creates event spanning multiple days, system creates individual Event records for each day (FR-007)
- Events in series share properties but can have individual status/attendance (FR-009)
- Display "1/3", "2/3", "3/3" notation on calendar (FR-008)
- Operations can affect single event or entire series (FR-010)

### Patterns Evaluated

| Pattern | Description | Pros | Cons |
|---------|-------------|------|------|
| **Junction Table** | Separate EventSeries table with many-to-many | Clean separation | Requires JOIN for every query |
| **Parent Record** | Self-referencing FK (parent_event_id) | Single table | Nullable FK complexity |
| **Hybrid Parent-Child** | EventSeries for shared props, Event for individual | Best of both | Two tables |

### Decision: Hybrid Parent-Child Pattern

**Schema Design:**

```
EventSeries (ser_xxx)              Event (evt_xxx)
─────────────                      ─────────────
id, guid                           id, guid
title                              series_id (FK, nullable)
description                        sequence_number
category_id                        total_in_series
location_id                        event_date
organizer_id                       start_time, end_time
logistics_defaults                 attendance_status
input_timezone                     individual_overrides
total_events                       deleted_at
```

**Rationale:**
1. **Matches spec exactly** - Individual Event records per day with shared properties on EventSeries
2. **Standalone events supported** - Nullable series_id allows single events without series
3. **Efficient queries** - Calendar queries don't require JOINs for basic display
4. **Clear cascade semantics** - Edit series title → cascades to all; Edit attendance → single event only

**Key Decisions:**

| Operation | Scope | Behavior |
|-----------|-------|----------|
| Edit title | Single | Set `event.title` (override) |
| Edit title | Series | Update `series.title` (all events inherit) |
| Edit attendance | Single only | Always individual, never shared |
| Edit location | Single | Set `event.location_id` (override) |
| Edit location | Series | Update `series.location_id` |
| Delete | Single | Soft delete single event |
| Delete | Series | Soft delete all events + series |

**UI Pattern:**
When editing a series event:
- "Edit this event only" → Opens single event form
- "Edit entire series" → Opens series form

**Cascade Delete:**
- Series soft delete cascades to all member events
- Single event soft delete does not affect series (sequence numbers preserved)

---

## 4. Additional Research Notes

### Timezone Handling (Builds on Issue #56)
- User enters times in event location's timezone (FR-003)
- Backend stores all times in UTC (FR-002)
- Frontend displays in user's local timezone using existing Intl APIs (FR-004)
- `input_timezone` field preserved for display during editing

### Logistics Status Colors (Per Design System)
| Requirement | Statuses | Colors |
|-------------|----------|--------|
| Ticket | Not Purchased / Purchased / Ready | Red / Yellow / Green |
| Time-off | Planned / Booked / Approved | Red / Yellow / Green |
| Travel | Planned / Booked | Red / Green |

### GUID Prefixes (New Entities)
| Entity | Prefix | Example |
|--------|--------|---------|
| Event | `evt_` | `evt_01hgw2bbg...` |
| EventSeries | `ser_` | `ser_01hgw2bbg...` |
| Location | `loc_` | `loc_01hgw2bbg...` |
| Organizer | `org_` | `org_01hgw2bbg...` |
| Performer | `prf_` | `prf_01hgw2bbg...` |
| Category | `cat_` | `cat_01hgw2bbg...` |

---

## Summary

All NEEDS CLARIFICATION items from Technical Context have been resolved:

1. **Geocoding**: Nominatim (free, privacy-focused) + timezonefinder (offline timezone lookup)
2. **Calendar UI**: Custom CSS Grid extending shadcn/ui Calendar component
3. **Event Series**: Hybrid parent-child pattern with EventSeries and Event tables

No constitution violations or blocking issues identified. Ready to proceed to Phase 1 (Design & Contracts).
