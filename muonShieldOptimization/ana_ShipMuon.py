from __future__ import print_function
# analyze muon background /media/Data/HNL/PythiaGeant4Production/pythia8_Geant4_total.root 
import os,ROOT
import multiprocessing as mp
from rootpyPickler import Unpickler
ROOT.gInterpreter.ProcessLine('typedef double Double32_t')
local = False
if not os.uname()[1].lower().find('ubuntu')< 0: local = True

parallel = True
if parallel: 
# Define an output queue
  output = mp.Queue()
  processes = []


# 11-19 with QGSP_BERT_EMV instead of QGSP_BERT_HP_PEN
# 51-59 passive shielding
# 41-49 fixed field horizontal
# 61-69  chamber with vacuum
# 71-79 without field in the wings
# 81-89 add shielding
# 91-99 switch off  muBrems, muPair
# 101-109 vacuum tube as cone, Al->Steel

#prefix = 'muon4' # default
#prefix = 'muon6' # Al -> vacuum 
#prefix = 'muon7' # no field in wings
#prefix = 'muon8' # entry window + additional shielding
#prefix = 'muon9' # switch off  muBrems, muPair
#prefix = 'muon10' # vacuum tube as cone, Al->Steel
#prefix = 'muon14' # vacuum tube as cone, Al->Steel, slightly smaller lead shield
#prefix = 'muon12' # switch off  muIoni
#prefix = 'muon13' # switch off  muBrems, muPair AND muIoni
#prefix = 'muon15' # vacuum tube as cone, Al->Steel, cave with air
#prefix = 'muon 161-169 new geometry
#prefix = 'muon 251-259 passive shielding with concrete walls
#prefix = 'muon 171-179 new increased Bdl,  2.5m clearance from start, 9m space for tau
# 181-189 narrow tunnel around first magnet, add 2m hadron absorber, fixed problem with B-field -> G4
# 191-199 narrow tunnel bug fix, also bug fix for top/bottom, now with tungsten core in add absorber
# 201-209 test with reduced field, 1.5T
# 211-219 many bug fixes, overlaps, added Goliath magnet
# 221-229 bug fix for Goliath 
# 231-239 reduce field to 1T
# 311-314 change numbering of veto volumes
# 321-324 1 Teslas
# 331-339 added TauSensitive, fixed C1, using muons from Yandex
# 341-349 should be the same as 331-339
# 361-364 4m high magnets!
# 371-374 new strawpoints
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
# 491-499 back to dy=1m display on
# 551-554 ultimate slim design
# 561-564 fixing overlaps hcal and almost overlaps in magnets
# 571-574 more undetected overlaps fixed
# 581-584 test with replacing tungsten core with iron, 10m height
# 591-599 test with replacing tungsten core with iron, 6m height, display
# 601-609 replacing tungsten core with iron, 6m height, Yandex data, display
# 610-619 replacing tungsten core with iron, 10m height, display
# 620-629 replacing tungsten core with iron, 10m height, Yandex data, display
# 630-639 10m height, change RPC width 4.5->3.6m
# 640-649 10m height, change RPC width 4.5->3.6m Yandex
# 650-669 6m height, change RPC width 4.5->3.6m
# 660-669 6m height, change RPC width 4.5->3.6m Yandex
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
#makeProd("muon729",10,True,True)   
#makeProd("muon730",10,'Jpsi',False)   
#makeProd("muon731",10,'Jpsi',True)   
#makeProd("muon732",10,'Jpsi',True)   
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
#makeProd("muon633",10,'concrete',False) # run with concrete wall enabled as sensitive
#makeProd("muon1111",10,'False',False) # try iron for first shield
#makeProd("muon1121",10,'True',False)  # try iron for first shield
#makeProd("muon1112",10,'False',True) # try iron for first shield
#makeProd("muon1122",10,'True',True)  # try iron for first shield
# restart with also rockS sensitive and &&->||
#makeProd("muon634",10,'concrete',False) # run with concrete wall enabled as sensitive, and active shield too
#makeProd("muon635",10,'concrete',True) #   run with concrete wall enabled as sensitive, and active shield too
#makeProd("muon636",10,'concrete',True) #   run with concrete wall enabled as sensitive, and active shield too
#makeProd("muon637",10,'concrete',True) #   run with concrete wall enabled as sensitive, and active shield too
#makeProd("muon638",10,'concrete',True) #   run with concrete wall enabled as sensitive, and active shield too
#makeProd("muon639",10,'concrete',True) #   run with concrete wall enabled as sensitive, and active shield too
#makeProd("muon640",10,'concrete',True) #   run with concrete wall enabled as sensitive, and active shield too
#makeProd("muon641",10,'concrete',True) #   run with concrete wall enabled as sensitive, and active shield too
#makeProd("muon642",10,'concrete',True) #   run with concrete wall enabled as sensitive, and active shield too
#makeProd("muon643",10,'concrete',True) #   run with concrete wall enabled as sensitive, and active shield too
#makeProd("muon650",10,'concrete',False) # run with concrete wall enabled as sensitive, first tunnel 10m wide
#makeProd("muon651",10,'concrete',False) # run with concrete wall enabled as sensitive, first tunnel 10m wide
#makeProd("muon652",10,'concrete',True) # run with concrete wall enabled as sensitive, first tunnel 10m wide
#makeProd("muon653",10,'concrete',True) # run with concrete wall enabled as sensitive, first tunnel 10m wide
#makeProd("muon654",10,'concrete',True) # run with concrete wall enabled as sensitive, first tunnel 10m wide
#makeProd("muon655",10,'concrete',True) # run with concrete wall enabled as sensitive, first tunnel 10m wide
#makeProd("muon656",10,'concrete',True) # run with concrete wall enabled as sensitive, first tunnel 10m wide
#makeProd("muon657",10,'concrete',True) # run with concrete wall enabled as sensitive, first tunnel 10m wide
#makeProd("muon658",10,'concrete',True) # run with concrete wall enabled as sensitive, first tunnel 10m wide
#makeProd("muon659",10,'concrete',True) # run with concrete wall enabled as sensitive, first tunnel 10m wide
#makeProd("muon660",10,'concrete',False) # liter magnet
#makeProd("muon661",10,'concrete',True) # liter magnet
#makeProd("muon662",10,'concrete',True) # liter magnet
#makeProd("muon663",10,'concrete',True) # liter magnet
#makeProd("muon664",10,'concrete',True) # liter magnet
#makeProd("muon665",10,'concrete',True) # liter magnet
#makeProd("muon666",10,'concrete',True) # liter magnet
#makeProd("muon667",10,'concrete',True) # liter magnet
#makeProd("muon668",10,'concrete',True) # liter magnet
#makeProd("muon669",10,'concrete',True) # liter magnet
#makeProd("muon670",10,'concrete',False) # even liter magnet
#makeProd("muon671",10,'concrete',True) # even liter magnet
#makeProd("muon672",10,'concrete',True) # even liter magnet
#makeProd("muon673",10,'concrete',True) # even liter magnet
#makeProd("muon674",10,'concrete',True) # even liter magnet
#makeProd("muon675",10,'concrete',True) # even liter magnet
#makeProd("muon676",10,'concrete',True) # even liter magnet
#makeProd("muon677",10,'concrete',True) # even liter magnet
#makeProd("muon678",10,'concrete',True) # even liter magnet
#makeProd("muon679",10,'concrete',True) # even liter magnet
# new attempt, previous did not worked out
#makeProd("muon680",10,'concrete',False) # even liter magnet
#makeProd("muon681",10,'concrete',True) # even liter magnet
#makeProd("muon682",10,'concrete',True) # even liter magnet
#makeProd("muon683",10,'concrete',True) # even liter magnet
#makeProd("muon684",10,'concrete',True) # even liter magnet
#makeProd("muon685",10,'concrete',True) # even liter magnet
#makeProd("muon686",10,'concrete',True) # even liter magnet
#makeProd("muon687",10,'concrete',True) # even liter magnet
#makeProd("muon688",10,'concrete',True) # even liter magnet
#makeProd("muon689",10,'concrete',True) # even liter magnet
# new attempt, increase height of first magnet, previous did not worked out either
#makeProd("muon690",10,'concrete',False) # even liter magnet
#makeProd("muon691",10,'concrete',True) # even liter magnet
#makeProd("muon692",10,'concrete',True) # even liter magnet
#makeProd("muon693",10,'concrete',True) # even liter magnet
#makeProd("muon694",10,'concrete',True) # even liter magnet
#makeProd("muon695",10,'concrete',True) # even liter magnet
#makeProd("muon696",10,'concrete',True) # even liter magnet
#makeProd("muon697",10,'concrete',True) # even liter magnet
#makeProd("muon698",10,'concrete',True) # even liter magnet
#makeProd("muon699",10,'concrete',True) # even liter magnet
# testing height 4m->2m
#makeProd("muon700",10,'concrete',False) # even liter magnet
#makeProd("muon701",10,'concrete',True) # even liter magnet
#makeProd("muon702",10,'concrete',True) # even liter magnet
#makeProd("muon703",10,'concrete',True) # even liter magnet
#makeProd("muon704",10,'concrete',True) # even liter magnet
#makeProd("muon705",10,'concrete',True) # even liter magnet
#makeProd("muon706",10,'concrete',True) # even liter magnet
#makeProd("muon707",10,'concrete',True) # even liter magnet
#makeProd("muon708",10,'concrete',True) # even liter magnet
#makeProd("muon709",10,'concrete',True) # even liter magnet
# testing height 4m->2m + new magnets
#makeProd("muon800",10,'concrete',False) # even liter magnet
#makeProd("muon801",10,'concrete',True) # even liter magnet
#makeProd("muon802",10,'concrete',True) # even liter magnet
#makeProd("muon803",10,'concrete',True) # even liter magnet
#makeProd("muon804",10,'concrete',True) # even liter magnet
#makeProd("muon805",10,'concrete',True) # even liter magnet
#makeProd("muon806",10,'concrete',True) # even liter magnet
#makeProd("muon807",10,'concrete',True) # even liter magnet
#makeProd("muon808",10,'concrete',True) # even liter magnet
#makeProd("muon809",10,'concrete',True) # even liter magnet
# new iteration, and ship_geo.Yheight*1./10.   
#makeProd("muon710",10,'concrete',False) # even liter magnet
#makeProd("muon711",10,'concrete',True) # even liter magnet
#makeProd("muon712",10,'concrete',True) # even liter magnet
#makeProd("muon713",10,'concrete',True) # even liter magnet
#makeProd("muon714",10,'concrete',True) # even liter magnet
#makeProd("muon715",10,'concrete',True) # even liter magnet
#makeProd("muon716",10,'concrete',True) # even liter magnet
#makeProd("muon717",10,'concrete',True) # even liter magnet
#makeProd("muon718",10,'concrete',True) # even liter magnet
#makeProd("muon719",10,'concrete',True) # even liter magnet
# new iteration, and back to ship_geo.Yheight*2./10.   
#makeProd("muon720",10,'concrete',False) # even liter magnet
#makeProd("muon721",10,'concrete',True) # even liter magnet
#makeProd("muon722",10,'concrete',True) # even liter magnet
#makeProd("muon723",10,'concrete',True) # even liter magnet
#makeProd("muon724",10,'concrete',True) # even liter magnet
#makeProd("muon725",10,'concrete',True) # even liter magnet
#makeProd("muon726",10,'concrete',True) # even liter magnet
#makeProd("muon727",10,'concrete',True) # even liter magnet
#makeProd("muon728",10,'concrete',True) # even liter magnet
#makeProd("muon729",10,'concrete',True) # even liter magnet
# new iteration, and back to ship_geo.Yheight*2./10. but with more info in vetoPoint  
#makeProd("muon730",10,'concrete',False) # even liter magnet
#makeProd("muon740",10,'concrete',False) # even liter magnet
# new iteration,  ship_geo.Yheight*1./10.   
#makeProd("muon750",10,'concrete',False) # 
# new iteration,  ship_geo.Yheight*1.5/10.   
#makeProd("muon760",10,'concrete',False) #
#makeProd("muon761",10,'concrete',True) #
# as before but now with full simulation
#makeProd("muon1710",10,False,False)
#makeProd("muon1720",10,True,False)
#makeProd("muon1711",10,False,True)
#makeProd("muon1721",10,True,True)
#makeProd("muon1712",10,False,True)
#makeProd("muon1722",10,True,True)
#makeProd("muon1713",10,False,True)
#makeProd("muon1723",10,True,True)
#makeProd("muon1714",10,False,True)
#makeProd("muon1724",10,True,True)
#makeProd("muon1715",10,False,True)
#makeProd("muon1725",10,True,True)
#makeProd("muon1716",10,False,True)
#makeProd("muon1726",10,True,True)
# another one, hopefully better
#makeProd("muon1717",10,'concrete',False) #
# another one, increasing height to 3m
#makeProd("muon1718",10,'concrete',False) #

