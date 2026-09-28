# OrbStack: Conventions

## Compose Overrides
- OrbStack-specific settings (domain labels) go in `compose.orbstack.yaml`, generated from `templates/compose.orbstack.yaml.tmpl`.
- Run with both files: `docker compose -f compose.yaml -f compose.orbstack.yaml up`. Developers on other engines just omit the second file.
- Use custom domains under `.local` (e.g. `api.myapp.local`) and document them in the project README.

## Documentation & Scripts
- In docs, prefer `https://<service>.<project>.orb.local` URLs for OrbStack users and keep the `localhost:<port>` form for everyone else.
- Scripts must not call `orb` or `orbctl` unconditionally — guard with `command -v orb` so the project still works on Docker Desktop, Linux, and CI.
- Do not commit the active Docker context or any path under `~/OrbStack`.
