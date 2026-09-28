# Docker: Runtime & CLI

## Engine vs. CLI
- The `docker` CLI is a client; the engine it talks to is chosen by the active **context** (`docker context show`). On macOS that engine may be Docker Desktop (`desktop-linux`), OrbStack (`orbstack`), or a remote host.
- Never hardcode a socket path such as `/var/run/docker.sock` in scripts or docs; rely on the active context or `DOCKER_HOST`.
- Dockerfiles and Compose files written for this module run unchanged on any Docker-compatible engine (see the `orbstack` module).

## Compose
- Use Compose v2 syntax: `docker compose up` (a CLI plugin), not the legacy `docker-compose` binary.
- Prefer the canonical filename `compose.yaml`; `docker-compose.yml` is still read but is the legacy name.
- Omit the top-level `version:` key — it is obsolete in the Compose Specification and only produces a warning.
- Put per-developer tweaks in `compose.override.yaml` (merged automatically) and keep it out of version control when it contains machine-specific values.

## Building on Apple Silicon
- Macs build `linux/arm64` images by default. Servers are frequently `linux/amd64`.
- Publish production images as multi-platform: `docker buildx build --platform linux/amd64,linux/arm64 -t <image> --push .`
- When only one platform is needed, set it explicitly (`--platform linux/amd64`) instead of relying on the host default.

## Networking
- Containers reach services on the host via `host.docker.internal`.
- Services in the same Compose project reach each other by service name (e.g. `db:5432`); never use `localhost` for another container.

## Build Context Hygiene
- Always ship a `.dockerignore` that excludes `.git`, `.venv`, `node_modules`, `.env*`, and build artifacts — they bloat the context and can leak secrets into image layers.
- Pass secrets with `RUN --mount=type=secret,...`, never via `ARG` or `ENV`, which are persisted in image history.
