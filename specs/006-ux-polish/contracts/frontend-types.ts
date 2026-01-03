/**
 * Frontend TypeScript Types for UX Polish Epic
 * Feature: 006-ux-polish
 *
 * New types and extensions to existing contracts for:
 * - Collection stats API response
 * - Connector stats API response
 * - Sidebar collapse state
 */

// ============================================================================
// API Response Types (New)
// ============================================================================

/**
 * Collection KPI statistics response
 * Endpoint: GET /api/collections/stats
 */
export interface CollectionStatsResponse {
  /** Total number of collections */
  total_collections: number

  /** Total storage used across all collections in bytes */
  storage_used_bytes: number

  /** Human-readable storage amount (e.g., "2.5 TB") */
  storage_used_formatted: string

  /** Total number of files across all collections */
  file_count: number

  /** Total number of images after grouping */
  image_count: number
}

/**
 * Connector KPI statistics response
 * Endpoint: GET /api/connectors/stats
 */
export interface ConnectorStatsResponse {
  /** Total number of connectors */
  total_connectors: number

  /** Number of active connectors (is_active=true) */
  active_connectors: number
}

// ============================================================================
// UI Component Props (New)
// ============================================================================

/**
 * KPI Card display data
 */
export interface KpiCardData {
  /** Display label for the KPI */
  label: string

  /** Current value (formatted for display) */
  value: string | number

  /** Optional trend indicator */
  trend?: 'up' | 'down' | 'neutral'

  /** Optional percentage change */
  changePercent?: number

  /** Optional icon name (Lucide icon) */
  icon?: string
}

/**
 * Props for KpiCard component
 */
export interface KpiCardProps {
  data: KpiCardData
  loading?: boolean
  className?: string
}

/**
 * Props for KpiCardGrid component
 */
export interface KpiCardGridProps {
  cards: KpiCardData[]
  loading?: boolean
  className?: string
}

// ============================================================================
// Hook Types (New)
// ============================================================================

/**
 * Return type for useCollectionStats hook
 */
export interface UseCollectionStatsReturn {
  stats: CollectionStatsResponse | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

/**
 * Return type for useConnectorStats hook
 */
export interface UseConnectorStatsReturn {
  stats: ConnectorStatsResponse | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

/**
 * Return type for useSidebarCollapse hook
 */
export interface UseSidebarCollapseReturn {
  /** Whether sidebar is manually collapsed */
  isCollapsed: boolean

  /** Toggle collapsed state */
  toggleCollapse: () => void

  /** Expand sidebar (un-collapse) */
  expand: () => void

  /** Collapse sidebar */
  collapse: () => void
}

// ============================================================================
// Extended Types (Modifications to existing)
// ============================================================================

/**
 * Extended collection list options
 * Adds search parameter to existing list options
 */
export interface CollectionListOptions {
  state?: 'live' | 'closed' | 'archived'
  type?: 'local' | 's3' | 'gcs' | 'smb'
  accessible_only?: boolean

  /** NEW: Case-insensitive partial match on collection name */
  search?: string
}

/**
 * Extended sidebar props
 * Adds collapse control props
 */
export interface ExtendedSidebarProps {
  activeItem?: string
  className?: string
  isMobileMenuOpen?: boolean
  onCloseMobileMenu?: () => void

  /** NEW: Whether sidebar is manually collapsed */
  isManuallyCollapsed?: boolean

  /** NEW: Callback when collapse state changes */
  onCollapseChange?: (collapsed: boolean) => void
}

// ============================================================================
// localStorage Types
// ============================================================================

/**
 * Sidebar collapse state stored in localStorage
 */
export interface SidebarCollapseStorage {
  isCollapsed: boolean
}

/**
 * localStorage key for sidebar collapse state
 */
export const SIDEBAR_COLLAPSE_STORAGE_KEY = 'sidebar-collapsed' as const
