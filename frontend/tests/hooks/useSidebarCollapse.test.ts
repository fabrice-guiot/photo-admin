/**
 * useSidebarCollapse Hook Tests
 *
 * Tests for sidebar collapse state management and localStorage persistence.
 * Issue #41: UX improvement for tablet - force collapse menu to hamburger mode
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSidebarCollapse } from '@/hooks/useSidebarCollapse'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
    get length() {
      return Object.keys(store).length
    },
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('useSidebarCollapse', () => {
  beforeEach(() => {
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('returns isCollapsed: false by default', () => {
      const { result } = renderHook(() => useSidebarCollapse())

      expect(result.current.isCollapsed).toBe(false)
    })

    it('reads initial state from localStorage', () => {
      localStorageMock.setItem('sidebar-collapsed', 'true')

      const { result } = renderHook(() => useSidebarCollapse())

      expect(result.current.isCollapsed).toBe(true)
    })

    it('returns false if localStorage has invalid value', () => {
      localStorageMock.setItem('sidebar-collapsed', 'invalid')

      const { result } = renderHook(() => useSidebarCollapse())

      expect(result.current.isCollapsed).toBe(false)
    })
  })

  describe('collapse()', () => {
    it('sets isCollapsed to true', () => {
      const { result } = renderHook(() => useSidebarCollapse())

      act(() => {
        result.current.collapse()
      })

      expect(result.current.isCollapsed).toBe(true)
    })

    it('persists collapsed state to localStorage', () => {
      const { result } = renderHook(() => useSidebarCollapse())

      act(() => {
        result.current.collapse()
      })

      expect(localStorageMock.setItem).toHaveBeenCalledWith('sidebar-collapsed', 'true')
    })
  })

  describe('expand()', () => {
    it('sets isCollapsed to false', () => {
      localStorageMock.setItem('sidebar-collapsed', 'true')
      const { result } = renderHook(() => useSidebarCollapse())

      act(() => {
        result.current.expand()
      })

      expect(result.current.isCollapsed).toBe(false)
    })

    it('persists expanded state to localStorage', () => {
      localStorageMock.setItem('sidebar-collapsed', 'true')
      const { result } = renderHook(() => useSidebarCollapse())

      act(() => {
        result.current.expand()
      })

      expect(localStorageMock.setItem).toHaveBeenCalledWith('sidebar-collapsed', 'false')
    })
  })

  describe('toggleCollapse()', () => {
    it('toggles from expanded to collapsed', () => {
      const { result } = renderHook(() => useSidebarCollapse())

      expect(result.current.isCollapsed).toBe(false)

      act(() => {
        result.current.toggleCollapse()
      })

      expect(result.current.isCollapsed).toBe(true)
    })

    it('toggles from collapsed to expanded', () => {
      localStorageMock.setItem('sidebar-collapsed', 'true')
      const { result } = renderHook(() => useSidebarCollapse())

      expect(result.current.isCollapsed).toBe(true)

      act(() => {
        result.current.toggleCollapse()
      })

      expect(result.current.isCollapsed).toBe(false)
    })
  })

  describe('State Persistence', () => {
    it('persists state across multiple collapse/expand cycles', () => {
      const { result } = renderHook(() => useSidebarCollapse())

      // Start expanded
      expect(result.current.isCollapsed).toBe(false)

      // Collapse
      act(() => {
        result.current.collapse()
      })
      expect(result.current.isCollapsed).toBe(true)
      expect(localStorageMock.setItem).toHaveBeenLastCalledWith('sidebar-collapsed', 'true')

      // Expand
      act(() => {
        result.current.expand()
      })
      expect(result.current.isCollapsed).toBe(false)
      expect(localStorageMock.setItem).toHaveBeenLastCalledWith('sidebar-collapsed', 'false')

      // Collapse again
      act(() => {
        result.current.collapse()
      })
      expect(result.current.isCollapsed).toBe(true)
      expect(localStorageMock.setItem).toHaveBeenLastCalledWith('sidebar-collapsed', 'true')
    })

    it('maintains state across page navigations (simulated by re-render)', () => {
      // First render - collapse the sidebar
      const { result: result1, unmount } = renderHook(() => useSidebarCollapse())

      act(() => {
        result1.current.collapse()
      })

      expect(result1.current.isCollapsed).toBe(true)

      // Unmount (simulating navigation away)
      unmount()

      // Second render (simulating navigation back)
      const { result: result2 } = renderHook(() => useSidebarCollapse())

      // State should be preserved
      expect(result2.current.isCollapsed).toBe(true)
    })
  })
})
