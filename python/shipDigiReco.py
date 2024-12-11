import os,ROOT,shipVertex,shipDet_conf
import global_variables
if global_variables.realPR == "Prev":
  import shipPatRec_prev as shipPatRec # The previous version of the pattern recognition
else: import shipPatRec
import shipunit as u
import rootUtils as ut
from array import array
import sys
from math import fabs
stop  = ROOT.TVector3()
start = ROOT.TVector3()

class ShipDigiReco:
 " convert FairSHiP MC hits / digitized hits to measurements"
 def __init__(self,fout,fgeo):
  self.fn = ROOT.TFile.Open(fout,'update')
  self.sTree     = self.fn.cbmsim
  if self.sTree.GetBranch("FitTracks"):
    print("remove RECO branches and rerun reconstruction")
    self.fn.Close()
    # make a new file without reco branches
    f = ROOT.TFile(fout)
    sTree = f.cbmsim
    if sTree.GetBranch("FitTracks"): sTree.SetBranchStatus("FitTracks",0)
    if sTree.GetBranch("goodTracks"): sTree.SetBranchStatus("goodTracks",0)
    if sTree.GetBranch("VetoHitOnTrack"): sTree.SetBranchStatus("VetoHitOnTrack",0)
    if sTree.GetBranch("Particles"): sTree.SetBranchStatus("Particles",0)
    if sTree.GetBranch("fitTrack2MC"): sTree.SetBranchStatus("fitTrack2MC",0)
    if sTree.GetBranch("EcalClusters"): sTree.SetBranchStatus("EcalClusters",0)
    if sTree.GetBranch("EcalReconstructed"): sTree.SetBranchStatus("EcalReconstructed",0)
    if sTree.GetBranch("Pid"): sTree.SetBranchStatus("Pid",0)
    if sTree.GetBranch("Digi_StrawtubesHits"): sTree.SetBranchStatus("Digi_StrawtubesHits",0)
    if sTree.GetBranch("Digi_SBTHits"): sTree.SetBranchStatus("Digi_SBTHits",0)
    if sTree.GetBranch("digiSBT2MC"):   sTree.SetBranchStatus("digiSBT2MC",0)
    if sTree.GetBranch("Digi_TimeDetHits"): sTree.SetBranchStatus("Digi_TimeDetHits",0)
    if sTree.GetBranch("Digi_UpstreamTaggerHits"): sTree.SetBranchStatus("Digi_UpstreamTaggerHits",0)
    if sTree.GetBranch("Digi_MuonHits"): sTree.SetBranchStatus("Digi_MuonHits",0)

    rawFile = fout.replace("_rec.root","_raw.root")
    recf = ROOT.TFile(rawFile,"recreate")
    newTree = sTree.CloneTree(0)
    for n in range(sTree.GetEntries()):
      sTree.GetEntry(n)
      rc = newTree.Fill()
    sTree.Clear()
    newTree.AutoSave()
    f.Close()
    recf.Close()
    os.system('cp '+rawFile +' '+fout)
    self.fn = ROOT.TFile(fout,'update')
    self.sTree     = self.fn.cbmsim
#  check that all containers are present, otherwise create dummy version
  self.dummyContainers={}
  branch_class = {"vetoPoint":"vetoPoint","ShipRpcPoint":"ShipRpcPoint","TargetPoint":"TargetPoint",\
                  "strawtubesPoint":"strawtubesPoint","EcalPointLite":"ecalPoint",\
                  "TimeDetPoint":"TimeDetPoint","muonPoint":"muonPoint","UpstreamTaggerPoint":"UpstreamTaggerPoint"}
  for x in branch_class:
    if not self.sTree.GetBranch(x):
     self.dummyContainers[x+"_array"] = ROOT.TClonesArray(branch_class[x])
     self.dummyContainers[x] = self.sTree.Branch(x,self.dummyContainers[x+"_array"],32000,-1)
     setattr(self.sTree,x,self.dummyContainers[x+"_array"])
     self.dummyContainers[x].Fill()
#
  if self.sTree.GetBranch("GeoTracks"): self.sTree.SetBranchStatus("GeoTracks",0)
# prepare for output
# event header
  self.header  = ROOT.FairEventHeader()
  self.eventHeader  = self.sTree.Branch("ShipEventHeader",self.header,32000,-1)
# fitted tracks
  self.fGenFitArray = ROOT.TClonesArray("genfit::Track")
  self.fGenFitArray.BypassStreamer(ROOT.kFALSE)
  self.fitTrack2MC  = ROOT.std.vector('int')()
  self.goodTracksVect  = ROOT.std.vector('int')()
  self.mcLink      = self.sTree.Branch("fitTrack2MC",self.fitTrack2MC,32000,-1)
  self.fitTracks   = self.sTree.Branch("FitTracks",  self.fGenFitArray,32000,-1)
  self.goodTracksBranch      = self.sTree.Branch("goodTracks",self.goodTracksVect,32000,-1)
  self.fTrackletsArray = ROOT.TClonesArray("Tracklet")
  self.Tracklets   = self.sTree.Branch("Tracklets",  self.fTrackletsArray,32000,-1)
#
  self.digiStraw    = ROOT.TClonesArray("strawtubesHit")
  self.digiStrawBranch   = self.sTree.Branch("Digi_StrawtubesHits",self.digiStraw,32000,-1)
  self.digiSBT    = ROOT.TClonesArray("vetoHit")
  self.digiSBTBranch=self.sTree.Branch("Digi_SBTHits",self.digiSBT,32000,-1)
  self.vetoHitOnTrackArray    = ROOT.TClonesArray("vetoHitOnTrack")
  self.vetoHitOnTrackBranch=self.sTree.Branch("VetoHitOnTrack",self.vetoHitOnTrackArray,32000,-1)
  self.digiSBT2MC  = ROOT.std.vector('std::vector< int >')()
  self.mcLinkSBT   = self.sTree.Branch("digiSBT2MC",self.digiSBT2MC,32000,-1)
  self.digiTimeDet    = ROOT.TClonesArray("TimeDetHit")
  self.digiTimeDetBranch=self.sTree.Branch("Digi_TimeDetHits",self.digiTimeDet,32000,-1)
  self.digiUpstreamTagger    = ROOT.TClonesArray("UpstreamTaggerHit")
  self.digiUpstreamTaggerBranch=self.sTree.Branch("Digi_UpstreamTaggerHits",self.digiUpstreamTagger,32000,-1)
  self.digiMuon    = ROOT.TClonesArray("muonHit")
  self.digiMuonBranch=self.sTree.Branch("Digi_muonHits",self.digiMuon,32000,-1)
