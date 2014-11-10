# result_1Bn_ecut_5.root  		1E9 with Ecut > 5 GeV
# result_0.1Bn_ecut_0.5.root         	1E8 with Ecut > 0.5 GeV

import ROOT,os
from ROOT import TDatabasePDG,TMath,gDirectory
from rootUtils import *
pdg  = TDatabasePDG()
mu   = pdg.GetParticle(13)
Mmu  = mu.Mass()
Mmu2 = Mmu * Mmu 


stats = {5.:1E9,0.5:1E8}
files  = {5.:'result_1Bn_ecut_5.root',0.5:'result_0.1Bn_ecut_0.5.root'}

fnew  = 'pythia8_Geant4_total_Yandex.root'

h={}
def makeFinalNtuples(norm=5.E13,opt=''):
  cuts = {'':'','_onlyMuons':'abs(id)==13','_onlyNeutrinos':'abs(id)==12||abs(id)==14||abs(id)==16'}
  first = True
  tuples = ''
  fn     = 1
  for ecut in stats:
    h[fn] = ROOT.TFile(files[ecut])
    t = h[fn].FindObjectAny("pythia8-Geant4")
    fn+=1 
    if first: 
     first = False
     for l in t.GetListOfLeaves(): tuples += l.GetName()+':'
     tuples+='w:ecut'
     fxx = fnew.replace('.root',opt+'.root')
     if opt!='': fxx = fxx.replace('_total','')
     h['N']      = ROOT.TFile(fxx, 'RECREATE')
     print 'new file created',fxx
     h['ntuple'] = ROOT.TNtuple("pythia8-Geant4","flux after 3m hadron absorber",tuples)
    gROOT.cd()
    t.SetEventList(0) 
    t.Draw(">>temp",cuts[opt])
    temp = gROOT.FindObjectAny('temp')
    t.SetEventList(temp) 
    nev    = temp.GetN()
    for iev in range(nev) :
     rc = t.GetEntry(temp.GetEntry(iev))
     leaves = t.GetListOfLeaves()
     vlist = []
     for x in range(leaves.GetEntries()):
      vlist.append( leaves.At(x).GetValue() )
     weight = norm/stats[ecut]
     vlist.append(weight)
     vlist.append( float(ecut) )
     # print vlist
     h['ntuple'].Fill(vlist[0],vlist[1],vlist[2],vlist[3],vlist[4],vlist[5],vlist[6],
                     vlist[7],vlist[8],vlist[9],vlist[10],vlist[11],vlist[12],vlist[13])
  h['N'].cd()
  h['ntuple'].Write()

makeFinalNtuples(norm=5.E13,opt='')
makeFinalNtuples(norm=5.E13,opt='_onlyMuons')
makeFinalNtuples(norm=5.E13,opt='_onlyNeutrinos')
