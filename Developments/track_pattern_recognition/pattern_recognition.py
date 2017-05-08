__author__ = 'Mikhail Hushchyn'


import numpy

import sys, os

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
utils_path = os.path.join(DIR_PATH, 'models/')
sys.path.insert(0, utils_path)

from recognition import TracksRecognition2D
from fast_hough import Clusterer, FastHough
from combination import Combinator

def track_pattern_recognition(X, z_magnet, method='FastHough'):

    if len(X) == 0:
        return {}

    ################################## Select models to search tracks in 2D planes #####################################

    if method=='FastHough':

        clustering=Clusterer(x_depth=2, y_depth=4, n_min=2)

        stm_y = FastHough(n_tracks=2,
                          min_hits=3,
                          k_size=0.7/4000,
                          b_size=1700./4000,
                          k_limits=(-0.35, 0.35),
                          b_limits=(-850, 850),
                          clustering=clustering,
                          unique_hit_labels=True)

        stm_stereo = FastHough(n_tracks=1,
                               min_hits=3,
                               k_size=0.6/160,
                               b_size=1000./160,
                               k_limits=(-0.3, 0.3),
                               b_limits=(-500, 500),
                               clustering=clustering,
                               unique_hit_labels=True)

    ################################## Recognize track before and after the magnet #####################################

    tr2d = TracksRecognition2D(model_y=stm_y, model_stereo=stm_stereo, unique_hit_labels=True)
    tr2d.predict(X, None)

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

        reco_tracks[track_id] = {'hits': atrack,
                                 'hitPosList': X[atrack, :-1],
                                 'charge': comb.charges_[track_id],
                                 'pinv':comb.inv_momentums_[track_id]}

    return reco_tracks