# for the digitizing step
  self.v_drift = global_variables.modules["Strawtubes"].StrawVdrift()
  self.sigma_spatial = global_variables.modules["Strawtubes"].StrawSigmaSpatial()
# optional if present, splitcalCluster
  if self.sTree.GetBranch("splitcalPoint"):
   self.digiSplitcal = ROOT.TClonesArray("splitcalHit")
   self.digiSplitcalBranch=self.sTree.Branch("Digi_SplitcalHits",self.digiSplitcal,32000,-1)
   self.recoSplitcal = ROOT.TClonesArray("splitcalCluster")
   self.recoSplitcalBranch=self.sTree.Branch("Reco_SplitcalClusters",self.recoSplitcal,32000,-1)

# setup ecal reconstruction
  self.caloTasks = []
  if self.sTree.GetBranch("EcalPoint") and not self.sTree.GetBranch("splitcalPoint"):
# Creates. exports and fills calorimeter structure
   dflag = 10 if global_variables.debug else 0
   ecalGeo = global_variables.ecalGeoFile + 'z' + str(global_variables.ShipGeo.ecal.z) + ".geo"
   if not ecalGeo in os.listdir(os.environ["FAIRSHIP"]+"/geometry"):
     shipDet_conf.makeEcalGeoFile(global_variables.ShipGeo.ecal.z, global_variables.ShipGeo.ecal.File)
   ecalFiller=ROOT.ecalStructureFiller("ecalFiller", dflag,ecalGeo)
   ecalFiller.SetUseMCPoints(ROOT.kTRUE)
   ecalFiller.StoreTrackInformation()
   self.caloTasks.append(ecalFiller)
 #GeV -> ADC conversion
   ecalDigi=ROOT.ecalDigi("ecalDigi",0)
   self.caloTasks.append(ecalDigi)
 #ADC -> GeV conversion
   ecalPrepare=ROOT.ecalPrepare("ecalPrepare",0)
   self.caloTasks.append(ecalPrepare)
 # Maximums locator
   ecalMaximumFind=ROOT.ecalMaximumLocator("maximumFinder",dflag)
   self.caloTasks.append(ecalMaximumFind)
 # Cluster calibration
   ecalClusterCalib=ROOT.ecalClusterCalibration("ecalClusterCalibration", 0)
 #4x4 cm cells
   ecalCl3PhS=ROOT.TFormula("ecalCl3PhS", "[0]+x*([1]+x*([2]+x*[3]))")
   ecalCl3PhS.SetParameters(6.77797e-04, 5.75385e+00, 3.42690e-03, -1.16383e-04)
   ecalClusterCalib.SetStraightCalibration(3, ecalCl3PhS)
   ecalCl3Ph=ROOT.TFormula("ecalCl3Ph", "[0]+x*([1]+x*([2]+x*[3]))+[4]*x*y+[5]*x*y*y")
   ecalCl3Ph.SetParameters(0.000750975, 5.7552, 0.00282783, -8.0025e-05, -0.000823651, 0.000111561)
   ecalClusterCalib.SetCalibration(3, ecalCl3Ph)
#6x6 cm cells
   ecalCl2PhS=ROOT.TFormula("ecalCl2PhS", "[0]+x*([1]+x*([2]+x*[3]))")
   ecalCl2PhS.SetParameters(8.14724e-04, 5.67428e+00, 3.39030e-03, -1.28388e-04)
   ecalClusterCalib.SetStraightCalibration(2, ecalCl2PhS)
   ecalCl2Ph=ROOT.TFormula("ecalCl2Ph", "[0]+x*([1]+x*([2]+x*[3]))+[4]*x*y+[5]*x*y*y")
   ecalCl2Ph.SetParameters(0.000948095, 5.67471, 0.00339177, -0.000122629, -0.000169109, 8.33448e-06)
   ecalClusterCalib.SetCalibration(2, ecalCl2Ph)
   self.caloTasks.append(ecalClusterCalib)
# Cluster finder
   ecalClusterFind=ROOT.ecalClusterFinder("clusterFinder",dflag)
   self.caloTasks.append(ecalClusterFind)
# Calorimeter reconstruction
   ecalReco=ROOT.ecalReco('ecalReco',0)
   self.caloTasks.append(ecalReco)
# Match reco to MC
   ecalMatch=ROOT.ecalMatch('ecalMatch',0)
   self.caloTasks.append(ecalMatch)
   if global_variables.EcalDebugDraw:
 # ecal drawer: Draws calorimeter structure, incoming particles, clusters, maximums
    ecalDrawer=ROOT.ecalDrawer("clusterFinder",10)
    self.caloTasks.append(ecalDrawer)
 # add pid reco
   import shipPid
   self.caloTasks.append(shipPid.Task(self))
# prepare vertexing
  self.Vertexing = shipVertex.Task(global_variables.h, self.sTree)
# setup random number generator
  self.random = ROOT.TRandom()
  ROOT.gRandom.SetSeed(13)
  self.PDG = ROOT.TDatabasePDG.Instance()
# access ShipTree
  self.sTree.GetEvent(0)
  if len(self.caloTasks)>0:
   print("** initialize Calo reconstruction **")
   self.ecalStructure     = ecalFiller.InitPython(self.sTree.EcalPointLite)
   ecalDigi.InitPython(self.ecalStructure)
   ecalPrepare.InitPython(self.ecalStructure)
   self.ecalMaximums      = ecalMaximumFind.InitPython(self.ecalStructure)
   self.ecalCalib         = ecalClusterCalib.InitPython()
   self.ecalClusters      = ecalClusterFind.InitPython(self.ecalStructure, self.ecalMaximums, self.ecalCalib)
   self.EcalClusters = self.sTree.Branch("EcalClusters",self.ecalClusters,32000,-1)
   self.ecalReconstructed = ecalReco.InitPython(self.sTree.EcalClusters, self.ecalStructure, self.ecalCalib)
   self.EcalReconstructed = self.sTree.Branch("EcalReconstructed",self.ecalReconstructed,32000,-1)
   ecalMatch.InitPython(self.ecalStructure, self.ecalReconstructed, self.sTree.MCTrack)
   if global_variables.EcalDebugDraw:
     ecalDrawer.InitPython(self.sTree.MCTrack, self.sTree.EcalPoint, self.ecalStructure, self.ecalClusters)
  else:
   ecalClusters      = ROOT.TClonesArray("ecalCluster")
   ecalReconstructed = ROOT.TClonesArray("ecalReconstructed")
   self.EcalClusters = self.sTree.Branch("EcalClusters",ecalClusters,32000,-1)
   self.EcalReconstructed = self.sTree.Branch("EcalReconstructed",ecalReconstructed,32000,-1)
