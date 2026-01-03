/**
 * Header Stats Context
 *
 * Allows pages to dynamically set stats displayed in the TopHeader.
 * Stats are shown in the topbar next to the bell icon.
 */

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import type { HeaderStat } from '@/components/layout/TopHeader'

// ============================================================================
// Types
// ============================================================================

interface HeaderStatsContextValue {
  stats: HeaderStat[]
  setStats: (stats: HeaderStat[]) => void
  clearStats: () => void
}

// ============================================================================
// Context
// ============================================================================

const HeaderStatsContext = createContext<HeaderStatsContextValue | null>(null)

// ============================================================================
// Provider
// ============================================================================

interface HeaderStatsProviderProps {
  children: ReactNode
  defaultStats?: HeaderStat[]
}

export function HeaderStatsProvider({ children, defaultStats = [] }: HeaderStatsProviderProps) {
  const [stats, setStatsState] = useState<HeaderStat[]>(defaultStats)

  const setStats = useCallback((newStats: HeaderStat[]) => {
    setStatsState(newStats)
  }, [])

  const clearStats = useCallback(() => {
    setStatsState([])
  }, [])

  return (
    <HeaderStatsContext.Provider value={{ stats, setStats, clearStats }}>
      {children}
    </HeaderStatsContext.Provider>
  )
}

// ============================================================================
// Hook
// ============================================================================

export function useHeaderStats() {
  const context = useContext(HeaderStatsContext)
  if (!context) {
    throw new Error('useHeaderStats must be used within a HeaderStatsProvider')
  }
  return context
}
