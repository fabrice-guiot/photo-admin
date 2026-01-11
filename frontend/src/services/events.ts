/**
 * Events API service
 *
 * Handles all API calls related to calendar events
 * Issue #39 - Calendar Events feature (Phase 4)
 */

import api from './api'
import { validateGuid } from '@/utils/guid'
import type {
  Event,
  EventDetail,
  EventListParams,
  EventStatsResponse
} from '@/contracts/api/event-api'

/**
 * List events with optional filtering
 *
 * @param params - Query parameters for filtering
 */
export const listEvents = async (params: EventListParams = {}): Promise<Event[]> => {
  const queryParams: Record<string, string | boolean> = {}

  if (params.start_date) queryParams.start_date = params.start_date
  if (params.end_date) queryParams.end_date = params.end_date
  if (params.category_guid) queryParams.category_guid = params.category_guid
  if (params.status) queryParams.status = params.status
  if (params.attendance) queryParams.attendance = params.attendance
  if (params.include_deleted !== undefined) queryParams.include_deleted = params.include_deleted

  const response = await api.get<Event[]>('/events', { params: queryParams })
  return response.data
}

/**
 * Get a single event by GUID
 *
 * @param guid - External ID (evt_xxx format)
 * @param includeDeleted - Include soft-deleted event
 */
export const getEvent = async (guid: string, includeDeleted = false): Promise<EventDetail> => {
  const safeGuid = encodeURIComponent(validateGuid(guid, 'evt'))
  const params: Record<string, boolean> = {}
  if (includeDeleted) params.include_deleted = true

  const response = await api.get<EventDetail>(`/events/${safeGuid}`, { params })
  return response.data
}

/**
 * Get event statistics (KPIs)
 * Returns aggregated stats for all events
 */
export const getEventStats = async (): Promise<EventStatsResponse> => {
  const response = await api.get<EventStatsResponse>('/events/stats')
  return response.data
}

/**
 * List events for a specific month (convenience function for calendar view)
 *
 * @param year - Full year (e.g., 2026)
 * @param month - Month (1-12)
 */
export const listEventsByMonth = async (year: number, month: number): Promise<Event[]> => {
  // Calculate first and last day of the month
  const startDate = `${year}-${String(month).padStart(2, '0')}-01`

  // Calculate last day of month
  const lastDay = new Date(year, month, 0).getDate()
  const endDate = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`

  return listEvents({ start_date: startDate, end_date: endDate })
}

/**
 * List events for a date range that spans across the visible calendar grid
 * This includes days from adjacent months that appear in the calendar view
 *
 * @param year - Full year (e.g., 2026)
 * @param month - Month (1-12)
 */
export const listEventsForCalendarView = async (year: number, month: number): Promise<Event[]> => {
  // Get the first day of the month
  const firstOfMonth = new Date(year, month - 1, 1)

  // Get the day of week (0 = Sunday)
  const startDayOfWeek = firstOfMonth.getDay()

  // Start from the Sunday before or on the first of the month
  const startDate = new Date(firstOfMonth)
  startDate.setDate(startDate.getDate() - startDayOfWeek)

  // Get the last day of the month
  const lastOfMonth = new Date(year, month, 0)

  // End on the Saturday after or on the last of the month
  const endDayOfWeek = lastOfMonth.getDay()
  const endDate = new Date(lastOfMonth)
  endDate.setDate(endDate.getDate() + (6 - endDayOfWeek))

  const formatDate = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

  return listEvents({
    start_date: formatDate(startDate),
    end_date: formatDate(endDate)
  })
}
