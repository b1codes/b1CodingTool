# Go: Coding Conventions

## Style Guide
- **gofmt:** All code must be formatted with `gofmt` (or `goimports`, which also manages imports). Never hand-format — run it on save.
- **golangci-lint:** Use `golangci-lint run` as the standard linter aggregator (covers `govet`, `staticcheck`, `errcheck`, `unused`, etc.).
- **Line Length:** No hard limit, but keep lines readable; wrap long function signatures and struct literals.

## Naming
| Entity | Convention | Example |
|--------|-----------|---------|
| Packages | short, lowercase, no underscores | `httputil`, `authz` |
| Exported identifiers | `PascalCase` | `UserService`, `NewClient()` |
| Unexported identifiers | `camelCase` | `parseToken()`, `retryCount` |
| Interfaces | `-er` suffix for single-method interfaces | `Reader`, `Validator` |
| Constants | `PascalCase` or `camelCase` (not `SCREAMING_SNAKE_CASE`) | `MaxRetries`, `defaultTimeout` |

## Imports
- Group imports in three blocks, separated by blank lines: standard library, third-party, local module — `goimports` enforces this automatically.
- Avoid dot imports and import aliasing except to resolve genuine name collisions.

## Comments & Documentation
- Every exported identifier gets a doc comment starting with its own name (`// UserService handles...`) so `go doc` and godoc render correctly.
- Package-level doc comments live in a `doc.go` file when they exceed a couple of lines.
