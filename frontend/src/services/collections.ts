/**
 * Collection API service
 *
 * Handles all API calls related to photo collections
 */

import api from './api'
import type {
  Collection,
  CollectionCreateRequest,
  CollectionUpdateRequest,
  CollectionListQueryParams,
  CollectionTestResponse,
  CollectionDeleteResponse,
  CollectionStatsResponse
} from '@/contracts/api/collection-api'

/**
 * List all collections with optional filters
 */
export const listCollections = async (filters: CollectionListQueryParams = {}): Promise<Collection[]> => {
  const params: CollectionListQueryParams = {}
  if (filters.state) params.state = filters.state
  if (filters.type) params.type = filters.type
  if (filters.accessible_only) params.accessible_only = true
  if (filters.search) params.search = filters.search
  if (filters.limit) params.limit = filters.limit
  if (filters.offset) params.offset = filters.offset

  const response = await api.get<Collection[]>('/collections', { params })
  return response.data
}

/**
 * Get a single collection by GUID
 * @param guid - External ID (col_xxx format)
 */
export const getCollection = async (guid: string): Promise<Collection> => {
  const response = await api.get<Collection>(`/collections/${guid}`)
  return response.data
}

/**
 * Create a new collection
 */
export const createCollection = async (data: CollectionCreateRequest): Promise<Collection> => {
  const response = await api.post<Collection>('/collections', data)
  return response.data
}

/**
 * Update an existing collection
 * @param guid - External ID (col_xxx format)
 */
export const updateCollection = async (guid: string, data: CollectionUpdateRequest): Promise<Collection> => {
  const response = await api.put<Collection>(`/collections/${guid}`, data)
  return response.data
}

/**
 * Delete a collection
 * @param guid - External ID (col_xxx format)
 * @returns Returns result info if collection has data, void if deleted
 * @throws Error 409 if results/jobs exist and force=false
 */
export const deleteCollection = async (
  guid: string,
  force = false
): Promise<CollectionDeleteResponse | void> => {
  const params = force ? { force_delete: force } : {}
  const response = await api.delete<CollectionDeleteResponse>(`/collections/${guid}`, { params })
  // If status is 200, return the result/job info
  if (response.status === 200) {
    return response.data
  }
  // Status 204 means deleted successfully, no data to return
}

/**
 * Test collection accessibility
 * @param guid - External ID (col_xxx format)
 */
export const testCollection = async (guid: string): Promise<CollectionTestResponse> => {
  const response = await api.post<CollectionTestResponse>(`/collections/${guid}/test`)
  return response.data
}

/**
 * Refresh collection cache
 * @param guid - External ID (col_xxx format)
 */
export const refreshCollection = async (guid: string, confirm = false): Promise<any> => {
  const params = confirm ? { confirm: true } : {}
  const response = await api.post(`/collections/${guid}/refresh`, null, { params })
  return response.data
}

/**
 * Get collection statistics (KPIs)
 * Returns aggregated stats unaffected by filters
 */
export const getCollectionStats = async (): Promise<CollectionStatsResponse> => {
  const response = await api.get<CollectionStatsResponse>('/collections/stats')
  return response.data
}

/**
 * Assign a pipeline to a collection
 * Stores the pipeline's current version as the pinned version
 * @param collectionGuid - Collection GUID (col_xxx format)
 * @param pipelineGuid - Pipeline GUID (pip_xxx format)
 */
export const assignPipeline = async (collectionGuid: string, pipelineGuid: string): Promise<Collection> => {
  const response = await api.post<Collection>(
    `/collections/${collectionGuid}/assign-pipeline`,
    null,
    { params: { pipeline_guid: pipelineGuid } }
  )
  return response.data
}

/**
 * Clear pipeline assignment from a collection
 * Collection will use default pipeline at runtime
 * @param collectionGuid - Collection GUID (col_xxx format)
 */
export const clearPipeline = async (collectionGuid: string): Promise<Collection> => {
  const response = await api.post<Collection>(`/collections/${collectionGuid}/clear-pipeline`)
  return response.data
}
