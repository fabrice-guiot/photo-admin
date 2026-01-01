# Developer Quickstart: UI Migration

**Feature**: 005-ui-migration
**Date**: 2026-01-01
**Audience**: Frontend developers working on the migration

## Overview

This guide helps developers get started with the UI migration from Material-UI to shadcn/ui + Tailwind CSS + TypeScript. Follow these steps to set up your development environment and understand the new tech stack.

---

## Prerequisites

### Required Software

- **Node.js**: v18.x or later (LTS recommended)
- **npm**: v9.x or later (comes with Node.js)
- **Git**: For version control
- **Code Editor**: VS Code recommended (for IntelliSense features)

### Recommended VS Code Extensions

1. **Tailwind CSS IntelliSense** (bradlc.vscode-tailwindcss)
   - Autocomplete for Tailwind classes
   - Syntax highlighting
   - Linting

2. **TypeScript and JavaScript Language Features** (Built-in)
   - Type checking
   - Code navigation
   - Refactoring

3. **ESLint** (dbaeumer.vscode-eslint)
   - Code quality checks

4. **Prettier** (esbenp.prettier-vscode)
   - Code formatting

5. **Path Intellisense** (christian-kohler.path-intellisense)
   - Autocomplete for file paths

---

## Initial Setup

### 1. Clone and Checkout Branch

```bash
# If not already on branch
git checkout 005-ui-migration

# Pull latest changes
git pull origin 005-ui-migration
```

### 2. Install Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install all dependencies (including new ones for migration)
npm install

# Expected new dependencies:
# - @radix-ui/* (shadcn/ui primitives)
# - tailwindcss
# - @tailwindcss/postcss
# - autoprefixer
# - typescript
# - @types/react
# - @types/react-dom
# - react-hook-form
# - @hookform/resolvers
# - zod
# - lucide-react
# - clsx
# - tailwind-merge
```

### 3. Verify Installation

```bash
# Check TypeScript compiler
npx tsc --version
# Expected: Version 5.x

# Check Tailwind CSS
npx tailwindcss --help
# Should show Tailwind CLI help

# Verify build works
npm run build
# Should complete without errors
```

---

## Development Workflow

### Running the Development Server

```bash
# From frontend directory
npm run dev

# Server starts on http://localhost:5173 (Vite default)
# Hot reload enabled - changes reflect immediately
```

### Type Checking

TypeScript compilation happens automatically during development, but you can run explicit checks:

```bash
# Type check all files
npm run type-check

# Watch mode (continuous type checking)
npm run type-check -- --watch
```

**Note**: Type errors won't block the dev server (incremental migration strategy), but fix them before committing.

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- src/components/connectors/ConnectorList.test.tsx
```

### Linting and Formatting

```bash
# Run ESLint
npm run lint

# Auto-fix lint issues
npm run lint -- --fix

# Format code with Prettier (if configured)
npm run format
```

---

## Understanding the New Stack

### 1. Tailwind CSS

**What it is**: Utility-first CSS framework

**How to use**:
```tsx
// Instead of CSS classes or styled-components:
<div className="bg-background text-foreground p-4 rounded-lg border border-border">
  <h1 className="text-2xl font-semibold mb-4">Title</h1>
  <p className="text-muted-foreground">Description</p>
</div>
```

**Key concepts**:
- `bg-*`: Background colors
- `text-*`: Text colors
- `p-*`, `m-*`: Padding/margin (4px scale: p-4 = 16px)
- `flex`, `grid`: Layout
- `hover:*`, `focus:*`: State variants

**Design tokens** (defined in `globals.css`):
- Colors: `bg-background`, `bg-card`, `bg-primary`, `text-foreground`, `text-muted-foreground`
- Borders: `border-border`, `rounded-lg`
- Use tokens, not arbitrary colors (e.g., `bg-primary` not `bg-blue-500`)

**IntelliSense**: Type `className="` and get autocomplete suggestions

### 2. shadcn/ui Components

**What it is**: Copy-paste component library built on Radix UI

