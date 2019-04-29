#import yep
import ROOT,os,time,sys,operator,atexit
ROOT.gROOT.ProcessLine('typedef std::unordered_map<int, std::unordered_map<int, std::unordered_map<int, std::vector<MufluxSpectrometerHit*>>>> nestedList;')
import numpy
from decorators import *
import __builtin__ as builtin
ROOT.gStyle.SetPalette(ROOT.kGreenPink)
PDG = ROOT.TDatabasePDG.Instance()
# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
# stop printing errors
ROOT.gErrorIgnoreLevel = ROOT.kBreak
from argparse import ArgumentParser
import shipunit as u
import rootUtils as ut
from array import array

########
zeroField    = False
DAFfitter    = True
withMaterial = True
MCdata = False
########
MCsmearing=0.04  #  + 0.027**2 -> 0.05
####### 
cuts={}
cuts['Ndf'] = 9
cuts['deltaNdf'] = 2
cuts['yMax']     = 5.
cuts['tot']      = 9.
cuts['hitDist'] = 5.
cuts['minLayersUV'] = 2
cuts['maxClusterSize'] = 2
cuts['delxAtGoliath'] = 8.
cuts['lateArrivalsToT'] = 9999.
# smallest group of channels for RT calibration
cuts['RTsegmentation'] = 12
# for muontagger clustering
cuts['muTaggerCluster_max'] = 6
cuts['muTaggerCluster_sep'] = 15
cuts['muTrackMatchX']= 5.
cuts['muTrackMatchY']= 10.
cuts['muTaggerCluster_grouping'] = 3
cuts["RPCmaxDistance"] = 10.

vbot = ROOT.TVector3()
vtop = ROOT.TVector3()
alignConstants = {}
h={}
log = {}
debug = False

views =  {1:['_x','_u'],2:['_x','_v'],3:['_x'],4:['_x']}
viewsI = {1:[0,1],2:[0,2],3:[0],4:[0]}
viewC = {0:"_x",1:"_u",2:"_v"}

muSources = {'eta':221,'omega':223,'phi':333,'rho0':113,'eta_prime':331}
muSourcesIDs = muSources.values()
rnr       = ROOT.TRandom()
#-----prepare python exit-----------------------------------------------
def pyExit():
 ut.errorSummary()
# atexit.register(pyExit)
#-----list of arguments--------------------------------------------------
parser = ArgumentParser()
parser.add_argument("-f", "--files", dest="listOfFiles", help="list of files comma separated", required=True)
parser.add_argument("-l", "--fileCatalog", dest="catalog", help="list of files in file", default=False)
parser.add_argument("-c", "--cmd", dest="command", help="command to execute", default="")
parser.add_argument("-d", "--Display", dest="withDisplay", help="detector display", default=True)
parser.add_argument("-e", "--eos", dest="onEOS", help="files on EOS", default=False)
parser.add_argument("-u", "--update", dest="updateFile", help="update file", default=False)
parser.add_argument("-i", "--input", dest="inputFile", help="input histo file", default='residuals.root')

#-----accessing file------------------------------------------------------
options = parser.parse_args()
fnames = []
if options.catalog:
 tmp = open(options.listOfFiles)
 for x in tmp.readlines():
  fname = x.replace('\n','')
  if fname.find("root")<0:continue
  f=ROOT.TFile.Open(fname)
  sTree = f.cbmsim
  if not sTree.GetBranch("FitTracks"): 
   print "does not contain FitTracks",fname
   f.Close()
   continue
  fnames.append(fname)
  fnames.append(x.replace('\n',''))
 tmp.close()
else:
 fnames = options.listOfFiles.split(',')
fname = fnames[0]
if options.updateFile:
 f=ROOT.TFile(fname,'update')
 sTree=f.Get('cbmsim')
 if not sTree: 
   print "Problem with updateFile",f
   exit(-1)
else:
 sTree = ROOT.TChain('cbmsim')
 for f in fnames: 
  print "add ",f
  if options.onEOS: sTree.Add(os.environ['EOSSHIP']+f)
  else:             sTree.Add(f)