#
# init geometry and mag. field
  gMan  = ROOT.gGeoManager
  self.geoMat =  ROOT.genfit.TGeoMaterialInterface()
#
  self.bfield = ROOT.genfit.FairShipFields()
  self.bfield.setField(global_variables.fieldMaker.getGlobalField())
  self.fM = ROOT.genfit.FieldManager.getInstance()
  self.fM.init(self.bfield)
  ROOT.genfit.MaterialEffects.getInstance().init(self.geoMat)

 # init fitter, to be done before importing shipPatRec
  #fitter          = ROOT.genfit.KalmanFitter()
  #fitter          = ROOT.genfit.KalmanFitterRefTrack()
  self.fitter      = ROOT.genfit.DAF()
  self.fitter.setMaxIterations(50)
  if global_variables.debug:
    self.fitter.setDebugLvl(1) # produces lot of printout
  #set to True if "real" pattern recognition is required also

# for 'real' PatRec
  shipPatRec.initialize(fgeo)

 def reconstruct(self):
   ntracks = self.findTracks()
   nGoodTracks = self.findGoodTracks()
   self.linkVetoOnTracks()
   for x in self.caloTasks:
    if hasattr(x,'execute'): x.execute()
    elif x.GetName() == 'ecalFiller': x.Exec('start',self.sTree.EcalPointLite)
    elif x.GetName() == 'ecalMatch':  x.Exec('start',self.ecalReconstructed, self.sTree.MCTrack)
    else : x.Exec('start')
   if len(self.caloTasks)>0:
    self.EcalClusters.Fill()
    self.EcalReconstructed.Fill()
   if global_variables.vertexing:
