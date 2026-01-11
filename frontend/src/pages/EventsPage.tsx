/**
 * Events Page
 *
 * Display and manage calendar events.
 * Calendar view with event management capabilities.
 *
 * Issue #39 - Calendar Events feature (Phase 4).
 */

import { useEffect, useState } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { useCalendar, useEventStats } from '@/hooks/useEvents'
import { useHeaderStats } from '@/contexts/HeaderStatsContext'
import { EventCalendar } from '@/components/events/EventCalendar'
import { EventList } from '@/components/events/EventCard'
import type { Event } from '@/contracts/api/event-api'

export default function EventsPage() {
  // Calendar state and navigation
  const {
    events,
    loading,
    error,
    currentYear,
    currentMonth,
    goToPreviousMonth,
    goToNextMonth,
    goToToday
  } = useCalendar()

  // KPI Stats for header (Issue #37)
  const { stats } = useEventStats()
  const { setStats } = useHeaderStats()

  // Update header stats when data changes
  useEffect(() => {
    if (stats) {
      setStats([
        { label: 'Total Events', value: stats.total_count.toLocaleString() },
        { label: 'Upcoming', value: stats.upcoming_count.toLocaleString() },
        { label: 'This Month', value: stats.this_month_count.toLocaleString() },
        { label: 'Attended', value: stats.attended_count.toLocaleString() }
      ])
    }
    return () => setStats([]) // Clear stats on unmount
  }, [stats, setStats])

  // Day detail dialog state
  const [selectedDay, setSelectedDay] = useState<{
    date: Date
    events: Event[]
  } | null>(null)

  // Event detail dialog state
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null)

  // Handle day click - show day detail dialog
  const handleDayClick = (date: Date) => {
    const dateString = formatDateString(date)
    const dayEvents = events.filter(e => e.event_date === dateString)

    if (dayEvents.length > 0) {
      setSelectedDay({ date, events: dayEvents })
    }
  }

  // Handle event click - show event detail
  const handleEventClick = (event: Event) => {
    setSelectedEvent(event)
    setSelectedDay(null) // Close day dialog if open
  }

  // Helper to format date as YYYY-MM-DD
  const formatDateString = (d: Date): string => {
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  }

  // Format date for display
  const formatDisplayDate = (date: Date): string => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <div className="flex flex-col h-full p-6">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Calendar View */}
      <div className="flex-1 min-h-0">
        <EventCalendar
          events={events}
          year={currentYear}
          month={currentMonth}
          loading={loading}
          onPreviousMonth={goToPreviousMonth}
          onNextMonth={goToNextMonth}
          onToday={goToToday}
          onEventClick={handleEventClick}
          onDayClick={handleDayClick}
          className="h-full"
        />
      </div>

      {/* Day Detail Dialog */}
      <Dialog
        open={selectedDay !== null}
        onOpenChange={(open) => !open && setSelectedDay(null)}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {selectedDay && formatDisplayDate(selectedDay.date)}
            </DialogTitle>
            <DialogDescription>
              {selectedDay?.events.length} event{selectedDay?.events.length !== 1 ? 's' : ''} on this day
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[60vh] overflow-y-auto">
            {selectedDay && (
              <EventList
                events={selectedDay.events}
                onEventClick={handleEventClick}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Event Detail Dialog */}
      <Dialog
        open={selectedEvent !== null}
        onOpenChange={(open) => !open && setSelectedEvent(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedEvent?.title}</DialogTitle>
            <DialogDescription>
              {selectedEvent && (
                <>
                  {new Date(selectedEvent.event_date).toLocaleDateString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric'
                  })}
                  {selectedEvent.start_time && ` at ${selectedEvent.start_time.slice(0, 5)}`}
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          {selectedEvent && (
            <div className="space-y-4 pt-4">
              {/* Category */}
              {selectedEvent.category && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">Category</div>
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: selectedEvent.category.color || '#888' }}
                    />
                    <span>{selectedEvent.category.name}</span>
                  </div>
                </div>
              )}

              {/* Status */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">Status</div>
                  <div className="capitalize">{selectedEvent.status}</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">Attendance</div>
                  <div className="capitalize">{selectedEvent.attendance}</div>
                </div>
              </div>

              {/* Series Info */}
              {selectedEvent.series_guid && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">Series</div>
                  <div>
                    Event {selectedEvent.sequence_number} of {selectedEvent.series_total}
                  </div>
                </div>
              )}

              {/* Time */}
              {!selectedEvent.is_all_day && selectedEvent.start_time && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">Time</div>
                  <div>
                    {selectedEvent.start_time.slice(0, 5)}
                    {selectedEvent.end_time && ` - ${selectedEvent.end_time.slice(0, 5)}`}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
