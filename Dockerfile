# Base image maintained at https://github.com/olantwin/ship-base and available
# on Docker Hub: https://hub.docker.com/r/olantwin/ship-base/
#
# Prebuilt images available on Docker Hub at:
# https://hub.docker.com/r/olantwin/fairship/
FROM olantwin/ship-base:191114

# Copy FairShip scripts
COPY . /FairShip

# Build FairShip
RUN aliBuild -c shipdist/ --defaults fairship build FairShip --no-local ROOT

# Setup environment. Setup the command that will be invoked when your docker
# image is run. Note that this requires running with `docker run -t` so that
# `alienv` detects an interactive terminal.
ENTRYPOINT alienv enter --shellrc FairShip/latest
