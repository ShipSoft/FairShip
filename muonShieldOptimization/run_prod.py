# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import os
import time

import ROOT


def makeProd(prefix, y: bool = False, phiRandom: bool = False, X=None) -> None:
    ncpu = 9
    shipsoft = os.environ["SHIPSOFT"].replace("/dev", "")
    if not y:
        f = shipsoft + "/data/pythia8_Geant4_onlyMuons.root"
        cmd = "python $FAIRSHIP/macro/run_simScript.py --MuonBack -f " + f  # --display"
    elif y == "Jpsi":
        f = shipsoft + "/data/pythia8_Geant4_Jpsi_onlyMuons.root"
        cmd = "python $FAIRSHIP/macro/run_simScript.py --MuonBack -f " + f  # --display"
    else:
        f = shipsoft + "/data/pythia8_Geant4_Yandex_onlyMuons.root"
        cmd = "python $FAIRSHIP/macro/run_simScript.py --MuonBack -f " + f  # --display"
    if phiRandom:
        cmd = cmd + " --phiRandom"
    fn = ROOT.TFile(f)
    sTree = fn.FindObjectAny("pythia8-Geant4")
    ntot = sTree.GetEntries()
    fn.Close()
    ns = 0
    n3 = int(ntot / ncpu)
    for i in range(1, ncpu + 1):
        d = prefix + str(i)
        if d not in os.listdir("."):
            os.system("mkdir " + d)
    os.chdir("./" + prefix + "1")
    for i in range(1, ncpu + 1):
        if i == ncpu:
            n3 = ntot - (i - 1) * n3
        if X:
            if i == X:
                os.system("cp $FAIRSHIP/macro/run_simScript.py .")
                os.system(cmd + " -n " + str(n3) + " -i " + str(ns) + " > log &")
        else:
            os.system("cp $FAIRSHIP/macro/run_simScript.py .")
            os.system(cmd + " -n " + str(n3) + " -i " + str(ns) + " > log &")
            time.sleep(5)
        # print " -n "+str(n3)+" -i "+str(ns)
        ns += n3
        if i == ncpu:
            os.chdir("../")
            break
        os.chdir("../" + prefix + str(i + 1))


#
# 11-19 with QGSP_BERT_EMV instead of QGSP_BERT_HP_PEN
# 51-59 passive shielding
# 41-49 fixed field horizontal
# 61-69  chamber with vacuum
# 71-79 without field in the wings
# 81-89 add shielding
# 91-99 also 111-119 switch off  muBrems, muPair
# 101-109 vacuum tube as cone, Al->Steel
# 121-129 switch off only muIoni
# 151-159 vacuum tube as cone, Al->Steel, air in cave
# 161-169 new geometry
# 251-259 passive shielding with concrete walls
# 171-179 new increased Bdl,  2.5m clearance from start, 9m space for tau
# 181-189 even more field, narrow tunnel around first magnet, add 2m hadron absorber
# 311-314 change numbering of veto volumes
# 321-324 1 Teslas
# 331-339 added TauSensitive, fixed C1, using muons from Yandex
# 341-349 should be the same as 331-339
# 351-354 fixed RpcPoints, fixed field !  also - 359 made on t3
# 361-364 4m high magnets!
# 371-374 new strawpoints  with magC1 fixed
# 381-389 yandex file, overwrite with magC1 fixed
# 391-399 change to dY = 2m
# 401-409 change to dY = 2m Yandex
# 411-419 back to dY = 4m, add sensitive plance downstream det2
# 421-429 reduce size of vacuum tank before veto station, add pdgcode for muonPoint, move det2 closer
# 431-439 reduce size of vacuum tank before veto station, add pdgcode for muonPoint, move det2 closer Yandex
# 441-449 try with increased tau mu detector, and reduced height of active muon shield, dy=1m
# 451-459 try with increased tau mu detector, and reduced height of active muon shield, dy=1m  Yandex
# 461-469 dy=4m and then 1m, RPC fixed, display on
# 471-479 dy=4m and then 1m, RPC fixed, Yandex
# 481-489 dy=4m and then 1m, RPC fixed, display OFF
# 491-499 back to dy=1m  display on
# 501-509 dy=4m for last magnet part,  display on
# 511-519 dy=2,3,4m for last magnet parts,  display on
# 521-529 removal of almost overlaps
# 551-554 ultimate slim design
# 561-564 fixing overlaps hcal and almost overlaps in magnets
# 571-574 more undetected overlaps fixed
# 581-584 test with replacing tungsten core with iron
# reuse the following, minor mod det2 with shielding, different lengths, new fine tuned active shield, no hcal overlap
# new scaling of L vs Y
# 591-599 6m height
# 601-609 6m height, Yandex data
# 610-619 10m height
# 620-629 10m height, Yandex data
#
# 630-639 10m height, change RPC width 4.5->3.6m
# 640-649  6m height, change RPC width 4.5->3.6m
# makeProd("muon59",False)  #
# makeProd("muon60",True)    #
# makeProd("muon61",False)    #
# makeProd("muon62",True)     #

# makeProd("muon63",False)     #
# makeProd("muon64",True)     #
# makeProd("muon65",False)     #
# makeProd("muon66",True)     #

