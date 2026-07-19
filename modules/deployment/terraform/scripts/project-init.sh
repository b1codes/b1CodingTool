#!/bin/bash
set -e

# Determine the directory of this script to locate templates
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")/templates"
TARGET_DIR="${PWD}/infrastructure/terraform"
ENV_DIR="$TARGET_DIR/environments"

echo "=== Terraform Root Project Scaffold ==="

read -p "Project name: " PROJECT_NAME
if [ -z "$PROJECT_NAME" ]; then
    echo "Project name is required. Exiting."
    exit 1
fi

read -p "Owner (team or person, default: platform-team): " OWNER
OWNER=${OWNER:-platform-team}

read -p "Environments (comma-separated, default: dev,staging,prod): " ENVIRONMENTS_INPUT
ENVIRONMENTS_INPUT=${ENVIRONMENTS_INPUT:-dev,staging,prod}

mkdir -p "$TARGET_DIR"
mkdir -p "$ENV_DIR"

write_file() {
    local target_file="$1"
    local render_cmd="$2"

    if [ -f "$target_file" ]; then
        read -p "$target_file already exists. Overwrite? (y/N) " OVERWRITE
        if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
            echo "Skipping $target_file."
            return
        fi
    fi

    eval "$render_cmd" > "$target_file"
    echo "Created $target_file"
}

write_file "$TARGET_DIR/main.tf" \
    "sed -e \"s#{{PROJECT_NAME}}#$PROJECT_NAME#g\" \"$TEMPLATE_DIR/main.tf.tmpl\""

write_file "$TARGET_DIR/variables.tf" \
    "sed -e \"s#{{PROJECT_NAME}}#$PROJECT_NAME#g\" \"$TEMPLATE_DIR/variables.tf.tmpl\""

write_file "$TARGET_DIR/outputs.tf" \
    "cat \"$TEMPLATE_DIR/outputs.tf.tmpl\""

write_file "$TARGET_DIR/versions.tf" \
    "cat \"$TEMPLATE_DIR/versions.tf.tmpl\""

IFS=',' read -ra ENV_LIST <<< "$ENVIRONMENTS_INPUT"
for ENV in "${ENV_LIST[@]}"; do
    ENV_TRIMMED=$(echo "$ENV" | xargs)
    [ -z "$ENV_TRIMMED" ] && continue

    write_file "$ENV_DIR/${ENV_TRIMMED}.tfvars" \
        "sed -e \"s#{{PROJECT_NAME}}#$PROJECT_NAME#g\" -e \"s#{{ENVIRONMENT}}#$ENV_TRIMMED#g\" -e \"s#{{OWNER}}#$OWNER#g\" \"$TEMPLATE_DIR/environment.tfvars.tmpl\""
done

echo "Terraform project scaffold complete in $TARGET_DIR"
