# Data Model: Frontend Type Definitions

**Feature**: 005-ui-migration
**Date**: 2026-01-01
**Status**: Design Complete

## Overview

This document defines the TypeScript type system for the Photo Admin frontend. Since this is a frontend-only migration, the data model consists of TypeScript interfaces that represent entities from the backend API, component props, and form schemas.

**Key Principle**: The backend data model (PostgreSQL schema) remains unchanged. These are client-side types that mirror backend entities and add frontend-specific types for components and forms.

---

## 1. Core Entity Types

### 1.1 Connector

Represents a remote storage connection configuration.

```typescript
// frontend/src/types/connector.ts

export type ConnectorType = 'S3' | 'GCS' | 'SMB'

export interface Connector {
  id: number
  name: string
  type: ConnectorType
  active: boolean
  credentials: ConnectorCredentials
  created_at: string
  updated_at: string
}

// Union type for type-specific credentials
export type ConnectorCredentials =
  | S3Credentials
  | GCSCredentials
  | SMBCredentials

export interface S3Credentials {
  access_key_id: string
  secret_access_key: string
  region: string
  bucket?: string
}

export interface GCSCredentials {
  service_account_json: string
  bucket?: string
}

export interface SMBCredentials {
  server: string
  share: string
  username: string
  password: string
  domain?: string
}

// API Response types
export interface ConnectorResponse {
  connectors: Connector[]
  total: number
}

export interface ConnectorTestResponse {
  success: boolean
  message: string
  details?: Record<string, unknown>
}

// Form types
export interface ConnectorFormData {
  name: string
  type: ConnectorType
  active: boolean
  credentials: Partial<ConnectorCredentials>
}

export interface ConnectorCreate extends Omit<Connector, 'id' | 'created_at' | 'updated_at'> {}
export interface ConnectorUpdate extends Partial<ConnectorCreate> {}
```

**Relationships**:
- A Collection (remote type) references a Connector via `connector_id`
- Credentials are polymorphic based on `ConnectorType`

**Validation Rules** (enforced in Zod schemas):
- `name`: Required, 1-255 characters
- `type`: Required, must be 'S3' | 'GCS' | 'SMB'
- `credentials`: Required, type-specific validation
  - S3: `access_key_id` (16-128 chars), `secret_access_key` (40+ chars), `region` (enum)
  - GCS: `service_account_json` (valid JSON object)
  - SMB: `server`, `share`, `username`, `password` (all required strings)

---

### 1.2 Collection

Represents a photo collection (local or remote).

```typescript
// frontend/src/types/collection.ts

export type CollectionType = 'LOCAL' | 'S3' | 'GCS' | 'SMB'
export type CollectionState = 'LIVE' | 'CLOSED' | 'ARCHIVED'

export interface Collection {
  id: number
  name: string
  type: CollectionType
  state: CollectionState
  location: string
  connector_id: number | null
  is_accessible: boolean
  accessibility_message: string | null
  cache_ttl: number | null
  created_at: string
  updated_at: string
  last_scanned_at: string | null
}

// API Response types
export interface CollectionResponse {
  collections: Collection[]
  total: number
}

export interface CollectionTestResponse {
  success: boolean
  is_accessible: boolean
  message: string
  details?: Record<string, unknown>
}

// Form types
export interface CollectionFormData {
  name: string
  type: CollectionType
  state: CollectionState
  location: string
  connector_id: number | null
  cache_ttl: number | null
}

export interface CollectionCreate extends Omit<Collection,
  'id' | 'is_accessible' | 'accessibility_message' | 'created_at' | 'updated_at' | 'last_scanned_at'
> {}

export interface CollectionUpdate extends Partial<CollectionCreate> {}

// Filter types
export interface CollectionFilters {
  state?: CollectionState | 'ALL'
  type?: CollectionType | 'ALL'
  accessible_only?: boolean
}
```

**Relationships**:
- Collection → Connector (optional, via `connector_id`)
- `connector_id` is `null` for LOCAL collections, required for remote types

**Validation Rules** (enforced in Zod schemas):
- `name`: Required, 1-255 characters
- `type`: Required, must be 'LOCAL' | 'S3' | 'GCS' | 'SMB'
- `state`: Required, must be 'LIVE' | 'CLOSED' | 'ARCHIVED'
- `location`: Required, 1-1024 characters
- `connector_id`: `null` for LOCAL, required (>= 1) for remote types
- `cache_ttl`: Optional, positive integer

**State Transitions**:
- LIVE ↔ CLOSED: User can toggle between active and inactive
- LIVE/CLOSED → ARCHIVED: User can archive
- ARCHIVED → LIVE: User can unarchive (reactivate)

