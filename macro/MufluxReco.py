#!/usr/bin/env python
#inputFile = '/eos/experiment/ship/data/muflux/run_fixedtarget/19april2018/pythia.root'
#geoFile   = '/eos/experiment/ship/data/muflux/run_fixedtarget/19april2018/geofile_full.root'
from __future__ import print_function
from __future__ import division
import global_variables
debug = False#False

withNoStrawSmearing = None # True   for debugging purposes
withDist2Wire = False
withNTaggerHits = 0
nEvents    = 10000
firstEvent = 0
withHists = True
dy  = None
saveDisk  = False # remove input file
realPR = ''
withT0 = False

import resource
def mem_monitor():
 # Getting virtual memory size 
    pid = os.getpid()
    with open(os.path.join("/proc", str(pid), "status")) as f:
        lines = f.readlines()
    _vmsize = [l for l in lines if l.startswith("VmSize")][0]
    vmsize = int(_vmsize.split()[1])
    #Getting physical memory size  
    pmsize = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print("memory: virtuell = %5.2F MB  physical = %5.2F MB"%(vmsize/1.0E3,pmsize/1.0E3))

import ROOT,os,sys,getopt
import rootUtils as ut
import shipunit as u
import shipRoot_conf

# geoMat =  ROOT.genfit.TGeoMaterialInterface()
shipRoot_conf.configure()

try:
        opts, args = getopt.getopt(sys.argv[1:], "o:D:FHPu:n:f:g:c:hqv:sl:A:Y:i:t:",\
           ["ecalDebugDraw","inputFile=","geoFile=","nEvents=","noStrawSmearing","noVertexing","saveDisk","realPR","withT0", "withNTaggerHits=", "withDist2Wire"])
except getopt.GetoptError:
        # print help information and exit:
        print(' enter --inputFile=  --geoFile= --nEvents=  --firstEvent=,')
        print(' noStrawSmearing: no smearing of distance to wire, default on')
        print(' outputfile will have same name with _rec added')
        sys.exit()
for o, a in opts:
        if o in ("--noVertexing",):
            print("WARNING: --noVertexing option not currently used by script.")
        if o in ("--noStrawSmearing",):
            withNoStrawSmearing = True
        if o in ("--withT0",):
            withT0 = True
        if o in ("--withDist2Wire",):
            withDist2Wire = True
        if o in ("-t", "--withNTaggerHits"):
            withNTaggerHits = int(a)
        if o in ("-f", "--inputFile"):
            inputFile = a
        if o in ("-g", "--geoFile"):
            geoFile = a
        if o in ("-n", "--nEvents="):
            nEvents = int(a)
        if o in ("-Y",):
            dy = float(a)
        if o in ("--ecalDebugDraw",):
            print("WARNING: --ecalDebugDraw option not currently used by script.")
        if o in ("--saveDisk",):
            saveDisk = True
        if o in ("--realPR",):
            realPR = "_PR"


# need to figure out which geometry was used
if not dy:
  # try to extract from input file name
  tmp = inputFile.split('.')
  try:
    dy = float( tmp[1]+'.'+tmp[2] )
  except:
    dy = None
print('configured to process ', nEvents, ' events from ', inputFile,
      ' starting with event ', firstEvent, ' with option Yheight = ', dy,
      ' with vertexing', False,' and real pattern reco',realPR=="_PR")
if not inputFile.find('_rec.root') < 0: 
  outFile   = inputFile
  inputFile = outFile.replace('_rec.root','.root') 
else:
  outFile = inputFile.replace('.root','_rec.root') 
# outfile should be in local directory
  tmp = outFile.split('/')
  outFile = tmp[len(tmp)-1]
  if saveDisk: os.system('mv '+inputFile+' '+outFile)
  else :       os.system('cp '+inputFile+' '+outFile)

# check if simulation or raw data
f=ROOT.TFile.Open(outFile)
if f.cbmsim.FindBranch('MCTrack'): simulation = True
else: simulation = False
f.Close()

if simulation and geoFile:
 fgeo = ROOT.TFile.Open(geoFile)
 from ShipGeoConfig import ConfigRegistry
 from rootpyPickler import Unpickler
