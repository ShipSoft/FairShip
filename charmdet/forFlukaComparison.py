import ROOT,os
from argparse import ArgumentParser
from numpy import zeros
from array import array
import rootUtils as ut
h = {}
flukaPDG={41:15,42:-15,45:411,46:-411,47:421,48:-421,49:431,50:-431,51:4122,57:-4122}
PDGfluka = {}
for x in flukaPDG: PDGfluka[flukaPDG[x]]=x
PDGflukaKeys=PDGfluka.keys()
def run():
 for n in range(0,20000,1000):
  cmd = "python $FAIRSHIP/charmdet/forFlukaComparison.py -f pythia8_Geant4_1.0_c"+str(n)+"_mu"
  os.system(cmd)
 cmd = "hadd ntuple-pythia8_Geant4_mbias_0-19_1.0_mu.root "
 for n in range(0,20000,1000):
  cmd += "ntuple-pythia8_Geant4_1.0_c"+str(n)+"_mu.root "
 os.system(cmd)
 cmd = "python $FAIRSHIP/charmdet/forFlukaComparison.py -f pythia8_Geant4_charm_0-19_1.0_mu"
 os.system(cmd)

def pids():
 ut.bookHist(h,'FpdgCode', 'Fluka pdgcode',100,0.5,100.5)
 ut.bookHist(h,'GpdgCodembias', 'Fluka pdgcode',100,0.5,100.5)
 ut.bookHist(h,'GpdgCodecharm', 'Fluka pdgcode',100,0.5,100.5)
 fluka = h['f'].muon
 for n in range(fluka.GetEntries()):
   rc=fluka.GetEvent(n)
   for x in fluka.parentpdg:
    rc = h['FpdgCode'].Fill(x)
 for x in ['mbias','charm']:
  h['g'+x]=ROOT.TFile('ntuple-pythia8_Geant4_'+x+'_0-19_1.0_mu.root')
  ship = h['g'+x].tMuFluxSim
  for n in range(ship.GetEntries()):
   rc = ship.GetEvent(n)
   for k in range(ship.nTracks):
    if ship.mother[k] in PDGflukaKeys:
     rc = h['GpdgCode'+x].Fill(PDGfluka[ship.mother[k]])
 Norm = fluka.GetEntries()/1.8E9
 h['GpdgCodeScaled']=h['GpdgCodecharm'].Clone('GpdgCodeScaled')
 h['GpdgCodeScaled'].Scale(Norm*charmNorm[1])
def compare():
 ut.bookHist(h,'FP', 'muon P Fluka',400,0.,400.)
 ut.bookHist(h,'FPt','muon Pt Fluka',50,0.,5.)
 h['f']=ROOT.TFile('MuonTree_FLUKA.root')
 fluka = h['f'].muon
 for n in range(fluka.GetEntries()):
  rc = fluka.GetEvent(n)
  for k in range(fluka.pdg.size()):
   rc = h['FP'].Fill(fluka.ptrk[k])
   pt = ROOT.TMath.Sqrt(fluka.xcotrk[k]**2+fluka.ycotrk[k]**2)*fluka.ptrk[k]
   if fluka.ptrk[k]>5.: rc = h['FPt'].Fill(pt)
 for x in ['mbias','charm']:
  h['g'+x]=ROOT.TFile('ntuple-pythia8_Geant4_'+x+'_0-19_1.0_mu.root')
  ship = h['g'+x].tMuFluxSim
  ut.bookHist(h,'GP'+x, 'muon P Pythia / Geant',400,0.,400.)
  ut.bookHist(h,'GPt'+x,'muon Pt Pythia / Geant',50,0.,5.)
  for n in range(ship.GetEntries()):
   rc = ship.GetEvent(n)
   for k in range(ship.nTracks):
    P = ROOT.TMath.Sqrt(ship.px[k]**2+ship.py[k]**2+ship.pz[k]**2)
    Pt = ROOT.TMath.Sqrt(ship.px[k]**2+ship.py[k]**2)
    rc = h['GP'+x].Fill(P)
    if P>5.: rc = h['GPt'+x].Fill(Pt)
 ut.bookCanvas(h,key='comparison',title='FLUKA / SHiP simulation comparison',nx=1600,ny=1200,cx=1,cy=2)
 case = {1:'P',2:'Pt'}
 for k in range(1,3):
  h['G'+case[k]]=h['G'+case[k]+'mbias'].Clone('GP')
  h['G'+case[k]].Add(h['G'+case[k]+'charm'],charmNorm[1])
  Norm = fluka.GetEntries()/1.8E9
  h['G'+case[k]+'scaled'] = h['G'+case[k]].Clone('G'+case[k]+'scaled')
  h['G'+case[k]+'scaled'].Scale(Norm)
  h['G'+case[k]+'mbiasscaled'] = h['G'+case[k]+'mbias'].Clone('G'+case[k]+'mbiasscaled')
  h['G'+case[k]+'mbiasscaled'].Scale(Norm)
  h['comparison'].cd(k)
  h['F'+case[k]].Draw()
  h['G'+case[k]+'scaled'].SetLineColor(ROOT.kMagenta)
  h['G'+case[k]+'scaled'].Draw('same')
  h['G'+case[k]+'mbiasscaled'].SetLineColor(ROOT.kRed)
  h['G'+case[k]+'mbiasscaled'].Draw('same')
  h['leg'+case[k]]=ROOT.TLegend(0.51,0.41,0.84,0.59)
  rc = h['leg'+case[k]].AddEntry(h['F'+case[k]],"FLUKA",'PL')
  rc = h['leg'+case[k]].AddEntry(h['G'+case[k]+'scaled'],"SHiP simulation, Pythia + Geant4",'PL')
  rc = h['leg'+case[k]].AddEntry(h['G'+case[k]+'mbiasscaled'],"SHiP simulation w/o charm, Pythia + Geant4",'PL')
  h['leg'+case[k]].Draw()
  h['ratio'+case[k]]=h['G'+case[k]+'scaled'].Clone('ratio')
  h['ratio'+case[k]].Divide(h['F'+case[k]])
 

