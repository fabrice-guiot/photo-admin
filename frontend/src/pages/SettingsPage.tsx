/**
 * Settings Page
 *
 * Configure application settings and preferences
 */

import { Settings } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <Settings className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-semibold text-foreground mb-2">
          Settings
        </h2>
        <p className="text-muted-foreground max-w-md">
          Settings panel coming soon. This will allow you to configure application
          preferences, notifications, and system settings.
        </p>
      </div>
    </div>
  )
}
