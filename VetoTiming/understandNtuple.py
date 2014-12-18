from ROOT import *

debug = True
if debug:
    f = TFile("../data/neutrino661/ship.10.0.Genie-TGeant4_D.root")
else:
    f = TFile("../data/all/ship.10.0.Genie-TGeant4-370k.root")
t = f.Get("cbmsim")

entries = t.GetEntries()
for entry in xrange(entries):
    #entry = 5429
    #if not (entry%1000):
    #if (entry%1000):
    #    continue
    print "%s / %s"%(entry,entries)
        #res = {}
    t.GetEntry(entry)
    strawtubesPoints = t.strawtubesPoint.GetEntriesFast()
    if strawtubesPoints>0:
        print "here we go"
        assert(False)
