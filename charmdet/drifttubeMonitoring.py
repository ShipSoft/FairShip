import ROOT,os,sys
ROOT.gStyle.SetPalette(ROOT.kDarkBodyRadiator)
import shipunit as u
from array import array
if len(sys.argv)<2:
  print "file name required, run/spilldata"
  exit()
fname = sys.argv[1]
f = ROOT.TFile.Open(os.environ['EOSSHIP']+"/eos/experiment/ship/data/muflux/rawdata/"+fname)

#f = ROOT.TFile.Open(os.environ['EOSSHIP']+"/eos/experiment/ship/data/muflux/rawdata/RUN_0C00_2121/SPILLDATA_0C00_0513352240.root")
#f = ROOT.TFile.Open(os.environ['EOSSHIP']+"/eos/experiment/ship/data/muflux/rawdata/RUN_0C00_2121/SPILLDATA_0C00_0513340890.root")
#f = ROOT.TFile.Open(os.environ['EOSSHIP']+"/eos/experiment/ship/data/muflux/rawdata/RUN_0C00_2091/SPILLDATA_0C00_0512761705.root") # 0 field

sTree=f.cbmsim

#rpc
rpc={}

from ShipGeoConfig import ConfigRegistry
ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/charm-geometry_config.py")
import charmDet_conf
run = ROOT.FairRunSim()
run.SetName("TGeant4")  # Transport engine
run.SetOutputFile("dummy")  # Output file
run.SetUserConfig("g4Config_basic.C") # geant4 transport not used, only needed for creating VMC field
rtdb = run.GetRuntimeDb()
modules = charmDet_conf.configure(run,ShipGeo)
# -----Create geometry----------------------------------------------
run.Init()

#geofile =  ROOT.TFile.Open(os.environ['EOSSHIP']+"/eos/experiment/ship/data/muflux/display-data/geo.root")
#sGeo = geofile.FAIRGeom
sGeo = ROOT.gGeoManager
nav = sGeo.GetCurrentNavigator()
top = sGeo.GetTopVolume()
top.SetVisibility(0)
top.Draw('ogl')


for n in range(6):
 rc = nav.cd('/VMuonBox_1/VSensitive_'+str(n))
 vol = nav.GetCurrentNode()
 shape = vol.GetVolume().GetShape()
 local = array('d',[0,0,0])
 globOrigin = array('d',[0,0,0])
 nav.LocalToMaster(local,globOrigin)
 rpc[n] = [shape.GetDX(),shape.GetDY(),globOrigin[2]]
rpcchannels = 184 # estimate for x view

vbot = ROOT.TVector3()
vtop = ROOT.TVector3()
import rootUtils as ut
h={}

import time
def printEventsWithDTandRPC(nstart=0):
 for n in range(nstart,sTree.GetEntries()):
  rc = sTree.GetEvent(n)
  if sTree.Digi_MufluxSpectrometerHits.GetEntries()*sTree.Digi_MuonTaggerHits.GetEntries()>0:
   print "Event number:",n
   plotEvent(n)
   next = raw_input("Next (Ret/Quit): ")         
   if next<>'':  break



hitCollection = {'upstream':[0,ROOT.TGraph()],'downstream':[0,ROOT.TGraph()],'muonTagger':[0,ROOT.TGraph()]}
stereoHits = []
for c in hitCollection: rc=hitCollection[c][1].SetName(c)

