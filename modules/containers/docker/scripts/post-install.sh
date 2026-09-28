#!/bin/bash
# post-install.sh: Report the local Docker setup after module install.
# Executed from the project root. Informational only — a missing runtime is
# not an install failure, so this script always exits 0.

if ! command -v docker &> /dev/null; then
    echo "ℹ️ Docker CLI not found. Install Docker Desktop, OrbStack, or Docker Engine to use this module's templates."
    exit 0
fi

context="$(docker context show 2>/dev/null)"
echo "🐳 Docker CLI found (active context: ${context:-unknown})."

if ! docker compose version &> /dev/null; then
    echo "⚠️ The Compose v2 plugin is missing. Install it so 'docker compose' works."
fi

if [ ! -f ".dockerignore" ] && { [ -f "Dockerfile" ] || [ -f "compose.yaml" ] || [ -f "docker-compose.yml" ]; }; then
    echo "⚠️ Docker files found but no .dockerignore — consider running '/docker audit'."
fi

exit 0
