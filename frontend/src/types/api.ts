/**
 * API Common Type Definitions
 *
 * Shared types for API interactions across all endpoints.
 * Includes error handling, pagination, and common response structures.
 */

// ============================================================================
// Error Types
// ============================================================================

export interface ApiError {
  error: {
    message: string
    code: string
    details?: Record<string, unknown>
  }
}

export interface ValidationError {
  field: string
  message: string
}

export interface ApiErrorResponse {
  error: {
    message: string
    code: string
    validation_errors?: ValidationError[]
    details?: Record<string, unknown>
  }
}

// ============================================================================
// Pagination Types
// ============================================================================

export interface PaginationParams {
  limit?: number
  offset?: number
}

export interface PaginationMeta {
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: PaginationMeta
}

// ============================================================================
// Common Response Types
// ============================================================================

export interface SuccessResponse {
  success: boolean
  message: string
}

export interface TestResponse {
  success: boolean
  message: string
  details?: Record<string, unknown>
}

// ============================================================================
// HTTP Status Codes
// ============================================================================

export enum HttpStatus {
  OK = 200,
  CREATED = 201,
  NO_CONTENT = 204,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  CONFLICT = 409,
  UNPROCESSABLE_ENTITY = 422,
  INTERNAL_SERVER_ERROR = 500,
  BAD_GATEWAY = 502,
  SERVICE_UNAVAILABLE = 503,
}

// ============================================================================
// Request Headers
// ============================================================================

export interface ApiHeaders {
  'Content-Type'?: string
  'Authorization'?: string
  [key: string]: string | undefined
}

// ============================================================================
// Utility Types
// ============================================================================

export type ApiResult<T> = {
  success: true
  data: T
} | {
  success: false
  error: ApiError
}

export type AsyncApiResult<T> = Promise<ApiResult<T>>
