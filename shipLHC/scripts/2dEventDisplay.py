import ROOT,os
import rootUtils as ut
from array import array
import shipunit as u
import SndlhcMuonReco

h={}
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-r", "--runNumber", dest="runNumber", help="run number", type=int,required=False)
parser.add_argument("-p", "--path", dest="path", help="run number",required=False,default="")
parser.add_argument("-f", "--inputFile", dest="inputFile", help="input file MC",default="",required=False)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", required=True)
parser.add_argument("-P", "--partition", dest="partition", help="partition of data", type=int,required=False,default=-1)

parser.add_argument("-H", "--houghTransform", dest="houghTransform", help="do not use hough transform for track reco", action='store_false',default=True)
parser.add_argument("-t", "--tolerance", dest="tolerance",  type=float, help="How far away from Hough line hits assigned to the muon can be. In cm.", default=0.)
parser.add_argument("--hits_to_fit", dest = "hits_to_fit", type=str, help="Which detectors to use in the fit, in the format: vesfusds, where [ve] is veto, [sf] is Scifi, [us] is Upstream muon filter, and [ds] is downstream muon filter", default = "sfusds")
parser.add_argument("--hits_for_triplet", dest = "hits_for_triplet", type=str, help="Which detectors to use for the triplet condition. In the same format as --hits_to_fit", default = "ds")

options = parser.parse_args()

trans2local = False

import SndlhcGeo
geo = SndlhcGeo.GeoInterface(options.geoFile)

lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
lsOfGlobals.Add(geo.modules['Scifi'])
lsOfGlobals.Add(geo.modules['MuFilter'])

detSize = {}
si = geo.snd_geo.Scifi
detSize[0] =[si.channel_width, si.channel_width, si.scifimat_z ]
mi = geo.snd_geo.MuFilter
detSize[1] =[mi.VetoBarX/2,                   mi.VetoBarY/2,            mi.VetoBarZ/2]
detSize[2] =[mi.UpstreamBarX/2,           mi.UpstreamBarY/2,    mi.UpstreamBarZ/2]
detSize[3] =[mi.DownstreamBarX_ver/2,mi.DownstreamBarY/2,mi.DownstreamBarZ/2]

mc = False

run      = ROOT.FairRunAna()
ioman = ROOT.FairRootManager.Instance()

if options.inputFile=="":
  f=ROOT.TFile.Open(options.path+'sndsw_raw_'+str(options.runNumber).zfill(6)+'.root')
else:
  f=ROOT.TFile.Open(options.path+options.inputFile)

if f.FindKey('cbmsim'):
        eventTree = f.cbmsim
        if eventTree.GetBranch('ScifiPoint'): mc = True
else:   
        eventTree = f.rawConv
        ioman.SetTreeName('rawConv')

outFile = ROOT.TMemFile('dummy','CREATE')
source = ROOT.FairFileSource(f)
run.SetSource(source)
sink = ROOT.FairRootFileSink(outFile)
run.SetSink(sink)

if options.houghTransform:
  muon_reco_task = SndlhcMuonReco.MuonReco()
  run.AddTask(muon_reco_task)
else:
  import SndlhcTracking
  trackTask = SndlhcTracking.Tracking() 
  trackTask.SetName('simpleTracking')
  run.AddTask(trackTask)

#avoiding some error messages
xrdb = ROOT.FairRuntimeDb.instance()
xrdb.getContainer("FairBaseParSet").setStatic()
xrdb.getContainer("FairGeoParSet").setStatic()

run.Init()
eventTree = ioman.GetInTree()
# backward compatbility for early converted events
eventTree.GetEvent(0)
if eventTree.GetBranch('Digi_MuFilterHit'): eventTree.Digi_MuFilterHits = eventTree.Digi_MuFilterHit

if options.houghTransform:
# prepare track reco with hough transform
  muon_reco_task.SetTolerance(options.tolerance)
  muon_reco_task.SetHitsToFit(options.hits_to_fit)
  muon_reco_task.SetHitsForTriplet(options.hits_for_triplet)

