import ROOT
import os,sys,subprocess,atexit
from array import array
import shipunit as u
import SndlhcMuonReco
import rootUtils as ut
from decorators import *
from rootpyPickler import Unpickler
import time
from XRootD import client

import numpy as np

from datetime import datetime
from pathlib import Path

import logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.WARNING)
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.FATAL)

ROOT.gStyle.SetPalette(ROOT.kViridis)
ROOT.gInterpreter.ProcessLine('#include "'+os.environ['SNDSW_ROOT']+'/analysis/tools/sndSciFiTools.h"')

def pyExit():
       "unfortunately need as bypassing an issue related to use xrootd"
       os.system('kill '+str(os.getpid()))
atexit.register(pyExit)


A,B = ROOT.TVector3(),ROOT.TVector3()

eventComment = {}   # possibility to add an event comment before moving to next event

h={}
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-r", "--runNumber", dest="runNumber", help="run number", type=int,required=False)
parser.add_argument("-p", "--path", dest="path", help="path to data file",required=False,default=os.environ["EOSSHIP"]+"/eos/experiment/sndlhc/convertedData/physics/2022/")
parser.add_argument("-f", "--inputFile", dest="inputFile", help="input file data and MC",default="",required=False)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", default=os.environ["EOSSHIP"]+"/eos/experiment/sndlhc/convertedData/physics/2022/geofile_sndlhc_TI18_V0_2022.root")
parser.add_argument("-P", "--partition", dest="partition", help="partition of data", type=int,required=False,default=-1)
parser.add_argument("--server", dest="server", help="xrootd server",default=os.environ["EOSSHIP"])
parser.add_argument("--no-extraInfo", dest="extraInfo", action="store_false", help="Do not print extra information on the event.")

parser.add_argument("--extension", help="Extension of file to save. E.g. png, pdf, root, etc.", default="png")
parser.add_argument("--rootbatch", help="Run ROOT in batch mode.", action="store_true")

parser.add_argument("--collision_axis", dest="drawCollAxis", help="Draw collision axis", action="store_true")

parser.add_argument("-par", "--parFile", dest="parFile", help="parameter file", default=os.environ['SNDSW_ROOT']+"/python/TrackingParams.xml")
parser.add_argument("-hf", "--HoughSpaceFormat", dest="HspaceFormat", help="Hough space representation. Should match the 'Hough_space_format' name in parFile, use quotes", default='linearSlopeIntercept')

parser.add_argument("--shower_dir", dest="drawShowerDir", help="Draw shower direction if a shower is found", action="store_true")

options = parser.parse_args()

resolution_factor = 1
if options.rootbatch:
   ROOT.gROOT.SetBatch()
   # Produce figures larger than the screen resolution. E.g., for printing.
   resolution_factor = 2

options.storePic = ''
trans2local = False
runInfo = False
try:
   fg  = ROOT.TFile.Open(options.server+options.p+"RunInfodict.root")
   pkl = Unpickler(fg)
   runInfo = pkl.load('runInfo')
   fg.Close()
except: pass

import SndlhcGeo
geo = SndlhcGeo.GeoInterface(options.geoFile)

lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
lsOfGlobals.Add(geo.modules['Scifi'])
lsOfGlobals.Add(geo.modules['MuFilter'])

detSize = {}
em = geo.snd_geo.EmulsionDet
si = geo.snd_geo.Scifi
detSize[0] =[si.channel_width, si.channel_width, si.scifimat_z ]
mi = geo.snd_geo.MuFilter
if hasattr(mi, "Veto3BarX"): vetoXdim = mi.Veto3BarX/2
else: vetoXdim = mi.VetoBarX/2
detSize[1] =[vetoXdim, mi.VetoBarY/2, mi.VetoBarZ/2]
detSize[2] =[mi.UpstreamBarX/2, mi.UpstreamBarY/2, mi.UpstreamBarZ/2]
detSize[3] =[mi.DownstreamBarX_ver/2,mi.DownstreamBarY/2,mi.DownstreamBarZ/2]
withDetector = True  # False is useful when using zoom
with2Points = False  # plot start and end point of straw/bar
mc = False

firstScifi_z = 300 * u.cm
# Initialize FairLogger: set severity and verbosity
logger = ROOT.FairLogger.GetLogger()
logger.SetColoredLog(True)
logger.SetLogVerbosityLevel('low')
logger.SetLogScreenLevel('WARNING')
logger.SetLogToScreen(True)

run      = ROOT.FairRunAna()
ioman = ROOT.FairRootManager.Instance()

if options.inputFile=="":
  f=ROOT.TFile.Open(options.path+'sndsw_raw_'+str(options.runNumber).zfill(6)+'.root')
else:
  f=ROOT.TFile.Open(options.path+options.inputFile)

if f.FindKey('cbmsim'):
        eventTree = f.Get("cbmsim")
        runId = 'sim'
        if eventTree.GetBranch('ScifiPoint'): mc = True
else:   
        eventTree = f.Get("rawConv")
        ioman.SetTreeName('rawConv')

outFile = ROOT.TMemFile('dummy','CREATE')
source = ROOT.FairFileSource(f)
run.SetSource(source)
sink = ROOT.FairRootFileSink(outFile)
run.SetSink(sink)

HT_tasks = {'muon_reco_task_Sf':SndlhcMuonReco.MuonReco(),
            'muon_reco_task_DS':SndlhcMuonReco.MuonReco(),
            'muon_reco_task_nuInt':SndlhcMuonReco.MuonReco()}
for ht_task in HT_tasks.values():
    run.AddTask(ht_task)

import SndlhcTracking
trackTask = SndlhcTracking.Tracking() 
trackTask.SetName('simpleTracking')
run.AddTask(trackTask)

#avoiding some error messages
xrdb = ROOT.FairRuntimeDb.instance()
xrdb.getContainer("FairBaseParSet").setStatic()
xrdb.getContainer("FairGeoParSet").setStatic()

for ht_task in HT_tasks.values():
    ht_task.SetParFile(options.parFile)
    ht_task.SetHoughSpaceFormat(options.HspaceFormat)
    # force the output of reco task to genfit::Track
    # as the display code looks for such output
    ht_task.ForceGenfitTrackFormat()
HT_tasks['muon_reco_task_Sf'].SetTrackingCase('passing_mu_Sf')
HT_tasks['muon_reco_task_DS'].SetTrackingCase('passing_mu_DS')
HT_tasks['muon_reco_task_nuInt'].SetTrackingCase('nu_interaction_products')

run.Init()
OT = sink.GetOutTree()
eventTree = ioman.GetInTree()
eventTree.GetEvent(0)
if eventTree.EventHeader.ClassName() == 'SNDLHCEventHeader':
   geo.modules['Scifi'].InitEvent(eventTree.EventHeader)
   geo.modules['MuFilter'].InitEvent(eventTree.EventHeader)
# if faireventheader, rely on user to select correct geofile.

if eventTree.GetBranch('Digi_MuFilterHit'):
# backward compatbility for early converted events
  eventTree.GetEvent(0)
  eventTree.Digi_MuFilterHits = eventTree.Digi_MuFilterHit

nav = ROOT.gGeoManager.GetCurrentNavigator()

# get filling scheme
try:
           runNumber = eventTree.EventHeader.GetRunId()
           fg  = ROOT.TFile.Open(os.environ['EOSSHIP']+options.p+'FSdict.root')
           pkl = Unpickler(fg)
           FSdict = pkl.load('FSdict')
           fg.Close()
           if runNumber in FSdict: fsdict = FSdict[runNumber]
           else:  fsdict = False
except:
           print('continue without knowing filling scheme')
           fsdict = False

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

