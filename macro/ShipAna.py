# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

# example for accessing smeared hits and fitted tracks
from argparse import ArgumentParser

import decorators
import math
import ROOT
import acts
import acts.examples
import rootUtils as ut
import shipRoot_conf
import shipunit as u
from ShipGeoConfig import load_from_root_file

shipRoot_conf.configure()
decorators.apply_decorators()
PDG = ROOT.TDatabasePDG.Instance()

chi2CutOff = 4.0
fiducialCut = False
measCutFK = 25
measCutPR = 22
docaCut = 2.0

parser = ArgumentParser()

parser.add_argument("-f", "--inputFile", dest="inputFile", help="Input file (MC simulation)", required=True)
parser.add_argument(
    "-r", "--recoFile", dest="recoFile", help="Reconstruction file (will be used as friend tree)", required=False
)
parser.add_argument(
    "-n", "--nEvents", dest="nEvents", help="Number of events to analyze", required=False, default=999999, type=int
)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="ROOT geofile", required=True)
parser.add_argument("--Debug", dest="Debug", help="Switch on debugging", required=False, action="store_true")
options = parser.parse_args()

# Determine reconstruction file
if not options.recoFile:
    # Default: replace .root with _rec.root, or if already _rec.root use as-is
    if options.inputFile.find("_rec.root") > 0:
        options.recoFile = options.inputFile
        options.inputFile = options.inputFile.replace("_rec.root", ".root")
    else:
        options.recoFile = options.inputFile.replace(".root", "_rec.root")

# Open MC simulation file
if not options.inputFile.find(",") < 0:
    sTree = ROOT.TChain("cbmsim")
    recoChain = ROOT.TChain("ship_reco_sim")
    for x in options.inputFile.split(","):
        sTree.AddFile(x)
    for x in options.recoFile.split(","):
        recoChain.AddFile(x)
    sTree.AddFriend(recoChain)
else:
    f = ROOT.TFile(options.inputFile)
    sTree = f["cbmsim"]
    # Add reconstruction data as friend tree
    sTree.AddFriend("ship_reco_sim", options.recoFile)

if not options.geoFile:
    options.geoFile = options.inputFile.replace("ship.", "geofile_full.").replace("_rec.", ".")
fgeo = ROOT.TFile(options.geoFile)

# new geofile, load Shipgeo dictionary written by run_simScript.py
ShipGeo = load_from_root_file(fgeo, "ShipGeo")
dy = ShipGeo.Yheight / u.m

# -----Create geometry----------------------------------------------
import shipDet_conf

run = ROOT.FairRunSim()
run.SetName("TGeant4")  # Transport engine
import tempfile

sink = ROOT.FairRootFileSink(tempfile.mktemp(suffix=".root"))
run.SetSink(sink)
ROOT.SetOwnership(sink, False)  # C++ FairRun takes ownership
run.SetUserConfig("g4Config_basic.C")  # geant4 transport not used, only needed for the mag field
rtdb = run.GetRuntimeDb()
# -----Create geometry----------------------------------------------
modules = shipDet_conf.configure(run, ShipGeo)

import geomGeant4

if hasattr(ShipGeo.Bfield, "fieldMap"):
    fieldMaker = geomGeant4.addVMCFields(ShipGeo, "", True, withVirtualMC=False)
else:
    print("no fieldmap given, geofile too old, not anymore support")
    exit(-1)
sGeo = fgeo["FAIRGeom"]


volDict = {}
i = 0
for x in ROOT.gGeoManager.GetListOfVolumes():
    volDict[i] = x.GetName()
    i += 1

# prepare veto decisions
import shipVeto

