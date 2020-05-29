from __future__ import print_function
import os,time,ROOT
def makeProd(prefix,DY,y=False,phiRandom=False,X=None):
  ncpu = 9
  shipsoft = os.environ['SHIPSOFT'].replace('/dev','')
  if not y:       
    f = shipsoft+'/data/pythia8_Geant4_onlyMuons.root'
    cmd  = "python $FAIRSHIP/macro/run_simScript.py --MuonBack -f " + f + " -Y "+str(float(DY)) # --display"
  elif y=='Jpsi': 
    f = shipsoft+'/data/pythia8_Geant4_Jpsi_onlyMuons.root'
    cmd  = "python $FAIRSHIP/macro/run_simScript.py --MuonBack -f " + f + " -Y "+str(float(DY)) # --display"
  else:       
    f = shipsoft+'/data/pythia8_Geant4_Yandex_onlyMuons.root'
    cmd  = "python $FAIRSHIP/macro/run_simScript.py --MuonBack -f " + f + " -Y "+str(float(DY)) # --display"
  if phiRandom:  cmd = cmd +' --phiRandom'
  fn = ROOT.TFile(f)
  sTree = fn.FindObjectAny('pythia8-Geant4')
  ntot = sTree.GetEntries()
  fn.Close()
  ns   = 0
  n3   = int(ntot/ncpu)
  for i in range(1,ncpu+1):
   d = prefix+str(i)
   if d not in os.listdir('.'): os.system('mkdir '+d)
  os.chdir('./'+prefix+'1')
  for i in range(1,ncpu+1):
   if i==ncpu: n3 = ntot - (i-1)*n3
   if X:
    if X==i: 
     os.system('cp $FAIRSHIP/macro/run_simScript.py .')
     os.system(cmd+" -n "+str(n3)+" -i "+str(ns) + " > log &")
   else:
    os.system('cp $FAIRSHIP/macro/run_simScript.py .')
    os.system(cmd+" -n "+str(n3)+" -i "+str(ns) + " > log &")
    time.sleep(5)
   #print " -n "+str(n3)+" -i "+str(ns) 
   ns += n3
   if i==ncpu: 
      os.chdir('../')
      break
   os.chdir('../'+prefix+str(i+1))
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
# 421-429 reduce size of vaccum tank before veto station, add pdgcode for muonPoint, move det2 closer
# 431-439 reduce size of vaccum tank before veto station, add pdgcode for muonPoint, move det2 closer Yandex
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
#makeProd("muon59",6,False)  #  
#makeProd("muon60",6,True)    #  
#makeProd("muon61",10,False)    # 
#makeProd("muon62",10,True)     #  

# makeProd("muon63",10,False)     #  
# makeProd("muon64",10,True)     #  
# makeProd("muon65",6,False)     #  
# makeProd("muon66",6,True)     #  

# run more statistics, 61, 62 
#makeProd("muon611",10,False,True)
#makeProd("muon621",10,True,True)   
#makeProd("muon612",10,False,True) 
#makeProd("muon622",10,True,True)  
#makeProd("muon613",10,False,True)
#makeProd("muon623",10,True,True) 
#makeProd("muon614",10,False,True)
#makeProd("muon624",10,True,True) 
#makeProd("muon615",10,False,True)
#makeProd("muon625",10,True,True) 
#makeProd("muon616",10,False,True)
#makeProd("muon626",10,True,True) 
#makeProd("muon617",10,False,True)
#makeProd("muon627",10,True,True) 
#makeProd("muon618",10,False,True)
#makeProd("muon628",10,True,True) 
#makeProd("muon619",10,False,True)
#makeProd("muon629",10,True,True) 
#makeProd("muon700",10,False,False) # switch off field of active shielding    # prefix,DY,y=False,phiRandom=False,X=None
#makeProd("muon710",10,False,False) # start production with beam smeared on r=3cm disk
#makeProd("muon720",10,True,False)   
#makeProd("muon711",10,False,True) # start production with beam smeared on r=3cm disk
#makeProd("muon721",10,True,True)   
#makeProd("muon712",10,False,True) # start production with beam smeared on r=3cm disk
#makeProd("muon722",10,True,True)   
#makeProd("muon713",10,False,True) # start production with beam smeared on r=3cm disk
#makeProd("muon723",10,True,True)   
#makeProd("muon714",10,False,True) # start production with beam smeared on r=3cm disk
#makeProd("muon724",10,True,True)   
#makeProd("muon715",10,False,True) # start production with beam smeared on r=3cm disk
#makeProd("muon725",10,True,True)   
#makeProd("muon716",10,False,True) # start production with beam smeared on r=3cm disk
#makeProd("muon726",10,True,True)   
#makeProd("muon717",10,False,True) # start production with beam smeared on r=3cm disk
#makeProd("muon777",10,False,True) # in case the other one does not work 717
#makeProd("muon727",10,True,True)  # ?
#makeProd("muon718",10,False,True) # start production with beam smeared on r=3cm disk
#makeProd("muon728",10,True,True)   
#makeProd("muon719",10,False,True) # start production with beam smeared on r=3cm disk
#makeProd("muon729",10,True,True)     #
#makeProd("muon730",10,'Jpsi',False)  # made with E50
#makeProd("muon731",10,'Jpsi',True)   # made with E50
#makeProd("muon732",10,'Jpsi',True)   # made with E50 
#makeProd("muon733",10,'Jpsi',True)   # back to pencil beam
#makeProd("muon630",10,False,True) # test with new muonShield code, 3cm smearing
#makeProd("muon631",10,False,True) # run with concrete wall enabled as sensitive
#makeProd("muon632",10,False,True) # run with concrete wall enabled as sensitive, active shielding polarity fixed
                                   # but wrong geometry
