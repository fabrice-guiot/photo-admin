/**
 * PipelinesPage component
 *
 * Main page for managing photo processing pipelines
 */

import React, { useEffect, useCallback, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, Beaker } from 'lucide-react'
import { useHeaderStats } from '@/contexts/HeaderStatsContext'
import { PipelineList } from '@/components/pipelines/PipelineList'
import { usePipelines, usePipelineStats, usePipelineExport, usePipelineImport } from '@/hooks/usePipelines'
import type { PipelineSummary } from '@/contracts/api/pipelines-api'

export const PipelinesPage: React.FC = () => {
  const navigate = useNavigate()
  const { setStats } = useHeaderStats()
  const fileInputRef = useRef<HTMLInputElement>(null)

  // State
  const [confirmDelete, setConfirmDelete] = useState<PipelineSummary | null>(null)
  const [confirmActivate, setConfirmActivate] = useState<PipelineSummary | null>(null)
  const [confirmDeactivate, setConfirmDeactivate] = useState<PipelineSummary | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  // Hooks
  const {
    pipelines,
    loading,
    error,
    deletePipeline,
    activatePipeline,
    deactivatePipeline,
    refetch,
  } = usePipelines({ autoFetch: true })

  const { stats, refetch: refetchStats } = usePipelineStats(true)
  const { downloadYaml, downloading } = usePipelineExport()
  const { importYaml, importing } = usePipelineImport()

  // Set header stats (TopHeader KPI pattern)
  useEffect(() => {
    if (stats) {
      setStats([
        { label: 'Total Pipelines', value: stats.total_pipelines },
        { label: 'Valid', value: stats.valid_pipelines },
        {
          label: 'Active Pipeline',
          value: stats.active_pipeline_name || 'None',
        },
      ])
    }
    return () => setStats([])
  }, [stats, setStats])

  // Handlers
  const handleCreateNew = useCallback(() => {
    navigate('/pipelines/new')
  }, [navigate])

  const handleImport = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file) return

      try {
        setActionLoading(true)
        setActionError(null)
        const pipeline = await importYaml(file)
        await refetch()
        await refetchStats()
        navigate(`/pipelines/${pipeline.id}`)
      } catch (err: any) {
        setActionError(err.userMessage || 'Failed to import pipeline')
      } finally {
        setActionLoading(false)
        // Reset file input
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      }
    },
    [importYaml, refetch, refetchStats, navigate]
  )

  const handleEdit = useCallback(
    (pipeline: PipelineSummary) => {
      navigate(`/pipelines/${pipeline.id}/edit`)
    },
    [navigate]
  )

  const handleView = useCallback(
    (pipeline: PipelineSummary) => {
      navigate(`/pipelines/${pipeline.id}`)
    },
    [navigate]
  )

  const handleDeleteClick = useCallback((pipeline: PipelineSummary) => {
    setConfirmDelete(pipeline)
  }, [])

  const handleDeleteConfirm = useCallback(async () => {
    if (!confirmDelete) return

    try {
      setActionLoading(true)
      setActionError(null)
      await deletePipeline(confirmDelete.id)
      await refetchStats()
      setConfirmDelete(null)
    } catch (err: any) {
      setActionError(err.userMessage || 'Failed to delete pipeline')
    } finally {
      setActionLoading(false)
    }
  }, [confirmDelete, deletePipeline, refetchStats])

  const handleActivateClick = useCallback((pipeline: PipelineSummary) => {
    setConfirmActivate(pipeline)
  }, [])

  const handleActivateConfirm = useCallback(async () => {
    if (!confirmActivate) return

    try {
      setActionLoading(true)
      setActionError(null)
      await activatePipeline(confirmActivate.id)
      await refetchStats()
      setConfirmActivate(null)
    } catch (err: any) {
      setActionError(err.userMessage || 'Failed to activate pipeline')
    } finally {
      setActionLoading(false)
    }
  }, [confirmActivate, activatePipeline, refetchStats])

  const handleDeactivateClick = useCallback((pipeline: PipelineSummary) => {
    setConfirmDeactivate(pipeline)
  }, [])

  const handleDeactivateConfirm = useCallback(async () => {
    if (!confirmDeactivate) return

    try {
      setActionLoading(true)
      setActionError(null)
      await deactivatePipeline(confirmDeactivate.id)
      await refetchStats()
      setConfirmDeactivate(null)
    } catch (err: any) {
      setActionError(err.userMessage || 'Failed to deactivate pipeline')
    } finally {
      setActionLoading(false)
    }
  }, [confirmDeactivate, deactivatePipeline, refetchStats])

  const handleExport = useCallback(
    async (pipeline: PipelineSummary) => {
      try {
        await downloadYaml(pipeline.id)
      } catch (err: any) {
        setActionError(err.userMessage || 'Failed to export pipeline')
      }
    },
    [downloadYaml]
  )

  return (
    <>
      {/* Hidden file input for import */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".yaml,.yml"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Beta indicator */}
      <div className="mb-4 flex items-center gap-2 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2">
        <Beaker className="h-4 w-4 flex-shrink-0" />
        <span>
          <strong>Beta Feature:</strong> Pipeline management is currently in beta.
          The visual graph editor will be available in a future release.
        </span>
      </div>

      {/* Error Alert */}
      {actionError && (
        <div className="mb-4 flex items-center gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          <span>{actionError}</span>
          <button
            onClick={() => setActionError(null)}
            className="ml-auto text-red-500 hover:text-red-700"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Pipeline List */}
      <PipelineList
        pipelines={pipelines}
        loading={loading || actionLoading || importing}
        error={error}
        onCreateNew={handleCreateNew}
        onImport={handleImport}
        onEdit={handleEdit}
        onDelete={handleDeleteClick}
        onActivate={handleActivateClick}
        onDeactivate={handleDeactivateClick}
        onExport={handleExport}
        onView={handleView}
      />

      {/* Delete Confirmation Modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Delete Pipeline
            </h3>
            <p className="text-gray-600 mb-4">
              Are you sure you want to delete <strong>{confirmDelete.name}</strong>?
              This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmDelete(null)}
                className="px-4 py-2 border rounded-lg text-gray-700 hover:bg-gray-50"
                disabled={actionLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                disabled={actionLoading}
              >
                {actionLoading ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Activate Confirmation Modal */}
      {confirmActivate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Activate Pipeline
            </h3>
            <p className="text-gray-600 mb-4">
              Activating <strong>{confirmActivate.name}</strong> will deactivate any
              currently active pipeline. Pipeline validation runs will use this
              pipeline.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmActivate(null)}
                className="px-4 py-2 border rounded-lg text-gray-700 hover:bg-gray-50"
                disabled={actionLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleActivateConfirm}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                disabled={actionLoading}
              >
                {actionLoading ? 'Activating...' : 'Activate'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Deactivate Confirmation Modal */}
      {confirmDeactivate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Deactivate Pipeline
            </h3>
            <p className="text-gray-600 mb-4">
              Deactivating <strong>{confirmDeactivate.name}</strong> will leave no
              active pipeline. Pipeline validation tool will not run without an
              active pipeline.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmDeactivate(null)}
                className="px-4 py-2 border rounded-lg text-gray-700 hover:bg-gray-50"
                disabled={actionLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleDeactivateConfirm}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
                disabled={actionLoading}
              >
                {actionLoading ? 'Deactivating...' : 'Deactivate'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default PipelinesPage
