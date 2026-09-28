# Apple Container: Best Practices

## What It Is
- `container` is Apple's open-source CLI for running OCI-compatible Linux containers on Apple silicon Macs.
- Each container runs in its **own lightweight VM** (Virtualization.framework) with its own IP address, rather than all containers sharing one Linux VM as Docker Desktop does.
- Images are standard OCI images: pull from and push to Docker Hub, GHCR, etc. (`docker.io/` prefixes are accepted), and build from an ordinary `Dockerfile` or `Containerfile`.

## Requirements
- Apple silicon only. Target macOS 26 or later.
- On macOS 15 it runs with limitations: all containers share one isolated network, so **container-to-container traffic does not work**, and `container network` / `--network` are unavailable. Do not recommend multi-service setups there.

## Lifecycle
- Start the system services before any other command: `container system start`. Check them with `container system status`.
- Most commands fail with "PLUGINS: not available" or "apiserver is not running" when the services are down — start them rather than debugging the command.
- Images build inside a builder container (`container builder status`); give heavy builds more resources with `container build --cpus <n> --memory <size>`.

## Networking & DNS
- There is **no `container compose`**. Multi-service setups are shell scripts of `container run -d` commands.
- Containers find each other by **domain-qualified name on the `default` network** only (e.g. `db.test`, never bare `db`). This requires one-time setup:
  1. `~/.config/container/config.toml` containing a `[dns]` table with `domain = "test"` (TOML — edit the table in place, never append a second one).
  2. `container system stop && container system start` to reload it.
  3. `sudo container system dns create test` to point macOS at the container resolver.
- **Do not create custom networks** to wire services together — DNS name lookup does not work on custom networks. Use a custom network only to isolate containers, and then connect by IP from `container inspect <name>`.
- Reach services on the Mac from a container by creating a host domain: `sudo container system dns create host.container.internal --localhost <ip>`. There is no built-in `host.docker.internal`.

## Architecture
- The default platform is `linux/arm64`. Run amd64-only images with `--arch amd64 --rosetta`, and build for servers with `container build --platform linux/amd64`.

## When To Choose It
- Choose it for single containers, isolated workloads, and machines where Docker Desktop is not allowed.
- Prefer the `docker` or `orbstack` module when a project depends on Compose, Docker-specific tooling (Testcontainers, Dev Containers), or the Docker socket.