rnames = []
for fname in fnames:
 rnames.append(fname[fname.rfind('/')+1:])
rname = rnames[0]
#sTree.SetMaxVirtualSize(300000)
#-------------------------------geometry initialization
from ShipGeoConfig import ConfigRegistry
ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/charm-geometry_config.py", Setup = 1, cTarget = 3)
builtin.ShipGeo = ShipGeo
import charmDet_conf
run = ROOT.FairRunSim()
run.SetName("TGeant4")  # Transport engine
run.SetOutputFile(ROOT.TMemFile('output', 'recreate'))  # Output file
run.SetUserConfig("g4Config_basic.C") # geant4 transport not used, only needed for creating VMC field
rtdb = run.GetRuntimeDb()
modules = charmDet_conf.configure(run,ShipGeo)
# -----Create geometry and draw display----------------------------------------------
run.Init()
sGeo = ROOT.gGeoManager
nav = sGeo.GetCurrentNavigator()
top = sGeo.GetTopVolume()
top.SetVisibility(0)
if options.withDisplay: 
 try: 
   #building the EVE display instead of the simple root one allows to add new objects there (instead of a separate canvas)
   ROOT.TEveManager.Create()
   gEve = ROOT.gEve
   #adding all subnodes for drawing
   for node in top.GetNodes():
     evenode = ROOT.TEveGeoTopNode(sGeo,node)
     evenode.UseNodeTrans()
     gEve.AddGlobalElement(evenode) 
   gEve.FullRedraw3D(kTRUE)
   
 except: pass

saveGeofile = False
import saveBasicParameters
if saveGeofile:
 run.CreateGeometryFile("charmxsec_geofile.root")
# save ShipGeo dictionary in geofile
 saveBasicParameters.execute("charmxsec_geofile.root",ShipGeo)

#list of positions of RPC channels, each entry of the list has two TVector3 objects
RPCPositionsBotTop = {}

vbot = ROOT.TVector3()
vtop = ROOT.TVector3()

#TEve material for track drawing
tracklist = ROOT.TEveTrackList()
prop = tracklist.GetPropagator()
prop.SetMaxZ(20000)
tracklist.SetName("RK Propagator")
recotrack = ROOT.TEveRecTrackD()

def GetPixelPositions(n=1):
    sTree.GetEntry(n)
    pixelhits = sTree.Digi_PixelHits_1
    pos = ROOT.TVector3(0,0,0)
    for hit in pixelhits:
      detID = hit.GetDetectorID()
      hit.GetPixelXYZ(pos,detID)
      print "This is the position of our pixel hit: ", pos[0], pos[1], pos[2]


def correctAlignmentRPC(hit,v):
 hit.EndPoints(vtop,vbot) #obtaining hit positions

 if v==1:
   vbot[0] = -vbot[0] -1.21
   vtop[0] = -vtop[0] -1.21
 else:
   vbot[1] = vbot[1] -1.21
   vtop[1] = vtop[1] -1.21
 return vbot,vtop

def RPCPosition():
 """ builds the list of positions for each detectorID. Same as driftubeMonitoring.py """
 for s in range(1,6): #RPC stations
  for v in range(2): #views
   for c in range(1,185): # channels per view
    if v==0 and c>116: continue
    detID = s*10000+v*1000+c
    hit = ROOT.MuonTaggerHit(detID,0)
    a,b = correctAlignmentRPC(hit,v)
    RPCPositionsBotTop[detID] = [a.Clone(),b.Clone()]
    x = (a[0]+b[0])/2.
    y = (a[1]+b[1])/2.
    z = (a[2]+b[2])/2.
    print "Posizione per view {} e canale {}: ({}, {},{})".format(v,c,x,y,z)

def GetRPCPosition(s,v,c):
    detID = s*10000+v*1000+c
    return RPCPositionsBotTop[detID]
