FROM python:3.12 AS base

WORKDIR /src

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN apt update -qq && \
    apt install -y libsodium23

COPY ./ /src
RUN pip3 install -r requirements.txt

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
RUN ln -s /src/scripts/start_backer.sh /usr/local/bin/cardano-backer && \
    ln -s /src/scripts/start_agent.sh /usr/local/bin/cardano-agent

RUN chmod +x /usr/local/bin/cardano*

FROM cardano-base AS cardano-backer
VOLUME /usr/local/var/keri
ENTRYPOINT ["/usr/local/bin/cardano-backer"]

FROM cardano-base AS cardano-agent
RUN apt update -qq && apt install -y jq
ENTRYPOINT ["/usr/local/bin/cardano-agent"]
