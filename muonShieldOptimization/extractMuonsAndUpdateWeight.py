import os,ROOT
import rootUtils as ut
path =  '/eos/experiment/ship/data/Mbias/background-prod-2018/'

# functions, should extract events with muons, update weight based on process/decay and PoT

muSources = {'eta':221,'omega':223,'phi':333,'rho0':113,'eta_prime':331}
charmExtern = [4332,4232,4132,4232,4122,431,411,421]

muSourcesIDs = muSources.values()

# for 10GeV Yandex Production 65.041 Billion PoT, weight 768.75 for 5E13 pot
weight = 768.75 

def muonUpdateWeight(sTree,diMuboost,xSecboost):
 nMu=0
 for v in sTree.vetoPoint:
   v = sTree.vetoPoint[0]
   mu = v.GetTrackID()
   t = sTree.MCTrack[mu]
   if abs(t.GetPdgCode())!=13: continue
   moID  = abs(sTree.MCTrack[t.GetMotherId()].GetPdgCode())
   if moID in charmExtern: continue  # take heavy flavours from separate production
   nMu+=1
   pName = t.GetProcName().Data()
   t.MultiplyWeight(weight)
   if not pName.find('Hadronic inelastic')<0:
     t.MultiplyWeight(1./diMuboost)
   elif not pName.find('Lepton pair')<0:
     t.MultiplyWeight(1./xSecboost)
   elif not pName.find('Positron annihilation')<0:
     t.MultiplyWeight(1./xSecboost)
   elif not pName.find('Primary particle')<0 or not pName.find('Decay')<0:
     if moID in muSourcesIDs:
       t.MultiplyWeight(1./diMuboost)
 return nMu

def PoT(f):
 nTot = 0
 # POT = 1000000000 with ecut=10.0 diMu100.0 X100.0
 diMuboost = 0.
 xSecboost = 0.
 ncycles = 0
 for k in f.GetListOfKeys():
  if k.GetName() == 'FileHeader':
   txt = k.GetTitle()
   tmp = txt.split('=')[1]
   nTot += int(tmp.split('with')[0])
   ncycles+=1
   i = txt.find('diMu')
   if i < 0:
     diMuboost+=1.
   else:
     diMuboost+=float(txt[i+4:].split(' ')[0])
   i = txt.find('X')
   if i < 0:
     xSecboost+=1.
   else:
     xSecboost+=float(txt[i+1:].split(' ')[0])
 diMuboost=diMuboost/float(ncycles) 
 xSecboost=xSecboost/float(ncycles) 
 print "POT = ",nTot," number of events:",f.cbmsim.GetEntries(),' diMuboost=',diMuboost,' XsecBoost=',xSecboost
 return nTot,diMuboost,xSecboost

def TotStat():
 lfiles = os.listdir(path)
 ntot = 0
 for fn in lfiles: 
  f=ROOT.TFile(path+fn)
  nPot,diMuboost,xSecboost = PoT(f)
  ntot += nPot
 print "Total statistics so far",ntot/1.E9," billion" 

def processFile(fin):
    f   = ROOT.TFile.Open(os.environ['EOSSHIP']+path+fin)
    nPot,diMuboost,xSecboost  = PoT(f)
    sTree = f.cbmsim
    outFile = fin.replace(".root","_mu.root")
    fmu = ROOT.TFile(outFile,"recreate")
    newTree = sTree.CloneTree(0)
    for n in range(sTree.GetEntries()):
      sTree.GetEntry(n)
      nMu = muonUpdateWeight(sTree,diMuboost,xSecboost)
      if nMu>0:
       rc = newTree.Fill()
    ff = f.FileHeader.Clone('Extracted Muon Background File')
    txt = ff.GetTitle()
    tmp = txt.split('=')[1]
    newTxt = txt.replace(tmp.split('with')[0].replace(' ',''),str(nPot))
    ff.SetTitle(newTxt)
    fmu.cd()
    ff.Write("FileHeader", ROOT.TObject.kSingleKey)
    newTree.AutoSave()
    fmu.Close()
    return 0

def run():
 tmp = "pythia8_Geant4_10.0_cXX.root"
 for run in range(0,67000,1000):
   rc = processFile(tmp.replace('XX',str(run)))
   if rc == 0:
     fmu = tmp.replace('XX',str(run)+"_mu")
     rc = os.system("xrdcp "+fmu+" $EOSSHIP/eos/experiment/ship/data/Mbias/background-prod-2018/"+fmu)
     if rc != 0: 
      print "copy to EOS failed, stop",fmu
     else:
      rc = os.system("rm "+fmu)


def run4Charm():
 tmp = "pythia8_Geant4_charm_XX-YY_10.0.root"
 for cycle in [0,1]:
  for run in range(0,100,20):
   crun = run+cyle*1000
   fname = tmp.replace('XX',str(crun)).replace('YY',str(crun+19))
   rc = processFile(fname)
   if rc == 0:
     fmu = fname.replace('.root',"_mu.root")
     rc = os.system("xrdcp "+fmu+" $EOSSHIP/eos/experiment/ship/data/Mbias/background-prod-2018/"+fmu)
     if rc != 0: 
      print "copy to EOS failed, stop",fmu
     else:
      rc = os.system("rm "+fmu)

