# SwiftUI: Directory Structure

## Standard App Layout
```
Sources/
├── [AppName]App.swift      # Application entry point
├── Features/                # One folder per feature (TCA)
│   └── Auth/
│       ├── AuthFeature.swift  # @Reducer: State, Action, body
│       └── AuthView.swift     # SwiftUI View bound to StoreOf<AuthFeature>
├── Views/                  # Reusable, feature-agnostic UI components
│   └── Common/             # Buttons, Text fields, etc.
├── Models/                 # Plain data types shared across features
├── Dependencies/           # @Dependency clients (DependencyKey conformances)
└── Resources/              # Assets, Colors, Fonts
```

See `swiftui-tca.md` for what belongs in a `*Feature.swift` file and how features compose.

## Modular Structure
- **Domain-Specific Views:** Keep a feature's `Feature.swift` and `View.swift` co-located under `Features/<Name>/`.
- **Preview Assets:** Use `Preview Content` folder for mock JSON or images that should only be included in development builds.
