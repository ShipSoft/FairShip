FROM ghcr.io/prefix-dev/pixi:0.72.2-noble

WORKDIR /FairShip

COPY pixi.toml pixi.lock /FairShip/
# Remove the rattler download cache in the same layer that creates it, so the
# multi-GB package tarballs don't get baked into the image.
RUN pixi install --locked && rm -rf ~/.cache/rattler

COPY . /FairShip
RUN pixi run --locked build

RUN echo '#!/bin/bash' > /entrypoint.sh \
    && pixi shell-hook -s bash >> /entrypoint.sh \
    && echo 'exec "$@"' >> /entrypoint.sh \
    && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