#load Shipgeo dictionary
 upkl    = Unpickler(fgeo)
 ShipGeo = upkl.load('ShipGeo')
else:
 ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/charm-geometry_config.py", Yheight = dy)

h={}
log={}
if withHists:
 ut.bookHist(h,'distu','distance to wire',100,0.,5.)
 ut.bookHist(h,'distv','distance to wire',100,0.,5.)
 ut.bookHist(h,'disty','distance to wire',100,0.,5.)
 ut.bookHist(h,'nmeas','nr measurements',100,0.,50.)
 ut.bookHist(h,'chi2','Chi2/DOF',100,0.,20.)
 ut.bookHist(h,'p-fittedtracks','p of fitted tracks',40,0.,400.)
 ut.bookHist(h,'1/p-fittedtracks','1/p of fitted tracks',120,-0.2,1.)
 ut.bookHist(h,'pt-fittedtracks','pt of fitted tracks',100,0.,10.)
 ut.bookHist(h,'1/pt-fittedtracks','1/pt of fitted tracks',120,-0.2,1.)
 ut.bookHist(h,'ptruth','ptruth',40,0.,400.)
 ut.bookHist(h,'delPOverP','Pfitted/Ptrue-1 vs Ptrue',40,0.,400.,50,-2.0,2.0)
 ut.bookHist(h,'invdelPOverP','1/Pfitted-1/Ptrue)/(1/Ptrue) vs Ptrue',40,0.,400.,50,-2.0,2.0)
 ut.bookProf(h,'deltaPOverP','Pfitted/Ptrue-1 vs Ptrue',40,0.,400.,-10.,10.0)
 ut.bookHist(h,'Pfitted-Pgun','P-fitted vs P-gun',40,0.,400.,50,0.,500.0)
 ut.bookHist(h,'Px/Pzfitted','Px/Pz-fitted',100,-0.04,0.04)
 ut.bookHist(h,'Py/Pzfitted','Py/Pz-fitted',100,-0.04,0.04) 
 ut.bookHist(h,'Px/Pztrue','Px/Pz-true',100,-0.04,0.04)
 ut.bookHist(h,'Py/Pztrue','Py/Pz-true',100,-0.04,0.04) 
 ut.bookHist(h,'Px/Pzfitted-noT4','Px/Pz-fitted only T1,T2,T3 ',100,-0.04,0.04)
 ut.bookHist(h,'Py/Pzfitted-noT4','Py/Pz-fitted only T1,T2,T3',100,-0.04,0.04)
 ut.bookHist(h,'Px/Pztrue-noT4','Px/Pz-true only T1,T2,T3',100,-0.04,0.04)
 ut.bookHist(h,'Py/Pztrue-noT4','Py/Pz-true only T1,T2,T3',100,-0.04,0.04)
 ut.bookHist(h,'Px/Pzfitted-all','Px/Pz-fitted',100,-0.04,0.04)
 ut.bookHist(h,'Py/Pzfitted-all','Py/Pz-fitted',100,-0.04,0.04)
 ut.bookHist(h,'Px/Pztrue-all','Px/Pz-true',100,-0.04,0.04)
 ut.bookHist(h,'Py/Pztrue-all','Py/Pz-true',100,-0.04,0.04)
 ut.bookHist(h,'Px/Pzfitted-Px/Pztruth','Px/Pz-fitted - Px/Pz-true vs P-true',40,0.,400.,100,-0.002,0.002)
 ut.bookHist(h,'Py/Pzfitted-Py/Pztruth','Py/Pz-fitted - Py/Pz-true vs P-true',40,0.,400.,50,-0.02,0.02)
 ut.bookHist(h,'Px/Pzfitted-Px/Pztruth-noT4','Px/Pz-fitted - Px/Pz-true vs P-true (no stereo layers)',40,0.,400.,100,-0.002,0.002)
 ut.bookHist(h,'Py/Pzfitted-Py/Pztruth-noT4','Py/Pz-fitted - Py/Pz-true vs P-true (no stereo layers)',40,0.,400.,50,-0.02,0.02)
 ut.bookHist(h,'Px/Pzfitted-Px/Pztruth-all','Px/Pz-fitted - Px/Pz-true vs P-true (no stereo layers)',40,0.,400.,100,-0.002,0.002)
 ut.bookHist(h,'Py/Pzfitted-Py/Pztruth-all','Py/Pz-fitted - Py/Pz-true vs P-true (no stereo layers)',40,0.,400.,50,-0.02,0.02)

 ut.bookHist(h,'p-value','p-value of fit',100,0.,1.)
 ut.bookHist(h,'pt-kick','pt-kick',100,-2.,2.)
 ut.bookHist(h,'nmeas-noT4','nr measurements only T1,T2,T3',100,0.,50.)
 ut.bookHist(h,'chi2-noT4','Chi2/DOF only T1,T2,T3',100,0.,20.)
 ut.bookHist(h,'nmeas-all','nr measurements',100,0.,50.)
 ut.bookHist(h,'chi2-all','Chi2/DOF',100,0.,20.)
 ut.bookHist(h,'p-fittedtracks-noT4','p of fitted track only T1,T2,T3',40,0.,400.)
 ut.bookHist(h,'1/p-fittedtracks-noT4','1/p of fitted tracks only T1,T2,T3',120,-0.2,1.)
 ut.bookHist(h,'pt-fittedtracks-noT4','pt of fitted tracks only T1,T2,T3',100,0.,10.)
 ut.bookHist(h,'1/pt-fittedtracks-noT4','1/pt of fitted tracks only T1,T2,T3',120,-0.2,1.)
 ut.bookHist(h,'ptruth-noT4','ptruth only T1,T2,T3',40,0.,400.)
 ut.bookHist(h,'delPOverP-noT4','Pfitted/Ptrue-1 vs Ptrue only T1,T2,T3',40,0.,400.,50,-2.0,2.0)
 ut.bookHist(h,'invdelPOverP-noT4','1/Pfitted-1/Ptrue)/(1/Ptrue) vs Ptrue only T1,T2,T3',40,0.,400.,50,-2.0,2.0)
 ut.bookProf(h,'deltaPOverP-noT4','Pfitted/Ptrue-1 vs Ptrue only T1,T2,T3',40,0.,400.,-10.,10.0)
 ut.bookHist(h,'Pfitted-Pgun-noT4','P-fitted vs P-gun only T1,T2,T3',40,0.,400.,50,0.,500.0)
 ut.bookHist(h,'p-value-noT4','p-value of fit only T1,T2,T3',100,0.,1.)
 ut.bookHist(h,'p-fittedtracks-all','p of fitted track',40,0.,400.)
 ut.bookHist(h,'1/p-fittedtracks-all','1/p of fitted tracks',120,-0.2,1.)
 ut.bookHist(h,'pt-fittedtracks-all','pt of fitted tracks',100,0.,10.)
 ut.bookHist(h,'1/pt-fittedtracks-all','1/pt of fitted tracks',120,-0.2,1.)
 ut.bookHist(h,'ptruth-all','ptruth',40,0.,400.)
 ut.bookHist(h,'delPOverP-all','Pfitted/Ptrue-1 vs Ptrue',40,0.,400.,50,-2.0,2.0)
 ut.bookHist(h,'invdelPOverP-all','1/Pfitted-1/Ptrue)/(1/Ptrue) vs Ptrue',40,0.,400.,50,-2.0,2.0)
 ut.bookProf(h,'deltaPOverP-all','Pfitted/Ptrue-1 vs Ptrue',40,0.,400.,-10.,10.0)
 ut.bookHist(h,'Pfitted-Pgun-all','P-fitted vs P-gun only',40,0.,400.,50,0.,500.0)
 ut.bookHist(h,'p-value-all','p-value of fit',100,0.,1.)
 ut.bookHist(h,'hits-T1','x vs y hits in T1',50,-25.,25.,100,-50.,50) 
 ut.bookHist(h,'hits-T2','x vs y hits in T2',50,-25.,25.,100,-50.,50) 
 ut.bookHist(h,'hits-T1x','x vs y hits in T1 x plane',50,-25.,25.,100,-50.,50) 
 ut.bookHist(h,'hits-T1u','x vs y hits in T1 u plane',50,-25.,25.,100,-50.,50)  
 ut.bookHist(h,'hits-T2x','x vs y hits in T2 x plane',50,-25.,25.,100,-50.,50) 
 ut.bookHist(h,'hits-T2v','x vs y hits in T2 v plane',50,-25.,25.,100,-50.,50) 
 ut.bookHist(h,'hits-T3','x vs y hits in T3',200,-100.,100.,160,-80.,80) 
 ut.bookHist(h,'hits-T4','x vs y hits in T4',200,-100.,100.,160,-80.,80) 

 ut.bookHist(h,'muontaggerhits', 'Muon Tagger Points', 300, -150, 150, 200, -100, 100)
 h['muontaggerhits'].SetMarkerSize(15)  

 ut.bookHist(h, 'muontagger_z', 'Z Hits', 600, 850, 2500)
 ut.bookHist(h, 'muontaggerdist', 'Muontagger Hits', 300, -150, 150, 200, -100, 100, 600, 850, 2000)

 
 ut.bookHist(h, 'muontagger_clusters', 'Clusters', 50, 0, 50)
   
 ut.bookHist(h,'NTrueTracks','Number of tracks.', 3, -0.5, 2.5)
 h['NTrueTracks'].GetXaxis().SetBinLabel(1,"Stations 1&2, Y views")
 h['NTrueTracks'].GetXaxis().SetBinLabel(2,"Stations 1&2, Stereo views")
 h['NTrueTracks'].GetXaxis().SetBinLabel(3,"Stations 3&4")
    
 ut.bookHist(h,'Reco_y12','Number of recognized tracks, clones and ghosts in stations 1&2, Y views', 5, -0.5, 4.5)
 h['Reco_y12'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_y12'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_y12'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_y12'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_y12'].GetXaxis().SetBinLabel(5,"N others")

 ut.bookHist(h,'Reco_stereo12','Number of recognized tracks, clones and ghosts in stations 1&2, Stereo views', 5, -0.5, 4.5)
 h['Reco_stereo12'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_stereo12'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_stereo12'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_stereo12'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_stereo12'].GetXaxis().SetBinLabel(5,"N others")
    
 ut.bookHist(h,'Reco_34','Number of recognized tracks, clones and ghosts in stations 3&4', 5, -0.5, 4.5)
 h['Reco_34'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_34'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_34'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_34'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_34'].GetXaxis().SetBinLabel(5,"N others")
    
 

 ut.bookHist(h,'NTrueTracks_3hits','Number of tracks with more than 3 hits.', 3, -0.5, 2.5)
 h['NTrueTracks_3hits'].GetXaxis().SetBinLabel(1,"Stations 1&2, Y views")
 h['NTrueTracks_3hits'].GetXaxis().SetBinLabel(2,"Stations 1&2, Stereo views")
 h['NTrueTracks_3hits'].GetXaxis().SetBinLabel(3,"Stations 3&4")
    
 ut.bookHist(h,'Reco_y12_3hits','Number of recognized tracks, clones and ghosts with more than 3 hits in stations 1&2, Y views', 5, -0.5, 4.5)
 h['Reco_y12_3hits'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_y12_3hits'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_y12_3hits'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_y12_3hits'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_y12_3hits'].GetXaxis().SetBinLabel(5,"N others")

 ut.bookHist(h,'Reco_stereo12_3hits','Number of recognized tracks, clones and ghosts with more than 3 hits in stations 1&2, Stereo views', 5, -0.5, 4.5)
 h['Reco_stereo12_3hits'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_stereo12_3hits'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_stereo12_3hits'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_stereo12_3hits'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_stereo12_3hits'].GetXaxis().SetBinLabel(5,"N others")
    
 ut.bookHist(h,'Reco_34_3hits','Number of recognized tracks, clones and ghosts with more than 3 hits in stations 3&4', 5, -0.5, 4.5)
 h['Reco_34_3hits'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_34_3hits'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_34_3hits'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_34_3hits'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_34_3hits'].GetXaxis().SetBinLabel(5,"N others")
    
    
    
 ut.bookHist(h,'NTrueTracks_Tr4','Number of tracks. At least one hit in stations 1-4.', 3, -0.5, 2.5)
 h['NTrueTracks_Tr4'].GetXaxis().SetBinLabel(1,"Stations 1&2, Y views")
 h['NTrueTracks_Tr4'].GetXaxis().SetBinLabel(2,"Stations 1&2, Stereo views")
 h['NTrueTracks_Tr4'].GetXaxis().SetBinLabel(3,"Stations 3&4")
    
 ut.bookHist(h,'Reco_y12_Tr4','Number of recognized tracks, clones and ghosts in stations 1&2, Y views. At least one hit in stations 1-4.', 5, -0.5, 4.5)
 h['Reco_y12_Tr4'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_y12_Tr4'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_y12_Tr4'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_y12_Tr4'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_y12_Tr4'].GetXaxis().SetBinLabel(5,"N others")

 ut.bookHist(h,'Reco_stereo12_Tr4','Number of recognized tracks, clones and ghosts in stations 1&2, Stereo views. At least one hit in stations 1-4.', 5, -0.5, 4.5)
 h['Reco_stereo12_Tr4'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_stereo12_Tr4'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_stereo12_Tr4'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_stereo12_Tr4'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_stereo12_Tr4'].GetXaxis().SetBinLabel(5,"N others")
    
 ut.bookHist(h,'Reco_34_Tr4','Number of recognized tracks, clones and ghosts in stations 3&4. At least one hit in stations 1-4.', 5, -0.5, 4.5)
 h['Reco_34_Tr4'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_34_Tr4'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_34_Tr4'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_34_Tr4'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_34_Tr4'].GetXaxis().SetBinLabel(5,"N others")

 ut.bookHist(h,'Reco_target','Number of recognized target tracks, clones and ghosts.', 5, -0.5, 4.5)
 h['Reco_target'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_target'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_target'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_target'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_target'].GetXaxis().SetBinLabel(5,"N others")

 ut.bookHist(h,'Reco_muon','Number of recognized muon tracks, clones and ghosts.', 5, -0.5, 4.5)
 h['Reco_muon'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_muon'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_muon'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_muon'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_muon'].GetXaxis().SetBinLabel(5,"N others")

 ut.bookHist(h,'Reco_muon_with_tagger','Number of recognized muon tracks, clones and ghosts with tagger hits.', 5, -0.5, 4.5)
 h['Reco_muon_with_tagger'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_muon_with_tagger'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_muon_with_tagger'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_muon_with_tagger'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_muon_with_tagger'].GetXaxis().SetBinLabel(5,"N others")

 ut.bookHist(h,'Reco_all_tracks','Number of recognized all tracks, clones and ghosts.', 5, -0.5, 4.5)
 h['Reco_all_tracks'].GetXaxis().SetBinLabel(1,"N total")
 h['Reco_all_tracks'].GetXaxis().SetBinLabel(2,"N recognized tracks")
 h['Reco_all_tracks'].GetXaxis().SetBinLabel(3,"N clones")
 h['Reco_all_tracks'].GetXaxis().SetBinLabel(4,"N ghosts")
 h['Reco_all_tracks'].GetXaxis().SetBinLabel(5,"N others")


 ut.bookHist(h,'NHits_true_y12','Number of hits per MC track. Stations 1&2, Y views', 9, -0.5, 8.5)
 ut.bookHist(h,'NHits_true_stereo12','Number of hits per MC track. Stations 1&2, Stereo views', 9, -0.5, 8.5)
 ut.bookHist(h,'NHits_true_34','Number of hits per MC track. Stations 3&4, Y views', 9, -0.5, 8.5)

 ut.bookHist(h,'NHits_reco_y12','Number of hits per Reco track. Stations 1&2, Y views', 9, -0.5, 8.5)
 ut.bookHist(h,'NHits_reco_stereo12','Number of hits per Reco track. Stations 1&2, Stereo views', 9, -0.5, 8.5)
 ut.bookHist(h,'NHits_reco_34','Number of hits per Reco track. Stations 3&4, Y views', 9, -0.5, 8.5)


 ut.bookHist(h,'p/pt','P vs Pt (GeV), Reco',100,0.,400.,100,0.,10.)
 ut.bookHist(h,'p/pt_truth','P vs Pt (GeV), MC Truth',100,0.,400.,100,0.,10.)
 ut.bookHist(h,'p/pt_noT4','P vs Pt (GeV), Reco',100,0.,400.,100,0.,10.)
 ut.bookHist(h,'p/pt_truth_noT4','P vs Pt (GeV), MC Truth',100,0.,400.,100,0.,10.)
 ut.bookHist(h,'p/pt_all','P vs Pt (GeV), Reco',100,0.,400.,100,0.,10.)
 ut.bookHist(h,'p/pt_truth_all','P vs Pt (GeV), MC Truth',100,0.,400.,100,0.,10.)

 ut.bookHist(h,'p_rel_error','(P_reco - P_true) / P_true',200,-2.,2.)
 ut.bookHist(h,'pt_rel_error','(Pt_reco - Pt_true) / Pt_true',200,-2.,2.)
 ut.bookHist(h,'p_rel_error_noT4','(P_reco - P_true) / P_true',200,-2.,2.)
 ut.bookHist(h,'pt_rel_error_noT4','(Pt_reco - Pt_true) / Pt_true',200,-2.,2.)
 ut.bookHist(h,'p_rel_error_all','(P_reco - P_true) / P_true',200,-2.,2.)
 ut.bookHist(h,'pt_rel_error_all','(Pt_reco - Pt_true) / Pt_true',200,-2.,2.)


 ut.bookHist(h,'Reco_muons_vs_p_true','Number of recognized muons vs P MC truth',40,0.,400.)
 ut.bookHist(h,'Ghosts_muons_vs_p_true','Number of ghosts vs P MC truth',40,0.,400.)
 ut.bookHist(h,'True_muons_vs_p_true','Number of muons vs P MC truth',40,0.,400.)
 ut.bookHist(h,'True_all_tracks_vs_p_true','Number of muons vs P MC truth',40,0.,400.)
 
