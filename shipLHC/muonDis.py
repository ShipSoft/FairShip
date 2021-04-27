#!/usr/bin/env python 
import ROOT,os,sys
import shipunit as u
from array import array
import rootUtils as ut
import time
from argparse import ArgumentParser
theSeed      = 0
ROOT.gRandom.SetSeed(theSeed)
PDG = ROOT.TDatabasePDG.Instance()
rnr = ROOT.TRandom()

flukaDict = {10:-13,11:13}

pids = [-3222, -2212, -321, -211,-13, -11, 11,13, 211, 321, 2212, 3112]
pidsDict = {}
pidsDictRev = {}
for i in range(len(pids)): 
     pidsDict[i] = pids[i]
     pidsDictRev[pids[i]] = i
muonMass  = 0.105658

normalization       = {}
normalization[0] = 5.83388
normalization[1] = normalization[0]*137.13/78.      # number of p-p collisions in FLUKA simulation 0 / FLUKA simulation 1
normalization[2] = normalization[0]*137.13/14.3     # number of p-p collisions in FLUKA simulation 0 / FLUKA simulation 2
normalization[3] = normalization[0]*137.13/50.     # number of p-p collisions in FLUKA simulation 0 / FLUKA simulation 3, muons_VCdown_IR1-LHC

h         = {}

SND_Z = 483.262*u.m
Eloss = 30.  # energy loss in 75m of rock

function = "13.6/1000.*sqrt([0])/x*(1.+0.038*log([0]))"
h['MS'] = ROOT.TF1('MS',function,0,10000)
h['MS'].SetParName(0,'X/X0')
# https://pdg.lbl.gov/2020/AtomicNuclearProperties/HTML/standard_rock.html
xOverX0 = 75*u.m/10.02*u.cm
h['MS'].SetParameter(0,xOverX0)

EnergyScan = [10,20,30,40,50,75,100,200,300,400,500,1000,2000,3000,4000,5000,6000,7000,8000,10000]

def photoabsorb(eps):
  return 114.3 + 1.647*(ROOT.TMath.Log(0.0213*eps))**2
def G(x):
 return 3./x**3*(x**2/2.-1.+ROOT.TMath.Exp(-x)*(1+x))
def nucl_cross(Ebeam,eps,A):
 # returns xsec in microbarns
 # A in g / mol ??
 Mmu = muonMass
 m1sq = 0.54 
 m2sq = 1.8
 alpha = 1./137.03599976
 nu = eps/Ebeam
 t = Mmu**2*nu**2/(1.-nu)
 k = 1.-2./nu+2./nu**2
 x = 0.00282*ROOT.TMath.Power(A,1./3.)*photoabsorb(eps) 
 if eps<5: sigma = 0  
 # if eps<3: sigma = 0 # 3.8.2015, test, text (PDG) says, <5 GeV not reliable 
 else: sigma = alpha/(2.*ROOT.TMath.Pi())*A*photoabsorb(eps)*nu*(0.75*G(x)*(k*ROOT.TMath.Log(1+m1sq/t) - \
         k*m1sq/(m1sq+t) - 2.*Mmu**2/t)+0.25*(k*ROOT.TMath.Log(1+m2sq/t)- 2.*Mmu**2/t) + \
         Mmu**2/(2.*t)*(0.75*G(x)*m1sq/(m1sq+t)+0.25*m2sq/t*ROOT.TMath.Log(1.+t/m2sq))) 
 return sigma

def SigmaAnalytic(Ebeam=5000.,A=1,nsteps = 10000):
    gname  = 'xsec_'+str(A)
    h[gname]   = ROOT.TGraph(nsteps)
    deps = Ebeam/float(nsteps)
    eps  = deps/2.
    for i in range(nsteps):
       sigma = nucl_cross(Ebeam,eps,A)
       h[gname].SetPoint(i,eps/Ebeam,sigma)
       eps+=deps

def SigmaAnalyticVsEnergy(A=1):
 nsteps = len(EnergyScan)
 gname = 'AnalyticCross_'+str(A)
 h[gname] = ROOT.TGraph(nsteps)
 h[gname].SetName(gname)
 i=0
 for Ebeam in EnergyScan: 
    SigmaAnalytic(Ebeam,A)
    h[gname].SetPoint(i,Ebeam, h['xsec_'+str(A)].Integral()/A/1000.)   # convert to mbarns
    i+=1

def SigmaAnalyticVsA(Ebeam=500):
 nsteps = 100
 gname = 'AnalyticCross_'+str(Ebeam)
 h[gname] = ROOT.TGraph(nsteps)
 h[gname].SetName(gname)
 i=0
 for A in range(1,nsteps+1): 
    SigmaAnalytic(Ebeam,A)
    h[gname].SetPoint(i,A, h['xsec_'+str(A)].Integral()/1000.)   # convert to mbarns
    i+=1
parser = ArgumentParser()
parser.add_argument("-b", "--heartbeat",  dest="heartbeat", type=int,  help="progress report",            default=10000)
parser.add_argument("-n", "--nEvents",    dest="nEvents",   type=int,  help="number of events",           default=1000000)
parser.add_argument("-s", "--firstEvent", dest="nStart",    type=int,  help="first event",                default=0)
parser.add_argument("-r", "--run",        dest="run",       type=int,  help="production sequence number", default=0)
parser.add_argument('-M', '--Emin',       dest='Emin',      type=float,help="cutOff",                     default=1.0)
parser.add_argument('-f', '--inputFile',  dest='muonIn',               help="input file with muons")
parser.add_argument('-c', '--command',    dest='command',              help="command")
parser.add_argument('-x', '--nMult',      dest='nMult',     type=int,  help="option to re-use muon",      default=1)
parser.add_argument('-N', '--nucleon',      dest='nucleon',     type=str,  help="nucleon for muon DIS pythia6",      default="p+")
parser.add_argument('-z', '--zextrap',      dest='z',     type=float,  help="muon extrapolation",      default=-5*u.m)
parser.add_argument('-P', '--pythia6',      dest='pythia6',     type=int,  help="pythia6 or not pythia6",      default=1)

options = parser.parse_args()

def myPrint(tc,tname,pathToPlots = "/mnt/hgfs/microDisk/CERNBOX/SND@LHC/MuonDis/"):
   for z in ['.png','.pdf','.root']:
      tc.Print(tname+z)
      os.system('mv '+tname+z+' '+pathToPlots)

def convertAscii2Root(fname,version=2):
# convert fluka ascii table into root tntuple
# /mnt/hgfs/microDisk/SND/MuonDis/unit30_Nm  unit30_Pm
# version 0:  col 0 is the run number
#                        col 1 is the event number
#                        col 2 is the FLUKA particle type (10=muon+,11=muon-) 
#                        col 3 is the  generation number (1 is a direct p-p collision product) 
#                        col 4 is the  kinetic energy in GeV 
#                        col 5 is the statistical weight 
#                        col 6 is the x coordinate in cm (x=0 is as IP1, with the x-axis  pointing outside the ring on the hor plane) 
#                        col 7 is the y coordinate  in cm (y=0 is as IP1, with the y-axis pointing opposite to the  gravity) 
#                        col 8 is the direction cosine wrt x-axis 
#                        col 9 is the direction cosine wrt y-axis 
#                        col 10 is the particle age in s (0 is the  p-p collision time) 
#                        col 11 is useless

# version 2: no change for columns 0 to 9, column 10 contains the z-coordinate (in cm) at the scoring plane
 # Col 10: z coord (cm)
 # Col 11: Last decay x cooord (cm)
 # Col 12: Last decay y cooord (cm)
 # Col 13: Last decay z cooord (cm)
 # Col 14: Last decay ID
 # Col 15: Last interaction x cooord (cm)
 # Col 16: Last interaction y cooord (cm)
 # Col 17: Last interaction z cooord (cm)
 # Col 18: Last interaction ID

   f = open(fname)
   variables = "run:event:id:generation:E:w:x:y:px:py:t:z:pz"
                         # 0        1         2        3               4  5 6 7  8   9  10 11 12
   fntuple = ROOT.TFile.Open(fname+'.root', 'RECREATE')
   nt  = ROOT.TNtupleD("nt","muon",variables)
   for l in f.readlines():
       if not l.find('#')<0: continue
       tmp  = l.replace('\n','').split(' ')
       line = []
       column = []
       for x in tmp:
          if x!='': line.append(float(x))
# convert to more standard variables
       column.append(line[0])
       column.append(line[1])
       column.append(flukaDict[line[2]])
       column.append(line[3])
       E         = line[4] + muonMass
       P         = ROOT.TMath.Sqrt(E*E-muonMass*muonMass)
       column.append(E)
       column.append(line[5])
       column.append(line[6])
       column.append(line[7])
       column.append(P*line[8])
       column.append(P*line[9])
       if version == 2:
              column.append(0)        # time had been dropped unfortunately
              column.append(line[10])
       else:
             column.append(line[10]*u.s)
             if version == 0:   column.append(409.*u.m)
             if version == 1:  column.append(418.684*u.m + line[6]*ROOT.TMath.Tan(2.338/180.*ROOT.TMath.Pi()))
       column.append(P*ROOT.TMath.Sqrt(1-line[8]**2-line[9]**2))
       theTuple  = array('d',column)
       nt.Fill(theTuple)
   fntuple.cd()
   nt.Write()

def muonPreTransport():
    f = ROOT.TFile(options.muonIn)
    nt = f.nt
    foutName = options.muonIn.replace('.root','_z'+str(options.z)+'.root')
    fout  = ROOT.TFile(foutName,'recreate')
    variables = ""
    for n in range(nt.GetListOfLeaves().GetEntries()):  
          variables+=nt.GetListOfLeaves()[n].GetName()
          if n < nt.GetListOfLeaves().GetEntries()-1: variables+=":"
    sTree =  ROOT.TNtupleD("nt","muon",variables)
    for n in range(nt.GetEntries()):
     rc = nt.GetEvent(n)
     E = nt.E - 27.
     if E>0:
           column = []
           lam = ((options.z+SND_Z)-nt.z)/nt.pz
           for n in range(nt.GetListOfLeaves().GetEntries()):
                val = nt.GetListOfLeaves()[n].GetValue()
                if nt.GetListOfLeaves()[n].GetName()=='E':  val = E
                if nt.GetListOfLeaves()[n].GetName()=='x':  val = nt.x+lam*nt.px
                if nt.GetListOfLeaves()[n].GetName()=='y':  val = nt.y+lam*nt.py
                if nt.GetListOfLeaves()[n].GetName()=='z':  val = options.z+SND_Z
                column.append(val)
           theTuple  = array('d',column)
           rc = sTree.Fill(theTuple)
    sTree.AutoSave()
    fout.Close()

masssq = {}

def getMasssq(pid):
  apid = abs(int(pid))
  if not apid in masssq:
    masssq[apid] = PDG.GetParticle(apid).Mass()**2
  return masssq[apid]
def rotate(ctheta,stheta,cphi,sphi,px,py,pz):
  #rotate around y-axis
  px1=ctheta*px+stheta*pz
  pzr=-stheta*px+ctheta*pz
  #rotate around z-axis
  pxr=cphi*px1-sphi*py
  pyr=sphi*px1+cphi*py
  return pxr,pyr,pzr

import sys
def getPythiaCrossSec(nstat,pmom=[]):
    if len(pmom)==0:
       pmom=[5.,10.,15.,20.,25.,50.,75.,100.,150.,200.,250,300.,400.,500.,750.,1000.,1500.,2500.,5000.,7500.,10000.]
    mutype = {-13:'gamma/mu+',13:'gamma/mu-'}
    for pid in mutype:
       h['g_'+str(pid)] = ROOT.TGraph()
       h['g_'+str(pid)].SetName('g_'+str(pid))
       np = 0
       for P in pmom:
          myPythia = ROOT.TPythia6()
          myPythia.SetMSEL(2)       # msel 2 includes diffractive parts
          myPythia.SetPARP(2,2)     # To get below 10 GeV, you have to change PARP(2)
          R = int(time.time()%900000000)
          myPythia.SetMRPY(1,R)
# stop pythia printout during loop
          myPythia.SetMSTU(11, 11)
          myPythia.Initialize('FIXT',mutype[pid],'p+',P)
          for n in range(nstat):
              myPythia.GenerateEvent()
# very ugly procedure, but myPythia.GetPyint5() does not work!
          myPythia.Pystat(0)
          myPythia.Pystat(0)
          xsec = readXsec(myPythia)
          h['g_'+str(pid)].SetPoint(np,P,xsec)
          np+=1
    fout = ROOT.TFile('muDIScrossSec.root','RECREATE')
    for pid in mutype: h['g_'+str(pid)].Write()

def readXsec(p):
   f = open("fort.11")
   tmp = None
   X = f.readlines()
   for i in range(1,len(X)):
       l = X[len(X)-i]
       if l.find('All included')<0: continue
       tmp = l.replace("\n",'').split('I')
       break
   if not tmp: 
       print("empty file")
       return 0
   return float(tmp[3].replace('D','E'))

def makeMuDISEvents(withElossFunction=False,nucleon='p+'):
# for energy loss:
    if withElossFunction:
       ut.readHists(h,"meanEloss.root")
       eLoss = h['TCeloss'].FindObject('pol3').Clone('eLoss')
#
    myPythia = ROOT.TPythia6()
    myPythia.SetMSEL(2)       # msel 2 includes diffractive parts
    myPythia.SetPARP(2,2)     # To get below 10 GeV, you have to change PARP(2)
    for kf in [211,321,130,310,3112,3122,3222,3312,3322,3334]:
        kc = myPythia.Pycomp(kf) 
        myPythia.SetMDCY(kc,1,0)
    R = int(time.time()%900000000)
    myPythia.SetMRPY(1,R)
    mutype = {-13:'gamma/mu+',13:'gamma/mu-'}
# DIS event
# incoming muon,      id:px:py:pz:x:y:z:w
# outgoing particles, id:px:py:pz
    fout  = ROOT.TFile('muonDis_'+str(options.run)+'.root','recreate')
    dTree = ROOT.TTree('DIS','muon DIS')
    iMuon       = ROOT.TClonesArray("TParticle") 
    iMuonBranch = dTree.Branch("InMuon",iMuon,32000,-1)
    dPart       = ROOT.TClonesArray("TParticle") 
    dPartBranch = dTree.Branch("Particles",dPart,32000,-1)
# read file with muons hitting concrete wall
    fin = ROOT.TFile(options.muonIn) # id:px:py:pz:x:y:z:w
    sTree = fin.nt
    nTOT  = sTree.GetEntries()
    nEnd  = min(nTOT,options.nStart + options.nEvents)
# stop pythia printout during loop
    myPythia.SetMSTU(11, 11)
    print("start production ",options.nStart,nEnd)
    nMade = 0
    for k in range(options.nStart,nEnd):
      rc = sTree.GetEvent(k)
