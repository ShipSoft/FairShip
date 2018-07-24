import ROOT,os,sys
ROOT.gStyle.SetPalette(ROOT.kDarkBodyRadiator)
import shipunit as u
from array import array
if len(sys.argv)<2:
  print "file name required, run/spilldata"
  exit()
fname = sys.argv[1]
if fname.find('rawdata')<0:
 f = ROOT.TFile.Open(os.environ['EOSSHIP']+"/eos/experiment/ship/data/muflux/rawdata/"+fname)
else:
 f = ROOT.TFile.Open(fname)
#f = ROOT.TFile.Open(os.environ['EOSSHIP']+"/eos/experiment/ship/data/muflux/rawdata/RUN_0C00_2121/SPILLDATA_0C00_0513352240.root")
#f = ROOT.TFile.Open(os.environ['EOSSHIP']+"/eos/experiment/ship/data/muflux/rawdata/RUN_0C00_2121/SPILLDATA_0C00_0513340890.root")
#f = ROOT.TFile.Open(os.environ['EOSSHIP']+"/eos/experiment/ship/data/muflux/rawdata/RUN_0C00_2091/SPILLDATA_0C00_0512761705.root") # 0 field

sTree=f.cbmsim

#rpc
rpc={}
DT={}

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

sGeo = ROOT.gGeoManager
nav = sGeo.GetCurrentNavigator()
top = sGeo.GetTopVolume()
top.SetVisibility(0)
top.Draw('ogl')

saveGeofile = True
import saveBasicParameters
if saveGeofile:
 run.CreateGeometryFile("muflux_geofile.root")
# save ShipGeo dictionary in geofile
 saveBasicParameters.execute("muflux_geofile.root",ShipGeo)

modid=[10002001,10112012,11002001,11112012,20002001,20112012,21002001,21112012,30002001,30112048,40002001,40112048]

for n in range(1,5):
 for x in top.GetNodes(): 
   if x.GetName().find('volDriftTube')<0: continue
   for y in x.GetVolume().GetNodes():
    if y.GetName().find('plane')<0: continue
    for z in y.GetVolume().GetNodes():
      rc = nav.cd('/'+x.GetName()+'/'+y.GetName()+'/'+z.GetName())
      vol = nav.GetCurrentNode()
      shape = vol.GetVolume().GetShape()
      local = array('d',[0,0,0])
      globOrigin = array('d',[0,0,0])
      nav.LocalToMaster(local,globOrigin)
      DT[z.GetName()] = [shape.GetDX(),shape.GetDY(),globOrigin[2]]

vbot = ROOT.TVector3()
vtop = ROOT.TVector3()
import rootUtils as ut
h={}
h['dispTrack3D']=[]
h['dispTrack']=[]
h['dispTrackY']=[]

import time
def printEventsWithDTandRPC(nstart=0):
 for n in range(nstart,sTree.GetEntries()):
  rc = sTree.GetEvent(n)
  if sTree.Digi_MufluxSpectrometerHits.GetEntries()*sTree.Digi_MuonTaggerHits.GetEntries()>0:
   print "Event number:",n
   plotEvent(n)
   next = raw_input("Next (Ret/Quit): ")         
   if next<>'':  break
h['hitCollection']={}

def dispTrack3D(theTrack):
     zstart = 0
     nPoints = 100
     delz = 1000./nPoints
     nt = len(h['dispTrack3D'])
     h['dispTrack3D'].append( ROOT.TPolyLine3D(nPoints) )
     h['dispTrack3D'][nt].SetLineWidth(3)
     h['dispTrack3D'][nt].SetLineColor(ROOT.kBlack)
     for nP in range(nPoints):
      zstart+=delz
      rc,pos,mom = extrapolateToPlane(theTrack,zstart)
      if not rc: print "extrap failed"
      else: 
        h['dispTrack3D'][nt].SetPoint(nP,pos[0],pos[1],pos[2])
     rc = ROOT.gROOT.FindObject('c1').cd()
     h['dispTrack3D'][nt].Draw('oglsame')
     rc = ROOT.gROOT.FindObject('c1').Update()

