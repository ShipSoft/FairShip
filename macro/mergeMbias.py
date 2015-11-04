import ROOT,os,random
import shipunit as u
import rootUtils as ut
from array import array
pdg  = ROOT.TDatabasePDG()
mu   = pdg.GetParticle(13)
Mmu  = mu.Mass()
Mmu2 = Mmu * Mmu 
rnr  = ROOT.TRandom()

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
  ut.bookCanvas(h,key='P',title='momentum',nx=1600,ny=1200,cx=2,cy=2)
  ut.bookCanvas(h,key='>P',title='N >P',   nx=1600,ny=1200,cx=2,cy=2)
  cuts = {'mu':'abs(id)==13','nu':'abs(id)!=13','mu-':'id==13','mu+':'id==-13',
          'nutau':'id==16','nutaubar':'id==-16','numu':'id==14','numubar':'id==-14',
          'nue':'id==12','nuebar':'id==-12'}
  OpenCharm = {'':'','charm':"&(pythiaid==id & (abs(parentid) == 15 ||  abs(parentid) == 4112 || abs(parentid) == 4122  || abs(parentid) == 4132  \
                         ||  abs(parentid) == 431 || abs(parentid) == 421  || abs(parentid) == 411) )"}
  ROOT.gROOT.cd('')
  for x in ['','charm']:
   for q in cuts:
    p = q+x
    hn = 'Tp'+p
    ut.bookHist(h,hn, p +' ;p [GeV] ;N',400,0.0,400.0)
    h[hn].Sumw2()
    sTree.Draw('sqrt(px**2+py**2+pz**2)>>'+hn,'w*('+cuts[q]+OpenCharm[x]+')','goff')
    if q=='mu+': h[hn].SetLineColor(3) 
    if q=='mu-': h[hn].SetLineColor(4) 
# integrated rates
  for p in [ 'mu','mu-','mu+','nu','nue','nuebar','numu','numubar','nutau','nutaubar']:
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
      if tuples == '': tuples += l.GetName()
      else:            tuples += ":"+l.GetName()
    fxx = fnew.replace('.root',opt+'.root')
    h['N']      = ROOT.TFile(fxx, 'RECREATE')
    print 'new file created',fxx
    h['ntuple'] = ROOT.TNtuple("pythia8-Geant4","min bias flux after 3m hadron absorber "+opt,tuples)
  ROOT.gROOT.cd()
  t.SetEventList(0) 
  t.Draw(">>temp",cuts[opt]+"&"+noOpCharm)
  temp = ROOT.gROOT.FindObjectAny('temp')
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

def mergeWithCharm(splitOnly=False):
  # Ntup.Fill(par.id(),par.px(),par.py(),par.pz(),par.e(),par.m(),wspill,sTree.id,sTree.px,sTree.py,sTree.pz,sTree.E,sTree.M)
  # i.e. the par. is for the neutrino, and the sTree. is for its mother.
  # wspill is the weight for this file normalised/5e13.
 if not splitOnly:
  fcascade = ROOT.TFile("Decay-Cascade-parp16-MSTP82-1-MSEL4-ntuple_prod_18M.root")
  t = fcascade.Decay
  newFile = ROOT.TFile("pythia8_Charm.root", 'RECREATE')
  nt = ROOT.TNtuple("pythia8-Geant4","mu/nu flux from charm","id:px:py:pz:x:y:z:pythiaid:parentid:w:ecut")
  for n in range(t.GetEntries()):
      rc = t.GetEntry(n)
      ztarget = rnr.Exp(16*10.) - 50.*1000. # Mo/H20/W average interaction length, need to work with Pythia8 units, mm = 1 !
      rc = nt.Fill(t.id,t.px,t.py,t.pz,0.,0.,ztarget,t.id,t.mid,t.weight,0.)
  newFile.cd()
  nt.Write()
  newFile.Close()
  fcascade.Close()
  os.system("hadd -f pythia8_Geant4-withCharm.root pythia8_Geant4-noOpenCharm.root pythia8_Charm.root")
  print " progress: minbias and charm merged"
  f = ROOT.TFile("pythia8_Geant4-withCharm.root")
  t = f.FindObjectAny('pythia8-Geant4')