def userProcessing(event):
    '''User hook to add action after event is plotted.

    Useful for adding special objects to the display for example.
    An example for display of 3-track events with external reco:

    ```python
    trackTask.multipleTrackCandidates(
        nMaxCl=8, dGap=0.2, dMax=0.8, dMax3=0.8, ovMax=1, doublet=True, debug=False
    )
    n3D = [0, 0]
    for p in range(2):
        tc = h['simpleDisplay'].cd(-p + 2)
        for trackId in trackTask.multipleTrackStore['trackCand'][p]:
            if trackId < 100000 and not trackTask.multipleTrackStore['doublet']:
                continue
            if trackId in trackTask.multipleTrackStore['cloneCand'][p]:
                continue
            n3D[p] += 1
            rc = trackTask.multipleTrackStore['trackCand'][p][trackId].Fit('pol1', 'SQ')
            trackTask.multipleTrackStore['trackCand'][p][trackId].Draw('same')
        tc.Update()
    print('Number of full tracks', n3D)
    return True
    ```
    '''
    return

def bunchXtype():
# check for b1,b2,IP1,IP2
        xing = {'all':True,'B1only':False,'B2noB1':False,'noBeam':False}
        if fsdict:
             T   = eventTree.EventHeader.GetEventTime()
             bunchNumber = int(T%(4*3564)/4+0.5)
             nb1 = (3564 + bunchNumber - fsdict['phaseShift1'])%3564
             nb2 = (3564 + bunchNumber - fsdict['phaseShift1']- fsdict['phaseShift2'])%3564
             b1 = nb1 in fsdict['B1']
             b2 = nb2 in fsdict['B2']
             IP1 = False
             IP2 = False
             if b1:
                IP1 =  fsdict['B1'][nb1]['IP1']
             if b2:
                IP2 =  fsdict['B2'][nb2]['IP2']
             if b2 and not b1:
                xing['B2noB1'] = True
             if b1 and not b2 and not IP1:
                xing['B1only'] = True
             if not b1 and not b2: xing['noBeam'] = True
        return xing

def getSciFiHitDensity(g, x_range=0.5):
       """Takes ROOT TGraph g and returns array with number of hits within x_range cm of each hit."""
       ret = []
       for i in range(g.GetN()):
              x_i = g.GetPointX(i)
              y_i = g.GetPointY(i)
              density = 0
              for j in range(g.GetN()):
                     x_j = g.GetPointX(j)
                     y_j = g.GetPointY(j)
                     if ((x_i - x_j)**2 + (y_i - y_j)**2) <= x_range**2:
                            density += 1
              ret.append(density)
       return ret
                       
def drawLegend(max_density, max_QDC, n_legend_points, darkMode=False):
       """Draws legend for hit colour"""
       h['simpleDisplay'].cd(1)
       n_legend_points = 5
       padLegScifi = ROOT.TPad("legend","legend",0.4,0.15,0.4+0.27, 0.15+0.25)
       padLegScifi.SetFillStyle(4000)
       padLegScifi.Draw()
       padLegScifi.cd()
       text_scifi_legend = ROOT.TLatex()
       text_scifi_legend.SetTextAlign(11)
       text_scifi_legend.SetTextFont(42)
       text_scifi_legend.SetTextSize(.15)
       if darkMode: text_scifi_legend.SetTextColor(ROOT.kWhite)
       for i in range(n_legend_points) :
              if i < (n_legend_points - 1) :
                     text_scifi_legend.DrawLatex((i+0.3)*(1./(n_legend_points+2)), 0.2, "{:d}".format(int(i*max_density/(n_legend_points-1))))
                     text_scifi_legend.DrawLatex((i+0.3)*(1./(n_legend_points+2)), 0.,  "{:.0f}".format(int(i*max_QDC/(n_legend_points-1))))
              else :
                     text_scifi_legend.DrawLatex((i+0.3)*(1./(n_legend_points+2)), 0.2, "{:d} SciFi hits/cm".format(int(i*max_density/(n_legend_points-1))))
                     text_scifi_legend.DrawLatex((i+0.3)*(1./(n_legend_points+2)), 0.,  "{:.0f} QDC units".format(int(i*max_QDC/(n_legend_points-1))))
                     
              h["markerCollection"].append(ROOT.TEllipse((i+0.15)*(1./(n_legend_points+2)), 0.26, 0.05/4, 0.05))
              if not darkMode:
                  h["markerCollection"][-1].SetFillColor(ROOT.TColor.GetPalette()[int(float(i*max_density/(n_legend_points-1))/max_density*(len(ROOT.TColor.GetPalette())-1))])
              else:
                  h["markerCollection"][-1].SetFillColor(ROOT.TColor.GetPalette()[int((1/4+3/4*float(i*max_density/(n_legend_points-1))/max_density)*(len(ROOT.TColor.GetPalette())-1))])
              h["markerCollection"][-1].Draw("SAME")
              
              h["markerCollection"].append(ROOT.TBox((i+0.15)*(1./(n_legend_points+2))-0.05/4 , 0.06 - 0.05, (i+0.15)*(1./(n_legend_points+2))+0.05/4, 0.06 + 0.05))
              if not darkMode:
                  h["markerCollection"][-1].SetFillColor(ROOT.TColor.GetPalette()[int(float(i*max_QDC/(n_legend_points-1))/max_QDC*(len(ROOT.TColor.GetPalette())-1))])
              else:
                  h["markerCollection"][-1].SetFillColor(ROOT.TColor.GetPalette()[int((1/4+3/4*float(i*max_QDC/(n_legend_points-1))/max_QDC)*(len(ROOT.TColor.GetPalette())-1))])
              h["markerCollection"][-1].Draw("SAME")

def drawSciFiHits(g, colour):
       """Takes TGraph g and draws the graphs markers with the TColor given in list colour."""
       n = g.GetN()
       # Draw highest density points last
       sorted_indices = np.argsort(colour)
       for i_unsorted in range(0, n):
              i = int(sorted_indices[i_unsorted])

              x = g.GetPointX(i)
              y = g.GetPointY(i)

              h["markerCollection"].append(ROOT.TEllipse(x, y, 1.5, 1.5))
              h["markerCollection"][-1].SetLineWidth(0)
              h["markerCollection"][-1].SetFillColor(colour[i])
              h["markerCollection"][-1].Draw("SAME")
 
