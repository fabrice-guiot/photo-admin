/**
 * Trends API Contracts
 *
 * Defines TypeScript interfaces for trend analysis endpoints.
 * These contracts mirror the backend FastAPI endpoints for Phase 6 implementation.
 */

// ============================================================================
// Entity Types
// ============================================================================

export type TrendDirection = 'improving' | 'stable' | 'degrading' | 'insufficient_data'

// ============================================================================
// PhotoStats Trend Types
// ============================================================================

export interface PhotoStatsTrendPoint {
  /** Timestamp of the analysis run */
  date: string // ISO 8601 timestamp
  /** ID of the analysis result */
  result_id: number
  /** Count of orphaned image files */
  orphaned_images_count: number
  /** Count of orphaned XMP files */
  orphaned_xmp_count: number
  /** Total files in collection at this point */
  total_files: number
  /** Total size in bytes at this point */
  total_size: number
}

export interface PhotoStatsCollectionTrend {
  collection_id: number
  collection_name: string
  data_points: PhotoStatsTrendPoint[]
}

export interface PhotoStatsTrendResponse {
  collections: PhotoStatsCollectionTrend[]
}

// ============================================================================
// Photo Pairing Trend Types
// ============================================================================

export interface PhotoPairingTrendPoint {
  /** Timestamp of the analysis run */
  date: string // ISO 8601 timestamp
  /** ID of the analysis result */
  result_id: number
  /** Number of image groups */
  group_count: number
  /** Total images in groups */
  image_count: number
  /** Map of camera_id to image count */
  camera_usage: Record<string, number>
}

export interface PhotoPairingCollectionTrend {
  collection_id: number
  collection_name: string
  /** List of camera IDs found across all data points */
  cameras: string[]
  data_points: PhotoPairingTrendPoint[]
}

export interface PhotoPairingTrendResponse {
  collections: PhotoPairingCollectionTrend[]
}

// ============================================================================
// Pipeline Validation Trend Types
// ============================================================================

export interface PipelineValidationTrendPoint {
  /** Timestamp of the analysis run */
  date: string // ISO 8601 timestamp
  /** ID of the analysis result */
  result_id: number
  /** Pipeline used for validation */
  pipeline_id: number
  /** Pipeline name */
  pipeline_name: string
  /** Count of CONSISTENT status */
  consistent_count: number
  /** Count of PARTIAL status */
  partial_count: number
  /** Count of INCONSISTENT status */
  inconsistent_count: number
  /** Percentage of CONSISTENT status (0-100) */
  consistent_ratio: number
  /** Percentage of PARTIAL status (0-100) */
  partial_ratio: number
  /** Percentage of INCONSISTENT status (0-100) */
  inconsistent_ratio: number
}

export interface PipelineValidationCollectionTrend {
  collection_id: number
  collection_name: string
  data_points: PipelineValidationTrendPoint[]
}

export interface PipelineValidationTrendResponse {
  collections: PipelineValidationCollectionTrend[]
}

// ============================================================================
// Trend Summary Types
// ============================================================================

export interface TrendSummaryResponse {
  /** Collection ID (null for all collections) */
  collection_id: number | null
  /** Trend direction for orphaned files */
  orphaned_trend: TrendDirection
  /** Trend direction for consistency */
  consistency_trend: TrendDirection
  /** Last PhotoStats run timestamp */
  last_photostats: string | null // ISO 8601 timestamp
  /** Last Pipeline Validation run timestamp */
  last_pipeline_validation: string | null // ISO 8601 timestamp
  /** Number of data points available by tool */
  data_points_available: {
    photostats: number
    photo_pairing: number
    pipeline_validation: number
  }
}

// ============================================================================
// API Query Parameters
// ============================================================================

export interface TrendQueryParams {
  /** Comma-separated collection IDs */
  collection_ids?: string
  /** Filter by date range (from) */
  from_date?: string // YYYY-MM-DD
  /** Filter by date range (to) */
  to_date?: string // YYYY-MM-DD
  /** Maximum data points per collection */
  limit?: number
}

