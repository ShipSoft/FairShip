__author__ = 'Mikhail Hushchyn'


import numpy

import sys, os

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
utils_path = os.path.join(DIR_PATH, 'models/')
sys.path.insert(0, utils_path)

from recognition import TracksRecognition2D
from fast_hough import FastHough
from artificial_retina import ArtificialRetina
from combination import Combinator

from reconstructor import Reconstructor
from utils import decodeDetectorID

def track_pattern_recognition(X, z_magnet, method='FH'):
    """
    Does track pattern recognition.

    Parameters
    ----------
    X : ndarray-like
        Information about active straw tubes: [[xtop, ytop, ztop, xbot, ybot, zboy, dist2wire, detID], [...], ...]
    z_magnet : float
        Z-coordinate of the magnet center.
    method : string
        Name of the track pattern recognition method.

    Retunrs
    -------
    reco_tracks : dict
        Dictionary of recognized tracks: {track_id: reco_track}.
        Reco_track is a dictionary:
        {'hits': [ind1, ind2, ind3, ...],
         'hitPosList': X[atrack, :-1],
         'charge': charge,
         'pinv': pinv,
         'params12': [[k_yz, b_yz], [k_xz, b_xz]],
         'params34': [[k_yz, b_yz], [k_xz, b_xz]]}
    """

    if len(X) == 0:
        return {}

    ###################################### For method in models/reconstructor.py #######################################

    if method == 'R':

        statnb, vnb, pnb, lnb, snb = decodeDetectorID(X[:, [-1]])
        event = numpy.concatenate((vnb, statnb, X[:, [0, 3, 1, 4, 2, 6]]), axis=1)

        try:
            rec = Reconstructor(z_magnet=z_magnet,
                                y_resolution=1.,
                                residual_threshold_x=2.,
                                residual_threshold_y=0.8)
            rec.fit(event)
        except:
            return {}

        track_inds = rec.track_inds_
        track_params = rec.tracks_params_

        track_params12 = track_params[0]
        track_params34 = track_params[1]

        ################################## Combine track before and after the magnet ###################################

        comb = Combinator(z_magnet=z_magnet, magnetic_field=-0.75, dy_max=2., dx_max=20.)

        pinvs = comb.get_inv_momentums(track_params12, track_params34, [[0, 0], [1, 1]])
        charges = comb.get_charges(track_params12, track_params34, [[0, 0], [1, 1]])

        ############################################ Save combined tracks ##############################################

        reco_tracks = {}

        for track_id, acomb in enumerate(track_inds):
            atrack = track_inds[track_id]
            reco_tracks[track_id] = {'hits': atrack,
                                     'hitPosList': X[atrack, :-1],
                                     'charge': charges[track_id],
                                     'pinv': pinvs[track_id],
                                     'params12': track_params12[track_id],
                                     'params34': track_params34[track_id]}

        return reco_tracks

    ####################################################################################################################

    ############################################# Process Input Data ###################################################

    X1 = X.copy()
    X1[:, 1] += X1[:, 6] * numpy.cos(numpy.deg2rad(5))
    X1[:, 4] += X1[:, 6] * numpy.cos(numpy.deg2rad(5))

    X2 = X.copy()
    X2[:, 1] += - X2[:, 6] * numpy.cos(numpy.deg2rad(5))
    X2[:, 4] += - X2[:, 6] * numpy.cos(numpy.deg2rad(5))

    XX = numpy.concatenate((X1, X2), axis=0)
    XX_inds = numpy.concatenate((range(len(X)), range(len(X))))

    ################################## Select models to search tracks in 2D planes #####################################

    if method=='FH':


        stm_y = FastHough(n_tracks=2,
                          min_hits=3,
                          k_size=0.7/10000,
                          b_size=1700./10000,
                          k_limits=(-0.5, 0.5),
                          b_limits=(-1150, 1150),
                          unique_hit_labels=True)

        stm_stereo = FastHough(n_tracks=1,
                               min_hits=3,
                               k_size=0.6/200,
                               b_size=1000./200,
                               k_limits=(-0.3, 0.3),
                               b_limits=(-500, 500),
                               unique_hit_labels=True)

    if method=='AR':


        stm_y = ArtificialRetina(n_tracks=2,
                                 min_hits=2,
                                 residuals_threshold=0.15,
                                 sigma=0.2,
                                 k_size=0.7/10000,
                                 b_size=1700./10000,
                                 k_limits=(-0.5, 0.5),
                                 b_limits=(-1150, 1150))

        stm_stereo = ArtificialRetina(n_tracks=1,
                                      min_hits=2,
                                      residuals_threshold=2,
                                      sigma=2,
                                      k_size=0.6/200,
                                      b_size=1000./200,
                                      k_limits=(-0.3, 0.3),
                                      b_limits=(-500, 500))

    ################################## Recognize track before and after the magnet #####################################

    tr2d = TracksRecognition2D(model_y=stm_y, model_stereo=stm_stereo, unique_hit_labels=True)
    tr2d.predict(XX, None)

    track_inds12, tracks_params12 = tr2d.track_inds12_, tr2d.tracks_params12_
    track_inds34, tracks_params34 = tr2d.track_inds34_, tr2d.tracks_params34_

    ################################## Combine track before and after the magnet #######################################

    comb = Combinator(z_magnet=z_magnet, magnetic_field=-0.75, dy_max=2., dx_max=20.)
    comb.combine(tracks_params12, tracks_params34)

    ############################################ Save combined tracks ##################################################

    reco_tracks = {}

    for track_id, acomb in enumerate(comb.tracks_combinations_):

        track_before_y, track_before_stereo = track_inds12[acomb[0]]
        track_before = numpy.concatenate((track_before_y, track_before_stereo))

        track_after_y, track_after_stereo = track_inds34[acomb[1]]
        track_after = numpy.concatenate((track_after_y, track_after_stereo))

        atrack = numpy.concatenate((track_before, track_after))
        atrack = numpy.unique(XX_inds[atrack])

        reco_tracks[track_id] = {'hits': atrack,
                                 'hitPosList': X[atrack, :-1],
                                 'charge': comb.charges_[track_id],
                                 'pinv':comb.inv_momentums_[track_id],
                                 'params12': tracks_params12[acomb[0]],
                                 'params34': tracks_params34[acomb[1]]}

    return reco_tracks
