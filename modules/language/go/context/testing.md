# Go: Testing Standards

## Setup
- **Built-in:** Use the standard `testing` package — no external framework required. Files must be named `*_test.go` and live alongside the code under test.
- **Naming:** Test functions are `func TestXxx(t *testing.T)`; benchmarks are `func BenchmarkXxx(b *testing.B)`.

## Style
- **Table-driven tests:** Prefer a slice of struct cases iterated with `t.Run(tc.name, func(t *testing.T) {...})` over duplicated test functions.
- **Assertions:** Standard library favors explicit `if got != want { t.Errorf(...) }`. `testify/assert` and `testify/require` are acceptable for readability on larger suites — pick one convention per repo.
- **Subtests:** Use `t.Run` to isolate and name individual cases so failures pinpoint the exact input.

## Mocking
- **Prefer interfaces:** Define small interfaces at the point of use so fakes/mocks can be substituted without a mocking framework.
- **mockgen:** For larger interfaces, generate mocks with `go.uber.org/mock/mockgen` rather than hand-writing them.

## Commands
```bash
go test ./...                # Run all tests
go test -race ./...          # Run with the race detector
go test -cover ./...         # Report coverage
go test -run TestName ./...  # Run a single test by name
go test -bench=. ./...       # Run benchmarks
```
