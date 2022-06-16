#!/usr/bin/env python 
from __future__ import print_function
import ROOT,os,sys,time,shipRoot_conf
ROOT.gROOT.ProcessLine('#include "FairModule.h"')
time.sleep(20)

import shipunit as u
from ShipGeoConfig import ConfigRegistry

mcEngine     = "TGeant4"
runnr        = 1
nev          = 1000000

setup = {}
# 
setup['NA62'] = {'thickness': 125*u.cm/2., 'material':'krypton','momentum': 10*u.GeV,'maxTheta':350*u.GeV} # 3000s for 5M
# rad length 4.71cm  125/4.71 = 27
# https://indico.in2p3.fr/event/420/contributions/29860/attachments/24033/29479/moriond.pdf
setup['ATLAS'] = {'thickness': 172*u.cm/2., 'material':'iron','momentum': 350*u.GeV,'maxTheta':350*u.GeV} # 3000s for 5M
# atlas testbeam http://cds.cern.ch/record/1123152/files/CERN-THESIS-2008-070.pdf?version=1 
# LArEM ~24X0  TileCal 4 compartments, same size LiqAr rad length 14cm
# http://cds.cern.ch/record/1263861/files/ATL-CAL-PUB-2010-001.pdf    tile cal mainly iron, LAr 1.35 DM 0.63 TileCal 8.18
# iron intlen 16.97 -> (1.35 + 0.63 + 8.18)*16.97

setup['Fig3'] = {'thickness': 0.1*u.cm, 'material':'lead','momentum': 2*u.GeV,'maxTheta':0.2}
setup['Fig4'] = {'thickness': 0.1*u.cm, 'material':'lead','momentum': 8*u.GeV,'maxTheta':0.04}
setup['Fig5'] = {'thickness': 0.1*u.cm, 'material':'lead','momentum': 14*u.GeV,'maxTheta':0.02}

setup['Fig6'] = {'thickness': 1.44*u.cm, 'material':'copper','momentum': 11.7*u.GeV,'maxTheta':0.045}
setup['Fig7'] = {'thickness': 1.44*u.cm, 'material':'copper','momentum': 7.3*u.GeV,'maxTheta':0.045}

s = sys.argv[1]
thickness = setup[s]['thickness']
material = setup[s]['material']
momentum = setup[s]['momentum']
maxTheta = setup[s]['maxTheta']

checkOverlap = True
storeOnlyMuons = True

outFile = "msc"+s+".root"
theSeed      = 0
ecut      = 0.0

import rootUtils as ut 
h={}

