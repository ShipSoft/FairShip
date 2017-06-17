__author__ = 'Mikhail Hushchyn'

from sklearn.linear_model import LinearRegression
import numpy



################################################## Main class ##########################################################


class FastHough(object):

    def __init__(self,
                 n_tracks=None,
                 min_hits=4,
                 k_size=0.1,
                 b_size=10,
                 k_limits=(-0.3, 0.3),
                 b_limits=(-800, 800),
                 unique_hit_labels=True):
        """
        Track pattern recognition method based on Hough Transform.

        Parameters
        ----------
        n_tracks : int
            Number of tracks to recognize.
        min_hits : int
            Min hits per track to be considered as recognized.
        k_size : int
            Size of k-bin in track parameter space (k, b). Track parametrization: y = k * x + b.
        b_size : int
            Size of b-bin in track parameter space (k, b). Track parametrization: y = k * x + b.
        k_limits : tuple
            Tuple (min, max) of min and max allowable k-values.
        b_limits : tuple
            Tuple (min, max) of min and max allowable b-values.
        unique_hit_labels : boolean
            Is it allowable to take a hit for several tracks of not.
        """


        self.n_tracks = n_tracks
        self.min_hits = min_hits

        self.k_size = k_size
        self.b_size = b_size

        self.k_limits = k_limits
        self.b_limits = b_limits

        self.unique_hit_labels = unique_hit_labels

    def transform(self, x, y):
        """
        This function performs fast Hough Transform.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.

        Return
        ------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        """

        track_inds = []

        for first in range(0, len(x)-1):
            for second in range(first+1, len(x)):

                x1, y1, layer1 = x[first], y[first], x[first]
                x2, y2, layer2 = x[second], y[second], x[second]

                if layer1 == layer2:
                   continue

                #if numpy.abs(x1 - x2) <= 100.:
                #    continue

                k = 1. * (y2 - y1) / (x2 - x1)
                b = y1 - k * x1

                if k >= self.k_limits[0] and k <= self.k_limits[1] and b >= self.b_limits[0] and b <= self.b_limits[1]:

                    one_track_inds = self.hits_in_bin(x, y, k, b)
                    one_track_inds1, one_track_inds2 = self.one_hit_per_layer(one_track_inds,
                                                                              x[one_track_inds],
                                                                              y[one_track_inds],
                                                                              x[one_track_inds],
                                                                              k,
                                                                              b)

                    if len(one_track_inds1) >= self.min_hits:
                        track_inds.append(one_track_inds1)

                    if len(one_track_inds2) >= self.min_hits:
                        track_inds.append(one_track_inds2)

        return numpy.array(track_inds)

    def one_hit_per_layer(self, track_inds, x, y, layer, k, b):
        """
        Drop hits from the same layer. In results, only one hit per layer remains.

        Parameters
        ----------
        track_inds : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        layer : array-like
            Array of layer ids of hits.
        k : float
            Track parameter: y = k * x + b
        b : float
            Track parameter: y = k * x + b

        Return
        ------
        track_inds1 : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        track_inds2 : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        """

        new_track_inds1 = []
        new_track_inds2 = []

        diff = numpy.abs(y - (b + k * x))
        sorted_inds = numpy.argsort(diff)
        used1 = []
        used2 = []

        for i in sorted_inds:

            if layer[i] not in used1:
                new_track_inds1.append(track_inds[i])
                used1.append(layer[i])
            elif layer[i] not in used2:
                new_track_inds2.append(track_inds[i])
                used2.append(layer[i])

        return numpy.array(new_track_inds1), numpy.array(new_track_inds2)


    def hits_in_bin(self, x, y, k_bin, b_bin):
        """
        Counts hits in a bin of track parameter space (b, k).

        Parameters
        ---------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        k_bin : float
            Track parameter: y = k_bin * x + b_bin
        b_bin : float
            Track parameter: y = k_bin * x + b_bin

        Return
        ------
        track_inds : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        """


        b_left = y - (k_bin - 0.5 * self.k_size) * x
        b_right = y - (k_bin + 0.5 * self.k_size) * x

        inds = numpy.arange(0, len(x))

        sel = (b_left >= b_bin - 0.5 * self.b_size) * (b_right <= b_bin + 0.5 * self.b_size) + \
              (b_left <= b_bin + 0.5 * self.b_size) * (b_right >= b_bin - 0.5 * self.b_size)

        track_inds = inds[sel]

        return track_inds



    def get_unique_hit_labels(self, track_inds, n_hits):
        """
        Selects the best track candidates. It supposed that a hit can belong to just one track.

        Parameters
        ----------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        n_hits : int
            Number of hits in an event.

        Return
        ------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        """

        new_track_inds = []
        used = numpy.zeros(n_hits)
        n_tracks = 0


        while 1:

            track_lens = numpy.array([len(i[used[i] == 0]) for i in track_inds])

            if len(track_lens) == 0:
                break

            max_len = track_lens.max()

            if max_len < self.min_hits:
                break

            one_track_inds = track_inds[track_lens == track_lens.max()][0]
            one_track_inds = one_track_inds[used[one_track_inds] == 0]

            used[one_track_inds] = 1
            new_track_inds.append(one_track_inds)

            n_tracks += 1
            if self.n_tracks != None and n_tracks >= self.n_tracks:
                break

        return numpy.array(new_track_inds)

    def remove_duplicates(self, track_inds):
        """
        Removes track duplicates.

        Parameters
        ----------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]

        Return
        ------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        """

        new_track_inds = []

        if len(track_inds) == 0:
            return numpy.array(new_track_inds)

        sorted_track_inds = [numpy.sort(track) for track in track_inds]

        for first_id in range(len(track_inds)-1):

            counter = 0
            first = sorted_track_inds[first_id]

            for second_id in range(first_id+1, len(track_inds)):

                second = sorted_track_inds[second_id]
                if list(first) == list(second):
                    counter += 1

            if counter == 0:
                new_track_inds.append(first)

        new_track_inds.append(sorted_track_inds[-1])

        return numpy.array(new_track_inds)

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
        """
        Runs track pattern recognition. Track parametrization: y = k * x + b.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        sample_weight : array-like
            Hit weights used during the track fit.
        """

        track_inds = self.transform(x, y)

        if self.unique_hit_labels:
            self.track_inds_ = self.get_unique_hit_labels(track_inds, len(x))
        else:
            self.track_inds_ = self.remove_duplicates(track_inds)

        self.tracks_params_ = self.get_tracks_params(x, y, self.track_inds_, sample_weight)

