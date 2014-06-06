# example for accessing smeared hits and fitted tracks
import ROOT 
import rootUtils as ut
import shipunit as u
import ShipGeo

ROOT.gSystem.Load("libgenfit2.so")
PDG = ROOT.TDatabasePDG.Instance()

bfield = ROOT.genfit.BellField(ShipGeo.Bfield.max ,ShipGeo.Bfield.z )
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)

f     = ROOT.TFile('ship.Pythia8-TGeant4_rec.root')
sTree = f.cbmsim

ev     = ut.PyListOfLeaves()                           
leaves = sTree.GetListOfLeaves()
names  = ut.setAttributes(ev,leaves)

MCTracks       = ROOT.TClonesArray("FairMCTrack")
TrackingHits   = ROOT.TClonesArray("vetoPoint")
fitTrack2MC    = ROOT.std.vector('int')()
sTree.SetBranchAddress("vetoPoint", TrackingHits)
sTree.SetBranchAddress("MCTrack", MCTracks)
sTree.SetBranchAddress("fitTrack2MC", fitTrack2MC)

h={}
ut.bookHist(h,'delPOverP','delP / P',100,0.,50.,100,-0.2,0.2)
ut.bookHist(h,'delPOverP2','delP / P chi2<25',100,0.,50.,100,-0.2,0.2)
ut.bookHist(h,'chi2','chi2 after trackfit',100,0.,1000.)
ut.bookHist(h,'IP','Impact Parameter',100,0.,10.)
ut.bookHist(h,'HNL','reconstructed Mass',100,0.,2.)

def makePlots():
   ut.bookCanvas(h,key='fitresults',title='Fit Results',nx=1600,ny=1200,cx=2,cy=2)
   cv = h['fitresults'].cd(1)
   h['delPOverP'].Draw('box')
   cv = h['fitresults'].cd(2)
   cv.SetLogy(1)
   h['chi2'].Draw()
   cv = h['fitresults'].cd(3)
   h['delPOverP_proj'] = h['delPOverP'].ProjectionY()
   ROOT.gStyle.SetOptFit(11111)
   h['delPOverP_proj'].Draw()
   h['delPOverP_proj'].Fit('gaus')
   cv = h['fitresults'].cd(4)
   h['delPOverP2_proj'] = h['delPOverP2'].ProjectionY()
   h['delPOverP2_proj'].Draw()
   h['delPOverP2_proj'].Fit('gaus')  
   h['fitresults'].Print('fitresults.gif')
   ut.bookCanvas(h,key='fitresults2',title='Fit Results',nx=1600,ny=1200,cx=2,cy=2)
   cv = h['fitresults2'].cd(1)
   h['IP'].Draw()
   cv = h['fitresults2'].cd(2)
   h['HNL'].Draw()
   h['HNL'].Fit('gaus') 
   h['fitresults2'].Print('fitresults2.gif')

# start event loop
nEvents = sTree.GetEntries()
for n in range(nEvents):
  rc = sTree.GetEntry(n)
  key = 0
  fittedTracks = {}
  for atrack in ev.FitTracks.GetObject(): 
   fitStatus   = atrack.getFitStatus()
   if not fitStatus.isFitConverged() : continue
   fittedTracks[key] = atrack
# needs different study why fit has not converged, continue with fitted tracks
   chi2        = fitStatus.getChi2()
   fittedState = atrack.getFittedState()
   h['chi2'].Fill(chi2)
   P = fittedState.getMomMag()
   mcPartKey = fitTrack2MC[key] 
   mcPart    = MCTracks[mcPartKey]
   Ptruth    = mcPart.GetP()
   delPOverP = (Ptruth - P)/Ptruth
   h['delPOverP'].Fill(Ptruth,delPOverP)
   if chi2<25: h['delPOverP2'].Fill(Ptruth,delPOverP)
# try measure impact parameter
   trackDir = fittedState.getDir()
   trackPos = fittedState.getPos()
   vx = ROOT.TVector3()
   mcPart.GetStartVertex(vx)
   t = 0
   for i in range(3):   t += trackDir(i)*(vx(i)-trackPos(i)) 
   dist = 0
   for i in range(3):   dist += (vx(i)-trackPos(i)-t*trackDir(i))**2
   dist = ROOT.TMath.Sqrt(dist)
   h['IP'].Fill(dist) 
   key+= 1  
# ---
# go for 2-track combinations
  if len(fittedTracks) == 2:
    LV = {}
    key = 0
    for tr in fittedTracks: 
     LV[key] = ROOT.TLorentzVector()
     mom = fittedTracks[tr].getFittedState().getMom()
     mcPartKey = fitTrack2MC[key] 
     mcPart    = MCTracks[mcPartKey]
     pgdCode   = mcPart.GetPdgCode()
     mass      = PDG.GetParticle(pgdCode).Mass()
     E = ROOT.TMath.Sqrt(mom.Mag2()+mass**2) 
     LV[key].SetPxPyPzE(mom.x(),mom.y(),mom.z(),E)
     key+= 1  
    HNL = LV[0]+LV[1]
    h['HNL'].Fill(HNL.M())

makePlots()


def access2SmearedHits():
 key = 0
 for ahit in ev.SmearedHits.GetObject():
   print ahit[0],ahit[1],ahit[2],ahit[3],ahit[4],ahit[5],ahit[6]
   # follow link to true MCHit
   mchit   = TrackingHits[key]
   mctrack =  MCTracks[mchit.GetTrackID()]
   print mchit.GetZ(),mctrack.GetP(),mctrack.GetPdgCode()
   key+=1