# make n events / muon
      px,py,pz = sTree.px,sTree.py,sTree.pz
      x,y,z    = sTree.x,sTree.y,sTree.z-SND_Z
      pid,w = int(sTree.id),sTree.w
      if withElossFunction:
          E  = sTree.E - eLoss.Eval(sTree.E) # energy loss in 75m of rock
      else:
          E = sTree.E -27.
      p  =  ROOT.TMath.Sqrt(px*px+py*py+pz*pz)
      Peloss  = ROOT.TMath.Sqrt(E*E-muonMass*muonMass)
      if E < 5. : continue
      t = sTree.t
  # px=p*sin(theta)cos(phi),py=p*sin(theta)sin(phi),pz=p*cos(theta)
      theta = ROOT.TMath.ACos(pz/p)
      phi     = ROOT.TMath.ATan2(py,px) 
      ctheta,stheta = ROOT.TMath.Cos(theta),ROOT.TMath.Sin(theta)
      cphi,sphi     = ROOT.TMath.Cos(phi),ROOT.TMath.Sin(phi)
      escale = Peloss/p
      muPart = ROOT.TParticle(pid,0,0,0,0,0,px*escale,py*escale,pz*escale,E,x,y,z,t)
      muPart.SetWeight(w)
      myPythia.Initialize('FIXT',mutype[pid],nucleon,E)
      for n in range(options.nMult):
         dPart.Clear()
         iMuon.Clear()
         iMuon[0] = muPart
         myPythia.GenerateEvent()
# remove all unnecessary stuff
         myPythia.Pyedit(2)
         for itrk in range(1,myPythia.GetN()+1):
            did = myPythia.GetK(itrk,2)
            dpx,dpy,dpz = rotate(ctheta,stheta,cphi,sphi,myPythia.GetP(itrk,1),myPythia.GetP(itrk,2),myPythia.GetP(itrk,3))
            psq =   dpx**2+dpy**2+dpz**2
            E = ROOT.TMath.Sqrt(getMasssq(did)+psq)
            part = ROOT.TParticle(did,0,0,0,0,0,dpx,dpy,dpz,E,x,y,z,t)
            part.SetWeight(w/float(options.nMult))
# copy to branch
            nPart = dPart.GetEntries()
            if dPart.GetSize() == nPart: dPart.Expand(nPart+10)
            dPart[nPart] = part
         nMade+=1
         if nMade%options.heartbeat==0: print('made so far  ',options.run,' :',nMade,time.ctime())
         dTree.Fill()
    fout.cd()  
    dTree.Write()
    myPythia.SetMSTU(11, 6)
    print("finished ",options.run)
def checkProdofMuDIS():
   redfac3d=100
   for pid in [13,-13]:
      ut.bookHist(h,"xyz_mu_"+str(pid),   'x/y /z',200,-100.,100.,200,-100.,100.,int(600/redfac3d) ,-500.,100.)
   for r in range(1,11):
      for z in [0,1000]:
            f=ROOT.TFile('/home/truf/ubuntu-1710/ship-ubuntu-1710-64/SND/MuonDis/Muons Extended Scoring Plane/muonDis_'+str(z+r)+'.root')
            for sTree in f.DIS:
                    for m in sTree.InMuon:
                              rc   = h['xyz_mu_'+str(m.GetPdgCode())].Fill(m.Vx(),m.Vy(),m.Vz())
   ut.bookCanvas(h,'muDIS_inMu','incoming muon',1500,900,2,1)
   c=h['muDIS_inMu'].cd(1)
   for x in ['13','-13']:
       h["xy_mu_"+x] = h["xyz_mu_"+x].Project3D('yx')
       h["xy_mu_"+x].SetName("xy_mu_"+x)
       h["xy_mu_"+x].SetStats(0)
       h["xy_mu_"+x].SetTitle(PDG.GetParticle(int(x)).GetName()+' ;x  [cm]; y  [cm]')
       h["xy_mu_"+x].Draw('colz')
       c=h['muDIS_inMu'].cd(2)
   myPrint(h['muDIS_SND2'],'inMu_XY')

def analyze(inFile):
    NinteractionLength = 3
    fin = ROOT.TFile('muDIScrossSec.root')
    ROOT.gROOT.cd()
    for pid in ['13','-13']: 
           h['g_'+pid] = fin.Get('g_'+pid).Clone('g_'+pid)
           ut.bookHist(h,'inMu_'+str(pid),'Energy',200,0.,5000.,20,0.0,19.5)
           ut.bookHist(h,'xy_In'+str(pid),  ' x/y muon In',120,-60.,60.,120,-60.,60.)
    ut.bookCanvas(h,'sec','xsec',900,600,1,1)
    ut.bookHist(h,'muDISXsec',';E  [GeV];#sigma [mb]',100,0.,10000.)
    h['sec'].cd(1)
    h['muDISXsec'].SetMinimum(0.)
    h['muDISXsec'].SetMaximum(30.E-3)
    h['muDISXsec'].Draw()
    h['muDISXsec'].SetStats(0)
    h['g_13'] .SetLineColor(ROOT.kGreen)
    h['g_13'] .SetLineWidth(4)
    h['g_13'] .Draw('same')
    h['g_-13'] .Draw('same')
    h['sec'].Print('muonXsec.png')

    h['sTree'] = ROOT.TChain('DIS')
    sTree  = h['sTree']
    for cycle in range(options.nMult):
     for run in range(1,11):
       for k in [0,1000]:
           f = ROOT.TFile('muonDis_'+str(run+cycle*100+k)+'.root')
           if not f.Get('DIS'):
               print("file corrupted ",run+cycle*100+k)
               continue
           sTree.AddFile('muonDis_'+str(run+cycle*100+k)+'.root')
    newFile = ROOT.TFile('muonDIS_SND.root','RECREATE')
    newTree = sTree.CloneTree(0)
    ROOT.gROOT.cd()
    for nt in sTree:
             muon = nt.InMuon[0]
             muonEnergy = muon.Energy()
             pid = muon.GetPdgCode()
             wLHC = 5.83388*muon.GetWeight()/options.nMult/10.  # ( options.nMult = number of cycles, 10 events per incoming muon in each cycle)
             wDis = NinteractionLength * 97.5 / 1.67E-24 * h['g_'+str(pid)].Eval(muonEnergy ) * 1E-27
             out  = nt.Particles
             rc = h['inMu_'+str(pid)].Fill(muonEnergy,out.GetEntries(),wLHC*wDis)
            # place interaction point 5m in front of SND
             z_int = -500.
             lam = (  (SND_Z-z_int)-muon.Vz() ) / muon.Pz()
             mxex = muon.Vx()+lam*muon.Px()
             myex = muon.Vy()+lam*muon.Py()
# missing update of time of flight
             rc = h['xy_In'+str(muon.GetPdgCode())].Fill(mxex,myex,muon.GetWeight())
             neutralParticles = []
             chargedParticles = []
             veto  = False
             for p in out:
                pid = p.GetPdgCode()
                E     = p.Energy()
                hname = "E_"+str(pid)
                if not hname in h:     
                    ut.bookHist(h,hname,'Energy',1000,0.,5000.)
                    ut.bookHist(h,'2dEsnd_'+str(pid),  'E in SND',1000,0.,5000.,100,0.,5000.)
                    ut.bookHist(h,'test1_'+str(pid),  'E in SND',100,0.,5000.)
                    ut.bookHist(h,'test2_'+str(pid),  'E in SND',100,0.,5000.)
                    ut.bookHist(h,'origin_xy'+str(pid),  'E in SND',100,-100.,100.,100,-100.,100.)
                    ut.bookHist(h,'2dEsnd_Veto_'+str(pid),  'E in SND',1000,0.,5000.,100,0.,5000.)
                    ut.bookHist(h,'Veto_mult_'+str(pid),  'veto multiplicity',100,0.,100.)
                    ut.bookHist(h,"xy_"+str(pid),  'x/y ',120,-60.,60.,120,-60.,60.)
                rc = h[hname].Fill(E,p.GetWeight())
                lamP = (SND_Z-z_int)/p.Pz()
                xex = mxex + lamP*p.Px()
                yex = myex + lamP*p.Py()
                rc    = h["xy_"+str(pid)].Fill(xex,yex,p.GetWeight())
                if abs(pid) in [211,321,13,2212]:  chargedParticles.append([pid,E])
# counting in 15<y<57, 8<x<49
# weight including interaction length,    concrete interaction length = 42.4cm, 97.5 g/cm^2 
#                                         Mproton = 1.67 10^-24 g, 1mb = 10^-27 cm^2
# muon weight: add up the statistical weights
#   divide by the number of simulated p-p collisions (137,130,000) and 
#   multiply by the actual collision rate (i.e. 8E8 at the nominal lumi of 1E34 cm-2 s-1):   5.83388
                if -8 > xex and xex >-49 and 15 < yex and yex < 57:
                   if  pid in [130,2112,-2112]:   neutralParticles.append([pid,E,muonEnergy,wDis*wLHC])
                   rc = h["2dEsnd_"+str(pid)].Fill(E,muonEnergy ,wDis*wLHC)
                   rc = h["test1_"+str(pid)].Fill(muonEnergy ,wLHC)
                   rc = h["test2_"+str(pid)].Fill(muonEnergy)
                   if abs(pid) in [211,321,13,2212]:
                          if E > 1*u.GeV: veto  = True
# end loop over out particles 
             for x in neutralParticles:
                   rc = h["Veto_mult_"+str(x[0])].Fill(len(chargedParticles))
                   if len(chargedParticles)>0:  rc = h['origin_xy'+str(x[0])].Fill(mxex,myex,x[3])
                   if not veto and len(neutralParticles)==1:
                           rc = h["2dEsnd_Veto_"+str(x[0])].Fill(x[1],x[2],x[3])
             if len(neutralParticles)>0:  rc = newTree.Fill()

#
    newFile.Write()
    ut.bookCanvas(h,'muDIS_SND2','incoming muon energy',1500,900,2,1)
    c=h['muDIS_SND2'].cd(1)
    hname = "inMuEsnd_2112"  # example
    h[hname] = h["2dEsnd_2112" ].ProjectionY(hname)
    ut.makeIntegralDistrib(h,hname)
    h['I-'+hname].SetTitle('incoming muon energy;> E [GeV/c];N arbitrary units')
    h['I-'+hname].SetMinimum(1.E-6)
    # h['I-'+hname].SetMaximum(90)
    h['I-'+hname].SetStats(0)
    h['I-'+hname].SetLineWidth(3)
    h['I-'+hname].Draw('hist')
    c=h['muDIS_SND2'].cd(2)
    h[hname].SetTitle('incoming muon energy; E [GeV/c];N arbitrary units')
    h[hname].SetStats(0)
    h[hname].SetLineWidth(3)
    h[hname].Draw('hist')
    h['muDIS_SND2'].Print('inMuEnergy.png')
    parts = [130,2112,-2112]
    for pid in parts:
      hname = "Esnd_"+str(pid)
      h[hname] = h["2dEsnd_"+str(pid)].ProjectionX(hname)
      h["Esnd_Veto_"+str(pid)] = h["2dEsnd_Veto_"+str(pid)].ProjectionX("Esnd_Veto_"+str(pid))
      ut.makeIntegralDistrib(h,hname)
      h['I-'+hname].GetXaxis().SetRangeUser(0.,1000.)
      h['I-'+hname].SetMinimum(1E-6)
      ut.makeIntegralDistrib(h,"Esnd_Veto_"+str(pid))
    ut.bookCanvas(h,'muDIS_SND','Kl and neutrons arriving at SND',2500,900,3,1)
    for k in range(len(parts)):
# 1E34 cm-2 s-1, 1fb = 1e-39 cm2, means 1fb requires 1E5 sec
        fbScale = 1E5
        tc=h['muDIS_SND'].cd(k+1)
        tc.SetLogy(1)
        pname = PDG.GetParticle(parts[k]).GetName()
        hname          = "Esnd_"+str(parts[k])
        hnameVeto = "Esnd_Veto_"+str(parts[k])
        for X in [hname,hnameVeto]:
           h['IFB-'+X] = h['I-'+X].Clone('IFB-'+X)
           h['IFB-'+X].Scale(150.*fbScale)
           h['IFB-'+X].SetTitle(pname+';> E [GeV/c];N /150 fb^{-1}')
           h['IFB-'+X]. GetYaxis().SetTitleOffset(1.4)
           h['IFB-'+X].SetMaximum(90*150.)
           h['IFB-'+X].SetStats(0)
           h['IFB-'+X].SetLineWidth(3)
           h['IFB-'+X].SetMinimum(0.1)
        h['IFB-'+hname].Draw('hist')
        h['IFB-'+hnameVeto].SetLineColor(ROOT.kRed)
        h['IFB-'+hnameVeto].Draw('histsame')
        hist = h['I-'+hname]
        histVeto = h['I-Esnd_Veto_'+str(parts[k])]
        R =  hist.GetBinContent(1)
        RVeto =  histVeto.GetBinContent(1)
        print("                        %s:   %5.2F N/sec   %5.2F  N fb  with Veto: %5.2F  N fb "%(pname,R,R*fbScale,RVeto*fbScale))
        R = hist.GetBinContent(3)
        RVeto = histVeto.GetBinContent(3)
        print("E>10GeV,    %s:  %5.2F N/sec   %5.2F  N fb  with Veto: %5.2F  N fb "%(pname,R,R*fbScale,RVeto*fbScale))
        R = hist.GetBinContent(21)
        RVeto= histVeto.GetBinContent(21)
        print("E>100GeV, %s:  %5.2E N/sec  %5.2F N fb  with Veto: %5.2F  N fb "%(pname,R,R*fbScale,RVeto*fbScale))
        R = hist.GetBinContent(41)
        RVeto= histVeto.GetBinContent(41)
        print("E>200GeV, %s:  %5.2E N/sec  %5.2F N fb  with Veto: %5.2F  N fb "%(pname,R,R*fbScale,RVeto*fbScale))
        R = hist.GetBinContent(101)
        RVeto = histVeto.GetBinContent(101)
        print("E>500GeV, %s:  %5.2E N/sec  %5.2F N fb  with Veto: %5.2F  N fb "%(pname,R,R*fbScale,RVeto*fbScale))
    h['muDIS_SND'].Print('muDIS_SND.png')
    h['muDIS_SND'].Print('muDIS_SND.pdf')
