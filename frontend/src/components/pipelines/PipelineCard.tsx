/**
 * PipelineCard component
 *
 * Displays a pipeline summary in card format with actions
 */

import React from 'react'
import {
  GitBranch,
  CheckCircle,
  XCircle,
  Zap,
  MoreVertical,
  Pencil,
  Trash2,
  Power,
  PowerOff,
  Download,
  Eye,
} from 'lucide-react'
import type { PipelineSummary } from '@/contracts/api/pipelines-api'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'

interface PipelineCardProps {
  pipeline: PipelineSummary
  onEdit: (pipeline: PipelineSummary) => void
  onDelete: (pipeline: PipelineSummary) => void
  onActivate: (pipeline: PipelineSummary) => void
  onDeactivate: (pipeline: PipelineSummary) => void
  onExport: (pipeline: PipelineSummary) => void
  onView: (pipeline: PipelineSummary) => void
  isLoading?: boolean
}

export const PipelineCard: React.FC<PipelineCardProps> = ({
  pipeline,
  onEdit,
  onDelete,
  onActivate,
  onDeactivate,
  onExport,
  onView,
  isLoading = false,
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <Card
      className={cn(
        'hover:shadow-md transition-shadow',
        pipeline.is_active && 'ring-2 ring-primary border-primary/50',
        isLoading && 'opacity-50 pointer-events-none'
      )}
    >
      <CardContent className="pt-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <div
              className={cn(
                'p-2 rounded-lg',
                pipeline.is_active ? 'bg-primary/10' : 'bg-muted'
              )}
            >
              <GitBranch
                className={cn(
                  'h-5 w-5',
                  pipeline.is_active ? 'text-primary' : 'text-muted-foreground'
                )}
              />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">{pipeline.name}</h3>
              <p className="text-sm text-muted-foreground">v{pipeline.version}</p>
            </div>
          </div>

          {/* Actions Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onView(pipeline)}>
                <Eye className="h-4 w-4 mr-2" />
                View Details
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onEdit(pipeline)}>
                <Pencil className="h-4 w-4 mr-2" />
                Edit
              </DropdownMenuItem>
              {pipeline.is_active ? (
                <DropdownMenuItem
                  onClick={() => onDeactivate(pipeline)}
                  className="text-orange-600 focus:text-orange-600"
                >
                  <PowerOff className="h-4 w-4 mr-2" />
                  Deactivate
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem
                  onClick={() => onActivate(pipeline)}
                  disabled={!pipeline.is_valid}
                  className={pipeline.is_valid ? 'text-green-600 focus:text-green-600' : ''}
                >
                  <Power className="h-4 w-4 mr-2" />
                  Activate
                </DropdownMenuItem>
              )}
              <DropdownMenuItem onClick={() => onExport(pipeline)}>
                <Download className="h-4 w-4 mr-2" />
                Export YAML
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onDelete(pipeline)}
                disabled={pipeline.is_active}
                className={!pipeline.is_active ? 'text-destructive focus:text-destructive' : ''}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Description */}
        {pipeline.description && (
          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
            {pipeline.description}
          </p>
        )}

        {/* Status Badges */}
        <div className="flex items-center gap-2 mb-3">
          {pipeline.is_active && (
            <Badge variant="default" className="gap-1">
              <Zap className="h-3 w-3" />
              Active
            </Badge>
          )}
          {pipeline.is_valid ? (
            <Badge variant="outline" className="gap-1 border-green-500/50 text-green-600 dark:text-green-400">
              <CheckCircle className="h-3 w-3" />
              Valid
            </Badge>
          ) : (
            <Badge variant="destructive" className="gap-1">
              <XCircle className="h-3 w-3" />
              Invalid
            </Badge>
          )}
        </div>

        {/* Metadata */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{pipeline.node_count} nodes</span>
          <span>Updated {formatDate(pipeline.updated_at)}</span>
        </div>
      </CardContent>
    </Card>
  )
}

export default PipelineCard
