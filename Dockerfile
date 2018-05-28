FROM olantwin/ship-base:20180528

RUN git clone https://github.com/ShipSoft/FairShip.git

RUN aliBuild -c shipdist/ --defaults fairship build FairShip --no-local ROOT \
	&& aliBuild clean --aggressive-cleanup
