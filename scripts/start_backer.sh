#!/bin/bash

CONFIG_DIR="${BACKER_CONFIG_DIR:-$(pwd)}"
STORE_DIR="${BACKER_STORE_DIR:-$(pwd)/store}"
INTERNAL_HOST=${BACKER_INTERNAL_HOST:-localhost}
EXTERNAL_HOST=${BACKER_EXTERNAL_HOST:-localhost}
URL="${BACKER_URL:-http://$EXTERNAL_HOST}"
PORT="${BACKER_PORT:-5666}"
if [[ -z "${BACKER_SALT}" ]]; then
  SALT=""
else
  SALT="--salt ${BACKER_SALT}"
fi

mkdir -p $CONFIG_DIR/keri/cf
cat > $CONFIG_DIR/keri/cf/backer.json <<EOF
{
  "backer": {
    "dt": "$(date -u +"%Y-%m-%dT%H:%M:%S.000000+00:00")",
    "curls": ["tcp://${INTERNAL_HOST}:$((PORT-1))/", "${URL}:${PORT}"]
  },
  "dt": "$(date -u +"%Y-%m-%dT%H:%M:%S.000000+00:00")",
  "iurls": [
  ]
}
EOF

cat > $CONFIG_DIR/backer_cfg.json <<EOF
{
  "transferable": false,
  "wits": [],
  "icount": 1,
  "ncount": 1,
  "isith": "1",
  "nsith": "1"
}
EOF

kli init --name backer --nopasscode  --config-dir $CONFIG_DIR --config-file backer --base $STORE_DIR $SALT

kli incept --name backer --alias backer --config $CONFIG_DIR --file backer_cfg.json --base $STORE_DIR 

backer start --name backer  --alias backer -H $PORT --ledger cardano --base $STORE_DIR 