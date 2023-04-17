FROM python:3.10 AS base

WORKDIR /src
COPY ./ /src

RUN apt update -qq && \
    apt install -y libsodium23 && \
    pip3 install -r requirements.txt

# kli binary image
FROM base AS kli

ENTRYPOINT ["kli"]

# keri binary image
FROM base AS keri

ENTRYPOINT ["keri"]

# cardano-backer

FROM kli AS cardano-base

ENV CONFIG_DIR /usr/local/var/keri
WORKDIR $CONFIG_DIR
RUN pip install blockfrost-python~=0.5.2 pycardano~=0.7.3
RUN ln -s /src/scripts/demo/backer/start_backer.sh /usr/local/bin/cardano-backer && \
    ln -s /src/scripts/demo/backer/start_agent.sh /usr/local/bin/cardano-agent

RUN chmod +x /usr/local/bin/cardano*

FROM cardano-base AS cardano-backer
VOLUME /usr/local/var/keri
ENTRYPOINT ["/usr/local/bin/cardano-backer"]

FROM cardano-base AS cardano-agent
RUN apt update -qq && apt install -y jq
ENTRYPOINT ["/usr/local/bin/cardano-agent"]