def muonRateAtSND(withFaser=False,withEff=False,version=1):
    norm = normalization[version]
    if withEff:
       ut.readHists(h,"efficiency.root")
       h['efficiency'] = h['eff'].FindObject('eloss_px').Clone('efficiency')
       fname = 'pol4'
       rc = h['efficiency'].Fit(fname,'S','',20,300.)
       effFun = h['efficiency'].GetFunction(fname)
       effPMax = 200.
       ut.readHists(h,"meanEloss.root")
       eLoss = h['TCeloss'].FindObject('pol3').Clone('eLoss')
    Rmult = 100  # if 1,  MS scattering replaced by efficiency
    fnames = {13:"unit30_Nm.root",-13:"unit30_Pm.root"}
    ut.bookCanvas(h,'muDIS_SNDXY_1','muons',1200,900,1,1)
    ut.bookCanvas(h,'muDIS_SNDXY_2','muons',1200,900,1,1)
    ut.bookCanvas(h,'muDIS_SNDE','muons',1200,900,1,1)
    for mu in fnames:
      fin   = ROOT.TFile(fnames[mu]) # id:px:py:pz:x:y:z:w
      ut.bookHist(h,'xy_'+str(mu),  'x/y;x [cm];y [cm];N/sec/cm^{2}  '  ,    200,-100.,100.,200,-100.,100.)
      ut.bookHist(h,'xyMS_'+str(mu),  'x/y;x [cm];y [cm];N/sec/cm^{2} ',200,-100.,100.,200,-100.,100.)
      ut.bookHist(h,'xyW_'+str(mu),  'x/y;x [cm];y [cm];N/sec/cm^{2}  '  ,     200,-100.,100.,200,-100.,100.)
      ut.bookHist(h,'xysco_'+str(mu),  'x/y;x [cm];y [cm];N/sec/cm^{2}  '  ,  200,-100.,100.,200,-100.,100.)
      ut.bookHist(h,'xyMSW_'+str(mu),  'x/y;x [cm];y [cm];N/sec/cm^{2}  ',200,-100.,100.,200,-100.,100.)
      ut.bookHist(h,'Esco_'+str(mu),  'E in SND',1000,0.,5000.)
      ut.bookHist(h,'Esnd_'+str(mu),  'E in SND',1000,0.,5000.)
      ut.bookHist(h,'EsndMS_'+str(mu),  'E in SND',1000,0.,5000.)
      ut.bookHist(h,'Efaser_'+str(mu),  'E in faser',1000,0.,5000.)
      ut.bookHist(h,'EfaserMS_'+str(mu),  'E in faser',1000,0.,5000.)
      ut.bookHist(h,'tanThetaXY_'+str(mu),  'tan theta X/Y',200,-0.01,0.01,200,-0.01,0.01)
      ut.bookHist(h,'tanThetaXY30_'+str(mu),  'tan theta X/Y',200,-0.01,0.01,200,-0.01,0.01)
      ut.bookHist(h,'tanThetaXYSND_'+str(mu),  'tan theta X/Y',200,-0.01,0.01,200,-0.01,0.01)
      ut.bookHist(h,'tanThetaXYMS_'+str(mu),  'tan theta X/Y',200,-0.01,0.01,200,-0.01,0.01)
      ut.bookHist(h,'tanThetaXYMSfaser_'+str(mu),  'tan theta X/Y',200,-0.01,0.01,200,-0.01,0.01)
      ut.bookHist(h,'theta',  'mult scattering angle',200,-1.,1.)
      for sTree in fin.nt:
         px,py,pz = sTree.px,sTree.py,sTree.pz
         m2cm = 1.
         if version == 0:  m2cm = 100
         x,y,z    = sTree.x,sTree.y,sTree.z*m2cm # how could have this happened? used u.m for conversion!
         # if abs(x)<50. and abs(y)<50. : continue
         pid,w    = int(sTree.id),sTree.w
         p = ROOT.TMath.Sqrt(px*px+py*py+pz*pz)
         wLHC = norm*w
         rc = h["Esco_"+str(mu)].Fill(p,wLHC)
         rc = h['xysco_'+str(pid)].Fill(x,y,wLHC)
# apply some multiple scattering and energy loss, and adjust weight for efficiency replacing MS angle
         if Rmult==-1:
            if p < effPMax: wLHC=wLHC*effFun.Eval(p)
            Psnd = p - eLoss.Eval(p)
         else:
            Psnd = p - 30.
            if version == 1: Psnd = p - 26.
         lam = ( SND_Z-z)/pz
         mxex = x+lam*px
         myex = y+lam*py
         # print('debug',SND_Z,z,lam,x,mxex,y,myex,px,py)
         rc = h['xy_'+str(pid)].Fill(mxex,myex)
         rc = h['xyW_'+str(pid)].Fill(mxex,myex,wLHC)
         tanThetaX = ROOT.TMath.Tan(ROOT.TMath.ATan2(px,pz))
         tanThetaY = ROOT.TMath.Tan(ROOT.TMath.ATan2(py,pz))
         rc = h['tanThetaXY_'+str(mu)].Fill(tanThetaX,tanThetaY,wLHC)
         if Psnd>0:
            rc = h['tanThetaXY30_'+str(mu)].Fill(tanThetaX,tanThetaY,wLHC)
         if -8 > mxex and mxex >-49 and 15 < myex and myex < 57:
            rc = h["Esnd_"+str(mu)].Fill(Psnd,wLHC)
         if -12 < mxex and mxex < 12 and -12 < myex and myex < 12:
             rc = h["Efaser_"+str(mu)].Fill(Psnd,wLHC)
#    13.6/P sqrt(L/x0)(1+0.038 log(L/x0)), L/X0 = 700
         for r in range(Rmult):
           mxexMS = mxex
           myexMS = myex
           if Rmult>1:
              thetaX = rnr.Gaus(0.,h['MS'].Eval(p))
              thetaY = rnr.Gaus(0.,h['MS'].Eval(p))
              rc = h['theta'].Fill(thetaX)
              rc = h['theta'].Fill(thetaY)
              mxexMS = mxex + (SND_Z-z)*ROOT.TMath.Tan(thetaX)
              myexMS = myex + (SND_Z-z)*ROOT.TMath.Tan(thetaY)
              tanThetaX = ROOT.TMath.Tan(ROOT.TMath.ATan2(px,pz)+thetaX)
              tanThetaY = ROOT.TMath.Tan(ROOT.TMath.ATan2(py,pz)+thetaY)
           rc = h['tanThetaXYSND_'+str(mu)].Fill(tanThetaX,tanThetaY,wLHC/Rmult)
           if Psnd >0:
                 rc = h['xyMS_'+str(pid)].Fill(mxexMS,myexMS)
                 rc = h['xyMSW_'+str(pid)].Fill(mxexMS,myexMS,wLHC/Rmult)
           if -8 > mxexMS and mxexMS >-49 and 15 < myexMS and myexMS < 57:
             rc = h["EsndMS_"+str(mu)].Fill(Psnd,wLHC/Rmult)
             if Psnd >0:   rc = h['tanThetaXYMS_'+str(mu)].Fill(tanThetaX,tanThetaY,wLHC/Rmult)
           if -12 < mxexMS and mxexMS < 12 and -12 < myexMS and myexMS < 12:
             rc = h["EfaserMS_"+str(mu)].Fill(Psnd,wLHC/Rmult)
             if Psnd >0:  rc = h['tanThetaXYMSfaser_'+str(mu)].Fill(tanThetaX,tanThetaY,wLHC/Rmult)
      for hname in ["Esco_"+str(mu),"Esnd_"+str(mu),"EsndMS_"+str(mu),"Efaser_"+str(mu),"EfaserMS_"+str(mu)]:
         if 'I-'+hname in h: A=h.pop('I-'+hname)
         ROOT.gROOT.cd()
         ut.makeIntegralDistrib(h,hname)
         h['I-'+hname].GetXaxis().SetRangeUser(0.,10000.)
         h['I-'+hname].SetMinimum(1E-6)
         pname = PDG.GetParticle(mu).GetName()
         if hname.find("Esco")==0:
            print("at scoring plane    %s, %s:  %5.2F N/sec "%(pname,hname,h['I-'+hname].GetBinContent(1)))
         else:
            print("at SND dE=-30GeV    %s, %s:  %5.2F N/sec "%(pname,hname,h['I-'+hname].GetBinContent(1)))
    h['snd_1']  =  ROOT.TLine(-49,15,-8,15)
    h['snd_2']  =  ROOT.TLine(-49,57,-8,57)
    h['snd_3']  =  ROOT.TLine(-49,57,-49,15)
    h['snd_4']  =  ROOT.TLine(-8,57,-8,15)
    h['fas_1']  =  ROOT.TLine(-12,12,12,12)
    h['fas_2']  =  ROOT.TLine(-12,-12,12,-12)
    h['fas_3']  =  ROOT.TLine(-12,-12,-12,12)
    h['fas_4']  =  ROOT.TLine(12,-12,12,12)
    for n in range(1,5):
      h['snd_'+str(n)] .SetLineColor(ROOT.kBlack)
      h['snd_'+str(n)] .SetLineWidth(5)
      h['snd_'+str(n)] .SetLineStyle(1)
      h['fas_'+str(n)] .SetLineColor(ROOT.kCyan)
      h['fas_'+str(n)] .SetLineWidth(5)
      h['fas_'+str(n)] .SetLineStyle(2)
    for Y in ['xyMSW_','xysco_']:
      for mu in fnames:
             h[Y+str(mu)].SetStats(0)
             if version==0:
                h[Y+str(mu)].GetXaxis().SetRangeUser(-60.,60.)
                h[Y+str(mu)].GetYaxis().SetRangeUser(-60.,60.)
             else:
                # h[Y+str(mu)].SetMaximum(10)
                h[Y+str(mu)].GetXaxis().SetRangeUser(-80.,80.)
                h[Y+str(mu)].GetYaxis().SetRangeUser(-80.,80.)
             if mu<0: h[Y+str(mu)].SetTitle("#mu^{+}")
             if mu>0: h[Y+str(mu)].SetTitle("#mu^{-}")
      tc = h['muDIS_SNDXY_1'].cd()
      tc.SetRightMargin(0.2)
      h[Y+'13'].GetZaxis().SetTitleOffset(1.3)
      h[Y+'13'].Draw('colz')
      tc.Update()
      pal = h[Y+'13'].GetListOfFunctions()[0]
      pal.SetX1NDC(0.81)
      pal.SetX2NDC(0.85)
      if Y=='xyMSW_':
        for n in range(1,5):
           h['snd_'+str(n)].Draw('same')
           if withFaser:    h['fas_'+str(n)].Draw('same')
      tc = h['muDIS_SNDXY_2'].cd()
      tc.SetRightMargin(0.2)
      h[Y+'-13'].GetZaxis().SetTitleOffset(1.5)
      h[Y+'-13'].Draw('colz')
      tc.Update()
      pal = h[Y+'-13'].GetListOfFunctions()[0]
      pal.SetX1NDC(0.8)
      pal.SetX2NDC(0.85)
      if Y=='xyMSW_':
        for n in range(1,5):
          h['snd_'+str(n)].Draw('same')
          if withFaser:    h['fas_'+str(n)].Draw('same')
      if Y=='xyMSW_':
        myPrint(h['muDIS_SNDXY_1'],'muDIS_SNDXY_muM')
        myPrint(h['muDIS_SNDXY_2'],'muDIS_SNDXY_muP')
      else:
        myPrint(h['muDIS_SNDXY_1'],'muDIS_SCOXY_muM')
        myPrint(h['muDIS_SNDXY_2'],'muDIS_SCOXY_muP')

    R = h['I-EsndMS_13'].GetBinContent(1)+h['I-EsndMS_-13'].GetBinContent(1)
    print('mu+ and mu- at SND: %5.2F N/sec      %5.2F  Hz/cm2'%(R,R/(41.*42.)))
    R = h['I-EfaserMS_13'].GetBinContent(1)+h['I-EfaserMS_-13'].GetBinContent(1)
    print('mu+ and mu- at Faser: %5.2F N/sec      %5.2F  Hz/cm2'%(R,R/(24.*24.)))
    rc = h['muDIS_SNDE'].cd(1)
    rc.SetLogy()
    h['I-Esnd_-13'].SetLineColor(ROOT.kRed)
    h['I-Esnd_13'].SetLineColor(ROOT.kBlue)
    h['I-Esnd_13'].SetFillStyle(2)
    h['I-Esnd_13'].SetStats(0)
    h['I-Esnd_-13'].SetStats(0)
    h['I-Esnd_-13'].SetFillStyle(2)
    h['I-Esnd_13'].SetMinimum(1E-3)
    h['I-Esnd_13'].SetTitle(';>P  [GeV/c]; Hz')
    h['I-Esnd_13'].Draw('BAR')
    h['I-Esnd_-13'].Draw('sameBAR')
    h['t-13' ]=ROOT.TLatex(500,0.1,PDG.GetParticle(-13).GetName())
    h['t13' ]=ROOT.TLatex(2500,0.3,PDG.GetParticle(13).GetName())
    h['t13' ].SetTextColor(ROOT.kWhite)
    h['t13' ].Draw('same')
    h['t-13'].Draw('same')
    h['muDIS_SNDE'].Print('muDIS_ESND.png')

from decorators import *
def boundaries():
   h['snd_1']  =  ROOT.TLine(-49,15,-8,15)
   h['snd_2']  =  ROOT.TLine(-49,57,-8,57)
   h['snd_3']  =  ROOT.TLine(-49,57,-49,15)
   h['snd_4']  =  ROOT.TLine(-8,57,-8,15)
   h['fas_1']  =  ROOT.TLine(-12,12,12,12)
   h['fas_2']  =  ROOT.TLine(-12,-12,12,-12)
   h['fas_3']  =  ROOT.TLine(-12,-12,-12,12)
   h['fas_4']  =  ROOT.TLine(12,-12,12,12)
   for n in range(1,5):
      h['snd_'+str(n)] .SetLineColor(ROOT.kBlack)
      h['snd_'+str(n)] .SetLineWidth(5)
      h['snd_'+str(n)] .SetLineStyle(1)
      h['fas_'+str(n)] .SetLineColor(ROOT.kCyan)
      h['fas_'+str(n)] .SetLineWidth(5)
      h['fas_'+str(n)] .SetLineStyle(2)

