# Quickstart: UX Polish Epic

**Branch**: `006-ux-polish`
**Created**: 2026-01-03

## Overview

This guide provides a quick reference for implementing the three features in the UX Polish Epic.

---

## Prerequisites

- Python 3.10+ with FastAPI backend running
- Node.js 18+ with React frontend running
- PostgreSQL database with existing collections/connectors tables
- Development environment set up per existing project docs

---

## Feature 1: Topband KPIs (Issue #37)

### Backend Tasks

1. **Add schema migration** for new Collection columns:
   ```bash
   # Create migration
   alembic revision --autogenerate -m "Add collection stats columns"

   # Run migration
   alembic upgrade head
   ```

2. **Update Collection model** (`backend/src/models/collection.py`):
   ```python
   storage_bytes = Column(BigInteger, nullable=True)
   file_count = Column(Integer, nullable=True)
   image_count = Column(Integer, nullable=True)
   ```

3. **Add stats endpoint** to `backend/src/api/collections.py`:
   ```python
   @router.get("/stats", response_model=CollectionStatsResponse)
   async def get_collection_stats(...):
       # Aggregate query implementation
   ```

4. **Add stats endpoint** to `backend/src/api/connectors.py`:
   ```python
   @router.get("/stats", response_model=ConnectorStatsResponse)
   async def get_connector_stats(...):
       # COUNT with is_active filter
   ```

### Frontend Tasks

1. **Create KPI card component** (`frontend/src/components/ui/kpi-card.tsx`)

2. **Add stats hooks**:
   - `useCollectionStats()` - fetches `/api/collections/stats`
   - `useConnectorStats()` - fetches `/api/connectors/stats`

3. **Integrate into pages**:
   - `CollectionsPage.tsx` - add KPI grid above list
   - `ConnectorsPage.tsx` - add KPI grid above list

---

## Feature 2: Collection Search (Issue #38)

### Backend Tasks

1. **Add search parameter** to `list_collections()` in `collection_service.py`:
   ```python
   def list_collections(
       self,
       search: Optional[str] = None,  # NEW
       ...
   ):
       if search:
           query = query.filter(Collection.name.ilike(f"%{search}%"))
   ```

2. **Expose search parameter** in API endpoint:
   ```python
   @router.get("")
   async def list_collections(
       search: Optional[str] = Query(None, max_length=100),
       ...
   ):
   ```

### Frontend Tasks

1. **Add search input** to `CollectionList.tsx`:
   ```tsx
   <Input
     placeholder="Search collections..."
     value={searchTerm}
     onChange={(e) => setSearchTerm(e.target.value)}
   />
   ```

2. **Add debounced search** to `useCollections` hook:
   ```typescript
   const [searchTerm, setSearchTerm] = useState('')
   const debouncedSearch = useDebouncedValue(searchTerm, 300)

   useEffect(() => {
     fetchCollections({ search: debouncedSearch })
   }, [debouncedSearch])
   ```

---

## Feature 3: Responsive Menu Collapse (Issue #41)

### Frontend Tasks

1. **Create collapse hook** (`frontend/src/hooks/useSidebarCollapse.ts`):
   ```typescript
   export function useSidebarCollapse() {
     const [isCollapsed, setIsCollapsed] = useLocalStorage('sidebar-collapsed', false)

     return {
       isCollapsed,
       toggleCollapse: () => setIsCollapsed(!isCollapsed),
       expand: () => setIsCollapsed(false),
       collapse: () => setIsCollapsed(true),
     }
   }
   ```

2. **Add collapse control** to `Sidebar.tsx`:
   - Position arrow button on right edge of sidebar
   - Show only when screen width > 768px (md breakpoint)
   - Add Pin button to hamburger menu header

3. **Update MainLayout.tsx** to use collapse state:
   ```tsx
   const { isCollapsed, toggleCollapse, expand } = useSidebarCollapse()

   <Sidebar
     isManuallyCollapsed={isCollapsed}
     onCollapseChange={toggleCollapse}
     onPinSidebar={expand}
   />
   ```

---

## Testing Checklist

### Backend Tests

- [ ] Collection stats endpoint returns correct aggregations
- [ ] Connector stats endpoint returns correct counts
- [ ] Search parameter filters by name (case-insensitive)
- [ ] Search works with other filters (state, type, accessible_only)
- [ ] Search handles special characters safely
- [ ] Empty search returns all collections

### Frontend Tests

- [ ] KPI cards display correct values
- [ ] KPI cards show loading state
- [ ] Search input debounces correctly (300ms)
- [ ] Search clears when input is empty
- [ ] Collapse button visible only above mobile breakpoint
- [ ] Collapse state persists across page navigation
- [ ] Collapse state persists across browser refresh
- [ ] Pin button restores expanded state

---

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/collections/stats` | GET | Collection KPI statistics |
| `/api/connectors/stats` | GET | Connector KPI statistics |
| `/api/collections?search=...` | GET | List with name search filter |

---

## File Changes Summary

### Backend (Modified)
- `backend/src/models/collection.py` - Add stats columns
- `backend/src/api/collections.py` - Add stats endpoint, search param
- `backend/src/api/connectors.py` - Add stats endpoint
- `backend/src/services/collection_service.py` - Add search logic
- `backend/src/schemas/collection.py` - Add stats response schemas

### Frontend (Modified)
- `frontend/src/components/layout/Sidebar.tsx` - Add collapse control
- `frontend/src/components/layout/MainLayout.tsx` - Add collapse state
- `frontend/src/components/collections/CollectionList.tsx` - Add search input
- `frontend/src/pages/CollectionsPage.tsx` - Add KPIs
- `frontend/src/pages/ConnectorsPage.tsx` - Add KPIs
- `frontend/src/hooks/useCollections.ts` - Add search, stats
- `frontend/src/hooks/useConnectors.ts` - Add stats

### Frontend (New)
- `frontend/src/components/ui/kpi-card.tsx` - KPI card component
- `frontend/src/hooks/useSidebarCollapse.ts` - Collapse state hook