def loopEvents(
              start=0,
              save=False,
              goodEvents=False,
              withTrack=-1,
              withHoughTrack=-1,
              nTracks=0,
              minSipmMult=1,
              withTiming=False,
              option=None,
              Setup='TI18',
              verbose=0,
              auto=False,
              hitColour=None,
              FilterScifiHits=None,
              darkMode=False
              ):
 if darkMode:
     ROOT.gStyle.SetCanvasColor(ROOT.kBlack)
     
 # check the format of FilterScifiHits if set
 if FilterScifiHits: 
    important_keys = {"bins_x", "min_x", "max_x", "time_lower_range", "time_upper_range"}
    all_keys = important_keys.copy()
    all_keys.add("method")
    filter_parameters = {"bins_x":52., "min_x":0., "max_x":26.,
                         "time_lower_range":1E9/(2*u.snd_freq/u.hertz),
                         "time_upper_range":2E9/(u.snd_freq/u.hertz),
                         "method":0}
    if FilterScifiHits!="default" and not important_keys.issubset(FilterScifiHits): 
       logging.fatal("Invalid FilterScifiHits format. Two options are supported:\n"
       "#1 FilterScifiHits = 'default'\nwhich sets the default parameters:\n"+
       str(filter_parameters)+" or\n"
       "#2 FilterScifiHits = filter_dictionary \nwhere filter_dictionary has all of the following keys\n"+
       str(important_keys)+"\nAn additional key 'method' exists: its single supported value, also default, is 0.")
       return
    if FilterScifiHits!="default" and any(k not in all_keys for k in FilterScifiHits):
       logging.warning("Ignoring provided keys other than "+str(all_keys))

 if 'simpleDisplay' not in h: 
    ut.bookCanvas(h,key='simpleDisplay',title='simple event display',nx=1200,ny=1016,cx=1,cy=2)

 h['simpleDisplay'].cd(1)
 # TI18 coordinate system
 zStart = 250.
 zEnd = 600.
 xStart = -100.
 yStart =  -30.
 if Setup == 'H6': zStart = 60.
 if Setup == 'TP': zStart = -50. # old coordinate system with origin in middle of target
 if Setup == 'H4': 
   xStart = -110.
   yStart = -10.
   zStart = 300.
   zEnd = 430.
 if 'xz' in h: 
    h.pop('xz').Delete()
    h.pop('yz').Delete()
 else:
    h['xmin'],h['xmax'] = xStart,xStart+110.
    h['ymin'],h['ymax'] = yStart,yStart+110.
    h['zmin'],h['zmax'] = zStart,zEnd
    for d in ['xmin','xmax','ymin','ymax','zmin','zmax']: h['c'+d]=h[d]
 ut.bookHist(h,'xz','; z [cm]; x [cm]',500,h['czmin'],h['czmax'],100,h['cxmin'],h['cxmax'])
 ut.bookHist(h,'yz','; z [cm]; y [cm]',500,h['czmin'],h['czmax'],100,h['cymin'],h['cymax'])
 if darkMode:
    for hist in [h['xz'], h['yz']]:
        # set axis lines, labels, titles to white in dark mode
        hist.GetXaxis().SetAxisColor(ROOT.kWhite)
        hist.GetYaxis().SetAxisColor(ROOT.kWhite)
        hist.GetXaxis().SetLabelColor(ROOT.kWhite)
        hist.GetYaxis().SetLabelColor(ROOT.kWhite)
        hist.GetXaxis().SetTitleColor(ROOT.kWhite)
        hist.GetYaxis().SetTitleColor(ROOT.kWhite)

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
 if withTrack==0 or withHoughTrack==0: OT = eventTree
 if type(start) == type(1):
    s = start
    e = event.GetEntries()
 else:
    s = 0
    e = len(start)
 for N in range(s,e):
    if type(start) == type(1): rc = event.GetEvent(N)
    else: rc = event.GetEvent(start[N])
    if goodEvents and not goodEvent(event): continue
    nHoughtracks = 0
    OT.Reco_MuonTracks = ROOT.TObjArray(10)
    if withHoughTrack > 0:
       rc = source.GetInTree().GetEvent(N)
       # Delete SndlhcMuonReco kalman tracks container
       for ht_task in HT_tasks.values():
           ht_task.kalman_tracks.Delete()
       if withHoughTrack==1:
            HT_tasks['muon_reco_task_Sf'].Exec(0)
            HT_tasks['muon_reco_task_DS'].Exec(0)
       elif withHoughTrack==2:
            HT_tasks['muon_reco_task_Sf'].Exec(0)
       elif withHoughTrack==3:
            HT_tasks['muon_reco_task_DS'].Exec(0)
       elif withHoughTrack==4:
            HT_tasks['muon_reco_task_nuInt'].Exec(0)
       # Save the tracks in OT.Reco_MuonTracks object
       for ht_task in HT_tasks.values():
           for trk in ht_task.kalman_tracks:
               OT.Reco_MuonTracks.Add(trk)
       nHoughtracks = OT.Reco_MuonTracks.GetEntries()
       if nHoughtracks>0: print('number of tracks by HT:', nHoughtracks)

    if withTrack > 0:
          # Delete SndlhcTracking fitted tracks container
          trackTask.fittedTracks.Delete()
          if withTrack==1:
              trackTask.ExecuteTask("ScifiDS")
          elif withTrack==2:
              trackTask.ExecuteTask("Scifi")
          elif withTrack==3:
              trackTask.ExecuteTask("DS")
          # Save found tracks
          for trk in trackTask.fittedTracks:
              OT.Reco_MuonTracks.Add(trk)
          ntracks = len(OT.Reco_MuonTracks) - nHoughtracks
          if ntracks>0: print('number of tracks by ST:', ntracks)
    nAlltracks = len(OT.Reco_MuonTracks)
    if nAlltracks<nTracks: continue

    if verbose>0:
       for aTrack in OT.Reco_MuonTracks:
           print(aTrack.__repr__())
           mom    = aTrack.getFittedState().getMom()
           pos      = aTrack.getFittedState().getPos()
           mom.Print()
           pos.Print()
    T,dT = 0,0
    T = event.EventHeader.GetEventTime()
    runId = eventTree.EventHeader.GetRunId()
    if Tprev >0: dT = T-Tprev
    Tprev = T
    if nAlltracks > 0: print('total number of tracks: ', nAlltracks)

    digis = []
    if event.FindBranch("Digi_ScifiHits"):
       scifi_digis = event.Digi_ScifiHits
       method = 0
       if FilterScifiHits!=None and FilterScifiHits!="default":
          filter_parameters = {k: FilterScifiHits[k] for k in important_keys if k in FilterScifiHits}
          method = FilterScifiHits.get("method", 0) # set to the default 0, if item is not provided
       if FilterScifiHits and (Setup=="TI18" or Setup=="H8" or Setup=="H4"):
          setup = Setup
          # Only H8 is explicitly supported in the SciFi tools. However, the same baby SciFi
          # system was reused in H4. It is then safe to use the SciFi tools for H4 as well.
          if Setup =="H4":
            setup ="H8"
          # Convert the filter_parameters to the needed std.map format
          selection_parameters = ROOT.std.map('string', 'float')()
          selection_parameters["bins_x"] = float(filter_parameters["bins_x"])
          selection_parameters["min_x"] = float(filter_parameters["min_x"])
          selection_parameters["max_x"] = float(filter_parameters["max_x"])
          selection_parameters["time_lower_range"] = float(filter_parameters["time_lower_range"])
          selection_parameters["time_upper_range"] = float(filter_parameters["time_upper_range"])
          scifi_digis = ROOT.snd.analysis_tools.filterScifiHits(event.Digi_ScifiHits,selection_parameters,method,setup,mc)
       else:
          if FilterScifiHits:
             logging.warning(Setup+" is not supported for the time-filtering of SciFi hits, using all hits instead.")
    digis.append(scifi_digis)
    run_conf = ROOT.snd.Configuration.Option.ti18_2022_2023
    if Setup=='TI18' or Setup=="H6":
      run_conf = ROOT.snd.Configuration.Option.ti18_2022_2023
    elif Setup == "H8":
      ROOT.snd.Configuration.Option.test_beam_2023
    elif Setup == "H4":
      ROOT.snd.Configuration.Option.test_beam_2024
    else:
      print("Going for default setup TI18")
    configuration = ROOT.snd.Configuration(run_conf, geo.modules['Scifi'], geo.modules['MuFilter'], mc)
    scifi_planes = ROOT.snd.analysis_tools.FillScifi(configuration, scifi_digis, geo.modules['Scifi'])
    us_planes = ROOT.snd.analysis_tools.FillUS(configuration, event.Digi_MuFilterHits, geo.modules['MuFilter'])
    if event.FindBranch("Digi_MuFilterHits"): digis.append(event.Digi_MuFilterHits)
    if event.FindBranch("Digi_MuFilterHit"): digis.append(event.Digi_MuFilterHit)
    empty = True
    for x in digis:
       if x.GetEntries()>0:
         if empty: print( "event -> %i"%N)
         empty = False
    if empty: continue
    h['hitCollectionX']= {'Veto':[0,ROOT.TGraphErrors()],'Scifi':[0,ROOT.TGraphErrors()],'DS':[0,ROOT.TGraphErrors()]}
    h['hitCollectionY']= {'Veto':[0,ROOT.TGraphErrors()],'Scifi':[0,ROOT.TGraphErrors()],'US':[0,ROOT.TGraphErrors()],'DS':[0,ROOT.TGraphErrors()]}
    if hitColour:
           h['hitColourX'] = {'Veto': [], 'Scifi': [], 'DS' : []}
           h['hitColourY'] = {'Veto': [], 'Scifi' : [], 'US' : [], 'DS' : []}
           h["markerCollection"] = []

    h['firedChannelsX']= {'Veto':[0,0,0,0],'Scifi':[0,0,0],'DS':[0,0,0]}
    h['firedChannelsY']= {'Veto':[0,0,0,0],'Scifi':[0,0,0],'US':[0,0,0,0],'DS':[0,0,0,0]}
    systems = {1:'Veto',2:'US',3:'DS',0:'Scifi'}
    for collection in ['hitCollectionX','hitCollectionY']:
       for c in h[collection]:
          rc=h[collection][c][1].SetName(c)
          rc=h[collection][c][1].Set(0)

    if hitColour:
           h["markerCollection"] = []

    #Do we still use these lines? Seems no. 
    #And for events having all negative QDCs minT[1] is returned empty and the display crashes.
    #dTs = "%5.2Fns"%(dT/u.snd_freq*1E9)
    # find detector which triggered
    #minT = firstTimeStamp(event)
    #dTs+= "    " + str(minT[1].GetDetectorID())
    for p in proj:
       rc = h[ 'simpleDisplay'].cd(p)
       h[proj[p]].Draw('b')

    if options.drawCollAxis:
       for k in proj:
          drawCollisionAxis(h['simpleDisplay'], k)
       
    if withDetector:
      drawDetectors(darkMode=darkMode)
    for D in digis:
      for digi in D:
         detID = digi.GetDetectorID()
         sipmMult = 1
         if digi.GetName()  == 'MuFilterHit':
            system = digi.GetSystem()
            geo.modules['MuFilter'].GetPosition(detID,A,B)
            sipmMult = len(digi.GetAllSignals(False,False))
            if sipmMult<minSipmMult and (system==1 or system==2): continue
         else:
            geo.modules['Scifi'].GetSiPMPosition(detID,A,B)
            system = 0
         curPath = nav.GetPath()
         tmp = curPath.rfind('/')
         nav.cd(curPath[:tmp])
         first = True
         for X in [A, B]:
             if not first and not with2Points:
                 continue
             first = False
             globA, locA = array('d', [X[0], X[1], X[2]]), array('d', [X[0], X[1], X[2]])
             if trans2local:
                 nav.MasterToLocal(globA, locA)
             Z = X[2]
             if digi.isVertical():
                   # only using hits with positive qdc for centroids, so only show such
                   if options.drawShowerDir and system==0 and digi.GetSignal(0)<0:
                     continue
                   collection = 'hitCollectionX'
                   Y = locA[0]
                   sY = detSize[system][0]
             else:
                   # only using hits with positive qdc for centroids, so only show such
                   if options.drawShowerDir and system==0 and digi.GetSignal(0)<0:
                     continue
                   collection = 'hitCollectionY'
                   Y = locA[1]
                   sY = detSize[system][1]
             c = h[collection][systems[system]]
             rc = c[1].SetPoint(c[0], Z, Y)
             rc = c[1].SetPointError(c[0], detSize[system][2], sY)
             c[0] += 1
         if hitColour == "q" :
                max_QDC = 200 * 16
                this_qdc = 0
                ns = max(1,digi.GetnSides())
                for side in range(ns):
                       for m in  range(digi.GetnSiPMs()):
                              qdc = digi.GetSignal(m+side*digi.GetnSiPMs())
                              if not qdc < 0  :
                                     this_qdc += qdc
                if this_qdc > max_QDC :
                       this_qdc = max_QDC
                if not darkMode:
                    fillNode(curPath, ROOT.TColor.GetPalette()[int(this_qdc/max_QDC*(len(ROOT.TColor.GetPalette())-1))])
                else:  # for dark mode, only use the lighter part of the colormap; the dark hues have bad contrast
                    fillNode(curPath, ROOT.TColor.GetPalette()[int((1/4 + 3/4*this_qdc/max_QDC) * (len(ROOT.TColor.GetPalette())-1))])
         else :
                fillNode(curPath, darkMode=darkMode)

         if digi.isVertical():  F = 'firedChannelsX'
         else:                     F = 'firedChannelsY'
         ns = max(1,digi.GetnSides())
         for side in range(ns):
             for m in  range(digi.GetnSiPMs()):
                   qdc = digi.GetSignal(m+side*digi.GetnSiPMs())
                   if qdc < 0 and qdc > -900:  h[F][systems[system]][1]+=1
                   elif not qdc<0:   
                       h[F][systems[system]][0]+=1
                       if len(h[F][systems[system]]) < 2+side: continue
                       h[F][systems[system]][2+side]+=qdc
    h['hitCollectionY']['Scifi'][1].SetMarkerColor(ROOT.kBlue+2 if not darkMode else ROOT.kBlue-4)
    h['hitCollectionX']['Scifi'][1].SetMarkerColor(ROOT.kBlue+2 if not darkMode else ROOT.kBlue-4)

    if hitColour == "q" :
       for orientation in ['X', 'Y']:
              max_density = 40
              density = np.clip(0, max_density, getSciFiHitDensity(h['hitCollection'+orientation]['Scifi'][1]))
              for i in range(h['hitCollection'+orientation]['Scifi'][1].GetN()) :
                  if not darkMode:
                      h['hitColour'+orientation]['Scifi'].append(ROOT.TColor.GetPalette()[int(float(density[i])/max_density*(len(ROOT.TColor.GetPalette())-1))])
                  else:  # for dark mode, only use the lighter part of the colormap; the dark hues have bad contrast
                      h['hitColour'+orientation]['Scifi'].append(ROOT.TColor.GetPalette()[int((1/4 + 3/4*float(density[i])/max_density) * (len(ROOT.TColor.GetPalette())-1))])

       drawLegend(max_density, max_QDC, 5, darkMode=darkMode)
                         
    k = 1
    moreEventInfo = []


    for collection in ['hitCollectionX','hitCollectionY']:
       h['simpleDisplay'].cd(k)
       drawInfo(h['simpleDisplay'], k, runId, N, T, darkMode=darkMode)
       k+=1
       for c in h[collection]:
          F = collection.replace('hitCollection','firedChannels')
          pj = collection.split('ion')[1]
          if pj =="X" or c=="Scifi":
              atext = "%1s %5s %3i  +:%3i -:%3i qdc :%5.1F"%(pj,c,h[collection][c][1].GetN(),h[F][c][0],h[F][c][1],h[F][c][2])
          else:
              atext = "%1s %5s %3i  +:%3i -:%3i qdcL:%5.1F qdcR:%5.1F"%(pj,c,h[collection][c][1].GetN(),h[F][c][0],h[F][c][1],h[F][c][2],h[F][c][3])
          moreEventInfo.append(atext)
          print(atext)
          if h[collection][c][1].GetN()<1: continue
          if c=='Scifi':
              if hitColour not in ["q"] :
                     h[collection][c][1].SetMarkerStyle(20)
                     h[collection][c][1].SetMarkerSize(1.5)
                     rc=h[collection][c][1].Draw('sameP')
                     h['display:'+c]=h[collection][c][1]
              elif hitColour == "q" :
                     drawSciFiHits(h[collection][c][1], h['hitColour'+collection[-1]][c])
                               
    T0 = eventTree.EventHeader.GetEventTime()
    if type(start) == type(1): rc = event.GetEvent(N-1)
    else: rc = event.GetEvent(start[N]-1)
    delTM1 = eventTree.EventHeader.GetEventTime() - T0
    if type(start) == type(1): rc = event.GetEvent(N+1)
    else: rc = event.GetEvent(start[N]+1)
    delTP1 = eventTree.EventHeader.GetEventTime() - T0
    atext = "timing info, prev event: %6i cc  next event: %6i cc"%(delTM1,delTP1)
    moreEventInfo.append(atext)
    if type(start) == type(1): rc = event.GetEvent(N)
    else: rc = event.GetEvent(start[N])

    k = 1
    for collection in ['hitCollectionX','hitCollectionY']:
       h['simpleDisplay'].cd(k)
       drawInfo(h['simpleDisplay'], k, runId, N, T,moreEventInfo, darkMode=darkMode)
       k+=1
            
    h['simpleDisplay'].Update()
    if withTiming: timingOfEvent()
    addTrack(OT, darkMode=darkMode)

    # try finding shower direction and intercept
    if options.drawShowerDir:
       sh_scifi_planes, sh_us_planes = ROOT.snd.analysis_tools.GetShoweringPlanes(scifi_planes, us_planes)
       ref_point, shower_direction = ROOT.snd.analysis_tools.GetShowerInterceptAndDirection(configuration, sh_scifi_planes, sh_us_planes)
       is_nan = np.isnan([ref_point.X(), ref_point.Y(), ref_point.Z(), shower_direction.X(), shower_direction.Y(), shower_direction.Z()]).any()
       if is_nan:
          print("Found shower direction and/or intercept contain NaN value")
       # try finding the shower origin
       else:
          shower_start = 10*ROOT.snd.analysis_tools.GetScifiShowerStart(scifi_planes)
          if shower_start<0:
             print("Could not find shower start in SciFi, going for US")
             shower_start = 100*ROOT.snd.analysis_tools.GetUSShowerStart(us_planes)
          if shower_start<0:
             print("Could not find shower start in SciFi or in US")
          else:
             for k in proj:
                 if k==1:
                    drawShowerAxis(h['simpleDisplay'], k, shower_start, ref_point.X(),
                                                       shower_direction.X()/shower_direction.Z())
                 else:
                    drawShowerAxis(h['simpleDisplay'], k, shower_start, ref_point.Y(),
                                                       shower_direction.Y()/shower_direction.Z())
    h['simpleDisplay'].Update()

    if option == "2tracks": 
          rc = twoTrackEvent(sMin=10,dClMin=7,minDistance=0.5,sepDistance=0.5, darkMode=darkMode)
          if not rc: rc = twoTrackEvent(sMin=10,dClMin=7,minDistance=0.5,sepDistance=0.75, darkMode=darkMode)
          if not rc: rc = twoTrackEvent(sMin=10,dClMin=7,minDistance=0.5,sepDistance=1.0, darkMode=darkMode)
          if not rc: rc = twoTrackEvent(sMin=10,dClMin=7,minDistance=0.5,sepDistance=1.75, darkMode=darkMode)
          if not rc: rc = twoTrackEvent(sMin=10,dClMin=7,minDistance=0.5,sepDistance=2.5, darkMode=darkMode)
          if not rc: rc = twoTrackEvent(sMin=10,dClMin=7,minDistance=0.5,sepDistance=3.0, darkMode=darkMode)

    if verbose>0: dumpChannels()
    userProcessing(event)

    if save:
        h['simpleDisplay'].Print('{:0>2d}-event_{:04d}'.format(runId, N) + '.' + options.extension)
    if auto:
        h['simpleDisplay'].Print(options.storePic + str(runId) + '-event_' + str(event.EventHeader.GetEventNumber()) + '.' + options.extension)
    if not auto:
       rc = input("hit return for next event or p for print or q for quit: ")
       if rc=='p': 
           h['simpleDisplay'].Print(options.storePic + str(runId) + '-event_' + str(event.EventHeader.GetEventNumber()) + '.' + options.extension)
       elif rc == 'q':
          break
       else:
          eventComment[f"{runId}-event_{event.EventHeader.GetEventNumber()}"] = rc
 if save:
     os.system("convert -delay 60 -loop 0 event*." + options.extension + " animated.gif")

