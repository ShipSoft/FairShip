from __future__ import print_function
from __future__ import division
import ROOT,os,random
import shipunit as u
import rootUtils as ut
from ShipGeoConfig import ConfigRegistry

from array import array
pdg  = ROOT.TDatabasePDG()
mu   = pdg.GetParticle(13)
Mmu  = mu.Mass()
Mmu2 = Mmu * Mmu 
rnr  = ROOT.TRandom()
eospath = ROOT.gSystem.Getenv("EOSSHIP")+"/eos/experiment/ship/data/"
ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = 10.)
endOfHadronAbsorber = (ship_geo['hadronAbsorber'].z + ship_geo['hadronAbsorber'].length/2.) /100.
startOfTarget       = -50. # value used for Geant4 production

def fillPart(t):
 particles = {}
 for n in range(t.GetEntries()):
    rc = t.GetEvent(n)
    if t.parentid not in particles : 
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
    if t.w not in weights[p] : 
         weights[p][t.w] = [t.ecut,0]
    weights[p][t.w][1] +=1
    if t.ecut > weights[p][t.w][0] : weights[p][t.w][0] = t.ecut
 return weights

def TplotP(sTree):
  ut.bookCanvas(h,key='P',title='momentum',nx=1800,ny=1200,cx=3,cy=2)
  ut.bookCanvas(h,key='>P',title='N >P',   nx=1800,ny=1200,cx=3,cy=2)
  ut.bookCanvas(h,key='PT',title='Pt',nx=1800,ny=1200,cx=3,cy=2)
  ut.bookCanvas(h,key='>PT',title='N >Pt',   nx=1800,ny=1200,cx=3,cy=2)
  cuts = {'mu':'abs(id)==13','nu':'abs(id)!=13','mu-':'id==13','mu+':'id==-13',
          'nutau':'id==16','nutaubar':'id==-16','numu':'id==14','numubar':'id==-14',
          'nue':'id==12','nuebar':'id==-12','nuesum':'abs(id)==12','numusum':'abs(id)==14','nutausum':'abs(id)==16'}
  OpenCharm = {'':'','charm':"&(pythiaid==id & (abs(parentid) == 15 ||  abs(parentid) == 4112 || abs(parentid) == 4122  || abs(parentid) == 4132  \
                         ||  abs(parentid) == 431 || abs(parentid) == 421  || abs(parentid) == 411) )"}
  ROOT.gROOT.cd('')
  for x in ['','charm']:
   for q in cuts:
    p = q+x
    hn  = 'Tp'+p
    hnt = 'Tpt'+p
    ut.bookHist(h,hn,  p +' ;p [GeV] ;N',400,0.0,400.0)
    ut.bookHist(h,hnt, p +' ;pt [GeV] ;N',40,0.0,4.0)
    sTree.Draw('sqrt(px**2+py**2+pz**2)>>'+hn,'w*('+cuts[q]+OpenCharm[x]+')','goff')
    sTree.Draw('sqrt(px**2+py**2)>>'+hnt,'w*('+cuts[q]+OpenCharm[x]+')','goff')
    if q=='mu+': h[hn].SetLineColor(3) 
    if q=='mu-': h[hn].SetLineColor(4) 
# integrated rates
  for q in [ 'mu','mu-','mu+','nu','nue','nuesum','nuebar','numusum','numu','numubar','nutau','nutaubar']:
   for x in ['','charm']:
    for z in ['p','pt']:
     p = z+q+x
     hi =  'T'+p+'_>E'
     h[hi]=h['T'+p].Clone(hi)
     h[hi].Reset()
     nsum = 0 
     for i in range(h[hi].GetNbinsX()+1,0,-1):
      nsum+=h['T'+p].GetBinContent(i)
      h[hi].SetBinContent(i,nsum) 
  for z in ['p','pt']: 
   k = 1
   for x in [ 'mu','nu']:
    t=z.upper()
    p=z+x 
    cv = h[t].cd(k)
    cv.SetLogy(1)
    h['T'+p].Draw()
    if h['T'+p].GetEntries()<1: continue
    if not p.find('mu')<0: 
     h['T'+p+'+'].Draw('same')
     h['T'+p+'-'].Draw('same')
    cv = h['>'+t].cd(k)
    cv.SetLogy(1)
    h[hi].Draw()
    k+=1