def plotEvent(n):
   h['dispTrack']=[]
   h['dispTrack3D']=[]
   h['dispTrackY']=[]
   rc = sTree.GetEvent(n)
   h['hitCollection']= {'upstream':[0,ROOT.TGraph()],'downstream':[0,ROOT.TGraph()],'muonTagger':[0,ROOT.TGraph()]}
   h['stereoHits'] = []
   for c in h['hitCollection']: rc=h['hitCollection'][c][1].SetName(c)
   for c in h['hitCollection']: rc=h['hitCollection'][c][1].Set(0)
   ut.bookHist(h,'xz','x (y) vs z',500,0.,1200.,100,-150.,150.)
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
      h['stereoHits'].append(stereoHit)
      continue
    if statnb<3:  
     c = h['hitCollection']['upstream'] 
     rc = c[1].SetPoint(c[0],vbot[2],vbot[0])
     c[0]+=1 
    else:
     c = h['hitCollection']['downstream'] 
     rc = c[1].SetPoint(c[0],vbot[2],vbot[0])
     c[0]+=1
   c = h['hitCollection']['muonTagger'] 
   for hit in sTree.Digi_MuonTaggerHits:
    channelID = hit.GetDetectorID()
    statnb = channelID/10000
    view   = (channelID-10000*statnb)/1000
    channel = channelID%1000
    if view == 1:
     hit.EndPoints(vtop,vbot)
     x,z =  (vtop[0]+vbot[0])/2.,(vtop[2]+vbot[2])/2.
     rc = c[1].SetPoint(c[0],z,x)
     c[0]+=1
   h['hitCollection']['downstream'][1].SetMarkerColor(ROOT.kRed)
   h['hitCollection']['upstream'][1].SetMarkerColor(ROOT.kBlue)
   h['hitCollection']['muonTagger'][1].SetMarkerColor(ROOT.kGreen)
   for c in h['hitCollection']: rc=h['hitCollection'][c][1].SetMarkerStyle(30)
   for c in h['hitCollection']:
     if h['hitCollection'][c][1].GetN()<1: continue
     rc=h['hitCollection'][c][1].Draw('sameP')
     h['display:'+c]=h['hitCollection'][c][1]
   for g in h['stereoHits']:
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


top = ROOT.TVector3()
bot = ROOT.TVector3()
z4=0.
z5=0.
for detid in modid:
    hit = ROOT.MufluxSpectrometerHit(detid,0)
    rc = hit.MufluxSpectrometerEndPoints(top,bot)
    if detid==21112012: z4=(bot.z()+top.z())/2.
    if detid==30002001: z5=(bot.z()+top.z())/2.
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
     if s==1 and view == '_v'or s==2 and view == '_u': continue
     j+=1
     rc = h['hitMapsX'].cd(j)
     xLayers[s][p][l][view].Draw()
     rc = h['TDCMapsX'].cd(j)
     h['TDC'+xLayers[s][p][l][view].GetName()].Draw()
     mean = xLayers[s][p][l][view].GetEntries()/channels[s][p][l][view]
     for i in range(1,int(xLayers[s][p][l][view].GetEntries())+1):
      if xLayers[s][p][l][view].GetBinContent(i) > noiseThreshold * mean:
        v = 0
        if s==2 and view == "_x": v = 1
        if s==1 and view == "_u": v = 1
        myDetID = s * 10000000 + v * 1000000 + p * 100000 + l*10000
        noisyChannels.append(myDetID+i)
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

ut.bookHist(h,'delx','delta x',200,-50.,50.)
def zCentre():
 ut.bookHist(h,'xs','x vs z',500,0.,800.,100,-150.,150.)
 ut.bookHist(h,'xss','x vs station',4,0.5,4.5,100,-150.,150.)
 ut.bookHist(h,'wss','wire vs station',4,0.5,4.5,100, -0.5,99.5)
 ut.bookHist(h,'center','z crossing',500,0.,500.)
 ut.bookHist(h,'delzCentrT3','extr to T3',100,-100.,100.)
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
     rc = h['xs'].Fill( (vbot[2]+vtop[2])/2.,(vbot[0]+vtop[0])/2.)
     rc = h['xss'].Fill( s,(vbot[0]+vtop[0])/2.)
     wire = hit.GetDetectorID()%1000
     rc = h['wss'].Fill(s,wire)
     if hit.GetDetectorID() in noisyChannels:
       continue  
     X[s]+=(vbot[0]+vtop[0])/2.
     Z[s]+=(vbot[2]+vtop[2])/2.
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
 rc = h['rpcPlot'].cd(j)
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
   M = min(fT.getNumPointsWithMeasurement(),30) # for unknown reason, get stuck for track with large measurements
   for m in [0,M/2,M-1]:
    st = fT.getFittedState(m)
    Pos = st.getPos()
    if abs(z-Pos.z())<mZmin:
      mZmin = abs(z-Pos.z())
      mClose = m
   fstate =  fT.getFittedState(mClose)
   NewPosition = ROOT.TVector3(0., 0., z)
   pdgcode = -int(13*fstate.getCharge())
   rep    = ROOT.genfit.RKTrackRep( pdgcode ) 
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