def plotEvent(n):
   rc = sTree.GetEvent(n)
   for c in hitCollection: rc=hitCollection[c][1].Set(0)
   global stereoHits
   stereoHits = []
   ut.bookHist(h,'xz','x vs z',500,0.,1000.,100,-150.,150.)
   if not h.has_key('simpleDisplay'): ut.bookCanvas(h,key='simpleDisplay',title='simple event display',nx=1600,ny=1200,cx=1,cy=0)
   rc = h[ 'simpleDisplay'].cd(1)
   h['xz'].SetMarkerStyle(30)
   h['xz'].SetStats(0)
   h['xz'].Draw('b')
   for hit in sTree.Digi_MufluxSpectrometerHits:
    statnb,vnb,pnb,lnb,view = stationInfo(hit)
    # print statnb,vnb,pnb,lnb,view,hit.GetDetectorID()
    rc = hit.MufluxSpectrometerEndPoints(vbot,vtop)
    if view != '_x':
      stereoHit = ROOT.TGraph()
      stereoHit.SetPoint(0,vbot[2],vbot[0])
      stereoHit.SetPoint(1,vtop[2],vtop[0])
      stereoHits.append(stereoHit)
      continue
    if statnb<3:  
     c = hitCollection['upstream'] 
     rc = c[1].SetPoint(c[0],vbot[2],vbot[0])
     c[0]+=1 
    else:
     c = hitCollection['downstream'] 
     rc = c[1].SetPoint(c[0],vbot[2],vbot[0])
     c[0]+=1
   c = hitCollection['muonTagger'] 
   for hit in sTree.Digi_MuonTaggerHits:
    channelID = hit.GetDetectorID()
    statnb = channelID/10000
    view   = (channelID-10000*statnb)/1000
    channel = channelID%1000
    if view == 1:
    #poor man geometry , probably completly wrong
     x = +rpc[statnb][0] - 2*rpc[statnb][0]/rpcchannels*channel
     rc = c[1].SetPoint(c[0],rpc[statnb][2],x)
     c[0]+=1
   hitCollection['downstream'][1].SetMarkerColor(ROOT.kRed)
   hitCollection['upstream'][1].SetMarkerColor(ROOT.kBlue)
   hitCollection['muonTagger'][1].SetMarkerColor(ROOT.kGreen)
   for c in hitCollection: rc=hitCollection[c][1].SetMarkerStyle(30)
   for c in hitCollection:
     if hitCollection[c][1].GetN()<1: continue
     rc=hitCollection[c][1].Draw('sameP')
     h['display:'+c]=hitCollection[c][1]
   for g in stereoHits:
     g.SetLineWidth(2)
     g.Draw('same')
   h[ 'simpleDisplay'].Update()

def stationInfo(hit):
 detid = hit.GetDetectorID()
 statnb = detid/10000000; 
 vnb =  (detid - statnb*10000000)/1000000
 pnb =  (detid - statnb*10000000 - vnb*1000000)/100000
 lnb =  (detid - statnb*10000000 - vnb*1000000 - pnb*100000)/10000
 view = "_x"   
 if vnb==0 and statnb==2: view = "_v"
 if vnb==1 and statnb==1: view = "_u"
 if pnb>1:
   print "something wrong with detector id",detid
   pnb = 0
 return statnb,vnb,pnb,lnb,view

xLayers = {}
channels = {}
for s in range(1,5):
 xLayers[s]={}
 channels[s]={}
 for p in range(2):
  xLayers[s][p]={}
  channels[s][p]={}
  for l in range(2):
   xLayers[s][p][l]={}
   channels[s][p][l]={}
   for view in ['_x','_u','_v']:
    ut.bookHist(h,str(1000*s+100*p+10*l)+view,'hit map station'+str(s)+' plane'+str(p)+' layer '+str(l)+view,50,-0.5,49.5)
    ut.bookHist(h,"TDC"+str(1000*s+100*p+10*l)+view,'TDC station'+str(s)+' plane'+str(p)+' layer '+str(l)+view,100,0.,3000.)
    xLayers[s][p][l][view]=h[str(1000*s+100*p+10*l)+view]
    channels[s][p][l][view]=12
    if s>2: channels[s][p][l][view]=48

noiseThreshold=5
noisyChannels=[]


modid=[10002001,10112012,11002001,11112012,20002001,20112012,21002001,21112012,30002001,30112048,40002001,40112048]
top = ROOT.TVector3()
bot = ROOT.TVector3()
z4=0.
z5=0.
for id in modid:
    hit = ROOT.MufluxSpectrometerHit(id,0)
    rc = hit.MufluxSpectrometerEndPoints(top,bot)
    if id==21112012: z4=(bot.z()+top.z())/2.
    if id==30002001: z5=(bot.z()+top.z())/2.
zgoliath=(z5+z4)/2.

def sortHits(event):
 spectrHitsSorted = {'_x':{1:[],2:[],3:[],4:[]},'_u':{1:[],2:[],3:[],4:[]},'_v':{1:[],2:[],3:[],4:[]}}
 for hit in event.Digi_MufluxSpectrometerHits:
   statnb,vnb,pnb,lnb,view = stationInfo(hit)
   spectrHitsSorted[view][statnb].append(hit)
 return spectrHitsSorted