# plot different nu species:
   k = 3
   cv = h[t].cd(k)
   cv.SetLogy(1)
   first = True
   i = 2
   h['tlnu'+z+str(k)] = ROOT.TLegend(0.49,0.13,0.88,0.36)
   for p in ['numu','numubar','nue','nuebar','nutau','nutaubar']:
    hn = 'T'+z+p 
    h['tlnu'+z+str(k)].AddEntry(h[hn],z+' '+p,'PL')
    h[hn].SetLineColor(i)
    h[hn+'8']=h[hn].Clone()
    h[hn+'8'].SetName(hn+'8')
    h[hn+'8'].Rebin(8)
    i+=1
    if first:
      h[hn+'8'].Draw() 
      first = False
    h[hn+'8'].Draw('same')  
   h['tlnu'+z+str(k)].Draw()
   k+=1
#

productions = {}
allProds = False
if allProds:
 productions["CERN-Cracow"] = {"stats":{1.:[1.1E8],10.:[1.22E9],100:[1.27E10]},
                               "file":"Mbias/pythia8_Geant4_total.root" }
# checked, 10 variables, parentid = 8
 productions["Yandex"]      = {"stats":{5.:[2.1E9,1E9],0.5:[1E8]},
                               "file":"Mbias/pythia8_Geant4_total_Yandex.root" }
# checked, 13 variables, parentid = 11
 productions["Yandex2"]     = {"stats":{10.:[1E10]},
                               "file":"Mbias/pythia8_Geant4_total_Yandex2.root" }
# now with mu momentum at prodcution, NOT after hadron absorber
productions["Yandex3"]     = {"stats":{10.:[1E10]},
                               "file":"Mbias/pythia8_Geant4_total_Yandex3.root" }
# checked, 13 variables, parentid = 11

fnew = "pythia8_Geant4-noOpenCharm.root"
noOpCharm = "!(pythiaid==id & (abs(parentid) == 15 ||  abs(parentid) == 4112 || abs(parentid) == 4122  || abs(parentid) == 4132  \
                         ||  abs(parentid) == 431 || abs(parentid) == 421  || abs(parentid) == 411) )"
OpCharm = "(pythiaid==id & (abs(parentid) == 15 ||  abs(parentid) == 4112 || abs(parentid) == 4122  || abs(parentid) == 4132  \
                         ||  abs(parentid) == 431 || abs(parentid) == 421  || abs(parentid) == 411) )"
cuts = {'':'abs(id)>0','_onlyMuons':'abs(id)==13','_onlyNeutrinos':'abs(id)==12||abs(id)==14||abs(id)==16'}

h={}

def mergeMinBias(pot,norm=5.E13,opt=''):
 storeCharm=False
 if opt != '': 
    storeCharm=True
    opt=''
 first = True
 for p in productions:
  f = ROOT.TFile.Open(eospath+productions[p]["file"])
  t = f.FindObjectAny("pythia8-Geant4")
  if first:
    first = False
    tuples = ''
    for l in t.GetListOfLeaves(): 
      if tuples == '': tuples += l.GetName()
      else:            tuples += ":"+l.GetName()
    fxx = fnew.replace('.root',opt+'.root')
    if storeCharm: fxx = fnew.replace('.root','old-charm.root')
    h['N']      = ROOT.TFile(fxx, 'RECREATE')
    print('new file created',fxx)
    h['ntuple'] = ROOT.TNtuple("pythia8-Geant4","min bias flux after 3m hadron absorber "+opt,tuples)
  ROOT.gROOT.cd()
  t.SetEventList(0) 
  if storeCharm: t.Draw(">>temp",cuts[opt]+"&"+OpCharm)
  else: t.Draw(">>temp",cuts[opt]+"&"+noOpCharm)
  temp = ROOT.gROOT.FindObjectAny('temp')
  t.SetEventList(temp) 
  nev = temp.GetN()
  leaves = t.GetListOfLeaves()
  nL = leaves.GetEntries()
  for iev in range(nev) :
     rc = t.GetEntry(temp.GetEntry(iev))
     vlist = []
     k=-1
     for x in range(nL):
      k+=1
      if nL > 11 and (k==7 or k==8 or k==9): continue
      vlist.append( leaves.At(x).GetValue() )
     if len(vlist) != 11 : 
         print("this should never happen, big error",len(vlist),k,p,iev,nev)
         1/0
     # "id:px:py:pz:x:y:z:pythiaid:parentid:w:ecut"
     # yandex productions have
     # "id:px:py:pz:x:y:z:ox:oy:oz:pythiaid:parentid:w:ecut"       
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
       print("this should not happen, except some rounding errors",p,Ekin,vlist[9])
