import ROOT
import rootUtils as ut
from array import array
theSeed      = 0
ROOT.gRandom.SetSeed(theSeed)
ROOT.gSystem.Load("libpythia8")

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-b", "--heartbeat",  dest="heartbeat", type=int,  help="progress report",  default=10000)
parser.add_argument("-n", "--pot",  dest="Np", type=int,  help="proton collisions",          default=1000000)
parser.add_argument("-Ecm", "--energyCM",  dest="eCM", type=float,  help="center of mass energy [GeV]",          default=13000.)
parser.add_argument('-C', '--charm', action='store_true', dest='charm',  default=False)
parser.add_argument('-B', '--beauty', action='store_true', dest='beauty',  default=False)
parser.add_argument('-X', '--PDFpSet',dest="PDFpSet",  type=str,  help="PDF pSet to use", default="13")

# for lhapdf, -X LHAPDF6:MMHT2014lo68cl (popular with LHC experiments, features LHC data till 2014)
# one PDF set, which is popular with IceCube, is HERAPDF15LO_EIG
# the default PDFpSet '13' is NNPDF2.3 QCD+QED LO

options = parser.parse_args()
X=ROOT.Pythia8Generator()

# Make pp events
generator = ROOT.Pythia8.Pythia()
generator.settings.mode("Next:numberCount",options.heartbeat)
generator.settings.mode("Beams:idA",  2212)
generator.settings.mode("Beams:idB",  2212)
generator.readString("Beams:eCM = "+str(options.eCM));
# The Monash 2013 tune (#14) is set by default for Pythia above v8.200. 
# This tune provides slightly higher Ds and Bs fractions, in better agreement with the data.
# Tune setting comes before PDF setting!
#generator.readString("Tune:pp = 14")
generator.readString("PDF:pSet = "+options.PDFpSet)
if options.charm:
     generator.readString("HardQCD:hardccbar = on")
elif options.beauty:
     generator.readString("HardQCD:hardbbbar = on")
else:
     generator.readString("HardQCD:all = on")
generator.init()

rc = generator.next()
processes = generator.info.codesHard()
hname = 'pythia8_PDFpset'+options.PDFpSet
hname = hname.replace('*','star')
hname = hname.replace('->','to')
hname = hname.replace('/','')

fout = ROOT.TFile(hname+".root","RECREATE")
dTree = ROOT.TTree('NuTauTree','tau neutrino')
dAnc = ROOT.TClonesArray("TParticle")
# AncstrBranch will hold nutaus at 0th TParticle entry.
# Nutau ancestry is followed backwards in evolution up to the colliding TeV proton
# and saved as 1st, 2nd,... TParticle entries of AncstrBranch branch
dAncstrBranch = dTree.Branch("Ancstr",dAnc,32000,-1)
# EvtId will hold event id
evtId = array('i', [0])
dEvtId = dTree.Branch("EvtId", evtId, "evtId/I")

timer = ROOT.TStopwatch()
timer.Start()

nMade = 0
py = generator
for n in range(int(options.Np)):
  rc = py.next()
  for ii in range(1,py.event.size()):
    # Ask for final state nutau
    if py.event[ii].isFinal() and abs(py.event[ii].id())==16:
     evt = py.event[ii]
     eta = evt.eta()
     if (eta > 6 and eta < 10) or (eta < -6 and eta > -10):
       dAnc.Clear()
       tau = ROOT.TParticle(evt.id(), evt.status(),
                            evt.mother1(),evt.mother2(),0,0,
                            evt.px(),evt.py(),evt.pz(),evt.e(),
                            evt.xProd(),evt.yProd(),evt.zProd(),evt.tProd())
       dAnc[0] = tau
       evtId[0] = n
       gm = py.event[ii].mother1()
       # Chain all mothers (gm)
       while gm:
          evtM = py.event[gm]
          anc = ROOT.TParticle(evtM.id(),evtM.status(),
                               evtM.mother1(),evtM.mother2(),evtM.daughter1(),evtM.daughter2(),
                               evtM.px(),evtM.py(),evtM.pz(),evtM.e(),
                               evtM.xProd(),evtM.yProd(),evtM.zProd(),evtM.tProd())
          nAnc = dAnc.GetEntries()
          if dAnc.GetSize() == nAnc: dAnc.Expand(nAnc+10)
          dAnc[nAnc] = anc
          gm = py.event[gm].mother1()
       dTree.Fill()
  nMade+=1
  if nMade%options.heartbeat==0: print('made so far :',nMade)
fout.cd() 
dTree.Write()
         
generator.stat()

timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print("proton collisions ",options.Np," Real time ",rtime, " s, CPU time ",ctime,"s")

def debugging(g):
   generator.settings.listAll()
