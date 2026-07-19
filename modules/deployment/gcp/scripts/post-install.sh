#!/bin/bash
set -e

# This script is executed from the project root.
# The script itself is located in .agent/modules/gcp/scripts/post-install.sh

INFRA_DIR="infrastructure/gcp"

echo "Initializing GCP deployment infrastructure structure..."

if [ ! -d "$INFRA_DIR" ]; then
    mkdir -p "$INFRA_DIR/base"
    mkdir -p "$INFRA_DIR/modules"
    mkdir -p "$INFRA_DIR/services"
    echo "Created $INFRA_DIR directory structure."
else
    echo "$INFRA_DIR already exists, skipping creation."
fi

echo "GCP module setup complete."