def flukaMuons(version=1,Plimit=False,withFaser=True):
   norm = normalization[version]
   path="/mnt/hgfs/microDisk/CERNBOX/SND@LHC/FLUKA/"
   pMin = 0
   if Plimit:   pMin = 30.
   if version==0: 
        fnames = {13:path+"muons_up/version0/unit30_Nm.root",-13:path+"muons_up/version0/unit30_Pm.root"}
   if version==1: 
        if Plimit:   pMin = 27.
        fnames = {13:path+"muons_up/version1/unit30_Nm.root",-13:path+"muons_up/version1/unit30_Pm.root"}
   if version==3: 
        if Plimit:   pMin = 27.
        fnames = {13:path+"muons_down/muons_VCdown_IR1-LHC.root"}
   boundaries()
   ut.bookCanvas(h,'TXY','muons',1800,650,2,1)
   ut.bookCanvas(h,'TE','muons',1800,650,2,1)
   ut.bookCanvas(h,'TW','muons',1800,650,2,1)

   for mu in [13,-13]:
      ut.bookHist(h,'xySCO_'+str(mu),  'x/y;x [cm];y [cm];N/sec/cm^{2}  '  ,    200,-100.,100.,200,-100.,100.)
      ut.bookHist(h,'xySND_'+str(mu),  'x/y;x [cm];y [cm];N/sec/cm^{2}  '  ,    200,-100.,100.,200,-100.,100.)
      ut.bookHist(h,'xySNDX_'+str(mu),  'x/y;x [cm];y [cm];N/sec/cm^{2}  '  ,    200,-100.,100.,200,-100.,100.)
      ut.bookHist(h,'E_'+str(mu),  ';E [GeV]; N / 5 GeV',1000,0.,5000.)
      ut.bookHist(h,'W_'+str(mu),  'w',100,0.,0.15)
   for mu in fnames:
      fin = ROOT.TFile(fnames[mu])
      for sTree in fin.nt:
         m2cm = 1.
         if version == 0:  m2cm = 100.
         P = ROOT.TVector3(sTree.px,sTree.py,sTree.pz)
         if P.Mag()<pMin: continue
         X = ROOT.TVector3(sTree.x,sTree.y,sTree.z*m2cm) # how could have this happened? used u.m for conversion!
         pid,w  = int(sTree.id),sTree.w
         wLHC = norm*w
         rc = h['xySCO_'+str(pid)].Fill(X[0],X[1],wLHC)
         rc = h["E_"+str(pid)].Fill(P.Mag(),wLHC)
         rc = h['W_'+str(pid)].Fill(w)
         lam = ( SND_Z-X[2])/P[2]
         Xex = X+lam*P
         rc = h['xySND_'+str(pid)].Fill(Xex[0],Xex[1],wLHC)
         if abs(sTree.x)>50. or abs(sTree.y)>50.:         rc = h['xySNDX_'+str(pid)].Fill(Xex[0],Xex[1],wLHC)
#
   for Y in ['xySCO_','xySND_','xySNDX_']:
      if version==0 and Y=='xySNDX_': continue
      k = 0
      for mu in [13,-13]:
             k+=1
             h[Y+str(mu)].SetStats(0)
             h[Y+str(mu)].SetMaximum(5.)
             if mu<0: h[Y+str(mu)].SetTitle("#mu^{+}")
             if mu>0: h[Y+str(mu)].SetTitle("#mu^{-}")
             tc = h['TXY'].cd(k)
             tc.SetRightMargin(0.2)
             h[Y+str(mu)].GetZaxis().SetTitleOffset(1.3)
             h[Y+str(mu)].Draw('colz')
             tc.Update()
             pal = h[Y+str(mu)].GetListOfFunctions()[0]
             pal.SetX1NDC(0.81)
             pal.SetX2NDC(0.85)
             if not Y.find('xySND')<0:
                for n in range(1,5):
                    h['snd_'+str(n)].Draw('same')
                    if withFaser:    h['fas_'+str(n)].Draw('same')
      myPrint(h['TXY'],'FlukaMuons'+Y+'v'+str(version))
   k = 0
   for mu in [13,-13]:
        k+=1
        tc = h['TE'].cd(k)
        tc.SetLogy(1)
        if mu<0: h["E_"+str(mu)].SetTitle("#mu^{+}")
        if mu>0: h["E_"+str(mu)].SetTitle("#mu^{-}")
        h["E_"+str(mu)].SetStats(0)
        h["E_"+str(mu)].Draw()
   myPrint(h['TE'],'FlukaMuonsE_v'+str(version))
   k = 0
   for mu in [13,-13]:
        k+=1
        tc = h['TW'].cd(k)
        tc.SetLogy(1)
        if mu<0: h["W_"+str(mu)].SetTitle("#mu^{+}")
        if mu>0: h["W_"+str(mu)].SetTitle("#mu^{-}")
        h["W_"+str(mu)].SetStats(0)
        h["W_"+str(mu)].Draw()
   myPrint(h['TW'],'FlukaMuonsW_v'+str(version))

   if not 'stats' in h: h['stats'] = {}
   h['stats'][version] = {}
   stats = h['stats'][version]
   for mu in fnames:
     stats[mu] = {}
     for z in ['snd','fas']:
       stats[mu][z] = []
       for Y in ['xySND_','xySNDX_']:
          hist = h[Y+str(mu)]
          xMin  = hist.GetXaxis().FindBin(h[z+'_1'].GetX1())
          xMax = hist.GetXaxis().FindBin(h[z+'_1'].GetX2())
          yMin  = hist.GetYaxis().FindBin(h[z+'_1'].GetY1())
          yMax = hist.GetYaxis().FindBin(h[z+'_2'].GetY1())
          if yMin>yMax:
             tmp = yMin
             yMin = yMax
             yMax = tmp
          sqcm = (xMax-xMin)*(yMax-yMin)
          stats[mu][z].append(hist.Integral(xMin,xMax,yMin,yMax))
       stats[mu][z].append(sqcm)
     stats[mu]['total'] = h['xySND_'+str(mu)].GetSumOfWeights()
     stats[mu]['1x1']   = h['xySND_'+str(mu)].GetSumOfWeights() - h['xySNDX_'+str(mu)].GetSumOfWeights()
   for mu in fnames:
        print("-------- "+PDG.GetParticle(mu).GetName()+"   ----------")
        if version==1 and 0 in h['stats']:
           print('increae of rates, total: %5.2F    absolute(1x1) %5.2F   new/old=%5.2F'%(stats[mu]['1x1']/stats[mu]['total'],stats[mu]['1x1'],stats[mu]['1x1']/h['stats'][0][mu]['1x1']))
           newOvOld = (stats[mu]['snd'][0] -stats[mu]['snd'][1])/(h['stats'][0][mu]['snd'][0] -h['stats'][0][mu]['snd'][1])
           newOvOldTOT = stats[mu]['snd'][0]/h['stats'][0][mu]['snd'][0]
           print('increae of rates, SND: %5.2F     absolute(1x1) %5.2F   new/old=%5.2F   new/old(tot)=%5.2F'%(stats[mu]['snd'][1]/stats[mu]['snd'][0],stats[mu]['snd'][0] -stats[mu]['snd'][1],newOvOld,newOvOldTOT    ))
           newOvOld = (stats[mu]['fas'][0] -stats[mu]['fas'][1])/(h['stats'][0][mu]['fas'][0] -h['stats'][0][mu]['fas'][1])
           newOvOldTOT = stats[mu]['fas'][0]/h['stats'][0][mu]['fas'][0]
           print('increae of rates, FAS: %5.2F      absolute(1x1) %5.2F   new/old=%5.2F   new/old(tot)=%5.2F'%(stats[mu]['fas'][1]/stats[mu]['fas'][0] ,stats[mu]['fas'][0] -stats[mu]['fas'][1],newOvOld,newOvOldTOT   ))
        else:
           print('increae of rates, total: %5.2F    absolute(1x1) %5.2F'%(h['xySNDX_'+str(mu)].GetSumOfWeights()/h['xySND_'+str(mu)].GetSumOfWeights(),
                                                                                                                                         h['xySND_'+str(mu)].GetSumOfWeights()-h['xySNDX_'+str(mu)].GetSumOfWeights()) )
           print('increae of rates, SND: %5.2F     absolute(1x1) %5.2F'%(stats[mu]['snd'][1]/stats[mu]['snd'][0],stats[mu]['snd'][0] -stats[mu]['snd'][1]  ))
           print('increae of rates, FAS: %5.2F      absolute(1x1) %5.2F'%(stats[mu]['fas'][1]/stats[mu]['fas'][0] ,stats[mu]['fas'][0] -stats[mu]['fas'][1] ))
# sum of muons
   if version==1 and 0 in h['stats']:
     for z in ['snd','fas']:
        sumMu = h['stats'][1][13][z][0]+h['stats'][1][-13][z][0]
        increase = sumMu/(h['stats'][0][13][z][0]+h['stats'][0][-13][z][0])
        print('%s: %5.2F /cm2/s    increase: %5.2F '%(z,sumMu/h['stats'][1][13][z][2],increase))


def muInterGeant4(version=2,njobs=100):
   redfac3d = 10
   norm = normalization[version]
   uninterestingParticles = [11,-11,-12,12,14,-14,13,-13]
   ut.bookHist(h,"xyz_muInter_",   'x/y /z',200,-100.,100.,200,-100.,100.,int(600/redfac3d) ,-500.,100.)
   ut.bookHist(h,"xyz_origin_",       'x/y /z',200,-100.,100.,200,-100.,100.,int(600/redfac3d) ,-500.,100.)

   if version == 2:  g = ROOT.TFile('muGeant4_0/geofile_full.conical.Ntuple-TGeant4.root')
   else:                       g = ROOT.TFile('muMinusGeant4_0/geofile_full.conical.Ntuple-TGeant4.root')
   geoManager = g.FAIRGeom
   for subjob in range(njobs):
    if version == 2: muons =  ['muGeant4_'+str(subjob)+'/ship.conical.Ntuple-TGeant4.root']
    else:                      muons =  ['muMinusGeant4_'+str(subjob)+'/ship.conical.Ntuple-TGeant4.root','muPlusGeant4_'+str(subjob)+'/ship.conical.Ntuple-TGeant4.root']
    pids = {}
    for fname  in muons:
        f = ROOT.TFile(fname)
        ROOT.gROOT.cd()
        nEv = -1
        for sTree in f.cbmsim:
             nEv+=1
             muon = sTree.MCTrack[0]
             w          = norm*muon.GetWeight()
             muID  = muon.GetPdgCode()
             for p in sTree.vetoPoint:
                  pid = p.PdgCode()
                  if not pid in pids: pids[pid]=0
                  pids[pid]+=1
                  if pid in uninterestingParticles: continue
                  if not "xyz_origin_"+str(pid) in h: 
                        for x in ["xyz_muInter_","xyz_origin_"]:
                             h[x+str(pid)]=h[x].Clone(x+str(pid))
                  track = p.GetTrackID()
                  exitPoint = p.LastPoint()
                  rc = h["xyz_origin_"+str(pid)].Fill(exitPoint[0],exitPoint[1],exitPoint[2],w)
                  while track > 0:
                             mother = sTree.MCTrack[track].GetMotherId()
                             if mother == 0: break
                             track = mother
                  if track >0:
                          m = sTree.MCTrack[track]
                          rc =  h["xyz_muInter_"+str(pid)].Fill(m.GetStartX(),m.GetStartY(),m.GetStartZ(),w)
                  

def muondEdX(version=2,njobs=100,path='',withFaser=False, plotOnly=True):
# version 1   /home/truf/ubuntu-1710/ship-ubuntu-1710-48/SND/MuonDis/

 #  python -i $SNDBUILD/sndsw/macro/run_simScript.py --shiplhc --PG --Estart 10 --Eend    5000 --EVz -7100 --EVx -30 --EVy 40 --pID 13 -n 100000 --FastMuon
 #  python -i $SNDBUILD/sndsw/macro/run_simScript.py --shiplhc --PG --Estart 10 --Eend    5000 --EVz -7100 --EVx -30 --EVy 40 --pID -13 -n 100000 --FastMuon
 #  python  $SNDSW_ROOT/macro/run_simScript.py --shiplhc -f unit30_Nm.root --Ntuple --FastMuon --output muMinusGeant4 -n 999999999
 #  python  $SNDSW_ROOT/macro/run_simScript.py --shiplhc -f unit30_Pm.root   --Ntuple --FastMuon --output muPlusGeant4 -n 999999999
 neuPartList = [22,130,310,2112,-2112,3122,-3122,3322,-3322]
 if not plotOnly:
   norm = normalization[version]

   ut.bookHist(h,'eloss','energyLoss',                500,0., 5000.,500,0.,500.)
   ut.bookHist(h,'dx','multiple scattering x',  500,0., 5000.,1000,-0.02,0.02)
   ut.bookHist(h,'dy','multiple scattering y',   500,0., 5000.,1000,-0.02,0.02)
   ut.bookHist(h,'oE','original energy',              500,0.,5000.)
   ut.bookHist(h,'oL','flight path',                         100,0.,10000.)
   ut.bookHist(h,'3d','exit points',200,-100.,100.,200,-100.,100.,600,-500.,100.)
   ut.bookHist(h,'z','last z ',1000,-1000.,1000.)
   ut.bookHist(h,'SNDmuP', 'SND entry points',200,-100.,100.,200,-100.,100.)
   ut.bookHist(h,'SNDmuM','SND entry points',200,-100.,100.,200,-100.,100.)
   ut.bookHist(h,'SNDMuFiltermuP', 'SND entry points',200,-100.,100.,200,-100.,100.)
   ut.bookHist(h,'SNDMuFiltermuM','SND entry points',200,-100.,100.,200,-100.,100.)
   ut.bookHist(h,'xy_13',   'x/y;x [cm];y [cm];N/sec/cm^{2}  '  ,    200,-100.,100.,200,-100.,100.)
   ut.bookHist(h,'xy_-13',  'x/y;x [cm];y [cm];N/sec/cm^{2}  '  ,    200,-100.,100.,200,-100.,100.)

   for p in neuPartList: ut.bookHist(h,"E_"+str(p),'Energy', 500,0.,5000.)

   if version == 3:  g = ROOT.TFile(path+'muGeant4_VCdown_0/geofile_full.conical.Ntuple-TGeant4.root')
   elif version == 2:  g = ROOT.TFile(path+'muGeant4_0/geofile_full.conical.Ntuple-TGeant4.root')
   else:                           g = ROOT.TFile(path+'muMinusGeant4_0/geofile_full.conical.Ntuple-TGeant4.root')
   geoManager = g.FAIRGeom
   for subjob in range(njobs):
    if version == 3: muons =  [path+'muGeant4_VCdown_'+str(subjob)+'/ship.conical.Ntuple-TGeant4.root']
    elif version == 2: muons =  [path+'muGeant4_'+str(subjob)+'/ship.conical.Ntuple-TGeant4.root']
    else:                      muons =  [path+'muMinusGeant4_'+str(subjob)+'/ship.conical.Ntuple-TGeant4.root',path+'muPlusGeant4_'+str(subjob)+'/ship.conical.Ntuple-TGeant4.root']
    for fname  in muons:
        h[fname] = ROOT.TFile(fname)
        ROOT.gROOT.cd()
        nEv = -1
        for sTree in h[fname].cbmsim:
             nEv+=1
             muon = sTree.MCTrack[0]
             w          = norm*muon.GetWeight()
             muID  = muon.GetPdgCode()
             if muon.GetPdgCode()==0: 
                  print('something strange here  PdgCode=0',fname)
             rc = h['oE'].Fill(muon.GetEnergy(),w)
             for x in sTree.MCTrack:
                  pid = x.GetPdgCode()
                  if pid in neuPartList: rc = h["E_"+str(pid)].Fill(x.GetEnergy())
             trajectories  = {}
             for p in sTree.vetoPoint:
                 track = p.GetTrackID()
                 if track < 0: continue   # trajectory not stored
                 if track != 0: continue   # only take original muon for the moment

                 if not track in trajectories: trajectories[track]={}
                 traj = trajectories[track]
                 end   = p.LastPoint()
                 middle = ROOT.TVector3(p.GetX(),p.GetY(),p.GetZ())
                 first  = 2*middle - end
                 Pin    = ROOT.Math.PxPyPzMVector(p.GetPx(),p.GetPy(),p.GetPz(),muonMass)
                 Pout = ROOT.Math.PxPyPzMVector(p.LastMom()[0],p.LastMom()[1],p.LastMom()[2],muonMass)
                 if not Pout.Z()>0:
                      enterCave = False
                      if sTree.ScifiPoint.GetEntries()>0 or sTree.MuFilterPoint.GetEntries()>0 and end.z() < -24.5:  # otherwise muon stops in or after SND
                            print('something strange here, pout.z<0',nEv,fname,sTree.ScifiPoint.GetEntries(),sTree.MuFilterPoint.GetEntries())
                            p.Print()
                 else:
                      test    = end + 1./Pout.Z()*p.LastMom()
                      node = geoManager.FindNode(test[0],test[1],test[2])
                      enterCave =   node.GetName() .find('Vrock') <0     # particle leaving concrete and entering rock
                 traj[first[2]]=[first[0],first[1],Pin,False]
                 traj[end[2]]=[end[0],end[1],Pout,enterCave]
             for track in trajectories:
                 traj    = trajectories[track]
                 zPos = list(traj.keys())
                 zPos.sort()
                 T = [ROOT.TGraph(),ROOT.TGraph()]
                 k = 0
                 for z in zPos:
                    for j in range(2):
                       T[j].SetPoint(k,z,traj[z][j])
                    k+=1
                 xex,yex = T[0].Eval(0),T[1].Eval(0)
                 if xex==0 and yex==0:
                      T[0].Print()
                      T[1].Print()
                      print(nEv,fname,track,traj,zPos)
                 rc = h['xy_'+str(muID)].Fill(xex,yex,w)
                 for z in zPos:
                    if not traj[z][3]: continue
                    oEnergy = muon.GetEnergy()
                    P = traj[z][2]
                    eloss = muon.GetEnergy() - P.E()
                    rc = h['eloss'].Fill(oEnergy,eloss,w)
                    start = ROOT.TVector3(sTree.MCTrack[0].GetStartX(),sTree.MCTrack[0].GetStartY(),sTree.MCTrack[0].GetStartZ())
                    L = end-start
                    rc = h['oL'].Fill(L.Mag(),w)
                    if P.Z()>0:
                      dAlpha = muon.GetPx()/muon.GetPz() - P.X()/P.Z()
                      rc = h['dx'].Fill(oEnergy,dAlpha)
                      dAlpha = muon.GetPy()/muon.GetPz()- P.Y()/P.Z()
                      rc = h['dy'].Fill(oEnergy,dAlpha)
                      rc = h['3d'].Fill(traj[z][0],traj[z][1],z,w)
                    break
             hitScifi = False
             for p in sTree.ScifiPoint:
