import ROOT
import rootUtils as ut
import shipunit  as u

fn = 'ship.Pythia8-TGeant4.root'
# fn = 'ship.Genie-TGeant4.root'

f = ROOT.TFile(fn)
sTree   = f.FindObjectAny('cbmsim')
nEvents = sTree.GetEntries()
sFol  = f.FindObjectAny('cbmroot')
MCTracks   = ROOT.TClonesArray("FairMCTrack")
TrackingHits   = ROOT.TClonesArray("vetoPoint")

h={}

def exMCTracks():
 ut.bookHist(h,'pz','pz',100,0.,100.)
 ut.bookHist(h,'oz','oz',100,-10000.,10000.)
 ut.bookHist(h,'ex','ex to det',100,-2.5,2.5,100,-2.5,2.5)
 ut.bookHist(h,'N','N tracks',300,0.5,299.5)
# 
 sTree.SetBranchAddress("MCTrack", MCTracks)
 detPos = (3.5*u.m+70*u.m+40*u.m-100*u.m)
 for n in range(nEvents):
  rc = sTree.GetEvent(n) 
  nMCTracks = MCTracks.GetEntriesFast() 
  rc = h['N'].Fill( nMCTracks )
  for i in range(nMCTracks):
   atrack = MCTracks.At(i)
   pdgCode = atrack.GetPdgCode()
   mom = ROOT.TLorentzVector()
   atrack.Get4Momentum(mom)
   if abs(pdgCode)==13 or abs(pdgCode)==211:  
    rc = h['pz'].Fill( mom.Pz() )
    rc = h['oz'].Fill( atrack.GetStartZ() )  
    lam = ( detPos-atrack.GetStartZ() )/mom.Pz()
    xdet = (atrack.GetStartX()+lam*mom.Px() )/u.m
    ydet = (atrack.GetStartY()+lam*mom.Py() )/u.m
    rc = h['ex'].Fill(xdet,ydet ) 
 h['N'].Draw('box')

def exMCHits(dump=False):
 ut.bookHist(h,'tz','tracking hits z',100,-100.,100.)
 ut.bookHist(h,'tztx','tracking hits x vs z',1000,-40.,40.,100,-2.5,2.5)
 ut.bookHist(h,'txty','tracking hits y vs x',100,-2.5,2.5,100,-2.5,2.5)
 sTree.SetBranchAddress("vetoPoint", TrackingHits)
 for n in range(nEvents):
  rc = sTree.GetEvent(n) 
  nHits = TrackingHits.GetEntriesFast() 
  for i in range(nHits):
    ahit = TrackingHits.At(i)
    rc = h['tz'].Fill( ahit.GetZ()/u.m )
    rc = h['txty'].Fill( ahit.GetX()/u.m,ahit.GetY()/u.m )
    rc = h['tztx'].Fill( ahit.GetZ()/u.m,ahit.GetX()/u.m ) 
 h['tztx'].Draw('box') 
 if dump:
  for n in range( min(10,nEvents) ):
   rc = sTree.GetEvent(n) 
   nHits = TrackingHits.GetEntriesFast() 
   for i in range(nHits):
    ahit = TrackingHits.At(i)
    print ahit.GetZ()/u.m, ahit.GetDetectorID(),ahit.GetLength(),ahit.GetEnergyLoss() 
