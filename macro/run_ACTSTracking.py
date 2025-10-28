from argparse import ArgumentParser
import sys
import os
import global_variables
import ROOT

env = os.environ.get("ACTS_ROOT")
python_dir=f"{env}/python"
sys.path.append(python_dir)

parser = ArgumentParser()

parser.add_argument("-f", "--inputFile", dest="inputFile", help="Input file", required=True)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="ROOT geofile", required=True)
parser.add_argument("-o", "--outputDir", dest="outputDir", help="Output directory", required=False, default=os.getcwd())
parser.add_argument("-n", "--nEvents", dest="nEvents", help="Num of events to process", type=int, required=False, default=1)
parser.add_argument("--detector", dest="detector", help="Select which detector to perform track reco." \
                                     , required=False, choices=['SiliconTarget','MTC','SND','StrawTracker'],  default='SiliconTarget')
parser.add_argument("--realPR", dest="realPR", help="Option for pattern recognition", required=False, default=False)
parser.add_argument("--vertexing", dest="vertexing", help="Enable vertexing", required=False, action="store_true")
parser.add_argument("--DQM", dest="DQM", help="Option to enable ACTS track and vertex DQM", required=False, default=True)
parser.add_argument("--minHits", dest="minHits", help="Option for minimum required hits to build a valid track", required=False)
parser.add_argument("--minP", dest="minP", help="Option for minimum required momenta to build a valid track", required=False)

options = parser.parse_args()

global_variables.inputFile = options.inputFile
global_variables.geoFile = options.geoFile
global_variables.outputDir = options.outputDir
global_variables.detector = options.detector
global_variables.vertexing = options.vertexing
global_variables.DQM = options.DQM

#Outfile should be in local directory
tmp = options.inputFile.split('/')
outFile = tmp[len(tmp)-1].replace('.root','_tracked.root')
outDir = options.inputFile.rsplit('/',1)[0]
fullpath = options.outputDir+''+str(outFile)
#Clone input file for writing
os.system('cp '+options.inputFile+' '+fullpath) 
global_variables.outputFile = fullpath

#Determine number of events to loop through
inFile = ROOT.TFile.Open(options.inputFile) 
fTree = inFile.Get("cbmsim")
global_variables.nEvents = min(fTree.GetEntries(),options.nEvents)
inFile.Close()

#If input file has not been converted to ACTS EDM then convert
if options.inputFile.find('_ACTS.root') < 0:
   import convertToACTS   
   convertToACTS.main()
   global_variables.inputFile = options.inputFile.replace('.root','_ACTS.root')

import ACTSReco
ACTSReco.runTracking()