veto = shipVeto.Task(sTree)
vetoDets = {}
h = {}
ut.bookHist(h, "delPOverP", "delP / P", 400, 0.0, 200.0, 100, -0.5, 0.5)
ut.bookHist(h, "pullPOverPx", "delPx / sigma", 400, 0.0, 200.0, 100, -3.0, 3.0)
ut.bookHist(h, "pullPOverPy", "delPy / sigma", 400, 0.0, 200.0, 100, -3.0, 3.0)
ut.bookHist(h, "pullPOverPz", "delPz / sigma", 400, 0.0, 200.0, 100, -3.0, 3.0)
ut.bookHist(h, "delPOverP2", "delP / P chi2/nmeas<" + str(chi2CutOff), 400, 0.0, 200.0, 100, -0.5, 0.5)
ut.bookHist(h, "delPOverPz", "delPz / Pz", 400, 0.0, 200.0, 100, -0.5, 0.5)
ut.bookHist(h, "delPOverP2z", "delPz / Pz chi2/nmeas<" + str(chi2CutOff), 400, 0.0, 200.0, 100, -0.5, 0.5)
ut.bookHist(h, "chi2", "chi2/nmeas after trackfit", 100, 0.0, 10.0)
ut.bookHist(h, "prob", "prob(chi2)", 100, 0.0, 1.0)
ut.bookHist(h, "IP", "Impact Parameter", 100, 0.0, 10.0)
ut.bookHist(h, "Vzresol", "Vz reco - true [cm]", 100, -50.0, 50.0)
ut.bookHist(h, "Vxresol", "Vx reco - true [cm]", 100, -10.0, 10.0)
ut.bookHist(h, "Vyresol", "Vy reco - true [cm]", 100, -10.0, 10.0)
ut.bookHist(h, "Vzpull", "Vz pull", 100, -5.0, 5.0)
ut.bookHist(h, "Vxpull", "Vx pull", 100, -5.0, 5.0)
ut.bookHist(h, "Vypull", "Vy pull", 100, -5.0, 5.0)
ut.bookHist(h, "Doca", "Doca between two tracks", 100, 0.0, 10.0)
for x in ["", "_pi0"]:
    ut.bookHist(h, "IP0" + x, "Impact Parameter to target", 100, 0.0, 100.0)
    ut.bookHist(h, "IP0/mass" + x, "Impact Parameter to target vs mass", 100, 0.0, 2.0, 100, 0.0, 100.0)
    ut.bookHist(h, "HNL" + x, "reconstructed Mass", 500, 0.0, 2.0)
ut.bookHist(h, "HNLw", "reconstructed Mass with weights", 500, 0.0, 2.0)
ut.bookHist(h, "meas", "number of measurements", 40, -0.5, 39.5)
ut.bookHist(h, "meas2", "number of measurements, fitted track", 40, -0.5, 39.5)
ut.bookHist(h, "measVSchi2", "number of measurements vs chi2/meas", 40, -0.5, 39.5, 100, 0.0, 10.0)
ut.bookHist(h, "distu", "distance to wire", 100, 0.0, 1.0)
ut.bookHist(h, "distv", "distance to wire", 100, 0.0, 1.0)
ut.bookHist(h, "disty", "distance to wire", 100, 0.0, 1.0)
ut.bookHist(h, "meanhits", "mean number of hits / track", 50, -0.5, 49.5)

ut.bookHist(h, "extrapTimeDetX", "extrapolation to TimeDet X", 100, -10.0, 10.0)
ut.bookHist(h, "extrapTimeDetY", "extrapolation to TimeDet Y", 100, -10.0, 10.0)

ut.bookHist(h, "oa", "cos opening angle", 100, 0.999, 1.0)
# potential Veto detectors
ut.bookHist(h, "nrtracks", "nr of tracks in signal selected", 10, -0.5, 9.5)
ut.bookHist(h, "nrSBT", "nr of hits in SBT", 100, -0.5, 99.5)

import TrackExtrapolateTool


from array import array


def dist2InnerWall(X, Y, Z):
    dist = 0
    # return distance to inner wall perpendicular to z-axis, if outside decayVolume return 0.
    node = sGeo.FindNode(X, Y, Z)
    if "DecayVacuum" not in node.GetName():
        return dist
    start = array("d", [X, Y, Z])
    nsteps = 8
    dalpha = 2 * ROOT.TMath.Pi() / nsteps
    X**2 + Y**2
    minDistance = 100 * u.m
    for n in range(nsteps):
        alpha = n * dalpha
        sdir = array("d", [ROOT.TMath.Sin(alpha), ROOT.TMath.Cos(alpha), 0.0])
        node = sGeo.InitTrack(start, sdir)
        sGeo.FindNextBoundary()
        distance = sGeo.GetStep()
        if distance < minDistance:
            minDistance = distance
    return minDistance


