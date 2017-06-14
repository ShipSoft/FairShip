__author__ = 'Mikhail Hushchyn'

import ROOT
import numpy

import getopt
import sys

# For ShipGeo
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler

# For modules
import shipDet_conf

# For track pattern recognition
from mctruth import getReconstructibleTracks, get_fitted_trackids, get_track_ids
from smear_hits import smearHits
from execute import execute

# For track pattern recognition quality measure
from quality import init_book_hist, quality_metrics, save_hists



def run_track_pattern_recognition(input_file, geo_file, output_file, dy, reconstructiblerequired, threeprong, method):
    """
    Runs all steps of track pattern recognition.

    Parameters
    ----------
    input_file : string
        Path to an input .root file with events.
    geo_file : string
        Path to a file with SHiP geometry.
    output_file : string
        Path to an output .root file with quality plots.
    dy : float
    reconstructiblerequired : int
        Number of reconstructible tracks in an event.
    threeprong : int
        If 1 - HNL decay into 3 particles is considered.
    method : string
        Name of a track pattern recognition method.
    """


    ############################################# Load SHiP geometry ###################################################

    # Check geo file
    try:
        fgeo = ROOT.TFile(geo_file)
    except:
        print "An error with opening the ship geo file."
        raise

    sGeo = fgeo.FAIRGeom

    # Prepare ShipGeo dictionary
    if not fgeo.FindKey('ShipGeo'):

        if sGeo.GetVolume('EcalModule3') :
            ecalGeoFile = "ecal_ellipse6x12m2.geo"
        else:
            ecalGeoFile = "ecal_ellipse5x10m2.geo"

        if dy:
            ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy, EcalGeoFile = ecalGeoFile)
        else:
            ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", EcalGeoFile = ecalGeoFile)

    else:
        upkl    = Unpickler(fgeo)
        ShipGeo = upkl.load('ShipGeo')

    ############################################# Load SHiP modules ####################################################

    run = ROOT.FairRunSim()
    modules = shipDet_conf.configure(run,ShipGeo)

    ############################################# Load inpur data file #################################################

    # Check input file
    try:
        fn = ROOT.TFile(input_file,'update')
    except:
        print "An error with opening the input data file."
        raise

    sTree = fn.cbmsim

    ########################################## Start Track Pattern Recognition #########################################

    # Init book of hists for the quality measurements
    h = init_book_hist()

    # Start event loop
    nEvents   = sTree.GetEntries()

    for iEvent in range(nEvents):

        if iEvent%100 == 0:
            print 'Event ', iEvent

        ########################################### Select one event ###################################################

        rc = sTree.GetEvent(iEvent)

        ########################################### Smear hits #########################################################

        smeared_hits = smearHits(sTree, ShipGeo, modules, no_amb=None)

        if len(smeared_hits) == 0:
            continue

        ########################################### Do track pattern recognition #######################################

        reco_tracks, theTracks  = execute(smeared_hits, sTree, ShipGeo, method)

        ########################################### Get MC truth #######################################################

        y = get_track_ids(sTree, smeared_hits)

        fittedtrackids, fittedtrackfrac = get_fitted_trackids(y, reco_tracks)

        reco_mc_tracks = getReconstructibleTracks(iEvent,
                                                  sTree,
                                                  sGeo,
                                                  reconstructiblerequired,
                                                  threeprong,
                                                  ShipGeo)

        ########################################### Measure quality metrics ############################################

        quality_metrics(smeared_hits, sTree, reco_mc_tracks, reco_tracks, theTracks, h)


    ############################################### Save results #######################################################

    save_hists(h, output_file)


    return

if __name__ == "__main__":

    input_file = None
    geo_file = None
    output_file = 'hists.root'
    dy = None
    reconstructiblerequired = 2
    threeprong = 0
    method = 'Baseline'


    argv = sys.argv[1:]

    msg = '''Runs ship track pattern recognition.\n\
    Usage:\n\
      python RunPR.py [options] \n\
    Example: \n\
      python RunPR.py -i "ship.conical.Pythia8-TGeant4.root" -g "geofile_full.conical.Pythia8-TGeant4.root"
    Options:
      -i  --input                   : Input file path
      -g  --geo                     : Path to geo file
      -o  --output                  : Output .root file path. Default is hists.root
      -y  --dy                      : dy
      -n  --n_reco                  : Number of reconstructible tracks per event is required
      -t  --three                   : Is threeprong mumunu decay?
      -m  --method                  : Name of a track pattern recognition method: 'Baseline', 'FH', 'AR', 'R'
                                    : Default is 'Baseline'
      -h  --help                    : Shows this help
      '''

    try:
        opts, args = getopt.getopt(argv, "hm:i:g:y:n:t:o:",
                                   ["help", "method=", "input=", "geo=", "dy=", "n_reco=", "three=", "output="])
    except getopt.GetoptError:
        print "Wrong options were used. Please, read the following help:\n"
        print msg
        sys.exit(2)
    if len(argv) == 0:
        print msg
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            print msg
            sys.exit()
        elif opt in ("-m", "--method"):
            method = arg
        elif opt in ("-i", "--input"):
            input_file = arg
        elif opt in ("-g", "--geo"):
            geo_file = arg
        elif opt in ("-y", "--dy"):
            dy = float(arg)
        elif opt in ("-n", "--n_reco"):
            reconstructiblerequired = int(arg)
        elif opt in ("-t", "--three"):
            threeprong = int(arg)
        elif opt in ("-o", "--output"):
            output_file = arg


    run_track_pattern_recognition(input_file, geo_file, output_file, dy, reconstructiblerequired, threeprong, method)
