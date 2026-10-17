#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Script to collect muons hitting either the UBT extended plane, or the SBT, including soft interaction products, and DIS events, to a ROOT file."""

"""
Begin of pythia block to avoid aliBuild error
Uncomment for running with aliBuild
"""
# import cppyy
## Load library
# cppyy.load_library("/cvmfs/ship.cern.ch/26.05/sw/slc9_x86-64/pythia6/latest/lib/libPythia6.so")
## Include header
# cppyy.include("/cvmfs/ship.cern.ch/26.05/sw/slc9_x86-64/ROOTEGPythia6/latest/include/TPythia6.h")
## Create object
# myPythia = cppyy.gbl.TPythia6()
# print("Pythia6 created")
"""
End of pythia block to avoid aliBuild error
"""

import argparse
import logging
import math
import sys
import time
from pathlib import Path

import file_summary
import ROOT as r
import saveBasicParameters
from filterEvents import load_muon_shield_field

print("Loading ShipMuDIS", flush=True)
if r.gSystem.Load("libShipMuDIS.so") < 0:
    raise RuntimeError("Could not load libShipMuDIS.so")
print("ShipMuDIS loaded", flush=True)
pdg = r.TDatabasePDG.Instance()

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--inputfile", help="full path to muon background files", required=True)
parser.add_argument(
    "-o",
    "--outputfile",
    help="custom outputfile name",
    default="muonsProduction_wsoft.root",
)
parser.add_argument("-n", "--n_events", type=int, default=-1)
parser.add_argument("-s", "--start_event", type=int, default=0)
parser.add_argument("--seed", type=int, help="Random seed for Pythia6 and ROOT (default: time-based)")
parser.add_argument("--check-all-volumes", action="store_true", help="Scan all geometry volumes for diagnostics")
parser.add_argument("-z", "--z_max", type=float, default=20000)
parser.add_argument("--z_min", type=float, default=2500, help="Minimum z in cm for diagnostics (default: 2500)")
parser.add_argument("-d", "--nDIS", help="Number of DIS per muon to generate", required=False, default=1000, type=int)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="ROOT geofile", required=True)
parser.add_argument("--muon-shield-field-map", help="Shield field map (default: geometry shieldName)")
parser.add_argument("--muon-shield-field-z", type=float, help="Shield map z offset in cm (default: geometry entrance)")
parser.add_argument(
    "--poca-jump-threshold",
    type=float,
    default=1.0,
    help="Count transverse jumps between measurement lines larger than this value in cm (default: 1)",
)
parser.add_argument(
    "--muon-selection",
    choices=("auto", "first", "hits", "all"),
    default="auto",
    help="Muon tracks to process per input event: first (MCTrack[0], particle gun), hits (every muon with a "
    "UBT, SBT, SST or TD point), all (every muon), auto (first if MCTrack[0] is a muon, else hits; default)",
)
parser.add_argument(
    "--debug",
    help="Control FairLogger verbosity: 0=info (default), 1=+debug, 2=+debug1, 3=+debug2",
    default=0,
    type=int,
    choices=range(0, 4),
)

args = parser.parse_args()
if not math.isfinite(args.poca_jump_threshold) or args.poca_jump_threshold < 0:
    parser.error("--poca-jump-threshold must be finite and nonnegative")

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
    logging.basicConfig(level=logging.DEBUG)
elif args.debug == 3:
    r.gInterpreter.ProcessLine('fair::Logger::SetConsoleSeverity("debug2");')
    logging.basicConfig(level=logging.DEBUG)

print(logging.getLogger().getEffectiveLevel())
logging.debug("Debug messages ON")

logging.info(f"Path to MuonBackground : {args.inputfile}")

# Keep the seed nonzero for ROOT and below Pythia6's 900000000 limit.
theseed = ((args.seed if args.seed is not None else time.time_ns()) - 1) % 899999999 + 1
logging.info("Random seed: %d", theseed)
r.gRandom.SetSeed(theseed)

# Read geofile to get gGeoManager
r.TGeoManager.Import(args.geoFile)

if not r.gGeoManager:
    logging.error("Failed to load geometry from '%s'", args.geoFile)
    sys.exit(1)

logging.info("Geometry successfully loaded.")

# Check
r.gGeoManager.Print()  # Read geometry

# Lowest muon momentum, in GeV/c, for which DIS interactions are generated.
MIN_PYTHIA_P = 2.0
muDis = r.MuDISProcessor()
# Keep the maker alive: it owns the map borrowed by the path processor.
field_maker = r.ShipFieldMaker()
shield_field, shield_path = load_muon_shield_field(
    field_maker, args.geoFile, args.muon_shield_field_map, args.muon_shield_field_z
)
muDis.SetMuonShieldField(shield_field, r.gGeoManager)
logging.info("Muon shield field map: %s", shield_path)
if args.check_all_volumes:
    muDis.CheckAllVolumes()
muDis.SetPocaJumpThreshold(args.poca_jump_threshold)
if not muDis.SetMuonSelection(args.muon_selection):
    sys.exit(1)
ok = muDis.init(args.n_events, args.start_event, MIN_PYTHIA_P, args.nDIS, theseed, args.z_max, args.z_min)
if not ok:
    print("Invalid initialisation. Doing nothing.")
    sys.exit(1)

p = Path(args.inputfile)

if p.is_file():
    input_files = [args.inputfile]
    muDis.process_file(args.inputfile, args.outputfile)

elif p.is_dir():
    pattern = "sim_"

    # Sorted, so that muon_srcFile indices and entry ranges are reproducible.
    input_files = sorted(
        str(path) for path in p.rglob("*") if path.is_file() and pattern in path.name and ".root" in path.name
    )

    print(f"Found {len(input_files)} files:")
    if len(input_files) < 1:
        print("No input file found in path.")
        sys.exit(1)
    for f in input_files:
        print(f)

    muDis.process_file(input_files, args.outputfile)
else:
    print("Inputfile string does not exist")
    sys.exit(1)

if not Path(args.outputfile).is_file():
    logging.error("No output written to %s", args.outputfile)
    sys.exit(1)

# Record how this file was made. muon_srcFile indexes inputFiles, in the order
# the input chain was built; PoT refers to the input files as a whole.
chain = r.TChain("cbmsim")
for name in input_files:
    chain.Add(name)
n_input = chain.GetEntries()
end_entry = n_input if args.n_events < 0 else min(args.start_event + args.n_events, n_input)
with r.TFile.Open(args.outputfile, "READ") as output:
    n_written = output.Get("MuonDIS").GetEntries()
summary = file_summary.merge_file_summaries(input_files)
summary.update(
    stage="prepareEvents",
    seed=theseed,
    seedFromTime=args.seed is None,
    nDIS=args.nDIS,
    minPythiaP=MIN_PYTHIA_P,
    inputEntries=n_input,
    entryRange=[args.start_event, max(args.start_event, end_entry)],
    muonsWritten=n_written,
    zMin=args.z_min,
    zMax=args.z_max,
    geoFile=args.geoFile,
    muonShieldFieldMap=str(shield_path),
    pocaJumpThreshold=args.poca_jump_threshold,
    muonSelection=args.muon_selection,
    versions=saveBasicParameters.retrieveGitTags({}),
)
file_summary.write_file_summary(args.outputfile, summary)
logging.info("FileSummary written to %s", args.outputfile)
