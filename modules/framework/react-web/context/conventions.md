# React Web: Coding Conventions

## TypeScript
- Use TypeScript for all new files. Avoid `any` — use `unknown` when the type is genuinely unknown, then narrow it.
- Type component props with an `interface` (not `type` alias) when the props are a plain object. Use `type` for unions, intersections, and mapped types.
- Never assert with `as` to silence a type error — fix the underlying type instead.
- Prefer explicit return types on hooks and utility functions; let TypeScript infer them on simple components.

```tsx
// Good
interface UserCardProps {
  user: User;
  onSelect: (id: string) => void;
}

export function UserCard({ user, onSelect }: UserCardProps) { ... }
```

## Naming
| Entity | Convention | Example |
|--------|-----------|---------|
| Components | `PascalCase` | `UserCard`, `LoginForm` |
| Hooks | `camelCase` with `use` prefix | `useAuth`, `useUserList` |
| Context | `PascalCase` + `Context` suffix | `ThemeContext`, `AuthContext` |
| Redux slices | `camelCase` + `Slice` suffix | `authSlice`, `counterSlice` |
| Files (components) | `PascalCase.tsx` | `UserCard.tsx` |
| Files (hooks/utils) | `camelCase.ts` | `useAuth.ts`, `formatDate.ts` |
| Files (tests) | `<subject>.test.tsx` | `UserCard.test.tsx` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| Event handlers | `handle` prefix | `handleSubmit`, `handleClose` |
| Boolean props/vars | `is`/`has`/`can` prefix | `isLoading`, `hasError`, `canEdit` |

## Imports
Order imports in four groups separated by blank lines:
1. React and React-ecosystem (`react`, `react-dom`, `react-router-dom`)
2. Third-party libraries (alphabetical)
3. Internal absolute imports (`@/components/...`, `@/hooks/...`)
4. Relative local imports (`./`, `../`)

```tsx
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import { format } from 'date-fns';
import { z } from 'zod';

import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';

import { UserCard } from './UserCard';
```

## Component Structure
Order the contents of a component file as follows:
1. Imports
2. Types / interfaces
3. Constants (module-scoped)
4. Component function (exported)
5. Helper functions used only by this component (non-exported)
6. Styles (if co-located CSS modules or styled-components)

## Props
- Destructure props in the function signature, not inside the body.
- Use default parameter values instead of `||` fallbacks inside the component.
- Never spread all props onto a DOM element (`<div {...props}>`) — it leaks unknown attributes to the DOM.

```tsx
// Good
function Badge({ label, variant = 'default', className }: BadgeProps) { ... }

// Bad
function Badge(props: BadgeProps) {
  const label = props.label || 'N/A'; // use default params instead
}
```

## Event Handlers
- Name handlers `handle<Event>` when defined inside the component, `on<Event>` when passed as a prop.
- Avoid inline arrow functions on JSX props for handlers with non-trivial logic — extract them for readability.

## Linting & Formatting
- Use **ESLint** with `eslint-plugin-react`, `eslint-plugin-react-hooks`, and `eslint-plugin-jsx-a11y`.
- Use **Prettier** for formatting (configure via `.prettierrc`).
- Enable the `react-hooks/exhaustive-deps` rule — never disable it without a comment explaining why.
- Run `tsc --noEmit` in CI to catch type errors separately from lint.
