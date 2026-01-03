import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { act } from 'react'
import { useConnectors } from '@/hooks/useConnectors'
import { resetMockData } from '../mocks/handlers'

describe('useConnectors', () => {
  beforeEach(() => {
    resetMockData()
  })

  it('should fetch connectors on mount', async () => {
    const { result } = renderHook(() => useConnectors())

    // Initially loading
    expect(result.current.loading).toBe(true)
    expect(result.current.connectors).toEqual([])

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.connectors).toHaveLength(2)
    expect(result.current.connectors[0].name).toBe('Test S3 Connector')
    expect(result.current.error).toBe(null)
  })

  it('should create a new connector successfully', async () => {
    const { result } = renderHook(() => useConnectors())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const newConnector = {
      name: 'New S3 Connector',
      type: 'S3' as const,
      active: true,
      credentials: {
        access_key_id: 'AKIAIOSFODNN7EXAMPLE',
        secret_access_key: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        region: 'us-east-1',
        bucket: '',
      },
    }

    await act(async () => {
      await result.current.createConnector(newConnector)
    })

    await waitFor(() => {
      expect(result.current.connectors).toHaveLength(3)
    })

    const createdConnector = result.current.connectors.find(
      (c) => c.name === 'New S3 Connector'
    )
    expect(createdConnector).toBeDefined()
    expect(createdConnector?.type).toBe('S3')
  })

  it('should update an existing connector', async () => {
    const { result } = renderHook(() => useConnectors())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const connectorId = result.current.connectors[0].id

    await act(async () => {
      await result.current.updateConnector(connectorId, {
        name: 'Updated Connector Name',
      })
    })

    await waitFor(() => {
      const updated = result.current.connectors.find((c) => c.id === connectorId)
      expect(updated?.name).toBe('Updated Connector Name')
    })
  })

  it('should delete a connector successfully', async () => {
    const { result } = renderHook(() => useConnectors())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const initialCount = result.current.connectors.length
    const connectorId = result.current.connectors[1].id // GCS connector (not referenced)

    await act(async () => {
      await result.current.deleteConnector(connectorId)
    })

    await waitFor(() => {
      expect(result.current.connectors).toHaveLength(initialCount - 1)
    })

    const deleted = result.current.connectors.find((c) => c.id === connectorId)
    expect(deleted).toBeUndefined()
  })

  it('should handle 409 error for delete protection', async () => {
    const { result } = renderHook(() => useConnectors())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Connector ID 1 is referenced by collection ID 2
    const connectorId = result.current.connectors[0].id

    await act(async () => {
      try {
        await result.current.deleteConnector(connectorId)
        // Should throw, fail if it doesn't
        expect.fail('Should have thrown 409 error')
      } catch (error: any) {
        expect(error.response?.status).toBe(409)
        expect(error.response?.data?.detail).toContain('referenced by')
      }
    })

    // Connector should still exist
    await waitFor(() => {
      const connector = result.current.connectors.find((c) => c.id === connectorId)
      expect(connector).toBeDefined()
    })
  })

  it('should test a connector connection', async () => {
    const { result } = renderHook(() => useConnectors())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const connectorId = result.current.connectors[0].id

    let response: { success: boolean; message: string } | undefined

    await act(async () => {
      response = await result.current.testConnector(connectorId)
      expect(response.success).toBe(true)
      expect(response.message).toBe('Connection successful')
    })

    // Verify last_validated_at was updated
    await act(async () => {
      await result.current.fetchConnectors()
    })

    await waitFor(() => {
      const tested = result.current.connectors.find((c) => c.id === connectorId)
      expect(tested?.last_validated_at).toBeTruthy()
    })
  })
})