# put all events in memory, otherwise will take years to finish
  event = ROOT.std.vector("float")
  f = ROOT.TFile("pythia8_Geant4-withCharm.root")
  t = f.FindObjectAny('pythia8-Geant4')
  leaves = t.GetListOfLeaves()
  L = leaves.GetEntries()  
  m=0
  allEvents = []
  for n in range(t.GetEntries()):
   rc = t.GetEvent(n)
   if m%1000000==0 : print 'status ',m
   m+=1
   a = event()
   for l in range(L): a.push_back(leaves.At(l).GetValue())
   allEvents.append(a)
# distribute events randomly
  evList = []
  for n in range(len(allEvents)): evList.append(n)
  random.shuffle(evList)
  leaves = t.GetListOfLeaves()
  tuples = ''
  for l in leaves: 
    if tuples=='': tuples += l.GetName()
    else:          tuples += ":"+l.GetName()
  newFile     = ROOT.TFile("pythia8_Geant4-withCharm-ram.root", 'RECREATE')
  randomTuple = ROOT.TNtuple(t.GetName(),t.GetTitle(),tuples)
  m=0
  for n in evList:
   a = allEvents[n]
   if m%1000000==0 : print 'status ',m
   m+=1
   randomTuple.Fill(a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],a[8],a[9],a[10])
  newFile.cd()
  randomTuple.Write()
  newFile.Close()
  print " progress: order of events randomized"
 if 1>0:
# split in muons and neutrinos
  cuts = {'_onlyNeutrinos':'abs(id)==12||abs(id)==14||abs(id)==16','_onlyMuons':'abs(id)==13'}
  fName = "pythia8_Geant4-withCharm-ram.root"
  f = ROOT.TFile(fName)
  t = f.FindObjectAny("pythia8-Geant4")
  tuples = ''
# add histograms
  for idnu in [16,-16,14,-14,12,-12]:
   name = pdg.GetParticle(idnu).GetName()
   idhnu=1000+idnu
   if idnu < 0: idhnu=2000+abs(idnu)
   ut.bookHist(h,str(idhnu),name+' momentum (GeV)',400,0.,400.)
   ut.bookHist(h,str(idhnu+100),name+' log10-p vs log10-pt',100,-0.3,1.7,100,-2.,0.5)
   ut.bookHist(h,str(idhnu+200),name+' log10-p vs log10-pt',25,-0.3,1.7,100,-2.,0.5)
  leaves = t.GetListOfLeaves()
  for l in leaves: 
    if tuples == '': tuples += l.GetName()
    else:            tuples += ":"+l.GetName()
  for opt in cuts:
    fxx = fName.replace('-ram.root',opt+'.root')
    N   = ROOT.TFile(fxx, 'RECREATE')
    ntuple = ROOT.TNtuple("pythia8-Geant4",opt.replace("_only","")+" flux mbias and charm"+opt,tuples)
    ROOT.gROOT.cd()
    t.SetEventList(0) 
    t.Draw(">>temp",cuts[opt])
    temp = ROOT.gROOT.FindObjectAny('temp')
    t.SetEventList(temp) 
    for iev in range(temp.GetN()) :
     rc = t.GetEntry(temp.GetEntry(iev))
     ntuple.Fill(leaves.At(0).GetValue(),leaves.At(1).GetValue(),leaves.At(2).GetValue(),leaves.At(3).GetValue(),\
                     leaves.At(4).GetValue(),leaves.At(5).GetValue(),leaves.At(6).GetValue(),leaves.At(7).GetValue(),\
                     leaves.At(8).GetValue(),leaves.At(9).GetValue(),leaves.At(10).GetValue())
     if "Neutrinos" in opt: 
        pt2=t.px**2+t.py**2
        ptot=ROOT.TMath.Sqrt(pt2+t.pz**2)
        l10ptot=min(max(ROOT.TMath.log10(ptot),-0.3),1.69999)
        l10pt=min(max(ROOT.TMath.log10(ROOT.TMath.Sqrt(pt2)),-2.),0.4999)
        idnu = int(t.id)
        idhnu=1000+idnu
        if idnu < 0: idhnu=2000+abs(idnu)
        h[str(idhnu)].Fill(ptot,t.w)
        h[str(idhnu+100)].Fill(l10ptot,l10pt,t.w)
        h[str(idhnu+200)].Fill(l10ptot,l10pt,t.w)        
#     
    N.cd()
    ntuple.Write()
    if "Neutrinos" in opt: 
     for akey in h:
      cln = h[akey].Class().GetName()
      if not cln.find('TH')<0:   h[akey].Write()
     N.Close()
    print " progress: splitted "+opt
