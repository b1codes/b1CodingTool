# SwiftUI: State Management with The Composable Architecture (TCA)

Use [The Composable Architecture](https://github.com/pointfreeco/swift-composable-architecture) (`swift-composable-architecture`) for all feature-level and business state. This is the standardized approach across B1Codes SwiftUI projects — analogous to `flutter_bloc` on the Flutter side.

## Core Concepts

TCA separates a feature into four pieces:

- **State** — a value type describing the data a feature needs
- **Action** — an enum describing every way the outside world can affect the feature (user interaction, network response, timer tick)
- **Reducer** — a function that evolves `State` given an `Action`, and optionally returns an `Effect` to run
- **Store** — runtime that owns the state, processes actions through the reducer, and publishes state changes to the view

```
View sends Action → Reducer mutates State → Store publishes → View re-renders
                                 └─→ Effect (async work) → sends further Action back in
```

**Rule of thumb:** Use `@State`/`@Binding` only for private, ephemeral, view-only data (sheet presentation flags with no side effects, focus state, drag offsets). Anything that represents business logic, survives navigation, triggers a side effect, or needs to be unit tested belongs in a TCA `Store`. Do not use `@Observable`/`ObservableObject` for new feature state — TCA's `@ObservableState` replaces that role.

## Defining a Feature

Use the `@Reducer` macro. `@ObservableState` makes `State` drive SwiftUI view updates directly through the store.

```swift
import ComposableArchitecture

@Reducer
struct CounterFeature {
  @ObservableState
  struct State: Equatable {
    var count = 0
    var numberFact: String?
    var isLoading = false
  }

  enum Action {
    case decrementButtonTapped
    case incrementButtonTapped
    case numberFactButtonTapped
    case numberFactResponse(String)
  }

  @Dependency(\.numberFactClient) var numberFactClient

  var body: some Reducer<State, Action> {
    Reduce { state, action in
      switch action {
      case .decrementButtonTapped:
        state.count -= 1
        return .none

      case .incrementButtonTapped:
        state.count += 1
        return .none

      case .numberFactButtonTapped:
        state.isLoading = true
        return .run { [count = state.count] send in
          let fact = try await numberFactClient.fetch(count)
          await send(.numberFactResponse(fact))
        }

      case let .numberFactResponse(fact):
        state.isLoading = false
        state.numberFact = fact
        return .none
      }
    }
  }
}
```

**Rules:**
- `State` must be `Equatable` — required for `@ObservableState` diffing and for `TestStore` assertions.
- `Action` is a plain enum, not a class hierarchy — exhaustive `switch` is the whole point.
- Never mutate `State` outside of the `Reduce` closure. The reducer is the single place state evolves.

## Composing Features (Parent/Child)

Use `Scope` to embed a child reducer's state/action inside a parent, and `.ifLet` / `@Presents` for optional child features driving navigation.

```swift
@Reducer
struct AppFeature {
  @ObservableState
  struct State: Equatable {
    var counter = CounterFeature.State()
    @Presents var addItem: ItemFormFeature.State?
  }

  enum Action {
    case counter(CounterFeature.Action)
    case addItem(PresentationAction<ItemFormFeature.Action>)
    case addButtonTapped
  }

  var body: some ReducerOf<Self> {
    Scope(state: \.counter, action: \.counter) {
      CounterFeature()
    }
    Reduce { state, action in
      switch action {
      case .addButtonTapped:
        state.addItem = ItemFormFeature.State()   // populating drives navigation
        return .none
      case .counter, .addItem:
        return .none
      }
    }
    .ifLet(\.$addItem, action: \.addItem) {
      ItemFormFeature()
    }
  }
}
```

Prefer standard SwiftUI presentation modifiers (`.sheet`, `.popover`, `.fullScreenCover`, `.navigationDestination`) bound to `@Presents` state via `@Bindable var store` — do not reach for TCA's older custom navigation modifiers in new code.

## Dependencies

Inject side effects (network clients, persistence, clocks) via `@Dependency`, never as singletons or directly-constructed instances inside the reducer.

```swift
@Reducer
struct Feature {
  @Dependency(\.numberFactClient) var numberFactClient
  @Dependency(\.dismiss) var dismiss
  // ...
}
```

Override dependencies for a scoped reducer (e.g. onboarding needs a mocked user-defaults) with `.dependency(\.key, value)` in the reducer's `body`. Override for tests via `TestStore`'s `withDependencies` — never by mutating a shared live instance.

## Consuming State in SwiftUI Views

Hold the store with `@Bindable` so two-way bindings can be derived directly from it.

```swift
struct CounterView: View {
  @Bindable var store: StoreOf<CounterFeature>

  var body: some View {
    Form {
      Text("\(store.count)")
      Button("Increment") { store.send(.incrementButtonTapped) }
      Button("Decrement") { store.send(.decrementButtonTapped) }

      if store.isLoading {
        ProgressView()
      } else if let fact = store.numberFact {
        Text(fact)
      }

      Button("Get fact") { store.send(.numberFactButtonTapped) }
    }
  }
}

#Preview {
  CounterView(
    store: Store(initialState: CounterFeature.State()) {
      CounterFeature()
    }
  )
}
```

For bindable controls (`TextField`, `Toggle`, `Slider`), derive the binding from the store and route the write through an action with `.sending(\.actionCase)`:

```swift
TextField("Name", text: $store.name.sending(\.nameChanged))
```

Read a child store for a subview with `store.scope(state:action:)`. Don't reach for `WithViewStore` in new SwiftUI code — it exists for pre-`@Observable` compatibility and UIKit interop only.

## Effects

Return `.none` when an action needs no side effect. Return `.run { send in ... }` for async work (network calls, timers, file I/O); it runs on a cooperative task tied to the store's lifetime and is automatically cancelled if the store is torn down. Capture only the state you need at the time the effect starts (`[count = state.count]`) — the effect closure does not have access to live `state`.

## Testing

Use `TestStore` to exhaustively assert every state mutation and every action an effect feeds back in.

```swift
import ComposableArchitecture
import Testing

@MainActor
struct CounterFeatureTests {
  @Test
  func incrementAndFetchFact() async {
    let store = TestStore(initialState: CounterFeature.State()) {
      CounterFeature()
    } withDependencies: {
      $0.numberFactClient.fetch = { "\($0) is a great number." }
    }

    await store.send(.incrementButtonTapped) {
      $0.count = 1
    }
    await store.send(.numberFactButtonTapped) {
      $0.isLoading = true
    }
    await store.receive(\.numberFactResponse) {
      $0.isLoading = false
      $0.numberFact = "1 is a great number."
    }
  }
}
```

`send` requires a trailing closure describing the expected state mutation; `receive` asserts an action produced by an in-flight effect arrives and describes its mutation. A mismatch fails with a state diff, not just a boolean.

## Best Practices

- **Never put business logic in the view.** The view sends an action; the reducer decides what happens.
- **One `@Reducer` per feature/domain concept.** A `CartFeature` should not know about authentication.
- **State must be `Equatable`.** Needed for `@ObservableState` change detection and `TestStore` diffing.
- **Inject all side effects via `@Dependency`.** Never call `URLSession.shared`, `UserDefaults.standard`, or construct a live client directly inside a reducer — it makes the feature untestable.
- **Don't build a `Store` inside a view's `body`.** Construct it once (at the app root, a parent feature, or a `@State` property on the owning view) and pass it down.
- **Prefer `.ifLet`/`@Presents` over hand-rolled optional-state navigation.** It keeps parent/child lifecycle and cancellation correct for free.

## Directory Placement

Combine `State`, `Action`, and the reducer `body` in a single `<Name>Feature.swift` file per feature — TCA convention favors this over splitting into separate files the way `flutter_bloc` does with event/state/bloc:

```
Sources/
├── Features/
│   └── Auth/
│       ├── AuthFeature.swift    # @Reducer: State, Action, body
│       └── AuthView.swift       # SwiftUI View bound to StoreOf<AuthFeature>
├── Models/                      # plain data types shared across features
└── Dependencies/                # @Dependency clients (DependencyKey conformances)
```
