#!/bin/bash
# Determine OS type
OS_TYPE="$(uname -s)"
case "$OS_TYPE" in
    Linux*)   DOWNLOAD_URL="https://github.com/bloxbean/yaci-devkit/releases/download/v0.11.0-beta1/yaci-cli-0.11.0-beta1-linux-X64.zip" ;;
    Darwin*)  DOWNLOAD_URL="https://github.com/bloxbean/yaci-devkit/releases/download/v0.11.0-beta1/yaci-cli-0.11.0-beta1-macos-ARM64.zip" ;;
    *)        echo "Unsupported OS: $OS_TYPE"; exit 1 ;;
esac
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILE="yaci-cli"
TMP_DIR="$(mktemp -d)"
ZIP_FILE="$TMP_DIR/yaci-cli.zip"
cd "$SCRIPT_DIR"
if [[ ! -f "$SCRIPT_DIR/$FILE" ]]; then
    echo "Downloading $FILE for $OS_TYPE..."
    if command -v curl &> /dev/null; then
        curl -L -o "$ZIP_FILE" "$DOWNLOAD_URL"
    elif command -v wget &> /dev/null; then
        wget --no-check-certificate -O "$ZIP_FILE" "$DOWNLOAD_URL"
    else
        echo "Error: curl or wget is required to download files." >&2
        exit 1
    fi
    # Verify download
    if [[ ! -s "$ZIP_FILE" ]]; then
        echo "Error: Downloaded file is empty or failed to download!" >&2
        rm -f "$ZIP_FILE"
        exit 1
    fi
    echo "Extracting $ZIP_FILE..."
    if ! unzip -o "$ZIP_FILE" -d "$TMP_DIR"; then
        echo "Error: Failed to unzip file!" >&2
        exit 1
    fi
    echo "Moving $FILE to $SCRIPT_DIR..."
    mv "$TMP_DIR/yaci-cli-0.11.0-beta1/$FILE" "$SCRIPT_DIR/" || { echo "Error: Failed to move $FILE"; exit 1; }
    chmod +x "$SCRIPT_DIR/$FILE"
    echo "Cleaning up..."
    rm -rf "$TMP_DIR"
fi
cd "$SCRIPT_DIR"
./yaci-cli <<EOF
download -c node
download -c ogmios
exit
EOF