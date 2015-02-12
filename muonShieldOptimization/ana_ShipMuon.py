# analyze muon background /media/Data/HNL/PythiaGeant4Production/pythia8_Geant4_total.root 
import os,ROOT

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
prefixes  = []
withChain = 0
if len(os.sys.argv)>1 : 
 for i in range(1,len(os.sys.argv)):
   for prefix in os.sys.argv[i].split(','):
    if prefix.find('muon')<0:prefix='muon'+prefix
    prefixes.append(prefix) 
    withChain+=1
else: 
 prefixes = ['']

testdir = '.'
if prefixes[0]!='': testdir = prefixes[0]+'1'
# figure out which setup
for f in os.listdir(testdir):
  if not f.find("geofile_full")<0:
     tgeom = ROOT.TGeoManager("Geometry", "Geane geometry")
     tgeom.Import(testdir+'/'+f)
     fGeo = ROOT.gGeoManager  
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

from array import array # gymnastic required by Ecal 
import rootUtils as ut
import shipunit as u
PDG = ROOT.TDatabasePDG.Instance()
from ShipGeoConfig import ConfigRegistry
# init geometry and mag. field
ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy )
# -----Create geometry----------------------------------------------
import shipDet_conf
run = ROOT.FairRunSim()
modules = shipDet_conf.configure(run,ShipGeo)

ecal = modules['Ecal']
EcalX = array('f',[0.])
EcalY = array('f',[0.])
EcalE = array('i',[0])

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
totl = 30.
ztarget = -100.

fchain = []
fchainRec = []
# first time trying to read a chain of Fairship files, doesn't seem to work out of the box, try some tricks.
if withChain>0:
 for prefix in prefixes:
  for i in range(1,10):
   if not prefix+str(i) in os.listdir('.'): continue
   q1 = inputFile1 in os.listdir(prefix+str(i))
   q2 = inputFile2 in os.listdir(prefix+str(i))
   if q1 : inputFile  = inputFile1
   elif q2: inputFile = inputFile2
   else: continue
   fname = prefix+str(i)+'/'+inputFile 
   fchain.append(fname)
   recFile = inputFile.replace('.root','_rec.root')
   if not recFile in os.listdir(prefix+str(i)): continue
   fname = prefix+str(i)+'/'+recFile
   fchainRec.append(fname)
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
  fGeo = ROOT.gGeoManager  
  detList = {}
  for v in fGeo.GetListOfVolumes():
   nm = v.GetName()
   i  = fGeo.FindVolumeFast(nm).GetNumber()
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
  ut.bookHist(h,tag+'_mul','multiplicity of hits/tracks '+detName,10,-0.5,9.5)
  ut.bookHist(h,tag+'_evmul','multiplicity of hits/event '+detName,10,-0.5,9.5)
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

histlistAll = {1:'strawstation_5',2:'strawstation_1',3:'strawstation_4',4:'Ecal',5:'muon',
               6:'lidT1lisci',7:'T1LS',8:'T2LS',9:'T4LS',10:'volDriftLayer5',11:'volDriftLayer',12:'Emulsion',13:'Det2','TimeDet':14}

# start event loop
mom = ROOT.TVector3()
pos = ROOT.TVector3()

def BigEventLoop():
 ntot = 0
 for fn in fchain: 
  f = ROOT.TFile(fn)
  if not f.FindObjectAny('cbmsim'): 
   print 'skip file ',f.GetName() 
   continue
  sTree = f.cbmsim
  nEvents = sTree.GetEntries()
  if sTree.GetBranch("GeoTracks"): sTree.SetBranchStatus("GeoTracks",0)
  sTree.GetEntry(0)
  hitContainers = [sTree.vetoPoint,sTree.muonPoint,sTree.EcalPointLite,sTree.strawtubesPoint,sTree.ShipRpcPoint]
  for n in range(nEvents):
   rc = sTree.GetEntry(n)
   theMuon = sTree.MCTrack[0] # also works for neutrinos
   w = theMuon.GetWeight()
   if w==0 : w = 1.
   rc = h['weight'].Fill(w)
   rc = h['muonP'].Fill(theMuon.GetP()/u.GeV,w)
   ntot+=1
   if ntot%10000 == 0 : print 'read event',f.GetName(),n
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
      detName = logVols[detID]
      x = ahit.GetX()
      y = ahit.GetY()
      z = ahit.GetZ()
      E = ahit.GetEnergyLoss()
     if not h.has_key(detName): bookHist(detName)
     mu=''
     pdgID = -2
     if 'PdgCode' in dir(ahit):   pdgID = ahit.PdgCode()
     trackID = ahit.GetTrackID()
     if not trackID < 0: 
       aTrack = sTree.MCTrack[trackID]
       pdgID  = aTrack.GetPdgCode()
     if abs(pdgID)==13: mu='_mu'
     rc = ahit.Momentum(mom)
     phit = mom.Mag()/u.GeV
     if phit>3 and abs(pdgID)==13: mu='_muV0'
     detName = detName + mu
     if detName.find('LS')<0: rc = h[detName].Fill(x/u.m,y/u.m,w)
     else:                    rc = h[detName].Fill(ahit.GetZ()/u.m,ROOT.TMath.ATan2(y,x)/ROOT.TMath.Pi(),w)
     rc = h[detName+'_E'].Fill(E/u.MeV,w)
     if not hitmult.has_key(detName): hitmult[detName] = {-1:0}
     if not hitmult[detName].has_key(trackID): hitmult[detName][trackID] = 0
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
  f.Close()