# run more statistics, 61, 62
# makeProd("muon611",False,True)
# makeProd("muon621",True,True)
# makeProd("muon612",False,True)
# makeProd("muon622",True,True)
# makeProd("muon613",False,True)
# makeProd("muon623",True,True)
# makeProd("muon614",False,True)
# makeProd("muon624",True,True)
# makeProd("muon615",False,True)
# makeProd("muon625",True,True)
# makeProd("muon616",False,True)
# makeProd("muon626",True,True)
# makeProd("muon617",False,True)
# makeProd("muon627",True,True)
# makeProd("muon618",False,True)
# makeProd("muon628",True,True)
# makeProd("muon619",False,True)
# makeProd("muon629",True,True)
# makeProd("muon700",False,False) # switch off field of active shielding    # prefix,y=False,phiRandom=False,X=None
# makeProd("muon710",False,False) # start production with beam smeared on r=3cm disk
# makeProd("muon720",True,False)
# makeProd("muon711",False,True) # start production with beam smeared on r=3cm disk
# makeProd("muon721",True,True)
# makeProd("muon712",False,True) # start production with beam smeared on r=3cm disk
# makeProd("muon722",True,True)
# makeProd("muon713",False,True) # start production with beam smeared on r=3cm disk
# makeProd("muon723",True,True)
# makeProd("muon714",False,True) # start production with beam smeared on r=3cm disk
# makeProd("muon724",True,True)
# makeProd("muon715",False,True) # start production with beam smeared on r=3cm disk
# makeProd("muon725",True,True)
# makeProd("muon716",False,True) # start production with beam smeared on r=3cm disk
# makeProd("muon726",True,True)
# makeProd("muon717",False,True) # start production with beam smeared on r=3cm disk
# makeProd("muon777",False,True) # in case the other one does not work 717
# makeProd("muon727",True,True)  # ?
# makeProd("muon718",False,True) # start production with beam smeared on r=3cm disk
# makeProd("muon728",True,True)
# makeProd("muon719",False,True) # start production with beam smeared on r=3cm disk
# makeProd("muon729",True,True)     #
# makeProd("muon730",'Jpsi',False)  # made with E50
# makeProd("muon731",'Jpsi',True)   # made with E50
# makeProd("muon732",'Jpsi',True)   # made with E50
# makeProd("muon733",'Jpsi',True)   # back to pencil beam
# makeProd("muon630",False,True) # test with new muonShield code, 3cm smearing
# makeProd("muon631",False,True) # run with concrete wall enabled as sensitive
# makeProd("muon632",False,True) # run with concrete wall enabled as sensitive, active shielding polarity fixed
# but wrong geometry
# makeProd("muon810",False,False) # start production with latest geometry
# makeProd("muon820",True,False)
# makeProd("muon811",False,True) #
# makeProd("muon821",True,True)
##makeProd("muon812",False,True) # --< 831  copied back, done 16.3.2015
# makeProd("muon822",True,True)
# makeProd("muon821",True,True)
# makeProd("muon822",True,True)
#
# makeProd("muon813",False,True) #
# makeProd("muon823",True,True)

# makeProd("muon814",False,True) #
# makeProd("muon824",True,True)
# makeProd("muon815",False,True)
# makeProd("muon825",True,True)
# makeProd("muon816",False,True)
# makeProd("muon826",True,True)
# makeProd("muon817",False,True)
# makeProd("muon827",True,True)
# makeProd("muon818",False,True)
# makeProd("muon828",True,True)
# makeProd("muon819",False,True)
# makeProd("muon829",True,True)
# makeProd("muon910",False,True)
# makeProd("muon920",True,True)
# makeProd("muon911",False,True)
# makeProd("muon921",True,True)

# makeProd("muon912",False,True)
# makeProd("muon922",True,True)

# makeProd("muon913",False,True)
# makeProd("muon923",True,True)
# makeProd("muon914",False,True)
# makeProd("muon924",True,True)
# makeProd("muon915",False,True)
# makeProd("muon925",True,True)
# makeProd("muon916",False,True)
# makeProd("muon926",True,True)
# makeProd("muon917",False,True)
# makeProd("muon927",True,True)
# makeProd("muon927",True,True,8)
# makeProd("muon918",False,True)
# makeProd("muon928",True,True)
# makeProd("muon919",False,True)
# makeProd("muon929",True,True)
# makeProd("muon1019",False,True)
# makeProd("muon1029",True,True)
# makeProd("muon1018",False,True)
# makeProd("muon1028",True,True)
# makeProd("muon1017",False,True)
# makeProd("muon1027",True,True)
# makeProd("muon1016",False,True)
# makeProd("muon1026",True,True)
# makeProd("muon1015",False,True)
# makeProd("muon1025",True,True)
# makeProd("muon1014",False,True)
# makeProd("muon1024",True,True)
# makeProd("muon1013",False,True)
# makeProd("muon1023",True,True)
# makeProd("muon1012",False,True)
# makeProd("muon1022",True,True)


def copy2EOS() -> None:
    import os

    eos = "/afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select"
    for prod in [610, 620]:
        for run in range(0, 10):
            prefix = "muon" + str(prod + run)
            if prod in [610, 620] and run == 0:
                prefix = "muon" + str(int(prod / 10))
            for i in range(1, 10):
                # requires full path
                cmd = (
                    eos
                    + " cp -r "
                    + os.path.abspath(".")
                    + "/"
                    + prefix
                    + str(i)
                    + "/ /eos/experiment/ship/data/muonBackground/"
                    + prefix
                    + str(i)
                    + "/"
                )
                print(cmd)
                os.system(cmd)


def copyFromEOS() -> None:
    import os

    eos = "/afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select"
    for prod in [610, 620]:
        for run in range(0, 10):
            prefix = "muon" + str(prod + run)
            if prod in [610, 620] and run == 0:
                prefix = "muon" + str(int(prod / 10))
            for i in range(1, 10):
                # requires full path
                cmd = (
                    eos
                    + " cp -r  /eos/experiment/ship/data/muonBackground/"
                    + prefix
                    + str(i)
                    + "/ "
                    + os.path.abspath(".")
                    + "/"
                    + prefix
                    + str(i)
                    + "/"
                )
                print(cmd)
                os.system(cmd)