# rate of muons entering SND, count only one hit
                 omu = p.GetTrackID()
                 if omu != 0 or abs(p.PdgCode()) != 13:  continue
                 hname = 'SNDmuM'
                 if p.PdgCode()<0: hname = 'SNDmuP'
                 rc = h[hname].Fill(p.GetX(),p.GetY(),w)
                 hitScifi=True
                 break
             hitMuFilter = False
             for p in sTree.MuFilterPoint:
# rate of muons entering SND, count only one hit
                 omu = p.GetTrackID()
                 if omu != 0 or abs(p.PdgCode()) != 13:  continue
                 hname = 'SNDMuFiltermuM'
                 if p.PdgCode()<0: hname = 'SNDMuFiltermuP'
                 rc = h[hname].Fill(p.GetX(),p.GetY(),w)
                 hitMuFilter=True
                 break
# go for first point, exit from concrete
             noHit = True
             for p in sTree.ScifiPoint:
                 if abs(p.PdgCode()) != 13:   continue
                 if p.GetDetectorID()==47:
                          noHit = False
                          break
             if noHit: continue
#
 else:
   ut.readHists(h,'muondEdX_'+str(version)+'.root')

   for det in ['SND','SNDMuFilter']:
      S = h[det+'muP'].Clone('S')
      S.Add(h[det+'muM'])
      hname = det+'muP'
      nx,ny = h[hname].GetXaxis().GetNbins(),h[hname].GetYaxis().GetNbins()
      projx = S.ProjectionX()
      projy = S.ProjectionY()
      for ix in range(1,nx+1):
       if projx.GetBinContent(ix)>0:
            xmin = projx.GetBinCenter(ix)-projx.GetBinWidth(ix)/2.
            break
      for ix in range(nx,0,-1):
       if projx.GetBinContent(ix)>0:
            xmax = projx.GetBinCenter(ix)+projx.GetBinWidth(ix)/2.
            break
      for iy in range(1,ny+1):
       if projy.GetBinContent(iy)>0:
            ymin = projy.GetBinCenter(iy)-projy.GetBinWidth(iy)/2.
            break
      for iy in range(ny,0,-1):
       if projy.GetBinContent(iy)>0:
            ymax = projy.GetBinCenter(iy)+projy.GetBinWidth(iy)/2.
            break
      sqcm = (xmax-xmin)*(ymax-ymin)
      muP = h[det+'muP'].GetSumOfWeights()
      muM = h[det+'muM'].GetSumOfWeights()
      print("%s       square:  %5.2F,%5.2F,%5.2F,%5.2F"%(det,xmin,xmax,ymin,ymax))
      print("         mu+ rate = %5.2F Hz    %5.2F Hz/cm2"%(muP,muP/sqcm))
      print("         mu-  rate = %5.2F Hz    %5.2F Hz/cm2"%(muM,muM/sqcm))
      print("         sum  rate = %5.2F Hz    %5.2F Hz/cm2"%(muM+muP,(muM+muP)/sqcm))

   ut.bookCanvas(h,'TCeloss','eloss',900,600,1,1)
   tc = h['TCeloss'].cd()
   h['eloss_mean'] = h['eloss'].ProfileX('mean',1,-1,'g')
   h['eloss_mean'].GetXaxis().SetRangeUser(10,5000)
   fname = 'pol3'
   h['eloss_mean'].Fit(fname,'S','',20.,5000.)
   tc.SetLogx(1)
   h['eloss_mean'].SetTitle(';  incoming momentun  [GeV/c] ; mean energy loss [GeV]')
   h['eloss_mean'].Draw('hist')
   fun = h['eloss_mean'].GetFunction(fname)
   fun.Draw('same')
   tc.Update()
   stats = h['eloss_mean'].FindObject('stats')
   stats.SetOptFit(111)
   stats.SetOptStat(0)
   stats.SetX1NDC(0.2)
   stats.SetY1NDC(0.5)
   stats.SetX2NDC(0.6)
   stats.SetY2NDC(0.75)
   tc.Update()
   myPrint(tc,'meanEloss_'+str(version))
#
   ut.bookCanvas(h,'eff','efficiency',900,600,1,1)
   tc = h['eff'].cd()
   eff = h['eloss'].ProjectionX()
   eff.Divide(h['oE'])
   eff.SetStats(0)
   eff.SetTitle("; incoming momentun  [GeV/c] ; efficiency")
   eff.GetXaxis().SetRangeUser(0.,500.)
   eff.Draw()
   myPrint(tc,'efficiency_'+str(version))
#
   ut.bookCanvas(h,'TCMS','multiple scattering',900,600,1,1)
   tc = h['TCMS'].cd()
   msDx = h['dx'].ProfileX('msDx',1,-1,'s')
   N = msDx.GetNbinsX()
   Xmin =  msDx.GetBinCenter(1)-msDx.GetBinWidth(1)
   Xmax = msDx.GetBinCenter(N)+msDx.GetBinWidth(N)
   ut.bookHist(h,'msDxE','msDxE',N,Xmin,Xmax)
   msDxE = h['msDxE']
   # angular distributions are distorted due to different paths and different integrated material
   for j in range(1,msDx.GetNbinsX()+1):
        tmp = h['dy'].ProjectionY('tmp',j,j)
        rms  = 0
        Erms = 0
        if tmp.GetEntries()>20:
           rc = tmp.Fit('gaus','SQL')
           fitResult = rc.Get()
           rms  =  fitResult.Parameter(2)
           Erms =  fitResult.ParError(2)
        msDxE.SetBinContent(j,rms)
        msDxE.SetBinError(j,Erms)
   msDxE.SetTitle("; incoming momentun  [GeV/c] ; MS angle  [rad]")
   msDxE.SetMaximum(0.02)
   msDxE.SetMinimum(0.0001)
   tc.SetLogy(1)
   msDxE.GetXaxis().SetRangeUser(0.,1000.)
   msDxE.Draw('hist')
   rc = msDxE.Fit(h['MS'],'S','',20.,400.)
   tc.Update()
   stats = msDxE.FindObject('stats')
   stats.SetOptFit(111)
   h['MS'].Draw('same')
   myPrint(h['TCMS'],'multipleScattering_'+str(version))
# rates
   boundaries()
   ut.bookCanvas(h,'TXY','muons',1800,650,2,1)
   k = 0
   for mu in [13,-13]:
             k+=1
             hist = h['xy_'+str(mu)]
             hist.SetStats(0)
             hist.SetMaximum(1.)
             if mu<0: hist.SetTitle("#mu^{+}")
             if mu>0: hist.SetTitle("#mu^{-}")
             tc = h['TXY'].cd(k)
             tc.SetRightMargin(0.2)
             hist.GetZaxis().SetTitleOffset(1.3)
             hist.Draw('colz')
             tc.Update()
             pal = hist.GetListOfFunctions()[0]
             pal.SetX1NDC(0.81)
             pal.SetX2NDC(0.85)
             for n in range(1,5):
                  h['snd_'+str(n)].Draw('same')
                  if withFaser:    h['fas_'+str(n)].Draw('same')
   myPrint(h['TXY'],'Geant4Muonsxy_v'+str(version))

   h['stats'] = {}
   stats = h['stats']
   for mu in [13,-13]:
     stats[mu] = {}
     for z in ['snd','fas']:
       stats[mu][z] = []
       hist = h['xy_'+str(mu)]
       xMin  = hist.GetXaxis().FindBin(h[z+'_1'].GetX1())
       xMax = hist.GetXaxis().FindBin(h[z+'_1'].GetX2())
       yMin  = hist.GetYaxis().FindBin(h[z+'_1'].GetY1())
       yMax = hist.GetYaxis().FindBin(h[z+'_2'].GetY1())
       if yMin>yMax:
             tmp = yMin
             yMin = yMax
             yMax = tmp
       sqcm = (xMax-xMin)*(yMax-yMin)
       stats[mu][z].append(hist.Integral(xMin,xMax,yMin,yMax))
       stats[mu][z].append(sqcm)
       print('%s, %s:  total = %5.2F  Hz     %5.2F  Hz/cm2 '%(mu,z,stats[mu][z][0],stats[mu][z][0]/stats[mu][z][1]))

   ut.writeHists(h,'muondEdX_'+str(version)+'.root')

# drawMuon3D(fname='muonDISfull.root',hname='3d')
def drawMuon3D(fname='muondEdX.root',hname='3d',gDir='muMinusGeant4_0'):
    # muonDISfull.root  h['xyz_Inter_'+str(pid)]
    ut.readHists(h,fname)
    ROOT.gStyle.SetPalette(ROOT.kRainBow)
    pal = ROOT.TColor.GetPalette()
    h['g'] = ROOT.TFile(gDir+'/geofile_full.conical.Ntuple-TGeant4.root')
    geoManager = h['g'] .FAIRGeom
    geoManager .SetNsegments(12)
    material = ROOT.TGeoMaterial("dummy")
    medium = ROOT.TGeoMedium('dummy',1,material)
    h['top'] = geoManager.GetTopVolume()
    top = h['top']
    nx,ny,nz = h[hname].GetXaxis().GetNbins(),h[hname].GetYaxis().GetNbins(),h[hname].GetZaxis().GetNbins()
    boxes = []
    hmax = pal.GetSize()/h[hname].GetMaximum()
    for ix in range(1,nx):
        for iy in range(1,ny):
           for iz in range(1,nz):
                C = h[hname].GetBinContent(ix,iy,iz)
                if not C>0: continue
                x,y,z  = h[hname].GetXaxis().GetBinCenter(ix),h[hname].GetYaxis().GetBinCenter(iy),h[hname].GetZaxis().GetBinCenter(iz)
                bn = str(ix)+':'+str(iy)+':'+str(iz)
                box = geoManager.MakeBox(bn,medium,0.5,0.5,0.5)
                kc = int(pal.GetAt(int(C*hmax)))
                # print("color",int(C*hmax),kc)
                box.SetLineColor(kc)
                boxes.append(box)
                top.AddNode(box, 1 , ROOT.TGeoTranslation(x,y, z))
    for n in top.GetNodes():
         if n.GetName().find('TI')>0: n.SetVisibility(0)
    top.Draw('ogl')

def plotMuDisCrossSection():
   fin = ROOT.TFile('muDIScrossSec.root')
   for pid in ['13','-13']: 
      h['g_'+pid] = fin.Get('g_'+pid).Clone('g_'+pid)

   SigmaAnalyticVsEnergy(A=1)
   SigmaAnalyticVsA(Ebeam=500)

   ut.bookCanvas(h,'sec','xsec',900,600,1,1)
   ut.bookHist(h,'muDISXsec',';E  [GeV];#sigma [mb]',100,0.,10000.)
   ut.bookHist(h,'muDISXsecA',';A ; #sigma [mb]',100,0.,100.)
   h['sec'].cd(1)
   h['muDISXsec'].SetMinimum(0.)
   h['muDISXsec'].SetMaximum(30.E-3)
   h['muDISXsecA'].SetMinimum(0.)
   h['muDISXsecA'].SetMaximum(3000.E-3)
   h['muDISXsec'].Draw()
   h['muDISXsec'].SetStats(0)
   h['g_13'].SetLineColor(ROOT.kGreen)
   h['g_-13'].SetLineColor(ROOT.kRed)
   h['g_13'].SetLineWidth(4)
   h['g_-13'].SetLineWidth(4)
   h['g_13'].Draw('same')
   h['g_-13'].Draw('same')
   h['AnalyticCross'].SetLineWidth(4)
   h['AnalyticCross'].SetLineColor(ROOT.kMagenta)
   h['AnalyticCross'].Draw('same')
   h['lxsec']=ROOT.TLegend(0.14,0.71,0.64,0.84)
   h['lxsec'].AddEntry(h['AnalyticCross'],'analytic cross section (Bezrukov and Bugaev, A=1)','PL')
   h['lxsec'].AddEntry(h['g_-13'],'Pythia6 for #mu^{+} p','PL')
   h['lxsec'].AddEntry(h['g_13'],'Pythia6 for #mu^{-} p','PL')
   h['lxsec'].Draw('same')

   myPrint(h['sec'],'muonXsec')

