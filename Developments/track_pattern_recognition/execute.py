__author__ = 'Mikhail Hushchyn'

import ROOT
import numpy
import shipunit  as u

from pattern_recognition import track_pattern_recognition
from digitization import Digitization
from fit import track_fit


def execute(smeared_hits, stree, ShipGeo):
    """
    Does real track pattern recognition and track fit.

    Parameters
    ----------
    smeared_hits : list of dicts
        List of smeared hits. A smeared hit is a dictionary:
        {'digiHit':key,'xtop':top x,'ytop':top y,'z':top z,'xbot':bot x,'ybot':bot y,'dist':smeared dist2wire}
    stree : root file
        Events in raw format.
    ShipGeo : object
        Contains SHiP detector geometry.

    Returns
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

    theTracks : list
        List of fitted track objects.
    """

    ######################################## Hits digitization #########################################################

    X = Digitization(stree, smeared_hits)

    ######################################## Do Track Pattern Recognition ##############################################

    reco_tracks = track_pattern_recognition(X, z_magnet=ShipGeo.Bfield.z, method='FastHough')

    ######################################### Fit recognized tracks ####################################################

    theTracks = track_fit(ShipGeo, reco_tracks)

    ######################################### Estimate true track ids ##################################################

    return reco_tracks, theTracks
