#!/bin/bash

pkill -9 -f "yaci-cli"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd $SCRIPT_DIR

./yaci-cli <<EOF
exit
EOF

