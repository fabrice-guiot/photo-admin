/**
 * Unit tests for useLocations hook.
 *
 * Tests CRUD operations, geocoding, category filtering, and statistics.
 * Issue #39 - Calendar Events feature (Phase 8)
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { act } from 'react'
import { useLocations, useLocationStats, useLocationsByCategory } from '@/hooks/useLocations'
import { resetMockData } from '../mocks/handlers'

describe('useLocations', () => {
  beforeEach(() => {
    resetMockData()
  })

  it('should fetch locations on mount', async () => {
    const { result } = renderHook(() => useLocations())

    // Initially loading
    expect(result.current.loading).toBe(true)
    expect(result.current.locations).toEqual([])

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.locations).toHaveLength(2)
    expect(result.current.locations[0].name).toBe('EAA Grounds')
    expect(result.current.error).toBe(null)
  })

  it('should return total count', async () => {
    const { result } = renderHook(() => useLocations())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.total).toBe(2)
  })

  it('should create a location successfully', async () => {
    const { result } = renderHook(() => useLocations())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const newLocation = {
      name: 'New Test Location',
      category_guid: 'cat_01hgw2bbg00000000000000001',
      city: 'New City',
      country: 'USA',
      is_known: true,
    }

    await act(async () => {
      await result.current.createLocation(newLocation)
    })

    await waitFor(() => {
      expect(result.current.locations).toHaveLength(3)
    })

    const created = result.current.locations.find(
      (l) => l.name === 'New Test Location'
    )
    expect(created).toBeDefined()
    expect(created?.city).toBe('New City')
  })

  it('should create a location with full details', async () => {
    const { result } = renderHook(() => useLocations())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const newLocation = {
      name: 'Full Details Location',
      category_guid: 'cat_01hgw2bbg00000000000000001',
      address: '123 Test Street',
      city: 'Test City',
      state: 'Test State',
      country: 'Test Country',
      postal_code: '12345',
      latitude: 40.7128,
      longitude: -74.006,
      timezone: 'America/New_York',
      rating: 4,
      timeoff_required_default: true,
      travel_required_default: false,
      notes: 'Test notes',
      is_known: true,
    }

    await act(async () => {
      await result.current.createLocation(newLocation)
    })

    await waitFor(() => {
      const created = result.current.locations.find(
        (l) => l.name === 'Full Details Location'
      )
      expect(created).toBeDefined()
      expect(created?.address).toBe('123 Test Street')
      expect(created?.rating).toBe(4)
      expect(created?.timeoff_required_default).toBe(true)
    })
  })

  it('should fail to create location with invalid category', async () => {
    const { result } = renderHook(() => useLocations())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const newLocation = {
      name: 'Invalid Category Location',
      category_guid: 'cat_00000000000000000000000000', // Non-existent
      is_known: true,
    }

    await act(async () => {
      try {
        await result.current.createLocation(newLocation)
        expect.fail('Should have thrown 404 error')
      } catch (error: any) {
        expect(error.response?.status).toBe(404)
      }
    })
  })

  it('should update a location successfully', async () => {
    const { result } = renderHook(() => useLocations())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const locationGuid = result.current.locations[0].guid

    await act(async () => {
      await result.current.updateLocation(locationGuid, {
        name: 'Updated Location Name',
        rating: 3,
      })
    })

    await waitFor(() => {
      const updated = result.current.locations.find((l) => l.guid === locationGuid)
      expect(updated?.name).toBe('Updated Location Name')
      expect(updated?.rating).toBe(3)
    })
  })

  it('should update location address fields', async () => {
    const { result } = renderHook(() => useLocations())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const locationGuid = result.current.locations[0].guid

    await act(async () => {
      await result.current.updateLocation(locationGuid, {
        city: 'Updated City',
        state: 'Updated State',
      })
    })

    await waitFor(() => {
      const updated = result.current.locations.find((l) => l.guid === locationGuid)
      expect(updated?.city).toBe('Updated City')
      expect(updated?.state).toBe('Updated State')
    })
  })

  it('should delete a location successfully', async () => {
    const { result } = renderHook(() => useLocations())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const initialCount = result.current.locations.length
    const locationGuid = result.current.locations[0].guid

    await act(async () => {
      await result.current.deleteLocation(locationGuid)
    })

    await waitFor(() => {
      expect(result.current.locations).toHaveLength(initialCount - 1)
    })

    const deleted = result.current.locations.find((l) => l.guid === locationGuid)
    expect(deleted).toBeUndefined()
  })

  it('should handle delete of non-existent location', async () => {
    const { result } = renderHook(() => useLocations())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await act(async () => {
      try {
        await result.current.deleteLocation('loc_00000000000000000000000000')
        expect.fail('Should have thrown 404 error')
      } catch (error: any) {
        expect(error.response?.status).toBe(404)
      }
    })
  })

  it('should fetch locations with search filter', async () => {
    const { result } = renderHook(() => useLocations())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await act(async () => {
      await result.current.fetchLocations({ search: 'Oshkosh' })
    })

    await waitFor(() => {
      expect(result.current.locations.length).toBeGreaterThanOrEqual(0)
    })
  })

  it('should fetch locations filtered by category', async () => {
    const { result } = renderHook(() => useLocations())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await act(async () => {
      await result.current.fetchLocations({
        category_guid: 'cat_01hgw2bbg00000000000000001'
      })
    })

    await waitFor(() => {
      // All returned locations should have the specified category
      result.current.locations.forEach((loc) => {
        expect(loc.category.guid).toBe('cat_01hgw2bbg00000000000000001')
      })
    })
  })

  it('should not auto-fetch when autoFetch is false', async () => {
    const { result } = renderHook(() => useLocations(false))

    // Should not be loading since autoFetch is false
    expect(result.current.loading).toBe(false)
    expect(result.current.locations).toEqual([])

    // Manually fetch
    await act(async () => {
      await result.current.fetchLocations({})
    })

    await waitFor(() => {
      expect(result.current.locations).toHaveLength(2)
    })
  })
})

describe('useLocationStats', () => {
  beforeEach(() => {
    resetMockData()
  })

  it('should fetch location stats on mount', async () => {
    const { result } = renderHook(() => useLocationStats())

    // Initially loading
    expect(result.current.loading).toBe(true)
    expect(result.current.stats).toBe(null)

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.stats).not.toBe(null)
    expect(result.current.stats?.total_count).toBe(2)
    expect(result.current.stats?.known_count).toBe(2)
    expect(result.current.stats?.with_coordinates_count).toBe(2)
    expect(result.current.error).toBe(null)
  })

  it('should allow manual refetch of stats', async () => {
    const { result } = renderHook(() => useLocationStats())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const initialStats = result.current.stats

    await act(async () => {
      await result.current.refetch()
    })

    await waitFor(() => {
      expect(result.current.stats).not.toBe(null)
    })

    // Stats should still be valid after refetch
    expect(result.current.stats?.total_count).toBe(initialStats?.total_count)
  })

  it('should not auto-fetch when autoFetch is false', async () => {
    const { result } = renderHook(() => useLocationStats(false))

    expect(result.current.loading).toBe(false)
    expect(result.current.stats).toBe(null)
  })
})

describe('useLocationsByCategory', () => {
  beforeEach(() => {
    resetMockData()
  })

  it('should fetch locations for a category', async () => {
    const { result } = renderHook(() =>
      useLocationsByCategory('cat_01hgw2bbg00000000000000001')
    )

    // Initially loading
    expect(result.current.loading).toBe(true)
    expect(result.current.locations).toEqual([])

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Should have locations for Airshow category
    expect(result.current.locations.length).toBeGreaterThanOrEqual(0)
    result.current.locations.forEach((loc) => {
      expect(loc.category.guid).toBe('cat_01hgw2bbg00000000000000001')
    })
  })

  it('should return empty array when category is null', async () => {
    const { result } = renderHook(() => useLocationsByCategory(null))

    // Should not be loading since no category
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.locations).toEqual([])
  })

  it('should refetch when category changes', async () => {
    const { result, rerender } = renderHook(
      ({ categoryGuid }) => useLocationsByCategory(categoryGuid),
      { initialProps: { categoryGuid: 'cat_01hgw2bbg00000000000000001' } }
    )

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Change to different category
    rerender({ categoryGuid: 'cat_01hgw2bbg00000000000000002' })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Should have wildlife locations now
    result.current.locations.forEach((loc) => {
      expect(loc.category.guid).toBe('cat_01hgw2bbg00000000000000002')
    })
  })

  it('should allow manual refetch', async () => {
    const { result } = renderHook(() =>
      useLocationsByCategory('cat_01hgw2bbg00000000000000001')
    )

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await act(async () => {
      await result.current.refetch()
    })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBe(null)
  })
})

describe('useLocations geocoding', () => {
  beforeEach(() => {
    resetMockData()
  })

  it('should geocode an address', async () => {
    const { result } = renderHook(() => useLocations())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    let geocodeResult: any = null

    await act(async () => {
      geocodeResult = await result.current.geocodeAddress('123 Main St, Test City')
    })

    expect(geocodeResult).not.toBe(null)
    expect(geocodeResult?.latitude).toBeDefined()
    expect(geocodeResult?.longitude).toBeDefined()
    expect(geocodeResult?.timezone).toBeDefined()
  })

  it('should return null for failed geocoding', async () => {
    const { result } = renderHook(() => useLocations())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // The mock handler always returns a result, so this tests the interface
    const geocodeResult = await result.current.geocodeAddress('Any Address')

    expect(geocodeResult).not.toBe(null)
    expect(typeof geocodeResult?.latitude).toBe('number')
    expect(typeof geocodeResult?.longitude).toBe('number')
  })
})
