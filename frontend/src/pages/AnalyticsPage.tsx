/**
 * Analytics Page
 *
 * View analytics and insights about photo collections
 */

import { BarChart3 } from 'lucide-react'

export default function AnalyticsPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <BarChart3 className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-semibold text-foreground mb-2">
          Analytics
        </h2>
        <p className="text-muted-foreground max-w-md">
          Analytics dashboard coming soon. This will provide insights into your
          photo collection usage, storage trends, and performance metrics.
        </p>
      </div>
    </div>
  )
}
