from __future__ import print_function
import ROOT,time,os,sys
nJob   = 2
nMult  = 10 # number of events / muon
muonIn = '$SHIPSOFT/data/muConcrete.root'
nPerJob = 20000

if len(sys.argv)>1: nJob = int(sys.argv[1])
if len(sys.argv)>2: nMult = int(sys.argv[2])
if len(sys.argv)>3: muonIn = sys.argv[3]
if len(sys.argv)>4: nPerJob = int(sys.argv[4])

#
from array import array
PDG = ROOT.TDatabasePDG.Instance()
myPythia = ROOT.TPythia6()
myPythia.SetMSEL(2)       # msel 2 includes diffractive parts
myPythia.SetPARP(2,2)     # To get below 10 GeV, you have to change PARP(2)
for kf in [211,321,130,310,3112,3122,3222,3312,3322,3334]:
   kc = myPythia.Pycomp(kf) 
   myPythia.SetMDCY(kc,1,0)

masssq = {}

def getMasssq(pid):
  apid = abs(int(pid))
  if not apid in masssq:
    masssq[apid] = PDG.GetParticle(apid).Mass()**2
  return masssq[apid]

R = int(time.time()%900000000)
myPythia.SetMRPY(1,R)
mutype = {-13:'gamma/mu+',13:'gamma/mu-'}

# DIS event
# incoming muon,      id:px:py:pz:x:y:z:w
# outgoing particles, id:px:py:pz
fout  = ROOT.TFile('muonDis_'+str(nJob)+'.root','recreate')
dTree = ROOT.TTree('DIS','muon DIS')
iMuon       = ROOT.TClonesArray("TVectorD") 
iMuonBranch = dTree.Branch("InMuon",iMuon,32000,-1)
dPart       = ROOT.TClonesArray("TVectorD") 
dPartBranch = dTree.Branch("Particles",dPart,32000,-1)

# read file with muons hitting concrete wall
fin = ROOT.TFile(muonIn) # id:px:py:pz:x:y:z:w
sTree = fin.muons

def rotate(ctheta,stheta,cphi,sphi,px,py,pz):
  #rotate around y-axis
  px1=ctheta*px+stheta*pz
  pzr=-stheta*px+ctheta*pz
  #rotate around z-axis
  pxr=cphi*px1-sphi*py
  pyr=sphi*px1+cphi*py
  return pxr,pyr,pzr

nTOT = sTree.GetEntries()

nStart = nPerJob*nJob
nEnd   = min(nTOT,nStart + nPerJob)
if muonIn.find('Concrete')<0: 
 nStart = 0
 nEnd   = nTOT

# stop pythia printout during loop
myPythia.SetMSTU(11, 11)
print("start production ",nStart,nEnd)
nMade = 0
for k in range(nStart,nEnd): 
  rc = sTree.GetEvent(k)
  # make n events / muon
  px,py,pz = sTree.px,sTree.py,sTree.pz
  x,y,z    = sTree.x,sTree.y,sTree.z
  pid,w = sTree.id,sTree.w 
  p = ROOT.TMath.Sqrt(px*px+py*py+pz*pz)
  E = ROOT.TMath.Sqrt(getMasssq(pid)+p*p)
  # px=p*sin(theta)cos(phi),py=p*sin(theta)sin(phi),pz=p*cos(theta)
  theta = ROOT.TMath.ACos(pz/p)
  phi   = ROOT.TMath.ATan2(py,px) 
  ctheta,stheta = ROOT.TMath.Cos(theta),ROOT.TMath.Sin(theta)
  cphi,sphi     = ROOT.TMath.Cos(phi),ROOT.TMath.Sin(phi)
  mu = array('d',[pid,px,py,pz,E,x,y,z,w])
  muPart = ROOT.TVectorD(9,mu)
  myPythia.Initialize('FIXT',mutype[pid],'p+',p)
  for n in range(nMult):
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
      m = array('d',[did,dpx,dpy,dpz,E])
      part = ROOT.TVectorD(5,m)
# copy to branch
      nPart = dPart.GetEntries()
      if dPart.GetSize() == nPart: dPart.Expand(nPart+10)
      dPart[nPart] = part
     nMade+=1
     if nMade%10000==0: print('made so far ',nMade)
     dTree.Fill()
fout.cd()  
dTree.Write()
myPythia.SetMSTU(11, 6)
print("created nJob ",nJob,':',nStart,' - ',nEnd," events")