def isInFiducial(X, Y, Z) -> bool:
    if not fiducialCut:
        return True
    if ShipGeo.TrackStation1.z < Z:
        return False
    # typical x,y Vx resolution for exclusive HNL decays 0.3cm,0.15cm (gaussian width)
    return not dist2InnerWall(X, Y, Z) < 5 * u.cm


#
def ImpactParameter(point, tPos, tMom):
    t = 0
    if hasattr(tMom, "P"):
        P = tMom.P()
    else:
        P = tMom.Mag()
    for i in range(3):
        t += tMom(i) / P * (point(i) - tPos(i))
    dist = 0
    for i in range(3):
        dist += (point(i) - tPos(i) - t * tMom(i) / P) ** 2
    dist = ROOT.TMath.Sqrt(dist)
    return dist


#
def checkHNLorigin(sTree) -> bool:
    flag = True
    if not fiducialCut:
        return flag
    flag = False
    # only makes sense for signal == HNL
    hnlkey = -1
    for n in range(len(sTree.MCTrack)):
        mo = sTree.MCTrack[n].GetMotherId()
        if mo < 0 or mo >= len(sTree.MCTrack):
            continue
        if abs(sTree.MCTrack[mo].GetPdgCode()) == 9900015:
            hnlkey = n
            break
    if hnlkey < 0:
        ut.reportError("ShipAna: checkHNLorigin, no HNL found")
    elif hnlkey >= len(sTree.MCTrack):
        ut.reportError("ShipAna: checkHNLorigin, HNL key out of bounds")
    else:
        # MCTrack after HNL should be first daughter
        theHNLVx = sTree.MCTrack[hnlkey]
        X, Y, Z = theHNLVx.GetStartX(), theHNLVx.GetStartY(), theHNLVx.GetStartZ()
        if isInFiducial(X, Y, Z):
            flag = True
    return flag


def checkFiducialVolume(sTree, tkey: int, dy) -> bool:
    # extrapolate track to middle of magnet and check if in decay volume
    inside = True
    if not fiducialCut:
        return True
    fT = sTree.RecoTracks[tkey]
    rc, pos_tuple, _mom = acts.extrapolateTrackToZ(fT, ShipGeo.Bfield.z)
    if not rc:
        return False
    posX, posY, posZ = pos_tuple[0], pos_tuple[1], pos_tuple[2]
    if not dist2InnerWall(posX, posY, posZ) > 0:
        return False
    return inside


def getPtruthFirst(sTree, mcPartKey):
    Ptruth, Ptruthx, Ptruthy, Ptruthz = -1.0, -1.0, -1.0, -1.0
    for ahit in sTree.strawtubesPoint:
        if ahit.GetTrackID() == mcPartKey:
            Ptruthx, Ptruthy, Ptruthz = ahit.GetPx(), ahit.GetPy(), ahit.GetPz()
            Ptruth = ROOT.TMath.Sqrt(Ptruthx**2 + Ptruthy**2 + Ptruthz**2)
            break
    return Ptruth, Ptruthx, Ptruthy, Ptruthz


def access2SmearedHits(ev, TrackingHits, MCTracks) -> None:
    key = 0
    for ahit in ev.SmearedHits.GetObject():
        print(ahit[0], ahit[1], ahit[2], ahit[3], ahit[4], ahit[5], ahit[6])
        # follow link to true MCHit
        mchit = TrackingHits[key]
        mctrack = MCTracks[mchit.GetTrackID()]
        print(mchit.GetZ(), mctrack.GetP(), mctrack.GetPdgCode())
        key += 1



