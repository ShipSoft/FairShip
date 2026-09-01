#!/usr/bin/env python
"""Script to collect muons hitting either the UBT extended plane, or the SBT, including soft interaction products, and DIS events, to a ROOT file."""

"""Created May 2026 A.-M. Magnan"""

"""
Begin of pythia block to avoid aliBuild error
"""
import cppyy
# Load library
#cppyy.load_library("/cvmfs/ship.cern.ch/26.05/sw/slc9_x86-64/ROOTEGPythia6/latest/lib/libPythia6.so")
cppyy.load_library("/cvmfs/ship.cern.ch/26.05/sw/slc9_x86-64/pythia6/latest/lib/libPythia6.so")
# Include header
cppyy.include("/cvmfs/ship.cern.ch/26.05/sw/slc9_x86-64/ROOTEGPythia6/latest/include/TPythia6.h")
# Create object
myPythia = cppyy.gbl.TPythia6()
print("Pythia6 created")
"""
End of pythia block to avoid aliBuild error
"""

import argparse
import logging
import time

import ROOT as r
from pathlib import Path

import geomGeant4

r.gSystem.Load("libShipMuDIS.so")
pdg = r.TDatabasePDG.Instance()

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--inputfile", help="full path to muon background files")
parser.add_argument(
    "-o",
    "--outputfile",
    help="custom outputfile name",
    default="muonsProduction_wsoft.root",
)
parser.add_argument("-n", "--n_events", type=int, default=-1)
parser.add_argument("-s", "--start_event", type=int, default=0)
parser.add_argument("-z", "--z_max", type=float, default=20000)
parser.add_argument("-d", "--nDIS", help="Number of DIS per muon to generate", required=False, default=1000, type=int)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="ROOT geofile", required=True)
parser.add_argument(
    "--debug",
    help="Control FairLogger verbosity: 0=info (default), 1=+debug, 2=+debug1, 3=+debug2",
    default=0,
    type=int,
    choices=range(0, 4),
)

args = parser.parse_args()

if args.debug == 0:
    r.gErrorIgnoreLevel = r.kWarning

# Configure FairLogger verbosity based on debug level
r.gInterpreter.ProcessLine('#include "FairLogger.h"')
if args.debug == 0:
    r.gInterpreter.ProcessLine('fair::Logger::SetConsoleSeverity("info");')
    logging.basicConfig(level=logging.INFO)
elif args.debug == 1:
    r.gInterpreter.ProcessLine('fair::Logger::SetConsoleSeverity("debug");')
    logging.basicConfig(level=logging.DEBUG)
elif args.debug == 2:
    r.gInterpreter.ProcessLine('fair::Logger::SetConsoleSeverity("debug1");')
elif args.debug == 3:
    r.gInterpreter.ProcessLine('fair::Logger::SetConsoleSeverity("debug2");')

print(logging.getLogger().getEffectiveLevel())
logging.debug("Debug messages ON")

logging.info(f"Path to MuonBackground : {args.inputfile}")

theseed = int(time.time())
print(theseed)

# Read geofile to get gGeoManager
r.TGeoManager.Import(args.geoFile)

if not r.gGeoManager:
    logging.error("Failed to load geometry from '%s'", args.geoFile)
    sys.exit(1)

logging.info("Geometry successfully loaded.")

# Check
r.gGeoManager.Print()  # Read geometry

from ShipGeoConfig import load_from_root_file
ShipGeo = load_from_root_file(args.geoFile, "ShipGeo")

fieldMaker = geomGeant4.addVMCFields(ShipGeo,
                                     "",
                                     True,
                                     withVirtualMC=False)

globalField = fieldMaker.getGlobalField()

if not globalField:
    raise RuntimeError("ShipFieldMaker::getGlobalField() returned a null field")

muDis = r.MuDISProcessor()
muDis.SetField(globalField)
muDis.init(args.n_events, args.start_event, 2.0, args.nDIS, theseed, args.z_max)
p = Path(args.inputfile)

if p.is_file():
    muDis.process_file(args.inputfile, args.outputfile)
    
elif p.is_dir():
    pattern = "sim_"

    matching_files = [
        str(path)
        for path in p.rglob("*")
        if path.is_file() and pattern in path.name
    ]
    
    print(f"Found {len(matching_files)} files:")
    for f in matching_files:
        print(f)
        
    muDis.process_file(matching_files, args.outputfile)
else:
    print("Inputfile string does not exist")
