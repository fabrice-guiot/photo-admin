/**
 * KPI Card Components
 *
 * Reusable components for displaying Key Performance Indicator cards
 * in dashboard topbands (Issue #37)
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"

// ============================================================================
// KpiCard Component
// ============================================================================

export interface KpiCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** The main value to display (e.g., "5", "2.5 TB") */
  value: string | number
  /** Label describing the KPI (e.g., "Total Collections") */
  label: string
  /** Optional icon to display (React component) */
  icon?: React.ReactNode
  /** Loading state - shows skeleton */
  loading?: boolean
}

const KpiCard = React.forwardRef<HTMLDivElement, KpiCardProps>(
  ({ className, value, label, icon, loading = false, ...props }, ref) => {
    return (
      <Card
        ref={ref}
        className={cn("min-w-[140px]", className)}
        {...props}
      >
        <CardContent className="flex items-center gap-3 p-4">
          {icon && (
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              {icon}
            </div>
          )}
          <div className="flex flex-col">
            {loading ? (
              <>
                <div className="h-7 w-16 animate-pulse rounded bg-muted" />
                <div className="mt-1 h-4 w-24 animate-pulse rounded bg-muted" />
              </>
            ) : (
              <>
                <span className="text-2xl font-bold tracking-tight">
                  {value}
                </span>
                <span className="text-sm text-muted-foreground">
                  {label}
                </span>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }
)
KpiCard.displayName = "KpiCard"

// ============================================================================
// KpiCardGrid Component
// ============================================================================

export interface KpiCardGridProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const KpiCardGrid = React.forwardRef<HTMLDivElement, KpiCardGridProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "grid gap-4 grid-cols-2 md:grid-cols-4 lg:grid-cols-5",
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)
KpiCardGrid.displayName = "KpiCardGrid"

export { KpiCard, KpiCardGrid }