ut.bookHist(h,'p/pt','momentum vs Pt (GeV)',400,0.,400.,100,0.,10.)
ut.bookHist(h,'chi2','chi2/nDoF',100,0.,25.)
ut.bookHist(h,'Nmeasurements','number of measurements used',25,-0.5,24.5)

bfield = ROOT.genfit.FairShipFields()
Bx,By,Bz = ROOT.Double(),ROOT.Double(),ROOT.Double()
def displayTrack(theTrack,debug=False):
     zstart = 0
     nPoints = 100
     delz = 1000./nPoints
     nt = len(h['dispTrack'])
     h['dispTrack'].append( ROOT.TGraph(nPoints) )
     h['dispTrackY'].append( ROOT.TGraph(nPoints) )
     for nP in range(nPoints):
      zstart+=delz
      rc,pos,mom = extrapolateToPlane(theTrack,zstart)
      if not rc: print "extrap failed"
      else: 
        h['dispTrack'][nt].SetPoint(nP,pos[2],pos[0])
        h['dispTrackY'][nt].SetPoint(nP,pos[2],pos[1])
        if debug:
         bfield.get(pos[0],pos[1],pos[2],Bx,By,Bz)
         print "%5.2F %5.2F %5.2F %5.2F %5.2F %5.2F %5.2F %5.2F %5.2F "%(pos[0],pos[1],pos[2],Bx,By,Bz,mom[0],mom[1],mom[2])
        # ptkick 1.03 / dalpha
      if nP ==0:
        fitStatus = theTrack.getFitStatus()
        print "trackinfoP/Pt/chi2/DoF/Ndf:%6.2F %6.2F %6.2F %6.2F"%(mom.Mag(),mom.Pt(),fitStatus.getChi2()/fitStatus.getNdf(),fitStatus.getNdf())
        st = theTrack.getFittedState(0)
        # if st.getPDG()*st.getCharge()>0: print "something wrong here",st.getPDG(),st.getCharge()
        if debug:
         N = theTrack.getNumPointsWithMeasurement()
         momU = theTrack.getFittedState(0).getMom()
         momD = theTrack.getFittedState(N-1).getMom()
         dalpha = momU[0]/momU[2] - ( momD[0]/momD[2] )
         slopeA = momU[0]/momU[2]
         slopeB = momD[0]/momD[2]
         posU = theTrack.getFittedState(0).getPos()
         posD = theTrack.getFittedState(N-1).getPos()
         bA = posU[0]-slopeA*posU[2]
         bB = posD[0]-slopeB*posD[2]
         x1 = zgoliath*slopeA+bA
         x2 = zgoliath*slopeB+bB
         delx = x2-x1
         rc = h['delx'].Fill(delx)
         print "mom from pt kick=",1.03/dalpha
         for j in range(theTrack.getNumPointsWithMeasurement()):
          st = theTrack.getFittedState(j)
          pos,mom = st.getPos(), st.getMom()
          print "%i %5.2F %5.2F %5.2F %5.2F %5.2F  %5.2F %i %i "%(j,pos[0],pos[1],pos[2],mom[0],mom[1],mom[2],st.getPDG(),st.getCharge())
     h['dispTrack'][nt].SetLineColor(ROOT.kMagenta)
     h['dispTrack'][nt].SetLineWidth(2)
     h['dispTrackY'][nt].SetLineColor(ROOT.kCyan)
     h['dispTrackY'][nt].SetLineWidth(2)
     h['simpleDisplay'].cd(1)
     h['dispTrack'][nt].Draw('same')
     h['dispTrackY'][nt].Draw('same')
     h[ 'simpleDisplay'].Update()
     dispTrack3D(theTrack)

def findSimpleEvent(event):
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
   return passed 

