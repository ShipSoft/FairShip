from __future__ import print_function
import ROOT,time,os,sys
nJob   = 1
nMult  = 1000 # 100000 # number of events / muon
muonIn = '/media/Data/HNL/muVetoDIS/muDISVetoCounter.root'

#
from array import array
PDG = ROOT.TDatabasePDG.Instance()
masssq = {}

def getMasssq(pid):
  apid = abs(int(pid))
  if not apid in masssq:
    masssq[apid] = PDG.GetParticle(apid).Mass()**2
  return masssq[apid]

# prepare muon input for FairShip/Geant4 processing
# incoming muon,      id:px:py:pz:x:y:z:ox:oy:oz:pythiaid:parentid:ecut:w

# just duplicate muon n times, rather stupid job

fout  = ROOT.TFile('muonEm_'+str(nJob)+'.root','recreate')
dTree = ROOT.TNtuple("pythia8-Geant4","muons for EM studies","id:px:py:pz:x:y:z:ox:oy:oz:pythiaid:parentid:ecut:w")

# read file with muons hitting concrete wall
fin = ROOT.TFile(muonIn) # id:px:py:pz:x:y:z:w
sTree = fin.muons

for k in range(sTree.GetEntries()): 
  rc = sTree.GetEvent(k)
  # make n events / muon
  px,py,pz = sTree.px,sTree.py,sTree.pz
  x,y,z    = sTree.x,sTree.y,sTree.z
  pid,w = sTree.id,sTree.w 
  p = ROOT.TMath.Sqrt(px*px+py*py+pz*pz)
  E = ROOT.TMath.Sqrt(getMasssq(pid)+p*p)
  mu = array('d',[pid,px,py,pz,E,x,y,z,w])
  muPart = ROOT.TVectorD(9,mu)
  for n in range(nMult):
     dPart.Clear()
     iMuon.Clear()
     iMuon[0] = muPart
     m = array('d',[pid,px,py,pz,E])
     part = ROOT.TVectorD(5,m)
# copy to branch
     nPart = dPart.GetEntries()
     dPart[nPart] = part
     dTree.Fill()
fout.cd()  
dTree.Write()
print("created",sTree.GetEntries()*nMult," events")
