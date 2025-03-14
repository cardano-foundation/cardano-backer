#!/bin/bash

DOWNLOAD_URL="https://github.com/bloxbean/yaci-devkit/releases/download/v0.10.2/yaci-cli-0.10.2-linux-X64.zip"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILE="yaci-cli"
TMP_DIR="/tmp/yaci"
ZIP_FILE="$TMP_DIR/yaci-cli.zip"

cd $SCRIPT_DIR

if [[ ! -f "$SCRIPT_DIR/$FILE" ]]; then
    mkdir -p "$TMP_DIR"

    echo "Downloading $FILE..."
    wget --no-check-certificate -O "$ZIP_FILE" "$DOWNLOAD_URL"

    echo "Extracting $ZIP_FILE..."
    unzip -o "$ZIP_FILE" -d "$TMP_DIR"

    echo "Moving $FILE to $SCRIPT_DIR..."
    mv "$TMP_DIR/yaci-cli-0.10.2/$FILE" "$SCRIPT_DIR/"

    chmod +x "$SCRIPT_DIR/$FILE"

    echo "Cleaning up..."
    rm -rf "$TMP_DIR"
fi

cd $SCRIPT_DIR

./yaci-cli <<EOF
download -c node
download -c ogmios
exit
EOF

