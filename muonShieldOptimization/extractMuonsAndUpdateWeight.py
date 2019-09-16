from __future__ import print_function
import os,ROOT
import rootUtils as ut
path =  '/eos/experiment/ship/data/Mbias/background-prod-2018/'

# functions, should extract events with muons, update weight based on process/decay and PoT

muSources = {'eta':221,'omega':223,'phi':333,'rho0':113,'eta_prime':331}
charmExtern = [4332,4232,4132,4232,4122,431,411,421]

# for 10GeV Yandex Production 65.041 Billion PoT, weight = 768.75 for 5E13 pot
weightMbias = 768.75

# for 10GeV charm Production 102.2 Billion PoT equivalent, weight = 489.24
# added another cycle
weightCharm = 489.24 * 2./3. 

# for 10GeV charm Production 5336 Billion PoT equivalent, weight = 9.37
weightBeauty = 9.37

def muonUpdateWeight(sTree,diMuboost,xSecboost,noCharm=True):
 nMu=0
 for v in sTree.vetoPoint:
   mu = v.GetTrackID()
   t = sTree.MCTrack[mu]
   if abs(t.GetPdgCode())!=13: continue
   moID  = abs(sTree.MCTrack[t.GetMotherId()].GetPdgCode())
   if moID in charmExtern and noCharm: continue  # take heavy flavours from separate production
   nMu+=1
   pName = t.GetProcName().Data()
   t.SetWeight(weight)
   if not pName.find('Hadronic inelastic')<0:
     t.MultiplyWeight(1./diMuboost)
   elif not pName.find('Lepton pair')<0:
     t.MultiplyWeight(1./xSecboost)
   elif not pName.find('Positron annihilation')<0:
     t.MultiplyWeight(1./xSecboost)
   elif not pName.find('Primary particle')<0 or not pName.find('Decay')<0:
     if moID in muSources.values():
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
   tmp2 = tmp.split('with')[0]
   if tmp2.find('E')<0: nTot += int(tmp2)
   else: nTot += float(tmp2)
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
 print("POT = ",nTot," number of events:",f.cbmsim.GetEntries(),' diMuboost=',diMuboost,' XsecBoost=',xSecboost)
 return nTot,diMuboost,xSecboost

def TotStat():
 lfiles = os.listdir(path)
 ntot = 0
 for fn in lfiles: 
  f=ROOT.TFile(path+fn)
  nPot,diMuboost,xSecboost = PoT(f)
  ntot += nPot
 print("Total statistics so far",ntot/1.E9," billion") 

def processFile(fin,noCharm=True):
    f   = ROOT.TFile.Open(os.environ['EOSSHIP']+path+fin)
    nPot,diMuboost,xSecboost  = PoT(f)
    sTree = f.cbmsim
    outFile = fin.replace(".root","_mu.root")
    fmu = ROOT.TFile(outFile,"recreate")
    newTree = sTree.CloneTree(0)
    for n in range(sTree.GetEntries()):
      sTree.GetEntry(n)
      nMu = muonUpdateWeight(sTree,diMuboost,xSecboost,noCharm)
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
 global weight 
 weight = weightMbias 
 for run in range(0,67000,1000):
   rc = processFile(tmp.replace('XX',str(run)))
   if rc == 0:
     fmu = tmp.replace('XX',str(run)+"_mu")
     rc = os.system("xrdcp "+fmu+" $EOSSHIP/eos/experiment/ship/data/Mbias/background-prod-2018/"+fmu)
     if rc != 0: 
      print("copy to EOS failed, stop",fmu)
     else:
      rc = os.system("rm "+fmu)


def run4Charm():
 tmp = "pythia8_Geant4_charm_XX-YY_10.0.root"
 global weight
 weight = weightCharm
 for cycle in [0,1,2]:
  for run in range(0,100,20):
   crun = run+cycle*1000
   fname = tmp.replace('XX',str(crun)).replace('YY',str(crun+19))
   rc = processFile(fname,False)
   if rc == 0:
     fmu = fname.replace('.root',"_mu.root")
     rc = os.system("xrdcp "+fmu+" $EOSSHIP/eos/experiment/ship/data/Mbias/background-prod-2018/"+fmu)
     if rc != 0: 
      print("copy to EOS failed, stop",fmu)
     else:
      rc = os.system("rm "+fmu)

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

# merge with beauty in a second step


# finished one file pythia8_Geant4_10.0_withCharm44000_mu.root 2712798 1113638

