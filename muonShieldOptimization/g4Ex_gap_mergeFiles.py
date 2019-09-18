from __future__ import print_function
# result_1Bn_ecut_5.root  		1E9 with Ecut > 5 GeV
# result_0.1Bn_ecut_0.5.root         	1E8 with Ecut > 0.5 GeV
Yandex   = False  # False
Yandex2   = False # summer 2015 production, 10B, Ecut>10GeV, Mo/W/ target
Yandex3   = True  # spring 2016 production, 10B, Ecut>10GeV, Mo/W/ target, record start of track
afterHadronAbsorber = False
JPsi     = False # True
MoTarget = False 
Tau      = False

import ROOT,os
from array import array
from ROOT import TDatabasePDG,TMath,gDirectory
from rootUtils import *
pdg  = TDatabasePDG()
mu   = pdg.GetParticle(13)
Mmu  = mu.Mass()
Mmu2 = Mmu * Mmu 

if Yandex:
 stats =  {5.:[1E9,1E9],0.5:[1E8]}
 files  = {5.:['$SHIPSOFT/data/result_1Bn_ecut_5.root','$SHIPSOFT/data/result_1Bn_ecut_5-v02.root'],0.5:['$SHIPSOFT/data/result_0.1Bn_ecut_0.5.root']}
 fnew  = 'pythia8_Geant4_total_Yandex.root'
if Yandex2:
 stats =  {10.:[1E10]}
 files  = {10.:['$SHIPSOFT/data/result_10Bn_ecut_10.root']}
 fnew  = 'pythia8_Geant4_total_Yandex2.root'
if Yandex3:
 stats =  {10.:[10.05E9]}
 files  = {10.:['/media/truf/Elements/Data/HNL/ShipSoft/data/Yandex-April2016_10.05B.root']}
 fnew  = 'pythia8_Geant4_total_Yandex3.root'
if JPsi:
 BR = 0.05961 
 stats =  {10.:[]}
 files  = {10.:[]}
 jobs = {'b6276c506a_g4Ex_gap_':['53','54','55','56'],'b602f257b0_g4Ex_gap_':['52']}
 nevts = 0
 ntot  = 0
 tag   = '#events='
 for job in jobs:
  for run in jobs[job]:
   for i in range(10):
    path = job+run+str(i)+'/'
    fl = open(path+'log'+run+str(i))
    for l in fl.readlines():
     k = l.find(tag)
     if k<0: continue
     nevts = int( l[k+len(tag):].replace(')',''))
    fl.close()
    files[10.].append(path+'pythia8_Geant4_'+run+str(i)+'_10.0.root')
    stats[10.].append(nevts/BR)
    ntot += nevts/BR
    print(run+str(i),' --> nevts = ',nevts)
 fnew  = 'pythia8_Geant4_total_Jpsi.root'
 print('total statistics ',ntot/1.E9,' *1E9')
#
if Tau:
 BR = 0.0554
 stats =  {0.:[]}
 files  = {0.:[]}
 jobs = {'b63edb1b12_g4Ex_gap_':['13']}
 nevts = 0
 ntot  = 0
 tag   = '#events='
 for job in jobs:
  for run in jobs[job]:
   for i in range(10):
    path = job+run+str(i)+'/'
    if not 'log'+run+str(i) in os.listdir(path): continue
    fl = open(path+'log'+run+str(i))
    for l in fl.readlines():
     k = l.find(tag)
     if k<0: continue
     nevts = int( l[k+len(tag):].replace(')',''))
    fl.close()
    files[0.].append(path+'pythia8_Geant4_'+run+str(i)+'_0.0.root')
    stats[0.].append(nevts/BR)
    ntot += nevts/BR
    print(run+str(i),' --> nevts = ',nevts)
 fnew  = 'pythia8_Geant4_total_tauOnly_MoTarget_E0.root'
 print('total statistics ',ntot/1.E9,' *1E9')
#
if MoTarget:
 stats =  {}
 files  = {}
 jobs = {'b64a4b817c.cern.ch_g4Ex_gap_':['60','61','62','65','66'],'b63edb1b12_g4Ex_gap_':['63','75','77','78','81','83','85','87','90','93','95'],\
         'b65dfad864_g4Ex_gap_':['70'],'b6276c506a_g4Ex_gap_':['71'],'b6e72959f6_g4Ex_gap_':['72'],\
         'b6429e4f38.cern.ch_g4Ex_gap_':['73','74','76','79','80','82','84','86','88','89','91','94','96']          }
 nevts = 0
 ntot  = 0
 tag   = '#events='
 for job in jobs:
  for run in jobs[job]:
   for i in range(10):
    path = job+run+str(i)+'/'
    fl = open(path+'log'+run+str(i))
    nevts = 0
    for l in fl.readlines():
     k = l.find(tag)
     if k<0: continue
     nevts = int( l[k+len(tag):].replace(')',''))
    fl.close()
    if nevts==0: continue
    for r in os.listdir(path):
      if r.find('.root')<0: continue
      ecut = float(r.split('.root')[0].split('_')[3])
      if ecut not in stats:
       stats[ecut] = []
       files[ecut] = []      
    files[ecut].append(path+r)
    stats[ecut].append(nevts)
    ntot += nevts
    print(run+str(i),' --> nevts = ',nevts)
 fnew  = 'pythia8_Geant4_total_MoTarget.root'
 print('total statistics ',ntot/1.E9,' *1E9')