# scoring plane, g4Ex_gap:   afterHadronZ = z0Pos+targetL+absorberL+5.1*cm  
#                                    z0Pos   = -50.*m    absorberL = 2*150.*cm
# target length increased for Yandex2 production, ignore this, put all muons at current end of hadronabsorber
     vlist[6] = endOfHadronAbsorber
     h['ntuple'].Fill(vlist[0],vlist[1],vlist[2],vlist[3],vlist[4],vlist[5],vlist[6],
                     vlist[7],vlist[8],vlist[9],vlist[10])
  h['N'].cd()
  h['ntuple'].Write()
 h['N'].Close()

def runProduction(opts=''):
 we = fillWeights()
 pot = {}
 norm = 5.E13
 for p in we:
  pot[p]={}
  for w in we[p]:
    pot[p][we[p][w][0]] = 5.E13/w
 print("pots:",pot)
 #
 mergeMinBias(pot,norm=5.E13,opt=opts)

def removeCharm(p):
  f = ROOT.TFile.Open(eospath+productions[p]["file"])
  t = f.FindObjectAny("pythia8-Geant4")
  first = True
  if first:
    first = False
    tuples = ''
    for l in t.GetListOfLeaves(): 
      if tuples == '': tuples += l.GetName()
      else:            tuples += ":"+l.GetName()
    h['N']      = ROOT.TFile(fnew, 'RECREATE')
    print('new file created',fnew)
    h['ntuple'] = ROOT.TNtuple("pythia8-Geant4",t.GetTitle()+" no charm",tuples)
  ROOT.gROOT.cd()
  t.SetEventList(0) 
  t.Draw(">>temp",noOpCharm)
  temp = ROOT.gROOT.FindObjectAny('temp')
  t.SetEventList(temp) 
  nev = temp.GetN()
  leaves = t.GetListOfLeaves()
  nL = leaves.GetEntries()
  for iev in range(nev):
     rc = t.GetEntry(temp.GetEntry(iev))
     vlist = array('f')
     for x in range(leaves.GetEntries()):
      vlist.append( leaves.At(x).GetValue() )
     h['ntuple'].Fill(vlist)
  h['N'].cd()
  h['ntuple'].Write()
  h['N'].Close()

