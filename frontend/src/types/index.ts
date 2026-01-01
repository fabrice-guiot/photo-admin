/**
 * Type Definitions Barrel File
 *
 * Central export point for all TypeScript type definitions.
 * Import from this file to access any type used across the application.
 *
 * @example
 * import { Connector, Collection, ApiError } from '@/types'
 */

// Re-export all types from connector module
export type {
  ConnectorType,
  Connector,
  ConnectorCredentials,
  S3Credentials,
  GCSCredentials,
  SMBCredentials,
  ConnectorCreateRequest,
  ConnectorUpdateRequest,
  ConnectorListResponse,
  ConnectorDetailResponse,
  ConnectorTestResponse,
  ConnectorDeleteResponse,
  ConnectorFormData,
  ConnectorCreate,
  ConnectorUpdate,
} from './connector'

// Re-export all types from collection module
export type {
  CollectionType,
  CollectionState,
  Collection,
  CollectionCreateRequest,
  CollectionUpdateRequest,
  CollectionListQueryParams,
  CollectionListResponse,
  CollectionDetailResponse,
  CollectionTestResponse,
  CollectionDeleteResponse,
  CollectionFormData,
  CollectionCreate,
  CollectionUpdate,
} from './collection'

// Re-export all types from api module
export type {
  ApiError,
  ValidationError,
  ApiErrorResponse,
  PaginationParams,
  PaginationMeta,
  PaginatedResponse,
  SuccessResponse,
  TestResponse,
  ApiHeaders,
  ApiResult,
  AsyncApiResult,
} from './api'

export { HttpStatus } from './api'
