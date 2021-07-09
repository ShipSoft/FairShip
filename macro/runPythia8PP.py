import ROOT
import rootUtils as ut
from array import array
theSeed      = 0
ROOT.gRandom.SetSeed(theSeed)
ROOT.gSystem.Load("libpythia8")

nudict = {12: "nue", -12: "anue", 14: "numu", -14: "anumu", 16: "nutau", -16: "anutau"}

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-f", "--nuflavour",  action='append', type=int, dest='nu_flavour', help="neutrino flavour", default=None)
parser.add_argument("-b", "--heartbeat",  dest="heartbeat", type=int,  help="progress report", default=10000)
parser.add_argument("-n", "--pot",  dest="Np", type=int,  help="proton collisions", default=1000000)
parser.add_argument("-Ecm", "--energyCM",  dest="eCM", type=float,  help="center of mass energy [GeV]", default=13000.)
parser.add_argument('-C', '--charm', action='store_true', dest='charm',help="ccbar production", default=False)
parser.add_argument('-B', '--beauty', action='store_true', dest='beauty',help="bbbar production", default=False)
parser.add_argument('-H', '--hard', action='store_true', dest='hard',help="all hard processes", default=False)
parser.add_argument('-X', '--PDFpSet',dest="PDFpSet",  type=str,  help="PDF pSet to use", default="13")
parser.add_argument('-EtaMin',dest="eta_min",  type=float,  help="minimum eta for neutrino to pass", default=6.)
parser.add_argument('-EtaMax',dest="eta_max",  type=float,  help="maximum eta for neutrino to pass", default=10.)

# for lhapdf, -X LHAPDF6:MMHT2014lo68cl (popular with LHC experiments, features LHC data till 2014)
# one PDF set, which is popular with IceCube, is HERAPDF15LO_EIG
# the default PDFpSet '13' is NNPDF2.3 QCD+QED LO

options = parser.parse_args()
X=ROOT.Pythia8Generator()

nunames=''
L=len(options.nu_flavour)
for i in range(0, L):
  if i==L-1: nunames +=nudict[options.nu_flavour[i]]
  else: nunames +=nudict[options.nu_flavour[i]]+'_'

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
tag = 'nobias'
if options.charm:
     generator.readString("HardQCD:hardccbar = on")
     tag = 'ccbar'
elif options.beauty:
     generator.readString("HardQCD:hardbbbar = on")
     tag = 'bbbar'
elif options.hard:
     generator.readString("HardQCD:all = on")
     tag = 'hard'
else:
     generator.readString("SoftQCD:inelastic = on")     
     
generator.init()

rc = generator.next()
processes = generator.info.codesHard()
hname = 'pythia8_'+tag+'_PDFpset'+options.PDFpSet+'_'+nunames
hname = hname.replace('*','star')
hname = hname.replace('->','to')
hname = hname.replace('/','')

fout = ROOT.TFile(hname+".root","RECREATE")
dTree = ROOT.TTree('NuTree', nunames)
dAnc = ROOT.TClonesArray("TParticle")
# AncstrBranch will hold the neutrino at 0th TParticle entry.
# Neutrino ancestry is followed backwards in evolution up to the colliding TeV proton
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
    # Ask for final state neutrino
    if py.event[ii].isFinal() and py.event[ii].id() in options.nu_flavour:
     evt = py.event[ii]
     eta = evt.eta()
     if (eta > options.eta_min and eta < options.eta_max) or (eta < -options.eta_min and eta > -options.eta_max):
       dAnc.Clear()
       neut = ROOT.TParticle(evt.id(), evt.status(),
                            evt.mother1(),evt.mother2(),0,0,
                            evt.px(),evt.py(),evt.pz(),evt.e(),
                            evt.xProd(),evt.yProd(),evt.zProd(),evt.tProd())
       dAnc[0] = neut
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
fout.cd() 
dTree.Write()
         
generator.stat()

timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
totalXsec = 0   # unit = mb,1E12 fb
processes = generator.info.codesHard()
for p in processes:
   totalXsec+=generator.info.sigmaGen(p)   
# nobias: 78.4mb, ccbar=4.47mb, bbbar=0.35mb

IntLumi = options.Np / totalXsec * 1E-12

print("Saving to output %s neutrino flavour(s) having PDG ID(s)"%(nunames), options.nu_flavour)
print("simulated events = %i, equivalent to integrated luminosity of %5.2G fb-1. Real time %6.1Fs, CPU time %6.1Fs"%(options.Np,IntLumi,rtime,ctime))
# neutrino CC cross section about 0.7 E-38 cm2 GeV-1 nucleon-1, SND@LHC: 59mm tungsten 
# sigma_CC(100 GeV) = 4.8E-12  
print("corresponding to effective luminosity (folded with neutrino CC cross section at 100GeV) of %5.2G fb-1."%(IntLumi/4.8E-12))


def debugging(g):
   generator.settings.listAll()
