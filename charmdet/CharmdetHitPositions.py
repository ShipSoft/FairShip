from __future__ import print_function, division
from future import standard_library
standard_library.install_aliases()
from builtins import range
import ROOT,os
#ROOT.gROOT.ProcessLine('typedef std::unordered_map<int, std::unordered_map<int, std::unordered_map<int, std::vector<MufluxSpectrometerHit*>>>> nestedList;')
import numpy
from decorators import *
import builtins as builtin
ROOT.gStyle.SetPalette(ROOT.kGreenPink)
PDG = ROOT.TDatabasePDG.Instance()
# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
# stop printing errors
ROOT.gErrorIgnoreLevel = ROOT.kBreak
from argparse import ArgumentParser
import shipunit as u

vbot = ROOT.TVector3()
vtop = ROOT.TVector3()

rnr       = ROOT.TRandom()
#-----prepare python exit-----------------------------------------------
def pyExit():
 ut.errorSummary()
#-----list of arguments--------------------------------------------------
parser = ArgumentParser()
parser.add_argument("-f", "--files", dest="listOfFiles", help="list of files comma separated", required=True)
parser.add_argument("-s", "--scififile", dest="scififilename", help="root file with scifi data", required=True)
parser.add_argument("-nev", "--nevent", dest="nevent", help="number of event to plot", default=0)
parser.add_argument("-w", "--write", dest="writentuple", help="option to write an ntuple",default=False, action='store_true')
parser.add_argument("-o", "--outputfile", dest="outputfilename", help= "outputfile with the ntuples", default="positions.root")
parser.add_argument("-l", "--fileCatalog", dest="catalog", help="list of files in file", default=False)
parser.add_argument("-d", "--Display", dest="withDisplay", help="detector display", default=False,action='store_true')
parser.add_argument("-e", "--eos", dest="onEOS", help="files on EOS", default=False, action='store_true')
parser.add_argument("-u", "--update", dest="updateFile", help="update file", default=False, action='store_true')
#-----accessing file------------------------------------------------------
options = parser.parse_args()

scififile = ROOT.TFile.Open(options.scififilename)
scifitree = scififile.Get('cbmsim')

writentuple = options.writentuple
nevent = int(options.nevent)

fnames = []
if options.catalog:
 tmp = open(options.listOfFiles)
 for x in tmp.readlines():
  fname = x.replace('\n','')
  if fname.find("root")<0:continue
  f=ROOT.TFile.Open(fname)
  sTree = f.cbmsim
  if not sTree.GetBranch("FitTracks"): 
   print("does not contain FitTracks: ",fname)
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
   print("Problem with updateFile: ",f)
   exit(-1)
else:
 sTree = ROOT.TChain('cbmsim')
 for f in fnames: 
  print("add ",f)
  if options.onEOS: sTree.Add(os.environ['EOSSHIP']+f)
  else:             sTree.Add(f)

#-------------------------------geometry initialization
from ShipGeoConfig import ConfigRegistry
ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/charm-geometry_config.py", Setup = 1, cTarget = 1)
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
   #TEve material for track drawing
   tracklist = ROOT.TEveTrackList()
   prop = tracklist.GetPropagator()
   prop.SetMaxZ(20000)
   tracklist.SetName("RK Propagator")
   recotrack = ROOT.TEveRecTrackD()
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

def GetPixelPositions(n=1,draw=True,writentuple=False):
  """ retrieves the position of the pixel hit using the pixel map """
  if not options.withDisplay:  
   draw = False

  sTree.GetEntry(n)
  npixelpoints = 0
  pixelhitslist = []
  pixelhitslist.append(sTree.Digi_PixelHits_1)
  hitx = []
  hity = []
  hitz = []
  for pixelhits in pixelhitslist:
   for hit in pixelhits:
    pos = ROOT.TVector3(0,0,0)
    npixelpoints = npixelpoints + 1
    detID = hit.GetDetectorID()
    hit.GetPixelXYZ(pos,detID)
    #print ("This is the position of our pixel hit: ", detID, pos[0], pos[1], pos[2])
    hitx.append(pos[0])
    hity.append(pos[1])
    hitz.append(pos[2])
    if writentuple: #add pixel hit position to ntuple
     hitnumber = leafnhits[0]
     leafdetID[hitnumber] = detID
     leafposx[hitnumber] = pos[0]
     leafposy[hitnumber] = pos[1]
     leafposz[hitnumber] = pos[2]
     leaftrackID[hitnumber] = 0
     leafsubdetector[hitnumber] = 1
     leafnhits[0] += 1
     # print ("Test tree saving: ", hitnumber, leafdetID[hitnumber], leafposx[hitnumber], leafposy[hitnumber], leafposz[hitnumber])
  if draw:
   DrawPoints(npixelpoints,hitx,hity,hitz,"PixelHits")