def muonDISfull(cycle = 0, sMin=0,sMax=200,rMin=1,rMax=11,path = '/eos/experiment/ship/user/truf/SND/muonDis/',debug=0,version=1,pythia6=True):
#
   muRange = [0,1000]
   geofile                                = 'geofile_full.conical.muonDIS-TGeant4.root'
   geofileExample              = 'run_1_1/'+geofile
   datafile                               = 'ship.conical.muonDIS-TGeant4.root'
   if not pythia6: 
                   muRange = ['muMinusGeant4','muPlusGeant4']
                   geofile                                ='geofile_full.conical.Ntuple-TGeant4.root'
                   geofileExample              = 'muMinusGeant4_0/'+geofile
                   datafile                               = '/ship.conical.Ntuple-TGeant4.root' 
                   if cycle ==100:  datafile  = '/ship.conical.Ntuple-TGeant4_boost100.0.root'

   redfac3d = 10
   norm = normalization[version]
   fin = ROOT.TFile('muDIScrossSec.root')
   ROOT.gROOT.cd()
   for pid in ['13','-13']: 
      h['g_'+pid] = fin.Get('g_'+pid).Clone('g_'+pid)
      ut.bookHist(h,'wDIS_'+pid,'muon DIS probability',100,0.,0.1)
      for z in ['0','inter']:
          ut.bookHist(h,'inMu_'+z+str(pid),'muon Energy vs #direct hits',200,0.,5000.,20,0.0,19.5)
          ut.bookHist(h,"xyz_mu_"+z+str(pid),   'x/y /z',200,-100.,100.,200,-100.,100.,int(600/redfac3d) ,-500.,100.)
   neuPartList = [22,130,310,2112,-2112,3122,-3122,3322,-3322]
   ut.bookHist(h,'fullStats','statistics',2000,-0.5,1999.5)
   ut.bookHist(h,'pidsDict','pids dictionary',100,-0.5,99.5)
   n = 1
   for x in pidsDict:
           h['pidsDict'].SetBinContent(n,x)
           n+=1

   for p in neuPartList:
          for o in ['','_secondary']:
              ut.bookHist(h,'inE_'+str(p)+o,'energy',500,0.,5000.,600,-500.,100.)                           # end vertex of primary neutral particle
              ut.bookHist(h,'inE_Concrete_'+str(p)+o,'energy',500,0.,5000.,600,-500.,100.)    # end vertex of primary neutral particle if in concrete
          ut.bookHist(h,"E_"+str(p),'Energy', 500,0.,5000.,200,-30.,170.)
          ut.bookHist(h,"E_veto_"+str(p),'Energy', 500,0.,5000.,200,-30.,170.)
          ut.bookHist(h,"E_vetoParticle_"+str(p),'Energy', 500,0.,50.,20,-0.5,19.5)
          ut.bookHist(h,"Eprim_"+str(p),'Energy', 500,0.,5000.,200,-30.,170.)
          ut.bookHist(h,"Eprim_veto_"+str(p),'Energy', 500,0.,5000.,200,-30.,170.)
          ut.bookHist(h,"startZ_"+str(p),'z',200,-100.,300.)
          ut.bookHist(h,"xyz_Inter_"+str(p),                     'x/y/z ',200,-100.,100.,200,-100.,100.,int(400/redfac3d),-100.,100.)
          ut.bookHist(h,"xyzE100_Inter_"+str(p),          'x/y/z ',200,-100.,100.,200,-100.,100.,int(400/redfac3d),-100.,100.)
          ut.bookHist(h,"xyzVeto_Inter_"+str(p),           'x/y/z ',200,-100.,100.,200,-100.,100.,int(400/redfac3d),-100.,100.)
          ut.bookHist(h,"xyz_muInter_"+str(p),   'x/y /z',200,-100.,100.,200,-100.,100.,int(600/redfac3d) ,-500.,100.)
          ut.bookHist(h,"xyz_origin_"+str(p),       'x/y /z',200,-100.,100.,200,-100.,100.,int(600/redfac3d) ,-500.,100.)
          ut.bookHist(h,"z_veto_"+str(p),      'z veto vs z neutral',100,-50.,50.,100,-50.,50.)
          ut.bookHist(h,"xy_z-30_veto_"+str(p),      'xy at z=-30cm',200,-100.,100.,200,-100.,100.)
          ut.bookHist(h,"xy_z-30_"+str(p),                  'xy at z=-30cm',200,-100.,100.,200,-100.,100.)

#  python -i $SNDBUILD/sndsw/macro/run_simScript.py --shiplhc -f muonDis_1108.root --MuDIS  --output run_1108  -n 99999999
#  prod = str(run+cycle*100+k), k=0 or 1000, mu+ or mu-,  number of cycles: 10 events per incoming muon in each cycle)
   if path.find('eos')<0:  g = ROOT.TFile.Open(path+geofileExample)
   else:                                  g = ROOT.TFile.Open(os.environ['EOSSHIP']+path+geofileExample)
   geoManager = g.FAIRGeom
   if path.find('eos')<0:
        topDir  = os.listdir(path)
   else:
        topDir  = str( subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+path,shell=True) )
   # for cycle in [options.nMult ]:
   for run in range(rMin,rMax):
    for k in muRange:
     for subjob in range(sMin,sMax):
       if pythia6:
          if options.Emin==0:  prod = 'run_'+str(run+cycle*100+k)+'_'+str(subjob)
          else:  prod = "ecut"+str(options.Emin)+'_run_'+str(run+cycle*100+k)+'_'+str(subjob)
       else:
                       prod = k+"_"+str(subjob)
       if path.find('eos')<0:
          if not prod in topDir:
                  print('prod not found ',prod)
                  continue
          if not geofile in os.listdir(path+prod):
                 print('no geofile found ',path+prod)
                 continue
       else:
          if not "/"+prod in topDir: 
                  print('prod not found on eos',prod)
                  continue
          temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+path+prod,shell=True)
          if not  geofile in str(temp):
                 print('no geofile found on eos',path+prod)
                 continue
       if pythia6:  rc = h['fullStats'].Fill(run+cycle*100+k)
       if path.find('eos')<0:   h['f']  = ROOT.TFile.Open(path+prod+datafile)
       else:                                    h['f']  = ROOT.TFile.Open(os.environ['EOSSHIP']+path+prod+datafile)
       nEv = -1
       for sTree in h['f'].cbmsim:
            nEv+=1
            if nEv%1000 == 0: print('N ',nEv,prod)
            muon                = sTree.MCTrack[0]
            muonEnergy = muon.GetEnergy()
            mupid               = muon.GetPdgCode()
            muInterVx      = ROOT.TVector3(muon.GetStartX(),muon.GetStartY(),muon.GetStartZ())
            if pythia6:
           # weights on muonDIs files: incoming muon has original FLUKA weight, outgoing particles FLUKA weight/options.nMult
           # unfortunately, weight of outgoing particles is overwritten by MuDISGenerator with  density along trajectory as weight, g/cm^2
               nMult = 10
               wLHC   =  norm*muon.GetWeight()/float(nMult)
               wInter  =  sTree.MCTrack[2].GetWeight()    # put density along trajectory as weight, g/cm^2
                                                                                                    # fast MC used NinteractionLength   * 97.5 g cm-2 interaction length of concrete  --> wInter
               wDis    = wInter / 1.67E-24 * h['g_'+str(mupid)].Eval(muonEnergy ) * 1E-27
               rc = h['wDIS_'+str(mupid)].Fill(wDis)
               W = wLHC*wDis
            else:
               W = norm*muon.GetWeight()
            rc   = h['inMu_0'+str(mupid)].Fill(muonEnergy,0,W)
            rc   = h['xyz_mu_0'+str(mupid)].Fill(muon.GetStartX(),muon.GetStartY(),muon.GetStartZ(),W)

            motherOf = {}
            for d in sTree.MCTrack:
               motherOf[d] = d.GetMotherId()
            daughterOf = dict(zip(motherOf.values(), motherOf.keys()))

            neutrals = {}
            tagged = -1
            n = -1
            for m in sTree.MCTrack:
                 n+=1
                 Apid = abs(m.GetPdgCode())
                 if  Apid in neuPartList:
# check origin of neutral particle, only count particles from outside
                     nodeOrigin  = geoManager.FindNode(m.GetStartX(),m.GetStartY(),m.GetStartZ())
                     om = nodeOrigin.GetName()
                     if not( om=='VTI18_1' or om=='Vrock_1' or om=='cave_1'):  continue
# find end vertex:
                     endZ         = 999.
                     concrete = False
                     if n in daughterOf:
                        d = daughterOf[n]
                        endZ = d.GetStartZ()
                        nodeInter   = geoManager.FindNode(d.GetStartX(),d.GetStartY(),d.GetStartZ())
                        if nodeInter.GetName()=='VTI18_1' or  nodeInter.GetName()=='Vrock_1':  concrete = True
                     if not endZ<999.: continue
                     origin = ''
                     if m.GetProcID()!=0 : origin = '_secondary'
                     rc = h['inE_'+str(m.GetPdgCode())+origin].Fill(m.GetEnergy(),endZ,W)
                     if concrete:   rc = h['inE_Concrete_'+str(m.GetPdgCode())+origin].Fill(m.GetEnergy(),endZ,W)
                     elif debug>2 and m.GetEnergy()>75. and endZ>-25. and endZ<25. and Apid==130 :
                          tagged = n
                          print('tagged ',h['f'].GetName(),nEv,tagged)
                     #elif endZ<-100: 
                     #   print('what is this place?',nodeInter.GetName(),m.GetPdgCode(),m.GetP(),d.GetProcName())
                     #  decay or photonpair prod or hadronic inelastic
                     nm = nodeInter.GetName()
                     if nm!='VTI18_1' and nm!='Vrock_1' and nm!='cave_1' and endZ<25:                  # only interested in emulsion
                                       # if Apid==130:   print('what is this place called',h['f'].GetName(),nEv,n,d,nm)
                                       neutrals[n] = [m.GetProcID(),nm,d.GetStartX(),d.GetStartY(),d.GetStartZ()]
            if sTree.ScifiPoint.GetEntries()<1: continue
            if len(neutrals)<1                                : continue
# find neutral with highest energy
            eMax, neu = -1,0
            for x in neutrals:
                E = sTree.MCTrack[x].GetEnergy()
                if E>eMax:
                   eMax,neu=E,x
            if debug>3: print('debug',len(neutrals),E,sTree.MCTrack[x])
# look for veto hit
# special case, low energy neutrons can also make a hit.
            vetoPoint, zMinCharged = -1,999.
            for det in [sTree.ScifiPoint,sTree.MuFilterPoint]:   # also loop over MuFilterPoint to get hits in veto station
             nP = -1
             for p in det:
                nP+=1
                part = PDG.GetParticle(p.PdgCode())
                charge = -1
                if part: charge = part.Charge()
                if  charge != 0 and p.GetZ() < zMinCharged :
                        vetoPoint,zMinCharged         = p,p.GetZ()
            if debug>2 and tagged >0:
                print("What happened",neu)
            Npart = sTree.MCTrack[neu]
            E     = Npart.GetEnergy()
            pid = Npart.GetPdgCode()
            # neutral particle interaction point, neutral particle origin, muon interaction point
            neutInterVx = [neutrals[neu][2],neutrals[neu][3],neutrals[neu][4]]
            veto = zMinCharged < neutInterVx[2]
            rc   =                          h['xyz_Inter_'+str(pid)].Fill(neutInterVx[0],neutInterVx[1],neutInterVx[2],W)
            if E>100.:    rc   = h['xyzE100_Inter_'+str(pid)].Fill(neutInterVx[0],neutInterVx[1],neutInterVx[2],W)
            rc   = h['xyz_origin_'+str(pid)].Fill(Npart.GetStartX(),Npart.GetStartY(),Npart.GetStartZ(),W)
            rc   = h['xyz_muInter_'+str(pid)].Fill(muInterVx.X(),muInterVx.Y(),muInterVx.Z(),W)
            if  veto: 
                  rc    = h['xyzVeto_Inter_'+str(pid)].Fill(neutInterVx[0],neutInterVx[1],neutInterVx[2],W)
                  rc    = h["E_veto_"+str(pid)].Fill(E,neutInterVx[2],W)
                  p     = vetoPoint
                  P     = ROOT.TVector3(p.GetPx(),p.GetPy(),p.GetPz())
                  pidVeto = p.PdgCode()
                  if not pidVeto in  pidsDictRev:
                         print("!!!! unknown pid",pidVeto)
                         L = len(pidsDictRev)
                         pidsDictRev[pidVeto] = L
                         rc = h['pidsDict'].SetBinContent(L+1,pidVeto)
                  rc    = h["E_vetoParticle_"+str(pid)].Fill(P.Mag(),pidsDictRev[pidVeto],W)
                  rc   =  h["z_veto_"+str(pid)].Fill(neutInterVx[2],zMinCharged)
            else:
                  rc   = h["E_"+str(pid)].Fill(E,neutInterVx[2],W)
            if  Npart.GetProcID()==0:
                if  veto: rc    = h["Eprim_veto_"+str(pid)].Fill(E,neutInterVx[2],W)
                else:       rc   = h["Eprim_"+str(pid)].Fill(E,neutInterVx[2],W)
#
# check for particles in the first muon station to study about increased veto detector
            for p in sTree.MuFilterPoint:
                 if p.GetZ()<50. and p.GetZ()>0:
                      track = p.GetTrackID()
                      if track<0: continue
                      V = sTree.MCTrack[track]
                      if V.GetStartZ()<-35:
                         rc = h["xy_z-30_"+str(pid)].Fill(p.GetX(),p.GetY(),W)
                         if veto: rc = h["xy_z-30_veto_"+str(pid)].Fill(p.GetX(),p.GetY(),W)
       h['f'].Close()
   h['3d']=h['xyz_muInter_130'].Clone('3d')
   h['3d'].Add(h['xyz_muInter_2112'])
   h['3d'].Add(h['xyz_muInter_-2112'])
   if pythia6:
       if options.Emin==0:  ut.writeHists(h,"muonDISfull-"+str(sMin)+"_"+str(sMax)+"_"+str(cycle)+".root")
       else:                                 ut.writeHists(h,"muonDISfull-"+str(options.Emin)+'_'+str(sMin)+"_"+str(sMax)+"_"+str(cycle)+".root")
   else:
       ut.writeHists(h,"muonGeant4full-"+str(sMin)+"_"+str(sMax)+".root")
