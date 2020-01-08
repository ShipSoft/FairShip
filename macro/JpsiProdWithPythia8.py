import ROOT
import rootUtils as ut
from array import array

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-n", "--pot", dest="NPoT", help="protons on target", default=1000000)
parser.add_argument("-r", "--run", dest="run", help="production sequence number", default=0)

options = parser.parse_args()

P8gen = ROOT.FixedTargetGenerator()
P8gen.SetHeartBeat(100000)
P8gen.Init()
generators = {'p':P8gen.GetPythia(),'n':P8gen.GetPythiaN()}

Fntuple = 'Jpsi-Pythia8_'+options.NPoT+'_'+options.run+'.root'
ftup = ROOT.TFile.Open(Fntuple, 'RECREATE')
Ntup = ROOT.TNtuple("pythia6","pythia8 Jpsi",\
       "id:px:py:pz:E:M:mid:mpx:mpy:mpz:mE:mM:k:a0:a1:a2:a3:a4:a5:a6:a7:a8:a9:a10:a11:a12:a13:a14:a15:\
s0:s1:s2:s3:s4:s5:s6:s7:s8:s9:s10:s11:s12:s13:s14:s15")
timer = ROOT.TStopwatch()
timer.Start()

for n in range(int(options.NPoT)):
  for g in generators:
    py = generators[g]
    rc = py.next()
    jpsi = False
    for ii in range(py.event.size()):
       theEvent = py.event
       pid      = theEvent[ii].id()
       if pid!=443:continue
       jpsi = True
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
    Ntup.Fill(vl)
Ntup.Write()
ftup.Close()
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print "run ",options.run," PoT ",options.NPoT," Real time ",rtime, " s, CPU time ",ctime,"s"

