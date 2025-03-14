#!/bin/bash

#WALLET_ADDRESS_CBORHEX=5820339f8d1757c2c19ba62146d98400be157cdbbe149a4200bd9cc68ef457c201f8
SPENDING_ADDRESS=addr_test1vrs5guudp8u6ryqmt4etlhkmgcr6qld7lc0y22r73amjtvqsqphu8
TOPUP_AMOUNT=100000

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILE="yaci-cli"

cd $SCRIPT_DIR

if [[ ! -f "$SCRIPT_DIR/$FILE" ]]; then
    bash "$SCRIPT_DIR/download-components.sh"
fi

./yaci-cli <<EOF
download -c node
download -c ogmios
enable-ogmios
create-node -o --start
topup $SPENDING_ADDRESS $TOPUP_AMOUNT
EOF

