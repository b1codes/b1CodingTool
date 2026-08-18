# SwiftUI: Best Practices

## View Composition
- **Small is Beautiful:** Extract subviews liberally. If a `body` property exceeds 30-40 lines, it's a candidate for extraction into a separate `struct`.
- **View Hierarchy:** Prefer `Group` or `@ViewBuilder` for logic-heavy views to avoid deep nesting of `if/else` inside containers.
- **Computed Properties:** Use private computed properties for simple sub-elements that don't need their own state.

## State Management
- **Feature/Business State:** Use The Composable Architecture (TCA) — `@Reducer` + `@ObservableState` + `Store`. See `swiftui-tca.md` for the full pattern. Avoid `ObservableObject`/`@Published` and standalone `@Observable` view models in new code; TCA's `@ObservableState` is the standardized replacement.
- **Local View State:** Use `@State` only for private, ephemeral, view-only data with no side effects (e.g. a `TextField`'s focus state, an in-progress drag offset).
- **Data Flow:** Pass a `Store` down via initializers; use `@Environment` only for cross-cutting concerns that are not feature state (e.g. theme, color scheme).
- **Binding:** Use `@Binding` for two-way connections to state owned by a parent *view*. When the binding needs to reach into a TCA `Store`, derive it with `@Bindable var store` and `.sending(\.action)` instead.

## Performance
- **Identify Stability:** Ensure your data models are stable to prevent unnecessary view body evaluations.
- **Previews:** Always include `Preview` providers. Use mock data to test various states (loading, error, empty).
- **Heavy Work:** Never perform network calls or heavy computation directly in a view initializer or `body`. Use `.task` or `.onAppear`.

## Layout
- **Containers:** Use `VStack`, `HStack`, and `ZStack` as primary building blocks.
- **Adaptive Layout:** Use `Spacer`, `layoutPriority()`, and `GeometryReader` (sparingly) to create responsive UIs.
- **Safe Areas:** Respect safe areas unless a background element explicitly needs to ignore them.
