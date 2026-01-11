/**
 * useEvents React hook
 *
 * Manages event state with fetch and mutation operations for calendar views
 * Issue #39 - Calendar Events feature (Phases 4 & 5)
 */

import { useState, useEffect, useCallback } from 'react'
import * as eventService from '../services/events'
import type {
  Event,
  EventDetail,
  EventListParams,
  EventStatsResponse,
  EventCreateRequest,
  EventSeriesCreateRequest,
  EventUpdateRequest,
  UpdateScope
} from '@/contracts/api/event-api'

// ============================================================================
// Events List Hook
// ============================================================================

interface UseEventsReturn {
  events: Event[]
  loading: boolean
  error: string | null
  fetchEvents: (params?: EventListParams) => Promise<Event[]>
  fetchEventsByMonth: (year: number, month: number) => Promise<Event[]>
  fetchEventsForCalendarView: (year: number, month: number) => Promise<Event[]>
}

/**
 * Hook for fetching and managing events list
 *
 * @param initialParams - Initial query parameters for auto-fetch
 * @param autoFetch - Whether to fetch on mount (default: false)
 */
export const useEvents = (
  initialParams: EventListParams = {},
  autoFetch = false
): UseEventsReturn => {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Fetch events with optional filtering
   */
  const fetchEvents = useCallback(async (params: EventListParams = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await eventService.listEvents(params)
      setEvents(data)
      return data
    } catch (err: any) {
      const errorMessage = err.userMessage || 'Failed to load events'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Fetch events for a specific month
   */
  const fetchEventsByMonth = useCallback(async (year: number, month: number) => {
    setLoading(true)
    setError(null)
    try {
      const data = await eventService.listEventsByMonth(year, month)
      setEvents(data)
      return data
    } catch (err: any) {
      const errorMessage = err.userMessage || 'Failed to load events'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Fetch events for calendar grid view (includes adjacent month days)
   */
  const fetchEventsForCalendarView = useCallback(async (year: number, month: number) => {
    setLoading(true)
    setError(null)
    try {
      const data = await eventService.listEventsForCalendarView(year, month)
      setEvents(data)
      return data
    } catch (err: any) {
      const errorMessage = err.userMessage || 'Failed to load events'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // Auto-fetch on mount if enabled
  useEffect(() => {
    if (autoFetch) {
      fetchEvents(initialParams)
    }
  }, [autoFetch]) // eslint-disable-line react-hooks/exhaustive-deps

  return {
    events,
    loading,
    error,
    fetchEvents,
    fetchEventsByMonth,
    fetchEventsForCalendarView
  }
}

// ============================================================================
// Event Detail Hook
// ============================================================================

interface UseEventReturn {
  event: EventDetail | null
  loading: boolean
  error: string | null
  fetchEvent: (guid: string, includeDeleted?: boolean) => Promise<EventDetail>
}

/**
 * Hook for fetching a single event's details
 *
 * @param guid - Event GUID to fetch (optional, can call fetchEvent later)
 * @param autoFetch - Whether to fetch on mount (default: true if guid provided)
 */
export const useEvent = (guid?: string, autoFetch = true): UseEventReturn => {
  const [event, setEvent] = useState<EventDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Fetch event details by GUID
   */
  const fetchEvent = useCallback(async (eventGuid: string, includeDeleted = false) => {
    setLoading(true)
    setError(null)
    try {
      const data = await eventService.getEvent(eventGuid, includeDeleted)
      setEvent(data)
      return data
    } catch (err: any) {
      const errorMessage = err.userMessage || 'Failed to load event'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // Auto-fetch on mount if guid provided
  useEffect(() => {
    if (guid && autoFetch) {
      fetchEvent(guid)
    }
  }, [guid, autoFetch, fetchEvent])

  return {
    event,
    loading,
    error,
    fetchEvent
  }
}

// ============================================================================
// Event Stats Hook
// ============================================================================

interface UseEventStatsReturn {
  stats: EventStatsResponse | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

/**
 * Hook for fetching event KPI statistics
 * Returns total, upcoming, this month, and attended counts
 */
export const useEventStats = (autoFetch = true): UseEventStatsReturn => {
  const [stats, setStats] = useState<EventStatsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await eventService.getEventStats()
      setStats(data)
    } catch (err: any) {
      const errorMessage = err.userMessage || 'Failed to load event statistics'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (autoFetch) {
      refetch()
    }
  }, [autoFetch, refetch])

  return { stats, loading, error, refetch }
}

// ============================================================================
// Calendar View Hook (combines events + navigation)
// ============================================================================

interface UseCalendarReturn {
  events: Event[]
  loading: boolean
  error: string | null
  currentYear: number
  currentMonth: number
  goToMonth: (year: number, month: number) => void
  goToPreviousMonth: () => void
  goToNextMonth: () => void
  goToToday: () => void
  refetch: () => Promise<void>
}

/**
 * Hook for managing calendar state with month navigation
 *
 * @param initialYear - Starting year (default: current year)
 * @param initialMonth - Starting month 1-12 (default: current month)
 */
export const useCalendar = (
  initialYear?: number,
  initialMonth?: number
): UseCalendarReturn => {
  const today = new Date()
  const [currentYear, setCurrentYear] = useState(initialYear ?? today.getFullYear())
  const [currentMonth, setCurrentMonth] = useState(initialMonth ?? today.getMonth() + 1)
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Fetch events for current month view
   */
  const fetchMonthEvents = useCallback(async (year: number, month: number) => {
    setLoading(true)
    setError(null)
    try {
      const data = await eventService.listEventsForCalendarView(year, month)
      setEvents(data)
    } catch (err: any) {
      const errorMessage = err.userMessage || 'Failed to load events'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Navigate to specific month
   */
  const goToMonth = useCallback((year: number, month: number) => {
    setCurrentYear(year)
    setCurrentMonth(month)
  }, [])

  /**
   * Navigate to previous month
   */
  const goToPreviousMonth = useCallback(() => {
    setCurrentMonth(prev => {
      if (prev === 1) {
        setCurrentYear(y => y - 1)
        return 12
      }
      return prev - 1
    })
  }, [])

  /**
   * Navigate to next month
   */
  const goToNextMonth = useCallback(() => {
    setCurrentMonth(prev => {
      if (prev === 12) {
        setCurrentYear(y => y + 1)
        return 1
      }
      return prev + 1
    })
  }, [])

  /**
   * Navigate to current month
   */
  const goToToday = useCallback(() => {
    const now = new Date()
    setCurrentYear(now.getFullYear())
    setCurrentMonth(now.getMonth() + 1)
  }, [])

  /**
   * Refetch current month's events
   */
  const refetch = useCallback(async () => {
    await fetchMonthEvents(currentYear, currentMonth)
  }, [currentYear, currentMonth, fetchMonthEvents])

  // Fetch events when month changes
  useEffect(() => {
    fetchMonthEvents(currentYear, currentMonth)
  }, [currentYear, currentMonth, fetchMonthEvents])

  return {
    events,
    loading,
    error,
    currentYear,
    currentMonth,
    goToMonth,
    goToPreviousMonth,
    goToNextMonth,
    goToToday,
    refetch
  }
}

// ============================================================================
// Event Mutations Hook (Phase 5)
// ============================================================================

interface UseEventMutationsReturn {
  /** Create a new standalone event */
  createEvent: (data: EventCreateRequest) => Promise<EventDetail>
  /** Create a new event series */
  createEventSeries: (data: EventSeriesCreateRequest) => Promise<Event[]>
  /** Update an existing event */
  updateEvent: (guid: string, data: EventUpdateRequest) => Promise<EventDetail>
  /** Soft delete an event */
  deleteEvent: (guid: string, scope?: UpdateScope) => Promise<EventDetail>
  /** Restore a soft-deleted event */
  restoreEvent: (guid: string) => Promise<EventDetail>
  /** Loading state */
  loading: boolean
  /** Error message if any */
  error: string | null
}

/**
 * Hook for event mutation operations (create, update, delete)
 *
 * Use this hook alongside useCalendar for full calendar functionality.
 *
 * @example
 * const { createEvent, deleteEvent, loading } = useEventMutations()
 * const calendar = useCalendar()
 *
 * const handleCreate = async (data: EventCreateRequest) => {
 *   await createEvent(data)
 *   await calendar.refetch()
 * }
 */
export const useEventMutations = (): UseEventMutationsReturn => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Create a new standalone event
   */
  const createEvent = useCallback(async (data: EventCreateRequest): Promise<EventDetail> => {
    setLoading(true)
    setError(null)
    try {
      const result = await eventService.createEvent(data)
      return result
    } catch (err: any) {
      const errorMessage = err.userMessage || 'Failed to create event'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Create a new event series
   */
  const createEventSeries = useCallback(async (data: EventSeriesCreateRequest): Promise<Event[]> => {
    setLoading(true)
    setError(null)
    try {
      const result = await eventService.createEventSeries(data)
      return result
    } catch (err: any) {
      const errorMessage = err.userMessage || 'Failed to create event series'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Update an existing event
   */
  const updateEvent = useCallback(async (guid: string, data: EventUpdateRequest): Promise<EventDetail> => {
    setLoading(true)
    setError(null)
    try {
      const result = await eventService.updateEvent(guid, data)
      return result
    } catch (err: any) {
      const errorMessage = err.userMessage || 'Failed to update event'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Soft delete an event
   */
  const deleteEvent = useCallback(async (guid: string, scope: UpdateScope = 'single'): Promise<EventDetail> => {
    setLoading(true)
    setError(null)
    try {
      const result = await eventService.deleteEvent(guid, scope)
      return result
    } catch (err: any) {
      const errorMessage = err.userMessage || 'Failed to delete event'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Restore a soft-deleted event
   */
  const restoreEvent = useCallback(async (guid: string): Promise<EventDetail> => {
    setLoading(true)
    setError(null)
    try {
      const result = await eventService.restoreEvent(guid)
      return result
    } catch (err: any) {
      const errorMessage = err.userMessage || 'Failed to restore event'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    createEvent,
    createEventSeries,
    updateEvent,
    deleteEvent,
    restoreEvent,
    loading,
    error
  }
}
