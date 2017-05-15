__author__ = 'Mikhail Hushchyn'

from copy import copy
import numpy

from fast_hough import FastHough
from combination import Combinator



class TracksRecognition2D(object):

    def __init__(self, model_y, model_stereo, unique_hit_labels=True):
        """
        This is realization of the reconstruction scheme which uses two 2D projections to reconstruct a 3D track.

        Parameters
        ----------
        model_y : object
            Model for the tracks reconstruction in y-z plane.
        model_stereo : object
            Model for the tracks reconstruction in x-z plane.
        """

        self.model_y = copy(model_y)
        self.model_stereo = copy(model_stereo)
        self.unique_hit_labels = unique_hit_labels

        self.labels_ = None
        self.tracks_params_ = None

    def decodeDetectorID(self, detID):
        """
        Decodes detector ID.

        Parameters
        ----------
        detID : int or array-like
            Detector ID values.

        Returns
        -------
        statnb : int or array-like
            Station numbers.
        vnb : int or array-like
            View numbers.
        pnb : int or array-like
            Plane numbers.
        lnb : int or array-like
            Layer numbers.
        snb : int or array-like
            Straw tube numbers.
        """

        statnb = detID // 10000000
        vnb = (detID - statnb * 10000000) // 1000000
        pnb = (detID - statnb * 10000000 - vnb * 1000000) // 100000
        lnb = (detID - statnb * 10000000 - vnb * 1000000 - pnb * 100000) // 10000
        snb = detID - statnb * 10000000 - vnb * 1000000 - pnb * 100000 - lnb * 10000 - 2000

        return statnb, vnb, pnb, lnb, snb

    def get_xz(self, plane_k, plane_b, X):
        """
        This method returns (z, x) coordinated of intersections of straw tubes in stereo-views and
        a plane corresponding to a founded track in y-view.

        Parameters
        ----------
        plane_k : float
            Slope of the track in y-view.
        plane_b : float
            Intercept of the track in y-view.
        X : ndarray-like
            Information about active straw tubes: [[xtop, ytop, ztop, xbot, ybot, zboy, dist2wire, detID], [...], ...]

        Returns
        -------
        z : array-like
            Z coordinates of the intersections.
        x : array-like
            X coordinates of the intersections.
        """

        Wz1 = X[:, 2]
        Wx1 = X[:, 0]
        Wx2 = X[:, 3]
        Wy1 = X[:, 1]
        Wy2 = X[:, 4]

        y = plane_k * Wz1 + plane_b
        x = (Wx2 - Wx1) / (Wy2 - Wy1) * (y - Wy1) + Wx1

        return Wz1, x

    def y_track_recognition(self, X, is_stereo, sample_weight=None):
        """
        Does track pattern recognition in y-z plane.

        Parameters
        ----------
        X : ndarray-like
            Information about active straw tubes: [[xtop, ytop, ztop, xbot, ybot, zboy, dist2wire, detID], [...], ...]
        is_stereo : array-like
            Whether a hit is from Y-views or stereo: [0, 1, 1, 1, 0, 0, ...]
        sample_weight : array-like
            Hit weights used during the track fit.

        Returns
        -------
        track_inds_y : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        tracks_params_y : array-like
            List of parameters of the recognized tracks. Example: [[k1, b1], [k2, b2], ...]
        """

        indeces = numpy.arange(len(X))

        # Tracks Reconstruction in Y-view
        X_y = X[is_stereo == 0]
        indeces_y = indeces[is_stereo == 0]
        mask_y = is_stereo == 0

        x_y = X_y[:, 2]
        y_y = X_y[:, 1]

        if sample_weight != None:
            sample_weight_y = sample_weight[mask_y == 1]
        else:
            sample_weight_y = None

        self.model_y.fit(x_y, y_y, sample_weight_y)

        track_inds_y = self.model_y.track_inds_
        for i in range(len(track_inds_y)):
            track_inds_y[i] = indeces_y[track_inds_y[i]]

        tracks_params_y = self.model_y.tracks_params_

        return track_inds_y, tracks_params_y

    def stereo_track_recognition(self, X, is_stereo, track_inds_y, track_params_y, sample_weight=None):
        """
        Does track pattern recognition in x-z plane.

        Parameters
        ----------
        X : ndarray-like
            Information about active straw tubes: [[xtop, ytop, ztop, xbot, ybot, zboy, dist2wire, detID], [...], ...]
        is_stereo : array-like
            Whether a hit is from Y-views or stereo: [0, 1, 1, 1, 0, 0, ...]
        track_inds_y : array-like
            List of recognized tracks in y-z plane. Recognized track is a list of hit indexes.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        tracks_params_y : array-like
            List of parameters of the recognized tracks in y-z plane. Example: [[k1, b1], [k2, b2], ...]
        sample_weight : array-like
            Hit weights used during the track fit.

        Returns
        -------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes.
            Example: [[track_inds_yz, track_inds_xz], [...], ...]
        tracks_params_y : array-like
            List of parameters of the recognized tracks. Example: [[[k_yz, b_yz], [k_xz, b_xz]], ...]
        """

        track_inds = []
        tracks_params = []

        indeces = numpy.arange(len(X))

        # Tracks Reconstruction in Stereo_views
        X_stereo = X[is_stereo == 1]
        indeces_stereo = indeces[is_stereo == 1]
        used = numpy.zeros(len(X_stereo))
        mask_stereo = is_stereo == 1

        for track_id, one_track_y in enumerate(track_params_y):

            if len(one_track_y) != 0:

                plane_k, plane_b = one_track_y
                x_stereo, y_stereo = self.get_xz(plane_k, plane_b, X_stereo)

                if self.unique_hit_labels:
                    sel = (used==0) * (numpy.abs(y_stereo) <= 293.)
                else:
                    sel = (numpy.abs(y_stereo) <= 293.)

                if sample_weight != None:
                    sample_weight_stereo = sample_weight[mask_stereo == 1][sel]
                else:
                    sample_weight_stereo = None

                self.model_stereo.fit(x_stereo[sel], y_stereo[sel], sample_weight_stereo)

                if len(self.model_stereo.track_inds_) == 0:
                    continue
                track_inds_stereo = self.model_stereo.track_inds_

                for i in range(len(track_inds_stereo)):
                    inds = numpy.arange(len(used))[sel][track_inds_stereo[i]]
                    used[inds] = 1
                    track_inds_stereo[i] = indeces_stereo[sel][track_inds_stereo[i]]

                tracks_params_stereo = self.model_stereo.tracks_params_


            else:

                track_inds_stereo = []
                tracks_params_stereo = []


            for i in range(len(tracks_params_stereo)):
                tracks_params.append([one_track_y, tracks_params_stereo[i]])
                track_inds.append([track_inds_y[track_id], track_inds_stereo[i]])

        tracks_params = numpy.array(tracks_params)
        track_inds = numpy.array(track_inds)

        return track_inds, tracks_params

    def global_indeces(self, track_inds, indeces):
        """
        Recover global indexes of hits.

        Parameters
        ----------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes.
            Example: [[track_inds_yz, track_inds_xz], [...], ...]
        indeces : array-like
            Global hit indexes.

        Returns
        -------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit global indexes.
            Example: [[track_inds_yz, track_inds_xz], [...], ...]
        """

        for track_id in range(len(track_inds)):

            for i, k in enumerate(track_inds[track_id]):

                track_inds[track_id][i] = indeces[track_inds[track_id][i]]

        return track_inds


    def predict(self, X, sample_weight=None):
        """
        Does track pattern recognition.
        X : ndarray-like
            Information about active straw tubes: [[xtop, ytop, ztop, xbot, ybot, zboy, dist2wire, detID], [...], ...]
        sample_weight : array-like
            Hit weights used during the track fit.
        """

        statnb, vnb, pnb, lnb, snb = self.decodeDetectorID(X[:, -1])
        is_stereo = ((vnb == 1) + (vnb == 2)) * 1

        X12 = X[(statnb == 1) + (statnb == 2)]
        X34 = X[(statnb == 3) + (statnb == 4)]

        is_stereo12 = is_stereo[(statnb == 1) + (statnb == 2)]
        is_stereo34 = is_stereo[(statnb == 3) + (statnb == 4)]

        indeces12 = numpy.arange(len(X))[(statnb == 1) + (statnb == 2)]
        indeces34 = numpy.arange(len(X))[(statnb == 3) + (statnb == 4)]

        if sample_weight == None:
            weights12 = None
            weights34 = None
        else:
            weights12 = sample_weight[(statnb == 1) + (statnb == 2)]
            weights34 = sample_weight[(statnb == 3) + (statnb == 4)]


        #############################################Y-view track recognition###########################################

        track_inds_y12, track_params_y12 = self.y_track_recognition(X12, is_stereo12, sample_weight=weights12)
        track_inds_y34, track_params_y34 = self.y_track_recognition(X34, is_stereo34, sample_weight=weights34)


        ########################################Stereo-view track recognition###########################################

        self.track_inds12_, self.tracks_params12_ = self.stereo_track_recognition(X12, is_stereo12, track_inds_y12, track_params_y12, sample_weight=weights12)
        self.track_inds34_, self.tracks_params34_ = self.stereo_track_recognition(X34, is_stereo34, track_inds_y34, track_params_y34, sample_weight=weights34)

        ########################################Get global indeces of the hits##########################################

        self.track_inds12_ = self.global_indeces(self.track_inds12_, indeces12)
        self.track_inds34_ = self.global_indeces(self.track_inds34_, indeces34)


