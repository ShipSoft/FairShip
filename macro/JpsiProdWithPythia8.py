import ROOT
import rootUtils as ut
from array import array
theSeed      = 0
ROOT.gRandom.SetSeed(theSeed)

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-n", "--pot", dest="NPoT", help="protons on target", default=1000000)
parser.add_argument("-r", "--run", dest="run", help="production sequence number", default=0)

options = parser.parse_args()

P8gen = ROOT.FixedTargetGenerator()
P8gen.SetHeartBeat(100000)
P8gen.Init()
generators = {'p':P8gen.GetPythia(),'n':P8gen.GetPythiaN()}
for g in generators:
  generators[g].readString("443:new  J/psi  J/psi  3   0   0    3.09692    0.00009    3.09602    3.09782  0.   1   1   0   1   0")
  generators[g].readString("443:addChannel = 1   1.    0      -13       13")

Fntuple = 'Jpsi-Pythia8_'+options.NPoT+'_'+options.run+'.root'
ftup = ROOT.TFile.Open(Fntuple, 'RECREATE')
Ntup = ROOT.TNtuple("pythia6","pythia8 Jpsi",\
       "id:px:py:pz:E:M:mid:mpx:mpy:mpz:mE:mM:mM2:p1x:p1y:p1z:p2x:p2y:p2z:a6:a7:a8:a9:a10:a11:a12:a13:a14:a15:\
s0:s1:s2:s3:s4:s5:s6:s7:s8:s9:s10:s11:s12:s13:s14:s15")
timer = ROOT.TStopwatch()
timer.Start()

for n in range(int(options.NPoT)):
  for g in generators:
    py = generators[g]
    rc = py.next()
    jpsi = False
    theEvent = py.event
    for ii in range(theEvent.size()):
       pid      = theEvent[ii].id()
       if pid==443:
          jpsi = True
          break
    if not jpsi: continue
    vl=array('f')
    vl.append(float(pid))
    vl.append(theEvent[ii].px())
    vl.append(theEvent[ii].py())
    vl.append(theEvent[ii].pz())
    vl.append(theEvent[ii].e())
    vl.append(theEvent[ii].m())
    vl.append(float(theEvent[2].id()))
    vl.append(theEvent[1].px())
    vl.append(theEvent[1].py())
    vl.append(theEvent[1].pz())
    vl.append(theEvent[1].e())
    m1 = theEvent[ii].mother1()
    vl.append(float(theEvent[m1].id()))
    m2 = theEvent[ii].mother2()
    vl.append(float(theEvent[m2].id()))
    d1,d2 = theEvent[ii].daughter1(),theEvent[ii].daughter2()
    if theEvent[x.daughter1()].charge() < 0:
      vl.append(theEvent[d1].px())
      vl.append(theEvent[d1].py())
      vl.append(theEvent[d1].pz())
      vl.append(theEvent[d2].px())
      vl.append(theEvent[d2].py())
      vl.append(theEvent[d2].pz())
    else:
      vl.append(theEvent[d2].px())
      vl.append(theEvent[d2].py())
      vl.append(theEvent[d2].pz())
      vl.append(theEvent[d1].px())
      vl.append(theEvent[d1].py())
      vl.append(theEvent[d1].pz())
# 
    Ntup.Fill(vl)
Ntup.Write()
ftup.Close()
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print "run ",options.run," PoT ",options.NPoT," Real time ",rtime, " s, CPU time ",ctime,"s"