def thermNeutron():
# under development, not used, low energy neutrons not stored.
     f=ROOT.TFile.Open('root://eospublic.cern.ch//eos/experiment/ship/user/truf/SND/muonDis/run_1_0/ship.conical.muonDIS-TGeant4.root')
     ut.bookHist(h,'n_2112','logE MeV',100,-10,2)
     ut.bookHist(h,'n_-2112','logE MeV',100,-10,2)
     L=ROOT.TLorentzVector()
     nMult = 10
     norm = 5.83388
     fin = ROOT.TFile('muDIScrossSec.root')
     ROOT.gROOT.cd()
     for pid in ['13','-13']: 
          h['g_'+pid] = fin.Get('g_'+pid).Clone('g_'+pid)
     for sTree in f.cbmsim:
         muon                = sTree.MCTrack[0]
         muonEnergy = muon.GetEnergy()
         mupid               = muon.GetPdgCode()
         wLHC   =  norm*muon.GetWeight()/float(nMult)
         wInter  =  sTree.MCTrack[2].GetWeight()
         wDis    = wInter / 1.67E-24 * h['g_'+str(mupid)].Eval(muonEnergy ) * 1E-27
         W = wLHC*wDis
         for m in sTree.MCTrack:
               if abs(m.GetPdgCode()) == 2112:
                   m.Get4Momentum(L)
                   logE = ROOT.TMath.Log10( 1000.*(L.Energy()-L.M()))
                   rc = h['n_'+str(m.GetPdgCode())].Fill(logE,W)
def analyzeDIS(NsubJobs=0,delta=13,hists="muonDISfull.root",runCoverage=6.):
    pathToPlots = "/mnt/hgfs/microDisk/CERNBOX/SND@LHC/MuonDis/"
    latex = 'latex.txt'
    if options.pythia6<0:
          pathToPlots =  "/mnt/hgfs/microDisk/CERNBOX/SND@LHC/MuonGeant4/"
          latex = 'latex-geant4.tex'
    if NsubJobs==0:
      # one cycle = 10x muon statistics
       ut.readHists(h,hists)
    else:
        s = 0
        while s < NsubJobs:
          sMin,sMax = s,s+delta
          print("reading muonDISfull-"+str(sMin)+"_"+str(sMax)+".root" )
          ut.readHists(h,"muonDISfull-"+str(sMin)+"_"+str(sMax)+".root")
          s+=delta

    ut.bookCanvas(h,'muDIS_SND2','incoming muon energy',1500,900,2,1)
    c=h['muDIS_SND2'].cd(1)
    hname = "inMu"
    h[hname] = h["inMu_013" ].ProjectionX(hname)
    h[hname].Add(h["inMu_0-13" ].ProjectionX())
    ut.makeIntegralDistrib(h,hname)
    h['I-'+hname].SetTitle('incoming muon energy;> E [GeV/c];N arbitrary units')
    h['I-'+hname].SetMinimum(1.E-6)
    h['I-'+hname].SetStats(0)
    h['I-'+hname].SetLineWidth(3)
    h['I-'+hname].Draw('hist')
    c=h['muDIS_SND2'].cd(2)
    h[hname].SetTitle('incoming muon energy; E [GeV/c];N arbitrary units')
    h[hname].SetStats(0)
    h[hname].SetLineWidth(3)
    h[hname].Draw('hist')
    myPrint(h['muDIS_SND2'],'inMuEnergy.png',pathToPlots=pathToPlots)
#
    c=h['muDIS_SND2'].cd(1)
    hname = "xyz_mu_0"
    for x in ['13','-13']:
       h["xy_mu_0"+x] = h["xyz_mu_0"+x].Project3D('yx')
       h["xy_mu_0"+x].SetName("xy_mu_0"+x)
       h["xy_mu_0"+x].SetStats(0)
       h["xy_mu_0"+x].SetTitle(PDG.GetParticle(int(x)).GetName()+' ;x  [cm]; y  [cm]')
       h["xy_mu_0"+x].Draw('colz')
       c=h['muDIS_SND2'].cd(2)
    myPrint(h['muDIS_SND2'],'inMu_0XY',pathToPlots=pathToPlots)
    h["xyz_mu_0"]=h["xyz_mu_013"].Clone("xyz_mu_0")
    h["xyz_mu_0"].Add(h["xyz_mu_0-13"])
    h["yz_mu_0"] = h["xyz_mu_0"].Project3D('yz')
    h["yz_mu_0"].SetName("yz_mu_0")
    h["yz_mu_0"].SetStats(0)
    h["yz_mu_0"].SetTitle("; z [cm]; y [cm]")
    ut.bookCanvas(h,'muDIS_SNDyz','incoming muon',1200,900,1,1)
    c=h['muDIS_SNDyz'].cd()
    h["yz_mu_0"].Draw('colz')
    myPrint(h['muDIS_SNDyz'],'inMu_0YZ',pathToPlots=pathToPlots)

    parts = [130,2112,-2112,310,3122,-3122,3322,-3322,22]
# 1E34 cm-2 s-1, 1fb = 1e-39 cm2, means 1fb requires 1E5 sec
    fbScale = 1E5
    ut.bookCanvas(h,'muDIS_N0In','primary neutrals',1200,1200,3,3)
    for k in range(len(parts)):
        pid = parts[k]
        pname = PDG.GetParticle(pid).GetName()
        tc=h['muDIS_N0In'].cd(k+1)
        tc.SetLogy(1)
        hname = "inE_"+str(pid)                        # all primary  particles
        hConcr = "inE_Concrete_"+str(pid)  # origin from concrete
        hout      = "inE_out_"+str(pid)              # going out
        h[hout]                        = h[hname].Clone(hout)
        h[hout].Add(h[hConcr],-1.)
        h[hout+'_projx']     =  h[hout].ProjectionX(hout+'_projx')
        h[hname+'_projx'] =  h[hname].ProjectionX(hname+'_projx')
        h[hout+'_projx'].SetMarkerStyle(20)
        h[hname+'_projx'].SetMarkerStyle(27)
        h[hname+'_projx'].SetStats(0)
        binw = int(h[hname+'_projx'].GetBinWidth(1))
        h[hname+'_projx'].GetYaxis().SetTitle('N [Hz/'+str(binw)+'GeV]')
        h[hout+'_projx'].SetMarkerStyle(29)
        h[hname+'_projx'].GetXaxis().SetRangeUser(0.,2900.)
        h[hname+'_projx'].GetXaxis().SetTitle('Energy   [GeV]    ')
        h[hname+'_projx'].SetTitle(pname)
        h[hname+'_projx'].GetYaxis().SetTitleOffset(1.2)
        h[hname+'_projx'].SetMaximum(20.)
        h[hname+'_projx'].Draw('PHIST')
        h[hname+'_projx'].Draw('histsame')
        h[hout+'_projx'].SetLineColor(ROOT.kRed)
        h[hout+'_projx'].Draw('SAMEPHIST')
        h[hout+'_projx'].Draw('histsame')
    myPrint(h['muDIS_N0In'],'EofPrimNeutrals',pathToPlots=pathToPlots)

    tname = 'muDIS_inSND'
    ut.bookCanvas(h,tname,'neutrals not in concrete and z>-25cm',1200,1200,3,3)
    for k in range(len(parts)):
        pid = parts[k]
        pname = PDG.GetParticle(pid).GetName()
        tc=h[tname].cd(k+1)
        tc.SetLogy(1)
        h["inE_prim_"+str(pid)] = h["inE_"+str(pid)].Clone("inE_prim_"+str(pid))
        h["inE_prim_"+str(pid)].Add(h["inE_Concrete_"+str(pid)],-1)
        h["inE_seco_"+str(pid)] = h["inE_"+str(pid)+'_secondary'].Clone("inE_"+str(pid)+'_secondary_out')
        h["inE_seco_"+str(pid)].Add(h["inE_Concrete_"+str(pid)+'_secondary'],-1)
        for x in ['prim_','seco_']:
           zmin  = h["inE_"+x+str(pid)].GetYaxis().FindBin(-25.)
           zmax = h["inE_"+x+str(pid)].GetYaxis().FindBin(+25.)
           hname = "inE_"+x+str(pid)+'_SND'
           h[hname] =   h["inE_"+x+str(pid)].ProjectionX(hname,zmin,zmax)
           h[hname].SetStats(0)
           binw = int(h[hname].GetBinWidth(1))
           h[hname].GetYaxis().SetTitle('N [Hz/'+str(binw)+'GeV]')
           h[hname].GetXaxis().SetRangeUser(0.,2900.)
           h[hname].GetXaxis().SetTitle('Energy   [GeV]    ')
           h[hname].SetTitle(pname)
           h[hname].GetYaxis().SetTitleOffset(1.2)
           h[hname].SetMaximum(20.)
           h[hname].SetMinimum(1.E-6)
        hname = "inE_prim_"+str(pid)+'_SND'
        h[hname].SetLineColor(ROOT.kRed)
        h[hname].Draw('hist')
        hname = "inE_seco_"+str(pid)+'_SND'
        h[hname].SetLineColor(ROOT.kBlue)
        h[hname].Draw('histsame')
    myPrint(h[tname],'EofNeutralsInSND',pathToPlots=pathToPlots)

    colour = {}
    colour['']                                       = ROOT.kRed
    colour['_secondary']               = ROOT.kBlue
    minMax = {'out_':[9,1E-6],'Concrete_':[30.,1E-5]}
    for k in range(len(parts)):
        pid = parts[k]
        for origin in ['_secondary','']:
             hname    = "inE_"+str(pid)+origin                           # all primary particles
             hConcr   = "inE_Concrete_"+str(pid) +origin   # end in concrete
             hout        = "inE_out_"+str(pid)+origin                 # end somewhere else
             h[hout]   = h[hname].Clone(hout)
             h[hout].Add(h[hConcr],-1.)

    for c in ['out_','Concrete_']:
        tname = 'muDIS_neuZend'+c
        ut.bookCanvas(h,tname,'end vertex z',1200,1200,3,3)
        for k in range(len(parts)):
            pid = parts[k]
            pname = PDG.GetParticle(pid).GetName()
            tc=h[tname].cd(k+1)
            tc.SetLogy(1)
            for origin in ['_secondary','']:
# only primaries
                hname = "inE_"+c+str(pid)+origin
                h[hname+'_projz'] =  h[hname].ProjectionY(hname+'_projz')
                h[hname+'_projz'].SetLineColor(colour[origin])
                h[hname+'_projz'].SetStats(0)
                binw = int(h[hname+'_projz'].GetBinWidth(1))
                h[hname+'_projz'].GetYaxis().SetTitle('N [Hz/'+str(binw)+'GeV]')
                h[hname+'_projz'].GetXaxis().SetTitle('z   [cm]    ')
                h[hname+'_projz'].SetTitle(pname)
                h[hname+'_projz'].GetYaxis().SetTitleOffset(1.2)
                h[hname+'_projz'].SetMaximum(minMax[c][0])
                h[hname+'_projz'].SetMinimum(minMax[c][1])
                if origin=='_secondary': h[hname+'_projz'].Draw('HIST')
                else:                        h[hname+'_projz'].Draw('HISTsame')
        myPrint(h[tname],c+'zEndOfNeutrals',pathToPlots=pathToPlots)


# vertices, note:  'xyz_muInter','xyz_Inter','xyz_origin' are for events with hits 
    for hist in ['xyz_muInter','xyz_Inter','xyzE100_Inter','xyz_origin','inE','inE_Concrete','xyzVeto_Inter','z_veto']:
        first = True
        for pid in parts:
               if pid==22: continue
               if first: 
                      h[hist] = h[hist+'_'+str(pid)].Clone(hist)
                      first = False
               else: h[hist].Add(h[hist+'_'+str(pid)])
    h['inE-noConc']=h['inE'].Clone('inE-noConc')
    h['inE-noConc'].Add(h['inE_Concrete'],-1.)
    h['inE-noConc_22']=h['inE_22'].Clone('inE-noConc_22')
    h['inE-noConc_22'].Add(h['inE_Concrete_22'],-1.)
    for hist in ['xyz_muInter','xyz_Inter','xyzE100_Inter','xyz_origin','inE','inE-noConc','xyzVeto_Inter','z_veto']:
           if  h[hist].ClassName() == 'TH2D': 
                h[hist+'_z']=h[hist].ProjectionY(hist+'_z')
                h[hist+'_22_z']=h[hist+'_22'].ProjectionY(hist+'_22_z')
                h[hist+'_22_z'].SetTitle(';z [cm]')
                h[hist+'_z'].SetTitle(';z [cm]')
           else: 
                for g in ['','_22']:
                   h[hist+g+'_z']  =h[hist+g].ProjectionZ(hist+g+'_z')
                   h[hist+g+'_z'].SetTitle(';z [cm]')
                   h[hist+g+'_xy']=h[hist+g].Project3D('yx')
                   h[hist+g+'_xy'].SetName(hist+g+'_xy')
                   h[hist+g+'_xy'].SetTitle(';x  [cm]; y  [cm]')
                   h[hist+g+'_xy'].SetStats(0)
                   h[hist+g+'_xz']=h[hist+g].Project3D('xz')
                   h[hist+g+'_xz'].SetName(hist+g+'_xz')
                   h[hist+g+'_xz'].SetTitle(';z  [cm]; x  [cm]')
                   h[hist+g+'_xz'].SetStats(0)
                   h[hist+g+'_yz']=h[hist+g].Project3D('yz')
                   h[hist+g+'_yz'].SetName(hist+g+'_yz')
                   h[hist+g+'_yz'].SetTitle(';z  [cm]; y  [cm]')
                   h[hist+g+'_yz'].SetStats(0)
           h[hist+'_z'].SetStats(0)
           h[hist+'_z'].SetTitle('; z  [cm]')
           ut.bookCanvas(h,'vertices'+hist+'_z','vertices '+hist,1200,900,1,1)
           tc = h['vertices'+hist+'_z'].cd()
           if hist=='z_veto':                tc.SetLogy()
           if hist=='xyzVeto_Inter': tc.SetLogy()
           if hist in ['xyz_muInter','xyz_origin']:
                    h[hist+'_z'].Draw()
           else:
                    h[hist+'_22_z'].SetStats(0)
                    h[hist+'_22_z'].SetLineColor(ROOT.kRed)
                    h[hist+'_22_z'].Draw()
                    h[hist+'_z'].Draw('same')
           if hist=='xyzE100_Inter':
               txtlam = 'empty'
               txtrad = 'empty'
               if h[hist+'_z'].GetEntries()>10:
                  rc = h[hist+'_z'].Fit('expo','S','',-25.,30.)
                  fitresult = rc.Get()
                  txtlam = '#lambda =%4.1Fcm'%(-1./fitresult.GetParams()[1])
                  rc = h[hist+'_22_z'].Fit('expo','SL','',-30.,10.)
                  fitresult = rc.Get()
                  funRad =h[hist+'_22_z'].GetFunction('expo')
                  funRad.SetBit(ROOT.TF1.kNotDraw)
                  funRad.SetLineColor(h[hist+'_22_z'].GetLineColor())
                  txtrad = 'X_{0}  =%4.1Fcm'%(-1./fitresult.GetParams()[1])
                  h[hist+'_z'].GetFunction('expo').SetLineColor(h[hist+'_z'].GetLineColor())
               h[hist+'_z'].Draw()
               h[hist+'_22_z'].Draw('same')
               T = ROOT.TLatex()
               T.DrawLatex(-10,0.005,txtlam)
               #T.DrawLatex(-10,0.0045,txtrad)
           myPrint(h['vertices'+hist+'_z'],hist+'_z',pathToPlots=pathToPlots)
           if  h[hist].ClassName() == 'TH3D':
              for proj in ['xy','xz','yz']:
                 ut.bookCanvas(h,'vertices'+hist+'_'+proj,'vertices '+hist,1200,900,1,1)
                 tc = h['vertices'+hist+'_'+proj].cd()
                 h[hist+'_'+proj].Draw('colz')
                 myPrint(h['vertices'+hist+'_'+proj],hist+'_'+proj,pathToPlots=pathToPlots)

    ut.bookCanvas(h,'verticesinE_z','vertices inE_z',1200,900,1,1)
    h['verticesinE_z'].cd()
    h["inE-noConc_z"].SetLineColor(ROOT.kRed)
    h["inE_z"].Draw('hist')
    h["inE-noConc_z"].Draw('samehist')
    myPrint(h['verticesinE_z'],"inE_z",pathToPlots=pathToPlots)
    ut.bookCanvas(h,'verticesxyz_Inter_z','vertices xyz_Inter_z',1200,900,1,1)
    h['verticesxyz_Inter_z'].cd()
    h['xyz_Inter_z'].GetXaxis().SetRangeUser(-50.,100.)
    h["xyz_Inter_z"].Draw('hist')
    myPrint(h['verticesxyz_Inter_z'],"verticesxyz_Inter_z",pathToPlots=pathToPlots)
