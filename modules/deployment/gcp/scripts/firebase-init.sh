#!/bin/bash
set -e

# Determine the directory of this script to locate templates
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")/templates"
TARGET_DIR="${PWD}"

echo "=== GCP Firebase Setup ==="

read -p "Firebase project ID: " PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    echo "Project ID is required. Exiting."
    exit 1
fi

read -p "Public directory for Hosting (default: public): " PUBLIC_DIR
PUBLIC_DIR=${PUBLIC_DIR:-public}

FIREBASE_JSON="$TARGET_DIR/firebase.json"
FIREBASERC="$TARGET_DIR/.firebaserc"

for TARGET_FILE in "$FIREBASE_JSON" "$FIREBASERC"; do
    if [ -f "$TARGET_FILE" ]; then
        read -p "$TARGET_FILE already exists. Overwrite? (y/N) " OVERWRITE
        if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
            echo "Skipping $TARGET_FILE."
            continue
        fi
    fi

    if [ "$TARGET_FILE" = "$FIREBASE_JSON" ]; then
        sed "s#{{PUBLIC_DIR}}#$PUBLIC_DIR#g" "$TEMPLATE_DIR/firebase.json.tmpl" > "$FIREBASE_JSON"
    else
        sed "s/{{PROJECT_ID}}/$PROJECT_ID/g" "$TEMPLATE_DIR/firebaserc.tmpl" > "$FIREBASERC"
    fi
    echo "Created $TARGET_FILE"
done

echo "Deploy with: firebase deploy --project $PROJECT_ID"