**How to add components**:
```bash
# Add a new component (copies code to src/components/ui/)
npx shadcn@latest add button
npx shadcn@latest add table
npx shadcn@latest add dialog

# List available components
npx shadcn@latest add
```

**How to use**:
```tsx
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'

function MyComponent() {
  return (
    <Dialog>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Connector</DialogTitle>
        </DialogHeader>
        <Button variant="default">Save</Button>
      </DialogContent>
    </Dialog>
  )
}
```

**Key components**:
- `Button`: Primary actions
- `Table`: Data tables
- `Dialog`: Modals
- `Select`: Dropdowns
- `Input`, `Textarea`: Form fields
- `Badge`: Status indicators
- `Checkbox`: Boolean inputs

**Documentation**: https://ui.shadcn.com/docs/components

### 3. TypeScript

**What it is**: Typed superset of JavaScript

**File extensions**:
- `.ts` for TypeScript files
- `.tsx` for TypeScript + JSX (React components)

**Basic types**:
```typescript
// Import types
import type { Connector, ConnectorFormData } from '@/types/connector'

// Type component props
interface MyComponentProps {
  connector: Connector
  onSubmit: (data: ConnectorFormData) => Promise<void>
}

function MyComponent({ connector, onSubmit }: MyComponentProps) {
  // TypeScript knows connector has id, name, type, etc.
  return <div>{connector.name}</div>
}

// Type state
const [loading, setLoading] = useState<boolean>(false)
const [connector, setConnector] = useState<Connector | null>(null)
```

**Path aliases**:
```typescript
// Use @ instead of relative paths
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import type { Connector } from '@/types/connector'

// NOT this:
// import { cn } from '../../lib/utils'
```

**Gradual typing**: You can use `any` when stuck, but try to add types:
```typescript
// OK during migration (but fix later)
const handleSubmit = (data: any) => { ... }

// Better
const handleSubmit = (data: ConnectorFormData) => { ... }
```

### 4. react-hook-form + Zod

**What it is**: Form library with type-safe validation

**How to use**:
```tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { ConnectorFormSchema, type ConnectorFormData } from '@/types/schemas/connector'
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form'

function ConnectorForm() {
  const form = useForm<ConnectorFormData>({
    resolver: zodResolver(ConnectorFormSchema),
    defaultValues: {
      name: '',
      type: 'S3',
      active: true,
      credentials: {}
    }
  })

  const onSubmit = async (data: ConnectorFormData) => {
    // data is fully typed and validated
    await createConnector(data)
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit">Save</Button>
      </form>
    </Form>
  )
}
```

**Key points**:
- `useForm()`: Initialize form with schema
- `FormField`: Individual field with validation
- `form.handleSubmit()`: Validates before calling onSubmit
- Zod schemas define both validation rules AND TypeScript types

### 5. Lucide Icons

**What it is**: SVG icon library

**How to use**:
```tsx
import { Plus, Edit, Trash2, RefreshCw } from 'lucide-react'

function MyComponent() {
  return (
    <Button>
      <Plus className="w-4 h-4 mr-2" />
      Create New
    </Button>
  )
}
```

**Common icons**:
- `Plus`: Create actions
- `Edit`: Edit actions
- `Trash2`: Delete actions
- `RefreshCw`: Refresh/test
- `Info`: Information
- `ChevronDown`: Dropdowns
- `X`: Close

**Documentation**: https://lucide.dev

---

## Project Structure

```text
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn/ui components (auto-generated)
│   │   ├── layout/          # NEW - Sidebar, TopHeader, MainLayout
│   │   ├── connectors/      # Connector components
│   │   └── collections/     # Collection components
│   ├── pages/               # Page components
│   ├── hooks/               # Custom hooks (useConnectors, useCollections)
│   ├── services/            # API services (axios)
│   ├── types/               # NEW - TypeScript type definitions
│   │   ├── connector.ts
│   │   ├── collection.ts
│   │   ├── api.ts
│   │   └── index.ts
│   ├── lib/                 # NEW - Utility functions
│   │   └── utils.ts         # cn() helper
│   ├── App.tsx              # Root component
│   ├── main.tsx             # Entry point
│   └── globals.css          # NEW - Tailwind + design tokens
├── tests/                   # Test files
├── tailwind.config.js       # NEW - Tailwind configuration
├── postcss.config.js        # NEW - PostCSS configuration
├── tsconfig.json            # NEW - TypeScript configuration
├── vite.config.ts           # Vite configuration (TypeScript)
└── package.json             # Dependencies
```