nav = ROOT.gGeoManager.GetCurrentNavigator()

Nlimit = 4
onlyScifi = False
def goodEvent(event):
# can be replaced by any user selection
           stations = {'Scifi':{},'Mufi':{}}
           if event.Digi_ScifiHits.GetEntries()>25: return False
           for d in event.Digi_ScifiHits:
               stations['Scifi'][d.GetDetectorID()//1000000] = 1
           for d in event.Digi_MuFilterHits:
               plane = d.GetDetectorID()//1000
               stations['Mufi'][plane] = 1
           totalN = len(stations['Mufi'])+len(stations['Scifi'])
           if len(stations['Scifi'])>4 and len(stations['Mufi'])>6: return True
           else: False
           if onlyScifi and len(stations['Scifi'])>Nlimit: return True
           elif not onlyScifi  and totalN >  Nlimit: return True
           else: return False

def loopEvents(start=0,save=False,goodEvents=False,withTrack=-1,nTracks=0,Setup='',verbose=0):
 if 'simpleDisplay' not in h: ut.bookCanvas(h,key='simpleDisplay',title='simple event display',nx=1200,ny=1600,cx=1,cy=2)
 h['simpleDisplay'].cd(1)
 zStart = 250. # TI18 coordinate system
 if Setup == 'H6': zStart = 60.
 if Setup == 'TP': zStart = -50. # old coordinate system with origin in middle of target
 if 'xz' in h: 
        h.pop('xz').Delete()
        h.pop('yz').Delete()
 ut.bookHist(h,'xz','; z [cm]; x [cm]',500,zStart,zStart+320.,100,-100.,10.)
 ut.bookHist(h,'yz','; z [cm]; y [cm]',500,zStart,zStart+320.,100,0.,80.)

 proj = {1:'xz',2:'yz'}
 h['xz'].SetStats(0)
 h['yz'].SetStats(0)

 N = -1
 Tprev = -1
 A,B = ROOT.TVector3(),ROOT.TVector3()
 ptext={0:'   Y projection',1:'   X projection'}
 text = ROOT.TLatex()
 event = eventTree
 OT = sink.GetOutTree()
 for N in range(start, event.GetEntries()):
    rc = event.GetEvent(N)
    if goodEvents and not goodEvent(event): continue
    if withTrack:
       if options.houghTransform:
          rc = source.GetInTree().GetEvent(N)
          muon_reco_task.Exec(0)
          ntracks = OT.Reco_MuonTracks.GetEntries()
          uniqueTracks = cleanTracks()
          if len(uniqueTracks)<nTracks: continue
       else:
          if withTrack==2:  Scifi_track()
          else:     trackTask.ExecuteTask()
          ntracks = len(OT.Reco_MuonTracks)
       if ntracks<nTracks: continue

       if verbose>0:
          for aTrack in OT.Reco_MuonTracks:
             mom    = aTrack.getFittedState().getMom()
             pos      = aTrack.getFittedState().getPos()
             mom.Print()
             pos.Print()
    print( "event ->",N )

    digis = []
    if event.FindBranch("Digi_ScifiHits"): digis.append(event.Digi_ScifiHits)
    if event.FindBranch("Digi_MuFilterHits"): digis.append(event.Digi_MuFilterHits)
    if event.FindBranch("Digi_MuFilterHit"): digis.append(event.Digi_MuFilterHit)
    empty = True
    for x in digis:
       if x.GetEntries()>0: empty = False
    if empty: continue
    h['hitCollectionX']= {'Scifi':[0,ROOT.TGraphErrors()],'DS':[0,ROOT.TGraphErrors()]}
    h['hitCollectionY']= {'Veto':[0,ROOT.TGraphErrors()],'Scifi':[0,ROOT.TGraphErrors()],'US':[0,ROOT.TGraphErrors()],'DS':[0,ROOT.TGraphErrors()]}
    systems = {1:'Veto',2:'US',3:'DS',0:'Scifi'}
    for collection in ['hitCollectionX','hitCollectionY']:
       for c in h[collection]:
          rc=h[collection][c][1].SetName(c)
          rc=h[collection][c][1].Set(0)

    if event.FindBranch("EventHeader"):
       T = event.EventHeader.GetEventTime()
       dT = 0
       if Tprev >0: dT = T-Tprev
       Tprev = T
    for p in proj:
       rc = h[ 'simpleDisplay'].cd(p)
       if p==1: h[proj[p]].SetTitle('event '+str(N))
       h[proj[p]].Draw('b')

    for D in digis:
      for digi in D:
         detID = digi.GetDetectorID()
         if digi.GetName()  == 'MuFilterHit':
            system = digi.GetSystem()
            geo.modules['MuFilter'].GetPosition(detID,A,B)
            if trans2local:
                curPath = nav.GetPath()
                tmp = curPath.rfind('/')
                nav.cd(curPath[:tmp])
         else:
            geo.modules['Scifi'].GetSiPMPosition(detID,A,B)
            if trans2local:
                curPath = nav.GetPath()
                tmp = curPath.rfind('/')
                nav.cd(curPath[:tmp])
            system = 0
         globA,locA = array('d',[A[0],A[1],A[2]]),array('d',[A[0],A[1],A[2]])
         if trans2local:   nav.MasterToLocal(globA,locA)
         Z = A[2]
         if digi.isVertical():
                   collection = 'hitCollectionX'
                   Y = locA[0]
                   sY = detSize[system][0]
         else:                         
                   collection = 'hitCollectionY'
                   Y = locA[1]
                   sY = detSize[system][1]
         c = h[collection][systems[system]]
         rc = c[1].SetPoint(c[0],Z,Y)
         rc = c[1].SetPointError(c[0],detSize[system][2],sY)
         c[0]+=1 
    h['hitCollectionY']['Veto'][1].SetMarkerColor(ROOT.kRed)
    h['hitCollectionY']['Scifi'][1].SetMarkerColor(ROOT.kBlue)
    h['hitCollectionX']['Scifi'][1].SetMarkerColor(ROOT.kBlue)
    h['hitCollectionY']['US'][1].SetMarkerColor(ROOT.kGreen)
    h['hitCollectionY']['DS'][1].SetMarkerColor(ROOT.kCyan)
    h['hitCollectionX']['DS'][1].SetMarkerColor(ROOT.kCyan)
    k = 1
    for collection in ['hitCollectionX','hitCollectionY']:
       h[ 'simpleDisplay'].cd(k)
       k+=1
       for c in h[collection]:
          print(collection.split('ion')[1],c, h[collection][c][1].GetN())
          if h[collection][c][1].GetN()<1: continue
          h[collection][c][1].SetMarkerStyle(20+k)
          h[collection][c][1].SetMarkerSize(1.5)
          rc=h[collection][c][1].Draw('sameP')
          h['display:'+c]=h[collection][c][1]

    if withTrack == 1: addTrack()
    if withTrack == 2: addTrack(True)

    h[ 'simpleDisplay'].Update()
    if save: h['simpleDisplay'].Print('event_'+"{:04d}".format(N)+'.png')
    rc = input("hit return for next event or q for quit: ")
    if rc=='q': break
 if save: os.system("convert -delay 60 -loop 0 event*.png animated.gif")

def addTrack(scifi=False):
   xax = h['xz'].GetXaxis()
   nTrack = 0
   OT = sink.GetOutTree()
   for   aTrack in OT.Reco_MuonTracks:
      for p in [0,1]:
          h['aLine'+str(nTrack*10+p)] = ROOT.TGraph()

      zEx = xax.GetBinCenter(1)
      mom    = aTrack.getFittedState().getMom()
      pos      = aTrack.getFittedState().getPos()
      lam      = (zEx-pos.z())/mom.z()
      Ex        = [pos.x()+lam*mom.x(),pos.y()+lam*mom.y()]
      for p in [0,1]:   h['aLine'+str(nTrack*10+p)].SetPoint(0,zEx,Ex[p])

      for i in range(aTrack.getNumPointsWithMeasurement()):
         state = aTrack.getFittedState(i)
         pos    = state.getPos()
         for p in [0,1]:
             h['aLine'+str(nTrack*10+p)].SetPoint(i+1,pos[2],pos[p])

      zEx = xax.GetBinCenter(xax.GetLast())
      mom    = aTrack.getFittedState().getMom()
      pos      = aTrack.getFittedState().getPos()
      lam      = (zEx-pos.z())/mom.z()
      Ex        = [pos.x()+lam*mom.x(),pos.y()+lam*mom.y()]
      for p in [0,1]:   h['aLine'+str(nTrack*10+p)].SetPoint(i+2,zEx,Ex[p])

      for p in [0,1]:
             tc = h[ 'simpleDisplay'].cd(p+1)
             h['aLine'+str(nTrack*10+p)].SetLineColor(ROOT.kRed)
             h['aLine'+str(nTrack*10+p)].SetLineWidth(2)
             h['aLine'+str(nTrack*10+p)].Draw('same')
             tc.Update()
             h[ 'simpleDisplay'].Update()
      nTrack+=1

def Scifi_track():
# check for low occupancy and enough hits in Scifi
    clusters = trackTask.scifiCluster()
    trackTask.kalman_tracks.Clear()
    stations = {}
    for s in range(1,6):
       for o in range(2):
          stations[s*10+o] = []
    for cl in clusters:
         detID = cl.GetFirst()
         s  = detID//1000000
         o = (detID//100000)%10
         stations[s*10+o].append(detID)
    nclusters = 0
    check = {}
    for s in range(1,6):
       for o in range(2):
            if len(stations[s*10+o]) > 0: check[s*10+o]=1
            nclusters+=len(stations[s*10+o])
    if len(check)<8 or nclusters > 12: return -1
# build trackCandidate
    hitlist = {}
    for k in range(len(clusters)):
           hitlist[k] = clusters[k]
    theTrack = trackTask.fitTrack(hitlist)
    eventTree.ScifiClusters = clusters
    trackTask.kalman_tracks.Add(theTrack)
def dumpVeto():
    muHits = {10:[],11:[]}
    for aHit in eventTree.Digi_MuFilterHits:
         if not aHit.isValid(): continue
         s = aHit.GetDetectorID()//10000
         if s>1: continue
         p = (aHit.GetDetectorID()//1000)%10
         bar = (aHit.GetDetectorID()%1000)%60
         plane = s*10+p
         muHits[plane].append(aHit)
    for plane in [10,11]:
        for aHit in muHits[plane]:
          S =aHit.GetAllSignals()
          txt = ""
          for x in S:
              if x[1]>0: txt+=str(x[1])+" "
          print(plane, (aHit.GetDetectorID()%1000)%60, txt)

def cleanTracks():
    T = sink.GetOutTree()
    listOfDetIDs = {}
    n = 0
    for aTrack in T.Reco_MuonTracks:
        listOfDetIDs[n] = []
        for i in range(aTrack.getNumPointsWithMeasurement()):
           M =  aTrack.getPointWithMeasurement(i)
           R =  M.getRawMeasurement()
           listOfDetIDs[n].append(R.getDetId())
           if R.getDetId()>0: listOfDetIDs[n].append(R.getDetId()-1)
           listOfDetIDs[n].append(R.getDetId()+1)
        n+=1
    uniqueTracks = []
    for n1 in range( len(listOfDetIDs) ):
       unique = True
       for n2 in range( len(listOfDetIDs) ):
             if n1==n2: continue
             I = set(listOfDetIDs[n1]).intersection(listOfDetIDs[n2])
             if len(I)>0:  unique = False
       if unique: uniqueTracks.append(n1)
    if len(uniqueTracks)>1: 
         for n1 in range( len(listOfDetIDs) ): print(listOfDetIDs[n1])
    return uniqueTracks
