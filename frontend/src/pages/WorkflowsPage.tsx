/**
 * Workflows Page
 *
 * Manage photo processing workflows and automation
 */

import { Workflow } from 'lucide-react'

export default function WorkflowsPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <Workflow className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-semibold text-foreground mb-2">
          Workflows
        </h2>
        <p className="text-muted-foreground max-w-md">
          Workflow management coming soon. This will allow you to create and
          manage automated photo processing workflows.
        </p>
      </div>
    </div>
  )
}
