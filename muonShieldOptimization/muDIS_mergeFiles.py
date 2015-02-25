import ROOT,os
import rootUtils as ut
h={}
def merge():
 sTree = ROOT.TChain('DIS')
 for i in range(0,12):
  fn = "muonDis_"+str(i)+".root"
  sTree.AddFile(fn)
 fm    = ROOT.TFile("test.root","recreate")
 nTree = ROOT.TTree('DIS','muon DIS')
 iMuon       = ROOT.TClonesArray("TVectorD") 
 iMuonBranch = nTree.Branch("InMuon",iMuon,32000,-1)
 dPart       = ROOT.TClonesArray("TVectorD") 
 dPartBranch = nTree.Branch("Particles",dPart,32000,-1)
 for n in range(sTree.GetEntries()):
   sTree.GetEvent(n)
   dPart.Clear()
   iMuon.Clear()
   iMuon[0] = sTree.InMuon[0]
   for part in sTree.Particles:
      nPart = dPart.GetEntries()
      if dPart.GetSize() == nPart: dPart.Expand(nPart+10)
      dPart[nPart] = part
   dPartBranch.Fill()
   iMuonBranch.Fill()
   nTree.Fill()
 fm.cd()
 nTree.Write()
 fm.Close()
def hadd():
 cmd = 'hadd -f muonDIS.root '
 for i in range(0,12):
  cmd+= " muonDis_"+str(i)+".root "
 os.system(cmd)
def makePlots(sTree):
 ut.bookHist(h,'muP','muon mom',100,0.,400.)
 ut.bookHist(h,'nOut','outgoing part',100,-0.5,99.5)
 ut.bookHist(h,'pos','position',100,-25.,100.,100,-12.,12.,100,-13.,13.)
 for n in range(sTree.GetEntries()):
   rc = sTree.GetEvent(n)
   inMu = sTree.InMuon[0]
   w = inMu[8]
   P = ROOT.TMath.Sqrt(inMu[1]**2+inMu[2]**2+inMu[3]**2)
   rc = h['muP'].Fill(P,w)
   rc = h['nOut'].Fill(sTree.Particles.GetEntries() )
   rc = h['pos'].Fill(inMu[7],inMu[5],inMu[6] )
def test(fn = "test.root"):
 fm    = ROOT.TFile(fn)
 sTree = fm.DIS
 makePlots(sTree)


