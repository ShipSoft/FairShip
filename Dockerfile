FROM olantwin/ship-base:20180627-online

ADD . /FairShip

RUN aliBuild -c shipdist/ --defaults fairship build FairShip --no-local ROOT \
	&& aliBuild clean --aggressive-cleanup