def plotHitMaps():
 for event in sTree:
  for hit in event.Digi_MufluxSpectrometerHits:
   s,v,p,l,view = stationInfo(hit)
   rc = xLayers[s][p][l][view].Fill(hit.GetDetectorID()%1000)
   rc = h['TDC'+xLayers[s][p][l][view].GetName()].Fill(hit.GetDigi())
  if not h.has_key('hitMapsX'): ut.bookCanvas(h,key='hitMapsX',title='Hit Maps All Layers',nx=1600,ny=1200,cx=4,cy=6)
  if not h.has_key('TDCMapsX'): ut.bookCanvas(h,key='TDCMapsX',title='TDC Maps All Layers',nx=1600,ny=1200,cx=4,cy=6)
 j=0
 for s in range(1,5):
  for view in ['_x','_u','_v']:
   for p in range(2):
    for l in range(2):
     if not xLayers[s][p][l].has_key(view):continue
     if s>2 and view != '_x': continue
     if s==1 and view == '_v': continue
     if s==2 and view == '_u': continue
     j+=1
     rc = h['hitMapsX'].cd(j)
     xLayers[s][p][l][view].Draw()
     rc = h['TDCMapsX'].cd(j)
     h['TDC'+xLayers[s][p][l][view].GetName()].Draw()
     mean = xLayers[s][p][l][view].GetEntries()/channels[s][p][l][view]
     for i in range(int(xLayers[s][p][l][view].GetEntries())):
      if xLayers[s][p][l][view].GetBinContent(i) > noiseThreshold * mean:
          n = xLayers[s][p][l][view].GetName().split('_')[0]
          noisyChannels.append(int(n)*100+i)
 print "list of noisy channels"
 for n in noisyChannels: print n

def printScalers():
   ut.bookHist(h,'rate','rate',100,-0.5,99.5)
   if not h.has_key('rates'): ut.bookCanvas(h,key='rates',title='Rates',nx=600,ny=400,cx=1,cy=1)
   rc = h['rates'].cd(1)
   scalers = f.scalers
   if not scalers:
     print "no scalers in this file"
     return
   scalers.GetEntry(0)
   for x in scalers.GetListOfBranches():
    name = x.GetName()
    s = eval('scalers.'+name)
    if name!='slices': print "%20s :%8i"%(name,s)
    else:
      for n in range(s.size()):
        rc=h['rate'].Fill(n,s[n])
   h['rate'].Draw('hist')

def zCentre():
 ut.bookHist(h,'xs','x vs z',500,0.,800.,100,-150.,150.)
 ut.bookHist(h,'xss','x vs station',4,0.5,4.5,100,-150.,150.)
 ut.bookHist(h,'wss','wire vs station',4,0.5,4.5,100, -0.5,99.5)
 ut.bookHist(h,'center','z crossing',500,0.,500.)
 ut.bookHist(h,'delx','delta x',200,-200.,200.)
 ut.bookHist(h,'delT3','extr to T3',100,-100.,100.)
 ut.bookHist(h,'delT2','extr to T2',100,-100.,100.)
 ut.bookHist(h,'delT1','extr to T1',100,-100.,100.)
 for event in sTree:
  spectrHitsSorted = sortHits(event)
  X = {1:0,2:0,3:0,4:0}
  Z = {1:0,2:0,3:0,4:0}
  nH  = {1:0,2:0,3:0,4:0}
  passed = True
  for s in range(1,5):
   for hit in spectrHitsSorted['_x'][s]:
     rc = hit.MufluxSpectrometerEndPoints(vbot,vtop)
     rc = h['xs'].Fill( (vbot[2]+vtop[2])/2.,(vbot[0]+vtop[2])/2.)
     rc = h['xss'].Fill( s,(vbot[0]+vtop[2])/2.)
     wire = hit.GetDetectorID()%1000
     rc = h['wss'].Fill(s,wire)
     statnb,vnb,pnb,lnb,view = stationInfo(hit)
     mychannel = (1000*statnb+100*pnb+10*lnb)*100+wire
     if mychannel in noisyChannels:
       continue  
     X[s]+=vbot[0]
     Z[s]+=vbot[2]
     nH[s]+=1
   if nH[s]<3 or nH[s]>6: passed = False
   if not passed: break
   Z[s]=Z[s]/float(nH[s])
   X[s]=X[s]/float(nH[s])
  if not passed: continue
  slopeA = (X[2]-X[1])/(Z[2]-Z[1])
  slopeB = (X[4]-X[3])/(Z[4]-Z[3])
  bA = X[1]-slopeA*Z[1]
  bB = X[3]-slopeB*Z[3]
  zC = (bB-bA)/(slopeA-slopeB+1E-10)
  rc = h['center'].Fill(zC)
  x1 = zgoliath*slopeA+bA
  x2 = zgoliath*slopeB+bB
  rc = h['delx'].Fill(x2-x1)
  rc = h['delT3'].Fill( slopeA*Z[3]+bA-X[3])
  delT1 = slopeB*Z[1]+bB-X[1]
  rc = h['delT1'].Fill( delT1 )
  if delT1 > -20 and delT1 < 10:
   delT2 = slopeB*Z[2]+bB-X[2]
   rc = h['delT2'].Fill( delT2 )
   #if delT2<-18 and delT2>-22 or delT2<38 and delT2> 30:
   #  txt = ''
   #  for hit in spectrHitsSorted['_x'][2]: txt+=str(hit.GetDetectorID())+" "
   #  print delT2,  txt
  
 if not h.has_key('magnetX'): ut.bookCanvas(h,key='magnetX',title='Tracks crossing at magnet',nx=1600,ny=600,cx=3,cy=2)
 h['magnetX'].cd(1)
 h['delx'].Draw()
 h['magnetX'].cd(2)
 h['center'].Draw()
 h['magnetX'].cd(4)
 h['delT3'].Draw()
 h['magnetX'].cd(5)
 h['delT1'].Draw()
 h['magnetX'].cd(6)
 h['delT2'].Draw()

