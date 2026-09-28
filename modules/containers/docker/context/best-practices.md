# Docker: Best Practices

## Local Development
- **Docker Compose:** Use `compose.yaml` and `docker compose` (v2) to orchestrate services locally.
- **Volumes:** Mount project directories as volumes for live-reloading.
- **Environment Variables:** Use `.env` files for local configuration.

## Production & CI
- **Multi-stage Builds:** Separate the build environment from the runtime environment to minimize image size.
- **Non-Root User:** Always run the application process as a non-privileged user.
- **Health Checks:** Include health checks in Compose files for reliable service dependencies.
- **No Orchestrators:** Focus on core container lifecycle; do not include Swarm or Kubernetes configs.