def run():
# -------------------------------------------------------------------
 ROOT.gRandom.SetSeed(theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
 shipRoot_conf.configure()      # load basic libraries, prepare atexit for python
 # ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = 10, tankDesign = 5, muShieldDesign = 7, nuTauTargetDesign=1)
# -----Timer--------------------------------------------------------
 timer = ROOT.TStopwatch()
 timer.Start()
# -----Create simulation run----------------------------------------
 gFairBaseContFact = ROOT.FairBaseContFact() # required by change to FairBaseContFact to avoid TList::Clear errors
 run = ROOT.FairRunSim()
 run.SetName(mcEngine)  # Transport engine
 if nev==0: run.SetOutputFile("dummy.root")
 else: run.SetOutputFile(outFile)  # Output file
 run.SetUserConfig("g4Config.C") # user configuration file default g4Config.C
 rtdb = run.GetRuntimeDb() 
# -----Materials----------------------------------------------
 run.SetMaterials("media.geo")  
# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 cave.SetGeometryFileName("cave.geo")
 run.AddModule(cave)
#
 target = ROOT.simpleTarget()
 material, thickness, 0
#
 target.SetEnergyCut(ecut*u.GeV) 
 if storeOnlyMuons: target.SetOnlyMuons()
 target.SetParameters(material,thickness,0.)
 run.AddModule(target)
#
 primGen = ROOT.FairPrimaryGenerator()
 myPgun  = ROOT.FairBoxGenerator(13,1) # pdg id  and multiplicity
 if s=="NA62": myPgun.SetPRange(momentum,maxTheta)
 else: myPgun.SetPRange(momentum-0.01,momentum+0.01)
 myPgun.SetPhiRange(0,0) # // Azimuth angle range [degree]
 myPgun.SetThetaRange(0,0) # // Polar angle in lab system range [degree]
 myPgun.SetXYZ(0.*u.cm, 0.*u.cm, -1.*u.mm - (thickness) )
 primGen.AddGenerator(myPgun)
#
 run.SetGenerator(primGen)
# -----Initialize simulation run------------------------------------
 run.Init()
 if nev==0: return
 gMC = ROOT.TVirtualMC.GetMC()

 fStack = gMC.GetStack()
 fStack.SetMinPoints(1)
 fStack.SetEnergyCut(-1.)

# -----Start run----------------------------------------------------
 print("run for ",nev,"events")
 run.Run(nev)

# -----Start Analysis---------------
 ROOT.gROOT.ProcessLine('#include "Geant4/G4EmParameters.hh"')
 emP = ROOT.G4EmParameters.Instance()
 emP.Dump()
 h['f']= ROOT.gROOT.GetListOfFiles()[0].GetName()
# -----Finish-------------------------------------------------------
 timer.Stop()
 rtime = timer.RealTime()
 ctime = timer.CpuTime()
 print(' ') 
 print("Macro finished succesfully.") 
 print("Output file is ",  outFile) 
 print("Real time ",rtime, " s, CPU time ",ctime,"s")

def makePlot(f,book=True):
# print interaction and radiation length of target
 sGeo=ROOT.gGeoManager
 if sGeo:
  v = sGeo.FindVolumeFast('target')
  m = v.GetMaterial()
  length = v.GetShape().GetDZ()*2
  print("Material:",m.GetName(),'total interaction length=',length/m.GetIntLen(),'total rad length=',length/m.GetRadLen())
 else:
  density= 2.413
  length= 125.0
  print("Use predefined values:",density,length)
 if book:
  ut.bookHist(h,'theta','scattering angle '+str(momentum)+'GeV/c;{Theta}(rad)',500,0,maxTheta)
  ut.bookHist(h,'eloss','rel energy loss as function of momentum GeV/c',100,0,maxTheta,10000,0.,1.)
  ut.bookHist(h,'elossRaw','energy loss as function of momentum GeV/c',100,0,maxTheta, 10000,0.,100.)
 sTree = f.cbmsim
 for n in range(sTree.GetEntries()):
  rc = sTree.GetEvent(n)
  Ein  = sTree.MCTrack[0].GetEnergy()
  M = sTree.MCTrack[0].GetMass()
  Eloss = 0
  for aHit in sTree.vetoPoint: 
    Eloss+=aHit.GetEnergyLoss()
    print(Ein,Eloss/Ein)
  rc = h['eloss'].Fill(Ein,Eloss/Ein)
  rc = h['elossRaw'].Fill(Ein,Eloss)
 ut.bookCanvas(h,key=s,title=s,nx=900,ny=600,cx=1,cy=1)
 tc = h[s].cd(1)
 if s=="NA62":
  h['eloss'].Draw()
  h['95'] = h['eloss'].ProjectionX('95',96,100)
  h['95'].Sumw2()
  h['0'] = h['eloss'].ProjectionX('0',1,100)
  h['0'].Sumw2()
  rc = h['95'].Divide(h['0'] )
  h['95'].Draw()
  h['meanEloss'] = h['elossRaw'].ProjectionX()
  for n in range(1,h['elossRaw'].GetNbinsX()+1):
    tmp = h['elossRaw'].ProjectionY('tmp',n,n)
    eloss = tmp.GetMean()
    h['meanEloss'].SetBinContent(n,eloss/density/length*1000)
  h['meanEloss'].SetTitle('mean energy loss MeV cm2 / g')
  h['meanEloss'].Draw()
 elif s=="ATLAS":
  h['eloss'].Draw()
  h['>eloss']=h['eloss'].ProjectionY().Clone('>eloss')
  cum = 0
  N = float(h['>eloss'].GetEntries())
  for n in range(h['>eloss'].GetNbinsX(),0,-1):
    cum+=h['>eloss'].GetBinContent(n)
    h['>eloss'].SetBinContent(n,cum/N)
  print("Ethreshold   event fraction in %")
  for E in [15.,20.,30.,50.,80.]:
    n = h['>eloss'].FindBin(E/350.)
    print(" %5.0F   %5.2F "%(E,h['>eloss'].GetBinContent(n)*100))
 else:
  tc.SetLogy(1)
  h['theta_100']=h['theta'].Clone('theta_100')
  h['theta_100']=h['theta'].Rebin(5)
  h['theta_100'].Scale(1./h['theta_100'].GetMaximum())
  h['theta_100'].Draw()
  h[s].Print(s+'.png')
  h[s].Print(s+'.root')
  f.Write(h['theta'].GetName())
  f.Write(h['theta_100'].GetName())

def readChain():
  tmp = "/mnt/hgfs/microDisk/Data/mscNA62_X.root"
  for i in [0,1]:
   f = ROOT.TFile(tmp.replace('X',str(i)))
   if i==1: makePlot(f,False)
   else: makePlot(f)

def NA62():
 na62Points = open('NA62.points')
 allPoints = na62Points.readlines()
 N = int((len(allPoints)-1)/3.)
 h['NA62']=ROOT.TGraphErrors(N)
 for l in range(N):
  tmp = allPoints[3*l].split(',')
  x=float(tmp[0])
  y=float(tmp[1].replace('\n',''))
  tmp = allPoints[3*l+1].split(',')
  y1=float(tmp[1].replace('\n',''))
  tmp = allPoints[3*l+2].split(',')
  y2=float(tmp[1].replace('\n',''))
  h['NA62'].SetPoint(l,x,y*1E-6)
  h['NA62'].SetPointError(l,0,abs(y1-y2)/2.*1E-6)
  h['NA62'].SetLineColor(ROOT.kRed)
  h['NA62'].SetMarkerColor(ROOT.kRed)
  h['NA62'].SetMarkerStyle(20)

def makeSummaryPlot():
# using data in /mnt/hgfs/microDisk/Data/eloss/eloss_sum.root
# krypton total interaction length= 1.97246306079 total rad length= 26.5231000393 
 pdg={10.0:1.914,14.0:1.978,20.0:2.055,30.0:2.164,40.0:2.263,80.0:2.630,100.:2.810,140.:3.170,200.:3.720,277.:4.420,300.:4.631,400.:5.561}
 h['Gpdg'] = ROOT.TGraph(len(pdg))
 Gpdg = h['Gpdg']
 Gpdg.SetMarkerColor(ROOT.kRed)
 Gpdg.SetMarkerStyle(20)
 keys = sorted(pdg.keys())
 for n in range(len(keys)):
  Gpdg.SetPoint(n,keys[n],pdg[keys[n]])
 density= 2.413
 length= 125.0
 ut.readHists(h,"/mnt/hgfs/microDisk/Data/eloss/eloss_sum.root")
 ut.readHists(h,"/mnt/hgfs/microDisk/Data/eloss/eloss_withRaw.root")
 ut.bookCanvas(h,key='summary',title=" ",nx=1200,ny=600,cx=2,cy=1)
 tc = h['summary'].cd(1)
 h['0'] = h['eloss'].ProjectionX('0',1,h['eloss'].GetNbinsY())
 h['0'].Sumw2()
 NA62()
 for t in [93,95]:
  h[t] = h['eloss'].ProjectionX(str(t),int(h['eloss'].GetNbinsY()*t/100.),h['eloss'].GetNbinsY())
  h[t].Sumw2()
  h[t].SetStats(0)
  h[t].SetMarkerStyle(24)
  rc = h[t].Divide(h['0'] )
  h[t].Rebin(2)
  h[t].Scale(1./2.)
  if t!=93: 
    h[t].SetMarkerColor(ROOT.kBlue)
    h[t].Draw('same')
  else: 
    h[t].SetMaximum(1E-5)
    h[t].SetMarkerColor(ROOT.kMagenta)
    h[t].SetXTitle('incoming muon momentum [GeV/c]')
    h[t].SetYTitle('prob #DeltaE>X%')
    h[t].SetTitle('')
    h[t].Draw()
  h['NA62'].Draw('sameP')
 h['lg'] = ROOT.TLegend(0.53,0.79,0.98,0.94)
 h['lg'].AddEntry(h['NA62'],'NA62 measurement >95%','PL')
 h['lg'].AddEntry(h[95],'FairShip >95%','PL')
 h['lg'].AddEntry(h[93],'FairShip >93%','PL')
 h['lg'].Draw()
 tc = h['summary'].cd(2)
 h['meanEloss'] = h['elossRaw'].ProjectionX()
 for n in range(1,h['elossRaw'].GetNbinsX()+1):
    tmp = h['elossRaw'].ProjectionY('tmp',n,n)
    eloss = tmp.GetMean()
    h['meanEloss'].SetBinContent(n,eloss/density/length*1000)
    h['meanEloss'].SetBinError(n,0)
 h['meanEloss'].SetTitle('mean energy loss MeV cm^{2}/g')
 h['meanEloss'].SetStats(0)
 h['meanEloss'].SetMaximum(7.)
 h['meanEloss'].SetXTitle('incoming muon momentum [GeV/c]')
 h['meanEloss'].SetYTitle('mean energy loss [MeV cm^[2]]/g')
 h['meanEloss'].SetTitle('')
 h['meanEloss'].Draw()
 Gpdg.Draw('sameP')
 h['lg2'] = ROOT.TLegend(0.53,0.79,0.98,0.94)
 h['lg2'].AddEntry(h['Gpdg'],'muon dE/dx, PDG ','PL')
 h['lg2'].AddEntry(h['meanEloss'],'energy deposited in krypton, FairShip','PL')
 h['lg2'].Draw()
 h['summary'].Print('catastrophicEnergyLoss.png')