#getting positions from the MuonTaggerHit containers, built from the files provided by Alessandra
def loadRPCtracks(n=1):
    """ Loads MuonTaggerHits from file and get position of clusters"""
    hitx = []
    hity = []
    hitz = []
    for icluster in range(5):
     hitx.append(0)
     hity.append(0)
     hitz.append(0)

    sTree.GetEntry(n)
    trackhits = sTree.MuonTaggerHit
    clustersH = []
    clustersV = []
    for hit in trackhits:
     detID = hit.GetDetectorID()
     station = int (detID/10000) #automatically an int in python2, but calling the conversion avoids confusion
     view = int((detID-station*10000)/1000)

     a,b = RPCPositionsBotTop[detID]
     x = (a[0]+b[0])/2.
     y = (a[1]+b[1])/2.
     z = (a[2]+b[2])/2.

    #adding the point to two different lists according to the view  
     if view == 0:
      hity[station-1] = y
      hitz[station-1] = z
      clustersH.append([x,y,z])
     elif view == 1:
      hitx[station-1] = x
      hitz[station-1] = z
      clustersV.append([x,y,z])
     print "Posizione cluster caricato: ({},{},{}), corrispondente alla stazione{} e alla view {}".format(x,y,z,station,view)    
    #fitting to two 2D tracks
    mH,bH = getSlopes(clustersH,0) 
    mV,bV = getSlopes(clustersV,1)   
    trackH = ROOT.RPCTrack(mH,bH)
    trackV = ROOT.RPCTrack(mV,bV)
    print "Line equation along horizontal: {}*z + {}".format(mH,bH)
    print "Line equation along vertical: {}*z + {}".format(mV,bV)
    theta = ROOT.TMath.ATan(pow((mH**2+mV**2),0.5))
    phi = ROOT.TMath.ATan(mH/mV)
    print "Angles of 3D track: theta is {} and phi is {}".format(theta,phi)  
    DrawPoints(5,hitx,hity,hitz)
    
    lastpoint = ROOT.TVector3(hitx[4],hity[4],hitz[4])
    print "Prova, ",hitx[4], hity[4], hitz[4]
    DrawTrack(theta,phi,lastpoint)

def DrawPoints(nclusters,hitx,hity,hitz):
    """Draws clusters as TEvePointSet"""  
    clusterlist = ROOT.TEvePointSet(3)
    clusterlist.SetElementName("Hits in MuonTagger")
    for icluster in range(nclusters):
     clusterlist.SetPoint(icluster,hitx[icluster],  hity[icluster], hitz[icluster])
     clusterlist.SetMarkerColor(ROOT.kAzure)
    gEve.AddElement(clusterlist)
    #drawing the track

def DrawTrack(theta,phi,lastpoint):
    """Draw track as TEveTrack, propagating backwards from last point provided. A proton of 400 GeV is assumed"""
    recotrack.fV.Set(lastpoint[0], lastpoint[1], lastpoint[2]); #'vertex' of track, here used as starting point
    fakemomentum = 400
    recotrack.fP.Set(fakemomentum * ROOT.TMath.Sin(theta) * ROOT.TMath.Cos(phi), fakemomentum * ROOT.TMath.Sin(theta) * ROOT.TMath.Sin(phi),-fakemomentum * ROOT.TMath.Cos(theta)); #track propagated backwards
    recotrack.fSign = 1

    track = ROOT.TEveTrack(recotrack, prop)
    track.SetName("Test proton")
    track.SetLineColor(ROOT.kRed)
    tracklist.AddElement(track)
    gEve.AddElement(tracklist)

    track.MakeTrack()
    gEve.Redraw3D()


#
def getSlopes(clusters,view=0):
    """using Numpy polyfit to obtain the slopes from the clusters. Adapted from the similar method in driftubeMonitoring.py"""
    x,z=[],[]
    for hit in clusters:     
      if view==0: #horizontal strip, fitting in the zy plane
        x.append(hit[1])
        z.append(hit[2])
      else: #vertical strip, fitting in the zx plane
        x.append(hit[0])
        z.append(hit[2])
    line = numpy.polyfit(z,x,1)
    return line[0],line[1]

# what methods are launched?
GetPixelPositions()