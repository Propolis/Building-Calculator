#!/bin/bash
# Installation script for Building Calculator QGIS plugin

# Determine QGIS plugins directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    PLUGINS_DIR="$HOME/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    PLUGINS_DIR="$HOME/.local/share/QGIS/QGIS3/profiles/default/python/plugins"
else
    # Windows (Git Bash)
    PLUGINS_DIR="$APPDATA/QGIS/QGIS3/profiles/default/python/plugins"
fi

PLUGIN_NAME="building_calculator"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/$PLUGIN_NAME"

echo "Installing Building Calculator plugin..."
echo "Source: $SOURCE_DIR"
echo "Destination: $PLUGINS_DIR/$PLUGIN_NAME"

# Create plugins directory if it doesn't exist
mkdir -p "$PLUGINS_DIR"

# Remove old version if exists
if [ -d "$PLUGINS_DIR/$PLUGIN_NAME" ]; then
    echo "Removing old version..."
    rm -rf "$PLUGINS_DIR/$PLUGIN_NAME"
fi

# Copy plugin
cp -r "$SOURCE_DIR" "$PLUGINS_DIR/"

echo ""
echo "✅ Plugin installed successfully!"
echo ""
echo "Next steps:"
echo "1. Restart QGIS"
echo "2. Go to: Plugins → Manage and Install Plugins"
echo "3. Find 'Building Calculator' and enable it"
echo "4. The plugin icon should appear in the toolbar"
