FROM olantwin/ship-base:20180627-online

# Copy FairShip scripts
COPY . /FairShip

# Build FairShip
RUN aliBuild -c shipdist/ --defaults fairship build FairShip --no-local ROOT && aliBuild clean --aggressive-cleanup

# Additional library for OpenGL
RUN yum install -y mesa-dri-drivers

# Fix problems with fonts
RUN yum install -y dejavu-lgc-sans-fonts

# Setup environment. Setup the command that will be invoked when your docker image is run.
ENTRYPOINT alienv enter --shellrc FairShip/latest
