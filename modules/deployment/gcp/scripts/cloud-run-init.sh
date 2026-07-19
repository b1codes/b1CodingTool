#!/bin/bash
set -e

# Determine the directory of this script to locate templates
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")/templates"
TARGET_DIR="${PWD}/infrastructure/gcp/services"

echo "=== GCP Cloud Run Service Setup ==="

read -p "Service name: " SERVICE_NAME
if [ -z "$SERVICE_NAME" ]; then
    echo "Service name is required. Exiting."
    exit 1
fi

read -p "Container image (e.g. gcr.io/PROJECT/IMAGE:TAG): " IMAGE
IMAGE=${IMAGE:-gcr.io/PROJECT_ID/$SERVICE_NAME:latest}

read -p "Container port (default: 8080): " CONTAINER_PORT
CONTAINER_PORT=${CONTAINER_PORT:-8080}

read -p "Environment (default: dev): " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-dev}

mkdir -p "$TARGET_DIR"
TARGET_FILE="$TARGET_DIR/${SERVICE_NAME}-cloudrun-service.yaml"

if [ -f "$TARGET_FILE" ]; then
    read -p "$TARGET_FILE already exists. Overwrite? (y/N) " OVERWRITE
    if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
        echo "Skipping."
        exit 0
    fi
fi

sed -e "s/{{SERVICE_NAME}}/$SERVICE_NAME/g" \
    -e "s#{{IMAGE}}#$IMAGE#g" \
    -e "s/{{CONTAINER_PORT}}/$CONTAINER_PORT/g" \
    -e "s/{{ENVIRONMENT}}/$ENVIRONMENT/g" \
    "$TEMPLATE_DIR/cloud-run-service.yaml.tmpl" > "$TARGET_FILE"

echo "Created $TARGET_FILE"
echo "Deploy with: gcloud run services replace $TARGET_FILE --region=<REGION>"