def fitSingleGauss(x: str, ba: float | None = None, be: float | None = None) -> None:
    name = "myGauss_" + x
    myGauss = h[x].GetListOfFunctions().FindObject(name)
    if not myGauss:
        if not ba:
            ba = h[x].GetBinCenter(1)
        if not be:
            be = h[x].GetBinCenter(h[x].GetNbinsX())
        bw = h[x].GetBinWidth(1)
        mean = h[x].GetMean()
        sigma = h[x].GetRMS()
        norm = h[x].GetEntries() * 0.3
        myGauss = ROOT.TF1(name, "[0]*" + str(bw) + "/([2]*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)+[3]", 4)
        myGauss.SetParameter(0, norm)
        myGauss.SetParameter(1, mean)
        myGauss.SetParameter(2, sigma)
        myGauss.SetParameter(3, 1.0)
        myGauss.SetParName(0, "Signal")
        myGauss.SetParName(1, "Mean")
        myGauss.SetParName(2, "Sigma")
        myGauss.SetParName(3, "bckgr")
    if h[x].GetEntries() > 0:
        h[x].Fit(myGauss, "", "", ba, be)


def match2HNL(p) -> bool:
    matched = False
    hnlKey = []
    for t in [p.GetDaughter(0), p.GetDaughter(1)]:
        mcp = sTree.fitTrack2MC[t]
        while mcp > -0.5:
            if mcp >= len(sTree.MCTrack):
                break
            mo = sTree.MCTrack[mcp]
            if abs(mo.GetPdgCode()) == 9900015:
                hnlKey.append(mcp)
                break
            mcp = mo.GetMotherId()
    if len(hnlKey) == 2 and hnlKey[0] == hnlKey[1]:
        matched = True
    return matched


