# Apple Container: Conventions

## Docker → `container` Command Map
| Docker | Apple `container` |
| :--- | :--- |
| `docker run` / `ps` / `rm` / `exec` / `logs` | `container run` / `ls` / `rm` / `exec` / `logs` |
| `docker build -t app .` | `container build -t app .` |
| `docker images` / `pull` / `push` / `tag` | `container image ls` / `pull` / `push` / `tag` |
| `docker login` | `container registry login` |
| `docker volume ...` / `docker network ...` | `container volume ...` / `container network ...` |
| `docker compose up` | *(none)* — `scripts/dev-containers.sh up` |
| `depends_on: condition: service_healthy` | *(none)* — poll readiness in the script |

## Project Layout
- `scripts/dev-containers.sh`: the project's Compose replacement, with `up`, `down`, and `status` subcommands. Generate it from `templates/dev-containers.sh.tmpl`.
- `Dockerfile`: shared with the `docker` module unchanged. Keep one Dockerfile for every runtime.

## Script Rules
- Name every container with `--name` so it has a stable DNS name (`<name>.<domain>`).
- Make `up` idempotent: skip or replace containers that already exist instead of failing.
- Use named volumes (`container volume create`) for database data; bind mounts (`-v "$PWD:/app"`) only for source code.
- Replace `depends_on` with explicit readiness polling (e.g. `container exec db pg_isready`) and a timeout.
- Keep secrets in an `.env` file passed with `--env-file`; never inline them in the script.
- Publish ports with `-p` only for what the Mac itself must reach; containers talk to each other over DNS.