def addTrack(OT,scifi=False, darkMode=False):
   xax = h['xz'].GetXaxis()
   nTrack = 0
   for   aTrack in OT.Reco_MuonTracks:
      trackColor = ROOT.kRed
      if aTrack.GetUniqueID()==1:
          trackColor = ROOT.kBlue+2 if not darkMode else ROOT.kBlue-4
          flightDir = trackTask.trackDir(aTrack)
          print('flight direction: %5.3F  significance: %5.3F'%(flightDir[0],flightDir[1]))
      if aTrack.GetUniqueID()==3: trackColor = ROOT.kBlack if not darkMode else ROOT.kWhite
      if aTrack.GetUniqueID()==11: trackColor = ROOT.kAzure-2 if not darkMode else ROOT.kAzure-3 # HT scifi track
      if aTrack.GetUniqueID()==13: trackColor = ROOT.kGray+2 if not darkMode else ROOT.kGray # HT ds track
      # HT cross-system track fit
      if aTrack.GetUniqueID()==15: trackColor = ROOT.kOrange+7
      S = aTrack.getFitStatus()
      if not S.isFitConverged() and (scifi or (aTrack.GetUniqueID()==1 or aTrack.GetUniqueID()==11) ):# scifi trk object ids are 1 or 11(Hough tracking)
         print('not converge')
         continue
      for p in [0,1]:
          h['aLine'+str(nTrack*10+p)] = ROOT.TGraph()

      # draw the track line starting from the most upstream Veto plane
      zEx = h['veto0_z']
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
             h['aLine'+str(nTrack*10+p)].SetLineColor(trackColor)
             h['aLine'+str(nTrack*10+p)].SetLineWidth(2)
             h['aLine'+str(nTrack*10+p)].Draw('same')
             tc.Update()
             h[ 'simpleDisplay'].Update()
      nTrack+=1

