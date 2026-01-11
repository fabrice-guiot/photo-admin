/**
 * Category Form Component
 *
 * Form for creating and editing event categories.
 * Issue #39 - Calendar Events feature (Phase 3)
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
import { Checkbox } from '@/components/ui/checkbox'
import type { Category } from '@/contracts/api/category-api'

// ============================================================================
// Form Schema
// ============================================================================

const categoryFormSchema = z.object({
  name: z.string()
    .min(1, 'Name is required')
    .max(100, 'Name must be 100 characters or less'),
  icon: z.string()
    .max(50, 'Icon must be 50 characters or less')
    .nullable()
    .optional()
    .transform(val => val === '' ? null : val),
  color: z.string()
    .regex(/^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$/, {
      message: 'Color must be a valid hex code (e.g., #FF0000 or #F00)'
    })
    .nullable()
    .optional()
    .or(z.literal(''))
    .transform(val => val === '' ? null : val),
  is_active: z.boolean().default(true)
})

type CategoryFormData = z.infer<typeof categoryFormSchema>

// ============================================================================
// Component Props
// ============================================================================

export interface CategoryFormProps {
  category?: Category | null
  onSubmit: (data: CategoryFormData) => Promise<void>
  onCancel: () => void
  loading?: boolean
}

// ============================================================================
// Preset Colors
// ============================================================================

const PRESET_COLORS = [
  { name: 'Blue', value: '#3B82F6' },
  { name: 'Green', value: '#22C55E' },
  { name: 'Pink', value: '#EC4899' },
  { name: 'Orange', value: '#F97316' },
  { name: 'Purple', value: '#8B5CF6' },
  { name: 'Red', value: '#EF4444' },
  { name: 'Gray', value: '#6B7280' },
  { name: 'Teal', value: '#14B8A6' },
]

// ============================================================================
// Suggested Icons
// ============================================================================

const SUGGESTED_ICONS = [
  'plane',
  'bird',
  'heart',
  'trophy',
  'user',
  'music',
  'car',
  'camera',
  'star',
  'flag',
]

// ============================================================================
// Component
// ============================================================================

export function CategoryForm({
  category,
  onSubmit,
  onCancel,
  loading = false
}: CategoryFormProps) {
  const isEdit = !!category

  // Initialize form with react-hook-form and Zod
  const form = useForm<CategoryFormData>({
    resolver: zodResolver(categoryFormSchema),
    defaultValues: {
      name: category?.name || '',
      icon: category?.icon || '',
      color: category?.color || '',
      is_active: category?.is_active ?? true
    }
  })

  // Update form when category prop changes
  useEffect(() => {
    if (category) {
      form.reset({
        name: category.name,
        icon: category.icon || '',
        color: category.color || '',
        is_active: category.is_active
      })
    }
  }, [category, form])

  const handleSubmit = async (data: CategoryFormData) => {
    await onSubmit(data)
  }

  const selectedColor = form.watch('color')

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        {/* Name Field */}
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input
                  placeholder="e.g., Airshow, Wedding, Wildlife"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Icon Field */}
        <FormField
          control={form.control}
          name="icon"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Icon</FormLabel>
              <FormControl>
                <Input
                  placeholder="e.g., plane, bird, heart"
                  {...field}
                  value={field.value || ''}
                />
              </FormControl>
              <FormDescription>
                Lucide icon name. Suggestions: {SUGGESTED_ICONS.join(', ')}
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Color Field */}
        <FormField
          control={form.control}
          name="color"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Color</FormLabel>
              <div className="flex gap-2 items-center">
                <FormControl>
                  <Input
                    placeholder="#3B82F6"
                    {...field}
                    value={field.value || ''}
                    className="flex-1"
                  />
                </FormControl>
                {selectedColor && (
                  <div
                    className="h-9 w-9 rounded-md border"
                    style={{ backgroundColor: selectedColor }}
                  />
                )}
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {PRESET_COLORS.map(({ name, value }) => (
                  <button
                    key={value}
                    type="button"
                    title={name}
                    className="h-6 w-6 rounded-full border-2 border-transparent hover:border-foreground transition-colors"
                    style={{ backgroundColor: value }}
                    onClick={() => form.setValue('color', value)}
                  />
                ))}
              </div>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Active Status */}
        <FormField
          control={form.control}
          name="is_active"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center space-x-3 space-y-0 rounded-lg border p-3">
              <FormControl>
                <Checkbox
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
              <div className="space-y-0.5">
                <FormLabel className="font-normal">Active</FormLabel>
                <FormDescription>
                  Inactive categories won't appear in dropdowns
                </FormDescription>
              </div>
            </FormItem>
          )}
        />

        {/* Form Actions */}
        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isEdit ? 'Update' : 'Create'}
          </Button>
        </div>
      </form>
    </Form>
  )
}

export default CategoryForm