# now go for 2-track combinations
    self.Vertexing.execute()

 def digitize(self):
   self.sTree.t0 = self.random.Rndm()*1*u.microsecond
   self.header.SetEventTime( self.sTree.t0 )
   self.header.SetRunId( self.sTree.MCEventHeader.GetRunID() )
   self.header.SetMCEntryNumber( self.sTree.MCEventHeader.GetEventID() )  # counts from 1
   self.eventHeader.Fill()
   self.digiSBT.Delete()
   self.digiSBT2MC.clear()
   self.digitizeSBT()
   self.digiSBTBranch.Fill()
   self.mcLinkSBT.Fill()
   self.digiStraw.Delete()
   self.digitizeStrawTubes()
   self.digiStrawBranch.Fill()
   self.digiTimeDet.Delete()
   self.digitizeTimeDet()
   self.digiTimeDetBranch.Fill()
   # self.digiUpstreamTagger.Delete()
   # self.digitizeUpstreamTagger()         TR 19/6/2020 work in progress
   # self.digiUpstreamTaggerBranch.Fill()
   self.digiMuon.Delete()
   self.digitizeMuon()
   self.digiMuonBranch.Fill()
   if self.sTree.GetBranch("splitcalPoint"):
    self.digiSplitcal.Delete()
    self.recoSplitcal.Delete()
    self.digitizeSplitcal()
    self.digiSplitcalBranch.Fill()
    self.recoSplitcalBranch.Fill()

 def digitizeSplitcal(self):
   listOfDetID = {} # the idea is to keep only one hit for each cell/strip and if more points fall in the same cell/strip just sum up the energy
   index = 0
   for aMCPoint in self.sTree.splitcalPoint:
     aHit = ROOT.splitcalHit(aMCPoint,self.sTree.t0)
     detID = aHit.GetDetectorID()
     if detID not in listOfDetID:
       if self.digiSplitcal.GetSize() == index:
         self.digiSplitcal.Expand(index+1000)
       listOfDetID[detID] = index
       self.digiSplitcal[index]=aHit
       index+=1
     else:
       indexOfExistingHit = listOfDetID[detID]
       self.digiSplitcal[indexOfExistingHit].UpdateEnergy(aHit.GetEnergy())
   self.digiSplitcal.Compress() #remove empty slots from array

   ##########################
   # cluster reconstruction #
   ##########################

   # hit selection
   # step 0: select hits above noise threshold to use in cluster reconstruction
   noise_energy_threshold = 0.002 #GeV
   #noise_energy_threshold = 0.0015 #GeV
   list_hits_above_threshold = []
   # print '--- digitizeSplitcal - self.digiSplitcal.GetSize() = ', self.digiSplitcal.GetSize()
   for hit in self.digiSplitcal:
     if hit.GetEnergy() > noise_energy_threshold:
       hit.SetIsUsed(0)
       # hit.SetEnergyWeight(1)
       list_hits_above_threshold.append(hit)

   self.list_hits_above_threshold = list_hits_above_threshold

   # print '--- digitizeSplitcal - n hits above threshold = ', len(list_hits_above_threshold)

   # clustering
   # step 1: group of neighbouring cells: loose criteria -> splitting clusters is easier than merging clusters

   self.step = 1
   self.input_hits = list_hits_above_threshold
   list_clusters_of_hits = self.Clustering()

   # step 2: to check if clusters can be split do clustering separtely in the XZ and YZ planes

   self.step = 2
   # print "--- digitizeSplitcal ==== STEP 2 ==== "
   list_final_clusters = {}
   index_final_cluster = 0

   for i in list_clusters_of_hits:

     list_hits_x = []
     list_hits_y = []
     for hit in list_clusters_of_hits[i]:
       hit.SetIsUsed(0)
       if hit.IsX(): list_hits_x.append(hit)
       if hit.IsY(): list_hits_y.append(hit) # FIXME: check if this could work also with high precision layers

     ###########

     #re-run reclustering only in xz plane possibly with different criteria
     self.input_hits = list_hits_x
     list_subclusters_of_x_hits = self.Clustering()
     cluster_energy_x = self.GetClusterEnergy(list_hits_x)

     # print "--- digitizeSplitcal - len(list_subclusters_of_x_hits) = ", len(list_subclusters_of_x_hits)

     self.list_subclusters_of_hits = list_subclusters_of_x_hits
     list_of_subclusters_x = self.GetSubclustersExcludingFragments()

     # compute energy weight
     weights_from_x_splitting = {}
     for index_subcluster in list_of_subclusters_x:
       subcluster_energy_x = self.GetClusterEnergy(list_of_subclusters_x[index_subcluster])
       weight = subcluster_energy_x/cluster_energy_x
       # print "======> weight = ", weight
       weights_from_x_splitting[index_subcluster] = weight

     ###########

     #re-run reclustering only in yz plane possibly with different criteria
     self.input_hits = list_hits_y
     list_subclusters_of_y_hits = self.Clustering()
     cluster_energy_y = self.GetClusterEnergy(list_hits_y)

     # print "--- digitizeSplitcal - len(list_subclusters_of_y_hits) = ", len(list_subclusters_of_y_hits)

     self.list_subclusters_of_hits = list_subclusters_of_y_hits
     list_of_subclusters_y = self.GetSubclustersExcludingFragments()

     # compute energy weight
     weights_from_y_splitting = {}
     for index_subcluster in list_of_subclusters_y:
       subcluster_energy_y = self.GetClusterEnergy(list_of_subclusters_y[index_subcluster])
       weight = subcluster_energy_y/cluster_energy_y
       # print "======> weight = ", weight
       weights_from_y_splitting[index_subcluster] = weight


     ###########

     # final list of clusters
     # In principle one could go directly with the loop without checking if the size of subcluster x/y are == 1.
     # But I noticed that in the second step the reclustering can trow away few lonely hits, making the weight just below 1
     # While looking for how to recover that, this is a quick fix
     if list_of_subclusters_x == 1 and list_of_subclusters_y == 1:
       list_final_clusters[index_final_cluster] = list_clusters_of_hits[i]
       for hit in list_final_clusters[index_final_cluster]:
         hit.AddClusterIndex(index_final_cluster)
         hit.AddEnergyWeight(1.)
       index_final_cluster += 1
     else:

       # this works, but one could try to reduce the number of shared hits

       for ix in list_of_subclusters_x:
         for iy in list_of_subclusters_y:

           for hit in list_of_subclusters_y[iy]:
              hit.AddClusterIndex(index_final_cluster)
              hit.AddEnergyWeight(weights_from_x_splitting[ix])

           for hit in list_of_subclusters_x[ix]:
              hit.AddClusterIndex(index_final_cluster)
              hit.AddEnergyWeight(weights_from_y_splitting[iy])

           list_final_clusters[index_final_cluster] = list_of_subclusters_y[iy] + list_of_subclusters_x[ix]
           index_final_cluster += 1

       # # try to reduce number of shared hits (if it does not work go back to solution above)
       # # ok, it has potential but it needs more thinking

       # for ix in list_of_subclusters_x:
       #   for iy in list_of_subclusters_y:

       #     list_final_clusters[index_final_cluster] = []

       #     for hitx in list_of_subclusters_x[ix]:
       #       self.input_hits = list_of_subclusters_y[iy]
       #       neighbours = self.getNeighbours(hitx)
       #       if len(neighbours) > 0:
       #         hitx.AddClusterIndex(index_final_cluster)
       #         hitx.AddEnergyWeight(weights_from_y_splitting[iy])
       #         list_final_clusters[index_final_cluster].append(hitx)
       #         for hity in neighbours:
       #           hity.AddClusterIndex(index_final_cluster)
       #           hity.AddEnergyWeight(weights_from_x_splitting[ix])
       #           list_final_clusters[index_final_cluster].append(hity)

       #     index_final_cluster += 1


   #################
   # fill clusters #
   #################

   for i in list_final_clusters:
     # print '------------------------'
     # print '------ digitizeSplitcal - cluster n = ', i
     # print '------ digitizeSplitcal - cluster size = ', len(list_final_clusters[i])

     for j,h in enumerate(list_final_clusters[i]):
       if j==0: aCluster = ROOT.splitcalCluster(h)
       else: aCluster.AddHit(h)

     aCluster.SetIndex(int(i))
     aCluster.ComputeEtaPhiE()
     # aCluster.Print()

     if self.recoSplitcal.GetSize() == i:
       self.recoSplitcal.Expand(i+1000)
     self.recoSplitcal[i]=aCluster

   self.recoSplitcal.Compress() #remove empty slots from array


   # #################
   # # visualisation #
   # #################

   # c_yz = ROOT.TCanvas("c_yz","c_yz", 200, 10, 800, 800)
   # graphs_yz = []

   # for i in list_final_clusters:

   #   gr_yz = ROOT.TGraphErrors()
   #   gr_yz.SetLineColor( i+1 )
   #   gr_yz.SetLineWidth( 2 )
   #   gr_yz.SetMarkerColor( i+1 )
   #   gr_yz.SetMarkerStyle( 21 )
   #   gr_yz.SetTitle( 'clusters in y-z plane' )
   #   gr_yz.GetXaxis().SetTitle( 'Y [cm]' )
   #   gr_yz.GetYaxis().SetTitle( 'Z [cm]' )

   #   for j,hit in enumerate (list_final_clusters[i]):

   #     gr_yz.SetPoint(j,hit.GetY(),hit.GetZ())
   #     gr_yz.SetPointError(j,hit.GetYError(),hit.GetZError())

   #   gr_yz.GetXaxis().SetLimits( -620, 620 )
   #   gr_yz.GetYaxis().SetRangeUser( 3600, 3800 )
   #   graphs_yz.append(gr_yz)

   #   c_yz.cd()
   #   c_yz.Update()
   #   if i==0:
   #     graphs_yz[-1].Draw( 'AP' )
   #   else:
   #     graphs_yz[-1].Draw( 'P' )

   # c_yz.Print("final_clusters_yz.eps")

   # ############################