def fitTracks(nMax=-1,withDisplay=False,debug=False):
# select special clean events for testing track fit
 n=-1
 for event in sTree:
   if nMax==0: break
   n+=1
   if not findSimpleEvent(event): continue
   theTrack = makeTracks()
   if type(theTrack)==type(1): 
     # print "event rejected",theTrack,n
     continue
   elif withDisplay:
     plotEvent(n)
     displayTrack(theTrack,debug)
     next = raw_input("Next (Ret/Quit): ")         
     if next<>'':  break
   nMax-=1
 ut.bookCanvas(h,key='mom',title='trackfit',nx=1200,ny=600,cx=2,cy=2)
 rc = h['mom'].cd(1)
 h['p/pt'].SetStats(0)
 rc = h['p/pt'].Draw('colz')
 rc = h['mom'].cd(2)
 h['p/pt_x']=h['p/pt'].ProjectionX()
 h['p/pt_x'].Draw()
 h['mom'].Update()
 stats = h['p/pt_x'].FindObject('stats')
 stats.SetOptStat(11111111)
 rc = h['mom'].cd(3)
 h['chi2'].Draw()
 rc = h['mom'].cd(4)
 h['Nmeasurements'].Draw()
 h['mom'].Update()
 
sigma_spatial = ShipGeo.MufluxSpectrometer.TubePitch/ROOT.TMath.Sqrt(12) / 2.
def makeTracks():
     hitlist = []
     for hit in sTree.Digi_MufluxSpectrometerHits:
      if hit.GetDetectorID() in noisyChannels: continue
      hitlist.append(hit)
     return fitTrack(hitlist)

def fitTrack(hitlist):
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
    for hit in hitlist:
      vbot,vtop = correctAlignment(hit)
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
     fittedState = theTrack[charge][0].getFittedState()
     P = fittedState.getMomMag()
     if Debug: print "track fitted",fitStatus.getNdf(), theTrack[charge][0].getNumPointsWithMeasurement(),P
     if fitStatus.getNdf() < 10:  return -2 
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

def getSlope(cl1,cl2):
    zx,zmx,zsq,zmz,n=0,0,0,0,0
    xmean,zmean=0,0
    for cl in [cl1,cl2]:
     for hit in cl:
       xmean+=hit[1]
       zmean+=hit[2]
       zx+=hit[1]*hit[2]
       zsq+=hit[2]*hit[2]
       n+=1
    A = (zx-zmean*xmean/float(n))/(zsq-zmean*zmean/float(n))
    b = (xmean-A*zmean)/float(n)
    return A,b

Debug = False
delxAtGoliath=10.
clusterWidth = 5.
yMatching = 10.
minHitsPerCluster, maxHitsPerCluster = 2,6
topA,botA = ROOT.TVector3(),ROOT.TVector3()
topB,botB = ROOT.TVector3(),ROOT.TVector3()
clusters = {}
pl = {0:'00',1:'01',2:'10',3:'11'}
for s in range(1,5):
   clusters[s]={}
   for view in ['_x','_u','_v']:
    if s>2 and view != '_x': continue
    if s==1 and view == '_v' or s==2 and view == '_u': continue
    ut.bookHist(h,'del'+view+str(s),'del x for '+str(s)+view,100,-20.,20.)
    clusters[s][view]={}
    dx = 0
    for layer in range(0,4):  # p*2+l
      for x in DT:
        if not x.find( 'Station_'+str(s)+view+'_plane_'+pl[layer][0]+'_layer_'+pl[layer][1] )<0:
         dx = DT[x][0]
         dy = DT[x][1]
         break
      if dx == 0:
        print "this should never happen",'Station_'+str(s)+view+'_plane_'+pl[layer][0]+'_layer_'+pl[layer][1]
      ut.bookHist(h,'biasResX_'+str(s)+view+str(layer),'biased residual for '+str(s)+view+' '+str(layer),100,-20.,20.,10,-dx,dx)
      ut.bookHist(h,'biasResY_'+str(s)+view+str(layer),'biased residual for '+str(s)+view+' '+str(layer),100,-20.,20.,10,-dy,dy)      

ut.bookHist(h,'clsN','cluster sizes',10,-0.5,9.5)
ut.bookHist(h,'Ncls','number of clusters / event',10,-0.5,9.5)
ut.bookHist(h,'delY','del Y from stereo',100,100.,100.)
ut.bookHist(h,'yest','estimated Y from stereo',100,100.,100.)
ut.bookHist(h,'xy','xy of first state',100,-30.,30.,100,-30.,30.)
views = {1:['_x','_u'],2:['_x','_v'],3:['_x'],4:['_x']}
myGauss = ROOT.TF1('gauss','[0]/([2]*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)+[3]',4)
myGauss.SetParName(0,'Signal')
myGauss.SetParName(1,'Mean')
myGauss.SetParName(2,'Sigma')
myGauss.SetParName(3,'bckgr')