---

## 2. Design System Types

### 2.1 Design Tokens

CSS variable definitions for the design system (not TypeScript, but documented for completeness).

```css
/* frontend/src/globals.css */

:root {
  /* Colors */
  --background: oklch(0.08 0 0);
  --foreground: oklch(0.97 0 0);
  --card: oklch(0.14 0 0);
  --primary: oklch(0.54 0.245 264);
  --secondary: oklch(0.26 0 0);
  --accent: oklch(0.54 0.245 264);
  --destructive: oklch(0.577 0.245 27.325);
  --border: oklch(0.22 0 0);
  --muted: oklch(0.35 0 0);
  --muted-foreground: oklch(0.6 0 0);

  /* Sidebar */
  --sidebar: oklch(0.12 0 0);
  --sidebar-foreground: oklch(0.97 0 0);
  --sidebar-primary: oklch(0.54 0.245 264);
  --sidebar-accent: oklch(0.26 0 0);
  --sidebar-border: oklch(0.22 0 0);

  /* Spacing */
  --radius: 0.5rem;
}
```

**Design Token Categories**:
- **Colors**: background, foreground, primary, secondary, accent, destructive, border, muted
- **Sidebar**: sidebar-specific color variants
- **Charts**: chart-1 through chart-5 for data visualization
- **Spacing**: radius values (sm, md, lg, xl)

---

### 2.2 Component Theme Types

```typescript
// frontend/src/types/theme.ts

export type ThemeColor =
  | 'default'
  | 'primary'
  | 'secondary'
  | 'destructive'
  | 'accent'
  | 'muted'

export type ThemeSize = 'sm' | 'md' | 'lg'

export type ButtonVariant =
  | 'default'
  | 'destructive'
  | 'outline'
  | 'secondary'
  | 'ghost'
  | 'link'

export type BadgeVariant =
  | 'default'
  | 'secondary'
  | 'destructive'
  | 'outline'

// Badge color mappings for collection types
export const collectionTypeBadgeVariant: Record<CollectionType, BadgeVariant> = {
  LOCAL: 'default',
  S3: 'secondary',
  GCS: 'secondary',
  SMB: 'secondary'
}

// Badge color mappings for collection states
export const collectionStateBadgeVariant: Record<CollectionState, BadgeVariant> = {
  LIVE: 'default',
  CLOSED: 'secondary',
  ARCHIVED: 'outline'
}
```

---

## 3. Component Prop Types

### 3.1 Layout Components

```typescript
// frontend/src/components/layout/Sidebar.tsx

export interface SidebarProps {
  activeItem?: string
  className?: string
}

export interface MenuItem {
  icon: LucideIcon
  label: string
  href: string
  active?: boolean
}

// frontend/src/components/layout/TopHeader.tsx

export interface TopHeaderProps {
  pageTitle: string
  pageIcon?: LucideIcon
  stats?: HeaderStat[]
  className?: string
}

export interface HeaderStat {
  label: string
  value: string | number
}

// frontend/src/components/layout/MainLayout.tsx

export interface MainLayoutProps {
  children: React.ReactNode
  pageTitle?: string
  pageIcon?: LucideIcon
}
```

---

### 3.2 Connector Components

```typescript
// frontend/src/components/connectors/ConnectorList.tsx

export interface ConnectorListProps {
  connectors: Connector[]
  loading: boolean
  onEdit: (connector: Connector) => void
  onDelete: (connector: Connector) => void
  onTest: (connector: Connector) => void
}

// frontend/src/components/connectors/ConnectorForm.tsx

export interface ConnectorFormProps {
  connector?: Connector  // undefined for create, defined for edit
  onSubmit: (data: ConnectorFormData) => Promise<void>
  onCancel: () => void
  loading?: boolean
  error?: string | null
}
```

---

### 3.3 Collection Components

```typescript
// frontend/src/components/collections/CollectionList.tsx

export interface CollectionListProps {
  collections: Collection[]
  loading: boolean
  onEdit: (collection: Collection) => void
  onDelete: (collection: Collection) => void
  onRefresh: (collection: Collection) => void
  onInfo: (collection: Collection) => void
}

// frontend/src/components/collections/CollectionForm.tsx

export interface CollectionFormProps {
  collection?: Collection
  connectors: Connector[]
  onSubmit: (data: CollectionFormData) => Promise<void>
  onCancel: () => void
  loading?: boolean
  error?: string | null
}

// frontend/src/components/collections/CollectionStatus.tsx

export interface CollectionStatusProps {
  collection: Collection
  className?: string
}

// frontend/src/components/collections/FiltersSection.tsx

export interface FiltersSectionProps {
  selectedState: CollectionState | 'ALL' | ''
  setSelectedState: (state: CollectionState | 'ALL' | '') => void
  selectedType: CollectionType | 'ALL' | ''
  setSelectedType: (type: CollectionType | 'ALL' | '') => void
  accessibleOnly: boolean
  setAccessibleOnly: (value: boolean) => void
}
```