export interface PipelineValidationTrendQueryParams extends TrendQueryParams {
  /** Filter by pipeline ID */
  pipeline_id?: number
}

export interface TrendSummaryQueryParams {
  /** Collection ID (optional, for single collection) */
  collection_id?: number
}

// ============================================================================
// API Error Response
// ============================================================================

export interface TrendsErrorResponse {
  detail: string
  userMessage?: string
}

// ============================================================================
// Frontend-Specific Types
// ============================================================================

/**
 * Filter state used in frontend UI
 */
export interface TrendFilters {
  collection_ids: number[]
  from_date: string
  to_date: string
  limit: number
}

/**
 * Date range presets for trend filtering
 */
export type DateRangePreset = 'last_7_days' | 'last_30_days' | 'last_90_days' | 'last_year' | 'all_time'

/**
 * Get date range from preset
 */
export function getDateRangeFromPreset(preset: DateRangePreset): { from_date: string; to_date: string } {
  const now = new Date()
  const to_date = now.toISOString().split('T')[0]
  let from_date: string

  switch (preset) {
    case 'last_7_days':
      from_date = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      break
    case 'last_30_days':
      from_date = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      break
    case 'last_90_days':
      from_date = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      break
    case 'last_year':
      from_date = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      break
    case 'all_time':
    default:
      from_date = ''
  }

  return { from_date, to_date }
}

/**
 * Convert frontend filters to API query params
 */
export function toApiQueryParams(filters: TrendFilters): TrendQueryParams {
  const params: TrendQueryParams = {}

  if (filters.collection_ids.length > 0) {
    params.collection_ids = filters.collection_ids.join(',')
  }

  if (filters.from_date) {
    params.from_date = filters.from_date
  }

  if (filters.to_date) {
    params.to_date = filters.to_date
  }

  if (filters.limit && filters.limit !== 50) {
    params.limit = filters.limit
  }

  return params
}

// ============================================================================
// Chart Data Types (for Recharts integration)
// ============================================================================

/**
 * Normalized chart data point for PhotoStats trends
 */
export interface PhotoStatsChartData {
  date: string
  orphaned_images: number
  orphaned_xmp: number
  total_files: number
}

/**
 * Normalized chart data point for Photo Pairing trends
 * Includes dynamic camera_id fields
 */
export interface PhotoPairingChartData {
  date: string
  group_count: number
  image_count: number
  [cameraId: string]: string | number // Dynamic camera usage fields
}

/**
 * Normalized chart data point for Pipeline Validation trends
 */
export interface PipelineValidationChartData {
  date: string
  consistent: number
  partial: number
  inconsistent: number
  consistent_ratio: number
}

// ============================================================================
// API Endpoint Definitions (OpenAPI-style documentation)
// ============================================================================

/**
 * GET /api/trends/photostats
 *
 * Get PhotoStats trends (orphaned files over time)
 *
 * Query Parameters: TrendQueryParams
 *
 * Response: 200 PhotoStatsTrendResponse
 * Errors:
 *   - 400: Invalid query parameters
 *   - 500: Internal server error
 */

/**
 * GET /api/trends/photo-pairing
 *
 * Get Photo Pairing trends (camera usage over time)
 *
 * Query Parameters: TrendQueryParams
 *
 * Response: 200 PhotoPairingTrendResponse
 * Errors:
 *   - 400: Invalid query parameters
 *   - 500: Internal server error
 */

/**
 * GET /api/trends/pipeline-validation
 *
 * Get Pipeline Validation trends (consistency over time)
 *
 * Query Parameters: PipelineValidationTrendQueryParams
 *
 * Response: 200 PipelineValidationTrendResponse
 * Errors:
 *   - 400: Invalid query parameters
 *   - 500: Internal server error
 */

/**
 * GET /api/trends/summary
 *
 * Get trend summary for dashboard
 *
 * Query Parameters: TrendSummaryQueryParams
 *
 * Response: 200 TrendSummaryResponse
 * Errors:
 *   - 500: Internal server error
 */
