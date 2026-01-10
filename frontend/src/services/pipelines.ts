/**
 * Pipelines API service
 *
 * Handles all API calls related to pipeline management
 */

import api from './api'
import type {
  Pipeline,
  PipelineSummary,
  PipelineListResponse,
  PipelineCreateRequest,
  PipelineUpdateRequest,
  PipelineStatsResponse,
  PipelineDeleteResponse,
  PipelineListQueryParams,
  ValidationResult,
  FilenamePreviewRequest,
  FilenamePreviewResponse,
  PipelineHistoryEntry,
} from '@/contracts/api/pipelines-api'

/**
 * List all pipelines with optional filters
 */
export const listPipelines = async (params: PipelineListQueryParams = {}): Promise<PipelineSummary[]> => {
  const response = await api.get<PipelineListResponse>('/pipelines', { params })
  return response.data.items
}

/**
 * Get pipeline details by ID or external ID
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const getPipeline = async (identifier: number | string): Promise<Pipeline> => {
  const response = await api.get<Pipeline>(`/pipelines/${identifier}`)
  return response.data
}

/**
 * Create a new pipeline
 */
export const createPipeline = async (data: PipelineCreateRequest): Promise<Pipeline> => {
  const response = await api.post<Pipeline>('/pipelines', data)
  return response.data
}

/**
 * Update an existing pipeline
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const updatePipeline = async (identifier: number | string, data: PipelineUpdateRequest): Promise<Pipeline> => {
  const response = await api.put<Pipeline>(`/pipelines/${identifier}`, data)
  return response.data
}

/**
 * Delete a pipeline
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const deletePipeline = async (identifier: number | string): Promise<PipelineDeleteResponse> => {
  const response = await api.delete<PipelineDeleteResponse>(`/pipelines/${identifier}`)
  return response.data
}

/**
 * Activate a pipeline for validation runs
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const activatePipeline = async (identifier: number | string): Promise<Pipeline> => {
  const response = await api.post<Pipeline>(`/pipelines/${identifier}/activate`)
  return response.data
}

/**
 * Deactivate a pipeline
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const deactivatePipeline = async (identifier: number | string): Promise<Pipeline> => {
  const response = await api.post<Pipeline>(`/pipelines/${identifier}/deactivate`)
  return response.data
}

/**
 * Set a pipeline as the default for tool execution
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const setDefaultPipeline = async (identifier: number | string): Promise<Pipeline> => {
  const response = await api.post<Pipeline>(`/pipelines/${identifier}/set-default`)
  return response.data
}

/**
 * Remove default status from a pipeline
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const unsetDefaultPipeline = async (identifier: number | string): Promise<Pipeline> => {
  const response = await api.post<Pipeline>(`/pipelines/${identifier}/unset-default`)
  return response.data
}

/**
 * Validate pipeline structure
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const validatePipeline = async (identifier: number | string): Promise<ValidationResult> => {
  const response = await api.post<ValidationResult>(`/pipelines/${identifier}/validate`)
  return response.data
}

/**
 * Preview expected filenames for a pipeline
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const previewFilenames = async (
  identifier: number | string,
  data: FilenamePreviewRequest = {}
): Promise<FilenamePreviewResponse> => {
  const response = await api.post<FilenamePreviewResponse>(`/pipelines/${identifier}/preview`, data)
  return response.data
}

/**
 * Get pipeline version history
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const getPipelineHistory = async (identifier: number | string): Promise<PipelineHistoryEntry[]> => {
  const response = await api.get<PipelineHistoryEntry[]>(`/pipelines/${identifier}/history`)
  return response.data
}

/**
 * Get a specific version of a pipeline
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const getPipelineVersion = async (identifier: number | string, version: number): Promise<Pipeline> => {
  const response = await api.get<Pipeline>(`/pipelines/${identifier}/versions/${version}`)
  return response.data
}

/**
 * Get pipeline statistics for KPIs
 */
export const getPipelineStats = async (): Promise<PipelineStatsResponse> => {
  const response = await api.get<PipelineStatsResponse>('/pipelines/stats')
  return response.data
}

/**
 * Import pipeline from YAML file
 */
export const importPipeline = async (file: File): Promise<Pipeline> => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post<Pipeline>('/pipelines/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

/**
 * Get URL for downloading pipeline as YAML
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const getExportUrl = (identifier: number | string): string => {
  const baseUrl = api.defaults.baseURL || 'http://localhost:8000/api'
  return `${baseUrl}/pipelines/${identifier}/export`
}

/**
 * Download pipeline as YAML file
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const downloadPipelineYaml = async (identifier: number | string): Promise<{ blob: Blob; filename: string }> => {
  const response = await api.get(`/pipelines/${identifier}/export`, {
    responseType: 'blob',
  })

  // Extract filename from Content-Disposition header
  const contentDisposition = response.headers['content-disposition']
  let filename = `pipeline_${identifier}.yaml` // Fallback

  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="?([^";\n]+)"?/)
    if (filenameMatch && filenameMatch[1]) {
      filename = filenameMatch[1]
    }
  }

  return { blob: response.data, filename }
}

/**
 * Download a specific version of a pipeline as YAML file
 * @param identifier - Numeric ID or external ID (pip_xxx)
 */
export const downloadPipelineVersionYaml = async (
  identifier: number | string,
  version: number
): Promise<{ blob: Blob; filename: string }> => {
  const response = await api.get(`/pipelines/${identifier}/versions/${version}/export`, {
    responseType: 'blob',
  })

  // Extract filename from Content-Disposition header
  const contentDisposition = response.headers['content-disposition']
  let filename = `pipeline_${identifier}_v${version}.yaml` // Fallback

  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="?([^";\n]+)"?/)
    if (filenameMatch && filenameMatch[1]) {
      filename = filenameMatch[1]
    }
  }

  return { blob: response.data, filename }
}