def makePlots() -> None:
    ut.bookCanvas(h, key="strawanalysis", title="Distance to wire and mean nr of hits", nx=1200, ny=600, cx=3, cy=1)
    cv = h["strawanalysis"].cd(1)
    h["disty"].Draw()
    h["distu"].Draw("same")
    h["distv"].Draw("same")
    cv = h["strawanalysis"].cd(2)
    h["meanhits"].Draw()
    cv = h["strawanalysis"].cd(3)
    h["meas2"].Draw()
    ut.bookCanvas(h, key="fitresults", title="Fit Results", nx=1600, ny=1200, cx=2, cy=2)
    cv = h["fitresults"].cd(1)
    h["delPOverPz"].Draw("box")
    cv = h["fitresults"].cd(2)
    cv.SetLogy(1)
    h["prob"].Draw()
    cv = h["fitresults"].cd(3)
    h["delPOverPz_proj"] = h["delPOverPz"].ProjectionY()
    ROOT.gStyle.SetOptFit(11111)
    h["delPOverPz_proj"].Draw()
    if h["delPOverPz_proj"].GetEntries() > 0:
        h["delPOverPz_proj"].Fit("gaus")
    cv = h["fitresults"].cd(4)
    h["delPOverP2z_proj"] = h["delPOverP2z"].ProjectionY()
    h["delPOverP2z_proj"].Draw()
    fitSingleGauss("delPOverP2z_proj")
    h["fitresults"].Print("fitresults.gif")
    for x in ["", "_pi0"]:
        ut.bookCanvas(h, key="fitresults2" + x, title="Fit Results " + x, nx=1600, ny=1200, cx=2, cy=2)
        cv = h["fitresults2" + x].cd(1)
        if x == "":
            h["Doca"].SetXTitle("closest distance between 2 tracks   [cm]")
            h["Doca"].SetYTitle("N/1mm")
            h["Doca"].Draw()
        else:
            h["pi0Mass"].SetXTitle("#gamma #gamma invariant mass   [GeV/c^{2}]")
            h["pi0Mass"].SetYTitle("N/" + str(int(h["pi0Mass"].GetBinWidth(1) * 1000)) + "MeV")
            h["pi0Mass"].Draw()
            if h["pi0Mass"].GetEntries() > 0:
                h["pi0Mass"].Fit("gaus", "S", "", 0.08, 0.19)
        cv = h["fitresults2" + x].cd(2)
        h["IP0" + x].SetXTitle("impact parameter to p-target   [cm]")
        h["IP0" + x].SetYTitle("N/1cm")
        h["IP0" + x].Draw()
        cv = h["fitresults2" + x].cd(3)
        h["HNL" + x].SetXTitle("inv. mass  [GeV/c^{2}]")
        h["HNL" + x].SetYTitle("N/4MeV/c2")
        h["HNL" + x].Draw()
        fitSingleGauss("HNL" + x, 0.9, 1.1)
        cv = h["fitresults2" + x].cd(4)
        h["IP0/mass" + x].SetXTitle("inv. mass  [GeV/c^{2}]")
        h["IP0/mass" + x].SetYTitle("IP [cm]")
        h["IP0/mass" + x].Draw("colz")
        h["fitresults2" + x].Print("fitresults2" + x + ".gif")
    ut.bookCanvas(h, key="vxpulls", title="Vertex resol and pulls", nx=1600, ny=1200, cx=3, cy=2)
    cv = h["vxpulls"].cd(4)
    h["Vxpull"].Draw()
    cv = h["vxpulls"].cd(5)
    h["Vypull"].Draw()
    cv = h["vxpulls"].cd(6)
    h["Vzpull"].Draw()
    cv = h["vxpulls"].cd(1)
    h["Vxresol"].Draw()
    cv = h["vxpulls"].cd(2)
    h["Vyresol"].Draw()
    cv = h["vxpulls"].cd(3)
    h["Vzresol"].Draw()
    ut.bookCanvas(h, key="trpulls", title="momentum pulls", nx=1600, ny=600, cx=3, cy=1)
    cv = h["trpulls"].cd(1)
    h["pullPOverPx_proj"] = h["pullPOverPx"].ProjectionY()
    h["pullPOverPx_proj"].Draw()
    cv = h["trpulls"].cd(2)
    h["pullPOverPy_proj"] = h["pullPOverPy"].ProjectionY()
    h["pullPOverPy_proj"].Draw()
    cv = h["trpulls"].cd(3)
    h["pullPOverPz_proj"] = h["pullPOverPz"].ProjectionY()
    h["pullPOverPz_proj"].Draw()
    ut.bookCanvas(h, key="vetodecisions", title="Veto Detectors", nx=1600, ny=600, cx=2, cy=1)
    cv = h["vetodecisions"].cd(1)
    cv.SetLogy(1)
    h["nrtracks"].Draw()
    cv = h["vetodecisions"].cd(2)
    cv.SetLogy(1)
    h["nrSBT"].Draw()
    #
    print("finished making plots")


