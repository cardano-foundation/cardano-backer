#!/bin/bash

CONFIG_DIR="scripts"
STORE_DIR="${CONFIG_DIR}/store"
INTERNAL_HOST=${BACKER_INTERNAL_HOST:-localhost}
EXTERNAL_HOST=${BACKER_EXTERNAL_HOST:-localhost}
URL="${BACKER_URL:-http://$EXTERNAL_HOST}"

cat > $CONFIG_DIR/backer.json <<EOF
{
  "transferable": false,
  "wits": [],
  "icount": 1,
  "ncount": 1,
  "isith": "1",
  "nsith": "1"
}
EOF

BACKERS=("wan" "wil" "wes" "wit")
SALTS=("0AB3YW5uLXRoZS13aXRuZXNz" "0AB3aWxsLXRoZS13aXRuZXNz" "0AB3ZXNzLXRoZS13aXRuZXNz" "0AB3aXRuLXRoZS13aXRuZXNz")
PORTS=(5642 5643 5644 5645)
TPORTS=(5632 5633 5634 5635)

for i in {0..3}
do
  cat > $CONFIG_DIR/keri/cf/${BACKERS[$i]}.json <<EOF
{
  "${BACKERS[$i]}": {
    "dt": "$(date -u +"%Y-%m-%dT%H:%M:%S.000000+00:00")",
    "curls": ["tcp://${INTERNAL_HOST}:${TPORTS[$i]}/", "${URL}:${PORTS[$i]}"]
  },
  "dt": "$(date -u +"%Y-%m-%dT%H:%M:%S.000000+00:00")",
  "iurls": [
  ]
}
EOF
kli init --name ${BACKERS[$i]} --nopasscode  --config-dir $CONFIG_DIR --config-file $CONFIG_DIR/keri/cf/${BACKERS[$i]}.json --base $STORE_DIR/${BACKERS[$i]} -s ${SALTS[$i]}

kli incept --name ${BACKERS[$i]} --alias ${BACKERS[$i]} --config $CONFIG_DIR --file backer_cfg.json --base $STORE_DIR/${BACKERS[$i]}

echo ""
echo "Starting backer ${BACKERS[$i]} on port ${PORTS[$i]} and tport ${TPORTS[$i]}"
echo ""

backer start --name ${BACKERS[$i]}  --alias ${BACKERS[$i]} -T ${TPORTS[$i]} -H ${PORTS[$i]} --ledger cardano --base $STORE_DIR/${BACKERS[$i]} &

sleep 5

done
# pkill -f "bin/backer.*start"
