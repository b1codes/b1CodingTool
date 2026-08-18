# React Native (Expo): Best Practices

## Component Design
- Use **function components** exclusively. Keep components focused on a single responsibility.
- Extract any subtree that would otherwise push `return` past ~50 lines into its own component file.
- Avoid anonymous inline components — define them at the module level so React can maintain stable identity across renders.
- Never nest `StyleSheet.create` calls inside components. Define styles at module scope so they're created once, not on every render.

## Platform-Specific Code
- Use `Platform.OS` for small conditional values (margins, font sizes). For substantially different UIs, use platform-specific file extensions: `Component.ios.tsx` / `Component.android.tsx`.
- Never hardcode pixel values for safe areas — always use `useSafeAreaInsets()` from `react-native-safe-area-context`.
- Use `KeyboardAvoidingView` with `behavior={Platform.OS === 'ios' ? 'padding' : 'height'}` for forms — the difference is required because iOS and Android handle keyboard displacement differently.

```tsx
// Good — platform file extension for divergent behavior
// Button.ios.tsx    → uses iOS HIG styling
// Button.android.tsx → uses Material styling
// Button.tsx        → fallback for web/other
```

## Navigation (Expo Router)
- Use **Expo Router** (file-based routing) for all navigation. Define routes via filesystem layout under `app/`, not imperative config.
- Use typed routes (`href` as a typed string) — enable `"experiments": { "typedRoutes": true }` in `app.json`.
- Pass data between routes via route params for shallow data; use a store for complex shared state. Never pass non-serializable objects as params.
- Use **layouts** (`_layout.tsx`) to wrap groups of screens with shared chrome (header, tabs, drawers).

## Performance
- Use `FlatList` (or `FlashList` from Shopify) for any list that could grow beyond ~20 items — never `ScrollView` + `.map()`.
- Memoize list item components with `React.memo` to prevent re-renders when only the scroll position changes.
- Use `InteractionManager.runAfterInteractions` to defer expensive operations until after navigation animations complete.
- Avoid JS-driven animations; use `react-native-reanimated` for 60fps animations that run on the UI thread.
- Profile with the Flipper Performance plugin or Expo Dev Tools before optimizing.

```tsx
// Good — FlashList is significantly more performant than FlatList for long lists
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={items}
  renderItem={({ item }) => <ItemRow item={item} />}
  estimatedItemSize={72}
  keyExtractor={(item) => item.id}
/>
```

## Images & Assets
- Always specify explicit `width` and `height` on `<Image>` — React Native cannot infer dimensions from remote URLs.
- Use `expo-image` instead of the built-in `Image` for better caching and performance.
- Prefer vector icons (`@expo/vector-icons`) over bitmap images for UI icons — they scale without blurring.

## State Management
- Keep local component state (`useState`/`useReducer`) for data genuinely owned by one component with no other consumers. Anything shared across screens, anything that must survive navigation, or anything business-relevant belongs in a **Redux Toolkit** slice — see `redux.md`.
- Use **RTK Query** (part of Redux Toolkit) for server state instead of manual `useState` + `useEffect` fetching. See `redux.md`.
- Provide the store from the Expo Router root layout (`app/_layout.tsx`), above the navigator, so every route can reach it.

## Async & State
- After any `await` in an event handler, check whether the component is still mounted before calling `setState`. Use a ref flag or the `useEffect` cleanup pattern.
- Use `SecureStore` (from `expo-secure-store`) for sensitive data (tokens, credentials) — never `AsyncStorage` for secrets, and never persist a Redux slice containing them through `redux-persist` (which writes to `AsyncStorage`). See `redux.md` for the persistence pattern.
- Use `AsyncStorage` only for non-sensitive, serializable user preferences.

## Accessibility
- Set `accessibilityRole` on all interactive elements (`button`, `link`, `header`, etc.).
- Set `accessibilityLabel` on elements whose visual label is insufficient (icon-only buttons, images).
- Test with VoiceOver (iOS) and TalkBack (Android) — automated tools miss many native a11y issues.

## Testing
- Use **React Native Testing Library** (`@testing-library/react-native`) for component tests.
- Mock `expo-router` and native modules in Jest via the Expo preset (`jest-expo`).
- Use `react-native-reanimated/mock` in test setup to prevent animation-related errors.
- Write E2E tests for critical flows with **Maestro** — it runs on real devices/simulators and requires no code changes.