##########################

 def GetSubclustersExcludingFragments(self):

   list_subclusters_excluding_fragments = {}

   fragment_indices = []
   subclusters_indices = []
   for k in self.list_subclusters_of_hits:
     subcluster_size = len(self.list_subclusters_of_hits[k])
     if subcluster_size < 5: #FIXME: it can be tuned on a physics case (maybe use fraction of hits or energy)
       fragment_indices.append(k)
     else:
       subclusters_indices.append(k)
   # if len(subclusters_indices) > 1:
   #   print "--- digitizeSplitcal - *** CLUSTER NEED TO BE SPLIT - set energy weight"
   # else:
   #   print "--- digitizeSplitcal - CLUSTER DOES NOT NEED TO BE SPLIT "

   # merge fragments in the closest subcluster. If there is not subcluster but everything is fragmented, merge all the fragments together
   minDistance = -1
   minIndex = -1

   if len(subclusters_indices) == 0 and len(fragment_indices) != 0: # only fragments
     subclusters_indices.append(0) # merge all fragments into the first fragment

   for index_fragment in fragment_indices:
     #print "--- index_fragment = ", index_fragment
     first_hit_fragment = self.list_subclusters_of_hits[index_fragment][0]
     for index_subcluster in subclusters_indices:
       #print "--- index_subcluster = ", index_subcluster
       first_hit_subcluster = self.list_subclusters_of_hits[index_subcluster][0]
       if first_hit_fragment.IsX():
         distance = fabs(first_hit_fragment.GetX()-first_hit_subcluster.GetX())
       else:
         distance = fabs(first_hit_fragment.GetY()-first_hit_subcluster.GetY())
       if (minDistance < 0 or distance < minDistance):
         minDistance = distance
         minIndex = index_subcluster

     # for h in self.list_subclusters_of_hits[index_fragment]:
     #   h.SetClusterIndex(minIndex)

     #print "--- minIndex = ", minIndex
     if minIndex != index_fragment: # in case there were only fragments - this is to prevent to sum twice fragment 0
       #print "--- BEFORE - len(self.list_subclusters_of_hits[minIndex]) = ", len(self.list_subclusters_of_hits[minIndex])
       self.list_subclusters_of_hits[minIndex] += self.list_subclusters_of_hits[index_fragment]
       #print "--- AFTER - len(self.list_subclusters_of_hits[minIndex]) = ", len(self.list_subclusters_of_hits[minIndex])


   for counter, index_subcluster in enumerate(subclusters_indices):
     list_subclusters_excluding_fragments[counter] = self.list_subclusters_of_hits[index_subcluster]

   return list_subclusters_excluding_fragments



 def GetClusterEnergy(self, list_hits):
   energy = 0
   for hit in list_hits:
     energy += hit.GetEnergy()
   return energy


 def Clustering(self):

   list_hits_in_cluster = {}
   cluster_index = -1

   for i,hit in enumerate(self.input_hits):
     if hit.IsUsed()==1:
       continue

     neighbours = self.getNeighbours(hit)
     # hit.Print()
     # #print "--- digitizeSplitcal - index of unused hit = ", i
     # print '--- digitizeSplitcal - hit has n neighbours = ', len(neighbours)

     if len(neighbours) < 1:
       # # hit.SetClusterIndex(-1) # lonely fragment
       # print '--- digitizeSplitcal - lonely fragment '
       continue

     cluster_index = cluster_index + 1
     hit.SetIsUsed(1)
     # hit.SetClusterIndex(cluster_index)
     list_hits_in_cluster[cluster_index] = []
     list_hits_in_cluster[cluster_index].append(hit)
     #print '--- digitizeSplitcal - cluster_index = ', cluster_index

     for neighbouringHit in neighbours:
       # print '--- digitizeSplitcal - in neighbouringHit - len(neighbours) = ', len(neighbours)

       if neighbouringHit.IsUsed()==1:
         continue

       # neighbouringHit.SetClusterIndex(cluster_index)
       neighbouringHit.SetIsUsed(1)
       list_hits_in_cluster[cluster_index].append(neighbouringHit)

       # ## test ###
       # # for step 2, add hits of different type to subcluster but to not look for their neighbours
       # not_same_type = hit.IsX() != neighbouringHit.IsX()
       # if self.step==2 and not_same_type:
       #   continue
       # ###########

       expand_neighbours = self.getNeighbours(neighbouringHit)
       # print '--- digitizeSplitcal - len(expand_neighbours) = ', len(expand_neighbours)

       if len(expand_neighbours) >= 1:
         for additionalHit in expand_neighbours:
           if additionalHit not in neighbours:
             neighbours.append(additionalHit)

   return list_hits_in_cluster



 def getNeighbours(self,hit):

   list_neighbours = []
   err_x_1 = hit.GetXError()
   err_y_1 = hit.GetYError()
   err_z_1 = hit.GetZError()

   layer_1 = hit.GetLayerNumber()

   # allow one or more 'missing' hit in x/y: not large difference between 1 (no gap) or 2 (one 'missing' hit)
   max_gap = 2.
   if hit.IsX(): err_x_1 = err_x_1*max_gap
   if hit.IsY(): err_y_1 = err_y_1*max_gap

   for hit2 in self.input_hits:
     if hit2 is not hit:
       Dx = fabs(hit2.GetX()-hit.GetX())
       Dy = fabs(hit2.GetY()-hit.GetY())
       Dz = fabs(hit2.GetZ()-hit.GetZ())
       err_x_2 = hit2.GetXError()
       err_y_2 = hit2.GetYError()
       err_z_2 = hit2.GetZError()

       # layer_2 = hit2.GetLayerNumber()
       # Dlayer = fabs(layer_2-layer_1)

       # allow one or more 'missing' hit in x/y
       if hit2.IsX(): err_x_2 = err_x_2*max_gap
       if hit2.IsY(): err_y_2 = err_y_2*max_gap

       if self.step == 1: # or self.step == 2:
         # use Dz instead of Dlayer due to split of 1m between the 2 parts of the calo
         #if ((Dx<=(err_x_1+err_x_2) or Dy<=(err_y_1+err_y_2)) and Dz<=2*(err_z_1+err_z_2)):
         #if ((Dx<=(err_x_1+err_x_2) and Dy<=(err_y_1+err_y_2)) and Dz<=2*(err_z_1+err_z_2)):
         if hit.IsX():
           if (Dx<=(err_x_1+err_x_2) and Dz<=2*(err_z_1+err_z_2) and ((Dy<=(err_y_1+err_y_2) and Dz>0.) or (Dy==0)) ):
                 list_neighbours.append(hit2)
         if hit.IsY():
           if (Dy<=(err_y_1+err_y_2) and Dz<=2*(err_z_1+err_z_2) and ((Dx<=(err_x_1+err_x_2) and Dz>0.) or (Dx==0)) ):
                 list_neighbours.append(hit2)

       elif self.step == 2:
         #for step 2 relax or remove at all condition on Dz
         #(some clusters were split erroneously along z while here one wants to split only in x/y )
         # first try: relax z condition
         if hit.IsX():
           if (Dx<=(err_x_1+err_x_2) and Dz<=6*(err_z_1+err_z_2) and ((Dy<=(err_y_1+err_y_2) and Dz>0.) or (Dy==0)) ):
           #if (Dx<=(err_x_1+err_x_2) and Dz<=6*(err_z_1+err_z_2) and Dy<=(err_y_1+err_y_2) and Dz>0.):
                 list_neighbours.append(hit2)
         if hit.IsY():
           if (Dy<=(err_y_1+err_y_2) and Dz<=6*(err_z_1+err_z_2) and ((Dx<=(err_x_1+err_x_2) and Dz>0.) or (Dx==0)) ):
           #if (Dy<=(err_y_1+err_y_2) and Dz<=6*(err_z_1+err_z_2) and Dx<=(err_x_1+err_x_2) and Dz>0. ):
                 list_neighbours.append(hit2)
       else:
         print("-- getNeighbours: ERROR: step not defined ")

   return list_neighbours




 def digitizeTimeDet(self):
   index = 0
   hitsPerDetId = {}
   for aMCPoint in self.sTree.TimeDetPoint:
     aHit = ROOT.TimeDetHit(aMCPoint,self.sTree.t0)
     if self.digiTimeDet.GetSize() == index: self.digiTimeDet.Expand(index+1000)
     self.digiTimeDet[index]=aHit
     detID = aHit.GetDetectorID()
     if aHit.isValid():
      if detID in hitsPerDetId:
       t = aHit.GetMeasurements()
       ct = aHit.GetMeasurements()