def test(fname):
 h['f'] = ROOT.TFile(fname)
 sTree = h['f'].FindObjectAny('pythia8-Geant4')
 TplotP(sTree)
def compare():
 test('$SHIPDATA/pythia8_Geant4_onlyMuons.root')
 for x in ['','_>E']:
  for ahist in ['pmu-','pmu+','pmu']:
   h['TP'+ahist+x]=h['T'+ahist+x].Clone('CT'+ahist+x)
 test('$SHIPDATA/pythia8_Geant4_onlyNeutrinos.root')
 for x in ['','_>E']:
  for ahist in ['pnumu','pnumubar','pnue','pnuebar']:
   h['TP'+ahist+x]=h['T'+ahist+x].Clone('CT'+ahist+x)
 test('pythia8_Geant4-withCharm.root')
 for x in ['','_>E']:
  t = 'P'
  if x != '' : t='>P' 
  h[t].cd(1)
  h['Tpmu'+x].Draw()
  h['TPpmu'+x].Draw('same')
  h['TPpmu'+x].SetLineColor(6)
  h['Tpmu'+x].SetLineColor(4)
  h['Lmu'+x] = ROOT.TLegend(0.32,0.62,0.71,0.85)
  h['Lmu'+x].AddEntry(h['Tpmu'+x],'muon new with charm, cascade, k-fac','PL')
  h['Lmu'+x].AddEntry(h['TPpmu'+x],'muon old CERN-Cracow prod','PL')
  h['Lmu'+x].Draw()
  h[t].cd(2)
  h['Tpnumu'+x].Draw()
  h['TPpnumu'+x].Draw('same')
  h['TPpnumu'+x].SetLineColor(6)
  h['Tpnumu'+x].SetLineColor(4)
  h['Lnu'+x] = ROOT.TLegend(0.32,0.62,0.71,0.85)
  h['Lnu'+x].AddEntry(h['Tpnumu'+x],'nu_mu new with charm, cascade, k-fac','PL')
  h['Lnu'+x].AddEntry(h['TPpnumu'+x],'nu_mu old CERN-Cracow prod','PL')
  h['Lnu'+x].Draw()
  t3 = h[t].cd(3)
  t3.SetLogy(1)
  h['Tpnuebar'+x].Draw()
  h['TPpnuebar'+x].Draw('same')
  h['TPpnuebar'+x].SetLineColor(6)
  h['Tpnuebar'+x].SetLineColor(4)
  h['Tpnue'+x].Draw('same')
  h['TPpnue'+x].Draw('same')
  h['TPpnue'+x].SetLineColor(5)
  h['Tpnue'+x].SetLineColor(3)
  h['Lnue'+x] = ROOT.TLegend(0.32,0.62,0.71,0.85)
  h['Lnue'+x].AddEntry(h['Tpnuebar'+x],'anti nu_e new with charm, cascade, k-fac','PL')
  h['Lnue'+x].AddEntry(h['TPpnuebar'+x],'anti nu_e old CERN-Cracow prod','PL')
  h['Lnue'+x].AddEntry(h['Tpnue'+x],'nu_e new with charm, cascade, k-fac','PL')
  h['Lnue'+x].AddEntry(h['TPpnue'+x],'nu_e old CERN-Cracow prod','PL')
  h['Lnue'+x].Draw() 
  t4 = h[t].cd(4)
  t4.SetLogy(1)
  h['Tpnumubar'+x].Draw()
  h['TPpnumubar'+x].Draw('same')
  h['TPpnumubar'+x].SetLineColor(6)
  h['Tpnumubar'+x].SetLineColor(4)
  h['Lnubar'+x] = ROOT.TLegend(0.32,0.62,0.71,0.85)
  h['Lnubar'+x].AddEntry(h['Tpnumubar'+x],'anti nu_mu new with charm, cascade, k-fac','PL')
  h['Lnubar'+x].AddEntry(h['TPpnumubar'+x],'anti nu_mu old CERN-Cracow prod','PL')
  h['Lnubar'+x].Draw() 
#
  h[t].Print('comparison'+x+'.png')
print "+ to start the full production: runProduction()"
print "+ merging with charm events:   mergeWithCharm()"
print "+ testing output: test('pythia8_Geant4-noOpenCharm.root')"

