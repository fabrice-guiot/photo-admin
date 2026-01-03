/**
 * Form Validation Schemas (Zod)
 *
 * Defines Zod schemas for form validation with TypeScript type inference
 */

import { z } from 'zod'

// ============================================================================
// Connector Form Schemas
// ============================================================================

/**
 * S3 Credentials Validation Schema
 */
export const S3CredentialsSchema = z.object({
  access_key_id: z
    .string()
    .min(16, 'Access Key ID must be at least 16 characters')
    .max(128, 'Access Key ID must be at most 128 characters')
    .regex(
      /^[A-Z0-9]+$/,
      'Access Key ID must contain only uppercase letters and numbers'
    ),

  secret_access_key: z
    .string()
    .min(40, 'Secret Access Key must be at least 40 characters')
    .max(255, 'Secret Access Key must be at most 255 characters'),

  region: z.enum(
    [
      'us-east-1',
      'us-east-2',
      'us-west-1',
      'us-west-2',
      'eu-west-1',
      'eu-central-1',
      'ap-southeast-1',
      'ap-northeast-1'
    ],
    {
      errorMap: () => ({ message: 'Please select a valid AWS region' })
    }
  ),

  bucket: z
    .string()
    .min(3, 'Bucket name must be at least 3 characters')
    .max(63, 'Bucket name must be at most 63 characters')
    .regex(
      /^[a-z0-9][a-z0-9.-]*[a-z0-9]$/,
      'Bucket name must follow AWS naming rules (lowercase, numbers, dots, hyphens)'
    )
    .optional()
    .or(z.literal(''))
})

/**
 * GCS Credentials Validation Schema
 */
export const GCSCredentialsSchema = z.object({
  service_account_json: z
    .string()
    .min(1, 'Service Account JSON is required')
    .refine(
      (val) => {
        try {
          const parsed = JSON.parse(val)
          return (
            parsed.type === 'service_account' &&
            parsed.project_id &&
            parsed.private_key &&
            parsed.client_email
          )
        } catch {
          return false
        }
      },
      {
        message:
          'Must be a valid Google Cloud service account JSON key file'
      }
    ),

  bucket: z
    .string()
    .min(3, 'Bucket name must be at least 3 characters')
    .max(63, 'Bucket name must be at most 63 characters')
    .regex(
      /^[a-z0-9][a-z0-9-_]*[a-z0-9]$/,
      'Bucket name must follow GCS naming rules (lowercase, numbers, hyphens, underscores)'
    )
    .optional()
    .or(z.literal(''))
})

/**
 * SMB Credentials Validation Schema
 */
export const SMBCredentialsSchema = z.object({
  server: z
    .string()
    .min(1, 'Server is required')
    .max(255, 'Server must be at most 255 characters')
    .refine(
      (val) => {
        // Accept IP address or hostname
        const ipRegex = /^(?:\d{1,3}\.){3}\d{1,3}$/
        const hostnameRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/
        return ipRegex.test(val) || hostnameRegex.test(val)
      },
      {
        message: 'Server must be a valid IP address or hostname'
      }
    ),

  share: z
    .string()
    .min(1, 'Share name is required')
    .max(80, 'Share name must be at most 80 characters')
    .regex(
      /^[a-zA-Z0-9_-]+$/,
      'Share name must contain only letters, numbers, underscores, and hyphens'
    ),

  username: z
    .string()
    .min(1, 'Username is required')
    .max(255, 'Username must be at most 255 characters'),

  password: z
    .string()
    .min(1, 'Password is required')
    .max(255, 'Password must be at most 255 characters'),

  domain: z
    .string()
    .max(255, 'Domain must be at most 255 characters')
    .optional()
    .or(z.literal(''))
})

/**
 * Union type for all credential schemas
 */
export const ConnectorCredentialsSchema = z.union([
  S3CredentialsSchema,
  GCSCredentialsSchema,
  SMBCredentialsSchema
])

/**
 * Connector Form Validation Schema
 */
export const ConnectorFormSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .max(255, 'Name must be at most 255 characters')
    .regex(
      /^[a-zA-Z0-9 _-]+$/,
      'Name must contain only letters, numbers, spaces, underscores, and hyphens'
    ),

  type: z.enum(['S3', 'GCS', 'SMB'], {
    errorMap: () => ({ message: 'Please select a connector type' })
  }),

  active: z.boolean().default(true),

  credentials: ConnectorCredentialsSchema
})

/**
 * Infer TypeScript type from schema
 */
export type ConnectorFormData = z.infer<typeof ConnectorFormSchema>

// ============================================================================
// Collection Form Schemas
// ============================================================================

/**
 * Collection Form Validation Schema
 */
export const CollectionFormSchema = z
  .object({
    name: z
      .string()
      .min(1, 'Name is required')
      .max(255, 'Name must be at most 255 characters')
      .regex(
        /^[a-zA-Z0-9 _-]+$/,
        'Name must contain only letters, numbers, spaces, underscores, and hyphens'
      ),

    type: z.enum(['LOCAL', 'S3', 'GCS', 'SMB'], {
      errorMap: () => ({ message: 'Please select a collection type' })
    }),

    state: z.enum(['LIVE', 'CLOSED', 'ARCHIVED'], {
      errorMap: () => ({ message: 'Please select a collection state' })
    }),

    location: z
      .string()
      .min(1, 'Location is required')
      .max(1024, 'Location must be at most 1024 characters'),

    connector_id: z.number().int().positive().nullable(),

    cache_ttl: z
      .number()
      .int()
      .positive('Cache TTL must be a positive number')
      .max(86400, 'Cache TTL must be at most 86400 seconds (24 hours)')
      .nullable()
  })
  .refine(
    (data) => {
      // Validation rule: LOCAL collections cannot have connector_id
      if (data.type === 'LOCAL') {
        return data.connector_id === null
      }
      return true
    },
    {
      message: 'LOCAL collections cannot have a connector',
      path: ['connector_id']
    }
  )
  .refine(
    (data) => {
      // Validation rule: Remote collections must have connector_id
      if (data.type !== 'LOCAL') {
        return data.connector_id !== null && data.connector_id >= 1
      }
      return true
    },
    {
      message: 'Remote collections must have a connector',
      path: ['connector_id']
    }
  )

/**
 * Infer TypeScript type from schema
 */
export type CollectionFormData = z.infer<typeof CollectionFormSchema>

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Validate connector credentials based on type
 */
export function validateConnectorCredentials(
  type: 'S3' | 'GCS' | 'SMB',
  credentials: unknown
): z.SafeParseReturnType<unknown, unknown> {
  switch (type) {
    case 'S3':
      return S3CredentialsSchema.safeParse(credentials)
    case 'GCS':
      return GCSCredentialsSchema.safeParse(credentials)
    case 'SMB':
      return SMBCredentialsSchema.safeParse(credentials)
  }
}

/**
 * Get credential schema for connector type
 */
export function getCredentialSchema(type: 'S3' | 'GCS' | 'SMB') {
  switch (type) {
    case 'S3':
      return S3CredentialsSchema
    case 'GCS':
      return GCSCredentialsSchema
    case 'SMB':
      return SMBCredentialsSchema
  }
}

/**
 * Error message formatter for Zod errors
 */
export function formatZodError(error: z.ZodError): Record<string, string> {
  const errors: Record<string, string> = {}

  error.errors.forEach((err) => {
    const path = err.path.join('.')
    errors[path] = err.message
  })

  return errors
}

/**
 * Form field error extractor
 */
export function getFieldError(
  errors: Record<string, string>,
  fieldPath: string
): string | undefined {
  return errors[fieldPath]
}
