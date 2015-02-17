import ROOT
path = "./"
fs = ['ship.10.0.nuRadiography-TGeant4.root']
ROOT.gROOT.cd()
myHist = ROOT.TH3F('myh','radio',500,-1000,1000,100,-300,300,100,-600,600)

for x in fs:
  fl = ROOT.TFile(path+x)
  sTree=fl.cbmsim
  ROOT.gROOT.cd()
  for n in range(sTree.GetEntries()):
    rc=sTree.GetEvent(n)
    nu = sTree.MCTrack[0]
    myHist.Fill(nu.GetStartZ()/10.,nu.GetStartX(),nu.GetStartY(),nu.GetWeight())
  fl.Close()
myHist.Draw('box')

