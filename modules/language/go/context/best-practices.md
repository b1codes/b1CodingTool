# Go: Best Practices

## Error Handling
- **Explicit checks:** Handle errors immediately after the call that can produce them — no bare `_` discards for anything that isn't genuinely safe to ignore.
- **Wrapping:** Use `fmt.Errorf("doing X: %w", err)` to wrap errors with context while preserving the chain for `errors.Is` / `errors.As`.
- **Sentinel & typed errors:** Prefer package-level `var ErrNotFound = errors.New(...)` sentinels or custom error types over matching on error message strings.
- **No panics for control flow:** Reserve `panic`/`recover` for truly unrecoverable programmer errors (e.g. invariant violations at startup), never for expected failure paths.

## Code Quality
- **Accept interfaces, return structs:** Function parameters should take the narrowest interface needed; return concrete types.
- **Zero values:** Design types so their zero value is useful (e.g. `var buf bytes.Buffer` works without construction).
- **Composition over inheritance:** Use struct embedding for code reuse; Go has no class hierarchies.
- **Avoid globals:** Pass dependencies explicitly (constructors, `context.Context`) instead of relying on package-level mutable state.

## Concurrency
- **Goroutine ownership:** Every goroutine you start should have a clear owner responsible for its lifecycle and for making sure it exits (via `context.Context` cancellation or a done channel).
- **Channels vs. mutexes:** Use channels to orchestrate/communicate; use `sync.Mutex` to protect shared state. Don't use channels where a mutex is simpler.
- **context.Context:** Thread `ctx context.Context` as the first parameter through call chains that may be cancelled or carry deadlines; never store it in a struct.
- **Race detector:** Run `go test -race` regularly — data races are a compile-clean, runtime-only class of bug in Go.

## Performance
- **Benchmark before optimizing:** Use `go test -bench=.` and `pprof` to find real bottlenecks rather than guessing.
- **Minimize allocations:** Prefer passing slices/pointers over copying large structs in hot paths; reuse buffers with `sync.Pool` when profiling justifies it.
