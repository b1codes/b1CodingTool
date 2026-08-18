# React Web: Directory Structure

## Feature-First Layout (Recommended)
Organize by **feature**, not by technical layer. Each feature is self-contained.

```
src/
├── main.tsx                   # Entry point — ReactDOM.createRoot only
├── App.tsx                    # Router setup, providers, global layout
├── core/                      # Shared, app-wide code
│   ├── components/            # Truly reusable UI primitives
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   └── index.ts       # Re-export: import { Button } from '@/core/components/Button'
│   │   └── ...
│   ├── hooks/                 # App-wide hooks (useDebounce, useLocalStorage, etc.)
│   ├── utils/                 # Pure utility functions (no React dependencies)
│   ├── types/                 # Shared TypeScript types/interfaces
│   ├── constants/             # App-wide constants
│   ├── store/                 # Redux Toolkit store setup (see redux.md)
│   │   ├── index.ts           # configureStore, RootState/AppDispatch types
│   │   ├── hooks.ts           # useAppDispatch/useAppSelector
│   │   └── api.ts             # createApi — shared RTK Query base
│   └── router/
│       └── router.tsx         # Route definitions (React Router, TanStack Router, etc.)
├── features/
│   ├── auth/
│   │   ├── components/        # Feature-local UI components
│   │   │   └── LoginForm.tsx
│   │   ├── hooks/             # Feature-local hooks
│   │   │   └── useLogin.ts
│   │   ├── pages/             # Route-level components (one per route)
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── services/          # API call functions for this feature
│   │   │   └── authService.ts
│   │   ├── store/             # Redux Toolkit slice for this feature (see redux.md)
│   │   │   └── authSlice.ts
│   │   └── types.ts           # Feature-local types
│   └── dashboard/
│       └── ...                # Same structure as auth/
├── assets/                    # Static assets (images, fonts, icons)
└── styles/                    # Global CSS, design tokens, theme
    ├── globals.css
    └── tokens.css
```

## Key Conventions

**Index files:** Use `index.ts` barrel files at the feature boundary to define the public API of a feature. Internal files should only be imported by sibling files in the same feature.

```ts
// features/auth/index.ts — public API
export { LoginPage } from './pages/LoginPage';
export { useAuth } from './hooks/useAuth';
export type { AuthUser } from './types';
```

**Services:** API calls live in `services/`, not directly in hooks or components. This separates transport concerns from UI logic and makes mocking in tests trivial.

```ts
// features/auth/services/authService.ts
export async function login(credentials: LoginCredentials): Promise<AuthUser> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });
  if (!res.ok) throw new ApiError(res);
  return res.json();
}
```

**Pages vs Components:** A `page` is a route-level component — it composes feature components and handles data fetching. A `component` is reusable within (or across) features.

## File Naming Rules
| Type | Convention | Example |
|------|-----------|---------|
| Components / Pages | `PascalCase.tsx` | `UserProfile.tsx`, `LoginPage.tsx` |
| Hooks | `camelCase.ts` | `useAuth.ts` |
| Services | `camelCase.ts` | `authService.ts` |
| Redux slices | `camelCase.ts` + `Slice` suffix | `authSlice.ts` |
| Tests | `<subject>.test.tsx` | `LoginForm.test.tsx` |
| Types | `camelCase.ts` or `types.ts` | `types.ts` |
| Barrel exports | `index.ts` | `index.ts` |

## Key Config Files at Project Root
| File | Purpose |
|------|---------|
| `tsconfig.json` | TypeScript config — set `paths` for `@/` alias |
| `vite.config.ts` / `next.config.ts` | Bundler config |
| `.eslintrc.cjs` | Lint rules |
| `.prettierrc` | Formatting rules |
| `vitest.config.ts` | Test runner config |