def plotRPCHitmap():
 ut.bookHist(h,'rpcHitmap','rpc Hitmaps',60,-0.5,59.5)
 for n in range(1,6):
  for l in range(2):
    ut.bookHist(h,'rpcHitmap'+str(n)+str(l),'rpc Hitmaps station '+str(n)+'layer '+str(l),200,-0.5,199.5)
 for event in sTree:
    for m in event.Digi_MuonTaggerHits:
      layer = m.GetDetectorID()/1000
      rc = h['rpcHitmap'].Fill(layer)
      channel = m.GetDetectorID()%1000
      rc = h['rpcHitmap'+str(layer)].Fill(channel)
 if not h.has_key('rpcPlot'): ut.bookCanvas(h,key='rpcPlot',title='RPC Hitmaps',nx=1200,ny=600,cx=4,cy=3)
 j=0
 for n in range(1,6):
  for l in range(2):
    j+=1
    rc = h['rpcPlot'].cd(j)
    h['rpcHitmap'+str(n)+str(l)].Draw()
 j+=1
 h['rpcHitmap'].Draw()

from array import array

gMan  = ROOT.gGeoManager
geoMat =  ROOT.genfit.TGeoMaterialInterface()
#
bfield = ROOT.genfit.FairShipFields()
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
fitter = ROOT.genfit.DAF()
fitter.setMaxIterations(50)
# fitter.setDebugLvl(1) # produces lot of printout
def RT(s,t):
# rt relation, drift time to distance, drift time?
  tMinAndTmax = {1:[550,1800],2:[550,1800],3:[550,2400],4:[550,2400]}
  #If you have a clean drift-time spectrum you get the rt-relation for each time bin by dividing the sum of the histogram from 0 to that bin by the total integral, 
  # multiplied with the tube radius, which is 1.815 cm (inner tube radius).
  # Since the gas conditions were not as stable as before, we probably have to have individual calibrations for the different 
  # modules for different times. Also, the readout cables for T1/2 are a little shorter than for T3/4, which will shift the position of the dt spectrum a little.
  r = ShipGeo.MufluxSpectrometer.InnerTubeDiameter/2. #  = 3.63*u.cm 
  t0_corr = t-tMinAndTmax[s][0]
  if t0_corr<0: t0_corr=0
  return t0_corr * r / (tMinAndTmax[s][1]-tMinAndTmax[s][0])

# from TrackExtrapolateTool
parallelToZ = ROOT.TVector3(0., 0., 1.) 
def extrapolateToPlane(fT,z):
# etrapolate to a plane perpendicular to beam direction (z)
  rc,pos,mom = False,None,None
  fst = fT.getFitStatus()
  if fst.isFitConverged():
# find closest measurement
   mClose = 0
   mZmin = 999999.
   for m in [0,fT.getNumPointsWithMeasurement()/2,fT.getNumPointsWithMeasurement()-1]:
    Pos = fT.getFittedState(m).getPos()
    if abs(z-Pos.z())<mZmin:
      mZmin = abs(z-Pos.z())
      mClose = m
    fstate =  fT.getFittedState(mClose)
    NewPosition = ROOT.TVector3(0., 0., z) 
    rep    = ROOT.genfit.RKTrackRep(fstate.getPDG() ) 
    state  = ROOT.genfit.StateOnPlane(rep) 
    pos,mom = fstate.getPos(),fstate.getMom()
    rep.setPosMom(state,pos,mom) 
    try:    
      rep.extrapolateToPlane(state, NewPosition, parallelToZ )
      pos,mom = state.getPos(),state.getMom()
      rc = True 
    except: 
      # print 'error with extrapolation: z=',z/u.m,'m',pos.X(),pos.Y(),pos.Z(),mom.X(),mom.Y(),mom.Z()
      pass
  return rc,pos,mom