# make list of hists with entries
 k = 1
 for x in histlistAll:
  if h.has_key(histlistAll[x]): 
   histlist[k]=histlistAll[x]
# add muons and make total
   rc = h[histlist[k]+'_mu'+'_P'].Add(h[histlist[k]+'_muV0'+'_P'],1.)
   rc = h[histlist[k]+'_mu'+'_OP'].Add(h[histlist[k]+'_muV0'+'_OP'],1.)
   rc = h[histlist[k]+'_mu'].Add(h[histlist[k]+'_muV0'],1.)
   rc = h[histlist[k]].Add(h[histlist[k]+'_mu'],1.)
   k+=1
 nstations = len(histlist)
 makePlots(nstations)
#
def makePlots(nstations):
 cxcy = {1:[2,1],2:[3,1],3:[2,2],4:[3,2],5:[3,2],6:[3,2],7:[3,3],8:[3,3],9:[3,3],10:[4,3],11:[4,3],12:[4,3],13:[5,3],14:[5,3]}
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
  if not h.has_key(hn): continue 
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
  print 'particle statistics for '+histlist[i]
  for k in range(hid.GetNbinsX()):
   ncont = hid.GetBinContent(k+1)
   pid   = hid.GetBinCenter(k+1) 
   if ncont > 0:
    temp = int(abs(pid)+0.5)*int(pid/abs(pid))
    nm = PDG.GetParticle(temp).GetName() 
    print '%s :%5.2g'%(nm,ncont)
  hid = h[histlist[i]+'_mu_id']
  for k in range(hid.GetNbinsX()):
   ncont = hid.GetBinContent(k+1)
   pid   = hid.GetBinCenter(k+1) 
   if ncont > 0:
    temp = int(abs(pid)+0.5)*int(pid/abs(pid))
    nm = PDG.GetParticle(temp).GetName() 
    print '%s :%5.2g'%(nm,ncont)
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
   print 'skip file ',f.GetName() 
   continue
  sTree = f.cbmsim
  sTree.GetEvent(0)
  if sTree.GetBranch("GeoTracks"): sTree.SetBranchStatus("GeoTracks",0)
  nEvents = sTree.GetEntries()
  for n in range(nEvents):
   sTree.GetEntry(n)
   if n==0 : print 'now at event ',n,f.GetName()
   wg = sTree.MCTrack[0].GetWeight()   
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
def analyzeConcrete():
 for m in ['','mu']:
  ut.bookHist(h,'conc_hitz'+m,'concrete hit z '+m,100,-100.,100.)
  ut.bookHist(h,'conc_hity'+m,'concrete hit y '+m,100,-15.,15.)
  ut.bookHist(h,'conc_p'+m,'concrete hit p '+m,100,0.,300.)
  ut.bookHist(h,'conc_pt'+m,'concrete hit pt '+m,100,0.,10.)
  ut.bookHist(h,'conc_hitzy'+m,'concrete hit zy '+m,100,-100.,100.,100,-15.,15.)
 top = fGeo.GetTopVolume()
 magn = top.GetNode("magyoke_1")
 z0 = magn.GetMatrix().GetTranslation()[2]/u.m
 for fn in fchain:
  f = ROOT.TFile(fn)
  if not f.FindObjectAny('cbmsim'): 
   print 'skip file ',f.GetName() 
   continue
  sTree = f.cbmsim
  nEvents = sTree.GetEntries()
  for n in range(nEvents):
   sTree.GetEntry(n)
   wg = sTree.MCTrack[0].GetWeight()   
   for ahit in sTree.vetoPoint:
     detID = ahit.GetDetectorID()
     if logVols[detID] != 'rockD': continue  
     m=''       
     if abs(ahit.PdgCode()) == 13: m='mu'
     h['conc_hitz'+m].Fill(ahit.GetZ()/u.m-z0,wg)
     h['conc_hity'+m].Fill(ahit.GetY()/u.m,wg)
     P = ROOT.TMath.Sqrt(ahit.GetPx()**2+ahit.GetPy()**2+ahit.GetPz()**2)
     h['conc_p'+m].Fill(P/u.GeV,wg)
     Pt = ROOT.TMath.Sqrt(ahit.GetPx()**2+ahit.GetPy()**2)
     h['conc_pt'+m].Fill(Pt/u.GeV,wg)
     h['conc_hitzy'+m].Fill(ahit.GetZ()/u.m-z0,ahit.GetY()/u.m,wg)
 ut.bookCanvas(h,key='Resultsmu',title='muons hitting concrete',nx=1000,ny=600,cx=2,cy=2)  
 ut.bookCanvas(h,key='Results',title='hitting concrete',nx=1000,ny=600,cx=2,cy=2)  
 for m in ['','mu']:
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

