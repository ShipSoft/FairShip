import ROOT,os
from argparse import ArgumentParser
from numpy import zeros
from array import array 

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


path = "/home/truf/ship-ubuntu-1710-64/simulation1GeV-withDeadChannels/"
MCStats = {1:1.8E9}
charmNorm  = {1:0.176,10:0.424}
beautyNorm = {1:0.,   10:0.01218}

parser = ArgumentParser()
parser.add_argument("-f", "--file", dest="fname", help="name of input file", required=True)
options = parser.parse_args()

if options.fname=="run": run()

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
   if not stationPerTrack.has_key(ntrack): stationPerTrack[ntrack] = {'x1':0,'x2':0,'x3':0,'x4':0,'u1':0,'v2':0,'P':[0,0,0],'X':[0,0,1000.],'pid':0}
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
