/**
 * Settings Page
 *
 * Configure application settings, connectors, and tool configuration.
 * Uses URL-synchronized tabs for deep linking.
 *
 * Issue #39 - Calendar Events feature navigation restructure.
 */

import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Settings, Plug, Cog } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ConnectorsTab } from '@/components/settings/ConnectorsTab'
import { ConfigTab } from '@/components/settings/ConfigTab'

// Tab configuration
const TABS = [
  {
    id: 'connectors',
    label: 'Connectors',
    icon: Plug,
  },
  {
    id: 'config',
    label: 'Configuration',
    icon: Cog,
  },
] as const

type TabId = typeof TABS[number]['id']

const DEFAULT_TAB: TabId = 'connectors'

export default function SettingsPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  // Get current tab from URL, default to 'connectors'
  const currentTab = (searchParams.get('tab') as TabId) || DEFAULT_TAB

  // Validate tab exists
  const validTab = TABS.some(t => t.id === currentTab) ? currentTab : DEFAULT_TAB

  // Sync URL with tab state
  const handleTabChange = (value: string) => {
    setSearchParams({ tab: value }, { replace: true })
  }

  // Set default tab in URL if not present
  useEffect(() => {
    if (!searchParams.has('tab')) {
      setSearchParams({ tab: DEFAULT_TAB }, { replace: true })
    }
  }, [searchParams, setSearchParams])

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex items-center gap-3">
        <Settings className="h-8 w-8" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">
            Configure connectors, tools, and application preferences
          </p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={validTab} onValueChange={handleTabChange} className="w-full">
        <TabsList>
          {TABS.map(tab => {
            const Icon = tab.icon
            return (
              <TabsTrigger key={tab.id} value={tab.id} className="gap-2">
                <Icon className="h-4 w-4" />
                {tab.label}
              </TabsTrigger>
            )
          })}
        </TabsList>

        <TabsContent value="connectors" className="mt-6">
          <ConnectorsTab />
        </TabsContent>

        <TabsContent value="config" className="mt-6">
          <ConfigTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
