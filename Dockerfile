FROM olantwin/ship-base:20180528

ADD . /FairShip

RUN aliBuild -c shipdist/ --defaults fairship build FairShip --no-local ROOT \
	&& aliBuild clean --aggressive-cleanup