def mergeWithCharm(splitOnly=False,ramOnly=False):
  # Ntup.Fill(par.id(),par.px(),par.py(),par.pz(),par.e(),par.m(),wspill,sTree.id,sTree.px,sTree.py,sTree.pz,sTree.E,sTree.M)
  # i.e. the par. is for the neutrino, and the sTree. is for its mother.
  # wspill is the weight for this file normalised/5e13.
 if not splitOnly:
  fcascade = ROOT.TFile.Open(eospath+"/Charm/Decay-Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1.root")
  t = fcascade.Decay
  newFile = ROOT.TFile("pythia8_Charm.root", 'RECREATE')
  nt = ROOT.TNtuple("pythia8-Geant4","mu/nu flux from charm","id:px:py:pz:x:y:z:opx:opy:opz:ox:oy:oz:pythiaid:parentid:w:ecut")
  for n in range(t.GetEntries()):
      rc = t.GetEntry(n)
      ztarget = rnr.Exp(0.16) + startOfTarget
      vlist = array('f')
      x = t.id,t.px,t.py,t.pz,0.,0.,ztarget,t.px,t.py,t.pz,0.,0.,ztarget,t.id,t.mid,t.weight,0.
      for ax in x:      vlist.append(ax)
      rc = nt.Fill(vlist)
  newFile.cd()
  nt.Write()
  newFile.Close()
  fcascade.Close()
  os.system("hadd -f pythia8_Geant4-withCharm.root pythia8_Geant4-noOpenCharm.root pythia8_Charm.root")
  print(" progress: minbias and charm merged")
  ramOnly = True
 if ramOnly:  
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
   if m%1000000==0 : print('status read',m)
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
   if m%1000000==0 : print('status write',m)
   m+=1
   vlist = array('f')
   for x in a: vlist.append(x)
   randomTuple.Fill(vlist)
  newFile.cd()
  randomTuple.Write()
  newFile.Close()
  f.Close()
  allEvents = []
  print(" progress: order of events randomized")
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
   ut.bookHist(h,str(idhnu+100),name+' log10(ptot) vs log10(pt+0.01)',100,-0.3,1.7,100,-2.,1.)
   ut.bookHist(h,str(idhnu+200),name+' log10(ptot) vs log10(pt+0.01)',25,-0.3,1.7,100,-2.,1.)
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
     vlist = array('f')
     for n in range(leaves.GetSize()):
      vlist.append(leaves.At(n).GetValue())
     ntuple.Fill(vlist)
     if "Neutrinos" in opt: 
        pt2=t.px**2+t.py**2
        ptot=ROOT.TMath.Sqrt(pt2+t.pz**2)
        l10ptot=min(max(ROOT.TMath.Log10(ptot),-0.3),1.69999)
        l10pt=min(ROOT.TMath.Log10(ROOT.TMath.Sqrt(pt2)+0.01),0.9999)
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
    print(" progress: splitted "+opt)
def test(fname):
 h['f'] = ROOT.TFile.Open(fname)
 sTree = h['f'].FindObjectAny('pythia8-Geant4')
 TplotP(sTree)
def compare():
 test(eospath+'pythia8_Geant4_onlyMuons.root')
 for x in ['','_>E']:
  for z in ['p','pt']:
   for ahist in ['mu-','mu+','mu','mu-charm','mu+charm','mucharm']:
    h['TP'+z+ahist+x]=h['T'+z+ahist+x].Clone('CT'+ahist+x)
 test(eospath+'pythia8_Geant4_Yandex_onlyNeutrinos.root')
 for x in ['','_>E']:
  for z in ['p','pt']:
   for ahist in ['numusum','nuesum','numusumcharm','nuesumcharm','numu','numubar','nue','nuebar','numucharm','numubarcharm','nuecharm','nuebarcharm']:
    h['TP'+z+ahist+x]=h['T'+z+ahist+x].Clone('CT'+ahist+x)
 test(eospath+'Mbias/pythia8_Geant4-withCharm-ram.root')
 for x in ['','_>E']:
  for z in ['p','pt']:
   t = z.upper()
   if x != '' : t='>'+t 
   t1=h[t].cd(1)
   p = z+'mu'
   h['T'+p+x].SetTitle('musum')
   h['T'+p+x].Draw()
   h['T'+p+'charm'+x].Draw('same')
   h['TP'+p+x].Draw('same')
   h['TP'+p+x].SetLineColor(6)
   h['TP'+p+'charm'+x].Draw('same')
   h['TP'+p+'charm'+x].SetLineColor(3)
   h['T'+p+'charm'+x].SetLineColor(2)
   h['T'+p+x].SetLineColor(4)
   h['L'+p+x] = ROOT.TLegend(0.33,0.69,0.99,0.94)
   h['L'+p+x].AddEntry(h['T'+p+x],'muon new with charm, cascade, k-fac','PL')
   h['L'+p+x].AddEntry(h['T'+p+'charm'+x],'muon from charm new with charm, cascade, k-fac','PL')
   h['L'+p+x].AddEntry(h['TP'+p+x],'muon old CERN-Cracow prod','PL')
   h['L'+p+x].AddEntry(h['TP'+p+'charm'+x],'muon from charm old CERN-Cracow prod','PL')
   h['L'+p+x].Draw()
   h[t].cd(2)
   p = z+'numusum'
   h['T'+p+x].Draw()
   h['T'+p+'charm'+x].Draw('same')
   h['TP'+p+x].Draw('same')
   h['TP'+p+x].SetLineColor(6)
   h['TP'+p+'charm'+x].Draw('same')
   h['TP'+p+'charm'+x].SetLineColor(3)
   h['T'+p+'charm'+x].SetLineColor(2)
   h['T'+p+x].SetLineColor(4)
   h['L'+p+x] = ROOT.TLegend(0.33,0.69,0.99,0.94)
   h['L'+p+x].AddEntry(h['T'+p+x],'nu_mu new with charm, cascade, k-fac','PL')
   h['L'+p+x].AddEntry(h['T'+p+'charm'+x],'nu_mu from charm new with charm, cascade, k-fac','PL')
   h['L'+p+x].AddEntry(h['TP'+p+x],'nu_mu old CERN-Cracow prod','PL')
   h['L'+p+x].AddEntry(h['TP'+p+'charm'+x],'nu_mu from charm old CERN-Cracow prod','PL')
   h['L'+p+x].Draw()
   t3=h[t].cd(3)
   t3.SetLogy(1)
   p = z+'nuesum'
   h['T'+p+x].Draw()
   h['T'+p+'charm'+x].Draw('same')
   h['TP'+p+x].Draw('same')
   h['TP'+p+x].SetLineColor(6)
   h['TP'+p+'charm'+x].Draw('same')
   h['TP'+p+'charm'+x].SetLineColor(3)
   h['T'+p+'charm'+x].SetLineColor(2)
   h['T'+p+x].SetLineColor(4)
   h['L'+p+x] = ROOT.TLegend(0.33,0.69,0.99,0.94)
   h['L'+p+x].AddEntry(h['T'+p+x],'nu_e new with charm, cascade, k-fac','PL')
   h['L'+p+x].AddEntry(h['T'+p+'charm'+x],'nu_e from charm new with charm, cascade, k-fac','PL')
   h['L'+p+x].AddEntry(h['TP'+p+x],'nu_e old CERN-Cracow prod','PL')
   h['L'+p+x].AddEntry(h['TP'+p+'charm'+x],'nu_e from charm old CERN-Cracow prod','PL')
   h['L'+p+x].Draw()
