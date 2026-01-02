/**
 * Photo Admin Application
 *
 * Main application component with routing and layout
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { FolderOpen, Database } from 'lucide-react'
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
}

const routes: RouteConfig[] = [
  {
    path: '/',
    element: <CollectionsPage />,
    pageTitle: 'Collections',
    pageIcon: FolderOpen,
  },
  {
    path: '/collections',
    element: <CollectionsPage />,
    pageTitle: 'Collections',
    pageIcon: FolderOpen,
  },
  {
    path: '/connectors',
    element: <ConnectorsPage />,
    pageTitle: 'Connectors',
    pageIcon: Database,
  },
]

// ============================================================================
// Component
// ============================================================================

function App() {
  return (
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
      </Routes>
    </BrowserRouter>
  )
}

export default App