def GetSciFiPositions(n=1,draw=True,writentuple=False):
  """ retrieves the position of the pixel hit using the pixel map """
  if not options.withDisplay:   
   draw = False

  scifitree.GetEntry(n+1)
  nscifipoints = 0
  scifihitslist = []
  scifihitslist.append(scifitree.Digi_SciFiHits)
  pos = ROOT.TVector3(0,0,0)
  hitx = []
  hity = []
  hitz = []
  for scifihits in scifihitslist:     
   for hit in scifihits:
    nscifipoints = nscifipoints + 1
    detID = hit.GetDetectorID()
    hit.GetSciFiXYZ(pos,detID)
    #print("This is the position of our scifi hit: ", detID, pos[0], pos[1], pos[2]) 
    hitx.append(pos[0])
    hity.append(pos[1])
    hitz.append(pos[2])
    if writentuple: #add scifi hit position to ntuple
	 hitnumber = leafnhits[0]
	 leafdetID[hitnumber] = detID
	 leafposx[hitnumber] = pos[0]
	 leafposy[hitnumber] = pos[1]
	 leafposz[hitnumber] = pos[2]
	 leaftrackID[hitnumber] = 0
	 leafsubdetector[hitnumber] = 2
         leafnhits[0] += 1
  if draw:
   DrawPoints(nscifipoints,hitx,hity,hitz)


def correctAlignmentRPC(hit,v):
  hit.EndPoints(vtop,vbot) #obtaining hit positions

  if v==1:
    vbot[0] = -vbot[0] -1.21
    vtop[0] = -vtop[0] -1.21
  else:
    vbot[1] = vbot[1] -1.21
    vtop[1] = vtop[1] -1.21
  return vbot,vtop

def GetDTPositions(n=1, draw=True,writentuple=False):
  if not options.withDisplay:
   draw = False
  sTree.GetEntry(n)
  hitlist = sTree.Digi_MufluxSpectrometerHits
  hitx = []
  hity = []
  hitz = []
  npoints = 0
  for hit in hitlist:
    detID = hit.GetDetectorID()

    vtop = ROOT.TVector3(0,0,0)
    vbot = ROOT.TVector3(0,0,0)
    hit.MufluxSpectrometerEndPoints(vtop,vbot, True)

    x = (vbot[0]+vtop[0])/2.
    y = (vbot[1]+vtop[1])/2.
    z = (vbot[2]+vtop[2])/2.
    hitx.append(x)
    hity.append(y)
    hitz.append(z)
    npoints = npoints + 1
    if writentuple: #add pixel hit position to ntuple
     hitnumber = leafnhits[0]
     leafdetID[hitnumber] = detID
     leafposx[hitnumber] = x
     leafposy[hitnumber] = y
     leafposz[hitnumber] = z
     leaftrackID[hitnumber] = 0
     leafsubdetector[hitnumber] = 3
     leafnhits[0] += 1
  if draw:
   DrawPoints(npoints,hitx,hity,hitz,"DTHits")
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
       # print("Postion for view {} and channel {}: ({}, {},{})".format(v,c,x,y,z))

def GetRPCPosition(s,v,c):
  """ Gets RPC Positions from the information of station, view and channel """
  detID = s*10000+v*1000+c
  return RPCPositionsBotTop[detID]