prefixes  = []
withChain = 0
pref = 'muon'
xx = os.path.abspath('.').lower()
if not xx.find('neutrino')<0: pref='neutrino'
if not xx.find('vdis')<0: pref='disV'
elif not xx.find('clby')<0:  pref='disCLBY'
elif not xx.find('dis')<0:  pref='dis'

if len(os.sys.argv)>1 : 
 for i in range(1,len(os.sys.argv)):
   for prefix in os.sys.argv[i].split(','):
    if prefix.find(pref)<0:prefix=pref+prefix
    prefixes.append(prefix) 
    withChain+=1
else: 
 prefixes = ['']

testdir = '.'
path = ''
# if local: path = "/media/Data/HNL/muonBackground/"
if prefixes[0]!='': testdir = path+prefixes[0]+'1'
# figure out which setup
for f in os.listdir(testdir):
  if not f.find("geofile_full")<0:
     fgeo = ROOT.TFile(testdir+'/'+f)
     sGeo = fgeo.FAIRGeom 
     inputFile = f.replace("geofile_full","ship")
     break 
# try to extract from input file name
tmp = inputFile.split('.')
try:
  dy = float( tmp[1]+'.'+tmp[2] )
except:
  dy = 10.

if not inputFile.find('_D.')<0:
 inputFile1 = inputFile.replace('_D.','.')
 inputFile2 = inputFile
else :
 inputFile1 = inputFile
 inputFile2 = inputFile.replace('.root','_D.root')

import rootUtils as ut
import shipunit as u
PDG = ROOT.TDatabasePDG.Instance()
from ShipGeoConfig import ConfigRegistry
# init geometry and mag. field
if not fgeo.FindKey('ShipGeo'):
 # old geofile, missing Shipgeo dictionary
 if sGeo.GetVolume('EcalModule3') :  ecalGeoFile = "ecal_ellipse6x12m2.geo"
 else: ecalGeoFile = "ecal_ellipse5x10m2.geo" 
 print('found ecal geo for ',ecalGeoFile)
 # re-create geometry and mag. field
 ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy, EcalGeoFile = ecalGeoFile )