def fitTracks(nMax=-1,withDisplay=False):
# select special clean events for testing track fit
 ut.bookHist(h,'p/pt','momentum vs Pt (GeV)',400,0.,400.,100,0.,10.)
 ut.bookHist(h,'chi2','chi2/nDoF',100,0.,25.)
 ut.bookHist(h,'Nmeasurements','number of measurements used',25,-0.5,24.5)
 n=-1
 for event in sTree:
   if nMax==0: break
   n+=1
   spectrHitsSorted = sortHits(event)
   nH  = {1:0,2:0,3:0,4:0}
   passed = True
   for s in range(1,5):
    for hit in spectrHitsSorted['_x'][s]:  nH[s]+=1
    if nH[s]<3 or nH[s]>6: passed = False
   nu = 0
   for hit in spectrHitsSorted['_u'][1]:  nu+=1
   if nu<3 or nu>6: passed = False
   nv = 0
   for hit in spectrHitsSorted['_v'][2]:  nv+=1
   if nv<3 or nv>6: passed = False
   if not passed: continue
   theTrack = makeTracks()
   if type(theTrack)==type(1): 
     # print "event rejected",theTrack,n
     continue
   elif withDisplay:
     plotEvent(n)
     zstart = 0
     nPoints = 100
     delz = 1000./nPoints
     h['dispTrack'] = ROOT.TGraph(nPoints)
     for nP in range(nPoints):
      zstart+=delz
      rc,pos,mom = extrapolateToPlane(theTrack,zstart)
      if not rc: print "extrap failed"
      else: h['dispTrack'].SetPoint(nP,pos[2],pos[0])
      if nP ==0:
        fitStatus = theTrack.getFitStatus()
        print "trackinfoP/Pt/chi2/DoF/Ndf:%6.2F %6.2F %6.2F %6.2F"%(mom.Mag(),mom.Pt(),fitStatus.getChi2()/fitStatus.getNdf(),fitStatus.getNdf())
     h['dispTrack'].SetLineColor(ROOT.kMagenta)
     h['dispTrack'].SetLineWidth(2)
     h['simpleDisplay'].cd(1)
     h['dispTrack'].Draw('same')
     h[ 'simpleDisplay'].Update()
     next = raw_input("Next (Ret/Quit): ")         
     if next<>'':  break
   nMax-=1
 ut.bookCanvas(h,key='mom',title='trackfit',nx=1200,ny=600,cx=2,cy=2)
 rc = h['mom'].cd(1)
 h['p/pt'].SetStats(0)
 rc = h['p/pt'].Draw('colz')
 rc = h['mom'].cd(3)
 h['chi2'].Draw()
 rc = h['mom'].cd(4)
 h['Nmeasurements'].Draw()

sigma_spatial = ShipGeo.MufluxSpectrometer.TubePitch/ROOT.TMath.Sqrt(12)

def makeTracks():
# need measurements
   hitPosLists={}
   trID = 0
   posM = ROOT.TVector3(0, 0, 20.)
   momM = ROOT.TVector3(0,0,3.*u.GeV)
# approximate covariance
   covM = ROOT.TMatrixDSym(6)
   resolution = sigma_spatial
   for  i in range(3):   covM[i][i] = resolution*resolution
   covM[0][0]=resolution*resolution*100.
   for  i in range(3,6): covM[i][i] = ROOT.TMath.Power(resolution / (4.*2.) / ROOT.TMath.Sqrt(3), 2)
# trackrep
   theTrack={13:[0,True],-13:[0,True]}   # not sure if it is required, but had the feeling it fits only one charge
   for pdg in theTrack: # 
    rep = ROOT.genfit.RKTrackRep(pdg)
# start state
    state = ROOT.genfit.MeasuredStateOnPlane(rep)
    rep.setPosMomCov(state, posM, momM, covM)
