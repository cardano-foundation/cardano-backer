# Build base images

Run this snippet from the root of this git repository:

```
TARGETS="kli keri cardano-backer cardano-agent"
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
  /src/scripts/demo/backer/generate_cborhex_cardano.py
```
* Setup an `.env` file (you can use `.env.example` file as template) in the root of the git repository and set the `FUNDING_ADDRESS_CBORHEX` using the value from the previous command
* Bring up `cardano-backer` and `cardano-agent`:
```
docker-compose --env-file .env up
```

At this point services should be accesible at these endpoints:

- cardano-backer: http://localhost:5666
- cardano-agent: http://localhost:5972

If you want to run the demo scripts, you can run them by executing this snippet (and replacing the values by the ones shown by the backer):
* `backer_demo-kli.sh`:
```
docker-compose exec cardano-backer bash \
  /src/scripts/demo/backer/backer_demo-kli.sh $BACKER_PREFIX $BACKER_ADDRESS
```
* `backer_demo-agent.sh`:
```
docker-compose exec cardano-agent bash -c '\
  BACKER_URL=http://cardano-backer:5666; \
  /src/scripts/demo/backer/backer_demo-agent.sh $BACKER_PREFIX $BACKER_ADDRESS'
```
