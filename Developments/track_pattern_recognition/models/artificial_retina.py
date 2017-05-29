__author__ = 'mikhail91'

import numpy
from scipy.optimize import minimize


class ArtificialRetina(object):

    def __init__(self,
                 n_tracks,
                 min_hits,
                 residuals_threshold,
                 sigma,
                 k_size=0.1,
                 b_size=10,
                 k_limits=(-0.3, 0.3),
                 b_limits=(-800, 800),
                 unique_hit_labels=True):
        """
        Artificial Retina method of track pattern recognition.

        Parameters
        ----------
        n_tracks : int
            Number of tracks to recognize.
        min_hits : int
            Min hits per track to be considered as recognized.
        residuals_threshold : float
            Max hit distance from a track.
        sigma : float
            Standard deviation of hit form a track.
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
        self.sigma = sigma
        self.residuals_threshold = residuals_threshold

        self.k_size = k_size
        self.b_size = b_size

        self.k_limits = k_limits
        self.b_limits = b_limits

        self.unique_hit_labels = unique_hit_labels

        self.tracks_params_ = None
        self.track_inds_ = None

    def retina_func(self, track_prams, x, y, sigma, sample_weight=None):
        """
        Calculates the artificial retina function value.

        Parameters
        ----------
        track_prams : array-like
            Track parameters [k, b].
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        sigma : float
            Standard deviation of hit form a track.
        sample_weight : array-like
            Hit weights used during the track fit.

        Retunrs
        -------
        retina : float
            Negative value of the artificial retina function.
        """

        rs = track_prams[0] * x + track_prams[1] - y


        if sample_weight == None:
            exps = numpy.exp(- (rs/sigma)**2)
        else:
            exps = numpy.exp(- (rs/sigma)**2) * sample_weight


        retina = exps.sum()

        return -retina

    def retina_grad(self, track_prams, x, y, sigma, sample_weight=None):
        """
        Calculates the artificial retina gradient.

        Parameters
        ----------
        track_prams : array-like
            Track parameters [k, b].
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        sigma : float
            Standard deviation of hit form a track.
        sample_weight : array-like
            Hit weights used during the track fit.

        Retunrs
        -------
        retina : float
            Negative value of the artificial retina gradient.
        """

        rs = track_prams[0] * x + track_prams[1] - y


        if sample_weight == None:
            exps = numpy.exp(- (rs/sigma)**2)
        else:
            exps = numpy.exp(- (rs/sigma)**2) * sample_weight


        dks = - 2.*rs / sigma**2 * exps * x
        dbs = - 2.*rs / sigma**2 * exps

        return -numpy.array([dks.sum(), dbs.sum()])

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

    def fit_one_track(self, x, y, sample_weight=None):
        """
        Finds the best track among hits. Track parametrization: y = k * x + b.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        sample_weight : array-like
            Hit weights used during the track fit.

        Returns
        -------
        track_prams : array-like
            Track parameters [k, b].
        """

        sigma = self.sigma


        rs = []
        ks = []
        bs = []

        for i in range(len(x)):
            for j in range(len(x)):

                if x[j] <= x[i]:
                    continue

                # if numpy.random.rand() > 0.5:
                #     continue

                x1 = x[i]
                x2 = x[j]
                y1 = y[i]
                y2 = y[j]

                k0 = (y2 - y1) / (x2 - x1)
                b0 = y1 - k0 * x1

                if k0 >= self.k_limits[0] and k0 <= self.k_limits[1] and b0 >= self.b_limits[0] and b0 <= self.b_limits[1]:

                    r = -self.retina_func([k0, b0], x, y, sigma, sample_weight)

                    rs.append(r)
                    ks.append(k0)
                    bs.append(b0)

        rs = numpy.array(rs)
        ks = numpy.array(ks)
        bs = numpy.array(bs)

        if len(rs) == 0:
            return []

        params = [ks[rs == rs.max()][0], bs[rs == rs.max()][0]]

        res = minimize(self.retina_func, params, args = (x, y, sigma, sample_weight), method='BFGS',
                       jac=self.retina_grad, options={'gtol': 1e-6, 'disp': False})

        params = res.x

        return res.x

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

        labels = -1 * numpy.ones(len(x))
        tracks_params = []
        track_inds = []

        if len(x) == 0:
            self.labels_ = labels
            self.tracks_params_ = numpy.array(tracks_params)
            self.track_inds_ = numpy.array(track_inds)
            return


        used = numpy.zeros(len(x))
        indexes = numpy.arange(len(x))

        for track_id in range(self.n_tracks):

            x_track = x[used == 0]
            y_track = y[used == 0]

            if sample_weight == None:
                sample_weight_track = None
            else:
                sample_weight_track = sample_weight[used == 0]

            if len(numpy.unique(x_track)) < self.min_hits or len(x_track) <= 0:
                break

            one_track_params = self.fit_one_track(x_track, y_track, sample_weight_track)

            if len(one_track_params) == 0:
                continue

            dists = numpy.abs(one_track_params[0] * x + one_track_params[1] - y)
            dist_mask = (dists <= self.residuals_threshold)

            if (dist_mask * 1).sum() < self.min_hits:
                if self.unique_hit_labels == True:
                    used[dist_mask] = 1
                continue

            atrack = indexes[dist_mask & (used == 0)]
            atrack, _ = self.one_hit_per_layer(atrack, x[atrack], y[atrack], x[atrack], one_track_params[0], one_track_params[1])
            track_inds.append(atrack)
            if self.unique_hit_labels == True:
                used[atrack] = 1

            if len(atrack) >= 2:
                one_track_params = numpy.polyfit(x[atrack], y[atrack], 1)
            else:
                one_track_params = []
            tracks_params.append(one_track_params)


        self.tracks_params_ = numpy.array(tracks_params)
        self.track_inds_ = numpy.array(track_inds)
