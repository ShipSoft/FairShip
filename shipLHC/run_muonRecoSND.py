import ROOT
from argparse import ArgumentParser
import os

import SndlhcMuonReco

parser = ArgumentParser()
parser.add_argument("-f", "--inputFile", dest="inputFile", help="single input file", required=True)
parser.add_argument("-p", "--parFile", dest="parFile", help="parfile", required=True)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", required=True)
parser.add_argument("-n", "--nEvents", dest="nEvents",  type=int, help="number of events to process", default=100000)

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

run.SetSource(ROOT.FairFileSource(options.inputFile))
run.SetSink(ROOT.FairRootFileSink(outFile))
rtdb = run.GetRuntimeDb()

parFile = ROOT.FairParRootFileIo()
parFile.open(options.parFile, "UPDATE")
rtdb.setFirstInput(parFile)
rtdb.setOutput(parFile);
rtdb.saveOutput();

run.AddTask(SndlhcMuonReco.MuonReco())

run.Init()
print("Done init about to Run")
run.Run()
print("Done running")
