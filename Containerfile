FROM ghcr.io/prefix-dev/pixi:0.71.3-noble

WORKDIR /FairShip

COPY pixi.toml pixi.lock /FairShip/
RUN pixi install --locked

COPY . /FairShip
RUN pixi run --locked build

RUN pixi shell-hook -s bash > /entrypoint.sh \
    && echo 'exec "$@"' >> /entrypoint.sh \
    && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
