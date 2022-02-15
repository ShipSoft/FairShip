import ROOT
from argparse import ArgumentParser
import os

import SndlhcMuonReco

parser = ArgumentParser()
parser.add_argument("-f", "--inputFile", dest="inputFile", help="single input file", required=True)
parser.add_argument("-p", "--parFile", dest="parFile", help="parfile", required=True)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", required=True)
parser.add_argument("-n", "--nEvents", dest="nEvents",  type=int, help="number of events to process", default=100000)
parser.add_argument("-t", "--tolerance", dest="tolerance",  type=float, help="How far away from Hough line hits assigned to the muon can be. In cm.", default=0.)
parser.add_argument("--use_scifi", dest="use_scifi",  help="Use SciFi hits.", action='store_true')
parser.add_argument("--no-use_scifi", dest="use_scifi",  help="No not use SciFi hits.", action='store_false')
parser.set_defaults(use_scifi=True)
parser.add_argument("--use_mufi", dest="use_mufi",  help="Use Muon Filter hits. Muon tracks are required to have three DS Muon Filter planes hit.", action='store_true')
parser.add_argument("--no-use_mufi", dest="use_mufi",  help="Do not use Muon Filter hits. The triplet condition will be based on SciFi hits.", action='store_false')
parser.set_defaults(use_mufi=True)

options = parser.parse_args()

import SndlhcGeo
geo = SndlhcGeo.GeoInterface(options.geoFile)

lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
lsOfGlobals.Add(geo.modules['Scifi'])
lsOfGlobals.Add(geo.modules['MuFilter'])

if options.inputFile.find('/eos')==0:
      x = options.inputFile
      filename = x[x.rfind('/')+1:]
      os.system('xrdcp '+os.environ['EOSSHIP']+options.inputFile+' '+filename)
      options.inputFile = filename

outFile = options.inputFile.replace('.root','_muonReco.root') 

os.system('cp '+options.inputFile+' '+outFile)

run = ROOT.FairRunAna()
print("Initialized FairRunAna")
source = ROOT.FairFileSource(options.inputFile)
run.SetSource(source)
sink = ROOT.FairRootFileSink(outFile)
run.SetSink(sink)
#print("Set Source and Sink")
#rtdb = run.GetRuntimeDb()
#print("Got runtime db")

#parFile = ROOT.FairParRootFileIo()
#parFile.open(options.parFile, "UPDATE")
#rtdb.setFirstInput(parFile)
#print("Set runtime db first input")
#rtdb.setOutput(parFile);
#print("Set runtime db output")
#rtdb.saveOutput();
#print("Save runtime db output")

muon_reco_task = SndlhcMuonReco.MuonReco()
run.AddTask(muon_reco_task)


print("Done adding task. Muon reco constructed")
run.Init()

# The following lines must be *after* run.Init()
muon_reco_task.SetTolerance(options.tolerance)
muon_reco_task.SetUseSciFi(options.use_scifi)
muon_reco_task.SetUseMuFi(options.use_mufi)


print("Done init about to Run")
run.Run(0, options.nEvents)
print("Done running")

