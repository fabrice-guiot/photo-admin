/**
 * Main Layout Component
 *
 * Composes Sidebar + TopHeader + content area into a unified layout.
 * Provides consistent structure across all pages of the application.
 */

import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { Sidebar } from './Sidebar'
import { TopHeader, type HeaderStat } from './TopHeader'
import { cn } from '@/lib/utils'

// ============================================================================
// Types
// ============================================================================

export interface MainLayoutProps {
  /**
   * Page content (typically a page component)
   */
  children: ReactNode

  /**
   * Optional page title for TopHeader
   * If not provided, defaults to "Photo Admin"
   */
  pageTitle?: string

  /**
   * Optional page icon for TopHeader
   */
  pageIcon?: LucideIcon

  /**
   * Optional stats for TopHeader
   */
  stats?: HeaderStat[]

  /**
   * Additional CSS classes for content area
   */
  className?: string
}

// ============================================================================
// Component
// ============================================================================

/**
 * MainLayout provides the application shell:
 *
 * Layout Structure:
 * ┌─────────────┬──────────────────────────────┐
 * │             │ TopHeader (4rem height)      │
 * │  Sidebar    ├──────────────────────────────┤
 * │  (14rem)    │                              │
 * │             │  Content Area (scrollable)   │
 * │             │                              │
 * └─────────────┴──────────────────────────────┘
 */
export function MainLayout({
  children,
  pageTitle = 'Photo Admin',
  pageIcon,
  stats,
  className,
}: MainLayoutProps) {
  return (
    <div className="flex h-screen w-full bg-background">
      {/* Sidebar: Fixed left navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col">
        {/* TopHeader: Page title, stats, notifications, user profile */}
        <TopHeader pageTitle={pageTitle} pageIcon={pageIcon} stats={stats} />

        {/* Scrollable Content Area */}
        <main className={cn('flex-1 overflow-auto p-6', className)}>
          {children}
        </main>
      </div>
    </div>
  )
}

export default MainLayout
