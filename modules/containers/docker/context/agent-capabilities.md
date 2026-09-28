# Docker: Agent Commands & Skills

## Recommended Skills
- **Docker Project Initializer:** Produces a multi-stage `Dockerfile` and a `compose.yaml` assembled from the modular service templates in `templates/`.
- **Docker Configuration Auditor:** Reviews Dockerfiles and Compose files for containers running as root, unpinned (`:latest`) base images, missing health checks, secrets baked into layers, and a missing `.dockerignore`.

## Common Agent Commands
These commands are run by the agent (not the `b1` CLI) when the user asks for them by name:
- `/docker init`: Follow the procedure in `skills/docker-init.md` inside this module's installed directory, using the files in `templates/`.
- `/docker audit`: Review the project's `Dockerfile*`, `compose*.yaml`, and `.dockerignore` against `best-practices.md` and `runtime.md` and report findings — no script backs this command; it is a review task performed directly by the agent.

## Related Modules
- `orbstack`: Drop-in Docker engine for macOS; everything in this module works unchanged on it.
- `apple-container`: Builds the same Dockerfiles but has no Compose support — see that module for the translation.
