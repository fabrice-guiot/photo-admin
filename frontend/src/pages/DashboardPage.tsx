/**
 * Dashboard Page
 *
 * Main dashboard view showing overview of photo collections and analytics
 */

import { LayoutGrid } from 'lucide-react'

export default function DashboardPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <LayoutGrid className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-semibold text-foreground mb-2">
          Dashboard
        </h2>
        <p className="text-muted-foreground max-w-md">
          Dashboard view coming soon. This will show an overview of your photo
          collections, recent activity, and key metrics.
        </p>
      </div>
    </div>
  )
}
