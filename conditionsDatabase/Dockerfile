# Example Dockerfile that builds a FairSHiP image with a local MongoDB server
#
# Base image maintained at https://github.com/olantwin/ship-base and available
# on Docker Hub: https://hub.docker.com/r/olantwin/ship-base/
#
# Prebuilt images available on Docker Hub at:
# https://hub.docker.com/r/olantwin/fairship/
FROM olantwin/ship-base:200213-2018

# Copy FairShip scripts
COPY . /FairShip

# Build FairShip
RUN aliBuild -c shipdist/ --defaults fairship-2018 build FairShip --no-local ROOT

# Install MongoDB
RUN echo -e "[mongodb-org-4.2] \n\
name=MongoDB Repository \n\
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/4.2/x86_64/ \n\
gpgcheck=1 \n\
enabled=1 \n\
gpgkey=https://www.mongodb.org/static/pgp/server-4.2.asc" \
>> /etc/yum.repos.d/mongodb-org-4.2.repo \
&& yum install -y mongodb-org

# Install Python dependencies
RUN cd ./FairShip/conditionsDatabase \
	&& pip install -r requirements.txt

# Setup environment. Setup the command that will be invoked when your docker
# image is run. Note that this requires running with `docker run -t` so that
# `alienv` detects an interactive terminal.
ENTRYPOINT alienv enter --shellrc FairShip/latest