#
   t4 = h[t].cd(4)
   t4.SetLogy(1)
   h['Lmuc'+z+x] = ROOT.TLegend(0.33,0.73,0.99,0.94)
   p = z+'mu-'
   h['T'+p+x].SetTitle('mu-/mu+')
   h['T'+p+x].Draw()
   h['TP'+p+x].Draw('same')
   h['TP'+p+x].SetLineColor(6)
   h['T'+p+x].SetLineColor(4)
   h['Lmuc'+z+x].AddEntry(h['T'+p+x],'mu- new with charm, cascade, k-fac','PL')
   h['Lmuc'+z+x].AddEntry(h['TP'+p+x],'mu- old Yandex prod','PL')
   p = z+'mu+'
   h['T'+p+x].Draw('same')
   h['TP'+p+x].Draw('same')
   h['TP'+p+x].SetLineColor(3)
   h['T'+p+x].SetLineColor(2)
   h['Lmuc'+z+x].AddEntry(h['T'+p+x],'mu+ new with charm, cascade, k-fac','PL')
   h['Lmuc'+z+x].AddEntry(h['TP'+p+x],'mu+ old Yandex prod','PL')
   h['Lmuc'+z+x].Draw() 
#
   t5 = h[t].cd(5)
   t5.SetLogy(1)
   h['Lnumu'+z+x] = ROOT.TLegend(0.33,0.73,0.99,0.94)
   p = z+'numu'
   h['T'+p+x].SetTitle('numu/numubar')
   h['T'+p+x].Draw()
   h['TP'+p+x].Draw('same')
   h['TP'+p+x].SetLineColor(6)
   h['T'+p+x].SetLineColor(4)
   h['Lnumu'+z+x].AddEntry(h['T'+p+x],'nu_mu new with charm, cascade, k-fac','PL')
   h['Lnumu'+z+x].AddEntry(h['TP'+p+x],'nu_mu old Yandex prod','PL')
   p = z+'numubar'
   h['T'+p+x].Draw('same')
   h['TP'+p+x].Draw('same')
   h['TP'+p+x].SetLineColor(3)
   h['T'+p+x].SetLineColor(2)
   h['Lnumu'+z+x].AddEntry(h['T'+p+x],'anti nu_mu new with charm, cascade, k-fac','PL')
   h['Lnumu'+z+x].AddEntry(h['TP'+p+x],'anti nu_mu old Yandex prod','PL')
   h['Lnumu'+z+x].Draw() 
   t6 = h[t].cd(6)
   t6.SetLogy(1)
   p = z+'nue'
   h['Lnue'+z+x] = ROOT.TLegend(0.33,0.73,0.99,0.94)
   h['T'+p+x].SetTitle('nue/nuebar')
   h['T'+p+x].Draw()
   h['TP'+p+x].Draw('same')
   h['TP'+p+x].SetLineColor(6)
   h['T'+p+x].SetLineColor(4)
   h['Lnue'+z+x].AddEntry(h['T'+p+x],'nu_e new with charm, cascade, k-fac','PL')
   h['Lnue'+z+x].AddEntry(h['TP'+p+x],'nu_e old Yandex prod','PL')
   p = z+'nuebar'
   h['T'+p+x].Draw('same')
   h['TP'+p+x].Draw('same')
   h['TP'+p+x].SetLineColor(3)
   h['T'+p+x].SetLineColor(2)
   h['Lnue'+z+x].AddEntry(h['T'+p+x],'anti nu_e new with charm, cascade, k-fac','PL')
   h['Lnue'+z+x].AddEntry(h['TP'+p+x],'anti nu_e old Yandex prod','PL')
   h['Lnue'+z+x].Draw() 
