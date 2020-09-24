import ROOT
import rootUtils as ut
from array import array
theSeed      = 0
ROOT.gRandom.SetSeed(theSeed)

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-n", "--pot", dest="NPoT", help="protons on target", default=1000000)
parser.add_argument("-r", "--run", dest="run",  help="production sequence number", default=0)
parser.add_argument('-J', '--Jpsi-mainly',  action='store_true', dest='JpsiMainly',  default=False)
parser.add_argument('-Y', '--DrellYan',  action='store_true', dest='DrellYan',  default=False)

options = parser.parse_args()

P8gen = ROOT.FixedTargetGenerator()
P8gen.SetHeartBeat(100000)
if options.JpsiMainly: P8gen.SetJpsiMainly()
if options.DrellYan: P8gen.SetDrellYan()

P8gen.Init()
generators = {'p':P8gen.GetPythia(),'n':P8gen.GetPythiaN()}

timer = ROOT.TStopwatch()
timer.Start()

for n in range(int(options.NPoT)):
  for g in generators:
    py = generators[g]
    rc = py.next()

print ">>>> proton statistics"
generators['p'].stat()
print ">>>> neutron statistics"
generators['n'].stat()

timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print "run ",options.run," PoT ",options.NPoT," Real time ",rtime, " s, CPU time ",ctime,"s"