else: 
 # new geofile, load Shipgeo dictionary written by run_simScript.py
  upkl    = Unpickler(fgeo)
  ShipGeo = upkl.load('ShipGeo')
  ecalGeoFile = ShipGeo.ecal.File

# -----Create geometry----------------------------------------------
import shipDet_conf
run = ROOT.FairRunSim()
modules = shipDet_conf.configure(run,ShipGeo)

ecal = modules['Ecal']

rz_inter = -1.,0.
def origin(sTree,it):
 at = sTree.MCTrack[it]
 im = at.GetMotherId()
 if im>0: origin(sTree,im)
 if im<0: 
   # print 'does not come from muon'
   rz_inter = -1.,0.
 if im==0: 
   #print 'origin z',at.GetStartZ()
   rz_inter = ROOT.TMath.Sqrt(at.GetStartX()**2+at.GetStartY()**2),at.GetStartZ()

otherPhysList = False
noField       = False
passive       = False
#
top  = sGeo.GetTopVolume()
muon = top.GetNode("MuonDetector_1")
mvol = muon.GetVolume()
zmuon = muon.GetMatrix().GetTranslation()[2]
totl  = (zmuon + mvol.GetShape().GetDZ() ) / u.m 
ztarget = -100.

fchain = []
fchainRec = []
# first time trying to read a chain of Fairship files, doesn't seem to work out of the box, try some tricks.
testdir = '.'
if path != '': testdir = path
if withChain>0:
 for prefix in prefixes:
  for i in range(1,10):
   if not prefix+str(i) in os.listdir(testdir): continue
   q1 = inputFile1 in os.listdir(path+prefix+str(i))
   q2 = inputFile2 in os.listdir(path+prefix+str(i))
   recFile1 = inputFile1.replace('.root','_rec.root')
   recFile2 = inputFile2.replace('.root','_rec.root')
   r1 = recFile1 in os.listdir(path+prefix+str(i))
   r2 = recFile2 in os.listdir(path+prefix+str(i))
   if q1 or r1 : inputFile  = inputFile1
   elif q2 or r2: inputFile = inputFile2
   else: continue
   fname = path+prefix+str(i)+'/'+inputFile 
   recFile = inputFile.replace('.root','_rec.root')
   if not recFile in os.listdir(path+prefix+str(i)): 
     fchain.append(fname)
     continue
   fname = path+prefix+str(i)+'/'+recFile
   fchainRec.append(fname)
   fchain.append(fname)  # take rec file if exist
else:
 fchain.append(inputFile)
 prefix = ''

def makeProd():
  ntot = 736406
  ncpu = 4
  n3   = int(ntot/ncpu)
  cmd  = "python $FAIRSHIP/macro/run_simScript.py --MuonBack -f $SHIPSOFT/data/pythia8_Geant4_onlyMuons.root " # --display"
  ns   = 0
  prefix = 'muon18'
  for i in range(1,ncpu+1):
   d = prefix+str(i)
   if d not in os.listdir('.'): os.system('mkdir '+d)
  os.chdir('./'+prefix+'1')
  for i in range(1,ncpu+1):
   if i==ncpu: n3 = ntot - i*n3
   os.system('cp $FAIRSHIP/macro/run_simScript.py .')
   os.system(cmd+" -n "+str(n3)+" -i "+str(ns) + " > log &")
   # print " -n "+str(n3)+" -i "+str(ns) 
   ns += n3
   if i==ncpu: break
   os.chdir('../'+prefix+str(i+1))

def strawEncoding(detid):
 # statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+1000+snb
 # vnb=view number; pnb=plane number; lnb=layer number; snb=straw number
 # statnb = station number. 1,2,3,4 tracking stations, 5 veto station
 vnb = ROOT.Long()
 pnb = ROOT.Long()
 lnb = ROOT.Long()
 snb = ROOT.Long() 
 statnb = ROOT.Long() 
 modules['Strawtubes'].StrawDecode(detid,statnb,vnb,pnb,lnb,snb)
 return [statnb,vnb,pnb,lnb,snb]

def detMap():
  sGeo = ROOT.gGeoManager  
  detList = {}
  for v in sGeo.GetListOfVolumes():
   nm = v.GetName()
   i  = sGeo.FindVolumeFast(nm).GetNumber()
   detList[i] = nm
  return detList

def fitSingleGauss(x,ba=None,be=None):
    name    = 'myGauss_'+x 
    myGauss = h[x].GetListOfFunctions().FindObject(name)
    if not myGauss:
       if not ba : ba = h[x].GetBinCenter(1) 
       if not be : be = h[x].GetBinCenter(h[x].GetNbinsX()) 
       bw    = h[x].GetBinWidth(1) 
       mean  = h[x].GetMean()
       sigma = h[x].GetRMS()
       norm  = h[x].GetEntries()*0.3
       myGauss = TF1(name,'[0]*'+str(bw)+'/([2]*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)+[3]',4)
       myGauss.SetParameter(0,norm)
       myGauss.SetParameter(1,mean)
       myGauss.SetParameter(2,sigma)
       myGauss.SetParameter(3,1.)
       myGauss.SetParName(0,'Signal')
       myGauss.SetParName(1,'Mean')
       myGauss.SetParName(2,'Sigma')
    h[x].Fit(myGauss,'','',ba,be) 


h={}
histlist={}
txt = {}
l={}
logVols = detMap()

def bookHist(detName):
 for mu in ['','_mu','_muV0']:
  tag = detName+mu
  if detName.find('LS')<0:  
   ut.bookHist(h,tag,'x/y '+detName,100,-3.,3.,100,-6.,6.)
  else:  
   ut.bookHist(h,tag,'z phi '+detName,100,-50.,50.,100,-1.,1.)
  ut.bookHist(h,tag+'_E','deposited energy MeV '+detName,100,0.,2.)
  ut.bookHist(h,tag+'_P','particle mom GeV '+detName,500,0.,50.)
  ut.bookHist(h,tag+'_LP','particle mom GeV '+detName,100,0.,1.)
  ut.bookHist(h,tag+'_OP','original particle mom GeV '+detName,400,0.,400.)
  ut.bookHist(h,tag+'_id','particle id '+detName,5001,-2499.5,2499.5)
  ut.bookHist(h,tag+'_mul','multiplicity of hits/tracks '+detName,100,-0.5,99.5)
  ut.bookHist(h,tag+'_evmul','multiplicity of hits/event '+detName,100,-0.5,9999.5)
  ut.bookHist(h,tag+'_origin','r vs z',100,  ztarget,totl,100,0.,12.)
  ut.bookHist(h,tag+'_originmu','r vs z',100,ztarget,totl,100,0.,12.)
 
ut.bookHist(h,'origin','r vs z',100,ztarget,totl,100,0.,15.)
ut.bookHist(h,'borigin','r vs z',100,ztarget,totl,500,0.,30.)
ut.bookHist(h,'porigin','r vs z secondary',100,ztarget,totl,500,0.,30.)
ut.bookHist(h,'mu-inter','r vs z',100,ztarget,totl,50,0.,3.)
ut.bookHist(h,'muonP','muon momentum',100,0.,400.)
ut.bookHist(h,'weight','muon weight',1000,1.E3,1.E6)
ut.bookHist(h,'delx13','x diff first and last point,  mu-',100,-10.,10.)
ut.bookHist(h,'delx-13','x diff first and last point, mu+',100,-10.,10.)
ut.bookHist(h,'deltaElec','energy of delta electrons',100,0.,10.)
ut.bookHist(h,'secondaries','energy of delta electrons',100,0.,10.)
ut.bookHist(h,'prop_deltaElec','energy of delta elec / muon energy',100,0.,1.)
ut.bookHist(h,'dummy','',10,0.,1.)
ut.bookHist(h,'dE','',100,0.,10.,100,0.,10.)
h['dummy'].SetMaximum(10.)