def findTracks():
   trackCandidates = []
   spectrHitsSorted = sortHits(sTree)
   for s in range(1,5):
    for view in views[s]:
     allHits = {}
     clusters[s][view]={}
     for l in range(4): allHits[l]=[]
     for hit in spectrHitsSorted[view][s]:
      statnb,vnb,pnb,layer,view = stationInfo(hit)
      allHits[pnb*2+layer].append(hit)
     hitsChecked=[]
     ncl = 0
     for hitA in allHits[0]:
       botA,topA = correctAlignment(hitA)
       xA = (botA[0]+topA[0])/2.
       zA = (botA[2]+topA[2])/2.
       clusters[s][view][ncl]=[[hitA,xA,zA]]
       for k in range(1,4):
         for hitB in allHits[k]:
          botB,topB = correctAlignment(hitB)
          xB = (botB[0]+topB[0])/2.
          delx = xA-xB
          rc = h['del'+view+str(s)].Fill(delx)
          if abs(delx)<clusterWidth:
           zB = (botB[2]+topB[2])/2.
           clusters[s][view][ncl].append([hitB,xB,zB])
           hitsChecked.append(hitB.GetDetectorID())
       ncl+=1
     for hitA in allHits[1]:
       if hitA.GetDetectorID() in hitsChecked: continue
       botA,topA = correctAlignment(hitA)
       xA = (botA[0]+topA[0])/2.
       zA = (botA[2]+topA[2])/2.
       clusters[s][view][ncl]=[[hitA,xA,zA]]
       for k in range(2,4):
         for hitB in allHits[k]:
          if hitB.GetDetectorID() in hitsChecked: continue
          botB,topB = correctAlignment(hitB)
          xB = (botB[0]+topB[0])/2.
          delx = xA-xB
          rc = h['del'+view+str(s)].Fill(delx)
          if abs(delx)<clusterWidth:
           zB = (botB[2]+topB[2])/2.
           clusters[s][view][ncl].append([hitB,xB,zB])
           hitsChecked.append(hitB.GetDetectorID())
       ncl+=1
     if minHitsPerCluster==2:
      for hitA in allHits[2]:
       if hitA.GetDetectorID() in hitsChecked: continue
       botA,topA = correctAlignment(hitA)
       xA = (botA[0]+topA[0])/2.
       zA = (botA[2]+topA[2])/2.
       clusters[s][view][ncl]=[[hitA,xA,zA]]
       for k in range(3,4):
         for hitB in allHits[k]:
          if hitB.GetDetectorID() in hitsChecked: continue
          botB,topB = correctAlignment(hitB)
          xB = (botB[0]+topB[0])/2.
          delx = xA-xB
          rc = h['del'+view+str(s)].Fill(delx)
          if abs(delx)<clusterWidth:
           zB = (botB[2]+topB[2])/2.
           clusters[s][view][ncl].append([hitB,xB,zB])
           hitsChecked.append(hitB.GetDetectorID())
       ncl+=1
     rc = h['clsN'].Fill(ncl)
     Ncl = 0
     keys = clusters[s][view].keys()
     for x in keys:
      aCl = clusters[s][view][x]
      if len(aCl)<minHitsPerCluster or len(aCl)>maxHitsPerCluster:   dummy = clusters[s][view].pop(x)
      else: Ncl+=1
     rc = h['Ncls'].Fill(Ncl)
   # make list of hits, see per event 1 and 2 tracks most
   # now we have to make a loop over all combinations 
   allStations = True
   for s in range(1,5):
      if len(clusters[s]['_x'])==0:   allStations = False
   if len(clusters[1]['_u'])==0:      allStations = False
   if len(clusters[2]['_v'])==0:      allStations = False
   if allStations:
    t1t2cand = []
    # list of lists of cluster1, cluster2, x
    t3t4cand = []
    h['dispTrackSeg'] = []
    for cl1 in clusters[1]['_x']:
     for cl2 in clusters[2]['_x']:
      slopeA,bA = getSlope(clusters[1]['_x'][cl1],clusters[2]['_x'][cl2])
      x1 = zgoliath*slopeA+bA
      t1t2cand.append([clusters[1]['_x'][cl1],clusters[2]['_x'][cl2],x1,slopeA,bA])
      if Debug:
       nt = len(h['dispTrackSeg'])
       h['dispTrackSeg'].append( ROOT.TGraph(2) )
       h['dispTrackSeg'][nt].SetPoint(0,0.,bA)
       h['dispTrackSeg'][nt].SetPoint(1,400.,slopeA*400+bA)
       h['dispTrackSeg'][nt].SetLineColor(ROOT.kCyan)
       h['dispTrackSeg'][nt].SetLineWidth(2)
       h['simpleDisplay'].cd(1)
       h['dispTrackSeg'][nt].Draw('same')
       nt+=1
    for cl1 in clusters[3]['_x']:
     for cl2 in clusters[4]['_x']:
      slopeA,bA = getSlope(clusters[3]['_x'][cl1],clusters[4]['_x'][cl2])
      x1 = zgoliath*slopeA+bA
      t3t4cand.append([clusters[3]['_x'][cl1],clusters[4]['_x'][cl2],x1,slopeA,bA])
      if Debug:
       nt = len(h['dispTrackSeg'])
       h['dispTrackSeg'].append( ROOT.TGraph(2) )
       h['dispTrackSeg'][nt].SetPoint(0,300.,slopeA*300+bA)
       h['dispTrackSeg'][nt].SetPoint(1,900.,slopeA*900+bA)
       h['dispTrackSeg'][nt].SetLineColor(ROOT.kMagenta)
       h['dispTrackSeg'][nt].SetLineWidth(2)
       h['simpleDisplay'].cd(1)
       h['dispTrackSeg'][nt].Draw('same')
       nt+=1
    if Debug: 
      print "trackCandidates",len(t1t2cand),len(t3t4cand)
      h['simpleDisplay'].Update()
    for nt1t2 in range(len(t1t2cand)):
     t1t2 = t1t2cand[nt1t2]
     for nt3t4 in range(len(t3t4cand)):
      t3t4 = t3t4cand[nt3t4]
      delx = t3t4[2]-t1t2[2]
      h['delx'].Fill(delx)
      if abs(delx) < delxAtGoliath:
       hitList = []
       for p in range(2):
         for cl in t1t2[p]: hitList.append(cl[0])
       for p in range(2):
         for cl in t3t4[p]: hitList.append(cl[0])
