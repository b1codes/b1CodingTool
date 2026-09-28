#!/bin/bash
# post-install.sh: Report the Apple `container` setup after module install.
# Executed from the project root. Informational only — a missing runtime is
# not an install failure, so this script always exits 0.

if ! command -v container &> /dev/null; then
    echo "ℹ️ Apple 'container' CLI not found. Install it from https://github.com/apple/container/releases (Apple silicon, macOS 26+)."
    exit 0
fi

echo "📦 $(container --version 2>/dev/null)"

if ! container system status &> /dev/null; then
    echo "⚠️ container services are not running. Start them with: container system start"
fi

if [ ! -f "$HOME/.config/container/config.toml" ]; then
    echo "ℹ️ No ~/.config/container/config.toml — container DNS names are not configured. Run '/apple-container init' for setup steps."
fi

exit 0