ntot = {}
for ecut in stats:
 ntot[ecut] = 0 
 for s in stats[ecut]: ntot[ecut]+=s
print(ntot)

h={}
def makeFinalNtuples(norm=5.E13,opt=''):
  cuts = {'':'','_onlyMuons':'abs(id)==13','_onlyNeutrinos':'abs(id)==12||abs(id)==14||abs(id)==16'}
  first = True
  tuples = ''
  fn     = 1
  for ecut in stats:
   for i in range(len(stats[ecut])):
    h[fn] = ROOT.TFile(files[ecut][i])
    t = h[fn].FindObjectAny("pythia8-Geant4")
    fn+=1 
    if first: 
     first = False
     for l in t.GetListOfLeaves(): tuples += l.GetName()+':'
     tuples+='w:ecut'
     fxx = fnew.replace('.root',opt+'.root')
     if opt!='': fxx = fxx.replace('_total','')
     h['N']      = ROOT.TFile(fxx, 'RECREATE')
     print('new file created',fxx)
     if afterHadronAbsorber:  
      h['ntuple'] = ROOT.TNtuple("pythia8-Geant4","flux after 3m hadron absorber",tuples)
     else:  
      h['ntuple'] = ROOT.TNtuple("pythia8-Geant4","flux after 3m hadron absorber, position&momentum before",tuples)
    gROOT.cd()
    t.SetEventList(0) 
    t.Draw(">>temp",cuts[opt])
    temp = gROOT.FindObjectAny('temp')
    t.SetEventList(temp) 
    nev    = temp.GetN()
    for iev in range(nev) :
     rc = t.GetEntry(temp.GetEntry(iev))
     leaves = t.GetListOfLeaves()
     vlist = array('f')
     for x in range(leaves.GetEntries()):
      vlist.append( leaves.At(x).GetValue() )
     # get kinetic energy "id:px:py:pz:x:y:z:ox:oy:oz:pythiaid:parentid"
     # since 2016         "id:px:py:pz:x:y:z:opx:opy:opz:ox:oy:oz:pythiaid:parentid"
     Psq = vlist[1]**2+vlist[2]**2+vlist[3]**2
     if abs(vlist[0])==13: Ekin = ROOT.TMath.Sqrt(Mmu2+Psq)-Mmu  
     else: Ekin = ROOT.TMath.Sqrt(Psq)
     if Yandex:
      if Ekin < ecut : continue
      if Ekin > 5. :     weight = norm/(ntot[5.] + ntot[0.5])
      else         :     weight = norm/(ntot[0.5])
     if Yandex2 or Yandex3:
      if Ekin < ecut : continue
      weight = norm/(ntot[10.])
     if JPsi       :     weight = norm/(ntot[10.])
     if Tau        :     weight = norm/(ntot[0.])
     if MoTarget:
      if Ekin < ecut : continue
      if Ekin > 50.   :     weight = norm/(ntot[0.5] + ntot[10.] + ntot[20.]+ ntot[50.])
      elif Ekin > 20.   :   weight = norm/(ntot[0.5] + ntot[10.] + ntot[20.])
      elif Ekin > 10. :     weight = norm/(ntot[0.5] + ntot[10.])
      else            :     weight = norm/(ntot[0.5])
     vlist.append(weight)
     vlist.append( float(ecut) )
     h['ntuple'].Fill(vlist)
  h['N'].cd()
  h['ntuple'].Write()

def interactionRegion():
 import rootUtils as ut
 import shipunit as u
 f = ROOT.TFile('pythia8_Geant4_13_350.0.root')
 sTree=f.FindObjectAny('pythia8-Geant4')
 ut.bookHist(h,'originz','z',100,-50.5,-49.)
 ut.bookHist(h,'originzr','r vs z',100,-50.5,-49.,100,0.,0.5)
 ut.bookHist(h,'originxy','x vs y',100,-0.5,0.5,100,-0.5,0.5)
 ROOT.gROOT.cd()
 sTree.Draw('z>>originz') 
 sTree.Draw('1000*sqrt(x*x+y*y):z>>originzr') 
 sTree.Draw('1000*x:1000*y>>originxy') 


makeFinalNtuples(norm=5.E13,opt='')
makeFinalNtuples(norm=5.E13,opt='_onlyMuons')
makeFinalNtuples(norm=5.E13,opt='_onlyNeutrinos')
