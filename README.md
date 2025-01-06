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
### `WALLET_ADDRESS_CBORHEX`
 This environmental variable is used by backer to provide the Private Key of spending address as CBOR Hex. Must be an Enterprice address (no Staking part) as PaymentSigningKeyShelley_ed25519. Note that storing private keys in an environmental variable is highly insecure !

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
See [DOCKER.md](docker.md) for instructions on how to deploy using Docker.


## Development

## Creating a local devnet with Yaci DevKit
Yaci DevKit: A set of development tools for building on Cardano by creating a local devnet.

### Pre-requisites

- Docker Compose

### Get Yaci DevKit

#### Download the latest zip from release section

Download the latest zip from [release section](https://github.com/bloxbean/yaci-devkit/releases) and unzip it.

### DevKit Script
You can find `devkit.sh` script under the `bin` folder. This script is used to manage the DevKit containers and Yaci CLI.

```shell
Options:
  start   Start the DevKit containers and CLI.
  stop    Stop the DevKit containers.
  cli     Query the Cardano node in the DevKit container using cardano-cli.
  ssh     Establish an SSH connection to the DevKit container.
  info    Display information about the Dev Node.
  version Display the version of the DevKit.
  help    Display this help message.

```

### To start the DevKit docker compose

To start the DevKit containers and yaci-cli.

```shell
./bin/devkit.sh start
```

**Note:** If you have some **ports** already in use, please make sure the mentioned ports in ```config/env``` file are free.
You can also change the ports in ```config/env``` file. Any changes to ```env``` file will be applied when you restart the docker compose.

### Update config/env file to fund test accounts (Optional)

Update ```env``` file to include your test Cardano addresses to automatically topup Ada.

```
topup_addresses=<address1>:<ada_value>,<address2><ada_value>
```

**Example**

```
topup_addresses=addr_test1qzlwg5c3mpr0cz5td0rvr5rvcgf02al05cqgd2wzv7pud6chpzk4elx4jh2f7xtftjrdxddr88wg6sfszu8r3gktpjtqrr00q9:20000,addr_test1qqwpl7h3g84mhr36wpetk904p7fchx2vst0z696lxk8ujsjyruqwmlsm344gfux3nsj6njyzj3ppvrqtt36cp9xyydzqzumz82:10000
```

**Important:** After updating env file, you need to restart the docker compose using ```devkit.sh stop``` and ```devkit.sh start``` options.

**Note:** You can also use the ``topup`` command in Yaci CLI to fund your test addresses later.

### Enable Ogmios Support
Yaci DevKit bundles Ogmios and Kupo. However, Kupo is not enabled by default. To activate both Ogmios,
set `ogmios_enabled` flag in `env` file to true. Alternatively, you can enable both Ogmios & Kupo support using ``enable-kupomios`` command in Yaci CLI.

### To stop DevKit

Use `devkit.sh` script to stop the DevKit containers.

```shell
./bin/devkit.sh stop
```

### Yaci CLI - Few Key Commands

This section explains a few key commands specific to Yaci CLI.

#### Create a default devnet

```
yaci-cli:>create-node
```
To overwrite data or reset the existing default devnet, use the "-o" flag.
Use --start flag to start the devnet after creation.

```
yaci-cli:>create-node -o
or,
yaci-cli:>create-node -o --start
```

**Known Issue:** Yaci DevKit uses a share folder to store the data on host machine. In some setup, this causes issue due to permission.
If you face similar issue and not able to start the devnet, you can remove ``volumes`` section from ``docker-compose.yml`` file and restart the docker compose.
It should work fine and create the devnet data in the docker container itself. Please check this [issue](https://github.com/bloxbean/yaci-devkit/issues/11) for more details.

##### Create a default devnet node with Conway Era

By default, Yaci DevKit creates a devnet with **Babbage** era. If you want to create a devnet with **Conway** era, use the following command.

```
yaci-cli:>create-node -o --era conway
```

##### Create a devnet with custom slots per epoch
To create devnet with a custom slots per epoch (By default 500 slots/epoch)

**For example:** Create and start a devnet with 30 slots per epoch

```
yaci-cli> create-node -o -e 30 --start

```

Now, you should be in the "devnet" context. To start the devnet, use the "start" command.

```
devnet:default>start
```

**Note** Now, with Yaci Viewer, you can conveniently check the devnet's data right from the browser. Simply open the following URL
in your browser to access the Yaci Viewer.

http://localhost:5173

#### To reset cluster's data

If your devnet gets stuck or you simply want to reset the data and restart with the same configuration, simply use the command "reset".
It will restore your devnet to its initial state, allowing you to continue your development seamlessly.

```
devnet:default>reset
```

#### To stop

```
devnet:default>stop
```

#### To fund a new address

Easily fund your test account with ADA using the "topup" command.

```shell
devnet:default> topup <address> <ada value>
```

#### To check utxos at an address

```shell
devnet:default> utxos <address>
```

#### To get default addresses

```shell
devnet:default> default-addresses
```

#### To check devnet and url info

```shell
devnet:default> info
```

For more details about **Yaci CLI**, please check https://yaci-cli.bloxbean.com .