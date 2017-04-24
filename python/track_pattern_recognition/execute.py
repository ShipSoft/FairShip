__author__ = 'Mikhail Hushchyn'

import ROOT
import numpy
import shipunit  as u

from pattern_recognition import track_pattern_recognition
from digitization import Digitization
from fit import track_fit


def execute(smeared_hits, stree, ShipGeo):

    ######################################## Hits digitization #########################################################

    X = Digitization(stree, smeared_hits)

    ######################################## Do Track Pattern Recognition ##############################################

    reco_tracks = track_pattern_recognition(X, z_magnet=ShipGeo.Bfield.z, method='FastHough')

    ######################################### Fit recognized tracks ####################################################

    theTracks = track_fit(ShipGeo, reco_tracks)

    ######################################### Estimate true track ids ##################################################

    return reco_tracks, theTracks