---

## 4. Hook Types

### 4.1 useConnectors Hook

```typescript
// frontend/src/hooks/useConnectors.ts

export interface UseConnectorsReturn {
  connectors: Connector[]
  loading: boolean
  error: string | null
  fetchConnectors: () => Promise<void>
  createConnector: (data: ConnectorCreate) => Promise<Connector>
  updateConnector: (id: number, data: ConnectorUpdate) => Promise<Connector>
  deleteConnector: (id: number) => Promise<void>
  testConnector: (id: number) => Promise<ConnectorTestResponse>
}
```

---

### 4.2 useCollections Hook

```typescript
// frontend/src/hooks/useCollections.ts

export interface UseCollectionsReturn {
  collections: Collection[]
  loading: boolean
  error: string | null
  fetchCollections: (filters?: CollectionFilters) => Promise<void>
  createCollection: (data: CollectionCreate) => Promise<Collection>
  updateCollection: (id: number, data: CollectionUpdate) => Promise<Collection>
  deleteCollection: (id: number) => Promise<void>
  testCollection: (id: number) => Promise<CollectionTestResponse>
}
```

---

## 5. API Service Types

### 5.1 Generic API Types

```typescript
// frontend/src/types/api.ts

export interface ApiError {
  message: string
  code?: string
  details?: Record<string, unknown>
}

export interface PaginationParams {
  limit?: number
  offset?: number
}

export interface PaginationMeta {
  total: number
  limit: number
  offset: number
}
```

---

### 5.2 API Response Envelopes

```typescript
// Standard response wrapper (if backend uses this pattern)
export interface ApiResponse<T> {
  data: T
  meta?: PaginationMeta
  error?: ApiError
}

// Error response
export interface ApiErrorResponse {
  error: ApiError
}
```

---

## 6. Form Validation Schemas (Zod)

### 6.1 Connector Form Schema

```typescript
// frontend/src/types/schemas/connector.ts

import { z } from 'zod'

export const S3CredentialsSchema = z.object({
  access_key_id: z.string()
    .min(16, 'Access Key ID must be at least 16 characters')
    .max(128, 'Access Key ID must be at most 128 characters'),
  secret_access_key: z.string()
    .min(40, 'Secret Access Key must be at least 40 characters'),
  region: z.enum([
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'eu-west-1', 'eu-central-1', 'ap-southeast-1', 'ap-northeast-1'
  ]),
  bucket: z.string().optional()
})

export const GCSCredentialsSchema = z.object({
  service_account_json: z.string()
    .min(1, 'Service Account JSON is required')
    .refine(
      (val) => {
        try {
          JSON.parse(val)
          return true
        } catch {
          return false
        }
      },
      'Must be valid JSON'
    ),
  bucket: z.string().optional()
})

export const SMBCredentialsSchema = z.object({
  server: z.string().min(1, 'Server is required'),
  share: z.string().min(1, 'Share is required'),
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
  domain: z.string().optional()
})

export const ConnectorFormSchema = z.object({
  name: z.string()
    .min(1, 'Name is required')
    .max(255, 'Name must be at most 255 characters'),
  type: z.enum(['S3', 'GCS', 'SMB']),
  active: z.boolean(),
  credentials: z.union([
    S3CredentialsSchema,
    GCSCredentialsSchema,
    SMBCredentialsSchema
  ])
})

export type ConnectorFormSchema = z.infer<typeof ConnectorFormSchema>
```

---

### 6.2 Collection Form Schema

```typescript
// frontend/src/types/schemas/collection.ts

import { z } from 'zod'

export const CollectionFormSchema = z.object({
  name: z.string()
    .min(1, 'Name is required')
    .max(255, 'Name must be at most 255 characters'),
  type: z.enum(['LOCAL', 'S3', 'GCS', 'SMB']),
  state: z.enum(['LIVE', 'CLOSED', 'ARCHIVED']),
  location: z.string()
    .min(1, 'Location is required')
    .max(1024, 'Location must be at most 1024 characters'),
  connector_id: z.number().int().positive().nullable(),
  cache_ttl: z.number().int().positive().nullable()
}).refine(
  (data) => {
    // LOCAL collections must have connector_id = null
    if (data.type === 'LOCAL') {
      return data.connector_id === null
    }
    // Remote collections must have connector_id >= 1
    return data.connector_id !== null && data.connector_id >= 1
  },
  {
    message: 'LOCAL collections cannot have a connector, remote collections must have a connector',
    path: ['connector_id']
  }
)

export type CollectionFormSchema = z.infer<typeof CollectionFormSchema>
```