# check for matching u and v hits, X
       stereoHits = {'u':[],'v':[]}
       for n in clusters[1]['_u']:
        for cl in clusters[1]['_u'][n]:
           botA,topA = correctAlignment(cl[0])
           sl  = (botA[1]-topA[1])/(botA[0]-topA[0])
           b = topA[1]-sl*topA[0]
           yest = sl*(t1t2[3]*topA[2]+t1t2[4])+b
           rc = h['yest'].Fill(yest)
           if yest > botA[0]+5. or yest < topA[0]-5: continue
           stereoHits['u'].append([cl[0],sl,b,yest])
       for n in clusters[2]['_v']: 
        for cl in clusters[2]['_v'][n]: 
           botA,topA = correctAlignment(cl[0])
           sl  = (botA[1]-topA[1])/(botA[0]-topA[0])
           b = topA[1]-sl*topA[0]
           yest = sl*(t1t2[3]*topA[2]+t1t2[4])+b
           rc = h['yest'].Fill(yest)
           if yest < botA[0]-5. or yest > topA[0]+5: continue
           stereoHits['v'].append([cl[0],sl,b,yest])
       nu = 0
       matched = {}
       for clu in stereoHits['u']:
        nv=0
        for clv in stereoHits['v']:
           dely = clu[3]-clv[3]
           rc = h['delY'].Fill(dely)
           if abs(dely)<yMatching:
             matched[clv[0]]=True
             matched[clu[0]]=True
           nv+=1
        nu+=1
       for cl in matched: hitList.append(cl)
       if Debug:  print "fit track t1t2 t3t4 with hits, stereo, delx",nt1t2,nt3t4,len(hitList),len(matched),delx
       aTrack = fitTrack(hitList)
       if type(aTrack) != type(1):
         trackCandidates.append(aTrack)
   return trackCandidates

def testClusters(nEvent=-1,nTot=1000):
  eventRange = [0,sTree.GetEntries()]
  if not nEvent<0: eventRange = [nEvent,nEvent+nTot]
  for Nr in range(eventRange[0],eventRange[1]):
   sTree.GetEvent(Nr)
   print "===== New Event =====",Nr
   plotEvent(Nr)
   trackCandidates = findTracks()
   print "tracks found",len(trackCandidates)
   for aTrack in trackCandidates:
      displayTrack(aTrack)
   next = raw_input("Next (Ret/Quit): ")
   if next<>'':  break

