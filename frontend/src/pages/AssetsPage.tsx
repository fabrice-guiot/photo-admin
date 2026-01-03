/**
 * Assets Page
 *
 * Browse and manage photo assets across all collections
 */

import { Archive } from 'lucide-react'

export default function AssetsPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <Archive className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-semibold text-foreground mb-2">
          Assets
        </h2>
        <p className="text-muted-foreground max-w-md">
          Asset browser coming soon. This will allow you to browse, search, and
          manage photo assets across all your collections.
        </p>
      </div>
    </div>
  )
}