---

## 7. Utility Types

### 7.1 Class Name Utilities

```typescript
// frontend/src/lib/utils.ts

import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

**Purpose**: Combines multiple class names and resolves Tailwind conflicts.

**Example Usage**:
```typescript
<div className={cn(
  'px-4 py-2',
  isActive && 'bg-primary text-primary-foreground',
  className
)}>
```

---

### 7.2 Type Guards

```typescript
// frontend/src/types/guards.ts

export function isConnector(obj: unknown): obj is Connector {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'name' in obj &&
    'type' in obj
  )
}

export function isCollection(obj: unknown): obj is Collection {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'name' in obj &&
    'type' in obj &&
    'state' in obj
  )
}

export function isS3Credentials(creds: ConnectorCredentials): creds is S3Credentials {
  return 'access_key_id' in creds
}

export function isGCSCredentials(creds: ConnectorCredentials): creds is GCSCredentials {
  return 'service_account_json' in creds
}

export function isSMBCredentials(creds: ConnectorCredentials): creds is SMBCredentials {
  return 'server' in creds && 'share' in creds
}
```

---

## 8. Type Exports (Barrel File)

```typescript
// frontend/src/types/index.ts

// Core entities
export type {
  Connector,
  ConnectorType,
  ConnectorCredentials,
  S3Credentials,
  GCSCredentials,
  SMBCredentials,
  ConnectorResponse,
  ConnectorTestResponse,
  ConnectorFormData,
  ConnectorCreate,
  ConnectorUpdate
} from './connector'

export type {
  Collection,
  CollectionType,
  CollectionState,
  CollectionResponse,
  CollectionTestResponse,
  CollectionFormData,
  CollectionCreate,
  CollectionUpdate,
  CollectionFilters
} from './collection'

// API types
export type {
  ApiError,
  ApiResponse,
  ApiErrorResponse,
  PaginationParams,
  PaginationMeta
} from './api'

// Theme types
export type {
  ThemeColor,
  ThemeSize,
  ButtonVariant,
  BadgeVariant
} from './theme'

// Schemas
export {
  ConnectorFormSchema,
  S3CredentialsSchema,
  GCSCredentialsSchema,
  SMBCredentialsSchema
} from './schemas/connector'

export {
  CollectionFormSchema
} from './schemas/collection'

// Type guards
export {
  isConnector,
  isCollection,
  isS3Credentials,
  isGCSCredentials,
  isSMBCredentials
} from './guards'
```

---

## 9. Component Hierarchy

```text
App (MainLayout wrapper)
├── MainLayout
│   ├── Sidebar
│   │   └── MenuItem[] (navigation items)
│   ├── TopHeader
│   │   ├── PageTitle
│   │   ├── HeaderStat[] (metrics)
│   │   └── UserProfile
│   └── Content (children)
│       ├── ConnectorsPage
│       │   ├── PageHeader (title + button)
│       │   ├── ConnectorList
│       │   │   ├── Table (shadcn/ui)
│       │   │   ├── FilterControls
│       │   │   └── ActionButtons
│       │   └── Dialog (create/edit)
│       │       └── ConnectorForm
│       │           ├── TypeSelect
│       │           └── DynamicCredentialFields
│       └── CollectionsPage
│           ├── PageHeader (title + button)
│           ├── Tabs (All/Recent/Archived)
│           ├── FiltersSection
│           │   ├── StateSelect
│           │   ├── TypeSelect
│           │   └── AccessibleCheckbox
│           ├── CollectionList
│           │   ├── Table (shadcn/ui)
│           │   ├── CollectionStatus (badges)
│           │   └── ActionButtons
│           └── Dialog (create/edit)
│               └── CollectionForm
│                   ├── TypeSelect
│                   ├── StateSelect
│                   ├── ConnectorSelect (conditional)
│                   └── TestConnectionButton
```

---

## 10. Summary

**Total Type Definitions**:
- 2 core entities (Connector, Collection)
- 10+ component prop interfaces
- 2 hook return types
- 2 Zod validation schemas
- 5+ utility types
- Type guards and theme types

**Type Safety Coverage**:
- ✅ All API responses typed
- ✅ All component props typed
- ✅ All form submissions typed
- ✅ Runtime validation with Zod
- ✅ Type guards for polymorphic data

**Next Steps**: Generate contracts (Phase 1) with detailed component prop interfaces and API types.
