#!/bin/bash
# post-install.sh: Report the OrbStack setup after module install.
# Executed from the project root. Informational only — a missing runtime is
# not an install failure, so this script always exits 0.

if ! command -v orb &> /dev/null && [ ! -d "/Applications/OrbStack.app" ]; then
    echo "ℹ️ OrbStack not found. Install it from https://orbstack.dev to use this module."
    exit 0
fi

echo "🟣 OrbStack is installed."

if command -v docker &> /dev/null; then
    context="$(docker context show 2>/dev/null)"
    if [ "$context" != "orbstack" ]; then
        echo "ℹ️ Active Docker context is '${context:-unknown}'. Switch with: docker context use orbstack"
    fi
fi

exit 0
