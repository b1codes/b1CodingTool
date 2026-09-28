# Docker: Python Conventions

## Image Selection
- Use official Python "slim" images (e.g., `python:3.12-slim`) for a balance of size and compatibility.

## Dependency Management
- **UV:** Prefer `uv` for fast dependency installation.
  - **Source:** Use `COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv` to get the binary.
  - **Environment:** Set `UV_COMPILE_BYTECODE=1` for faster startup.
  - **Workflow:** Use `uv sync` to manage a virtual environment (`.venv`) in the builder stage.
- **Layer Caching:** 
  - Copy `pyproject.toml` and `uv.lock` before application code.
  - Use `--mount=type=cache,target=/root/.cache/uv` to speed up repeated installs.

## Production Servers
- **Django:** Use `gunicorn` or `uvicorn` (with gunicorn worker).
- **FastAPI:** Use `uvicorn`.
- **Runtime:** Only copy the `.venv` and application code to the final stage using `COPY --chown`.