def mergeCharm():
 tmp = "pythia8_Geant4_charm_XX-YY_10.0.root"
 mergedFile = "pythia8_Geant4_charm_102.2B_10.0_mu.root"
 cmd = "hadd "+mergedFile
 for cycle in [0,1]:
  for run in range(0,100,20):
   crun = run+cycle*1000
   fname = tmp.replace('XX',str(crun)).replace('YY',str(crun+19))
   fmu = " $EOSSHIP/eos/experiment/ship/data/Mbias/background-prod-2018/"+fname.replace('.root',"_mu.root")
   cmd += fmu
 rc = os.system(cmd)
 rc = os.system("xrdcp "+mergedFile+" $EOSSHIP/eos/experiment/ship/data/Mbias/background-prod-2018/"+mergedFile)

def mergeMbiasAndCharm(flavour="charm"):
 done = []
 timer = ROOT.TStopwatch()
 timer.Start()
 pp = os.environ['EOSSHIP']+path
 Rndm=ROOT.TRandom3()
 Rndm.SetSeed(0)
 if flavour=="charm": 
   allFiles = {'charm':"pythia8_Geant4_charm_102.2B_10.0_mu.root"}
   tmp = "pythia8_Geant4_10.0_cXX_mu.root"
 else:                
   allFiles = {'beauty':"pythia8_Geant4_beauty_5336B_10.0_mu.root"}
   tmp = "pythia8_Geant4_10.0_withCharmXX_mu.root"
 for run in range(0,67000,1000):
    allFiles[str(run)] = tmp.replace('XX',str(run))
 nEntries = {}
 Nall = 0
 for x in allFiles:
  f=ROOT.TFile.Open(pp+allFiles[x])
  nEntries[x]=f.cbmsim.GetEntries()
  Nall += nEntries[x]
 nCharm = 0
 nDone  = 0
 frac = nEntries[flavour]/float(Nall)
 print("debug",frac)
 os.system('xrdcp '+pp +allFiles[flavour] +' '+allFiles[flavour])
 for k in allFiles:
  if k==flavour: continue
  if k in done:  continue
  os.system('xrdcp '+pp +allFiles[k] +' ' +allFiles[k])
  os.system('hadd -f tmp.root '+ allFiles[flavour] + ' '+ allFiles[k] )
  os.system('rm '+allFiles[k])
  f = ROOT.TFile('tmp.root')
  sTree = f.cbmsim
  sTree.LoadBaskets(30000000000)
  if flavour=="charm": 
   outFile = tmp.replace('cXX','withCharm'+k)
  else:
   outFile = tmp.replace('XX','andBeauty'+k)
  fmu = ROOT.TFile(outFile,"recreate")
  newTree = sTree.CloneTree(0)
  nMbias = 0
 # 0 - nEntries['charm']-1 , nEntries['charm'] - nEntries[0]-1, nEntries[0] - nEntries[1000]-1
  # randomList = ROOT.TEntryList(chain)
  myList = []
  while nMbias<nEntries[k]:
   copyEvent = True
   if Rndm.Rndm() > frac:
    # rc = randomList.Enter(nMbias+nEntries['charm'])
    myList.append( nMbias+nEntries[flavour] )
    nMbias+=1
   else:
    if nEntries[flavour]>nCharm:
     # rc = randomList.Enter(nCharm)
     myList.append( nCharm )
     nCharm+=1
    else: copyEvent = False
  # chain.SetEntryList(randomList) 
  # nev = randomList.GetN()
  nev = len(myList)
  print("start:",outFile,nev)
  for iev in range(nev) :
     rc =sTree.GetEntry(myList[iev])
     rc = newTree.Fill()
     if (iev)%100000==0:
       timer.Stop()
       print("status:",timer.RealTime(),k,iev)
       timer.Start()
  newTree.AutoSave()
  print("finished one file",outFile,nMbias,nCharm)
  if flavour=="charm": 
   ff = f.FileHeader.Clone('With Charm Merged Muon Background File')
  else: 
   ff = f.FileHeader.Clone('With Charm and Beauty Merged Muon Background File')
  txt = ff.GetTitle()
  fmu.cd()
  ff.Write("FileHeader", ROOT.TObject.kSingleKey)
  fmu.Close()
  f.Close()
  rc = os.system("xrdcp "+outFile+" $EOSSHIP/eos/experiment/ship/data/Mbias/background-prod-2018/"+outFile)
  if rc != 0: 
      print("copy to EOS failed",outFile)
  else:
      rc = os.system("rm "+outFile)

def testRatio(fname):
 f=ROOT.TFile.Open(os.environ['EOSSHIP']+path+fname)
 sTree = f.cbmsim
 Nall = sTree.GetEntries()
 charm = 0
 for n in range(Nall):
   rc = sTree.GetEvent(n)
   for m in sTree.MCTrack:
    pdgID = abs(m.GetPdgCode())
    if pdgID in charmExtern:
        charm+=1
        break
 print("charm found",charm," ratio ",charm/float(Nall))
 