# this is not really correct, only first attempt
# case that one measurement only is earlier not taken into account
# SetTDC(Float_t val1, Float_t val2)
       if  t[0]>ct[0] or t[1]>ct[1]:
 # second hit with smaller tdc
        self.digiTimeDet[hitsPerDetId[detID]].setInvalid()
        hitsPerDetId[detID] = index
     index+=1

 def digitizeUpstreamTagger(self):
   index = 0
   hitsPerDetId = {}
   for aMCPoint in self.sTree.UpstreamTaggerPoint:
     aHit = ROOT.UpstreamTaggerHit(aMCPoint, global_variables.modules["UpstreamTagger"], self.sTree.t0)
     if self.digiUpstreamTagger.GetSize() == index: self.digiUpstreamTagger.Expand(index+1000)
     self.digiUpstreamTagger[index]=aHit
     detID = aHit.GetDetectorID()
     if aHit.isValid():
      if detID in hitsPerDetId:
       t = aHit.GetMeasurements()
       ct = aHit.GetMeasurements()
# this is not really correct, only first attempt
# case that one measurement only is earlier not taken into account
# SetTDC(Float_t val1, Float_t val2)
       if  t[0]>ct[0] or t[1]>ct[1]:
 # second hit with smaller tdc
        self.digiUpstreamTagger[hitsPerDetId[detID]].setInvalid()
        hitsPerDetId[detID] = index
     index+=1


 def digitizeMuon(self):
   index = 0
   hitsPerDetId = {}
   for aMCPoint in self.sTree.muonPoint:
     aHit = ROOT.muonHit(aMCPoint,self.sTree.t0)
     if self.digiMuon.GetSize() == index: self.digiMuon.Expand(index+1000)
     self.digiMuon[index]=aHit
     detID = aHit.GetDetectorID()
     if aHit.isValid():
      if detID in hitsPerDetId:
       if self.digiMuon[hitsPerDetId[detID]].GetDigi() > aHit.GetDigi():
 # second hit with smaller tdc
        self.digiMuon[hitsPerDetId[detID]].setValidity(0)
        hitsPerDetId[detID] = index
     index+=1

 def digitizeSBT(self):
     ElossPerDetId    = {}
     tOfFlight        = {}
     listOfVetoPoints = {}
     key=-1
     for aMCPoint in self.sTree.vetoPoint:
       key+=1
       detID=aMCPoint.GetDetectorID()
       Eloss=aMCPoint.GetEnergyLoss()
       if detID not in ElossPerDetId:
        ElossPerDetId[detID]=0
        listOfVetoPoints[detID]=[]
        tOfFlight[detID]=[]
       ElossPerDetId[detID] += Eloss
       listOfVetoPoints[detID].append(key)
       tOfFlight[detID].append(aMCPoint.GetTime())
     index=0
     for seg in ElossPerDetId:
       aHit = ROOT.vetoHit(seg,ElossPerDetId[seg])
       aHit.SetTDC(min( tOfFlight[seg] ) + self.sTree.t0 )
       if self.digiSBT.GetSize() == index:
          self.digiSBT.Expand(index+1000)
       if ElossPerDetId[seg]<0.045:    aHit.setInvalid()  # threshold for liquid scintillator, source Berlin group
       self.digiSBT[index] = aHit
       v = ROOT.std.vector('int')()
       for x in listOfVetoPoints[seg]:
           v.push_back(x)
       self.digiSBT2MC.push_back(v)
       index=index+1
 def digitizeStrawTubes(self):
 # digitize FairSHiP MC hits
   index = 0
   hitsPerDetId = {}
   for aMCPoint in self.sTree.strawtubesPoint:
     aHit = ROOT.strawtubesHit(aMCPoint,self.sTree.t0)
     if self.digiStraw.GetSize() == index: self.digiStraw.Expand(index+1000)
     self.digiStraw[index]=aHit
     if aHit.isValid():
      detID = aHit.GetDetectorID()
      if detID in hitsPerDetId:
       if self.digiStraw[hitsPerDetId[detID]].GetTDC() > aHit.GetTDC():
 # second hit with smaller tdc
        self.digiStraw[hitsPerDetId[detID]].setInvalid()
        hitsPerDetId[detID] = index
     index+=1

 def withT0Estimate(self):
 # loop over all straw tdcs and make average, correct for ToF
  n = 0
  t0 = 0.
  key = -1
  SmearedHits = []
  v_drift = global_variables.modules["Strawtubes"].StrawVdrift()
  global_variables.modules["Strawtubes"].StrawEndPoints(10002001, start, stop)
  z1 = stop.z()
  for aDigi in self.digiStraw:
    key+=1
    if not aDigi.isValid(): continue
    detID = aDigi.GetDetectorID()
