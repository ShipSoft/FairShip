import ROOT
path = "./"
fs = ['ship.10.0.nuRadiography-TGeant4.root']
ROOT.gROOT.cd()
myHist = ROOT.TH3F('myh','radio',500,-10000,10000,100,-300,300,100,-600,600)
myHist2 = ROOT.TH3F('myh2','radio',500,-3000,3000,100,-300,300,100,-600,600)

for x in fs:
  fl = ROOT.TFile(path+x)
  sTree=fl.cbmsim
  ROOT.gROOT.cd()
  for n in range(sTree.GetEntries()):
    rc=sTree.GetEvent(n)
    nu = sTree.MCTrack[0]
    myHist.Fill(nu.GetStartZ(),nu.GetStartX(),nu.GetStartY(),nu.GetWeight())
    myHist2.Fill(nu.GetStartZ(),nu.GetStartX(),nu.GetStartY(),nu.GetWeight())
  fl.Close()
myHist.SetStats(0)
myHist.SetXTitle('Z [m]')
myHist.SetZTitle('Y [m]')
myHist.SetYTitle('X [m]')

c1 = ROOT.gROOT.FindObject('c1')
myHist.Draw('box')
c1.Print('radio.png')
myHistxy = myHist.Project3D('xy')
myHistxz = myHist.Project3D('xz')
myHistyz = myHist.Project3D('yz')
myHistxy.SetStats(0)
myHistxz.SetStats(0)
myHistyz.SetStats(0)

myHistxy.SetTitle('radio xz projection')
myHistxy.Draw('colz')
c1.Print('radioxz.png')
myHistxz.SetTitle('radio yz projection')
myHistxz.Draw('colz')
c1.Print('radioyz.png')
