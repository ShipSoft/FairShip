#!/usr/bin/env python
"""Script to collect muons hitting either the UBT extended plane, or the SBT, including soft interaction products, and DIS events, to a ROOT file."""

"""Created May 2026 A.-M. Magnan"""

import argparse
import logging
import time

import ROOT as r

r.gSystem.Load("libShipMuDIS.so")
# Configure FairLogger verbosity based on debug level
r.gInterpreter.ProcessLine('#include "FairLogger.h"')
# r.gInterpreter.ProcessLine('fair::Logger::SetConsoleSeverity("warn");')
r.gInterpreter.ProcessLine('fair::Logger::SetConsoleSeverity("info");')
#r.gInterpreter.ProcessLine('fair::Logger::SetConsoleSeverity("debug");')
pdg = r.TDatabasePDG.Instance()

logging.basicConfig(level=logging.INFO)
#logging.basicConfig(level=logging.DEBUG)

logging.debug("Debug messages ON")
print(logging.getLogger().getEffectiveLevel())


parser = argparse.ArgumentParser()
parser.add_argument("-f", "--inputfile", help="full path to muon background files")
parser.add_argument(
    "-o",
    "--outputfile",
    help="custom outputfile name",
    default="muonsProduction_wsoft.root",
)
parser.add_argument("-n", "--n_events", type=int, default=-1)
parser.add_argument("-z", "--z_max", type=float, default=20000)
parser.add_argument("-d", "--nDIS", help="Number of DIS per muon to generate", required=False, default=1000, type=int)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="ROOT geofile", required=True)

args = parser.parse_args()


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

muDis = r.MuDISProcessor()
muDis.init(args.n_events, args.nDIS, theseed, args.z_max)
muDis.process_file(args.inputfile, args.outputfile)
