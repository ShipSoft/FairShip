#import yep
import ROOT,os,time,sys,operator,atexit
ROOT.gROOT.ProcessLine('typedef std::unordered_map<int, std::unordered_map<int, std::unordered_map<int, std::vector<MufluxSpectrometerHit*>>>> nestedList;')

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
 try: top.Draw('ogl')
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
    #muflux_Reco.setRPCPositions(detID,x,y,z)

def GetRPCPosition(s,v,c):
    detID = s*10000+v*1000+c
    return RPCPositionsBotTop[detID]

#copied from event display, but here we do not have Eve, so what can we do?
def plotRPCTracks(n=1):
    tracklist = ROOT.TEveTrackList()
    prop = tracklist.GetPropagator()
    #prop.SetFitDaughters(kFALSE);
    prop.SetMaxZ(20000)
    tracklist.SetName("RK Propagator")
    #rpc positioning, as from Alessandra's reconstruction
    localRPCfile = ROOT.TFile.Open("localrpctrack_test.root")
    sTree = localRPCfile.Get("RPCTracks")   

    sTree.GetEntry(n)
    localtracks = sTree.RPCTracks
    localtrack = localtracks[0]
    trk_theta = localtrack.GetTheta() * ROOT.TMath.Pi() / 180
    trk_phi = localtrack.GetPhi() * ROOT.TMath.Pi() / 180
#print "Track", id_track, "for run", id_run, ", spill", id_spill, "and trigger", trigger
    #print "Teta and phi angles", trk_teta, " , ", trk_phi
    #print "Slopes (xz, yz): ( ", trk_slopexz, ", ", trk_slopeyz, " )"
    #print " # clusters = ", nclusters

    zoffset = 873 #start in FairShip of firstRPC
    #adding a track
    fakemomentum = 400

    hitx = []
    hity = []
    hitz = []
    for icluster in range(5):
     hitx.append(0)
     hity.append(0)
     hitz.append(0)
    nclusters = localtrack.GetNClusters()

    for i in range(nclusters):

     direction = localtrack.GetClusterDir(i)
     station = localtrack.GetClusterStation(i) - 1
     if (direction == 1):
      hitx[station] = localtrack.GetClusterPos(i)[0]
      hitz[station] = localtrack.GetClusterPos(i)[2]
     else:
      hity[station] = localtrack.GetClusterPos(i)[1]
      hitz[station] = localtrack.GetClusterPos(i)[2]
    
    clusterlist = ROOT.TEvePointSet(3)
    clusterlist.SetElementName("Hits in MuonTagger")
    for icluster in range(5):
     clusterlist.SetPoint(icluster,hitx[icluster],  hity[icluster], hitz[icluster] + zoffset);
     clusterlist.SetMarkerColor(ROOT.kAzure)
    gEve.AddElement(clusterlist)

    recotrack = ROOT.TEveRecTrackD()
    recotrack.fV.Set(hitx[4], hity[4], hitz[4] + 873.); #'vertex' of track, here used as starting point
    #recotrack.fP.Set(0,0,400)
    recotrack.fP.Set(fakemomentum * ROOT.TMath.Sin(trk_theta) * ROOT.TMath.Cos(trk_phi), fakemomentum * ROOT.TMath.Sin(trk_theta) * ROOT.TMath.Sin(trk_phi),-fakemomentum * ROOT.TMath.Cos(trk_theta)); #track propagated backwards
    recotrack.fSign = 1

    track = ROOT.TEveTrack(recotrack, prop)
    #track.SetName(Form("Charge %d", sign));
    track.SetLineColor(ROOT.kRed)

    gEve.AddElement(tracklist)
    tracklist.AddElement(track)

    track.MakeTrack()

    gEve.Redraw3D()
    