def rareEventEmulsion(fname = 'rareEmulsion.txt'):
 ntot = 0
 fout = open(fname,'w')
 for fn in fchainRec:
  f = ROOT.TFile(fn)
  if not f.FindObjectAny('cbmsim'): 
   print 'skip file ',f.GetName() 
   continue
  sTree = f.cbmsim
  sTree.GetEvent(0)
  if sTree.GetBranch("GeoTracks"): sTree.SetBranchStatus("GeoTracks",0)
  nEvents = sTree.GetEntries()
  for n in range(nEvents):
   sTree.GetEntry(n)
   if n==0 : print 'now at event ',n,f.GetName()
   for ahit in sTree.vetoPoint:
     detID = ahit.GetDetectorID()
     if logVols[detID] != 'Emulsion': continue
     x = ahit.GetX()
     y = ahit.GetY()
     z = ahit.GetZ()
     wg = sTree.MCTrack[0].GetWeight()   
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
   print 'skip file ',f.GetName() 
   continue
  sTree = f.cbmsim
  nEvents = sTree.GetEntries()
  raref = ROOT.TFile(fn.replace(".root","_rare.root"),"recreate")
  newTree = sTree.CloneTree(0)
  for n in range(nEvents):
   sTree.GetEntry(n)
   if n==0 : print 'now at event ',n,f.GetName()
   if sTree.FitTracks.GetEntries()>0: 
    rc = newTree.Fill()
    print 'filled newTree',rc
   sTree.Clear()
  newTree.AutoSave()
  print '   --> events saved:',newTree.GetEntries()
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
  if not h.has_key('tc'): h['tc'] = ROOT.TFile(fn)
  for x in ['ResultsI','ResultsII','ResultsImu','ResultsImuV0','ResultsIII','ResultsIV','ResultsV']:
   h[x]=h['tc'].FindObjectAny(x)
   h[x].Draw() 
def printAndCopy(prefix=None):
  if not prefix: prefix = (h['tc'].GetName()).replace('.root','')
  for x in ['ResultsI','ResultsII','ResultsImu','ResultsImuV0','ResultsIII','ResultsIV','ResultsV']:
   h[x].Update()
  if not prefix in os.listdir('/media/Work/HNL'): os.mkdir('/media/Work/HNL/'+prefix)
  h['ResultsI'].Print(prefix+'Back_occ.png')
  h['ResultsII'].Print(prefix+'Back_depE.png')
  h['ResultsImu'].Print(prefix+'muBack_occ.png')
  h['ResultsImuV0'].Print(prefix+'muV0Back_occ.png')
  h['ResultsIII'].Print(prefix+'Back_P.png')
  h['ResultsIV'].Print(prefix+'Back_OP.png')
  h['ResultsV'].Print(prefix+'origin.png')
  os.system('cp '+prefix+'*.png /media/Work/HNL/'+prefix)
  

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
     print i,n,gt.GetFirstPoint()[2],gt.GetLastPoint()[2],gt.GetParticle().GetPdgCode(),gt.GetParticle().P()
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
     print i,nS
     mom.Print()
     sp = sTree.strawtubesPoint[(max(0,nS-3))]
     sp.Momentum(mom)
     mom.Print()
     print '-----------------------'
def eventsWithEntryPoints(i):
 sTree = fchain[i].cbmsim
 mom = ROOT.TVector3()
 for i in range(sTree.GetEntries()):
   sTree.GetEntry(i)
   np = 0
   for vp in sTree.vetoPoint:   
    detName = logVols[vp. GetDetectorID()]
    if detName== "lidT1lisci": np+=0 #??
    vp.Momentum(mom)
    print i,detName,vp.PdgCode()
    mom.Print()
    print '-----------------------'
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
 for fn in x:
  f = open(fn)
  recTrack = None
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
 print '%4s %8s %8s %4s %8s %8s %8s %8s %8s '%('nr','origin','pythiaID','ID','p_orig','p_hit','chi2','weight','file') 
# sort according to p_hit
 tmp = sorted(result, key=itemgetter('fp_hit'))
 for i in range(len(tmp)):
  tr = tmp[i]
  print '%4i %8s %8s %4s %8s %8s %8s %8s %8s '%( i,tr['origin'],tr['pytiaid'],tr['id_hit'],tr['o-mom'],tr['p_hit'],tr['chi2'],tr['w'],tr['file'])
 return tmp

# files without spiral p-beam
# python -i $HNL/ana_ShipMuon.py 61 611 612 613 614 615 616 617 618 619 62 621 622 623 624 625 626 627 628 629
# with
# python -i $HNL/ana_ShipMuon.py 710 711 712 713 714 715 716 717 718 719 720 721 722 723 724 725 726 727 728 729