histlistAll = {1:'strawstation_5',2:'strawstation_1',3:'strawstation_4',4:'Ecal',5:'muondet',
               6:'VetoTimeDet',7:'T1LiSc',8:'T2LiSc',9:'T3LiSc',10:'T5LiSc',
              11:'ShipRpc',12:'volHPT',13:'Target',14:'TimeDet',15:'Det2'}
hLiSc = {1:{}}
for i in range(1,7):  hLiSc[1][i] = "T1LiSc_"+str(i)
hLiSc[2] = {}
for i in range(1,48): hLiSc[2][i] = "T2LiSc_"+str(i)
hLiSc[3] = {}
for i in range(1,3): hLiSc[3][i] = "T3LiSc_"+str(i)
hLiSc[5] = {}
for i in range(1,3): hLiSc[5][i] = "T5LiSc_"+str(i)
hMuon = {}
for i in range(0,4): hMuon[i] = "muondet"+str(i)


# start event loop
mom = ROOT.TVector3()
pos = ROOT.TVector3()

def BigEventLoop():
 pid = 1
 for fn in fchain: 
  if os.path.islink(fn): 
    rfn = os.path.realpath(fn).split('eos')[1]
    fn  = ROOT.gSystem.Getenv("EOSSHIP")+'/eos/'+rfn
  elif not os.path.isfile(fn): 
    print("Don't know what to do with",fn)
    1/0 
  if parallel: 
# process files parallel instead of sequential
   processes.append(mp.Process(target=executeOneFile, args=(fn,output,pid) ) )
   pid+=1 
  else:
   processes.append(fn)
# Run processes
 n=0
 for p in processes:
   if parallel: 
       p.start()
       n+=1
   else: executeOneFile(p)
 if parallel:
# Exit the completed processes
   for p in processes: p.join()
# clean histos before reading in the new ones
   for x in h: h[x].Reset()
   print("now, collect the output")
   pid = 1
   for p in processes:
    ut.readHists(h,'tmpHists_'+str(pid)+'.root')
    pid+=1
# compactify liquid scintillator
 for mu in ['','_mu','_muV0']:
  for x in ['','_E','_P','_LP','_OP','_id','_mul','_evmul','_origin','_originmu']:
    for k in [1,2,3,5]: 
     first = True
     for j in hLiSc[k]:
      detName=hLiSc[k][j]
      tag  = detName+mu+x
      newh = detName[0:2]+'LiSc'+mu+x
      if tag not in h: continue 
      if first: 
         h[newh] = h[tag].Clone(newh)
         h[newh].SetTitle( h[tag].GetTitle().split('_')[0])
         first = False
      else:  rc = h[newh].Add(h[tag])
# compactify muon stations
 for mu in ['','_mu','_muV0']:
   for x in ['','_E','_P','_LP','_OP','_id','_mul','_evmul','_origin','_originmu']:
    first = True
    for j in hMuon: 
     detName=hMuon[j]
     tag  = detName+mu+x
     newh = 'muondet'+mu+x
     if first: 
       h[newh] = h[tag].Clone(newh)
       h[newh].SetTitle( h[tag].GetTitle().split(' ')[0]+' '+newh)
       first = False
     else:  rc = h[newh].Add(h[tag])
 
 # make list of hists with entries
 k = 1
 for x in histlistAll:
  if histlistAll[x] in h:
   histlist[k]=histlistAll[x]    
# make cumulative histograms
   for c in ['','_E','_P','_LP','_OP','_id','_mul','_evmul','_origin','_originmu']:
    h[histlist[k]+'_mu'+c].Add(  h[histlist[k]+'_muV0'+c] )
    h[histlist[k]+c].Add(  h[histlist[k]+'_mu'+c] )
    h[histlist[k]+c].SetMinimum(0.) 
    h[histlist[k]+'_mu'+c].SetMinimum(0.) 
    h[histlist[k]+'_muV0'+c] .SetMinimum(0.) 
   k+=1
 nstations = len(histlist)
 makePlots(nstations)
 
def executeOneFile(fn,output=None,pid=None):
  f     = ROOT.TFile.Open(fn)
  sTree = f.cbmsim
  nEvents = sTree.GetEntries()
  if sTree.GetBranch("GeoTracks"): sTree.SetBranchStatus("GeoTracks",0)
  sTree.GetEntry(0)
  hitContainers = [sTree.vetoPoint,sTree.muonPoint,sTree.EcalPointLite,sTree.strawtubesPoint,sTree.ShipRpcPoint,sTree.TargetPoint]
  ntot = 0
  for n in range(nEvents):
   rc = sTree.GetEntry(n)
   theMuon = sTree.MCTrack[0]
   if sTree.MCTrack.GetEntries() > 1: 
    w = sTree.MCTrack[1].GetWeight() # also works for neutrinos
   else: 
    print('should not happen with new files',n,fn)
    w = sTree.MCTrack[0].GetWeight() # also works for neutrinos
   if w==0 : w = 1.
   rc = h['weight'].Fill(w)
   rc = h['muonP'].Fill(theMuon.GetP()/u.GeV,w)
   ntot+=1
   if ntot%10000 == 0 : print('read event',f.GetName(),n)
   hitmult   = {} 
   esum = 0
   for mcp in sTree.MCTrack:
    if mcp.GetMotherId() == 0: # mother is original muon
     E = mcp.GetEnergy()
     if mcp.GetPdgCode() == 11: 
         rc = h['deltaElec'].Fill(E,w)
         esum += E
     rc = h['secondaries'].Fill(E,w)
   rc = h['prop_deltaElec'].Fill(esum/sTree.MCTrack[0].GetP(),w)   # until energy is really made persistent GetEnergy()
   for c in hitContainers:
    for ahit in c:
     if not ahit.GetEnergyLoss()>0: continue
     detID = ahit.GetDetectorID()
     if ahit.GetName() == 'strawtubesPoint':
      tmp = strawEncoding(detID)
      # detName = str(tmp[0]*10000000+tmp[1]*1000000+tmp[2]*100000+tmp[3]*10000)
      detName = "strawstation_"+str(tmp[0])
      x = ahit.GetX()
      y = ahit.GetY()
      E = ahit.GetEnergyLoss()
     elif ahit.GetName() == 'ecalPoint':
      # not needed for lite collection: if abs(ahit.GetPdgCode())==12 or abs(ahit.GetPdgCode())==14  : continue
      detName = 'Ecal' 
      ecal.GetCellCoordForPy(detID,pos)   
      x = pos.X()
      y = pos.Y()
      E = ahit.GetEnergyLoss()
     else: 
      if detID not in logVols:
         detName = c.GetName().replace('Points','')
         if not detName in histlistAll.values(): print(detID,detName,c.GetName()) 
      else: detName = logVols[detID]
      x = ahit.GetX()
      y = ahit.GetY()
      z = ahit.GetZ()
      E = ahit.GetEnergyLoss()
     if detName not in h: bookHist(detName)
     mu=''
     pdgID = -2
     if 'PdgCode' in dir(ahit):   pdgID = ahit.PdgCode()
     trackID = ahit.GetTrackID()
     phit = -100.
     mom = ROOT.TVector3()
     if not trackID < 0: 
       aTrack = sTree.MCTrack[trackID]
       pdgID  = aTrack.GetPdgCode()
       aTrack.GetMomentum(mom) # ! this is not momentum of particle at Calorimeter place
       phit   = mom.Mag()/u.GeV
     if abs(pdgID)==13: mu='_mu'
     if ahit.GetName().find('ecal')<0:
      rc = ahit.Momentum(mom)
      phit = mom.Mag()/u.GeV
     else:
      for ahit in sTree.EcalPoint:
        if ahit.GetTrackID() == trackID:
         rc   = ahit.Momentum(mom)
         phit = mom.Mag()/u.GeV          
     if phit>3 and abs(pdgID)==13: mu='_muV0'
     detName = detName + mu
     if detName.find('LS')<0: rc = h[detName].Fill(x/u.m,y/u.m,w)
     else:                    rc = h[detName].Fill(ahit.GetZ()/u.m,ROOT.TMath.ATan2(y,x)/ROOT.TMath.Pi(),w)
     rc = h[detName+'_E'].Fill(E/u.MeV,w)
     if detName not in hitmult: hitmult[detName] = {-1:0}
     if trackID not in hitmult[detName]: hitmult[detName][trackID] = 0
     hitmult[detName][trackID] +=1
     hitmult[detName][-1]      +=1
     rc = h[detName+'_id'].Fill(pdgID,w)
     rc = h[detName+'_P'].Fill(phit,w)
     rc = h[detName+'_LP'].Fill(phit,w)
     if not trackID < 0: 
       r = ROOT.TMath.Sqrt(aTrack.GetStartX()**2+aTrack.GetStartY()**2)/u.m   
       rc = h['origin'].Fill(aTrack.GetStartZ()/u.m,r,w)
       rc = h[detName+'_origin'].Fill(aTrack.GetStartZ()/u.m,r,w)
       if abs(pdgID)== 13: rc = h[detName+'_originmu'].Fill(aTrack.GetStartZ()/u.m,r,w)
       rc = h['borigin'].Fill(aTrack.GetStartZ()/u.m,r,w)
       rc = aTrack.GetMomentum(mom)
       rc = h[detName+'_OP'].Fill(mom.Mag()/u.GeV,w)
       if trackID > 0: 
         origin(sTree,trackID)
         rc = h['porigin'].Fill(aTrack.GetStartZ()/u.m,ROOT.TMath.Sqrt(aTrack.GetStartX()**2+aTrack.GetStartY()**2)/u.m,w)
       rc = h['mu-inter'].Fill(rz_inter[1]/u.m,rz_inter[0]/u.m,w) 
   for detName in hitmult:
    rc = h[detName+'_evmul'].Fill(hitmult[detName][-1],w) 
    for tr in hitmult[detName]:
      rc = h[detName+'_mul'].Fill(hitmult[detName][tr],w) 
  if output:
   ut.writeHists(h,'tmpHists_'+str(pid)+'.root')
   output.put('ok')
  f.Close()
