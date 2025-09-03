from argparse import ArgumentParser
import global_variables

parser = ArgumentParser()

parser.add_argument("-f", "--inputFile", dest="inputFile", help="Input file", required=True)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="ROOT geofile", required=True)
parser.add_argument("-o", "--outputDir", dest="outputDir", help="Output directory", required=False, default="trackingOut")
parser.add_argument("--detector", dest="detector", help="Select which detector to perform track reco." \
                                     , required=False, choices=['SiliconTarget','MTC','StrawTracker'],  default='SiliconTarget')
parser.add_argument("--realPR", dest="realPR", help="Option for pattern recognition", required=False, default=False)
parser.add_argument("--vertexing", dest="vertexing", help="Enable vertexing", required=False, action="store_true")
parser.add_argument("--minHits", dest="minHits", help="Option for minimum required hits to build a valid track", required=False)
parser.add_argument("--minP", dest="minP", help="Option for minimum required momenta to build a valid track", required=False)

options = parser.parse_args()

global_variables.inputFile = options.inputFile
global_variables.geoFile = options.geoFile
global_variables.outputDir = options.outputDir
global_variables.detector = options.detector
global_variables.vertexing = options.vertexing

import ACTSReco
ACTSReco.runTracking()