def twoTrackEvent(sMin=10,dClMin=7,minDistance=1.5,sepDistance=0.5, darkMode=False):
        trackTask.clusScifi.Clear()
        trackTask.scifiCluster()
        clusters = trackTask.clusScifi
        sortedClusters={}
        for aCl in clusters:
           so = aCl.GetFirst()//100000
           if not so in sortedClusters: sortedClusters[so]=[]
           sortedClusters[so].append(aCl)
        if len(sortedClusters)<sMin: return False
        M=0
        for x in sortedClusters:
           if len(sortedClusters[x]) == 2:  M+=1
        if M < dClMin: return False
        seeds = {}
        S = [-1,-1]
        for o in range(0,2):
# same procedure for both projections
# take seeds from from first station with 2 clusters
             for s in range(1,6):
                 x = 10*s+o
                 if x in sortedClusters:
                    if len(sortedClusters[x])==2:
                       sortedClusters[x][0].GetPosition(A,B)
                       if o%2==1: pos0 = (A[0]+B[0])/2
                       else: pos0 = (A[1]+B[1])/2
                       sortedClusters[x][1].GetPosition(A,B)
                       if o%2==1: pos1 = (A[0]+B[0])/2
                       else: pos1 = (A[1]+B[1])/2
                       if abs(pos0-pos1) > minDistance:
                         S[o] = s
                         break
             if S[o]<0: break  # no seed found
             seeds[o]={}
             k = -1
             for c in sortedClusters[S[o]*10+o]:
                 k += 1
                 c.GetPosition(A,B)
                 if o%2==1: pos = (A[0]+B[0])/2
                 else: pos = (A[1]+B[1])/2
                 seeds[o][k] = [[c,pos]]
             if k!=1: continue
             if abs(seeds[o][0][0][1] - seeds[o][1][0][1]) < sepDistance: continue
             for s in range(1,6):
               if s==S[o]: continue
               for c in sortedClusters[s*10+o]:
                   c.GetPosition(A,B)
                   if o%2==1: pos = (A[0]+B[0])/2
                   else: pos = (A[1]+B[1])/2
                   for k in range(2):
                        if  abs(seeds[o][k][0][1] - pos) < sepDistance:
                           seeds[o][k].append([c,pos])
        if S[0]<0 or S[1]<0:
            passed = False
        else:
           passed = True
           for o in range(0,2):
              for k in range(2):
                  if len(seeds[o][k])<3:
                      passed = False
                      break
        print(passed)
        if passed:
           tracks = []
           for k in range(2):
             # arbitrarly combine X and Y of combination 0
               n = 0
               hitlist = {}
               for o in range(0,2):
                   for X in seeds[o][k]:
                      hitlist[n] = X[0]
                      n+=1
               theTrack = trackTask.fitTrack(hitlist)
               if not hasattr(theTrack,"getFittedState"):
                    validTrack = False
                    continue
               fitStatus = theTrack.getFitStatus()
               if not fitStatus.isFitConverged():
                    theTrack.Delete()
               else: 
                    tracks.append(theTrack)
           if len(tracks)==2:
                 OT = sink.GetOutTree()
                 OT.Reco_MuonTracks = tracks
                 addTrack(OT,True, darkMode=darkMode) 
        return passed