# -----Create geometry----------------------------------------------
import charmDet_conf
run = ROOT.FairRunSim()
run.SetName("TGeant4")  # Transport engine
run.SetOutputFile(ROOT.TMemFile('output', 'recreate'))  # Output file
run.SetUserConfig("g4Config_basic.C") # geant4 transport not used, only needed for creating VMC field
rtdb = run.GetRuntimeDb()
modules = charmDet_conf.configure(run,ShipGeo)
# -----Create geometry----------------------------------------------
fgeo.FAIRGeom

# make global variables
global_variables.debug = debug
global_variables.withT0 = withT0
global_variables.realPR = realPR

global_variables.ShipGeo = ShipGeo
global_variables.modules = modules

global_variables.withNoStrawSmearing = withNoStrawSmearing
global_variables.withNTaggerHits = withNTaggerHits
global_variables.withDist2Wire = withDist2Wire
global_variables.h = h
global_variables.log = log
global_variables.simulation = simulation
global_variables.iEvent = 0

# import reco tasks
import MufluxDigiReco
SHiP = MufluxDigiReco.MufluxDigiReco(outFile)

nEvents   = min(SHiP.sTree.GetEntries(),nEvents)
# main loop
for global_variables.iEvent in range(firstEvent, nEvents):
    if global_variables.iEvent % 1000 == 0 or global_variables.debug:
        print('event ', global_variables.iEvent)
    SHiP.iEvent = global_variables.iEvent
    rc = SHiP.sTree.GetEvent(global_variables.iEvent)
    if global_variables.simulation:
        SHiP.digitize()
 # IS BROKEN SHiP.reconstruct()
 # memory monitoring
 # mem_monitor() 
 
# end loop over events
SHiP.finish()