#
def makePlots(nstations):
 cxcy = {1:[2,1],2:[3,1],3:[2,2],4:[3,2],5:[3,2],6:[3,2],7:[3,3],8:[3,3],9:[3,3],10:[4,3],11:[4,3],12:[4,3],13:[5,3],14:[5,3],15:[5,3]}
 ut.bookCanvas(h,key='ResultsI',title='hit occupancies',  nx=1100,ny=600*cxcy[nstations][1],cx=cxcy[nstations][0],cy=cxcy[nstations][1])
 ut.bookCanvas(h,key='ResultsImu',title='hit occupancies',nx=1100,ny=600*cxcy[nstations][1],cx=cxcy[nstations][0],cy=cxcy[nstations][1])
 ut.bookCanvas(h,key='ResultsImuV0',title='hit occupancies',nx=1100,ny=600*cxcy[nstations][1],cx=cxcy[nstations][0],cy=cxcy[nstations][1])
 ut.bookCanvas(h,key='ResultsII', title='deposited energies',nx=1100,ny=600*cxcy[nstations][1],cx=cxcy[nstations][0],cy=cxcy[nstations][1])
 ut.bookCanvas(h,key='ResultsIII',title='track info',nx=1100,ny=600*cxcy[nstations][1],cx=cxcy[nstations][0],cy=cxcy[nstations][1])
 ut.bookCanvas(h,key='ResultsIV',title='track info',nx=1100,ny=600*cxcy[nstations][1],cx=cxcy[nstations][0],cy=cxcy[nstations][1])
 ut.bookCanvas(h,key='ResultsV',title='origin info',nx=600,ny=400,cx=1,cy=1)
 txt[0] ='occupancy 1sec 5E13pot '
 h['dummy'].Fill(-1)
 nSpills = len(prefixes)
 for i in histlist:
  tc = h['ResultsI'].cd(i)
  hn = histlist[i] 
  if hn not in h: continue 
  h[hn].SetStats(0)
  h[hn].Draw('colz')
  txt[i] = '%5.2G'%(h[hn].GetSumOfWeights()/nSpills)
  l[i] = ROOT.TLatex().DrawLatexNDC(0.15,0.85,txt[i])
#
  hn = histlist[i]+'_mu' 
  tc = h['ResultsImu'].cd(i)
  h[hn].SetStats(0)
  h[hn].Draw('colz')
  txt[i+100] = '%5.2G'%(h[hn].GetSumOfWeights()/nSpills)
  l[i+100] = ROOT.TLatex().DrawLatexNDC(0.15,0.85,txt[i+100])
#
  hn = histlist[i]+'_muV0' 
  tc = h['ResultsImuV0'].cd(i)
  h[hn].SetStats(0)
  h[hn].Draw('colz')
  txt[i+200] = '%5.2G'%(h[hn].GetSumOfWeights()/nSpills)
  l[i+200] = ROOT.TLatex().DrawLatexNDC(0.15,0.85,txt[i+200])
#
 for i in histlist:
  tc = h['ResultsII'].cd(i)
  h[histlist[i]+'_E'].Draw('colz')
#
 for i in histlist:
  tc = h['ResultsIII'].cd(i)
  tc.SetLogy(1)
  hn = histlist[i]
  drawBoth('_P',hn)
  hid = h[hn+'_id']
  print('particle statistics for '+histlist[i])
  for k in range(hid.GetNbinsX()):
   ncont = hid.GetBinContent(k+1)
   pid   = hid.GetBinCenter(k+1) 
   if ncont > 0:
    temp = int(abs(pid)+0.5)*int(pid/abs(pid))
    nm = PDG.GetParticle(temp).GetName() 
    print('%s :%5.2g'%(nm,ncont))
  hid = h[histlist[i]+'_mu_id']
  for k in range(hid.GetNbinsX()):
   ncont = hid.GetBinContent(k+1)
   pid   = hid.GetBinCenter(k+1) 
   if ncont > 0:
    temp = int(abs(pid)+0.5)*int(pid/abs(pid))
    nm = PDG.GetParticle(temp).GetName() 
    print('%s :%5.2g'%(nm,ncont))
#
  tc = h['ResultsV'].cd(1)
  h['origin'].SetStats(0)
  h['origin'].Draw('colz')
#
 for i in histlist:
   tc = h['ResultsIV'].cd(i)
   tc.SetLogy(1)
   hn = histlist[i]
   drawBoth('_OP',hn)
 persistency()
