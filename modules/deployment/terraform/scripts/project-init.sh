#!/bin/bash
set -e

# Determine the directory of this script to locate templates
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")/templates"
TARGET_DIR="${PWD}/infrastructure/terraform"
ENV_DIR="$TARGET_DIR/environments"

# Escapes a value so it can be safely embedded inside an HCL double-quoted
# string literal: backslash, then the closing quote, then '${' (HCL
# interpolation) so user input can't break out of the string or inject an
# expression into the generated .tf file.
hcl_escape() {
    local s="$1"
    local bs='\' dq='"' interp_open='${' interp_escaped='$${'
    s="${s//$bs/$bs$bs}"
    s="${s//$dq/$bs$dq}"
    s="${s//$interp_open/$interp_escaped}"
    printf '%s' "$s"
}

# Escapes backslash, ampersand, and the '#' delimiter so a value can never
# break out of a sed replacement (or reach GNU sed's `e`/`w` extensions).
sed_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//&/\\&}"
    s="${s//#/\\#}"
    printf '%s' "$s"
}

# Combines both: makes a value safe for the HCL output, then safe to pass
# through sed's replacement parsing to get there.
render_value() {
    sed_escape "$(hcl_escape "$1")"
}

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

# Renders a template file to a target path via direct sed/cat argv calls
# (never eval) with each PLACEHOLDER/value pair pre-escaped by render_value.
# Usage: render_template <template_file> <target_file> [PLACEHOLDER value]...
render_template() {
    local template_file="$1"; shift
    local target_file="$1"; shift

    if [ -f "$target_file" ]; then
        read -p "$target_file already exists. Overwrite? (y/N) " OVERWRITE
        if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
            echo "Skipping $target_file."
            return
        fi
    fi

    if [ "$#" -eq 0 ]; then
        cat "$template_file" > "$target_file"
    else
        local sed_args=()
        while [ "$#" -gt 0 ]; do
            sed_args+=(-e "s#{{$1}}#$(render_value "$2")#g")
            shift 2
        done
        sed "${sed_args[@]}" "$template_file" > "$target_file"
    fi
    echo "Created $target_file"
}

render_template "$TEMPLATE_DIR/main.tf.tmpl" "$TARGET_DIR/main.tf" PROJECT_NAME "$PROJECT_NAME"
render_template "$TEMPLATE_DIR/variables.tf.tmpl" "$TARGET_DIR/variables.tf" PROJECT_NAME "$PROJECT_NAME"
render_template "$TEMPLATE_DIR/outputs.tf.tmpl" "$TARGET_DIR/outputs.tf"
render_template "$TEMPLATE_DIR/versions.tf.tmpl" "$TARGET_DIR/versions.tf"

IFS=',' read -ra ENV_LIST <<< "$ENVIRONMENTS_INPUT"
for ENV in "${ENV_LIST[@]}"; do
    ENV_TRIMMED=$(echo "$ENV" | xargs)
    [ -z "$ENV_TRIMMED" ] && continue

    if [[ ! "$ENV_TRIMMED" =~ ^[A-Za-z0-9_-]+$ ]]; then
        echo "Skipping invalid environment name '$ENV_TRIMMED' (only letters, numbers, hyphens, and underscores are allowed)."
        continue
    fi

    render_template "$TEMPLATE_DIR/environment.tfvars.tmpl" "$ENV_DIR/${ENV_TRIMMED}.tfvars" \
        PROJECT_NAME "$PROJECT_NAME" ENVIRONMENT "$ENV_TRIMMED" OWNER "$OWNER"
done

echo "Terraform project scaffold complete in $TARGET_DIR"
