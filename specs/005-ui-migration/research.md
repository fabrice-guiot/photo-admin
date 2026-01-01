# Research: UI Migration Technology Stack

**Feature**: 005-ui-migration
**Date**: 2026-01-01
**Status**: Decisions Finalized

## Overview

This document consolidates the technical research and strategic decisions for migrating the Photo Admin frontend from Material-UI to a modern design system. Most decisions were made during the strategic evaluation documented in `/specs/004-remote-photos-persistence/ui-migration.md`. This research validates those decisions and resolves remaining implementation details.

## Key Decisions Summary

| Decision Area | Choice | Status |
|--------------|--------|--------|
| UI Component Library | shadcn/ui + Radix UI | ✅ Finalized |
| CSS Framework | Tailwind CSS v4 | ✅ Finalized |
| Form Management | react-hook-form + Zod | ✅ Finalized |
| Type System | TypeScript 5.x | ✅ Finalized |
| Icon Library | Lucide React | ✅ Finalized |
| Framework Migration | Hybrid (No Next.js) | ✅ Finalized |
| Migration Timing | NOW (post-Phase 3) | ✅ Finalized |

## Decision 1: UI Component Library

### Choice: shadcn/ui + Radix UI

**Rationale**:
1. **Copy-Paste Architecture**: Components are copied into the project rather than installed as dependencies, providing full control and customization
2. **Tailwind Integration**: Built specifically for Tailwind CSS, ensuring seamless styling
3. **Accessibility**: Built on Radix UI primitives which are fully accessible (WCAG compliant)
4. **Tree-Shakeable**: Only components actually used contribute to bundle size
5. **Modern Design**: Clean, professional aesthetic that matches design requirements
6. **Vite Compatible**: Verified compatibility with Vite build system

**Alternatives Considered**:
- **Material-UI (keep)**: Rejected - outdated design, large bundle size, CSS-in-JS performance issues
- **Chakra UI**: Rejected - still uses CSS-in-JS (Emotion), similar bundle size issues as MUI
- **Ant Design**: Rejected - opinionated Chinese design language, harder to customize
- **Mantine**: Considered - good Tailwind support, but shadcn/ui has better copy-paste model

**Implementation Notes**:
- Install via CLI: `npx shadcn@latest init`
- Components stored in `frontend/src/components/ui/`
- Configuration in `frontend/components.json`
- Choose "New York" style for modern aesthetic

**Validation**: ✅ Confirmed Vite compatibility in existing project testing

---

## Decision 2: CSS Framework

### Choice: Tailwind CSS v4

**Rationale**:
1. **Utility-First**: Rapid development with utility classes, reduces custom CSS
2. **Design Token System**: CSS variables provide consistent design system
3. **Better DX**: IntelliSense support, faster than CSS-in-JS
4. **Performance**: No runtime JavaScript overhead (unlike Emotion/styled-components)
5. **Modern Features**: v4 includes improved @apply, better color system, faster builds
6. **Dark Theme Support**: Native CSS variable system for theme switching

**Alternatives Considered**:
- **Emotion/CSS-in-JS (keep)**: Rejected - runtime overhead, harder to debug, slower builds
- **CSS Modules**: Rejected - more boilerplate than Tailwind utilities
- **Vanilla CSS**: Rejected - no design system, harder to maintain consistency
- **UnoCSS**: Considered - faster than Tailwind v3, but v4 closes the gap

**Implementation Notes**:
- Install: `npm install -D tailwindcss @tailwindcss/postcss autoprefixer`
- Config: `tailwind.config.js` with design tokens from ui-style-proposal
- PostCSS: `postcss.config.js` for build integration
- CSS file: `frontend/src/globals.css` with @tailwind directives

**Design Tokens** (from ui-style-proposal/app/globals.css):
```css
--background: oklch(0.08 0 0)
--foreground: oklch(0.97 0 0)
--primary: oklch(0.54 0.245 264)
--accent: oklch(0.54 0.245 264)
--border: oklch(0.22 0 0)
--sidebar: oklch(0.12 0 0)
```

**Validation**: ✅ Tailwind CSS v4 stable release available, production-ready

---

## Decision 3: Form Management