def drawDetectors(darkMode=False):
   nodes = {'volMuFilter_1/volFeBlockEnd_1':ROOT.kGreen-6 if not darkMode else ROOT.kGreen-2}
   for i in range(mi.NVetoPlanes):
      nodes['volVeto_1/volVetoPlane_{}_{}'.format(i, i)]=ROOT.kRed
      for j in range(mi.NVetoBars):
         if i<2: nodes['volVeto_1/volVetoPlane_{}_{}/volVetoBar_1{}{:0>3d}'.format(i, i, i, j)]=ROOT.kRed
         if i==2: nodes['volVeto_1/volVetoPlane_{}_{}/volVetoBar_ver_1{}{:0>3d}'.format(i, i, i, j)]=ROOT.kRed
      if i<2: nodes['volVeto_1/subVetoBox_{}'.format(i)]=ROOT.kGray+1 if not darkMode else ROOT.kGray+2
      if i==2: nodes['volVeto_1/subVeto3Box_{}'.format(i)]=ROOT.kGray+1 if not darkMode else ROOT.kGray+2
   for i in range(si.nscifi): # number of scifi stations
      nodes['volTarget_1/ScifiVolume{}_{}000000'.format(i+1, i+1)]=ROOT.kBlue+1 if not darkMode else ROOT.kCyan-6
      # iron blocks btw SciFi planes in the testbeam 2023-2024 det layout
      nodes['volTarget_1/volFeTarget{}_1'.format(i+1)]=ROOT.kGreen-6 if not darkMode else ROOT.kGreen-2
   for i in range(em.wall): # number of target walls
      nodes['volTarget_1/volWallborder_{}'.format(i)]=ROOT.kGray if not darkMode else ROOT.kGray+2
   for i in range(mi.NDownstreamPlanes):
      nodes['volMuFilter_1/volMuDownstreamDet_{}_{}'.format(i, i+mi.NVetoPlanes+mi.NUpstreamPlanes)]=ROOT.kBlue+1 if not darkMode else ROOT.kCyan-6
      for j in range(mi.NDownstreamBars):
         nodes['volMuFilter_1/volMuDownstreamDet_{}_{}/volMuDownstreamBar_ver_3{}{:0>3d}'.format(i, i+mi.NVetoPlanes+mi.NUpstreamPlanes, i, j+mi.NDownstreamBars)]=ROOT.kBlue+1 if not darkMode else ROOT.kCyan-6
         if i < 3:
            nodes['volMuFilter_1/volMuDownstreamDet_{}_{}/volMuDownstreamBar_hor_3{}{:0>3d}'.format(i, i+mi.NVetoPlanes+mi.NUpstreamPlanes, i, j)]=ROOT.kBlue+1 if not darkMode else ROOT.kCyan-6
   for i in range(mi.NDownstreamPlanes):
      nodes['volMuFilter_1/subDSBox_{}'.format(i+mi.NVetoPlanes+mi.NUpstreamPlanes)]=ROOT.kGray+1 if not darkMode else ROOT.kGray+2
   for i in range(mi.NUpstreamPlanes):
      nodes['volMuFilter_1/subUSBox_{}'.format(i+mi.NVetoPlanes)]=ROOT.kGray+1 if not darkMode else ROOT.kGray+2
      nodes['volMuFilter_1/volMuUpstreamDet_{}_{}'.format(i, i+mi.NVetoPlanes)]=ROOT.kBlue+1 if not darkMode else ROOT.kCyan-6
      for j in range(mi.NUpstreamBars):
         nodes['volMuFilter_1/volMuUpstreamDet_{}_{}/volMuUpstreamBar_2{}00{}'.format(i, i+mi.NVetoPlanes, i, j)]=ROOT.kBlue+1 if not darkMode else ROOT.kCyan-6
      nodes['volMuFilter_1/volFeBlock_{}'.format(i)]=ROOT.kGreen-6 if not darkMode else ROOT.kGreen-2
   for i in range(mi.NVetoPlanes+mi.NUpstreamPlanes,mi.NVetoPlanes+mi.NUpstreamPlanes+mi.NDownstreamPlanes):
      nodes['volMuFilter_1/volFeBlock_{}'.format(i)]=ROOT.kGreen-6 if not darkMode else ROOT.kGreen-2
   passNodes = {'Block', 'Wall', 'FeTarget'}
   xNodes = {'UpstreamBar', 'VetoBar', 'hor'}
   proj = {'X':0,'Y':1}
   for node_ in nodes:
      node = '/cave_1/Detector_0/'+node_
      for p in proj:
         if node+p in h and any(passNode in node for passNode in passNodes):
            X = h[node+p]
            c = proj[p]
            h['simpleDisplay'].cd(c+1)
            X.Draw('f&&same')
            X.Draw('same')
         else:
            # check if node exists
            if not nav.CheckPath(node): continue
            nav.cd(node)
            N = nav.GetCurrentNode()
            S = N.GetVolume().GetShape()
            dx,dy,dz = S.GetDX(),S.GetDY(),S.GetDZ()
            ox,oy,oz = S.GetOrigin()[0],S.GetOrigin()[1],S.GetOrigin()[2]
            P = {}
            M = {}
            if p=='X' and (not any(xNode in node for xNode in xNodes) or 'VetoBar_ver' in node):
               P['LeftBottom'] = array('d',[-dx+ox,oy,-dz+oz])
               P['LeftTop'] = array('d',[dx+ox,oy,-dz+oz])
               P['RightBottom'] = array('d',[-dx+ox,oy,dz+oz])
               P['RightTop'] = array('d',[dx+ox,oy,dz+oz])
            elif p=='Y' and 'ver' not in node:
               P['LeftBottom'] = array('d',[ox,-dy+oy,-dz+oz])
               P['LeftTop'] = array('d',[ox,dy+oy,-dz+oz])
               P['RightBottom'] = array('d',[ox,-dy+oy,dz+oz])
               P['RightTop'] = array('d',[ox,dy+oy,dz+oz])
            else: continue
            for C in P:
               M[C] = array('d',[0,0,0])
               nav.LocalToMaster(P[C],M[C])
            if "volVetoPlane_0" in node:
               h['veto0_z'] = M['LeftBottom'][2]
            if "ScifiVolume" in node:
               for st in range(1,si.nscifi+1):
                  if f"{st}_{st}000000" in node:
                     h[f"scifi{st}_z"] = M['LeftBottom'][2]
            if "volMuUpstreamDet" in node:
               for st in range(mi.NUpstreamPlanes):
                  if f"{st}_{st+mi.NVetoPlanes}" in node:
                     h[f"us{st+1}_z"] = M['LeftBottom'][2]

            h[node+p] = ROOT.TPolyLine()
            X = h[node+p]
            c = proj[p]
            X.SetPoint(0,M['LeftBottom'][2],M['LeftBottom'][c])
            X.SetPoint(1,M['LeftTop'][2],M['LeftTop'][c])
            X.SetPoint(2,M['RightTop'][2],M['RightTop'][c])
            X.SetPoint(3,M['RightBottom'][2],M['RightBottom'][c])
            X.SetPoint(4,M['LeftBottom'][2],M['LeftBottom'][c])
            X.SetLineColor(nodes[node_])
            X.SetLineWidth(1)
            h['simpleDisplay'].cd(c+1)
            if any(passNode in node for passNode in passNodes):
               X.SetFillColorAlpha(nodes[node_], 0.5)
               X.Draw('f&&same')
            X.Draw('same')
