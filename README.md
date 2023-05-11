# KERI Registrar Backer on Cardano
A KERI witness that anchors key events on Cardano blockchain.

## Feaures
* Cardano Address is derived from the same Ed25519 seed (private key) used to derive the prefix of the backer
* Anchoring KELs from multiple prefixes
* Queue events during a period of time to allow several block confirmations as a safety meassure
* Optional funding address to fund the backer address

## Previous and related work
*  [keri-roots](https://github.com/roots-id/keri-roots)
* original `keripy` [PR](https://github.com/WebOfTrust/keripy/pull/418)

## Installation
```
pip install -e .
```
Check installation and available commands:
```
$ backer --help
usage: backer [-h] command ...

options:
  -h, --help  show this help message and exit

subcommands:

  command
    info      Display registrar backer information
    query     Query KEL on ledger for a given prefix
    start     Runs KERI backer controller
```

## Start script example
```
./tests/start_backer.sh
```
Check variables and environmental variables that you can pass to configure the backer.

## Environment variables
### `BLOCKFROST_API_KEY`

API KEY from [Blockfrost](https://blockfrost.io). It's the only `REQUIRED` variable and it's needed to interact with the Cardano blockchain. Block Frost provide a free tier service with limits. Additionally, you can select Cardano mainnet or a testnet.

Be aware that the Backer Cardano address needs to be funded (transfer ADA or tADA to it). If you are using the testnet, you can fund it at [Testnets faucet](https://docs.cardano.org/cardano-testnet/tools/faucet).

### `FUNDING_ADDRESS_CBORHEX`
 This is an `OPTIONAL` variable to provide the Private Key of funding address as CBOR Hex. Must be an Enterprice address (no Staking part) as PaymentSigningKeyShelley_ed25519. Note that storing private keys in an environmental variable is highly insecure !

### `BACKER_CONFIG_DIR`
This environmental variable is used by `start_backer.sh` script to specify the directory to place the configuration files.

### `BACKER_STORE_DIR`
This environmental variable is used by `start_backer.sh` script to specify the directory to create the database and keystore.

### `BACKER_URL`
This environmental variable is used by `start_backer.sh` script to specify the URL of the backer needed to resolve `OOBI` and to receive queries from the agents.

### `BACKER_PORT`
This environmental variable is used by `start_backer.sh` script to specify the PORT of the backer needed to resolve `OOBI` and to receive queries from the agents.

### `BACKER_SALT`
This environmental variable is used by `start_backer.sh` script that passes it to the `kli init` as a `SALT` parameter. It's a qualified base64 salt for creating key pairs, that means that you can regenerate a backer with same AID and Cardano address.


## Docker
```
docker build -f ./Dockerfile .  -t cardano-backer   // use --platform=linux/amd64 if needed
docker run -i -t -p 5666:5666 -e BLOCKFROST_API_KEY={API KEY} cardano-backer
```

