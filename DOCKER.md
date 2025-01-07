# Build base images

Run this snippet from the root of this git repository:

```
TARGETS="kli keri cardano-backer"
for target in ${TARGETS}
do
  docker build \
    --target ${target} \
    -t keripy/${target} .
done
```

# Run

* Run `kli`:
`docker run -it keripy/kli --help`

# Run cardano-backer

* Generate a funding address and fund it using the [testnet](https://docs.cardano.org/cardano-testnet/tools/faucet):
```
docker run -it --rm \
  --entrypoint=python \
  keripy/cardano-backer \
  /src/scripts/generate_funding_cborhex_cardano.py
```
* Setup an `.env` file (you can use `.env.example` file as template) in the root of the git repository and set the `WALLET_ADDRESS_CBORHEX` using the value from the previous command
* Bring up `cardano-backer`:
```
docker-compose --env-file .env up
```

At this point services should be accesible at these endpoints:

- cardano-backer: http://localhost:5666

If you want to run the demo scripts, you can run them by executing this snippet (and replacing the values by the ones shown by the backer):
* `backer_demo-kli.sh`:
```
docker-compose exec cardano-backer bash \
  /src/scripts/backer_demo-kli.sh $BACKER_PREFIX $BACKER_ADDRESS
```

# Production deployment

Edit `docker-compose-traefik.yaml` to deploy on a machine using a domain.
`BACKER_EXTERNAL_HOST` can remain as `localhost` (default) as traefik can handle the routing externally.