def plotBiasedResiduals(nEvent=-1,nTot=1000):
  plotHitMaps()
  
  eventRange = [0,sTree.GetEntries()]
  if not nEvent<0: eventRange = [nEvent,nEvent+nTot]
  for Nr in range(eventRange[0],eventRange[1]):
   sTree.GetEvent(Nr)
   #if Nr%100==0:  
   print "now at event",Nr
   if not findSimpleEvent(sTree): continue
   trackCandidates = findTracks()
   for aTrack in trackCandidates:
       sta = aTrack.getFittedState(0)
       if sta.getMomMag() < 3.: continue
       pos = sta.getPos()
       h['xy'].Fill(pos[0],pos[1])
       for hit in sTree.Digi_MufluxSpectrometerHits:
          if hit.GetDetectorID() in noisyChannels:  continue
          s,v,p,l,view = stationInfo(hit)
          vbot,vtop = correctAlignment(hit)
          z = (vbot[2]+vtop[2])/2.
          try:
           rc,pos,mom = extrapolateToPlane(aTrack,z)
          except:
           continue
          if view == '_x': res = pos[0]-(vbot[0]+vtop[0])/2.
          else: 
            res = vbot[0]*pos[1] - vtop[0]*pos[1] - vbot[1]*pos[0]+ vtop[0]*vbot[1] + pos[0]*vtop[1]-vbot[0]*vtop[1]
            res = res/ROOT.TMath.Sqrt( (vtop[0]-vbot[0])**2+(vtop[1]-vbot[1])**2)
          h['biasResX_'+str(s)+view+str(2*l+p)].Fill(res,pos[0])
          h['biasResY_'+str(s)+view+str(2*l+p)].Fill(res,pos[1])
  if not h.has_key('biasedResiduals'): 
      ut.bookCanvas(h,key='biasedResiduals',title='biasedResiduals',nx=1600,ny=1200,cx=4,cy=6)
      ut.bookCanvas(h,key='biasedResidualsX',title='biasedResiduals function of X',nx=1600,ny=1200,cx=4,cy=6)
      ut.bookCanvas(h,key='biasedResidualsY',title='biasedResiduals function of Y',nx=1600,ny=1200,cx=4,cy=6)
  j=1
  rc = h['biasedResiduals'].cd(j)
  for s in range(1,5):
   for view in ['_x','_u','_v']:
    if s>2 and view != '_x': continue
    if s==1 and view == '_v' or s==2 and view == '_u': continue
    for l in range(0,4):
     hname = 'biasResX_'+str(s)+view+str(l)
     hnameProjX = 'biasRes_'+str(s)+view+str(l)
     if h[hname].GetEntries()==0: continue
     h[hnameProjX] = h[hname].ProjectionX()
     myGauss.SetParameter(0,h[hnameProjX].GetMaximum())
     myGauss.SetParameter(1,0.)
     myGauss.SetParameter(2,4.)
     myGauss.SetParameter(3,1.)
     rc = h['biasedResiduals'].cd(j)
     fitResult = h[hnameProjX].Fit(myGauss,'SQ','',-10.,10.)
     rc = fitResult.Get()
     mean = rc.GetParams()[1]
     rms  = rc.GetParams()[2]
     print "%i, %s, %i mean=%5.2F RMS=%5.2F"%(s,view,l,mean,rms)
     # make plot of mean as function of X,Y
     for p in ['X','Y']:
      hname = 'biasRes'+p+'_'+str(s)+view+str(l)
      h[hname+'_mean'+p] = h[hname].ProjectionY(hname+'_mean')
      h[hname+'_mean'+p].Reset()
      rc = h['biasedResiduals'+p].cd(j)  
      for k in range(1,h[hname].GetNbinsY()+1):
       tmp = h[hname].ProjectionX('tmp',k,k)
       if tmp.GetEntries()<10: continue
       myGauss.SetParameter(0,tmp.GetMaximum())
       myGauss.SetParameter(1,0.)
       myGauss.SetParameter(2,4.)
       myGauss.SetParameter(3,1.)
       fitResult = tmp.Fit(myGauss,'SQ','',-10.,10.)
       rc = fitResult.Get()
       mean = rc.GetParams()[1]
       rms  = rc.GetParams()[2]
       rc = h[hname+'_mean'+p].Fill( h[hname+'_mean'+p].GetBinCenter(k), mean)
      h[hname+'_mean'+p].SetMaximum(10.)
      h[hname+'_mean'+p].SetMinimum(-10.)
      h[hname+'_mean'+p].Draw()
     j+=1
