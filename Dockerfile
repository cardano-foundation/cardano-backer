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

ENV BACKER_CONFIG_FILE /config/witroot-config.json
ENV AGENT_CONFIG_FILE /config/agent-config.json
ENV WITROOTS_CONFIG_DIR /usr/local/var/keri/cardano-roots
RUN pip install blockfrost-python~=0.5.2 pycardano~=0.7.3
RUN mkdir /config && \
    ln -s /src/scripts/demo/backer/start_backer.sh /usr/local/bin/cardano-backer && \
    ln -s /src/scripts/demo/backer/start_agent.sh /usr/local/bin/cardano-agent && \
    cp -a /src/scripts/demo/backer/witroot-config.json /config/ && \
    cp -a /src/scripts/demo/backer/agent-config.json /config/

RUN chmod +x /usr/local/bin/cardano*

FROM cardano-base AS cardano-backer
VOLUME /usr/local/var/keri
ENTRYPOINT ["/usr/local/bin/cardano-backer"]

FROM cardano-base AS cardano-agent
ENTRYPOINT ["/usr/local/bin/cardano-agent"]
