FROM python:3.13 AS base

WORKDIR /backer

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN apt update -qq && \
    apt install -y libsodium23

COPY requirements.txt setup.py ./
RUN mkdir /backer/src
RUN pip3 install -r requirements.txt

COPY ./ ./

RUN PYTHON_LIB_PATH=$(python3.13 -c "import ogmios.model.cardano_model as m; print(m.__file__)") && \
    sed -i "/class Era2(Enum):/a \ \ \ \ conway = 'conway'" "$PYTHON_LIB_PATH"

FROM base AS cardano-base
ENV CONFIG_DIR /usr/local/var/keri
RUN apt update -qq && \
    apt install -y jq && \
    apt clean 
WORKDIR $CONFIG_DIR
RUN apt update -qq && apt install -y jq && apt clean
RUN ln -s /backer/scripts/start_backer.sh /usr/local/bin/cardano-backer
RUN chmod +x /usr/local/bin/cardano*


FROM cardano-base AS cardano-backer
VOLUME /usr/local/var/keri
ENTRYPOINT ["/usr/local/bin/cardano-backer"]
