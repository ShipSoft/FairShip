import ROOT,operator
import rootUtils as ut
from argparse import ArgumentParser
PDG = ROOT.TDatabasePDG.Instance()

### Add what is missed:
### PDG nuclear states are 10-digit numbers
### 10LZZZAAAI e.g. deuteron is 
### 1000010020
### from http://svn.cern.ch/guest/AliRoot/trunk/STEER/STEERBase/AliPDG.cxx and https://github.com/FairRootGroup/FairRoot/blob/master/eventdisplay/FairEventManager.cxx
### https://geant4.web.cern.ch/geant4/UserDocumentation/UsersGuides/ForApplicationDeveloper/html/AllResources/TrackingAndPhysics/particleList.src/ions/index.html

# ubuntu_miniShip_1/pythia8_Geant4_1_0.0.root : 20 GeV 50cm iron 50cm iron 
# ubuntu_miniShip_2/pythia8_Geant4_2_0.0.root : 20 GeV 50cm iron 100cm iron 
# ubuntu_miniShip_3/pythia8_Geant4_3_0.0.root : 20 GeV 50cm iron 200cm iron 
# ubuntu_miniShip_4/pythia8_Geant4_4_0.0.root : 20 GeV 50cm tungsten 200cm iron 

h = {}

parser = ArgumentParser()
parser.add_argument("-f", "--file", dest="inputFile", help="input file", default=False)

options = parser.parse_args()

acc = [250.,250.]
f = ROOT.TFile(options.inputFile)
mom = ROOT.TVector3()
for sTree in f.cbmsim:
    for v in sTree.vetoPoint:
          pid = v.PdgCode()
          hpid = 'p_'+str(pid)
          if not h.has_key(hpid):
               pname = hpid
               if PDG.GetParticle(pid): pname = PDG.GetParticle(pid).GetName()
               ut.bookHist(h,hpid,pname,1000,0.,10.)
               ut.bookHist(h,'inAcc'+hpid,pname,1000,0.,10.)
               ut.bookHist(h,'xy'+hpid,pname,100,-1*acc[0],acc[0],100,-1*acc[1],acc[1])
          v.Momentum(mom)
          rc = h[hpid].Fill(mom.Mag())
          if ( abs(v.GetX())<acc[0] and abs(v.GetY())<acc[1] ): rc = h['inAcc'+hpid].Fill(mom.Mag())
          rc = h['xy'+hpid].Fill(v.GetX(),v.GetY())

particles = {}
meanMom   = {}
for p in h:
  if not p.find('p')==0: continue
  particles[p]=h[p].GetEntries()
  meanMom[p]=[h[p].GetTitle(),h[p].GetMean(),h['xy'+p].GetSumOfWeights(),h['inAcc'+p].GetMean()]

sorted_pnames = sorted(particles.items(), key=operator.itemgetter(1))

for x in  sorted_pnames:
   pname = meanMom[x[0]][0]
   mean1 = meanMom[x[0]][1]
   mean2 = meanMom[x[0]][3]
   entries = x[1]
   inAcc = meanMom[x[0]][2]
   print "%20s %7.2F MeV/c %7.4F | %7.2F MeV/c %7.4F /event"%(pname,mean1*1000.,float(entries)/f.cbmsim.GetEntries(),mean2*1000.,float(inAcc)/f.cbmsim.GetEntries())
