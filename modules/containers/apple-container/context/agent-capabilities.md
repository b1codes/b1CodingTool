# Apple Container: Agent Commands & Skills

## Recommended Skills
- **Compose-to-Container Translator:** Reads an existing `compose.yaml` (or the list of services the user needs) and produces `scripts/dev-containers.sh` from `templates/dev-containers.sh.tmpl`, mapping each service to a `container run -d --name <service>` call on the `default` network.
- **Container Runtime Doctor:** Diagnoses a broken setup by checking services, the DNS domain, and the macOS version.

## Common Agent Commands
These commands are run by the agent (not the `b1` CLI) when the user asks for them by name:
- `/apple-container init`:
  1. Collect the services from `compose.yaml` if present, otherwise ask the user.
  2. Generate `scripts/dev-containers.sh` from `templates/dev-containers.sh.tmpl` and make it executable.
  3. If `~/.config/container/config.toml` has no `[dns]` domain, show the user `templates/config.toml.tmpl` and the `sudo container system dns create <domain>` step — do not run `sudo` on the user's behalf.
- `/apple-container doctor`: Run `container system status`, `container system property ls`, and `container system dns ls`, check `sw_vers -productVersion` against the macOS 15 limitations in `best-practices.md`, and report what to fix — no script backs this command; it is performed directly by the agent.

## Related Modules
- `docker`: Source of the shared `Dockerfile` templates; `container build` consumes them unchanged.
- `orbstack`: Use instead when the project needs Compose or the Docker socket.