### Choice: react-hook-form + Zod

**Rationale**:
1. **Type Safety**: Zod schemas provide runtime validation + TypeScript types
2. **Performance**: react-hook-form minimizes re-renders, better than Formik
3. **Developer Experience**: Clean API, excellent TypeScript support
4. **Dynamic Forms**: Handles conditional fields (connector credentials based on type)
5. **React 18 Compatible**: Full support for concurrent features
6. **Bundle Size**: Smaller than alternatives (Formik, React Final Form)

**Alternatives Considered**:
- **Formik**: Rejected - heavier bundle, more re-renders, aging library
- **React Final Form**: Rejected - less active development, smaller community
- **Manual useState**: Rejected - too much boilerplate for validation logic
- **Built-in HTML5 validation**: Rejected - insufficient for complex validation rules

**Implementation Notes**:
- Install: `npm install react-hook-form zod @hookform/resolvers`
- Zod schemas define validation rules and TypeScript types
- Use shadcn/ui Form components with react-hook-form integration
- Dynamic field rendering based on form state

**Validation Patterns**:
```typescript
// Connector credentials schema (example)
const S3CredentialsSchema = z.object({
  access_key_id: z.string().min(16).max(128),
  secret_access_key: z.string().min(40),
  region: z.enum(['us-east-1', 'us-west-2', 'eu-west-1', ...])
})

// Form with react-hook-form
const form = useForm<ConnectorFormData>({
  resolver: zodResolver(ConnectorFormSchema)
})
```

**Validation**: ✅ Confirmed compatibility with shadcn/ui Form components

---

## Decision 4: TypeScript Migration Strategy

### Choice: Incremental TypeScript with Gradual Strictness

**Rationale**:
1. **Non-Blocking**: Allows development to continue while refining types
2. **Pragmatic**: Start with `any` where needed, refine types over time
3. **Safety**: Still catches most errors without strict mode initially
4. **Team Velocity**: Doesn't slow down migration with type gymnastics
5. **Progressive**: Can enable strict mode per-file as types mature

**Alternatives Considered**:
- **Strict TypeScript from start**: Rejected - too slow, blocks development
- **No TypeScript**: Rejected - misses major benefit of migration (type safety)
- **JSDoc types only**: Rejected - less robust, harder to maintain

**Implementation Strategy**:
1. **Phase 1**: Convert files to `.ts`/`.tsx`, use `any` for complex types
2. **Phase 2**: Define core entity types (Connector, Collection)
3. **Phase 3**: Define API response types
4. **Phase 4**: Define component prop types
5. **Phase 5**: Refine `any` types to specific types
6. **Future**: Enable strict mode incrementally

**tsconfig.json Configuration**:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": false,  // Start false, enable later
    "noUnusedLocals": false,  // Start false
    "noUnusedParameters": false,  // Start false
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Validation**: ✅ TypeScript 5.x supports all required features

---

## Decision 5: Icon Library

### Choice: Lucide React

**Rationale**:
1. **Modern Design**: Clean, consistent icon set
2. **React Components**: First-class React support with tree-shaking
3. **Lightweight**: Each icon is a separate component, small bundle impact
4. **Maintained**: Active development, frequent updates
5. **Consistency**: Used in shadcn/ui examples and documentation

**Alternatives Considered**:
- **Material Icons (keep)**: Rejected - tied to Material Design, larger bundle
- **Heroicons**: Considered - good alternative, but Lucide has better React integration
- **React Icons**: Rejected - umbrella package, larger bundle
- **Font Awesome**: Rejected - font-based (not SVG), accessibility issues

**Implementation Notes**:
- Install: `npm install lucide-react`
- Import icons individually: `import { Plus, Edit, Trash2 } from 'lucide-react'`
- Configure size/color via className: `<Plus className="w-5 h-5 text-primary" />`

**Icon Mapping** (from ui-style-proposal):
```typescript
// Sidebar navigation
LayoutGrid - Dashboard
Workflow - Workflows
FolderOpen - Collections (active)
Archive - Assets
BarChart3 - Analytics
Users - Team
Settings - Settings

// Actions
Plus - Create new
Edit - Edit item
Trash2 - Delete
RefreshCw - Refresh/Test
Info - Info/Details
Bell - Notifications
ChevronDown - Dropdown
```