def plot2dResiduals():
 j=1
 h['biasedResiduals'].cd(j)
 for s in range(1,5):
   for view in ['_x','_u','_v']:
    if s>2 and view != '_x': continue
    if s==1 and view == '_v' or s==2 and view == '_u': continue
    for l in range(0,4):
     hname = 'biasResX_'+str(s)+view+str(l)
     if h[hname].GetEntries()<1: continue
     print s,view,l,h[hname].GetEntries()
     for p in ['X','Y']:
      hname = 'biasRes'+p+'_'+str(s)+view+str(l)
      rc = h['biasedResiduals'+p].cd(j)  
      h[hname].Draw('box')
     j+=1

sqrt2 = ROOT.TMath.Sqrt(2.)
cos30 = ROOT.TMath.Cos(30./180.*ROOT.TMath.Pi())
sin30 = ROOT.TMath.Sin(30./180.*ROOT.TMath.Pi())
def correctAlignment(hit):
 #delX=[[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]
 delX=[[-1.2,1.4,-0.9,0.7],[-1.69-1.31,0.3+2.82,0.6-0.4,-0.8-0.34],[-0.9,1.14,-0.80,1.1],[-0.8,1.29,0.15,2.0]]
 #delUV = [[1.8,-2.,0.8,-1.],[1.2,-1.1,-0.5,0.3]]
 delUV = [[0,0,0,0],[0,0,0,0]]
 rc = hit.MufluxSpectrometerEndPoints(vbot,vtop)
 s,v,p,l,view = stationInfo(hit)
 if view=='_x':
   cor = delX[s-1][2*l+p]
   vbot[0]=vbot[0]+cor
   vtop[0]=vtop[0]+cor
 else:
   if view=='_u':     cor = delUV[0][2*l+p]
   elif view=='_v':   cor = delUV[1][2*l+p]
   vbot[0]=vbot[0]+cor*cos30
   vtop[0]=vtop[0]+cor*cos30
   vbot[1]=vbot[1]+cor*sin30
   vtop[1]=vtop[1]+cor*sin30
   #tmp = vbot[0]*ROOT.TMath.Cos(rotUV)-vbot[1]*ROOT.TMath.Sin(rotUV)
   #vbot[1]=vbot[1]*ROOT.TMath.Cos(rotUV)+vbot[0]*ROOT.TMath.Sin(rotUV)
   #vbot[0]=tmp
   #tmp = vtop[0]*ROOT.TMath.Cos(rotUV)-vtop[1]*ROOT.TMath.Sin(rotUV)
   #vtop[1]=vtop[1]*ROOT.TMath.Cos(rotUV)+vtop[0]*ROOT.TMath.Sin(rotUV)
   #vbot[0]=tmp
 return vbot,vtop

def testMultipleHits(nEvent=-1,nTot=1000):
  occ = 0
  eventRange = [0,sTree.GetEntries()]
  if not nEvent<0: eventRange = [nEvent,nEvent+nTot]
  for Nr in range(eventRange[0],eventRange[1]):
   sTree.GetEvent(Nr)
   listOfDigits=[]
   for hit in sTree.Digi_MufluxSpectrometerHits:
     detID = hit.GetDetectorID()
     if detID in listOfDigits:
       print "multiple hit",detID,Nr
       occ+=1
     else:   listOfDigits.append(detID)
  print "error rate",occ/float(nTot)

print "existing methods"
print " --- plotHitMaps(): hitmaps / layer, TDC / layer, together with list of noisy channels"
print " --- plotEvent(n) : very basic event display, just x hits in x/z projection " 
print " --- plotRPCHitmap() : basic plots for RPC "
print " --- fitTracks(100) and fitTracks(100,True) with simple Display and 3d display of tracks with detector, low occupancy events"
print " --- testClusters(nstart,nevents), clustering of hits and pattern recognition followed by track fit"
print " --- plotBiasedResiduals(nstart,nevents), fit tracks in low occupancy events and plot residuals, plot2dResiduals() for display del vs x, del vs y"
print " --- printScalers()"
print " --- zCentre() : extrapolation of straight tracks upstream / downstream to magnet centre"


