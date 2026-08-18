# React Web: Best Practices

## Component Design
- **One responsibility per component.** If a component fetches data, transforms it, AND renders it, split it up. Keep presentational components free of data-fetching logic.
- Prefer **function components** exclusively. Class components are legacy — don't introduce new ones.
- Keep component files under ~150 lines. If a file grows larger, extract sub-components or hooks.
- Extract repeated JSX patterns into their own components, not private render functions. Extracted components get their own reconciliation identity; private functions do not.

## Hooks
- Only call hooks at the top level — never inside conditions, loops, or nested functions.
- Extract stateful logic into **custom hooks** (`use` prefix) when the same logic appears in more than one component or when a component's logic becomes hard to follow.
- Keep `useEffect` lean: one effect per concern, and always include a cleanup function when the effect sets up a subscription or timer.
- Avoid lying to the dependency array. If a value is used inside `useEffect`, it must be in the array. Use `useCallback`/`useMemo` to stabilize references rather than omitting them.

```tsx
// Good — one concern per effect, honest deps
useEffect(() => {
  const sub = eventBus.subscribe('update', handleUpdate);
  return () => sub.unsubscribe();
}, [handleUpdate]);
```

## State Management
- Keep local component state (`useState`/`useReducer`) for data genuinely owned by one component with no other consumers. Anything shared, cross-feature, or business-relevant belongs in a **Redux Toolkit** slice — see `redux.md`.
- Use `useReducer` over multiple related `useState` calls when *local* state transitions are complex or interdependent; once the state is shared, move it to a slice instead of reaching for `useReducer` + context.
- Use **RTK Query** (part of Redux Toolkit) for server state — it supersedes manually managing fetch/loading/error state in `useState` + `useEffect`, and standalone libraries like TanStack Query or SWR. See `redux.md`.
- Reserve context for truly global, low-frequency, non-transactional values (theme, locale) — not as a substitute for a slice. Once a value has real transitions or is written from more than one place, it belongs in Redux.

## Performance
- Wrap expensive computations in `useMemo`; wrap callbacks passed as props in `useCallback` — but only when you have a measured reason to, not preemptively.
- Use `React.lazy` + `Suspense` to code-split routes and heavy components.
- Virtualize long lists with a library like `@tanstack/react-virtual` — never render thousands of DOM nodes eagerly.
- Profile with React DevTools Profiler before optimizing. Premature optimization introduces complexity for no gain.

## Data Fetching
- Co-locate data fetching with the component that owns it, not a top-level ancestor that passes data down five levels.
- Always handle three states explicitly: loading, error, success. Never assume a fetch will succeed.
- Cancel or ignore in-flight requests when a component unmounts to avoid state updates on unmounted components.

```tsx
// Good — explicit states
if (isLoading) return <Spinner />;
if (error) return <ErrorView message={error.message} />;
return <UserList users={data} />;
```

## Accessibility
- Every interactive element must be reachable by keyboard and have a descriptive label (`aria-label`, `aria-labelledby`, or visible text).
- Use semantic HTML elements (`<button>`, `<nav>`, `<main>`, `<section>`) — don't use `<div onClick>` where a `<button>` belongs.
- Manage focus explicitly on route changes and modal open/close.
- Test with a screen reader periodically, not just automated lint tools.

## Error Boundaries
- Wrap route-level and feature-level subtrees in error boundaries so a single component crash doesn't take down the whole app.
- Log errors to an observability service (Sentry, Datadog) inside `componentDidCatch`.

## Testing
- Prefer **React Testing Library** over Enzyme or snapshot tests — test behavior, not implementation.
- Query by accessible roles and labels (`getByRole`, `getByLabelText`), not by class names or test IDs.
- Use **MSW (Mock Service Worker)** to intercept network requests in tests rather than mocking fetch directly.
- Reserve end-to-end tests (Playwright, Cypress) for critical user flows; they're slow — don't use them as unit tests.

```tsx
// Good — tests what the user sees
test('shows error on failed login', async () => {
  render(<LoginForm />);
  await userEvent.type(screen.getByLabelText('Email'), 'bad@example.com');
  await userEvent.click(screen.getByRole('button', { name: /sign in/i }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials');
});
```
