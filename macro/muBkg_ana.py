import os
import sys
import ROOT
import shipunit as u
import rootUtils as ut
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler
from argparse import ArgumentParser
import shipRoot_conf
import shipVeto

ROOT.gROOT.SetBatch(True)
shipRoot_conf.configure()

# Argument Parsing
parser = ArgumentParser()
parser.add_argument("-f", "--inputFiles", nargs="+", help="Input ROOT files (space-separated) or a text file containing file paths", required=True)
parser.add_argument("-g", "--geoFile", help="ROOT geofile", required=True)
parser.add_argument("-n", "--nEvents", help="Number of events to analyze", default=999999, type=int)
options = parser.parse_args()

# If inputFiles is a single text file, read the list of files from it
input_files = []
if len(options.inputFiles) == 1 and options.inputFiles[0].endswith(".txt"):
    with open(options.inputFiles[0], "r") as file_list:
        input_files = [line.strip() for line in file_list if line.strip()]
else:
    input_files = options.inputFiles

if not input_files:
    print("Error: No valid input files provided!")
    sys.exit(1)

# Load Geometry
fgeo = ROOT.TFile.Open(options.geoFile)
unpkl = Unpickler(fgeo)
ShipGeo = unpkl.load('ShipGeo')

# -----Create geometry----------------------------------------------
import shipDet_conf
run = ROOT.FairRunSim()
run.SetName("TGeant4")
run.SetSink(ROOT.FairRootFileSink(ROOT.TMemFile('output', 'recreate')))
run.SetUserConfig("g4Config_basic.C")
rtdb = run.GetRuntimeDb()

modules = shipDet_conf.configure(run, ShipGeo)

import geomGeant4
if hasattr(ShipGeo.Bfield, "fieldMap"):
    fieldMaker = geomGeant4.addVMCFields(ShipGeo, '', True, withVirtualMC=False)
else:
    print("No fieldmap given, geofile too old, not supported anymore.")
    exit(-1)

sGeo = fgeo.FAIRGeom
geoMat = ROOT.genfit.TGeoMaterialInterface()
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
bfield = ROOT.genfit.FairShipFields()
bfield.setField(fieldMaker.getGlobalField())
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)

# Book Histograms
h = {}
ut.bookHist(h, "nUpstreamHits", "Number of Hits in Upstream Tagger", 50, 0, 50)
ut.bookHist(h, "nSBTHits", "Number of Hits in SBT", 50, 0, 50)
ut.bookHist(h, "UpstreamHitMap", "Upstream Tagger Hit Map;X [cm];Y [cm]", 1001, -500.5, 500.5, 1001, -500.5, 500.5)
ut.bookHist(h, "UpstreamHitMapZ", "Upstream Tagger Hit Map;X [cm];Z [cm]", 1001, -500.5, 500.5, 1001, -2497.2, -2496.3)
ut.bookHist(h, "UpstreamHitMap_onlyMuons", "Upstream Tagger Hit Map;X [cm];Y [cm]",1001, -500.5, 500.5, 1001, -500.5, 500.5)
ut.bookHist(h, "SBTHitMap", "SBT Hit Map;X [cm];Y [cm]", 1001, -500.5, 500.5, 1001, -500.5, 500.5)
ut.bookHist(h, "MuonFlux", "Muon Flux;X [cm];Y [cm]", 1001, -500.5, 500.5, 1001, -500.5, 500.5)
ut.bookHist(h, "MuonFlux_andPion", "Muon and Pion Flux;X [cm];Y [cm]", 1001, -500.5, 500.5, 1001, -500.5, 500.5)
ut.bookHist(h, "ElecFlux", "Electron Flux;X [cm];Y [cm]", 1001, -500.5, 500.5, 1001, -500.5, 500.5)
ut.bookHist(h, "GammaFlux", "Gamma Flux;X [cm];Y [cm]", 1001, -500.5, 500.5, 1001, -500.5, 500.5)
ut.bookHist(h, "MuonP_xy", "Muon Momentum;X [cm];Y [cm]", 1001, -500.5, 500.5, 1001, -500.5, 500.5)
ut.bookHist(h, "ElecP_xy", "Electron/positron Momentum;X [cm];Y [cm]", 1001, -500.5, 500.5, 1001, -500.5, 500.5)
ut.bookHist(h, "GammaP_xy", "Gamma P ;X [cm];Y [cm]", 1001, -500.5, 500.5, 1001, -500.5, 500.5)
ut.bookHist(h, "MuonPtP", "pT vs P ;P [GeV];P_T [Gev]", 100, 0, 1, 100, 0, 10)
ut.bookHist(h, "UBT_PtvsP", "pT vs P ;P [GeV];P_T [Gev]", 100, 0, 1, 100, 0, 6)
ut.bookHist(h, "SBT_PtvsP", "pT vs P ;P [GeV];P_T [Gev]", 100, 0, 1, 100, 0, 6)
ut.bookHist(h, "UBT_pdgcode", "UBT particle rate", 500, 0.5, 500.5)
ut.bookHist(h, "SBT_pdgcode", "SBT particle rate", 500, 0.5, 500.5)
ut.bookHist(h, "UBT_efficiency", "Upstream Tagger Efficiency", 100, 0, 1)
ut.bookHist(h, "SBT_efficiency", "SBT Efficiency", 100, 0, 1)