def loadRPCtracks(n=1,draw=True,writentuple=False,fittedtracks=False):
  """ Loads MuonTaggerHits from file and get position of clusters. Fittedtracks is used when reading hits from locally reconstructed tracks by Alessandra"""
  if not options.withDisplay:
   draw = False
  hitx = []
  hity = []
  hitz = []
  npoint = 0
  if fittedtracks:
   npoint=5
   for icluster in range(5):
     hitx.append(0)
     hity.append(0)
     hitz.append(0)

  sTree.GetEntry(n)
  #trackhits = sTree.LocallyTracked_MuonTaggerHits
  trackhits = sTree.Digi_MuonTaggerHits
  clustersH = []
  clustersV = []

  maxntracks = 20 
  maxtrackID = 0
  hitxarray = numpy.zeros((maxntracks,5))
  hityarray = numpy.zeros((maxntracks,5))
  hitzarray = numpy.zeros((maxntracks,5))

  for hit in trackhits:
    detID = hit.GetDetectorID()
    station = int (detID/10000)
    view = int((detID-station*10000)/1000)

    a,b = RPCPositionsBotTop[detID]
    x = (a[0]+b[0])/2.
    y = (a[1]+b[1])/2.
    z = (a[2]+b[2])/2.
    if fittedtracks: #clusters with already fitted tracks
     trackID = int(hit.GetDigi())
     if (trackID > maxtrackID): maxtrackID = trackID
     #adding the point to two different lists according to the view  
     # for each track we have a xyz position at each station (with at most two views)
     if view == 0: #I have yz info     
       hityarray[trackID-1][station-1] = y
       hitzarray[trackID-1][station-1] = z
       clustersH.append([x,y,z])
     elif view == 1: #I have xz info
       hitxarray[trackID-1][station-1] = x
       hitzarray[trackID-1][station-1] = z
       clustersV.append([x,y,z])
    else: 
      hitx.append(x) 
      hity.append(y)
      hitz.append(z)
      npoint = npoint+1 
      if writentuple:
       hitnumber = leafnhits[0]
       leafdetID[hitnumber] = detID
       leafposx[hitnumber] = x
       leafposy[hitnumber] = y
       leafposz[hitnumber] = z
       leaftrackID[hitnumber] = 0
       leafsubdetector[hitnumber] = 4
       leafnhits[0] += 1
    #print("Position of loaded cluster: ({},{},{}), station {} and view {}".format(x,y,z,station,view))    
  #fitting to two 2D tracks
  if fittedtracks:
   mH,bH = getSlopes(clustersH,0) 
   mV,bV = getSlopes(clustersV,1)   
   trackH = ROOT.RPCTrack(mH,bH)
   trackV = ROOT.RPCTrack(mV,bV)
   for itrk in range(maxtrackID):
      for istation in range(5):
        x = hitxarray[itrk,istation]
        y = hityarray[itrk,istation]
        z = hitzarray[itrk,istation]
        #point added to containers for drawing
        hitx[istation] = x
        hity[istation] = y
        hitz[istation] = z
        npoint = 5      
        if x == 0: subdetector = 40 #not paired cluster
        if y == 0: subdetector = 40
        if writentuple:
         hitnumber = leafnhits[0]
         leafdetID[hitnumber] = istation + 1
         leafposx[hitnumber] = x
         leafposy[hitnumber] = y
         leafposz[hitnumber] = z
         leaftrackID[hitnumber] = itrk + 1 
         leafsubdetector[hitnumber] = 4
         leafnhits[0] += 1
  #print("Line equation along horizontal: {}*z + {}".format(mH,bH))
  #print("Line equation along vertical: {}*z + {}".format(mV,bV))
   theta = ROOT.TMath.ATan(pow((mH**2+mV**2),0.5))
   phi = ROOT.TMath.ATan(mH/mV)
  #print("Angles of 3D track: theta is {} and phi is {}".format(theta,phi))  
    
   lastpoint = ROOT.TVector3(hitx[4],hity[4],hitz[4])
   if draw:
      DrawTrack(theta,phi,lastpoint)
  if draw:
   DrawPoints(npoint,hitx,hity,hitz,"MuonTaggerHits")
 

def DrawPoints(nclusters,hitx,hity,hitz, name = "FairShipHits"):
  """Draws clusters as TEvePointSet"""  
  clusterlist = ROOT.TEvePointSet(3)
  clusterlist.SetElementName(name)
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
  line = []
  for hit in clusters:     
    if view==0: #horizontal strip, fitting in the zy plane
      x.append(hit[1])
      z.append(hit[2])
    else: #vertical strip, fitting in the zx plane
      x.append(hit[0])
      z.append(hit[2])
  if (len(x) > 0):
    line = numpy.polyfit(z,x,1)
  else:
    line.append(1000.)
    line.append(1000.)
  return line[0],line[1]

# what methods are launched?
GetPixelPositions(nevent)    
GetSciFiPositions(nevent)
GetDTPositions(nevent)
RPCPosition()
loadRPCtracks(nevent,True,False,fittedtracks = False)

def writeNtuples():
  """write positions of subdetectors into an easy to read ntuple. DetectorID go downstream to upstream, 1: Pixel, 2:SciFi, 3:DT,4:RPC"""
  nevents = sTree.GetEntries()
  print("Start processing", nevents, "nevents")
  for ievent in range(nevents):
   leafnhits[0] = 0 #resetting counter of hits
   GetPixelPositions(ievent, False, True)
   GetDTPositions(ievent, False, True)
   GetSciFiPositions(ievent, False, True)
   loadRPCtracks(ievent, False, True, False)
   outputtree.Fill()
  outputfile.Write()

if writentuple:
 from array import array

 outputfile = ROOT.TFile(options.outputfilename,"RECREATE")
 outputtree = ROOT.TTree("shippositions","Ntuple with hit positions")
 # tree initialization, branches must be arrays in order to pass the addresss
 maxdim = 10000
 leafnhits = array('i',[0])
 leafsubdetector = array( 'i',maxdim*[0])
 leafdetID = array( 'i',maxdim*[0])
 leaftrackID = array( 'i',maxdim*[0])
 leafposx = array('f',maxdim*[0.])
 leafposy = array('f',maxdim*[0.])
 leafposz = array('f',maxdim*[0.])
 #creating the branches
 outputtree.Branch("nhits",leafnhits,"nhits/I")
 outputtree.Branch("detID",leafdetID,"detID[nhits]/I")
 outputtree.Branch("posx",leafposx,"posx[nhits]/F")
 outputtree.Branch("posy",leafposy,"posy[nhits]/F")
 outputtree.Branch("posz",leafposz,"posz[nhits]/F")
 outputtree.Branch("trackID",leaftrackID,"trackID[nhits]/I")
 outputtree.Branch("subdetector",leafsubdetector,"subdetector[nhits]/I")
 writeNtuples()