# don't use hits from straw veto
    station = int(detID//10000000)
    if station > 4 : continue
    global_variables.modules["Strawtubes"].StrawEndPoints(detID, start, stop)
    delt1 = (start[2]-z1)/u.speedOfLight
    t0+=aDigi.GetDigi()-delt1
    SmearedHits.append( {'digiHit':key,'xtop':stop.x(),'ytop':stop.y(),'z':stop.z(),'xbot':start.x(),'ybot':start.y(),'dist':aDigi.GetDigi(), 'detID':detID} )
    n+=1
  if n>0: t0 = t0/n - 73.2*u.ns
  for s in SmearedHits:
    delt1 = (s['z']-z1)/u.speedOfLight
    s['dist'] = (s['dist'] -delt1 -t0)*v_drift
  return SmearedHits

 def smearHits(self,no_amb=None):
 # smear strawtube points
  SmearedHits = []
  key = -1
  v_drift = global_variables.modules["Strawtubes"].StrawVdrift()
  global_variables.modules["Strawtubes"].StrawEndPoints(10002001, start, stop)
  z1 = stop.z()
  for aDigi in self.digiStraw:
     key+=1
     if not aDigi.isValid(): continue
     detID = aDigi.GetDetectorID()
# don't use hits from straw veto
     station = int(detID//10000000)
     if station > 4 : continue
     global_variables.modules["Strawtubes"].StrawEndPoints(detID, start, stop)
   #distance to wire
     delt1 = (start[2]-z1)/u.speedOfLight
     p=self.sTree.strawtubesPoint[key]
     # use true t0  construction:
     #     fdigi = t0 + p->GetTime() + t_drift + ( stop[0]-p->GetX() )/ speedOfLight;
     smear = (aDigi.GetDigi() - self.sTree.t0  - p.GetTime() - ( stop[0]-p.GetX() )/ u.speedOfLight) * v_drift
     if no_amb: smear = p.dist2Wire()
     SmearedHits.append( {'digiHit':key,'xtop':stop.x(),'ytop':stop.y(),'z':stop.z(),'xbot':start.x(),'ybot':start.y(),'dist':smear, 'detID':detID} )
     # Note: top.z()==bot.z() unless misaligned, so only add key 'z' to smearedHit
     if abs(stop.y()) == abs(start.y()):
       global_variables.h['disty'].Fill(smear)
     elif abs(stop.y()) > abs(start.y()):
       global_variables.h['distu'].Fill(smear)
     elif abs(stop.y()) < abs(start.y()):
       global_variables.h['distv'].Fill(smear)

  return SmearedHits

 def findTracks(self):
  hitPosLists    = {}
  hit_detector_ids = {}
  stationCrossed = {}
  fittedtrackids=[]
  listOfIndices  = {}
  self.fGenFitArray.Clear()
  self.fTrackletsArray.Delete()
  self.fitTrack2MC.clear()

#
  if global_variables.withT0:
    self.SmearedHits = self.withT0Estimate()
  # old procedure, not including estimation of t0
  else:
    self.SmearedHits = self.smearHits(global_variables.withNoStrawSmearing)

  nTrack = -1
  trackCandidates = []

  if global_variables.realPR:
    # Do real PatRec
    track_hits = shipPatRec.execute(self.SmearedHits, global_variables.ShipGeo, global_variables.realPR)
    # Create hitPosLists for track fit
    for i_track in track_hits.keys():
      atrack = track_hits[i_track]
      atrack_y12 = atrack['y12']
      atrack_stereo12 = atrack['stereo12']
      atrack_y34 = atrack['y34']
      atrack_stereo34 = atrack['stereo34']
      atrack_smeared_hits = list(atrack_y12) + list(atrack_stereo12) + list(atrack_y34) + list(atrack_stereo34)
      for sm in atrack_smeared_hits:
        detID = sm['detID']
        station = int(detID//10000000)
        trID = i_track
        # Collect hits for track fit
        if trID not in hitPosLists:
          hitPosLists[trID] = ROOT.std.vector('TVectorD')()
          listOfIndices[trID] = []
          stationCrossed[trID]  = {}
          hit_detector_ids[trID] = ROOT.std.vector('int')()
        hit_detector_ids[trID].push_back(detID)
        m = array('d',[sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist']])
        hitPosLists[trID].push_back(ROOT.TVectorD(7,m))
        listOfIndices[trID].append(sm['digiHit'])
        if station not in stationCrossed[trID]:
          stationCrossed[trID][station] = 0
        stationCrossed[trID][station] += 1
  else: # do fake pattern recognition
   for sm in self.SmearedHits:
    detID = self.digiStraw[sm['digiHit']].GetDetectorID()
    station = int(detID//10000000)
    trID = self.sTree.strawtubesPoint[sm['digiHit']].GetTrackID()
    if trID not in hitPosLists:
      hitPosLists[trID]     = ROOT.std.vector('TVectorD')()
      listOfIndices[trID] = []
      stationCrossed[trID]  = {}
      hit_detector_ids[trID] = ROOT.std.vector('int')()
    hit_detector_ids[trID].push_back(detID)
    m = array('d',[sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist']])
    hitPosLists[trID].push_back(ROOT.TVectorD(7,m))
    listOfIndices[trID].append(sm['digiHit'])
    if station not in stationCrossed[trID]: stationCrossed[trID][station]=0
    stationCrossed[trID][station]+=1
#
   # for atrack in listOfIndices:
   #   # make tracklets out of trackCandidates, just for testing, should be output of proper pattern recognition
   #  nTracks   = self.fTrackletsArray.GetEntries()
   #  aTracklet  = self.fTrackletsArray.ConstructedAt(nTracks)
   #  listOfHits = aTracklet.getList()
   #  aTracklet.setType(3)
   #  for index in listOfIndices[atrack]:
   #    listOfHits.push_back(index)
#
  for atrack in hitPosLists:
    if atrack < 0: continue # these are hits not assigned to MC track because low E cut
    pdg    = self.sTree.MCTrack[atrack].GetPdgCode()
    if not self.PDG.GetParticle(pdg): continue # unknown particle
    # pdg = 13
    meas = hitPosLists[atrack]
    detIDs = hit_detector_ids[atrack]
    nM = meas.size()
    if nM < 25 : continue                          # not enough hits to make a good trackfit
    if len(stationCrossed[atrack]) < 3 : continue  # not enough stations crossed to make a good trackfit
    if global_variables.debug:
       mctrack = self.sTree.MCTrack[atrack]
    # charge = self.PDG.GetParticle(pdg).Charge()/(3.)
    posM = ROOT.TVector3(0, 0, 0)
    momM = ROOT.TVector3(0,0,3.*u.GeV)
# approximate covariance
    covM = ROOT.TMatrixDSym(6)
    resolution = self.sigma_spatial
    if global_variables.withT0:
      resolution *= 1.4 # worse resolution due to t0 estimate
    for  i in range(3):   covM[i][i] = resolution*resolution
    covM[0][0]=resolution*resolution*100.
    for  i in range(3,6): covM[i][i] = ROOT.TMath.Power(resolution / nM / ROOT.TMath.Sqrt(3), 2)
# trackrep
    rep = ROOT.genfit.RKTrackRep(pdg)
# smeared start state
    stateSmeared = ROOT.genfit.MeasuredStateOnPlane(rep)
    rep.setPosMomCov(stateSmeared, posM, momM, covM)
# create track
    seedState = ROOT.TVectorD(6)
    seedCov   = ROOT.TMatrixDSym(6)
    rep.get6DStateCov(stateSmeared, seedState, seedCov)
    theTrack = ROOT.genfit.Track(rep, seedState, seedCov)
    hitCov = ROOT.TMatrixDSym(7)
    hitCov[6][6] = resolution*resolution
    hitID = 0
    for m, detID in zip(meas, detIDs):
      tp = ROOT.genfit.TrackPoint(theTrack) # note how the point is told which track it belongs to
      measurement = ROOT.genfit.WireMeasurement(
        m,
        hitCov,
        detID,
        hitID,
        tp
      ) # the measurement is told which trackpoint it belongs to
      # print measurement.getMaxDistance()
      measurement.setMaxDistance(global_variables.ShipGeo.strawtubes.InnerStrawDiameter / 2.)
      # measurement.setLeftRightResolution(-1)
      tp.addRawMeasurement(measurement) # package measurement in the TrackPoint
      theTrack.insertPoint(tp)  # add point to Track
      hitID += 1
   # print "debug meas",atrack,nM,stationCrossed[atrack],self.sTree.MCTrack[atrack],pdg
    trackCandidates.append([theTrack,atrack])

  for entry in trackCandidates:
#check
    atrack = entry[1]
    theTrack = entry[0]
    try:
      theTrack.checkConsistency()
    except ROOT.genfit.Exception as e:
      print('Problem with track before fit, not consistent',atrack,theTrack)
      print(e.what())
      ut.reportError(e)
# do the fit
    try:
      self.fitter.processTrack(theTrack) # processTrackWithRep(theTrack,rep,True)
    except:
      if global_variables.debug:
        print("genfit failed to fit track")
      error = "genfit failed to fit track"
      ut.reportError(error)
      continue
#check
    try:
      theTrack.checkConsistency()
    except ROOT.genfit.Exception as e:
      if global_variables.debug:
        print('Problem with track after fit, not consistent', atrack, theTrack)
        print(e.what())
      error = "Problem with track after fit, not consistent"
      ut.reportError(error)
    try:
      fittedState = theTrack.getFittedState()
      fittedMom = fittedState.getMomMag()
    except:
      error = "Problem with fittedstate"
      ut.reportError(error)
      continue
    fitStatus = theTrack.getFitStatus()
    try:
      fitStatus.isFitConverged()
    except ROOT.genfit.Exception as e:
      error = "Fit not converged"
      ut.reportError(error)
    nmeas = fitStatus.getNdf()
    if nmeas > 0:
      chi2 = fitStatus.getChi2() / nmeas
      global_variables.h['chi2'].Fill(chi2)
# make track persistent
    nTrack   = self.fGenFitArray.GetEntries()
    self.fGenFitArray[nTrack] = theTrack
    # self.fitTrack2MC.push_back(atrack)
    if global_variables.debug:
     print('save track',theTrack,chi2,nmeas,fitStatus.isFitConverged())
    # Save MC link
    track_ids = []
    for index in listOfIndices[atrack]:
      ahit = self.sTree.strawtubesPoint[index]
      track_ids += [ahit.GetTrackID()]
    frac, tmax = self.fracMCsame(track_ids)
    self.fitTrack2MC.push_back(tmax)
    # Save hits indexes of the the fitted tracks
    nTracks   = self.fTrackletsArray.GetEntries()
    aTracklet  = self.fTrackletsArray.ConstructedAt(nTracks)
    listOfHits = aTracklet.getList()
    aTracklet.setType(1)
    for index in listOfIndices[atrack]:
      listOfHits.push_back(index)
  self.Tracklets.Fill()
  self.fitTracks.Fill()
  self.mcLink.Fill()
# debug
  if global_variables.debug:
   print('save tracklets:')
   for x in self.sTree.Tracklets:
    print(x.getType(),x.getList().size())
  return nTrack+1

 def findGoodTracks(self):
   self.goodTracksVect.clear()
   nGoodTracks = 0
   for i,track in enumerate(self.fGenFitArray):
    fitStatus = track.getFitStatus()
    if not fitStatus.isFitConverged(): continue
    nmeas = fitStatus.getNdf()
    chi2  = fitStatus.getChi2()/nmeas
    if chi2<50 and not chi2<0:
      self.goodTracksVect.push_back(i)
      nGoodTracks+=1
   self.goodTracksBranch.Fill()
   return nGoodTracks

 def findVetoHitOnTrack(self,track):
   distMin = 99999.
   vetoHitOnTrack = ROOT.vetoHitOnTrack()
   xx  = track.getFittedState()
   rep   = ROOT.genfit.RKTrackRep(xx.getPDG())
   state = ROOT.genfit.StateOnPlane(rep)
   rep.setPosMom(state,xx.getPos(),xx.getMom())
   for i,vetoHit in enumerate(self.digiSBT):
     vetoHitPos = vetoHit.GetXYZ()
     try:
      rep.extrapolateToPoint(state,vetoHitPos,False)
     except:
      error =  "shipDigiReco::findVetoHitOnTrack extrapolation did not worked"
      ut.reportError(error)
      if global_variables.debug:
        print(error)
      continue
     dist = (rep.getPos(state) - vetoHitPos).Mag()
     if dist < distMin:
       distMin = dist
       vetoHitOnTrack.SetDist(distMin)
       vetoHitOnTrack.SetHitID(i)
   return vetoHitOnTrack

 def linkVetoOnTracks(self):
   self.vetoHitOnTrackArray.Delete()
   index = 0
   for goodTrak in self.goodTracksVect:
     track = self.fGenFitArray[goodTrak]
     if self.vetoHitOnTrackArray.GetSize() == index: self.vetoHitOnTrackArray.Expand(index+1000)
     self.vetoHitOnTrackArray[index] = self.findVetoHitOnTrack(track)
     index+=1
   self.vetoHitOnTrackBranch.Fill()

 def fracMCsame(self, trackids):
  track={}
  nh=len(trackids)
  for tid in trackids:
    if tid in track:
      track[tid] += 1
    else:
      track[tid] = 1
  if track != {}:
    tmax = max(track, key=track.get)
  else:
    track = {-999: 0}
    tmax = -999
  frac=0.0
  if nh > 0:
    frac = float(track[tmax]) / float(nh)
  return frac, tmax

 def finish(self):
  del self.fitter
  print('finished writing tree')
  self.sTree.Write()
  ut.errorSummary()
  ut.writeHists(global_variables.h,"recohists.root")
  if global_variables.realPR:
    shipPatRec.finalize()
  self.fn.Close()
