/**
 * Events Page
 *
 * Display and manage calendar events.
 * Calendar view with event management capabilities.
 *
 * Issue #39 - Calendar Events feature.
 */

import { Calendar } from 'lucide-react'

export default function EventsPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <Calendar className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-semibold text-foreground mb-2">Events Calendar</h2>
        <p className="text-muted-foreground max-w-md">
          Calendar view for managing events. This will be implemented in Phase 4 (User Story 1).
        </p>
      </div>
    </div>
  )
}