# start event loop
def myEventLoop(n: int) -> None:
    rc = sTree.GetEntry(n)
    # check if tracks are made from real pattern recognition
    measCut = measCutFK
    if sTree.GetBranch("FitTracks_PR"):
        sTree.FitTracks = sTree.FitTracks_PR
        measCut = measCutPR
    if sTree.GetBranch("fitTrack2MC_PR"):
        sTree.fitTrack2MC = sTree.fitTrack2MC_PR
    if sTree.GetBranch("Particles_PR"):
        sTree.Particles = sTree.Particles_PR
    if not checkHNLorigin(sTree):
        return
    if not len(sTree.MCTrack) > 1:
        wg = 1.0
    else:
        wg = sTree.MCTrack[1].GetWeight()
    if not wg > 0.0:
        wg = 1.0

        # make some straw hit analysis
    hitlist = {}
    for ahit in sTree.strawtubesPoint:
        detID = ahit.GetDetectorID()
        top = ROOT.TVector3()
        bot = ROOT.TVector3()
        modules["strawtubes"].StrawEndPoints(detID, bot, top)
        dw = ahit.dist2Wire()
        if detID < 50000000:
            if abs(top.y()) == abs(bot.y()):
                h["disty"].Fill(dw)
            if abs(top.y()) > abs(bot.y()):
                h["distu"].Fill(dw)
            if abs(top.y()) < abs(bot.y()):
                h["distv"].Fill(dw)
        #
        trID = ahit.GetTrackID()
        if not trID < 0:
            if trID in hitlist:
                hitlist[trID] += 1
            else:
                hitlist[trID] = 1
    for tr in hitlist:
        h["meanhits"].Fill(hitlist[tr])
    key = -1
    for atrack in sTree.RecoTracks:
        key += 1
        # kill tracks outside fiducial volume
        if not checkFiducialVolume(sTree, key, dy):
            continue
        nmeas = atrack.nDoF()
        h["meas"].Fill(nmeas)

        h["meas2"].Fill(nmeas)
        if nmeas < measCut:
            continue
        # needs different study why fit has not converged, continue with fitted tracks
        rchi2 = atrack.chi2()
        prob = ROOT.TMath.Prob(rchi2, int(nmeas))
        h["prob"].Fill(prob)
        chi2 = rchi2 / nmeas

        h["chi2"].Fill(chi2, wg)
        h["measVSchi2"].Fill(atrack.nMeasurements(), chi2)
        p = math.hypot(atrack.px(), atrack.py(), atrack.pz())
        Px, Py, Pz = atrack.px(), atrack.py(), atrack.pz()
        cov = atrack.GetCovarianceElements()
        if len(sTree.fitTrack2MC) - 1 < key:
            continue
        mcPartKey = sTree.fitTrack2MC[key]
        if mcPartKey < 0 or mcPartKey >= len(sTree.MCTrack):
            continue
        mcPart = sTree.MCTrack[mcPartKey]
        mcPart.GetP()
        mcPart.GetPz()
        # get p truth from first strawpoint
        Ptruth, Ptruthx, Ptruthy, Ptruthz = getPtruthFirst(sTree, mcPartKey)
        delPOverP = (Ptruth - P) / Ptruth
        h["delPOverP"].Fill(Ptruth, delPOverP)
        delPOverPz = (1.0 / Ptruthz - 1.0 / Pz) * Ptruthz
        h["pullPOverPx"].Fill(Ptruth, (Ptruthx - Px) / ROOT.TMath.Sqrt(cov[3][3]))
        h["pullPOverPy"].Fill(Ptruth, (Ptruthy - Py) / ROOT.TMath.Sqrt(cov[4][4]))
        h["pullPOverPz"].Fill(Ptruth, (Ptruthz - Pz) / ROOT.TMath.Sqrt(cov[5][5]))
        h["delPOverPz"].Fill(Ptruthz, delPOverPz)
        if chi2 > chi2CutOff:
            continue
        h["delPOverP2"].Fill(Ptruth, delPOverP)
        h["delPOverP2z"].Fill(Ptruth, delPOverPz)
        # try measure impact parameter
        trackDir = ROOT.TVector3(atrack.px()/p, atrack.py()/p, atrack.pz()/p)
        trackPos = ROOT.TVector3(atrack.x(), atrack.y(), atrack.z())
        vx = ROOT.TVector3()
        mcPart.GetStartVertex(vx)
        t = 0
        for i in range(3):
            t += trackDir(i) * (vx(i) - trackPos(i))
        dist = 0
        for i in range(3):
            dist += (vx(i) - trackPos(i) - t * trackDir(i)) ** 2
        dist = ROOT.TMath.Sqrt(dist)
        h["IP"].Fill(dist)
    # ---
    # loop over particles, 2-track combinations
    vertexKey = -1
    for HNL in sTree.Particles:
        vertexKey += 1
        t1, t2 = HNL.GetDaughter(0), HNL.GetDaughter(1)
        # kill tracks outside fiducial volume, if enabled
        if not checkFiducialVolume(sTree, t1, dy) or not checkFiducialVolume(sTree, t2, dy):
            continue
        checkMeasurements = True
        # cut on nDOF
        for tr in [t1, t2]:
            fitStatus = sTree.RecoTracks[tr]
            nmeas = fitStatus.nDoF()
            if nmeas < measCut:
                checkMeasurements = False
        if not checkMeasurements:
            continue
            # check mc matching
        if not match2HNL(HNL):
            continue
        HNLPos = ROOT.TLorentzVector()
        HNL.ProductionVertex(HNLPos)
        HNLMom = ROOT.TLorentzVector()
        HNL.Momentum(HNLMom)
        doca = HNL.GetDoca()
        # redo doca calculation
        # xv,yv,zv,doca,HNLMom  = RedoVertexing(t1,t2)
        # if HNLMom == -1: continue
        # check if decay inside decay volume
        if not isInFiducial(HNLPos.X(), HNLPos.Y(), HNLPos.Z()):
            continue
        h["Doca"].Fill(doca)
        if doca > docaCut:
            continue
        tr = ROOT.TVector3(0, 0, ShipGeo.target.z0)

        # look for pi0
        """
    for pi0 in pi0Reco.findPi0(sTree,HNLPos):
       rc = h['pi0Mass'].Fill(pi0.M())
       if abs(pi0.M()-0.135)>0.02: continue
# could also be used for eta, by changing cut
       HNLwithPi0 =  HNLMom + pi0
       dist = ImpactParameter(tr,HNLPos,HNLwithPi0)
       mass = HNLwithPi0.M()
       h['IP0_pi0'].Fill(dist)
       h['IP0/mass_pi0'].Fill(mass,dist)
       h['HNL_pi0'].Fill(mass)
    """

        dist = ImpactParameter(tr, HNLPos, HNLMom)
        mass = HNLMom.M()
        h["IP0"].Fill(dist)
        h["IP0/mass"].Fill(mass, dist)
        h["HNL"].Fill(mass)
        h["HNLw"].Fill(mass, wg)
        #
        vetoDets["SBT"] = veto.SBT_decision()
        vetoDets["UBT"] = veto.UBT_decision()
        vetoDets["TRA"] = veto.Track_decision()
        h["nrtracks"].Fill(vetoDets["TRA"][2])
        h["nrSBT"].Fill(vetoDets["SBT"][2])
        #   HNL true
        mcTrackIdx = sTree.fitTrack2MC[t1]
        if mcTrackIdx < 0 or mcTrackIdx >= len(sTree.MCTrack):
            continue
        mctrack = sTree.MCTrack[mcTrackIdx]
        h["Vzresol"].Fill((mctrack.GetStartZ() - HNLPos.Z()) / u.cm)
        h["Vxresol"].Fill((mctrack.GetStartX() - HNLPos.X()) / u.cm)
        h["Vyresol"].Fill((mctrack.GetStartY() - HNLPos.Y()) / u.cm)
        PosDir, newPosDir, CovMat, _scalFac = {}, {}, {}, {}
        # opening angle at vertex
        newPos = ROOT.TVector3(HNLPos.X(), HNLPos.Y(), HNLPos.Z())
        st1, st2 = sTree.RecoTracks[t1], sTree.RecoTracks[t2]

        #Get the smoothed parameters at the vertex
        vtx_acts = sTree.RecoVertices[vertexKey]

        vtx_px = vtx_acts.trackPx()
        vtx_py = vtx_acts.trackPy()
        vtx_pz = vtx_acts.trackPz()
        if len(vtx_px) >= 2:
            mom1 = ROOT.TVector3(vtx_px[0], vtx_py[0], vtx_pz[0])
            mom2 = ROOT.TVector3(vtx_px[1], vtx_py[1], vtx_pz[1])
        else:
            mom1 = ROOT.TVector3(st1.px(), st1.py(), st1.pz())
            mom2 = ROOT.TVector3(st2.px(), st2.py(), st2.pz())

        oa = mom1.Dot(mom2) / (mom1.Mag() * mom2.Mag())
        h["oa"].Fill(oa)
        #
        covX = HNL.GetCovV()
        dist = HNL.GetDoca()
        h["Vzpull"].Fill((mctrack.GetStartZ() - HNLPos.Z()) / ROOT.TMath.Sqrt(covX[5]))
        h["Vxpull"].Fill((mctrack.GetStartX() - HNLPos.X()) / ROOT.TMath.Sqrt(covX[0]))
        h["Vypull"].Fill((mctrack.GetStartY() - HNLPos.Y()) / ROOT.TMath.Sqrt(covX[3]))

    # check extrapolation to TimeDet if exists
    if hasattr(ShipGeo, "TimeDet"):
        for fT in sTree.RecoTracks:
            rc, pos_tuple, _mom = acts.extrapolateTrackToZ(fT, ShipGeo.Bfield.z)
            if rc:
                posX, posY, posZ = pos_tuple[0], pos_tuple[1], pos_tuple[2]
                for aPoint in sTree.TimeDetPoint:
                    h["extrapTimeDetX"].Fill(posX - aPoint.GetX())
                    h["extrapTimeDetY"].Fill(posY - aPoint.GetY())


