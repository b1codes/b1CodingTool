#!/bin/bash
set -e

# This script is executed from the project root.
# The script itself is located in .agent/modules/terraform/scripts/post-install.sh

INFRA_DIR="infrastructure/terraform"

echo "Initializing Terraform infrastructure structure..."

if [ ! -d "$INFRA_DIR" ]; then
    mkdir -p "$INFRA_DIR/modules"
    mkdir -p "$INFRA_DIR/environments"
    echo "Created $INFRA_DIR directory structure."
else
    echo "$INFRA_DIR already exists, skipping creation."
fi

echo "Terraform module setup complete."
