#!/bin/bash
set -e

# Determine the directory of this script to locate templates
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")/templates"
TARGET_DIR="${PWD}/infrastructure/terraform"
TARGET_FILE="$TARGET_DIR/backend.tf"

echo "=== Terraform Remote State Backend Setup ==="

read -p "Backend type (s3/gcs/azurerm): " BACKEND_TYPE
case "$BACKEND_TYPE" in
    s3|gcs|azurerm) ;;
    *)
        echo "Unsupported backend type '$BACKEND_TYPE'. Must be one of: s3, gcs, azurerm. Exiting."
        exit 1
        ;;
esac

mkdir -p "$TARGET_DIR"

if [ -f "$TARGET_FILE" ]; then
    read -p "$TARGET_FILE already exists. Overwrite? (y/N) " OVERWRITE
    if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
        echo "Skipping $TARGET_FILE."
        exit 0
    fi
fi

case "$BACKEND_TYPE" in
    s3)
        read -p "S3 bucket name: " BUCKET_NAME
        read -p "State object key (default: terraform.tfstate): " STATE_KEY
        STATE_KEY=${STATE_KEY:-terraform.tfstate}
        read -p "AWS region: " REGION
        read -p "DynamoDB lock table name (default: terraform-locks): " LOCK_TABLE
        LOCK_TABLE=${LOCK_TABLE:-terraform-locks}

        sed -e "s#{{BUCKET_NAME}}#$BUCKET_NAME#g" \
            -e "s#{{STATE_KEY}}#$STATE_KEY#g" \
            -e "s#{{REGION}}#$REGION#g" \
            -e "s#{{LOCK_TABLE}}#$LOCK_TABLE#g" \
            "$TEMPLATE_DIR/backend-s3.tf.tmpl" > "$TARGET_FILE"
        ;;
    gcs)
        read -p "GCS bucket name: " BUCKET_NAME
        read -p "State prefix (default: terraform/state): " STATE_PREFIX
        STATE_PREFIX=${STATE_PREFIX:-terraform/state}

        sed -e "s#{{BUCKET_NAME}}#$BUCKET_NAME#g" \
            -e "s#{{STATE_PREFIX}}#$STATE_PREFIX#g" \
            "$TEMPLATE_DIR/backend-gcs.tf.tmpl" > "$TARGET_FILE"
        ;;
    azurerm)
        read -p "Resource group name: " RESOURCE_GROUP
        read -p "Storage account name: " STORAGE_ACCOUNT
        read -p "Container name (default: tfstate): " CONTAINER_NAME
        CONTAINER_NAME=${CONTAINER_NAME:-tfstate}
        read -p "State blob key (default: terraform.tfstate): " STATE_KEY
        STATE_KEY=${STATE_KEY:-terraform.tfstate}

        sed -e "s#{{RESOURCE_GROUP}}#$RESOURCE_GROUP#g" \
            -e "s#{{STORAGE_ACCOUNT}}#$STORAGE_ACCOUNT#g" \
            -e "s#{{CONTAINER_NAME}}#$CONTAINER_NAME#g" \
            -e "s#{{STATE_KEY}}#$STATE_KEY#g" \
            "$TEMPLATE_DIR/backend-azurerm.tf.tmpl" > "$TARGET_FILE"
        ;;
esac

echo "Created $TARGET_FILE"
echo "Run 'terraform init' from $TARGET_DIR to initialize this backend."
