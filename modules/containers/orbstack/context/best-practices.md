# OrbStack: Best Practices

## What It Is
- OrbStack is a macOS app that provides a **Docker-compatible engine**, a Kubernetes cluster, and full **Linux machines**, all in one lightweight VM.
- It is a drop-in replacement for Docker Desktop: the standard `docker` and `docker compose` CLIs, Dockerfiles, and Compose files work unchanged. Keep projects runtime-neutral — never add OrbStack-only requirements to a shared `compose.yaml`.

## Engine Selection
- OrbStack registers the Docker context `orbstack` and repoints `/var/run/docker.sock` to its engine.
- Switch engines explicitly: `docker context use orbstack` or `docker context use desktop-linux`. Check with `docker context show` before debugging "missing" containers or images — they live per engine.
- Migrate existing Docker Desktop data (containers, volumes, images) with `orb docker migrate`.

## Local Domains & HTTPS
- Every container gets `<container-name>.orb.local`; Compose services get `<service>.<project>.orb.local`, where `<project>` is usually the folder name.
- OrbStack serves zero-setup HTTPS for these domains, and `https://orb.local` lists them. Prefer these URLs over published ports for local web services.
- Assign custom domains with the `dev.orbstack.domains` label (comma-separated, wildcards allowed). Keep the labels in an OrbStack-only override file so other engines ignore them.

## Networking
- Containers reach the Mac via `host.docker.internal`.
- Linux machines reach published container ports via `docker.orb.internal`.

## Linux Machines
- Create a full Linux distro with `orb create <distro> <name>` (e.g. `orb create ubuntu ci-runner`).
- Mac files are available inside machines under `/mnt/mac`; machine files are available on the Mac under `~/OrbStack`.
- Use a machine instead of a container when a task needs systemd, a persistent distro, or native Linux tooling rather than a packaged service.

## When To Choose It
- Choose it on macOS when a project needs Docker compatibility (Compose, Dev Containers, Testcontainers, the Docker socket) with lower resource use than Docker Desktop.
- Container workflows themselves are governed by the `docker` module; this module only covers what OrbStack adds on top.