#makeProd("muon810",10,False,False) # start production with latest geometry
#makeProd("muon820",10,True,False)   
#makeProd("muon811",10,False,True) # 
#makeProd("muon821",10,True,True)   
##makeProd("muon812",10,False,True) # --< 831  copied back, done 16.3.2015
#makeProd("muon822",10,True,True)   
#makeProd("muon821",10,True,True)   
#makeProd("muon822",10,True,True)   
#
#makeProd("muon813",10,False,True) # 
#makeProd("muon823",10,True,True)   

#makeProd("muon814",10,False,True) # 
#makeProd("muon824",10,True,True)   
#makeProd("muon815",10,False,True)
#makeProd("muon825",10,True,True)
#makeProd("muon816",10,False,True)
#makeProd("muon826",10,True,True)
#makeProd("muon817",10,False,True)
#makeProd("muon827",10,True,True)
#makeProd("muon818",10,False,True)
#makeProd("muon828",10,True,True)
#makeProd("muon819",10,False,True)
#makeProd("muon829",10,True,True)
#makeProd("muon910",10,False,True)
#makeProd("muon920",10,True,True)
#makeProd("muon911",10,False,True)
#makeProd("muon921",10,True,True)

#makeProd("muon912",10,False,True)
#makeProd("muon922",10,True,True)

#makeProd("muon913",10,False,True)
#makeProd("muon923",10,True,True)
#makeProd("muon914",10,False,True)
#makeProd("muon924",10,True,True)
#makeProd("muon915",10,False,True)
#makeProd("muon925",10,True,True)
#makeProd("muon916",10,False,True)
#makeProd("muon926",10,True,True)
#makeProd("muon917",10,False,True)
#makeProd("muon927",10,True,True)
#makeProd("muon927",10,True,True,8)
#makeProd("muon918",10,False,True)
#makeProd("muon928",10,True,True)
#makeProd("muon919",10,False,True)
#makeProd("muon929",10,True,True)
#makeProd("muon1019",10,False,True)
#makeProd("muon1029",10,True,True)
#makeProd("muon1018",10,False,True)
#makeProd("muon1028",10,True,True)
#makeProd("muon1017",10,False,True)
#makeProd("muon1027",10,True,True)
#makeProd("muon1016",10,False,True)
#makeProd("muon1026",10,True,True)
#makeProd("muon1015",10,False,True)
#makeProd("muon1025",10,True,True)
#makeProd("muon1014",10,False,True)
#makeProd("muon1024",10,True,True)
#makeProd("muon1013",10,False,True)
#makeProd("muon1023",10,True,True)
#makeProd("muon1012",10,False,True)
#makeProd("muon1022",10,True,True)

def copy2EOS():
 import os
 eos = "/afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select"
 for prod in [610,620]:
  for run in range(0,10):
   prefix = 'muon'+str(prod+run)
   if prod in [610,620] and run == 0: prefix = 'muon'+str(int(prod/100))
   for i in range(1,10):
   # requires full path
    cmd = eos+' cp -r '+os.path.abspath('.')+'/'+prefix+str(i)+'/ /eos/experiment/ship/data/muonBackground/'+prefix+str(i)+'/'
    print(cmd)
    os.system(cmd)
def copyFromEOS():
 import os
 eos = "/afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select"
 for prod in [610,620]:
  for run in range(0,10):
   prefix = 'muon'+str(prod+run)
   if prod in [610,620] and run == 0: prefix = 'muon'+str(int(prod/100))
   for i in range(1,10):
   # requires full path
    cmd = eos+' cp -r  /eos/experiment/ship/data/muonBackground/'+prefix+str(i)+'/ ' +os.path.abspath('.')+'/'+prefix+str(i)+'/'
    print(cmd)
    os.system(cmd)
