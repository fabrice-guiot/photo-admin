/**
 * Team Page
 *
 * Manage team members and access permissions
 */

import { Users } from 'lucide-react'

export default function TeamPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <Users className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-semibold text-foreground mb-2">
          Team
        </h2>
        <p className="text-muted-foreground max-w-md">
          Team management coming soon. This will allow you to invite team members,
          manage roles, and configure access permissions.
        </p>
      </div>
    </div>
  )
}