def zoom(xmin=None,xmax=None,ymin=None,ymax=None,zmin=None,zmax=None):
# zoom() will reset to default setting
  for d in ['xmin','xmax','ymin','ymax','zmin','zmax']:
     if eval(d): h['c'+d]=eval(d)
     else: h['c'+d]=h[d]
  h['xz'].GetXaxis().SetRangeUser(h['czmin'],h['czmax'])
  h['yz'].GetXaxis().SetRangeUser(h['czmin'],h['czmax'])
  h['xz'].GetYaxis().SetRangeUser(h['cxmin'],h['cxmax'])
  h['yz'].GetYaxis().SetRangeUser(h['cymin'],h['cymax'])
  tc = h['simpleDisplay'].cd(1)
  tc.Update()
  tc = h['simpleDisplay'].cd(2)
  tc.Update()
  h['simpleDisplay'].Update()

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
          S =aHit.GetAllSignals(False,False)
          txt = ""
          for x in S:
              if x[1]>0: txt+=str(x[1])+" "
          print(plane, (aHit.GetDetectorID()%1000)%60, txt)

# decode MuFilter detID
def MuFilter_PlaneBars(detID):
         s = detID//10000
         l  = (detID%10000)//1000  # plane number
         bar = (detID%1000)
         if s>2:
             l=2*l
             if bar>59:
                  bar=bar-60
                  if l<6: l+=1
         return {'station':s,'plane':l,'bar':bar}

def checkOtherTriggers(event,deadTime = 100,debug=False):
      T0 = event.EventHeader.GetEventTime()
      N = event.EventHeader.GetEventNumber()
      Nprev = 1
      rc = event.GetEvent(N-Nprev)
      dt = T0 - event.EventHeader.GetEventTime()
      otherFastTrigger = False
      otherAdvTrigger = False
      tightNoiseFilter = False
      while dt < deadTime:
         otherFastTrigger = False
         for x in event.EventHeader.GetFastNoiseFilters():
             if debug: print('fast:', x.first, x.second )
             if x.second and not x.first == 'Veto_Total': otherFastTrigger = True
         otherAdvTrigger = False
         for x in event.EventHeader.GetAdvNoiseFilters():
             if debug: print('adv:', x.first, x.second )
             if x.second and not x.first == 'VETO_Planes': otherAdvTrigger = True
         if debug: print('pre event ',Nprev,dt,otherFastTrigger,otherAdvTrigger)
         if otherFastTrigger and otherAdvTrigger:
             rc = event.GetEvent(N)
             return otherFastTrigger, otherAdvTrigger, tightNoiseFilter, Nprev, dt
         Nprev+=1
         rc = event.GetEvent(N-Nprev)
         dt = T0 - event.EventHeader.GetEventTime()
      Nprev = 1
      rc = event.GetEvent(N-Nprev)
      dt = T0 - event.EventHeader.GetEventTime()
      while dt < deadTime:
         hits = {1:0,0:0}
         for aHit in event.Digi_MuFilterHits:
            Minfo = MuFilter_PlaneBars(aHit.GetDetectorID())
            s,l,bar = Minfo['station'],Minfo['plane'],Minfo['bar']
            if s>1: continue
            allChannels = aHit.GetAllSignals(False,False)
            hits[l]+=len(allChannels)
         noiseFilter0 = (hits[0]+hits[1])>4.5
         noiseFilter1 = hits[0]>0 and hits[1]>0
         if debug: print('veto hits:',hits)
         if noiseFilter0 and noiseFilter1: 
            tightNoiseFilter = True
            rc = event.GetEvent(N)
            return otherFastTrigger, otherAdvTrigger, tightNoiseFilter, Nprev-1, dt
         Nprev+=1
         rc = event.GetEvent(N-Nprev)
         dt = T0 - event.EventHeader.GetEventTime()
      if Nprev>1: 
            rc = event.GetEvent(N-Nprev+1)
            dt = T0 - event.EventHeader.GetEventTime()
      rc = event.GetEvent(N)
      return otherFastTrigger, otherAdvTrigger, tightNoiseFilter, Nprev-1, dt
      
def cleanTracks():
    OT = sink.GetOutTree()
    listOfDetIDs = {}
    n = 0
    for aTrack in OT.Reco_MuonTracks:
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

def timingOfEvent(makeCluster=False,debug=False):
   ut.bookHist(h,'evTimeDS','cor time of hits;[ns]',70,-5.,30)
   ut.bookHist(h,'evTimeScifi','cor time of hits blue DS red Scifi;[ns]',70,-5.,30)
   ut.bookCanvas(h,'tevTime','cor time of hits',1024,768,1,1)
   h['evTimeScifi'].SetLineColor(ROOT.kRed)
   h['evTimeDS'].SetLineColor(ROOT.kBlue)
   h['evTimeScifi'].SetStats(0)
   h['evTimeDS'].SetStats(0)
   h['evTimeScifi'].SetLineWidth(2)
   h['evTimeDS'].SetLineWidth(2)
   if makeCluster: trackTask.scifiCluster()
   meanXY = {}
   for siCl in trackTask.clusScifi:
       detID = siCl.GetFirst()
       s = detID//1000000
       isVertical = detID%1000000//100000
       siCl.GetPosition(A,B)
       z=(A[2]+B[2])/2.
       pos = (A[1]+B[1])/2.
       L = abs(A[0]-B[0])/2.
       if isVertical:
          pos = (A[0]+B[0])/2.
          L = abs(A[1]-B[1])/2.
       corTime = geo.modules['Scifi'].GetCorrectedTime(detID, siCl.GetTime(), 0) - (z-firstScifi_z)/u.speedOfLight
       h['evTimeScifi'].Fill(corTime)
       if debug: print(detID,corTime,pos)
   for aHit in eventTree.Digi_MuFilterHits:
       detID = aHit.GetDetectorID()
       if not detID//10000==3: continue
       if aHit.isVertical(): nmax = 1
       else: nmax=2
       geo.modules['MuFilter'].GetPosition(detID,A,B)
       z=(A[2]+B[2])/2.
       pos = (A[1]+B[1])/2.
       L = abs(A[0]-B[0])/2.
       if isVertical: 
          pos = (A[0]+B[0])/2.
          L = abs(A[1]-B[1])/2.
       for i in range(nmax):
            corTime = geo.modules['MuFilter'].GetCorrectedTime(detID, i, aHit.GetTime(i)*u.snd_TDC2ns, 0)- (z-firstScifi_z)/u.speedOfLight
            h['evTimeDS'].Fill(corTime)
            if debug: print(detID,i,corTime,pos)
   tc=h['tevTime'].cd()
   h['evTimeScifi'].Draw()
   h['evTimeDS'].Draw('same')
   tc.Update()
