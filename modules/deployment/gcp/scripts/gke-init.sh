#!/bin/bash
set -e

# Determine the directory of this script to locate templates
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")/templates"
TARGET_DIR="${PWD}/infrastructure/gcp/services"

echo "=== GCP GKE Manifest Setup ==="

read -p "App name: " APP_NAME
if [ -z "$APP_NAME" ]; then
    echo "App name is required. Exiting."
    exit 1
fi

read -p "Container image (e.g. gcr.io/PROJECT/IMAGE:TAG): " IMAGE
IMAGE=${IMAGE:-gcr.io/PROJECT_ID/$APP_NAME:latest}

read -p "Container port (default: 8080): " CONTAINER_PORT
CONTAINER_PORT=${CONTAINER_PORT:-8080}

read -p "Environment (default: dev): " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-dev}

mkdir -p "$TARGET_DIR"

for KIND in deployment service; do
    TARGET_FILE="$TARGET_DIR/${APP_NAME}-k8s-${KIND}.yaml"
    if [ -f "$TARGET_FILE" ]; then
        read -p "$TARGET_FILE already exists. Overwrite? (y/N) " OVERWRITE
        if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
            echo "Skipping $TARGET_FILE."
            continue
        fi
    fi

    sed -e "s/{{APP_NAME}}/$APP_NAME/g" \
        -e "s#{{IMAGE}}#$IMAGE#g" \
        -e "s/{{CONTAINER_PORT}}/$CONTAINER_PORT/g" \
        -e "s/{{ENVIRONMENT}}/$ENVIRONMENT/g" \
        "$TEMPLATE_DIR/k8s-${KIND}.yaml.tmpl" > "$TARGET_FILE"

    echo "Created $TARGET_FILE"
done

echo "Deploy with: kubectl apply -f $TARGET_DIR/${APP_NAME}-k8s-deployment.yaml -f $TARGET_DIR/${APP_NAME}-k8s-service.yaml"
