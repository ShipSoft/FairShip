# Base image maintained at https://github.com/SND-LHC/snd-base and available
# on the CERN gitlab registry: https://gitlab-registry.cern.ch/olantwin/snd-base/
#
# Prebuilt images available on Docker Hub at:
# https://gitlab-registry.cern.ch/olantwin/sndsw/
FROM gitlab-registry.cern.ch/olantwin/snd-base:201214

# Copy sndsw scripts
COPY . /sndsw

# Build sndsw
RUN aliBuild -c snddist/ build sndsw --no-local ROOT

# Setup environment. Setup the command that will be invoked when your docker
# image is run. Note that this requires running with `docker run -t` so that
# `alienv` detects an interactive terminal.
ENTRYPOINT alienv enter --shellrc sndsw/latest
