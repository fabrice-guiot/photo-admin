/**
 * Collection Form Validation Schemas
 *
 * Zod schemas for collection forms with type-safe validation
 */

import { z } from 'zod'
import type { CollectionType } from '@/contracts/api/collection-api'

// ============================================================================
// Collection Form Schema
// ============================================================================

/**
 * Base collection form schema
 */
export const collectionFormSchema = z
  .object({
    name: z
      .string()
      .min(1, 'Collection name is required')
      .max(100, 'Collection name must be less than 100 characters')
      .regex(
        /^[a-zA-Z0-9\s\-_]+$/,
        'Collection name can only contain letters, numbers, spaces, hyphens, and underscores'
      ),
    type: z.enum(['LOCAL', 'S3', 'GCS', 'SMB'], {
      message: 'Invalid collection type'
    }),
    state: z.enum(['LIVE', 'CLOSED', 'ARCHIVED'], {
      message: 'Invalid collection state'
    }),
    location: z
      .string()
      .min(1, 'Location is required')
      .max(500, 'Location must be less than 500 characters'),
    connector_id: z
      .number()
      .int('Connector ID must be an integer')
      .positive('Connector ID must be positive')
      .nullable(),
    cache_ttl: z
      .number()
      .int('Cache TTL must be an integer')
      .positive('Cache TTL must be positive')
      .nullable()
      .optional()
  })
  .refine(
    (data) => {
      // LOCAL type must have null connector_id
      if (data.type === 'LOCAL') {
        return data.connector_id === null
      }
      return true
    },
    {
      message: 'Local collections cannot have a connector',
      path: ['connector_id']
    }
  )
  .refine(
    (data) => {
      // Remote types (S3, GCS, SMB) must have non-null connector_id
      if (data.type !== 'LOCAL') {
        return data.connector_id !== null && data.connector_id > 0
      }
      return true
    },
    {
      message: 'Remote collections require a connector',
      path: ['connector_id']
    }
  )

// ============================================================================
// Type Inference
// ============================================================================

export type CollectionFormData = z.infer<typeof collectionFormSchema>

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Check if a collection type requires a connector
 */
export function isConnectorRequiredForType(type: CollectionType): boolean {
  return type !== 'LOCAL'
}

/**
 * Get default form values for a collection type
 */
export function getDefaultCollectionFormValues(type: CollectionType = 'LOCAL'): Partial<CollectionFormData> {
  return {
    name: '',
    type,
    state: 'LIVE',
    location: '',
    connector_id: type === 'LOCAL' ? null : undefined,
    cache_ttl: null
  }
}
