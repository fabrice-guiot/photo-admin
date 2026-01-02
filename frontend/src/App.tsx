/**
 * Photo Admin Application
 *
 * Main application component with routing and layout
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { FolderOpen, Plug } from 'lucide-react'
import { MainLayout } from './components/layout/MainLayout'

// Page components
import ConnectorsPage from './pages/ConnectorsPage'
import CollectionsPage from './pages/CollectionsPage'

// ============================================================================
// Route Configuration
// ============================================================================

interface RouteConfig {
  path: string
  element: JSX.Element
  pageTitle: string
  pageIcon?: typeof FolderOpen
  stats?: { label: string; value: string | number }[]
}

const routes: RouteConfig[] = [
  {
    path: '/',
    element: <CollectionsPage />,
    pageTitle: 'Collections',
    pageIcon: FolderOpen,
    stats: [
      { label: 'Total Collections', value: '12' },
      { label: 'Storage Used', value: '2.4 TB' },
    ],
  },
  {
    path: '/collections',
    element: <CollectionsPage />,
    pageTitle: 'Collections',
    pageIcon: FolderOpen,
    stats: [
      { label: 'Total Collections', value: '12' },
      { label: 'Storage Used', value: '2.4 TB' },
    ],
  },
  {
    path: '/connectors',
    element: <ConnectorsPage />,
    pageTitle: 'Connectors',
    pageIcon: Plug,
    stats: [
      { label: 'Active Connectors', value: '3' },
      { label: 'Total Connectors', value: '5' },
    ],
  },
]

// ============================================================================
// Component
// ============================================================================

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {routes.map(({ path, element, pageTitle, pageIcon, stats }) => (
          <Route
            key={path}
            path={path}
            element={
              <MainLayout pageTitle={pageTitle} pageIcon={pageIcon} stats={stats}>
                {element}
              </MainLayout>
            }
          />
        ))}
      </Routes>
    </BrowserRouter>
  )
}

export default App
