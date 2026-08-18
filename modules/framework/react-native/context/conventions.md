# React Native (Expo): Coding Conventions

## TypeScript
- Use TypeScript for all files. Configure `strict: true` in `tsconfig.json`.
- Avoid `any`. Use `unknown` for values of indeterminate type and narrow before use.
- Type all component props with an `interface`. Use `type` for unions and utility types.
- Type navigation params explicitly using Expo Router's typed routes or a hand-written param map.

```tsx
interface UserAvatarProps {
  uri: string;
  size?: number;
  onPress?: () => void;
}

export function UserAvatar({ uri, size = 40, onPress }: UserAvatarProps) { ... }
```

## Naming
| Entity | Convention | Example |
|--------|-----------|---------|
| Components / Screens | `PascalCase.tsx` | `UserCard.tsx`, `ProfileScreen.tsx` |
| Hooks | `camelCase` with `use` prefix | `useAuth.ts`, `useNotifications.ts` |
| Redux slices | `camelCase` + `Slice` suffix | `authSlice.ts` |
| Services | `camelCase` + `Service` suffix | `authService.ts` |
| Route files (Expo Router) | `kebab-case.tsx` | `user-profile.tsx` (maps to `/user-profile`) |
| Layout files | `_layout.tsx` | `_layout.tsx` |
| Constants | `SCREAMING_SNAKE_CASE` | `API_BASE_URL` |
| Event handlers | `handle` prefix | `handlePress`, `handleSubmit` |
| Boolean props | `is`/`has`/`can` prefix | `isLoading`, `hasError` |

## Styles
- Always use `StyleSheet.create()` at module scope — never inline style objects on JSX elements.
- Avoid hardcoded color values in component files. Reference design tokens from a central theme file.
- Use `useColorScheme()` or a theme context for dark/light mode — never duplicate style definitions.

```tsx
// Good
const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: theme.colors.background,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: theme.colors.text,
  },
});

// Bad — inline objects create a new object on every render
<View style={{ flex: 1, padding: 16 }}>
```

## Imports
Order imports in four groups separated by blank lines:
1. React and React Native core (`react`, `react-native`)
2. Expo SDK packages (`expo-*`, `@expo/*`)
3. Third-party libraries (alphabetical)
4. Internal and relative imports

```tsx
import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useRouter } from 'expo-router';
import * as SecureStore from 'expo-secure-store';

import { FlashList } from '@shopify/flash-list';

import { useAuth } from '@/hooks/useAuth';
import { theme } from '@/core/theme';
```

## Component File Structure
Order contents as follows:
1. Imports
2. Types / interfaces
3. Module-scoped constants
4. Exported component function
5. Private helper functions (non-exported)
6. `StyleSheet.create(...)` call (always last)

## Linting & Formatting
- Use **ESLint** with `eslint-config-expo` as the base config.
- Use **Prettier** for formatting.
- Enable `react-hooks/exhaustive-deps` — never disable it.
- Run `npx expo-doctor` periodically to catch SDK version mismatches and config issues.