# create track
    seedState = ROOT.TVectorD(6)
    seedCov   = ROOT.TMatrixDSym(6)
    rep.get6DStateCov(state, seedState, seedCov)
    theTrack[pdg][0] = ROOT.genfit.Track(rep, seedState, seedCov)
    hitCov = ROOT.TMatrixDSym(7)
    hitCov[6][6] = resolution*resolution
    for hit in sTree.Digi_MufluxSpectrometerHits:
      rc = hit.MufluxSpectrometerEndPoints(vbot,vtop)
      tdc = hit.GetDigi()
      distance = RT(hit.GetDetectorID()/10000000,tdc) 
      tmp = array('d',[vtop[0],vtop[1],vtop[2],vbot[0],vbot[1],vbot[2],distance])
      m = ROOT.TVectorD(7,tmp)
      tp = ROOT.genfit.TrackPoint(theTrack[pdg][0]) # note how the point is told which track it belongs to 
      measurement = ROOT.genfit.WireMeasurement(m,hitCov,1,6,tp) # the measurement is told which trackpoint it belongs to
      measurement.setMaxDistance(ShipGeo.MufluxSpectrometer.TubePitch) 
      tp.addRawMeasurement(measurement) # package measurement in the TrackPoint                                          
      theTrack[pdg][0].insertPoint(tp)  # add point to Track
    if not theTrack[pdg][0].checkConsistency():
      theTrack[pdg][1] = False
      continue
# do the fit
    try:  fitter.processTrack(theTrack[pdg][0]) # processTrackWithRep(theTrack,rep,True)
    except:   
      theTrack[pdg][1] = False
      continue
    fitStatus   = theTrack[pdg][0].getFitStatus()
     # print "Fit result:",fitStatus.isFitConverged(),nmeas,chi2
    if not fitStatus.isFitConverged():
      theTrack[pdg][1] = False
      continue
# find best fitted solution
   maxChi2 = 1E30
   charge = 0
   for pdg in theTrack:
     if theTrack[pdg][1]:
       fitStatus   = theTrack[pdg][0].getFitStatus()
       chi2 = fitStatus.getChi2()/fitStatus.getNdf()
       if chi2<maxChi2:
        charge = pdg
        maxChi2 = chi2
   if charge != 0:
     fitStatus   = theTrack[charge][0].getFitStatus()
     rc = h['Nmeasurements'].Fill(fitStatus.getNdf())
     if fitStatus.getNdf() < 12:  return -2 
     fittedState = theTrack[charge][0].getFittedState()
     P = fittedState.getMomMag()
     Px,Py,Pz = fittedState.getMom().x(),fittedState.getMom().y(),fittedState.getMom().z()
     rc = h['p/pt'].Fill(P,ROOT.TMath.Sqrt(Px*Px+Py*Py))
     rc = h['chi2'].Fill(fitStatus.getChi2()/fitStatus.getNdf())
     return theTrack[charge][0]
   else: return -1

def testT0():
 ut.bookHist(h,'means0','mean vs s0',100,0.,3000.,100,0.,3000.)
 ut.bookHist(h,'means1','mean vs s1',100,0.,3000.,100,0.,3000.)
 ut.bookHist(h,'means2','mean vs s2',100,0.,3000.,100,0.,3000.)
 for event in sTree:
    sumOfTDCs = 0
    if event.Digi_MufluxSpectrometerHits.GetEntries() < 15 or event.Digi_MufluxSpectrometerHits.GetEntries() > 30: continue
    for m in event.Digi_MufluxSpectrometerHits:
      sumOfTDCs+=m.GetDigi()
    mean = sumOfTDCs/float(event.Digi_MufluxSpectrometerHits.GetEntries())
    if event.Digi_ScintillatorHits.GetEntries()==0:
      print "no scint"
    else:
     rc = h['means0'].Fill(mean,event.Digi_ScintillatorHits[0].GetDigi())
     rc = h['means1'].Fill(mean,event.Digi_ScintillatorHits[1].GetDigi())
     if event.Digi_ScintillatorHits.GetEntries()>2:
      rc = h['means2'].Fill(mean,event.Digi_ScintillatorHits[2].GetDigi())

print "existing methods"
print " --- plotHitMaps(): hitmaps / layer, TDC / layer, together with list of noisy channels"
print " --- plotEvent(n) : very basic event display, just x hits in x/z projection" 
print " --- plotRPCHitmap() : basic plots for RPC "
print " --- fitTracks(100) and fitTracks(100,True) with Display"
print " --- printScalers()"
print " --- zCentre() : extrapolation of straight tracks upstream / downstream to magnet centre"