#
def AnaEventLoop():
 ntot = 0
 fout = open('rareEvents.txt','w')
 for fn in fchainRec:
  f = ROOT.TFile(fn)
  if not f.FindObjectAny('cbmsim'): 
   print('skip file ',f.GetName()) 
   continue
  sTree = f.cbmsim
  sTree.GetEvent(0)
  if sTree.GetBranch("GeoTracks"): sTree.SetBranchStatus("GeoTracks",0)
  nEvents = sTree.GetEntries()
  for n in range(nEvents):
   sTree.GetEntry(n)
   if n==0 : print('now at event ',n,f.GetName())
   if sTree.MCTrack.GetEntries() > 1: 
    wg = sTree.MCTrack[1].GetWeight() # also works for neutrinos
   else: 
    wg = sTree.MCTrack[0].GetWeight() # also works for neutrinos
   i = -1
   for atrack in sTree.FitTracks:
    i+=1
    fitStatus   = atrack.getFitStatus()
    if not fitStatus.isFitConverged() : continue
    nmeas = atrack.getNumPoints()
    chi2        = fitStatus.getChi2()/nmeas
    fittedState = atrack.getFittedState()
    P = fittedState.getMomMag()
    fout.write( 'rare event with track %i, %s, %8.2F \n'%(n,f.GetName(),wg) )
    originOfMuon(fout,n,f.GetName(),nEvents)
    fout.write( 'reco %i,%5.3F,%8.2F \n'%(nmeas,chi2,P) )
    mcPartKey = sTree.fitTrack2MC[i]
    mcPart    = sTree.MCTrack[mcPartKey]
    for ahit in sTree.strawtubesPoint:
      if ahit.GetTrackID() == mcPartKey:
       fout.write( 'P when making hit %i, %8.2F \n'%(ahit.PdgCode(),ROOT.TMath.Sqrt(ahit.GetPx()**2+ahit.GetPy()**2+ahit.GetPz()**2)/u.GeV) )  
       break
    if not mcPart : continue
    Ptruth    = mcPart.GetP()
    fout.write( 'Ptruth %i %8.2F \n'%(mcPart.GetPdgCode(),Ptruth/u.GeV) ) 
#
def muDISntuple(fn):
# take as input the rare events
  fout = ROOT.TFile('muDISVetoCounter.root','recreate')
  h['ntuple'] = ROOT.TNtuple("muons","muon flux VetoCounter","id:px:py:pz:x:y:z:w")
  f = ROOT.TFile(fn)
  sTree = f.cbmsim
  nEvents = sTree.GetEntries()
  for n in range(nEvents):
   sTree.GetEntry(n)
   if sTree.MCTrack.GetEntries() > 1: 
      wg = sTree.MCTrack[1].GetWeight()
   else: 
      wg = sTree.MCTrack[0].GetWeight()
   for ahit in sTree.vetoPoint:
     detID = ahit.GetDetectorID()
     if logVols[detID] != 'VetoTimeDet': continue
     pid = ahit.PdgCode()    
     if abs(pid) != 13: continue
     P = ROOT.TMath.Sqrt(ahit.GetPx()**2+ahit.GetPy()**2+ahit.GetPz()**2)
     if P>3/u.GeV:
       h['ntuple'].Fill(float(pid), float(ahit.GetPx()/u.GeV),float(ahit.GetPy()/u.GeV),float(ahit.GetPz()/u.GeV),\
                   float(ahit.GetX()/u.m),float(ahit.GetY()/u.m),float(ahit.GetZ()/u.m),float(wg) )
  fout.cd()
  h['ntuple'].Write()
def analyzeConcrete():
 h['fout'] = ROOT.TFile('muConcrete.root','recreate')
 h['ntuple'] = ROOT.TNtuple("muons","muon flux concrete","id:px:py:pz:x:y:z:w")
 for m in ['','mu','V0']:
  ut.bookHist(h,'conc_hitz'+m,'concrete hit z '+m,100,-100.,100.)
  ut.bookHist(h,'conc_hitzP'+m,'concrete hit z vs P'+m,100,-100.,100.,100,0.,25.)
  ut.bookHist(h,'conc_hity'+m,'concrete hit y '+m,100,-15.,15.)
  ut.bookHist(h,'conc_p'+m,'concrete hit p '+m,1000,0.,400.)
  ut.bookHist(h,'conc_pt'+m,'concrete hit pt '+m,100,0.,20.)
  ut.bookHist(h,'conc_hitzy'+m,'concrete hit zy '+m,100,-100.,100.,100,-15.,15.)
 top = sGeo.GetTopVolume()
 magn = top.GetNode("magyoke_1")
 z0 = magn.GetMatrix().GetTranslation()[2]/u.m
 for fn in fchain:
  f = ROOT.TFile(fn)
  if not f.FindObjectAny('cbmsim'): 
   print('skip file ',f.GetName()) 
   continue
  sTree = f.cbmsim
  nEvents = sTree.GetEntries()
  ROOT.gROOT.cd()
  for n in range(nEvents):
   rc=sTree.GetEntry(n)
   if sTree.MCTrack.GetEntries() > 1: 
      wg = sTree.MCTrack[1].GetWeight() 
   else: 
      wg = sTree.MCTrack[0].GetWeight() 
   for ahit in sTree.vetoPoint:
     detID = ahit.GetDetectorID()
     if logVols[detID] != 'rockD': continue  
     m=''    
     pid = ahit.PdgCode()    
     if abs(pid) == 13: m='mu'
     P = ROOT.TMath.Sqrt(ahit.GetPx()**2+ahit.GetPy()**2+ahit.GetPz()**2)
     if abs(pid) == 13 and P>3/u.GeV: 
       m='V0'
       h['ntuple'].Fill(float(pid), float(ahit.GetPx()/u.GeV),float(ahit.GetPy()/u.GeV),float(ahit.GetPz()/u.GeV),\
                   float(ahit.GetX()/u.m),float(ahit.GetY()/u.m),float(ahit.GetZ()/u.m),float(wg) )
     h['conc_hitz'+m].Fill(ahit.GetZ()/u.m-z0,wg)
     h['conc_hity'+m].Fill(ahit.GetY()/u.m,wg)
     h['conc_p'+m].Fill(P/u.GeV,wg)
     h['conc_hitzP'+m].Fill(ahit.GetZ()/u.m,P/u.GeV,wg)
     Pt = ROOT.TMath.Sqrt(ahit.GetPx()**2+ahit.GetPy()**2)
     h['conc_pt'+m].Fill(Pt/u.GeV,wg)
     h['conc_hitzy'+m].Fill(ahit.GetZ()/u.m-z0,ahit.GetY()/u.m,wg)
 #
     #start = [ahit.GetX()/u.m,ahit.GetY()/u.m,ahit.GetZ()/u.m]
     #direc = [-ahit.GetPx()/P,-ahit.GetPy()/P,-ahit.GetPz()/P]
     #t = - start[0]/direc[0]
     
 ut.bookCanvas(h,key='ResultsV0',title='muons hitting concrete, p>3GeV',nx=1000,ny=600,cx=2,cy=2)  
 ut.bookCanvas(h,key='Resultsmu',title='muons hitting concrete',nx=1000,ny=600,cx=2,cy=2)  
 ut.bookCanvas(h,key='Results',title='hitting concrete',nx=1000,ny=600,cx=2,cy=2)  
 for m in ['','mu','V0']:
  tc = h['Results'+m].cd(1)
  h['conc_hity'+m].Draw()
  tc = h['Results'+m].cd(2)
  h['conc_hitz'+m].Draw()
  tc = h['Results'+m].cd(3)
  tc.SetLogy(1)
  h['conc_pt'+m].Draw()
  tc = h['Results'+m].cd(4)
  tc.SetLogy(1)
  h['conc_p'+m].Draw()
  h['fout'].cd()
  h['ntuple'].Write()

