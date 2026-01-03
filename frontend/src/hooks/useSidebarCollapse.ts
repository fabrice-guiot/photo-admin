/**
 * useSidebarCollapse Hook
 *
 * Manages sidebar collapse state with localStorage persistence for tablet screens.
 * Allows users to manually collapse the sidebar to gain more content space.
 *
 * Features:
 * - Persists collapse preference to localStorage
 * - Provides collapse/expand toggle functionality
 * - Provides pin/unpin functionality for hamburger mode
 *
 * Issue #41: UX improvement for tablet - force collapse menu to hamburger mode
 */

import { useState, useEffect, useCallback } from 'react'

const STORAGE_KEY = 'sidebar-collapsed'

export interface UseSidebarCollapseReturn {
  /**
   * Whether the sidebar is currently collapsed (in hamburger mode on tablet)
   */
  isCollapsed: boolean

  /**
   * Toggle the collapsed state
   */
  toggleCollapse: () => void

  /**
   * Collapse the sidebar (switch to hamburger mode)
   */
  collapse: () => void

  /**
   * Expand/pin the sidebar (restore normal sidebar)
   */
  expand: () => void
}

/**
 * Hook to manage sidebar collapse state with localStorage persistence.
 *
 * @returns Object with collapse state and control functions
 *
 * @example
 * ```tsx
 * const { isCollapsed, toggleCollapse, collapse, expand } = useSidebarCollapse()
 *
 * // In Sidebar component
 * <button onClick={collapse}>
 *   <ChevronLeft /> Collapse
 * </button>
 *
 * // In hamburger menu
 * <button onClick={expand}>
 *   <Pin /> Pin Sidebar
 * </button>
 * ```
 */
export function useSidebarCollapse(): UseSidebarCollapseReturn {
  // Initialize state from localStorage (default: not collapsed)
  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    // Only access localStorage on client side
    if (typeof window === 'undefined') return false

    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      return stored === 'true'
    } catch {
      // localStorage might be unavailable (e.g., private browsing)
      return false
    }
  })

  // Persist to localStorage when state changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, String(isCollapsed))
    } catch {
      // Silently fail if localStorage is unavailable
    }
  }, [isCollapsed])

  const toggleCollapse = useCallback(() => {
    setIsCollapsed(prev => !prev)
  }, [])

  const collapse = useCallback(() => {
    setIsCollapsed(true)
  }, [])

  const expand = useCallback(() => {
    setIsCollapsed(false)
  }, [])

  return {
    isCollapsed,
    toggleCollapse,
    collapse,
    expand
  }
}

export default useSidebarCollapse