**Validation**: ✅ Lucide icons used successfully in ui-style-proposal reference implementation

---

## Decision 6: Framework Migration Approach

### Choice: Hybrid Migration (React + Vite, NO Next.js)

**Rationale**:
1. **Faster Migration**: 3 weeks vs 6-8 weeks for full Next.js rewrite
2. **Lower Risk**: Keep familiar React patterns, reduce unknowns
3. **Immediate Value**: Get modern UI without framework complexity
4. **Progressive Enhancement**: Can migrate to Next.js later if SSR/SSG needed
5. **Team Velocity**: Less learning curve, focus on design system

**What We Keep**:
- React 18.3.1 (no framework change)
- Vite 6.0.5 (fast, familiar build tool)
- React Router DOM (existing routing)
- Axios (API layer)
- Vitest + React Testing Library (test infrastructure)

**What We Change**:
- Material-UI → shadcn/ui + Radix UI
- Emotion/CSS-in-JS → Tailwind CSS
- JavaScript → TypeScript

**Alternatives Considered**:
- **Full Next.js Migration**: Rejected - too complex, 2x longer timeline, unnecessary for current needs
- **Remix**: Rejected - smaller ecosystem, less familiar to team
- **Astro**: Rejected - not suitable for SPA-heavy applications
- **Keep Material-UI**: Rejected - defeats purpose of improving UX and DX

**Future Considerations**:
- Next.js migration could be Feature 006 if SSR/SSG becomes needed
- Current approach doesn't prevent future Next.js adoption
- Many companies run React + Vite in production successfully

**Validation**: ✅ Vite + shadcn/ui combination verified in multiple production apps

---

## Decision 7: Migration Timing

### Choice: Migrate NOW (after Phase 3, before Phases 4-7)

**Rationale**:
1. **Minimal Scope**: Only 11 components vs 25+ if we wait
2. **Maximum Benefit**: 64 future tasks inherit modern stack
3. **Best ROI**: 3-4x return on time investment (95h saves 185-255h)
4. **No User Disruption**: Not yet in production
5. **Team Learning**: Master tools with simple components first

**Impact Analysis** (from ui-migration.md):

| Scenario | Components | Effort | Future Benefit |
|----------|-----------|--------|----------------|
| NOW (✅) | 11 components | 95 hours | All Phase 4-7 tasks inherit |
| LATER (❌) | 25+ components | 280-350 hours | Migration blocks features 2+ months |

**Cost Avoidance**:
- Phases 4-7 would add 14+ components if implemented with MUI
- Migrating 25+ components: 280-350 hours
- Migrating NOW: 95 hours
- **Savings: 185-255 hours**

**Alternatives Considered**:
- **Migrate After Phase 4-7**: Rejected - 3-4x more work, team builds obsolete muscle memory
- **Never Migrate**: Rejected - UX feedback negative, technical debt accumulates
- **Incremental Migration**: Rejected - mixed UI libraries confuses users, harder to maintain

**Validation**: ✅ Strategic analysis documented in ui-migration.md confirms NOW is optimal

---

## Testing Strategy

### Approach: Component-by-Component Test Migration

**Strategy**:
1. Update test infrastructure first (Vitest config for TypeScript)
2. Migrate tests alongside component migration (not separate phase)
3. Update selectors for shadcn/ui components (Table, Dialog, Select, etc.)
4. Maintain >75% coverage throughout migration
5. Use MSW (Mock Service Worker) for API mocking (unchanged)

**Test Updates Required**:

| Test Type | Changes Needed | Effort |
|-----------|---------------|--------|
| Component tests | Update selectors, shadcn APIs | 3-4h per component |
| Hook tests | Add TypeScript types | 2h total |
| Integration tests | Update selectors, new layout | 4h total |
| Test infrastructure | TypeScript config, utilities | 3h |

