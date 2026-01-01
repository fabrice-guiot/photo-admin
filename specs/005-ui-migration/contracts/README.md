# Frontend Contracts

This directory contains TypeScript interface definitions (contracts) for the UI migration feature.

## Structure

```text
contracts/
├── components/     # Component prop interfaces
├── api/            # API request/response types
└── forms/          # Form validation schemas
```

## Purpose

These contracts define the "shape" of data expected by components, APIs, and forms. They serve as:

1. **Component API Documentation**: Clear prop definitions for each component
2. **Type Safety**: Compile-time checks for correct data usage
3. **Integration Points**: Contracts between frontend components and backend APIs
4. **Validation Rules**: Form schemas that enforce data integrity

## Usage

These types will be implemented in the actual source code at:
- `frontend/src/types/` - Type definitions
- `frontend/src/components/` - Component implementations

## Contract Stability

These contracts are **stable** and should not change during implementation unless:
1. The backend API contract changes (requires backend coordination)
2. A design flaw is discovered (requires spec update)
3. A new requirement is added (requires feature change request)

## Relationship to Backend

The backend API contracts are unchanged in this migration. These frontend contracts **mirror** the existing backend API while adding frontend-specific types (component props, form state, etc.).