def rareEventEmulsion(fname = 'rareEmulsion.txt'):
 ntot = 0
 fout = open(fname,'w')
 for fn in fchainRec:
  f = ROOT.TFile(fn)
  if not f.FindObjectAny('cbmsim'): 
   print('skip file ',f.GetName()) 
   continue
  sTree = f.cbmsim
  sTree.GetEvent(0)
  if sTree.GetBranch("GeoTracks"): sTree.SetBranchStatus("GeoTracks",0)
  nEvents = sTree.GetEntries()
  for n in range(nEvents):
   sTree.GetEntry(n)
   if n==0 : print('now at event ',n,f.GetName())
   for ahit in sTree.vetoPoint:
     detID = ahit.GetDetectorID()
     if logVols[detID] != 'Emulsion': continue
     x = ahit.GetX()
     y = ahit.GetY()
     z = ahit.GetZ()
     if sTree.MCTrack.GetEntries() > 1: 
      wg = sTree.MCTrack[1].GetWeight() # also works for neutrinos
     else: 
      wg = sTree.MCTrack[0].GetWeight() # also works for neutrinos
     fout.write( 'rare emulsion hit %i, %s, %8.3F, %i \n'%(n,f.GetName(),wg,ahit.PdgCode() ))
     if ahit.GetPz()/u.GeV > 1. :
      fout.write( 'V,P when making hit %8.3F,%8.3F,%8.3F %8.3F,%8.3F,%8.3F (GeV) \n'%(\
                  ahit.GetX()/u.m,ahit.GetY()/u.m,ahit.GetZ()/u.m, \
                  ahit.GetPx()/u.GeV,ahit.GetPy()/u.GeV,ahit.GetPz()/u.GeV ) ) 
     else: 
      fout.write( 'V,P when making hit %8.3F,%8.3F,%8.3F %8.3F,%8.3F,%8.3F (MeV)\n'%(\
                  ahit.GetX()/u.m,ahit.GetY()/u.m,ahit.GetZ()/u.m, \
                  ahit.GetPx()/u.MeV,ahit.GetPy()/u.MeV,ahit.GetPz()/u.MeV ) ) 
     originOfMuon(fout,n,f.GetName(),nEvents)
#
def extractRareEvents(single = None):
 for fn in fchainRec:
  if single :
    if fn.find(str(single)) < 0 : continue
  f = ROOT.TFile(fn)
  if not f.FindObjectAny('cbmsim'): 
   print('skip file ',f.GetName()) 
   continue
  sTree = f.cbmsim
  nEvents = sTree.GetEntries()
  raref = ROOT.TFile(fn.replace(".root","_rare.root"),"recreate")
  newTree = sTree.CloneTree(0)
  for n in range(nEvents):
   sTree.GetEntry(n)
   if n==0 : print('now at event ',n,f.GetName())
# count fitted tracks which have converged and nDF>20:
   n = 0
   for fT in sTree.FitTracks:
    fst = fT.getFitStatus()
    if not fst.isFitConverged(): continue
    if fst.getNdf() < 20: continue
    n+=1
   if n > 0:
    rc = newTree.Fill()
    print('filled newTree',rc)
   sTree.Clear()
  newTree.AutoSave()
  print('   --> events saved:',newTree.GetEntries())
  f.Close() 
  raref.Close() 
#
def extractMuCloseByEvents(single = None):
 mom = ROOT.TVector3()
 pos = ROOT.TVector3()
 golmx = top.GetNode("volGoliath_1").GetMatrix()
 zGol = golmx.GetTranslation()[2]
 for fn in fchainRec:
  if single :
    if fn.find(str(single)) < 0 : continue
  f = ROOT.TFile(fn)
  if not f.FindObjectAny('cbmsim'): 
   print('skip file ',f.GetName()) 
   continue
  sTree = f.cbmsim
  nEvents = sTree.GetEntries()
  raref = ROOT.TFile(fn.replace(".root","_clby.root"),"recreate")
  newTree = sTree.CloneTree(0)
  for n in range(nEvents):
   sTree.GetEntry(n)
   if n==0 : print('now at event ',n,f.GetName())
# look for muons p>3 hitting something
   n = 0
   for c in [sTree.vetoPoint,sTree.strawtubesPoint,sTree.ShipRpcPoint]:
    for ahit in c:
     if abs(ahit.PdgCode())!=13: continue
     ahit.Momentum(mom)
     if mom.Mag()<3. : continue
     ahit.Position(pos)
     if pos.z()<zGol : continue
     n+=1
   if n > 0:
    rc = newTree.Fill()
    # print 'filled newTree',rc
   sTree.Clear()
  newTree.AutoSave()
  print('   --> events saved:',newTree.GetEntries())
  f.Close() 
  raref.Close()
#
def MergeRareEvents(runs=['61','62']):
 for prefix in runs:
  cmd = '$ROOTSYS/bin/hadd rareEvents_'+prefix+'.root -f '
  for fn in fchainRec:
   if fn.find('muon'+prefix)<0 : continue
   fr = fn.replace(".root","_rare.root")
   cmd = cmd + ' '+ fr
  os.system( cmd )
     
#
def persistency():
  printAndCopy(prefix)
  ut.writeHists(h,prefix+".root",plusCanvas=True)

def reDraw(fn):
  if fn.find('root')<0: fn=fn+'.root'
  if 'tc' not in h: h['tc'] = ROOT.TFile(fn)
  for x in ['ResultsI','ResultsII','ResultsImu','ResultsImuV0','ResultsIII','ResultsIV','ResultsV']:
   h[x]=h['tc'].FindObjectAny(x)
   h[x].Draw() 
def printAndCopy(prefix=None):
  if not prefix: prefix = (h['tc'].GetName()).replace('.root','')
  for x in ['ResultsI','ResultsII','ResultsImu','ResultsImuV0','ResultsIII','ResultsIV','ResultsV']:
   h[x].Update()
  if not prefix in os.listdir('.'): os.mkdir(prefix)
  os.chdir(prefix)
  h['ResultsI'].Print(prefix+'Back_occ.png')
  h['ResultsII'].Print(prefix+'Back_depE.png')
  h['ResultsImu'].Print(prefix+'muBack_occ.png')
  h['ResultsImuV0'].Print(prefix+'muV0Back_occ.png')
  h['ResultsIII'].Print(prefix+'Back_P.png')
  h['ResultsIV'].Print(prefix+'Back_OP.png')
  h['ResultsV'].Print(prefix+'origin.png')
  os.chdir("../")
  

def drawBoth(tag,hn):
  n1 = h[hn+'_mu'+tag].GetMaximum()
  n2 = h[hn+tag].GetMaximum()
  if n1>n2: h[hn+tag].SetMaximum(n1)
  h[hn+'_mu'+tag].SetLineColor(4)
  h[hn+tag].SetLineColor(3)
  h[hn+'_mu'+tag].Draw()
  h[hn+tag].Draw('same')


def debugGeoTracks():
 for i in range(sTree.GetEntries()):
   sTree.GetEntry(i)
   n = 0
   for gt in sTree.GeoTracks:
     print(i,n,gt.GetFirstPoint()[2],gt.GetLastPoint()[2],gt.GetParticle().GetPdgCode(),gt.GetParticle().P())
     n+=1
def eventsWithStrawPoints(i):
 sTree = fchain[i].cbmsim
 mom = ROOT.TVector3()
 for i in range(sTree.GetEntries()):
   sTree.GetEntry(i)
   nS = sTree.strawtubesPoint.GetEntries()
   if nS>0:
     mu = sTree.MCTrack[0]
     mu.GetMomentum(mom)
     print(i,nS)
     mom.Print()
     sp = sTree.strawtubesPoint[(max(0,nS-3))]
     sp.Momentum(mom)
     mom.Print()
     print('-----------------------')
