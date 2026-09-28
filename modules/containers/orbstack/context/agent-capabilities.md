# OrbStack: Agent Commands & Skills

## Recommended Skills
- **Docker Desktop Migrator:** Walks the user through moving from Docker Desktop to OrbStack without losing volumes.
- **Local Domain Configurator:** Gives each Compose service a readable HTTPS domain via an override file.

## Common Agent Commands
These commands are run by the agent (not the `b1` CLI) when the user asks for them by name:
- `/orbstack migrate`: Confirm with the user first (it copies all Docker Desktop data), then run `orb docker migrate`, then `docker context use orbstack`, and verify with `docker context show` and `docker volume ls`.
- `/orbstack domains`: Read the services from `compose.yaml`, ask which should get custom domains, and generate `compose.orbstack.yaml` from `templates/compose.orbstack.yaml.tmpl`. Remind the user that default `<service>.<project>.orb.local` domains already work without it.

## Related Modules
- `docker`: Owns Dockerfile and Compose conventions; install it alongside this module.
- `apple-container`: Apple's native alternative, without Compose or Docker socket compatibility.