---

## Common Tasks

### Adding a New shadcn/ui Component

```bash
# Example: Add a Tooltip component
npx shadcn@latest add tooltip

# Component is now in src/components/ui/tooltip.tsx
# Import and use:
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
```

### Creating a New Component

```tsx
// src/components/example/MyComponent.tsx
import { cn } from '@/lib/utils'

interface MyComponentProps {
  title: string
  className?: string
}

export function MyComponent({ title, className }: MyComponentProps) {
  return (
    <div className={cn('p-4 bg-card rounded-lg', className)}>
      <h2 className="text-xl font-semibold">{title}</h2>
    </div>
  )
}
```

### Defining New Types

```typescript
// src/types/myentity.ts
export interface MyEntity {
  id: number
  name: string
  created_at: string
}

export interface MyEntityFormData {
  name: string
}

// Export from barrel file
// src/types/index.ts
export type { MyEntity, MyEntityFormData } from './myentity'
```

### Creating a Validation Schema

```typescript
// src/types/schemas/myentity.ts
import { z } from 'zod'

export const MyEntityFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255)
})

export type MyEntityFormData = z.infer<typeof MyEntityFormSchema>
```

---

## Debugging Tips

### TypeScript Errors

```bash
# See all type errors
npm run type-check

# VS Code: Hover over red squiggles to see error
# Use CMD+. (Mac) or CTRL+. (Windows) for quick fixes
```

**Common fixes**:
- Missing type import: `import type { Connector } from '@/types/connector'`
- Wrong prop type: Check component interface
- `any` type: Use specific type or accept `any` temporarily

### Tailwind Classes Not Working

1. Check `tailwind.config.js` includes all content paths
2. Restart dev server (`npm run dev`)
3. Check for typos in class names (IntelliSense helps)
4. Use browser DevTools to inspect element (classes should be applied)

### Hot Reload Issues

```bash
# Restart dev server
# Press CTRL+C to stop
npm run dev
```

### Test Failures

```bash
# Run tests in watch mode to see failures immediately
npm run test:watch

# Check test file for updated component selectors
# Old: screen.getByRole('button', { name: /create/i })
# New: screen.getByRole('button', { name: /NEW CONNECTOR/i })
```

---

## Resources

### Official Documentation

- **Tailwind CSS**: https://tailwindcss.com/docs
- **shadcn/ui**: https://ui.shadcn.com/docs
- **TypeScript**: https://www.typescriptlang.org/docs
- **react-hook-form**: https://react-hook-form.com/get-started
- **Zod**: https://zod.dev
- **Lucide Icons**: https://lucide.dev

### Internal Documentation

- **Feature Spec**: `/specs/005-ui-migration/spec.md`
- **Migration Plan**: `/specs/004-remote-photos-persistence/ui-migration.md`
- **Data Model**: `/specs/005-ui-migration/data-model.md`
- **Contracts**: `/specs/005-ui-migration/contracts/`

### Getting Help

1. Check the migration plan for detailed task breakdown
2. Review ui-style-proposal for reference implementation
3. Ask team members familiar with the stack
4. Search shadcn/ui docs for component examples

---

## Next Steps

Once you're set up, you can:

1. Review the migration plan (`/specs/004-remote-photos-persistence/ui-migration.md`)
2. Look at the ui-style-proposal reference implementation
3. Start with Phase 0 tasks (Setup & Infrastructure)
4. Work through phases sequentially (recommended) or pick specific tasks

**Happy coding!** 🚀
