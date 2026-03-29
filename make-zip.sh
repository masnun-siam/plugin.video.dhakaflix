#!/bin/bash

# Kodi Addon Zip Builder Script
# Creates a properly structured zip file for Kodi addon installation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="plugin.video.dhakaflix"
DESKTOP_PATH="$HOME/Desktop"
ADDON_PATH="$SCRIPT_DIR"

echo "Building Kodi addon zip..."
echo "Source: $ADDON_PATH"
echo "Destination: $DESKTOP_PATH/$PROJECT_NAME.zip"

# Check if source directory exists
if [ ! -d "$ADDON_PATH" ]; then
    echo "Error: Addon directory not found at $ADDON_PATH"
    exit 1
fi

# Check if addon.xml exists (required for Kodi)
if [ ! -f "$ADDON_PATH/addon.xml" ]; then
    echo "Error: addon.xml not found in $ADDON_PATH"
    exit 1
fi

# Create temporary directory for staging
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Create the addon folder inside temp directory
mkdir -p "$TEMP_DIR/$PROJECT_NAME"

# Copy files, excluding unnecessary directories
rsync -av \
    --exclude='.git' \
    --exclude='.gitignore' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.planning' \
    --exclude='CLAUDE.md' \
    --exclude='AGENTS.md' \
    --exclude='.claude' \
    --exclude='.gitnexus' \
    --exclude='.ruff_cache' \
    --exclude='make-zip.sh' \
    "$ADDON_PATH/" "$TEMP_DIR/$PROJECT_NAME/"

# Create the zip file from the temp directory
cd "$TEMP_DIR"
rm -f "$DESKTOP_PATH/$PROJECT_NAME.zip"
zip -r "$DESKTOP_PATH/$PROJECT_NAME.zip" "$PROJECT_NAME/"

# Verify the structure
echo ""
echo "Zip file created successfully!"
echo ""
echo "Contents:"
unzip -l "$DESKTOP_PATH/$PROJECT_NAME.zip" | tail -10

echo ""
echo "✓ Kodi addon zip saved to: $DESKTOP_PATH/$PROJECT_NAME.zip"