def eventsWithEntryPoints(i):
 sTree = fchain[i].cbmsim
 mom = ROOT.TVector3()
 for i in range(sTree.GetEntries()):
   sTree.GetEntry(i)
   np = 0
   for vp in sTree.vetoPoint:   
    detName = logVols[vp. GetDetectorID()]
    if detName== "VetoTimeDet": np+=0 #??
    vp.Momentum(mom)
    print(i,detName,vp.PdgCode())
    mom.Print()
    print('-----------------------')
def depEnergy():
 for n in range(sTree.GetEntries()):
  rc = sTree.GetEntry(n)
  for ahit in sTree.strawtubesPoint:
   dE = ahit.GetEnergyLoss()/u.keV
   rc = ahit.Momentum(mom)
   pa = PDG.GetParticle(ahit.PdgCode())
   mpa = pa.Mass()
   E = ROOT.TMath.Sqrt(mom.Mag2()+mpa**2)
   ekin = E-mpa
   rc = h['dE'].Fill(dE,ekin/u.MeV)
  h['dE'].SetXTitle('keV')
  h['dE'].SetYTitle('MeV')

def originOfMuon(fout,n,fn,nEvents):
      # from fn extract Yandex or CERN/cracow
 ncpu = 9
 x = fn.find('/')
 ni = int(fn[x-1:x])-1
 if nEvents < 100000: 
   fm   = "$SHIPSOFT/data/pythia8_Geant4_onlyMuons.root"   
 else:
   fm = "$SHIPSOFT/data/pythia8_Geant4_Yandex_onlyMuons.root"   
 fmuon = ROOT.TFile(fm)
 ntupl = fmuon.Get("pythia8-Geant4")
 ntot  = ntupl.GetEntries()
 n3    = int(ntot/ncpu)
 N = n3*ni+n
 ntupl.GetEvent(N)
 P = ROOT.TMath.Sqrt(ntupl.pz*ntupl.pz+ntupl.py*ntupl.py+ntupl.px*ntupl.px)
 fout.write('original muon %i, %i, %8.2F \n'%(ntupl.parentid,ntupl.pythiaid,P) )
 fmuon.Close()
#
# BigEventLoop()
# makePlots()
# AnaEventLoop()

# ShipAna
def pers():
  xdisk = '/media/Work/HNL/'
  for x in h:
    if type(h[x])==type(ROOT.TCanvas()): 
      h[x].Update()
      tn = h[x].GetName()+'.png'
      h[x].Print(tn)       
      rpath = os.path.abspath('.').split('/HNL/')[1]
      lp = rpath.split('/') 
      prefix = xdisk
      for i in range(len(lp)):
         if not lp[i] in os.listdir(prefix): os.system('mkdir '+prefix+'/'+lp[i])
         prefix = prefix+'/'+lp[i]    
      os.system('cp '+tn+ ' '+xdisk+rpath)

from operator import itemgetter
def makeNicePrintout(x=['rareEvents_61-62.txt','rareEvents_71-72.txt']):
 result = []
 cor = 1.
 for fn in x:
  f = open(fn)
  recTrack = None
  if fn=="rareEvents_81-102.txt" : cor = 30.
  for lx in f.readlines():
   l = lx.replace('\n','')
   if not l.find('rare event')<0:
      if recTrack: result.append(recTrack)
      tmp = l.split(',')
      w   = tmp[2].replace(' ','')
      ff  = tmp[1].split('/')[0].replace(' ','')
      recTrack = {'w':w,'file':ff}
   elif not l.find('original')<0:
      tmp = l.split(',')
      recTrack['origin']  = tmp[0].split(' ')[2]
      recTrack['pytiaid'] = tmp[1].replace(' ','')
      recTrack['o-mom']   = tmp[2].replace(' ','') 
   elif not l.find('reco ')<0:
      tmp = l.split(',')
      recTrack['nmeas'] = tmp[0].split(' ')[1]
      recTrack['chi2'] = tmp[1]
      recTrack['p_rec'] = tmp[2].replace(' ','') 
   elif not l.find('making')<0:
      tmp = l.split(',')
      recTrack['p_hit'] = tmp[1].replace(' ','')
      recTrack['fp_hit'] = float(tmp[1].replace(' ',''))
   elif not l.find('Ptruth')<0:
      tmp = l.split(' ')
      recTrack['id_hit'] = tmp[1].replace(' ','')
 # print a table
 print('%4s %8s %8s %4s %8s %8s %8s %8s %8s  %8s '%('nr','origin','pythiaID','ID','p_orig','p_hit','chi2','weight','file','cor w')) 
# sort according to p_hit
 tmp = sorted(result, key=itemgetter('fp_hit'))
 muonrate1 = 0
 muonrate2 = 0
 muonrate3 = 0
 for i in range(len(tmp)):
  tr = tmp[i]
  corw = float(tr['w'])/cor
  if float(tr['p_hit'])>1:muonrate1+=corw
  if float(tr['p_hit'])>2:muonrate2+=corw
  if float(tr['p_hit'])>3:muonrate3+=corw
  print('%4i %8s %8s %4s %8s %8s %8s %8s %8s  %8s '%( i,tr['origin'],tr['pytiaid'],tr['id_hit'],tr['o-mom'],tr['p_hit'],tr['chi2'],tr['w'],tr['file'],corw))
 print("guestimate for muonrate above 1GeV = ",muonrate1)
 print("guestimate for muonrate above 2GeV = ",muonrate2)
 print("guestimate for muonrate above 3GeV = ",muonrate3)
#guestimate for muonrate above 1GeV =  56025.4793333
#guestimate for muonrate above 2GeV =  25584.9546667
#guestimate for muonrate above 3GeV =  14792.8113333
 return tmp
#
def readAndMergeHistos(prods):
 for p in prods:
   x=p
   if p.find('.root')<0: x=p+'.root' 
   ut.readHists(h,x)
# make list of hists with entries
 k = 1
 for x in histlistAll:
  if histlistAll[x] in h: 
   histlist[k]=histlistAll[x]
   k+=1
 nstations = len(histlist)
 print("make plots for ",nstations) 
 makePlots(nstations)
 printAndCopy(prods[0].replace('.root',''))

# python -i $HNL/ana_ShipMuon.py 810 811 812 813 814 815 816 817 818 819 820 821 822 823 824 825 826 827 828 829
# python -i $HNL/ana_ShipMuon.py 910 911 912 913 914 915 916 917 918 919 920 921 922 923 924 925 926 927 928 929
# python -i $HNL/ana_ShipMuon.py 1012 1013 1014 1015 1016 1017 1018 1019 1022 1023 1024 1025 1026 1027 1028 1029
# python -i $HNL/ana_ShipMuon.py 634 635 636 637 638 639 640 641 642 643   
# combine all cern-cracow
# python -i $HNL/ana_ShipMuon.py 810 811 812 813 814 815 816 817 818 819 910 911 912 913 914 915 916 917 918 919 1012 1013 1014 1015 1016 1017 1018 1019
# python -i $HNL/ana_ShipMuon.py 820 821 822 823 824 825 826 827 828 829 920 921 922 923 924 925 926 927 928 929 1022 1023 1024 1025 1026 1027 1028 1029
# make muonDIS ntuple: muDISntuple("/media/Data/HNL/muonBackground/rareEvents_81-102.root") -> 'muDISVetoCounter.root'
#                      second step python $FAIRSHIP/muonShieldOptimization/makeMuonDIS.py 1 10000 muDISVetoCounter.root
#                      third step run_simScript.py --MuDIS -n 10 -f  muonDis_1.root
# for concrete
# analyzeConcrete() -> muConcrete.root