# multiplicities
    withMult=False
    if withMult:
     ut.bookCanvas(h,'mult',' ',1200,900,1,1)
     tc = h['mult'].cd()
     tc.SetLogy(1)
     mults = {22:[19,ROOT.kMagenta],130:[20,ROOT.kRed],2112:[22,ROOT.kBlue],-2112:[23,ROOT.kCyan],
                       310:[21,ROOT.kOrange],3122:[24,ROOT.kGreen-1],-3122:[25,ROOT.kGreen+1],
                       3322:[26,ROOT.kGreen-2],-3322:[27,ROOT.kGreen+2]}
     h['legmult']=ROOT.TLegend(0.6,0.6,0.82,0.75)
     for m in mults:
         hist = 'mult_'+str(m)
         h[hist].SetStats(0)
         h[hist].SetTitle('; N')
         h[hist].SetMarkerStyle(mults[m][0])
         h[hist].SetMarkerColor(mults[m][1])
         h[hist].SetLineColor(mults[m][1])
         rc = h['legmult'].AddEntry(h[hist],PDG.GetParticle(m).GetName(),'PL')
     h['mult_22'].Draw()
     for m in mults:    h['mult_'+str(m)].Draw('same')
     h['legmult'].Draw('same')
     myPrint(h['mult'],"neutralMultiplicities",pathToPlots=pathToPlots)
    for pid in parts:
     ut.makeIntegralDistrib(h,"inE_"+str(pid))
     ut.makeIntegralDistrib(h,"inE_Concrete_"+str(pid))
     for  o in ["","prim"]:
      hname       = "Esnd"+o+"_"+str(pid)
      h[hname] = h["E"+o+"_"+str(pid)].ProjectionX(hname)
      h["Esnd"+o+"_all_"+str(pid)] = h["E"+o+"_veto_"+str(pid)].ProjectionX("Esnd"+o+"_all_"+str(pid))
      h["Esnd"+o+"_all_"+str(pid)] .Add(h[hname] )
      ut.makeIntegralDistrib(h,hname)
      h['I-'+hname].GetXaxis().SetRangeUser(0.,1000.)
      h['I-'+hname].SetMinimum(1E-6)
      ut.makeIntegralDistrib(h,"Esnd"+o+"_all_"+str(pid))
    for  o in ["","prim"]:
     ut.bookCanvas(h,'muDIS_SND'+o,'neutrals arriving at SND',1800,1200,3,3)
     for k in range(len(parts)):
        tc=h['muDIS_SND'+o].cd(k+1)
        tc.SetLogy(1)
        tc.SetLogx(0)
        pname = PDG.GetParticle(parts[k]).GetName()
        hname       = "Esnd"+o+"_"+str(parts[k])
        hnameAll = "Esnd"+o+"_all_"+str(parts[k])
        for X in [hname,hnameAll]:
           h['IFB-'+X] = h['I-'+X].Clone('IFB-'+X)
           h['IFB-'+X].Scale(150.*fbScale)
           h['IFB-'+X].SetTitle(pname+';> E [GeV/c];N /150 fb^{-1}')
           h['IFB-'+X]. GetYaxis().SetTitleOffset(1.4)
           h['IFB-'+X]. GetXaxis().SetRangeUser(0.1,1200.)
           h['IFB-'+X].SetMaximum(2E7)
           h['IFB-'+X].SetStats(0)
           h['IFB-'+X].SetLineWidth(3)
           h['IFB-'+X].SetMinimum(1.0)
        h['IFB-'+hnameAll].Draw('hist')
        h['IFB-'+hname].SetLineColor(ROOT.kRed)
        h['IFB-'+hname].Draw('histsame')
        hist = h['I-'+hname]
        histAll = h['I-'+hnameAll]
        print("---->  results for "+o)
        for E in [0,10,100,200,300,500,1000]:
            n = hist.FindBin(E)
            RVeto =  hist.GetBinContent(n)      / runCoverage
            R           =  histAll.GetBinContent(n) / runCoverage
            faser = ''
            if  parts[k] in FASERNU:
                  if E in FASERNU[parts[k]]:
                       faser = "%5.2G"%( FASERNU[parts[k]][E]*scaleFactor )
            print("E>%i GeV,    %s:  %5.2F N/sec   %5.2F  N fb  with Veto: %5.2F  N fb |    %5.2G     veto %5.2G   (%s) "%(E,pname,R,R*fbScale,RVeto*fbScale,R*150.*fbScale,RVeto*150.*fbScale,faser))
     myPrint(h['muDIS_SND'+o],'muDIS_SND'+o,pathToPlots=pathToPlots)
# make latex output
     fout = open(latex,'w')
     platex = {2112:'$n$' ,-2112: '$\overline{n}$' ,130:'$K_L$',310:'$K_S$',3122:'$\Lambda$',-3122:'$\overline{\Lambda}$',3322:'$\Xi + \overline{\Xi}$',22:'$\gamma$'}

     for x in [2112,-2112,130,310,3122,-3122,3322,22]:
          line = platex[x]
          for E in [10,100,200,300,500,1000]:
               pname = PDG.GetParticle(x).GetName()
               hnameAll = "Esnd"+"_all_"+str(x)
               histAll = h['I-'+hnameAll]
               n  = histAll.FindBin(E)
               R  =  histAll.GetBinContent(n) / runCoverage
               if x == 3322: R+=h['I-'+hnameAll.replace('3322','-3322')].GetBinContent(n) / runCoverage
               R150 = R*150.*fbScale
               if R150<1E-8: R150=0
               if R150<1000: line +=  "&  $%5.1F$"%(R150)
               else:                     line +=  "&  $%6.2G$"%(R150)
          line+=  "\\\\  \n"
          #print(line)
          xline = line.replace('E+0','\,10^') 
          fout.write(xline)
     fout.write("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n")
     for x in [2112,-2112,130,310,3122,-3122,3322,22]:
          line = platex[x]
          for E in [10,100,200,300,500,1000]:
               pname = PDG.GetParticle(x).GetName()
               hname = "Esnd_"+str(x)
               hist= h['I-'+hname]
               n  = hist.FindBin(E)
               R  =  hist.GetBinContent(n) / runCoverage
               if x == 3322: R+=h['I-'+hname.replace('3322','-3322')].GetBinContent(n) / runCoverage
               R150 = R*150.*fbScale
               if R150<1E-8: R150=0
               if R150<1000: line +=  "&  $%5.1F$"%(R150)
               else:                     line +=  "&  $%6.2G$"%(R150)
          line+=  "\\\\  \n"
          #print(line)
          xline = line.replace('E+0','\,10^') 
          fout.write(xline)
     fout.write("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
     for x in [2112,-2112,130,310,3122,-3122,3322,22]:
          line = platex[x]
          for E in [10,100,300,1000]:
               faser = FASERNU[x][E]*scaleFactor
               if x == 3322: faser+=FASERNU[-x][E]*scaleFactor
               if faser<1000: line +=  "&  $%5.1F$"%(faser)
               else:                     line +=  "&  $%6.2G$"%(faser)
          line+=  "\\\\  \n"
          #print(line)
          xline = line.replace('E+0','\,10^') 
          fout.write(xline)
     fout.close()

FASERNU={}
FASERNU[2112]  ={10:27.8E3,100:1500,300:150,1000:2.2}
FASERNU[-2112] ={10:15.5E3,100:900,300:110,1000:2.8}
FASERNU[3122]  ={10:5.3E3,100:390,300:39,1000:0.9}
FASERNU[-3122] ={10:3.4E3,100:290,300:31,1000:0.6}
FASERNU[310]     ={10:1.3E3,100:240,300:52,1000:1.8}
FASERNU[130]     ={10:1.6E3,100:270,300:55,1000:1.2}
FASERNU[22]     ={10:2.2E6,100:160E3,300:38.2E3,1000:5.9E3}
FASERNU[3322]     = { 10:240, 100:13, 300:2.3,1000:0.1}
FASERNU[-3322]     = {10:150.,100:10,300:1.4,1000:0}
scaleFactor = (42.*42.)/(24.*24.)

import os,subprocess,time,multiprocessing
import pwd
ncpus = multiprocessing.cpu_count()

def count_python_processes(macroName):
    username = pwd.getpwuid(os.getuid()).pw_name
    callstring = "ps -f -u " + username
# only works if screen is wide enough to print full name!
    status = subprocess.check_output(callstring,shell=True)
    n=0
    for x in status.decode().split('\n'):
        if not x.find(macroName)<0 and not x.find('python') <0: n+=1
    return n

def muonDISProduction(cycle,ecut=1.,strippedEvents=False):
     for run in range(1,11):
       for k in [0,1000]:
             prod = str(run+cycle*100+k)
             if strippedEvents: fn = "muonDis_"+prod+"_stripped.root"
             else:                            fn = "muonDis_"+prod+".root"
             command = "python  $SNDSW_ROOT/macro/run_simScript.py --shiplhc"
             os.system(command+" -f "+fn+"  --MuDIS  --output run_"+prod+"  -n 99999999  --eMin "+str(ecut) + " &")
             while count_python_processes('run_simScript')>ncpus: time.sleep(200)

def energyOfDISevents():
   for cycle in range(4):
     for run in range(1,11):
       for k in [0,1000]:
             prod   = str(run+cycle*100+k)
             print('opening','muonDis_'+str(prod)+'.root')
             f           = ROOT.TFile('muonDis_'+str(prod)+'.root')
             if not f: continue
             if not f.FindKey('DIS'): continue
             sTree = f.DIS
             for sTree in f.DIS:
                 for P in sTree.Particles:
                     hname = 'E_'+str(P.GetPdgCode())
                     if not hname in h:
                          ut.bookHist(h,hname,'Energy '+PDG.GetParticle(P.GetPdgCode()).GetName(),1000,0.,5000.)
                     rc = h[hname].Fill(P.Energy())
   ut.writeHists(h,'energyOfDISevents.root')
# maybe better to make a first selection of events with n or KL above 100GeV
# cautious, n or KL can also be produced by other particles. Specially problematic, 
# DIS events with no n or KL above 100GeV, but pion or protons make n or KL in transport!
def selectEvents(Ecut=10):
   for cycle in range(10):
     for run in range(1,11):
       for k in [0,1000]:
             prod = str(run+cycle*100+k)
             f                   = ROOT.TFile('muonDis_'+str(prod)+'.root')
             sTree = f.DIS
             fstripped = ROOT.TFile('muonDis_'+str(prod)+'_stripped.root','recreate')
             newTree = sTree.CloneTree(0)
             for sTree in f.DIS:
                 flag = False
                 for P in sTree.Particles:
                     if P.GetPdgCode() in [130,2112,-2112]:
                         if P.Energy() > Ecut:  rc = newTree.Fill()
             newTree.AutoSave()
             f.Close()
             print('f closed',prod)
             fstripped.Close() 
def signalNeutrinos():
     nudict = {'e':'$\\nu_e$','ae':'$\overline{\\nu}_e$','mu':'$\\nu_\mu$','amu':'$\overline{\\nu}_\mu$','tau':'$\\nu_\\tau$','atau':'$\overline{\\nu}_\\tau$'}
     ut.readHists(h,'/mnt/hgfs/microDisk/CERNBOX/SND@LHC/Neutrinos/SND_Neutrinos_Interacting_CCDIS.root')
     for p in ['','a']:
       for nu in [ 'e','mu','tau']:
         line = ''
         hname = 'h'+p+'nu'+nu
         ut.makeIntegralDistrib(h,hname)
         hist = h['I-'+hname]
         line += nudict[p+nu]
         for E in [10,100,200,300,500,1000]:
            n = hist.FindBin(E)
            N = hist.GetBinContent(n)
            line += ' & '+'$%5.1F$'%(N)
         line +=' \\\\'
         print(line)

def missing3Dproj(hist,ymin,ymax):
     h[hist+'XZ']=h[hist].Project3D('xz')
     h[hist+'XZ'].SetName(hist+'XZ')
     h[hist+'XZ'].Reset()
     for ix in range(1,h[hist].GetNbinsX()+1):
        for iz in range(1,h[hist].GetNbinsZ()+1):
           N = 0
           for iy in range(ymin,ymax): N+=h[hist].GetBinContent(ix,iy,iz)
           h[hist+'XZ'].SetBinContent(iz,ix,N)


if not options.command.find("muonDIS")<0:
     if options.pythia6 > 0:
             muonDISfull(cycle=options.nMult,sMin=options.nStart,sMax=options.nStart+options.nEvents)
     else:
             muonDISfull(cycle = options.nMult,sMin=options.nStart,sMax=options.nStart+options.nEvents,rMin=1,rMax=2,path = options.muonIn,pythia6=False)

elif not options.command.find("convert")<0: convertAscii2Root(options.muonIn)
elif not options.command.find("make")<0:    makeMuDISEvents(nucleon=options.nucleon)
elif not options.command.find("ana")<0:     analyze(options.muonIn)
elif not options.command.find("cross")<0:   getPythiaCrossSec(options.nEvents)
elif not options.command.find("muonPreTransport")<0:    muonPreTransport()
elif not options.command.find("muon")<0:    muonRateAtSND()

# conversion from sec to fb, nominal lumi =  1E34 cm-2 s-1, 1fb = 1e-39, means 1E5 sec
