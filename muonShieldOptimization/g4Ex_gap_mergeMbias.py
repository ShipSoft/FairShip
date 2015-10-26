import ROOT,os
from rootUtils import *
pdg  = ROOT.TDatabasePDG()
mu   = pdg.GetParticle(13)
Mmu  = mu.Mass()
Mmu2 = Mmu * Mmu 

eospath = "root://eoslhcb//eos/ship/data/"

def fillPart(t):
 particles = {}
 for n in range(t.GetEntries()):
    rc = t.GetEvent(n)
    if not particles.has_key(t.parentid) : 
         particles[t.parentid] = 0
    particles[t.parentid] +=1
 return particles
#
def fillWeights():
 weights = {}
 for p in productions:
  f = ROOT.TFile.Open(eospath+productions[p]["file"])
  t = f.FindObjectAny("pythia8-Geant4")
  weights[p]={}
  for n in range(t.GetEntries()):
    rc = t.GetEvent(n)
    if not weights[p].has_key(t.w) : 
         weights[p][t.w] = [t.ecut,0]
    weights[p][t.w][1] +=1
    if t.ecut > weights[p][t.w][0] : weights[p][t.w][0] = t.ecut
 return weights

def TplotP(sTree):
  bookCanvas(h,key='P',title='momentum',nx=700,ny=400,cx=2,cy=2)
  bookCanvas(h,key='>P',title='N >P',   nx=700,ny=400,cx=2,cy=2)
  cuts = {'mu':'abs(id)==13','nu':'abs(id)!=13','mu-':'id==13','mu+':'id==-13',
          'nutau':'id==16','nutaubar':'id==-16','numu':'id==14','numubar':'id==-14',
          'nue':'id==12','nuebar':'id==-12'}
  gROOT.cd('')
  for p in cuts:
    hn = 'Tp'+p
    bookHist(h,hn, p +' ;p [GeV] ;N',400,0.0,400.0)
    h[hn].Sumw2()
    sTree.Draw('sqrt(px**2+py**2+pz**2)>>'+hn,'w*('+cuts[p]+')','goff')
    if p=='mu+': h[hn].SetLineColor(3) 
    if p=='mu-': h[hn].SetLineColor(4) 
# integrated rates
  for p in [ 'mu','mu-','mu+','nu','nue','numu','numubar','nutau','nutaubar']:
    hi =  'Tp'+p+'_>E'
    h[hi]=h['Tp'+p].Clone(hi)
    h[hi].Reset()
    nsum = 0 
    for i in range(h[hi].GetNbinsX()+1,1,-1):
     nsum+=h['Tp'+p].GetBinContent(i)
     h[hi].SetBinContent(i,nsum) 
  k = 1
  for p in [ 'mu','nu']:
   cv = h['P'].cd(k)
   cv.SetLogy(1)
   h['Tp'+p].Draw()
   if h['Tp'+p].GetEntries()<1: continue
   if p=='mu': 
     h['Tpmu+'].Draw('same')
     h['Tpmu-'].Draw('same')
   cv = h['>P'].cd(k)
   cv.SetLogy(1)
   h[hi].Draw()
   k+=1
# plot different nu species:
  k = 3
  cv = h['P'].cd(k)
  cv.SetLogy(1)
  first = True
  i = 2
  h['tlnu'+str(k)] = ROOT.TLegend(0.49,0.13,0.88,0.36)
  for p in ['numu','numubar','nue','nuebar','nutau','nutaubar']:
    hn = 'Tp'+p 
    h['tlnu'+str(k)].AddEntry(h['Tp'+p],p,'PL')
    h[hn].SetLineColor(i)
    h[hn+'8']=h[hn].Clone()
    h[hn+'8'].SetName(hn+'8')
    h[hn+'8'].Rebin(8)
    i+=1
    if first:
      h[hn+'8'].Draw() 
      first = False
    h[hn+'8'].Draw('same')  
  h['tlnu'+str(k)].Draw()
  k+=1
#

productions = {}
productions["CERN-Cracow"] = {"stats":{1.:[1.1E8],10.:[1.22E9],100:[1.27E10]},
                               "file":"pythia8_Geant4_total.root" }
productions["Yandex"]      = {"stats":{5.:[2.1E9,1E9],0.5:[1E8]},
                               "file":"pythia8_Geant4_total_Yandex.root" }
productions["Yandex2"]     = {"stats":{10.:[1E10]},
                               "file":"pythia8_Geant4_total_Yandex2.root" }
fnew = "pythia8_Geant4-noOpenCharm.root"

h={}