path = "/home/truf/ship-ubuntu-1710-64/simulation1GeV-withDeadChannels/"
MCStats = {1:1.8E9}
charmNorm  = {1:0.176,10:0.424}
beautyNorm = {1:0.,   10:0.01218}

parser = ArgumentParser()
parser.add_argument("-f", "--file", dest="fname", help="name of input file", required=True)
options = parser.parse_args()

if options.fname=="run": 
  run()
elif options.fname=="compare": 
  compare()
else:
 options = parser.parse_args()
 fName = "ntuple-"+options.fname

 fNtuple = ROOT.TFile.Open(fName+'.root','recreate')
 tMuFluxSim  = ROOT.TTree('tMuFluxSim','Muflux simulation tree')

 maxD = 10
 nTracks  = array('i',1*[0])
 pid = array('i',maxD*[0])
 px  = array('f',maxD*[0])
 py  = array('f',maxD*[0])
 pz  = array('f',maxD*[0])
 x   = array('f',maxD*[0])
 y   = array('f',maxD*[0])
 z   = array('f',maxD*[0])
 w   = array('f',maxD*[0])
 mother  = array('i',maxD*[0])
 process = array('i',maxD*[0])

 tMuFluxSim.Branch('nTracks',nTracks,'nTracks/I')
 tMuFluxSim.Branch('pid',pid,'pid[nTracks]/I')
 tMuFluxSim.Branch('px',px,'px[nTracks]/F')
 tMuFluxSim.Branch('py',py,'py[nTracks]/F')
 tMuFluxSim.Branch('pz',pz,'pz[nTracks]/F')
 tMuFluxSim.Branch('x',x,'x[nTracks]/F')
 tMuFluxSim.Branch('y',y,'y[nTracks]/F')
 tMuFluxSim.Branch('z',z,'z[nTracks]/F')
 tMuFluxSim.Branch('w',w,'w[nTracks]/F')
 tMuFluxSim.Branch('mother',mother,'mother[nTracks]/I')
 tMuFluxSim.Branch('process',process,'process[nTracks]/I')

 sTree = ROOT.TChain('cbmsim')
 for n in range(5):
  sTree.Add(path+options.fname+'/ship.conical.MuonBack-TGeant4_dig_RT-'+str(n)+'.root')
 for n in range(sTree.GetEntries()):
  rc = sTree.GetEvent(n)
  stationPerTrack = {}
  for p in sTree.MufluxSpectrometerPoint:
   if abs(p.PdgCode())!=13: continue
   ntrack = p.GetTrackID()
   if ntrack<0: continue
   if not ntrack in stationPerTrack: stationPerTrack[ntrack] = {'x1':0,'x2':0,'x3':0,'x4':0,'u1':0,'v2':0,'P':[0,0,0],'X':[0,0,1000.],'pid':0}
   detID = p.GetDetectorID()
   hit = ROOT.MufluxSpectrometerHit(detID,0)
   info = hit.StationInfo()
   s = info[0]
   if info[4] == 0:
     stationPerTrack[ntrack]['x'+str(s)]+=1
     if p.GetZ()<stationPerTrack[ntrack]['X'][2]:
      stationPerTrack[ntrack]['X'][2] = p.GetZ()
      stationPerTrack[ntrack]['X'][0] = p.GetX()
      stationPerTrack[ntrack]['X'][1] = p.GetY()
      stationPerTrack[ntrack]['P'][0] = p.GetPx()
      stationPerTrack[ntrack]['P'][1] = p.GetPy()
      stationPerTrack[ntrack]['P'][2] = p.GetPz()
      stationPerTrack[ntrack]['pid'] = p.PdgCode()
   if info[4] == 1: stationPerTrack[ntrack]['u1']+=1
   if info[4] == 2: stationPerTrack[ntrack]['v2']+=1
  nTracks[0] = 0
  for ntrack in stationPerTrack:
   test = 1
   for k in ['x1','x2','x3','x4','u1','v2']: test*=stationPerTrack[ntrack][k]
   if test == 0: continue
   pid[nTracks[0] ] = stationPerTrack[ntrack]['pid']
   px[nTracks[0] ] = stationPerTrack[ntrack]['P'][0]
   py[nTracks[0] ] = stationPerTrack[ntrack]['P'][1]
   pz[nTracks[0] ] = stationPerTrack[ntrack]['P'][2]
   x[nTracks[0] ] = stationPerTrack[ntrack]['X'][0]
   y[nTracks[0] ] = stationPerTrack[ntrack]['X'][1]
   z[nTracks[0] ] = stationPerTrack[ntrack]['X'][2]
   mo = sTree.MCTrack[ntrack].GetMotherId()
   mother[nTracks[0] ] = 0
   if not mo < 0: mother[nTracks[0] ] =  sTree.MCTrack[mo].GetPdgCode()
   process[nTracks[0] ]  = sTree.MCTrack[ntrack].GetProcID()
   w[nTracks[0]] = MCStats[1]
   if not options.fname.find('charm')<0: w[nTracks[0]]=w[nTracks[0]]/charmNorm[1]
   nTracks[0]+=1
#
  tMuFluxSim.Fill()

 fNtuple.Write() 
 fNtuple.Close()
