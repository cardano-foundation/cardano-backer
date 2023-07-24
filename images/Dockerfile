FROM python:3.10.4

WORKDIR /code

COPY ./ /code

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"

RUN apt-get update

RUN apt-get install -y libsodium-dev pkg-config

RUN pip install --no-cache-dir --upgrade -e .

CMD "/code/scripts/start_backer.sh"