def mergeMinBias(pot,norm=5.E13,opt=''):
 noOpCharm = "!(pythiaid==id & (abs(parentid) == 15 ||  abs(parentid) == 4112 || abs(parentid) == 4122  || abs(parentid) == 4132  \
                         ||  abs(parentid) == 431 || abs(parentid) == 421  || abs(parentid) == 411) )"
 cuts = {'':'abs(id)>0','_onlyMuons':'abs(id)==13','_onlyNeutrinos':'abs(id)==12||abs(id)==14||abs(id)==16'}
 first = True
 for p in productions:
  f = ROOT.TFile.Open(eospath+productions[p]["file"])
  t = f.FindObjectAny("pythia8-Geant4")
  if first:
    tuples = ''
    for l in t.GetListOfLeaves(): 
      if first:
       first = False
       tuples += l.GetName()
      else: tuples += ":"+l.GetName()
    fxx = fnew.replace('.root',opt+'.root')
    h['N']      = ROOT.TFile(fxx, 'RECREATE')
    print 'new file created',fxx
    h['ntuple'] = ROOT.TNtuple("pythia8-Geant4","min bias flux after 3m hadron absorber "+opt,tuples)
  gROOT.cd()
  t.SetEventList(0) 
  t.Draw(">>temp",cuts[opt]+"&"+noOpCharm)
  temp = gROOT.FindObjectAny('temp')
  t.SetEventList(temp) 
  nev = temp.GetN()
  for iev in range(nev) :
     rc = t.GetEntry(temp.GetEntry(iev))
     leaves = t.GetListOfLeaves()
     vlist = []
     for x in range(leaves.GetEntries()):
      vlist.append( leaves.At(x).GetValue() )
     # "id:px:py:pz:x:y:z:pythiaid:parentid:w:ecut"
     Psq = vlist[1]**2+vlist[2]**2+vlist[3]**2
     if abs(vlist[0])==13: Ekin = ROOT.TMath.Sqrt(Mmu2+Psq)-Mmu  
     else: Ekin = ROOT.TMath.Sqrt(Psq)
     # re calculate weights
     # pot = 5E13/w
     # E > 100 GeV:              add all pots -> w = 5E13/pot
     #   w = norm/( pot["CERN-Cracow"][100.] + productions["Yandex"][5.] + productions["Yandex2"][10.] )
     # E < 100 & E > 10 GeV 
     #   w = norm/( pot["CERN-Cracow"][10.] + productions["Yandex"][5.] + productions["Yandex2"][10.] )
     # E < 10 & E > 5 GeV 
     #   w = norm/( pot["CERN-Cracow"][1.] + productions["Yandex"][5.]  )
     # E < 5 GeV & E >   1 GeV 
     #   w = norm/( pot["CERN-Cracow"][1.] + productions["Yandex"][0.5]  )
     # E < 1 GeV & E > 0.5 GeV 
     #   w = norm/( productions["Yandex"][0.5]  )
     if Ekin > 100. :
       vlist[9] = norm/( pot["CERN-Cracow"][100.] + pot["Yandex"][5.] + pot["Yandex2"][10.] )
     elif Ekin > 10.   :  
       vlist[9] = norm/( pot["CERN-Cracow"][10.] + pot["Yandex"][5.] + pot["Yandex2"][10.] )
     elif Ekin > 5.   :  
       vlist[9] = norm/( pot["CERN-Cracow"][1.] + pot["Yandex"][5.]  )
     elif Ekin > 1.   :  
       vlist[9] = norm/( pot["CERN-Cracow"][1.] + pot["Yandex"][0.5]  )
     elif Ekin > 0.5  :  
       vlist[9] = norm/( pot["Yandex"][0.5]  )
     else   :  
       print "this should not happen, except some rounding errors",p,Ekin,vlist[9]
     h['ntuple'].Fill(vlist[0],vlist[1],vlist[2],vlist[3],vlist[4],vlist[5],vlist[6],
                     vlist[7],vlist[8],vlist[9],vlist[10])
  h['N'].cd()
  h['ntuple'].Write()

def runProduction():
 we = fillWeights()
 pot = {}
 norm = 5.E13
 for p in we:
  pot[p]={}
  for w in we[p]:
    pot[p][we[p][w][0]] = 5.E13/w
 print "pots:",pot
 #
 mergeMinBias(pot,norm=5.E13,opt='')
 mergeMinBias(pot,norm=5.E13,opt='_onlyMuons')
 mergeMinBias(pot,norm=5.E13,opt='_onlyNeutrinos')

print "to start the full production: runProduction()"
print "testing output: "
print " f = ROOT.TFile('pythia8_Geant4-noOpenCharm.root')"
print " sTree = f.FindObjectAny('pythia8-Geant4')"
print " TplotP(sTree)"
