# Go: Dependency Management with Go Modules

## Overview
**Go Modules** (built into the `go` tool since Go 1.16+) are the standard dependency system — no external package manager needed. Dependencies and their versions are tracked in `go.mod`, with exact resolved checksums in `go.sum`.

## Common Commands
```bash
go mod init <module-path>   # Initialize a new module (e.g. github.com/org/repo)
go get <package>@<version>  # Add or upgrade a dependency
go get -u ./...             # Upgrade all dependencies to latest minor/patch
go mod tidy                 # Add missing / remove unused dependencies, sync go.sum
go mod vendor                # Vendor dependencies into vendor/ (optional, for reproducible builds)
go list -m all               # List the full resolved dependency graph
```

## go.mod
- Declare the module path matching the repository's import path (e.g. `module github.com/org/repo`).
- Pin the `go` directive to the minimum supported toolchain version.
- Always run `go mod tidy` before committing — a dirty `go.mod`/`go.sum` should fail CI.

## Versioning
- Follow semantic import versioning: major version ≥ 2 requires a `/v2` (etc.) suffix on the module path.
- Prefer well-maintained, minimal-dependency third-party packages; audit new dependencies via `go list -m all` and `govulncheck`.
