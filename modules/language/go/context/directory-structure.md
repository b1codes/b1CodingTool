# Go: Directory Structure

## Standard Project Layout
Based on the widely-adopted (unofficial but de facto standard) `golang-standards/project-layout`:

```
project_root/
├── go.mod                 # Module definition
├── go.sum                 # Dependency checksums
├── README.md
├── cmd/                   # Entry points, one subdir per binary
│   └── myapp/
│       └── main.go
├── internal/               # Private application/library code (import-restricted by the compiler)
│   ├── config/
│   └── service/
├── pkg/                    # Public library code safe for external import (use sparingly)
├── api/                    # API definitions (OpenAPI/Swagger, protobuf/gRPC specs)
└── test/                   # Additional external test data and integration test helpers
```

## Guidelines
- **`internal/` is enforced by the compiler:** packages under `internal/` cannot be imported by code outside the module rooted at the parent of `internal/`. Default to `internal/` unless a package is deliberately a public API.
- **`cmd/` per binary:** each `main` package gets its own directory under `cmd/`; keep `main.go` thin — wire up dependencies and delegate to `internal/` packages.
- **No `src/` directory:** unlike some ecosystems, Go projects put packages directly at the module root or under `internal/`/`pkg/`, not inside a `src/` wrapper.
- **Tests live beside code:** `*_test.go` files sit in the same directory as the code they test, not in a separate `tests/` tree.