def mufiNoise():
  for s in range(1,4): 
    ut.bookHist(h,'mult'+str(s),'hit mult for system '+str(s),100,-0.5,99.5)
    ut.bookHist(h,'multb'+str(s),'hit mult per bar for system '+str(s),20,-0.5,19.5)
    ut.bookHist(h,'res'+str(s),'residual system '+str(s),20,-10.,10.)
  OT = sink.GetOutTree()
  N=0
  for event in eventTree:
       N+=1
       if N%1000==0: print(N)
       OT.Reco_MuonTracks.Delete()
       rc = trackTask.ExecuteTask("Scifi")
       for aTrack in OT.Reco_MuonTracks:
           mom    = aTrack.getFittedState().getMom()
           pos      = aTrack.getFittedState().getPos()
           if not aTrack.getFitStatus().isFitConverged(): continue
           mult = {1:0,2:0,3:0}
           for aHit in eventTree.Digi_MuFilterHits:
              if not aHit.isValid(): continue
              s = aHit.GetDetectorID()//10000
              S = aHit.GetAllSignals(False,False)
              rc = h['multb'+str(s)].Fill(len(S))
              mult[s]+=len(S)
              if s==2 or s==1:
                 geo.modules['MuFilter'].GetPosition(aHit.GetDetectorID(),A,B)
                 y = (A[1]+B[1])/2.
                 zEx = (A[2]+B[2])/2.
                 lam      = (zEx-pos.z())/mom.z()
                 Ey        = pos.y()+lam*mom.y()
                 rc = h['res'+str(s)].Fill(Ey-y)
           for s in mult: rc = h['mult'+str(s)].Fill(mult[s])
  ut.bookCanvas(h,'noise','',1200,1200,2,3)
  for s in range(1,4):
   tc = h['noise'].cd(s*2-1)
   tc.SetLogy(1)
   h['mult'+str(s)].Draw()
   h['noise'].cd(s*2)
   h['multb'+str(s)].Draw()
  ut.bookCanvas(h,'res','',600,1200,1,3)
  for s in range(1,4):
   tc = h['res'].cd(s)
   h['res'+str(s)].Draw()

def firstTimeStamp(event):
        tmin = [1E9,'']
        digis = [event.Digi_MuFilterHits,event.Digi_ScifiHits]
        for digi in event.Digi_ScifiHits:
               dt = digi.GetTime()
               if dt<tmin[0]:
                    tmin[0]=dt
                    tmin[1]=digi
        for digi in event.Digi_MuFilterHits:
           for t in digi.GetAllTimes():    # will not give time if QDC<0!
               dt = t.second
               if dt<tmin[0]:
                    tmin[0]=dt
                    tmin[1]=digi
        return tmin

def dumpChannels(D='Digi_MuFilterHits'):
     X = eval("eventTree."+D)
     text = {}
     for aHit in X:
         side = 'L'
         txt = "%8i"%(aHit.GetDetectorID())
         for k in range(aHit.GetnSiPMs()*aHit.GetnSides()):
              qdc = aHit.GetSignal(k)
              if qdc < -900: continue
              i = k
              if not k<aHit.GetnSiPMs():
                   i = k-aHit.GetnSiPMs()
                   if side == 'L':
                        txt += " | "
                        side = 'R'
              txt+= "  %2i:%4.1F  "%(i,qdc)
         text[aHit.GetDetectorID()] = txt
     keys = list(text.keys())
     keys.sort()
     for k in keys: print(text[k])

def fillNode(node, color=None, darkMode=False):
   xNodes = {'UpstreamBar', 'VetoBar', 'hor'}
   proj = {'X':0,'Y':1}
   if color == None :
          hcal_color = ROOT.kBlack if not darkMode else ROOT.kWhite
          veto_color = ROOT.kRed+1 if not darkMode else ROOT.kRed-4
   else :
          hcal_color = color
          veto_color = color
   thick = 5
   for p in proj:
      if node+p in h:
         X = h[node+p]
         if 'Veto' in node:
              color = veto_color
         else :
              color = hcal_color
       
         if 'Downstream' in node:
            thick = 5
         c = proj[p]
         h[ 'simpleDisplay'].cd(c+1)
         X.SetFillColor(color)
         X.SetLineColor(color)
         X.SetLineWidth(thick)
         X.Draw('f&&same')
         X.Draw('same')   

def drawInfo(pad, k, run, event, timestamp,moreEventInfo=[], darkMode=False):
   drawLogo = True
   drawText = True
   if drawLogo:
      padLogo = ROOT.TPad("logo","logo",0.1,0.1,0.2,0.3)
      padLogo.SetFillStyle(4000)
      padLogo.SetFillColorAlpha(0, 0)
      if darkMode: padLogo.SetFillColor(ROOT.kBlack)
      padLogo.Draw()
      logo = ROOT.TImage.Open('$SNDSW_ROOT/shipLHC/Large__SND_Logo_black_cut.png') if not darkMode else ROOT.TImage.Open('$SNDSW_ROOT/shipLHC/Large__SND_Logo_white_cut.png')
      logo.SetConstRatio(True)
      padLogo.cd()
      logo.Draw()
      pad.cd(k)

   if drawText:
    if k==1 or len(moreEventInfo)<5:
      runNumber = eventTree.EventHeader.GetRunId()
      timestamp_print = False
      if not mc and hasattr(eventTree.EventHeader, "GetUTCtimestamp"):
        timestamp_print = True
        time_event= datetime.utcfromtimestamp(eventTree.EventHeader.GetUTCtimestamp())
      padText = ROOT.TPad("info","info",0.19,0.1,0.6,0.3)
      padText.SetFillStyle(4000)
      padText.Draw()
      padText.cd()
      textInfo = ROOT.TLatex()
      textInfo.SetTextAlign(11)
      textInfo.SetTextFont(42)
      textInfo.SetTextSize(.15)
      if darkMode: textInfo.SetTextColor(ROOT.kWhite)
      textInfo.DrawLatex(0, 0.6, 'SND@LHC Experiment, CERN')
      if hasattr(eventTree.EventHeader,'GetEventNumber'): N = eventTree.EventHeader.GetEventNumber()
      else: N = event
      textInfo.DrawLatex(0, 0.4, 'Run / Event: '+str(run)+' / '+str(N))
      if timestamp_print:
           textInfo.DrawLatex(0, 0.2, 'Time (GMT): {}'.format(time_event))
      pad.cd(k)
    elif options.extraInfo:
      padText = ROOT.TPad("info","info",0.29,0.12,0.9,0.35)
      padText.SetFillStyle(4000)
      padText.Draw()
      padText.cd()
      textInfo = ROOT.TLatex()
      textInfo.SetTextAlign(11)
      textInfo.SetTextFont(42)
      textInfo.SetTextSize(.1)
      textInfo.SetTextColor((ROOT.kMagenta+2) if not darkMode else (ROOT.kMagenta-4))
      dely = 0.12
      ystart = 0.85
      for i in range(7):
        textInfo.DrawLatex(0.4, 0.9-dely*i, moreEventInfo[i])
      pad.cd(k)

def drawCollisionAxis(pad, k):
   line_name = "collision_axis_line_" + str(k)
   h[line_name] = ROOT.TLine(h["zmin"], 0, h["zmax"], 0)
   h[line_name].SetLineColor(ROOT.kRed)
   h[line_name].SetLineStyle(2)

   text_name = "collision_axis_text_" + str(k)
   h[text_name] = ROOT.TText(h["zmin"] + 8, 0 + 2, "Collision axis")
   h[text_name].SetTextAlign(12)
   h[text_name].SetTextFont(43)
   h[text_name].SetTextSize(13 * resolution_factor)
   h[text_name].SetTextColor(ROOT.kRed)   
   
   pad.cd(k)
   h[line_name].Draw()
   h[text_name].Draw()

def drawShowerAxis(pad, k, shower_start, ref_point, shower_direction):
   line_name= "shower_dir_" + str(k)
   if shower_start<100:
      zpos_name='scifi'+str(shower_start//10)
   else:
      zpos_name='us'+str(shower_start//100)
   h[line_name] = ROOT.TLine(h[zpos_name+'_z'],
                             ref_point+shower_direction*h[zpos_name+'_z'],
                             h['zmax'],
                             ref_point+shower_direction*h['zmax'])
   h[line_name].SetLineColor(ROOT.kPink-6)
   h[line_name].SetLineStyle(3)
   h[line_name].SetLineWidth(5)
   pad.cd(k)
   h[line_name].Draw()