**Test Utilities**:
```typescript
// Custom render with providers (unchanged pattern)
function render(ui: ReactElement) {
  return {
    ...rtlRender(ui, { wrapper: AllProviders }),
    ...screen
  }
}

// Helper for shadcn Select interactions
async function selectOption(label: string, option: string) {
  const select = screen.getByLabelText(label)
  await userEvent.click(select)
  await userEvent.click(screen.getByRole('option', { name: option }))
}
```

**Validation**: ✅ Vitest supports TypeScript natively, React Testing Library APIs unchanged

---

## Browser Compatibility

### Target: Modern Browsers (Last 2 Versions)

**Supported Browsers**:
- Chrome 120+ (Dec 2023)
- Firefox 121+ (Dec 2023)
- Safari 17+ (Sep 2023)
- Edge 120+ (Dec 2023)

**Required Features**:
- ✅ CSS Variables (--var): Supported all modern browsers
- ✅ CSS Grid/Flexbox: Supported all modern browsers
- ✅ ES2020 JavaScript: Supported all modern browsers
- ✅ CSS oklch() colors: Supported Safari 15+, Chrome 111+, Firefox 113+

**Polyfills**: None required for target browsers

**Testing Strategy**:
- Primary development: Chrome
- CI testing: Chrome headless
- Manual testing: Firefox, Safari, Edge
- BrowserStack for additional verification (optional)

**Validation**: ✅ All required CSS features supported in target browsers

---

## Performance Benchmarks

### Bundle Size Analysis

**Current (Material-UI)**:
- Total bundle: ~800KB (raw), ~250KB (gzipped)
- Material-UI: ~500KB (raw)
- Emotion: ~100KB (raw)

**Target (shadcn/ui + Tailwind)**:
- Total bundle: ~300KB (raw), ~90KB (gzipped)
- shadcn/ui: ~50KB (only used components)
- Tailwind: ~10KB (purged)
- **Savings: ~500KB raw, ~160KB gzipped**

**First Contentful Paint**:
- Current: ~2.0s (local dev)
- Target: <1.5s (goal)
- Improvement: ~25% faster

**Validation**: ✅ Expected improvements based on bundle analysis

---

## Risk Assessment

### Technical Risks

**1. Component API Differences**
- **Risk**: shadcn/ui components have different APIs than Material-UI
- **Mitigation**: Gradual migration, comprehensive testing, refer to ui-style-proposal examples
- **Status**: LOW (most components have similar patterns)

**2. TypeScript Migration Complexity**
- **Risk**: Type errors block development
- **Mitigation**: Incremental approach, allow `any` initially
- **Status**: LOW (flexible typing strategy)

**3. Test Update Effort**
- **Risk**: Test updates take longer than estimated
- **Mitigation**: Buffer time in estimates, parallel test/component migration
- **Status**: MEDIUM (11 test files to update)

**4. Browser Compatibility**
- **Risk**: CSS variables don't work in older browsers
- **Mitigation**: Target modern browsers only, document requirements
- **Status**: LOW (all features supported in target browsers)

### Schedule Risks

**1. Learning Curve**
- **Risk**: Team unfamiliar with Tailwind/shadcn/TypeScript
- **Mitigation**: Pair programming, reference ui-style-proposal, start with simple components
- **Status**: MEDIUM (new tools for team)

**2. Scope Creep**
- **Risk**: Temptation to add features during migration
- **Mitigation**: Strict "migration only" rule, defer enhancements
- **Status**: LOW (clear scope boundaries)

---

## Conclusion

All major technical decisions are finalized and validated:

✅ **UI Library**: shadcn/ui + Radix UI (Vite compatible, accessible, modern)
✅ **CSS**: Tailwind CSS v4 (performant, design system, production-ready)
✅ **Forms**: react-hook-form + Zod (type-safe, performant, React 18 compatible)
✅ **Types**: TypeScript 5.x incremental migration (pragmatic, non-blocking)
✅ **Icons**: Lucide React (modern, tree-shakeable, consistent)
✅ **Approach**: Hybrid migration (faster, lower risk, immediate value)
✅ **Timing**: NOW (minimal scope, maximum future benefit)

**Next Steps**: Proceed to Phase 1 (Design & Contracts) - generate data-model.md, contracts, and quickstart.md.

**Ready for Implementation**: All research complete, no blocking unknowns.
