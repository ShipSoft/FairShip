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

source = ROOT.FairFileSource(options.inputFile)
run.SetSource(source)
sink = ROOT.FairRootFileSink(outFile)
run.SetSink(sink)
rtdb = run.GetRuntimeDb()

parFile = ROOT.FairParRootFileIo()
parFile.open(options.parFile, "UPDATE")
rtdb.setFirstInput(parFile)
rtdb.setOutput(parFile);
rtdb.saveOutput();

muon_reco_task = SndlhcMuonReco.MuonReco()

muon_reco_task.SetTolerance(options.tolerance)

run.AddTask(muon_reco_task)
print("Done adding task. Muon reco constructed")
run.Init()
print("Done init about to Run")
run.Run(0, options.nEvents)
print("Done running")

