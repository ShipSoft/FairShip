from __future__ import print_function
import os,ROOT
import rootUtils as ut
path =  '/eos/experiment/ship/data/Mbias/background-prod-2018/'

# should fill hisograms with neutrinos, for mbias, exclude neutrinos from charm 
# update weight based on process/decay and PoT

charmExtern = [4332,4232,4132,4232,4122,431,411,421,15]
neutrinos = [12,14,16]

# for 10GeV Yandex Production 65.041 Billion PoT, weight = 768.75 for 5E13 pot
weightMbias = 768.75
# for 1GeV Yandex Production  1.8 Billion PoT, weight = 27778. for 5E13 pot
weightMbias1GeV = 27778.

# for 10GeV charm Production 153.3 Billion PoT equivalent, weight = 489.24
# added another cycle
weightCharm = 326.
# for 1GeV charm Production 10.2 Billion PoT equivalent, weight = 4895.24
weightCharm1GeV = 4895.24

# for 10GeV beauty Production 5336 Billion PoT equivalent, weight = 9.37
weightBeauty = 9.37

import rootUtils as ut
h={}
PDG = ROOT.TDatabasePDG.Instance()
for idnu in range(12,17,2):
  # nu or anti-nu
   for idadd in range(-1,2):
    idw=idnu
    idhnu=1000+idw
    if idadd==-1:
     idhnu+=1000
     idw=-idnu
    name=PDG.GetParticle(idw).GetName()
    title = name+" momentum (GeV)"
    key = idhnu
    ut.bookHist(h,key,title,400,0.,400.)
    title = name+"  log10-p vs log10-pt"
    key = idhnu+100
    ut.bookHist(h,key,title,100,-0.3,1.7,100,-2.,0.5)
    title = name+"  log10-p vs log10-pt"
    key = idhnu+200
    ut.bookHist(h,key,title,25,-0.3,1.7,100,-2.,0.5)

def processFile(fin,noCharm=True):
    f   = ROOT.TFile.Open(os.environ['EOSSHIP']+path+fin)
    print("opened file ",fin)
    sTree = f.cbmsim
    for n in range(sTree.GetEntries()):
      sTree.GetEntry(n)
      for v in sTree.vetoPoint:
       nu = v.GetTrackID()
       t = sTree.MCTrack[nu]
       pdgCode = t.GetPdgCode()
       if abs(pdgCode) not in neutrinos: continue
       moID  = abs(sTree.MCTrack[t.GetMotherId()].GetPdgCode())
       if moID in charmExtern and noCharm: continue  # take heavy flavours from separate production
       idhnu=abs(pdgCode)+1000
       if pdgCode<0: idhnu+=1000
       l10ptot = ROOT.TMath.Min(ROOT.TMath.Max(ROOT.TMath.Log10(t.GetP()),-0.3),1.69999)
       l10pt   = ROOT.TMath.Min(ROOT.TMath.Max(ROOT.TMath.Log10(t.GetPt()),-2.),0.4999)
       key = idhnu
       h[key].Fill(t.GetP(),weight)
       key = idhnu+100
       h[key].Fill(l10ptot,l10pt,weight)
       key=idhnu+200
       h[key].Fill(l10ptot,l10pt,weight)

def run():
 tmp = "pythia8_Geant4_10.0_cXX.root"
 global weight 
 weight = weightMbias 
 for run in range(0,67000,1000):
   rc = processFile(tmp.replace('XX',str(run)))
 ut.writeHists(h,'pythia8_Geant4_10.0_c0-67000_nu.root')

def run1GeV():
 tmp = "pythia8_Geant4_1.0_cXX.root"
 global weight 
 weight = weightMbias1GeV
 for run in range(0,19000,1000):
   rc = processFile(tmp.replace('XX',str(run)))
 ut.writeHists(h,'pythia8_Geant4_1.0_c0-19000_nu.root')

def run4Charm():
 tmp = "pythia8_Geant4_charm_XX-YY_10.0.root"
 global weight
 weight = weightCharm
 for cycle in [0,1,2]:
  for run in range(0,100,20):
   crun = run+cycle*1000
   fname = tmp.replace('XX',str(crun)).replace('YY',str(crun+19))
   rc = processFile(fname,False)
 ut.writeHists(h,'pythia8_Geant4_charm_10.0_nu.root')

def run4Charm1GeV():
 fname = "pythia8_Geant4_charm_0-19_1.0.root" # renamed pythia8_Geant4_charm_XX-YY_10.0.root
 global weight
 weight = weightCharm1GeV
 rc = processFile(fname,False)
 ut.writeHists(h,'pythia8_Geant4_charm_1.0_nu.root')

def run4beauty():
 global weight
 weight = weightBeauty
 fname = "pythia8_Geant4_beauty_5336B_10.0.root"
 rc = processFile(fname,False)
 if rc == 0:
     fmu = fname.replace('.root',"_mu.root")
     rc = os.system("xrdcp "+fmu+" $EOSSHIP/eos/experiment/ship/data/Mbias/background-prod-2018/"+fmu)
     if rc != 0: 
      print("copy to EOS failed, stop",fmu)
     else:
      rc = os.system("rm "+fmu)
 
def finalResult():
 h10={}
 ut.readHists(h10,'pythia8_Geant4_10.0_c0-67000_nu.root')
 h1={}
 ut.readHists(h1,'pythia8_Geant4_1.0_c0-19000_nu.root')
 c10={}
 ut.readHists(c10,'pythia8_Geant4_charm_10.0_nu.root')
 c1={}
 ut.readHists(c1,'pythia8_Geant4_charm_1.0_nu.root')
 cmd = "hadd pythia8_Geant4_10.0_withCharm_nu.root pythia8_Geant4_10.0_c0-67000_nu.root pythia8_Geant4_charm_10.0_nu.root"
 os.system(cmd)
 cmd = "hadd pythia8_Geant4_1.0_withCharm_nu.root pythia8_Geant4_1.0_c0-19000_nu.root pythia8_Geant4_charm_1.0_nu.root"
 os.system(cmd)
