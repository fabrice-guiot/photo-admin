/**
 * Photo Admin Application
 *
 * Main application component with routing and layout
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { type ReactElement } from 'react'
import {
  LayoutGrid,
  Workflow,
  FolderOpen,
  Archive,
  ChartNoAxesCombined,
  Users,
  Settings,
  GitBranch,
  Calendar,
  BookOpen,
  type LucideIcon
} from 'lucide-react'
import { MainLayout } from './components/layout/MainLayout'
import { ErrorBoundary } from './components/error'

// Page components
import DashboardPage from './pages/DashboardPage'
import NotFoundPage from './pages/NotFoundPage'
import WorkflowsPage from './pages/WorkflowsPage'
import CollectionsPage from './pages/CollectionsPage'
import AssetsPage from './pages/AssetsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import TeamPage from './pages/TeamPage'
import SettingsPage from './pages/SettingsPage'
import PipelinesPage from './pages/PipelinesPage'
import PipelineEditorPage from './pages/PipelineEditorPage'
import EventsPage from './pages/EventsPage'
import DirectoryPage from './pages/DirectoryPage'

// ============================================================================
// Route Configuration
// ============================================================================

interface RouteConfig {
  path: string
  element: ReactElement
  pageTitle: string
  pageIcon?: LucideIcon
}

const routes: RouteConfig[] = [
  {
    path: '/',
    element: <DashboardPage />,
    pageTitle: 'Dashboard',
    pageIcon: LayoutGrid,
  },
  {
    path: '/events',
    element: <EventsPage />,
    pageTitle: 'Events',
    pageIcon: Calendar,
  },
  {
    path: '/workflows',
    element: <WorkflowsPage />,
    pageTitle: 'Workflows',
    pageIcon: Workflow,
  },
  {
    path: '/collections',
    element: <CollectionsPage />,
    pageTitle: 'Collections',
    pageIcon: FolderOpen,
  },
  {
    path: '/assets',
    element: <AssetsPage />,
    pageTitle: 'Assets',
    pageIcon: Archive,
  },
  {
    path: '/analytics',
    element: <AnalyticsPage />,
    pageTitle: 'Analytics',
    pageIcon: ChartNoAxesCombined,
  },
  {
    path: '/team',
    element: <TeamPage />,
    pageTitle: 'Team',
    pageIcon: Users,
  },
  {
    path: '/pipelines',
    element: <PipelinesPage />,
    pageTitle: 'Pipelines',
    pageIcon: GitBranch,
  },
  {
    path: '/directory',
    element: <DirectoryPage />,
    pageTitle: 'Directory',
    pageIcon: BookOpen,
  },
  {
    path: '/settings',
    element: <SettingsPage />,
    pageTitle: 'Settings',
    pageIcon: Settings,
  },
]

// ============================================================================
// Component
// ============================================================================

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          {routes.map(({ path, element, pageTitle, pageIcon }) => (
            <Route
              key={path}
              path={path}
              element={
                <MainLayout pageTitle={pageTitle} pageIcon={pageIcon}>
                  {element}
                </MainLayout>
              }
            />
          ))}
          {/* Pipeline editor routes - these pages include their own MainLayout */}
          <Route path="/pipelines/new" element={<PipelineEditorPage />} />
          <Route path="/pipelines/:id" element={<PipelineEditorPage />} />
          <Route path="/pipelines/:id/edit" element={<PipelineEditorPage />} />
          {/* Legacy route redirects (Issue #39 - Navigation restructure) */}
          <Route path="/connectors" element={<Navigate to="/settings?tab=connectors" replace />} />
          <Route path="/config" element={<Navigate to="/settings?tab=config" replace />} />
          {/* Catch-all 404 route */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
