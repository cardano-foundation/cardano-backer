FROM python:3.13 AS base

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
RUN apt update -qq && \
    apt install -y jq && \
    apt clean 
WORKDIR $CONFIG_DIR
RUN apt update -qq && apt install -y jq && apt clean
RUN ln -s /src/scripts/start_backer.sh /usr/local/bin/cardano-backer
RUN chmod +x /usr/local/bin/cardano*

FROM cardano-base AS cardano-backer
VOLUME /usr/local/var/keri
ENTRYPOINT ["/usr/local/bin/cardano-backer"]