# Process Each Input File
for inputFile in input_files:
    print(f"Processing file: {inputFile}")

    # Open ROOT File
    f = ROOT.TFile.Open(inputFile)
    if not f or f.IsZombie():
        print(f"Error: Unable to open {inputFile}, skipping...")
        continue

    sTree = f.cbmsim
    print(f"Number of events in {inputFile}: {sTree.GetEntries()}")

    # Initialize Veto System
    if hasattr(sTree, "Digi_SBTHits"):
        veto = shipVeto.Task(sTree)
        veto_enable = True
    else:
        veto_enable = False

    # Event Loop
    nEvents = min(sTree.GetEntries(), options.nEvents)
    for i in range(nEvents):
        sTree.GetEntry(i)

        # Veto Decision
        if veto_enable :
            UBT_flag, UBT_weight, UBT_nHits = veto.UBT_decision()
            SBT_flag, SBT_weight, SBT_nHits = veto.SBT_decision()
        else:
            UBT_flag, UBT_weight, UBT_nHits = 1,1,1
            SBT_flag, SBT_weight, SBT_nHits = 1,1,1
        ## Fill the muon flux
        for ahit in sTree.MCTrack:
            if ahit.GetPdgCode() == 13 or ahit.GetPdgCode() == -13:
                x, y = ahit.GetStartX(), ahit.GetStartY()
                Px, Py, Pz = ahit.GetPx(), ahit.GetPy(), ahit.GetPz()
                momentum = ROOT.TVector3(Px, Py, Pz)
                pT, p = momentum.Perp(), momentum.Mag()

        # Process UpstreamTaggerPoint
        if hasattr(sTree, "UpstreamTaggerPoint"):
            for ahit in sTree.UpstreamTaggerPoint:
                h["UBT_pdgcode"].Fill(abs(ahit.PdgCode()))
                x, y, z = ahit.GetX(), ahit.GetY(), ahit.GetZ()
                h["UpstreamHitMap"].Fill(x, y)
                h["UpstreamHitMapZ"].Fill(x,z)
                Px, Py, Pz = ahit.GetPx(), ahit.GetPy(), ahit.GetPz()
                momentum = ROOT.TVector3(Px, Py, Pz)
                pT = momentum.Perp()
                p = momentum.Mag()
                if ahit.PdgCode() == 13 or ahit.PdgCode() == -13: 
                    h["MuonFlux"].Fill(x,y)
                    h["UpstreamHitMap_onlyMuons"].Fill(x, y)
                    h["UBT_PtvsP"].Fill(pT, p)
                    h["MuonP_xy"].Fill(x,y,p)
                    h["MuonPtP"].Fill(pT,p)

                if ahit.PdgCode() == 13 or ahit.PdgCode() == -13 or ahit.PdgCode() == 211 or ahit.PdgCode() == -211:
                    h["MuonFlux_andPion"].Fill(x,y)
                if ahit.PdgCode() == 22:
                    h["GammaFlux"].Fill(x,y)
                    h["GammaP_xy"].Fill(x,y,p)
                if ahit.PdgCode() == 11 or ahit.PdgCode()==-11:
                    h["ElecFlux"].Fill(x,y)
                    h["ElecP_xy"].Fill(x,y,p)




        # Process vetoPoint
        if hasattr(sTree, "vetoPoint"):
            for ahit in sTree.vetoPoint:
                h["SBT_pdgcode"].Fill(abs(ahit.PdgCode()))
                if ahit.PdgCode() == 13 or ahit.PdgCode() == -13: 
                    x, y = ahit.GetX(), ahit.GetY()
                    Px, Py, Pz = ahit.GetPx(), ahit.GetPy(), ahit.GetPz()
                    momentum = ROOT.TVector3(Px, Py, Pz)
                    pT = momentum.Perp()
                    p = momentum.Mag()
                    h["SBT_PtvsP"].Fill(pT, p)
                    h["SBTHitMap"].Fill(x, y)

        h["nUpstreamHits"].Fill(UBT_nHits)
        h["nSBTHits"].Fill(SBT_nHits)
        h["SBT_efficiency"].Fill(SBT_flag)
        h["UBT_efficiency"].Fill(UBT_flag)

# Save Histograms
output_file = "/eos/user/g/gvasquez/SHiP/Physics/Plots/UBT_extension.root"
output = ROOT.TFile(output_file, "RECREATE")
canvas = ROOT.TCanvas("canvas", "", 800, 600)
h["UpstreamHitMap"].Write()
h["UpstreamHitMapZ"].Write()
h["UpstreamHitMap_onlyMuons"].Write()
h["SBTHitMap"].Write()
h["MuonFlux"].Write()
h["MuonPtP"].Write()
h["UBT_PtvsP"].Write()
h["SBT_PtvsP"].Write()
h["nUpstreamHits"].Write()
h["UBT_pdgcode"].Write()
h["SBT_pdgcode"].Write()
h["SBT_efficiency"].Write()
h["UBT_efficiency"].Write()
h["MuonP_xy"].Draw("colz")
canvas.Write("MuonP_xy")
h["ElecP_xy"].Draw("colz")
canvas.Write("ElecP_xy")
h["GammaP_xy"].Draw("colz")
canvas.Write("GammaP_xy")
h["MuonFlux"].Write()
h["MuonFlux_andPion"].Write()
h["ElecFlux"].Write()
h["GammaFlux"].Write()

canvas.Close()
output.Close()

print("Analysis completed and output saved.")