#
   h[t].Print('comparison'+z+x.replace('_>','')+'.png')
   h[t].Print('comparison'+z+x.replace('_>','')+'.pdf')
# make ratio plots
 x = '_>E'
 for z in ['p','pt']:
   h[z+'muRatio'+x]=h['T'+z+'mu'+x].Clone(z+'muRatio'+x)
   h[z+'muRatio'+x].Divide(h['TP'+z+'mu'+x])
   h[z+'numuRatio'+x]=h['T'+z+'numusum'+x].Clone(z+'numuRatio'+x)
   h[z+'numuRatio'+x].Divide(h['TP'+z+'numusum'+x])
   h[z+'nueRatio'+x]=h['T'+z+'nuesum'+x].Clone(z+'nueRatio'+x)
   h[z+'nueRatio'+x].Divide(h['TP'+z+'nuesum'+x])
 ut.bookCanvas(h,key='ratios',title='ratios',nx=1800,ny=600,cx=2,cy=1)
 n = 1
 for z in ['p','pt']:
   h['Lratio'+z+x] = ROOT.TLegend(0.21,0.74,0.71,0.85)
   tc = h['ratios'].cd(n)
   n+=1
   h[z+'muRatio'+x].SetLineColor(2)
   h[z+'muRatio'+x].SetMaximum(max(h[z+'muRatio'+x].GetMaximum(),h[z+'numuRatio'+x].GetMaximum()))
   h[z+'muRatio'+x].SetMinimum(0)
   h[z+'muRatio'+x].SetStats(0)
   h[z+'muRatio'+x].Draw()
   h[z+'numuRatio'+x].SetLineColor(3)
   h[z+'numuRatio'+x].SetStats(0)
   h[z+'numuRatio'+x].Draw('same')
   #h[z+'nueRatio'+x].SetLineColor(4)
   #h[z+'nueRatio'+x].Draw('same')
   h['Lratio'+z+x].AddEntry(h[z+'muRatio'+x],'muon flux new / old ','PL')
   h['Lratio'+z+x].AddEntry(h[z+'numuRatio'+x],'nu_mu flux new / old ','PL')
   #h['Lratio'+z+x].AddEntry(h[z+'nueRatio'+x],'nu_e flux new / old ','PL')
   h['Lratio'+z+x].Draw()
 h['ratios'].Print('comparisonRatios.png')
 h['ratios'].Print('comparisonRatios.pdf')

print("+ merging with charm events using existing charmless Mbias file:   mergeWithCharm()")
print("+ removeCharm(p) from mbias file made with g4Ex_gap_mergeFiles.py")
print("+ testing output: test('pythia8_Geant4-noOpenCharm.root')")
print("+ not used anymore: to start the full production, including merging of Mbias files: runProduction()")

