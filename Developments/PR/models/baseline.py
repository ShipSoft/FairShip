__author__ = 'mikhail91'

import numpy
from sklearn.linear_model import LinearRegression

class Baseline(object):

    def __init__(self, nrwant, window):

        self.nrwant = nrwant
        self.window = window

    def sort_hits(self, x, y):

        hits = {}
        xlayer = {}
        indexes = numpy.arange(len(x))

        for num, ax in enumerate(numpy.unique(x)):
            hits[ax] = indexes[x == ax]
            xlayer[num] = ax

        return xlayer, hits

    def get_tracks_params(self, x, y, track_inds, sample_weight=None):
        """
        Estimates track parameters y = k * x + b for the recognized tracks.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        track_inds : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        sample_weight : array-like
            Hit weights used during the track fit.

        Return
        ------
        tracks_params : array-like
            Track parameters [k, b].
        """

        tracks_params = []

        if len(track_inds) == 0:
            return []

        for track in track_inds:

            x_track = x[track]
            y_track = y[track]

            if sample_weight != None:
                sample_weight_track = sample_weight[track]
            else:
                sample_weight_track = None

            lr = LinearRegression(copy_X=False)
            lr.fit(x_track.reshape(-1,1), y_track, sample_weight_track)

            params = list(lr.coef_) + [lr.intercept_]
            tracks_params.append(params)

        return numpy.array(tracks_params)

    def fit(self, x, y, sample_weight=None):

        track_inds = []
        track_params = []

        xlayer, hits = self.sort_hits(self, x, y)
        used = numpy.zeros(len(x))

        planes=xlayer.keys()
        planes.sort()
        i_1=planes[0]
        i_2=planes[len(planes)-1]
        ndrop=len(planes) - self.nrwant

        nrtracks=0

        # loop over maxnr hits, to max-ndrop
        for nhitw in range(i_2-i_1+1, i_2-i_1-ndrop, -1):

            # nhitw: wanted number of hits when looking for a track
            for idrop in range(ndrop):

                # only start if wanted nr hits <= the nr of planes
                nrhitmax = i_2 - i_1 - idrop + 1

                if nhitw <= nrhitmax:

                    for k in range(idrop+1):

                        # calculate the id of the first and last plane for this try.
                        ifirst = i_1 + k
                        ilast = i_2 - (idrop - k)

                        # now loop over hits in first/last planes, and construct line
                        dx = xlayer[ilast] - xlayer[ifirst]

                        # hits in first plane
                        for ifr in hits[xlayer[ifirst]]:

                            # has this hit been used already for a track: skip
                            if used[ifr] == 0:

                                yfirst = y[ifr]

                                # hits in last plane
                                for il in hits[xlayer[ilast]]:

                                    # has this hit been used already for a track: skip
                                    if used[il] == 0:

                                        ylast = y[il]

                                        nrhitsfound = 2
                                        tancand = (ylast - yfirst) / dx

                                        # fill temporary hit list for track-candidate with -1
                                        trcand=(i_2 - i_1 + 2) * [-1]

                                        # loop over in between planes
                                        for inbetween in range(ifirst + 1, ilast):

                                            # can wanted number of hits be satisfied?
                                            if nrhitsfound + ilast - inbetween >= nhitw:

                                                # calculate candidate hit
                                                ywinlow = yfirst + tancand * (xlayer[inbetween] - xlayer[ifirst]) - self.window

                                                for im in hits[xlayer[inbetween]]:

                                                    # has this hit been used?
                                                    if used[im] == 0:

                                                        yin= y[im]

                                                        # hit belwo window, try next one
                                                        if yin > ywinlow:

                                                            # if hit larger than upper edge of window: goto next plane
                                                            if yin > ywinlow + 2 * self.window:
                                                                break

                                                            # hit found, do administation
                                                            if trcand[inbetween] == -1:
                                                                nrhitsfound += 1

                                                            trcand[inbetween] = im

                                        # looped over in between planes, collected enough hits?
                                        if nrhitsfound == nhitw:

                                            atrack = []

                                            # mark used hits
                                            trcand[ifirst] = ifr
                                            trcand[ilast] = il

                                            for i in range(ifirst, ilast + 1):

                                                if trcand[i] >= 0:
                                                    used[trcand[i]] = 1
                                                    atrack.append(trcand[i])

                                            # store the track
                                            nrtracks += 1

                                            track_inds.append(atrack)


        self.track_inds_ = numpy.array(track_inds)
        self.tracks_params_ = self.get_tracks_params(x, y, self.track_inds_, sample_weight)