#
def HNLKinematics() -> None:
    HNLorigin = {}
    ut.bookHist(h, "HNLmomNoW", "momentum unweighted", 100, 0.0, 300.0)
    ut.bookHist(h, "HNLmom", "momentum", 100, 0.0, 300.0)
    ut.bookHist(h, "HNLPtNoW", "Pt unweighted", 100, 0.0, 10.0)
    ut.bookHist(h, "HNLPt", "Pt", 100, 0.0, 10.0)
    ut.bookHist(h, "HNLmom_recTracks", "momentum", 100, 0.0, 300.0)
    ut.bookHist(h, "HNLmomNoW_recTracks", "momentum unweighted", 100, 0.0, 300.0)
    for n in range(sTree.GetEntries()):
        sTree.GetEntry(n)
        for hnlkey in [1, 2]:
            if hnlkey >= len(sTree.MCTrack):
                continue
            if abs(sTree.MCTrack[hnlkey].GetPdgCode()) == 9900015:
                theHNL = sTree.MCTrack[hnlkey]
                wg = theHNL.GetWeight()
                if not wg > 0.0:
                    wg = 1.0
                if hnlkey - 1 < 0 or hnlkey - 1 >= len(sTree.MCTrack):
                    continue
                idMother = abs(sTree.MCTrack[hnlkey - 1].GetPdgCode())
                if idMother not in HNLorigin:
                    HNLorigin[idMother] = 0
                HNLorigin[idMother] += wg
                P = theHNL.GetP()
                Pt = theHNL.GetPt()
                h["HNLmom"].Fill(P, wg)
                h["HNLmomNoW"].Fill(P)
                h["HNLPt"].Fill(Pt, wg)
                h["HNLPtNoW"].Fill(Pt)                
                for HNL in sTree.Particles:
                    t1, t2 = HNL.GetDaughter(0), HNL.GetDaughter(1)
                    for tr in [t1, t2]:
                        xx = sTree.RecoTracks[tr]
                        Prec = math.hypot(xx.px(), xx.py(), xx.pz())
                        h["HNLmom_recTracks"].Fill(Prec, wg)
                        h["HNLmomNoW_recTracks"].Fill(Prec)
    theSum = 0
    for x in HNLorigin:
        theSum += HNLorigin[x]
    for x in HNLorigin:
        print("%4i : %5.4F relative fraction: %5.4F " % (x, HNLorigin[x], HNLorigin[x] / theSum))


#
sTree.GetEvent(0)
options.nEvents = min(sTree.GetEntries(), options.nEvents)

# import pi0Reco
ut.bookHist(h, "pi0Mass", "gamma gamma inv mass", 100, 0.0, 0.5)

for n in range(options.nEvents):
    myEventLoop(n)
    #sTree.FitTracks.clear()
makePlots()
# output histograms
hfile = options.inputFile.split(",")[0]
if "_rec" in hfile:
    hfile = hfile.replace("_rec", "_ana")
else:
    hfile = hfile.replace(".root", "_ana.root")
if "/eos" in hfile or not options.inputFile.find(",") < 0:
    # do not write to eos, write to local directory
    tmp = hfile.split("/")
    hfile = tmp[len(tmp) - 1]
ROOT.gROOT.cd()
ut.writeHists(h, hfile)
