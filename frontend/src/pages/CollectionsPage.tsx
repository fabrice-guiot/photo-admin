import { useState } from 'react'
import { Plus, FolderOpen, HardDrive, FileText, Image } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { KpiCard, KpiCardGrid } from '@/components/ui/kpi-card'
import { useCollections, useCollectionStats } from '../hooks/useCollections'
import { useConnectors } from '../hooks/useConnectors'
import { CollectionList } from '../components/collections/CollectionList'
import CollectionForm from '../components/collections/CollectionForm'
import type { Collection } from '@/contracts/api/collection-api'

export default function CollectionsPage() {
  const {
    collections,
    loading,
    error,
    createCollection,
    updateCollection,
    deleteCollection,
    testCollection,
    refreshCollection
  } = useCollections()

  const { connectors } = useConnectors()

  // KPI Stats (Issue #37)
  const { stats, loading: statsLoading } = useCollectionStats()

  const [open, setOpen] = useState(false)
  const [editingCollection, setEditingCollection] = useState<Collection | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const handleOpen = (collection: Collection | null = null) => {
    setEditingCollection(collection)
    setFormError(null)
    setOpen(true)
  }

  const handleClose = () => {
    setOpen(false)
    setEditingCollection(null)
    setFormError(null)
  }

  const handleSubmit = async (formData: any) => {
    setFormError(null)
    try {
      if (editingCollection) {
        await updateCollection(editingCollection.id, formData)
      } else {
        await createCollection(formData)
      }
      handleClose()
    } catch (err: any) {
      setFormError(err.userMessage || 'Operation failed')
    }
  }

  const handleDelete = (collection: Collection) => {
    deleteCollection(collection.id, false).catch(() => {
      // Error handled by hook
    })
  }

  const handleInfo = (collection: Collection) => {
    testCollection(collection.id).catch(() => {
      // Error handled by hook
    })
  }

  const handleRefresh = (collection: Collection) => {
    refreshCollection(collection.id, false).catch(() => {
      // Error handled by hook
    })
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Photo Collections</h1>
        <Button onClick={() => handleOpen()} className="gap-2">
          <Plus className="h-4 w-4" />
          New Collection
        </Button>
      </div>

      {/* KPI Cards (Issue #37) */}
      <KpiCardGrid>
        <KpiCard
          value={stats?.total_collections ?? 0}
          label="Total Collections"
          icon={<FolderOpen className="h-5 w-5" />}
          loading={statsLoading}
        />
        <KpiCard
          value={stats?.storage_used_formatted ?? '0 B'}
          label="Storage Used"
          icon={<HardDrive className="h-5 w-5" />}
          loading={statsLoading}
        />
        <KpiCard
          value={stats?.file_count ?? 0}
          label="Total Files"
          icon={<FileText className="h-5 w-5" />}
          loading={statsLoading}
        />
        <KpiCard
          value={stats?.image_count ?? 0}
          label="Total Images"
          icon={<Image className="h-5 w-5" />}
          loading={statsLoading}
        />
      </KpiCardGrid>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Collection List */}
      <CollectionList
        collections={collections}
        loading={loading}
        onEdit={handleOpen}
        onDelete={handleDelete}
        onInfo={handleInfo}
        onRefresh={handleRefresh}
      />

      {/* Create/Edit Dialog */}
      <Dialog open={open} onOpenChange={handleClose}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingCollection ? 'Edit Collection' : 'New Collection'}
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4">
            {formError && (
              <Alert variant="destructive" className="mb-4">
                <AlertDescription>{formError}</AlertDescription>
              </Alert>
            )}
            <CollectionForm
              collection={editingCollection}
              connectors={connectors}
              onSubmit={handleSubmit}
              onCancel={handleClose}
            />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
