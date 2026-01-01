/**
 * Connector Type Definitions
 *
 * TypeScript interfaces for connector entities and API interactions.
 * These mirror the backend FastAPI endpoints for remote storage connections.
 */

// ============================================================================
// Core Types
// ============================================================================

export type ConnectorType = 'S3' | 'GCS' | 'SMB'

export interface Connector {
  id: number
  name: string
  type: ConnectorType
  active: boolean
  credentials: ConnectorCredentials
  created_at: string  // ISO 8601 timestamp
  updated_at: string  // ISO 8601 timestamp
}

// ============================================================================
// Credentials Types (Polymorphic by ConnectorType)
// ============================================================================

export type ConnectorCredentials =
  | S3Credentials
  | GCSCredentials
  | SMBCredentials

export interface S3Credentials {
  access_key_id: string
  secret_access_key: string
  region: string
  bucket?: string
}

export interface GCSCredentials {
  service_account_json: string
  bucket?: string
}

export interface SMBCredentials {
  server: string
  share: string
  username: string
  password: string
  domain?: string
}

// ============================================================================
// API Request Types
// ============================================================================

export interface ConnectorCreateRequest {
  name: string
  type: ConnectorType
  active: boolean
  credentials: ConnectorCredentials
}

export interface ConnectorUpdateRequest {
  name?: string
  type?: ConnectorType
  active?: boolean
  credentials?: ConnectorCredentials
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ConnectorListResponse {
  connectors: Connector[]
  total: number
}

export interface ConnectorDetailResponse {
  connector: Connector
}

export interface ConnectorTestResponse {
  success: boolean
  message: string
  details?: {
    connection_time_ms?: number
    endpoint?: string
    [key: string]: unknown
  }
}

export interface ConnectorDeleteResponse {
  success: boolean
  message: string
}

// ============================================================================
// Form Data Types
// ============================================================================

export interface ConnectorFormData {
  name: string
  type: ConnectorType
  active: boolean
  credentials: Partial<ConnectorCredentials>
}

export interface ConnectorCreate extends Omit<Connector, 'id' | 'created_at' | 'updated_at'> {}
export interface ConnectorUpdate extends Partial<ConnectorCreate> {}
