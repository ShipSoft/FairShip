# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
#
# SPDX-License-Identifier: LGPL-3.0-or-later

"""Write a synthetic SHiP neutrino flux file (schema v1).

Produces the two RNTuples the GENIE flux driver reads — ``nu_flux`` (one
entry per neutrino ray) and ``flux_meta`` (POT equivalent, maximum energy) —
filled with a plausible toy spectrum. Useful for exercising the flux driver
and the genie source without a real production; for real flux files convert
FairShip productions with aegir's ``scripts/convert_fairship_nu_flux.py``.

Usage: python make_flux_ntuple.py [output.root] [n_entries]
"""

import os
import sys
from argparse import ArgumentParser

import ROOT

parser = ArgumentParser()

parser.add_argument("-f", "--file", dest="inputfilename", help="Input file name (FairShip fixedTarget production)", required=True)
parser.add_argument("-o", "--output", dest="out", help="Output file name, will use nu_flux_inputfilename if not provided", required=False)
parser.add_argument("-p", "--pot", dest="pot_number", help="Number of PoT for the input file", required=True, type=int)
parser.add_argument("-nc","--nocharm", dest="noCharm", help="If True, do not store neutrinos from charmed hadrons and tau leptons", action="store_true", default=False)

options = parser.parse_args()

inputfilename = str(options.inputfilename)
if options.out:
    out = str(options.out)
else:
    out = "nu_flux_" + os.path.basename(inputfilename)
pot_number = int(options.pot_number)

noCharm = bool(options.noCharm)


model = ROOT.RNTupleModel.Create()
model.MakeField["std::int32_t"]("pdg")
for name in (
    "vx",
    "vy",
    "vz",
    "t",
    "px",
    "py",
    "pz",
    "weight",
    "parent_px",
    "parent_py",
    "parent_pz",
):
    model.MakeField["double"](name)
model.MakeField["std::int32_t"]("parent_pdg")
model.MakeField["std::int32_t"]("process_id")
model.MakeField["std::int64_t"]("origin_run")
model.MakeField["std::int64_t"]("origin_event")

writer = ROOT.RNTupleWriter.Recreate(model, "nu_flux", out)
entry = writer.CreateEntry()
emax = 0.0

charmExtern = [4332, 4232, 4132, 4232, 4122, 431, 411, 421, 15] #exclude charmed hadrons and tau leptons
neutrinos = [-12, 12, -14, 14, -16, 16]

cm2mm = 10.
nentries = 0


f = ROOT.TFile.Open(os.environ["EOSSHIP"] + inputfilename, "READ")  
print("opened file ", inputfilename)
sTree = f.Get("cbmsim")
for n in range(sTree.GetEntries()):
   sTree.GetEntry(n)
   header = sTree.MCEventHeader
   for v in sTree.PlaneHAPoint:
    nu = v.GetTrackID()
    t = sTree.MCTrack[nu]
    pdg = t.GetPdgCode()
    if abs(pdg) not in neutrinos and noCharm:
        continue  # story only neutrinos
    momt = sTree.MCTrack[t.GetMotherId()]
    mompdg = momt.GetPdgCode()
    if abs(mompdg) in charmExtern:
        continue  # take heavy flavours from separate production
    e = t.GetEnergy()
    nentries += 1 #all check passed, we store the neutrino
    emax = max(emax, e)
    entry["pdg"] = pdg
    entry["vx"] = v.GetX() * cm2mm  # mm
    entry["vy"] = v.GetY() * cm2mm  # mm
    entry["vz"] = v.GetZ() * cm2mm  # mm
    entry["t"] = v.GetTime()  # ns
    entry["px"] = t.GetPx() # GeV
    entry["py"] = t.GetPy()
    entry["pz"] = t.GetPz()
    entry["weight"] = 1.0
    entry["parent_pdg"] = mompdg
    entry["parent_px"] = momt.GetPx()
    entry["parent_py"] = momt.GetPy()
    entry["parent_pz"] = momt.GetPz()
    entry["process_id"] = momt.GetProcID()
    #taking the header values, we may also prefer the ttree entry number
    entry["origin_run"] = header.GetRunID()
    entry["origin_event"] = header.GetEventID()
    writer.Fill(entry)
del writer

meta = ROOT.RNTupleModel.Create()
meta.MakeField["std::int32_t"]("schema_version")
meta.MakeField["double"]("pot")
meta.MakeField["double"]("max_energy")
meta.MakeField["std::string"]("description")
meta.MakeField["std::string"]("software")
f = ROOT.TFile.Open(out, "UPDATE")
mwriter = ROOT.RNTupleWriter.Append(meta, "flux_meta", f)
mentry = mwriter.CreateEntry()
mentry["schema_version"] = 1
mentry["pot"] = pot_number
mentry["max_energy"] = emax
mentry["description"] = "flux from FairShip production (schema v1)"
mentry["software"] = "aegir-genie convert_flux_ntuple.py"
mwriter.Fill(mentry)
del mwriter
f.Close()

print(f"wrote {out}: {nentries} rays, max energy {emax:.1f} GeV")
sys.stdout.flush()
# PyROOT teardown can hang after RNTuple writes; exit hard once done.
os._exit(0)
