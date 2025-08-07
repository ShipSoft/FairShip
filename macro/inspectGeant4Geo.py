# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import sys

import ROOT
import shipRoot_conf
from ShipGeoConfig import load_from_root_file

shipRoot_conf.configure()

fname = "geofile_full.10.0.Pythia8-TGeant4.root"
if len(sys.argv) > 1:
    fname = sys.argv[1]

fgeo = ROOT.TFile(fname)
sGeo = fgeo.Get("FAIRGeom")
import shipDet_conf

run = ROOT.FairRunSim()
ShipGeo = load_from_root_file(fgeo, "ShipGeo")
modules = shipDet_conf.configure(run, ShipGeo)
# Use FairYamlVMCConfig for YAML configuration
yamlConfig = ROOT.FairYamlVMCConfig("g4Config", "g4Config.yaml")
yamlConfig.Setup()
run.SetName("TGeant4")
run.SetSink(ROOT.FairRootFileSink(ROOT.TMemFile("output", "recreate")))
# Create and set custom ShipStack for YAML config compatibility
stack = ROOT.ShipStack(1000)
stack.StoreSecondaries(ROOT.kTRUE)
stack.SetMinPoints(0)
# Get the Geant4 VMC instance and set our custom stack
geant4 = ROOT.TVirtualMC.GetMC()
if geant4:
    geant4.SetStack(stack)
run.Init()
run.Run(0)
import geomGeant4

geomGeant4.printVMCFields()
geomGeant4.printWeightsandFields()
