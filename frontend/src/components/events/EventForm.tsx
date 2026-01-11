/**
 * Event Form Component
 *
 * Form for creating and editing calendar events.
 * Issue #39 - Calendar Events feature (Phase 5)
 */

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import type { EventDetail, EventCreateRequest, EventUpdateRequest } from '@/contracts/api/event-api'
import type { Category } from '@/contracts/api/category-api'

// ============================================================================
// Form Schema
// ============================================================================

const eventFormSchema = z.object({
  title: z.string().min(1, 'Title is required').max(255),
  description: z.string().optional(),
  category_guid: z.string().min(1, 'Category is required'),
  event_date: z.string().min(1, 'Event date is required'),
  start_time: z.string().optional(),
  end_time: z.string().optional(),
  is_all_day: z.boolean().default(false),
  status: z.enum(['future', 'confirmed', 'completed', 'cancelled']).default('future'),
  attendance: z.enum(['planned', 'attended', 'skipped']).default('planned'),
})

type EventFormValues = z.infer<typeof eventFormSchema>

// ============================================================================
// Component Props
// ============================================================================

interface EventFormProps {
  /** Event to edit (null for create mode) */
  event?: EventDetail | null
  /** Available categories for selection */
  categories: Category[]
  /** Called when form is submitted */
  onSubmit: (data: EventCreateRequest | EventUpdateRequest) => Promise<void>
  /** Called when cancel is clicked */
  onCancel: () => void
  /** Whether form is submitting */
  isSubmitting?: boolean
  /** Pre-selected date for new events */
  defaultDate?: string
}

// ============================================================================
// Event Form Component
// ============================================================================

export const EventForm = ({
  event,
  categories,
  onSubmit,
  onCancel,
  isSubmitting = false,
  defaultDate
}: EventFormProps) => {
  const isEditMode = !!event

  // Initialize form
  const form = useForm<EventFormValues>({
    resolver: zodResolver(eventFormSchema),
    defaultValues: {
      title: '',
      description: '',
      category_guid: '',
      event_date: defaultDate || new Date().toISOString().split('T')[0],
      start_time: '',
      end_time: '',
      is_all_day: false,
      status: 'future',
      attendance: 'planned',
    }
  })

  // Populate form when editing
  useEffect(() => {
    if (event) {
      form.reset({
        title: event.title,
        description: event.description || '',
        category_guid: event.category?.guid || '',
        event_date: event.event_date,
        start_time: event.start_time?.slice(0, 5) || '', // HH:MM
        end_time: event.end_time?.slice(0, 5) || '', // HH:MM
        is_all_day: event.is_all_day,
        status: event.status,
        attendance: event.attendance,
      })
    }
  }, [event, form])

  // Handle form submission
  const handleSubmit = async (values: EventFormValues) => {
    const data: EventCreateRequest | EventUpdateRequest = {
      title: values.title,
      description: values.description || null,
      category_guid: values.category_guid,
      event_date: values.event_date,
      start_time: values.is_all_day ? null : (values.start_time || null),
      end_time: values.is_all_day ? null : (values.end_time || null),
      is_all_day: values.is_all_day,
      status: values.status,
      attendance: values.attendance,
    }

    await onSubmit(data)
  }

  // Watch all-day state to show/hide time fields
  const isAllDay = form.watch('is_all_day')

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
        {/* Title */}
        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Title</FormLabel>
              <FormControl>
                <Input placeholder="Event title" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Description */}
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Event description (optional)"
                  className="resize-none"
                  rows={3}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Category */}
        <FormField
          control={form.control}
          name="category_guid"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Category</FormLabel>
              <Select onValueChange={field.onChange} value={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a category" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {categories.map(category => (
                    <SelectItem key={category.guid} value={category.guid}>
                      <span className="flex items-center gap-2">
                        {category.color && (
                          <span
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: category.color }}
                          />
                        )}
                        {category.name}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Event Date */}
        <FormField
          control={form.control}
          name="event_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Date</FormLabel>
              <FormControl>
                <Input type="date" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* All Day Checkbox */}
        <FormField
          control={form.control}
          name="is_all_day"
          render={({ field }) => (
            <FormItem className="flex flex-row items-start space-x-3 space-y-0">
              <FormControl>
                <Checkbox
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
              <div className="space-y-1 leading-none">
                <FormLabel>All day event</FormLabel>
                <FormDescription>
                  Event spans the entire day without specific times
                </FormDescription>
              </div>
            </FormItem>
          )}
        />

        {/* Time Fields (hidden when all-day) */}
        {!isAllDay && (
          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="start_time"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Start Time</FormLabel>
                  <FormControl>
                    <Input type="time" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="end_time"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>End Time</FormLabel>
                  <FormControl>
                    <Input type="time" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        )}

        {/* Status and Attendance */}
        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="status"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Status</FormLabel>
                <Select onValueChange={field.onChange} value={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="future">Future</SelectItem>
                    <SelectItem value="confirmed">Confirmed</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="attendance"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Attendance</FormLabel>
                <Select onValueChange={field.onChange} value={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select attendance" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="planned">Planned</SelectItem>
                    <SelectItem value="attended">Attended</SelectItem>
                    <SelectItem value="skipped">Skipped</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {/* Form Actions */}
        <div className="flex justify-end gap-2 pt-4">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isEditMode ? 'Save Changes' : 'Create Event'}
          </Button>
        </div>
      </form>
    </Form>
  )
}

export default EventForm
