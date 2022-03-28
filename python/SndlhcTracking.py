import ROOT
from array import array
import shipunit as u

class Tracking(ROOT.FairTask):
 " Tracking "
 def Init(self):
   geoMat =  ROOT.genfit.TGeoMaterialInterface()
   bfield     = ROOT.genfit.ConstField(0,0,0)   # constant field of zero
   fM = ROOT.genfit.FieldManager.getInstance()
   fM.init(bfield)
   ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
   ROOT.genfit.MaterialEffects.getInstance().setNoEffects()
   lsOfGlobals  = ROOT.gROOT.GetListOfGlobals()
   self.scifiDet = lsOfGlobals.FindObject('Scifi')
   self.mufiDet = lsOfGlobals.FindObject('MuFilter')

   self.fitter = ROOT.genfit.KalmanFitter()
   self.fitter.setMaxIterations(50)
   self.sigmaScifi_spatial = 150.*u.um
   self.sigmaMufiUS_spatial = 2.*u.cm
   self.sigmaMufiDS_spatial = 0.3*u.cm
   self.Debug = False
   self.kalman_tracks = ROOT.TObjArray(10);
   self.ioman = ROOT.FairRootManager.Instance()
   self.event = self.ioman.GetInChain()

   self.ioman.Register("Reco_MuonTracks", "", self.kalman_tracks, ROOT.kTRUE);

   self.systemAndPlanes  = {1:2,2:5,3:7}
   self.nPlanes = 8
   self.nClusters = 11
   return 0

 def FinishEvent(self):
  pass

 def ExecuteTask(self,option=''):
    self.kalman_tracks.Clear()
    self.clusters = self.scifiCluster()
    if option=='DS':  self.trackCandidates = self.DStrack()
    elif option=='Scifi':  self.trackCandidates = self.Scifi_track()
    else:                   self.trackCandidates = self.patternReco()
    for aTrack in self.trackCandidates:
           rc = self.fitTrack(aTrack)
           if type(rc)==type(1):
                print('trackfit failed',rc,aTrack)
           else:
                self.kalman_tracks.Add(rc)

 def DStrack(self):
# special for H8 testbeam, make track with 2 DS stations only for low occupancy events
    trackCandidates = []
    stations = {}
    for s in self.systemAndPlanes:
       for plane in range(self.systemAndPlanes[s]): 
          stations[s*10+plane] = {}
    k=-1
    for aHit in self.MuFilterHits:
         k+=1
         if not aHit.isValid(): continue
         s = aHit.GetDetectorID()//10000
         p = (aHit.GetDetectorID()//1000)%10
         bar = aHit.GetDetectorID()%1000
         plane = s*10+p
         if s==3:
           if bar<60 or p==3: plane = s*10+2*p
           else:  plane = s*10+2*p+1
         stations[plane][k] = aHit
    success = True
    for p in range(30,34):
         if len(stations[p])>2 or len(stations[p])<1: success = False
    if success:
 # build trackCandidate
      hitlist = {}
      for p in range(30,34):
         k = list(stations[p].keys())[0]
         hitlist[k] = stations[p][k]
      trackCandidates.append(hitlist)
    return trackCandidates

 def Scifi_track(self):
# check for low occupancy and enough hits in Scifi
    trackCandidates = []
    stations = {}
    for s in range(1,6):
       for o in range(2):
          stations[s*10+o] = []
    for cl in self.clusters:
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
    if len(check)>=self.nPlanes and nclusters >= self.nClusters:
# build trackCandidate
       hitlist = {}
       for k in range(len(clusters)):
           hitlist[k] = clusters[k]
       trackCandidates.append(hitlist)
    return trackCandidates

 def scifiCluster(self):
       clusters = []
       hitDict = {}
       for k in range(self.event.Digi_ScifiHits.GetEntries()):
            d = self.event.Digi_ScifiHits[k]
            if not d.isValid(): continue 
            hitDict[d.GetDetectorID()] = k
       hitList = list(hitDict.keys())
       if len(hitList)>0:
              hitList.sort()
              tmp = [ hitList[0] ]
              cprev = hitList[0]
              ncl = 0
              last = len(hitList)-1
              hitvector = ROOT.std.vector("sndScifiHit*")()
              for i in range(len(hitList)):
                   if i==0 and len(hitList)>1: continue
                   c=hitList[i]
                   neighbour = False
                   if (c-cprev)==1:    # does not account for neighbours across sipms
                        neighbour = True
                        tmp.append(c)
                   if not neighbour  or c==hitList[last]:
                        first = tmp[0]
                        N = len(tmp)
                        hitvector.clear()
                        for aHit in tmp: hitvector.push_back( self.event.Digi_ScifiHits[hitDict[aHit]])
                        aCluster = ROOT.sndCluster(first,N,hitvector,self.scifiDet,False)
                        clusters.append(aCluster)
                        if c!=hitList[last]:
                             ncl+=1
                             tmp = [c]
                        elif not neighbour :   # save last channel
                            hitvector.clear()
                            hitvector.push_back( self.event.Digi_ScifiHits[hitDict[c]])
                            aCluster = ROOT.sndCluster(c,1,hitvector,self.scifiDet,False)
                            clusters.append(aCluster)
                   cprev = c
       return clusters

 def patternReco(self):
# very simple for the moment, take all scifi clusters
    trackCandidates = []
    hitlist = {}
    ScifiStations = {}
    for k in range(len(self.clusters)):
           hitlist[k] = self.clusters[k]
           ScifiStations[hitlist[k].GetFirst()//1000000] = 1
# take fired muonFilter bars if more than 2 SiPMs have fired
# nasty hack because of some wrong name of older data
    if self.event.GetBranch('Digi_MuFilterHits'):
         self.MuFilterHits = self.event.Digi_MuFilterHits
    elif self.ioman.GetInTree().GetBranch('Digi_MuFilterHit'):
         self.MuFilterHits =self.event.Digi_MuFilterHit
    nMin = 1
    MuFiPlanes = {}
    for k in range(self.MuFilterHits.GetEntries()):
         aHit = self.MuFilterHits[k]
         if not aHit.isValid(): continue
         detID = aHit.GetDetectorID()
         sy    = detID//10000
         l       = (detID%10000)//1000  # plane number
         bar = (detID%1000)
         nSiPMs = aHit.GetnSiPMs()
         nSides  = aHit.GetnSides()
         nFired = 0
         for i in range(nSides*nSiPMs):
              if aHit.GetSignal(i) > 0: nFired+=1
         if nMin > nFired: continue
         hitlist[k*1000] = self.MuFilterHits[k]
         MuFiPlanes[sy*100+l] = 1
    if (len(ScifiStations) == 5 or len(MuFiPlanes)>4) and len(hitlist)<20:
           trackCandidates.append(hitlist)
    return trackCandidates

 def fitTrack(self,hitlist):
# hitlist:  clusterID: [A,B] endpoints of scifiCluster
    hitPosLists={}
    trID = 0

    posM    = ROOT.TVector3(0, 0, 0.)
    momM = ROOT.TVector3(0,0,100.)  # default track with high momentum

# approximate covariance
    covM = ROOT.TMatrixDSym(6)
    res = self.sigmaScifi_spatial
    for  i in range(3):   covM[i][i] = res*res
    for  i in range(3,6): covM[i][i] = ROOT.TMath.Power(res / (4.*2.) / ROOT.TMath.Sqrt(3), 2)
    rep = ROOT.genfit.RKTrackRep(13)

# start state
    state = ROOT.genfit.MeasuredStateOnPlane(rep)
    rep.setPosMomCov(state, posM, momM, covM)

# create track
    seedState = ROOT.TVectorD(6)
    seedCov   = ROOT.TMatrixDSym(6)
    rep.get6DStateCov(state, seedState, seedCov)
    theTrack = ROOT.genfit.Track(rep, seedState, seedCov)

# make measurements sorted in z
    unSortedList = {}
    tmpList = {}
    A,B = ROOT.TVector3(),ROOT.TVector3()
    for k in hitlist:
        isSifi = False
        isUS  =False
        isDS  =False
        aCl = hitlist[k]
        if hasattr(aCl,"GetFirst"):
            isSifi = True
            detID = aCl.GetFirst()
            aCl.GetPosition(A,B)
        else:
            detID = aCl.GetDetectorID()
            if detID//10000 < 2: isUS  = True
            else: isDS  = True
            self.mufiDet.GetPosition(detID,A,B)
        distance = 0
        tmp = array('d',[A[0],A[1],A[2],B[0],B[1],B[2],distance])
        unSortedList[A[2]] = [ROOT.TVectorD(7,tmp),detID,k]
    sorted_z=list(unSortedList.keys())
    sorted_z.sort()
    for z in sorted_z:
        tp = ROOT.genfit.TrackPoint() # note how the point is told which track it belongs to
        hitCov = ROOT.TMatrixDSym(7)
        if isDS:      
              res = self.sigmaMufiDS_spatial
              maxDis = 1.0
        elif isUS:  
              res = self.sigmaMufiUS_spatial
              maxDis = 5.0
        else:         
              res = self.sigmaScifi_spatial
              maxDis = 0.1
        hitCov[6][6] = res*res
        measurement = ROOT.genfit.WireMeasurement(unSortedList[z][0],hitCov,1,6,tp) # the measurement is told which trackpoint it belongs to
        measurement.setMaxDistance(maxDis)
        measurement.setDetId(unSortedList[z][1])
        measurement.setHitId(unSortedList[z][2])
        tp.addRawMeasurement(measurement) # package measurement in the TrackPoint                                          
        theTrack.insertPoint(tp)  # add point to Track
    if not theTrack.checkConsistency():
        print("track not consistent")
        theTrack.Delete()
        return -2
# do the fit
    self.fitter.processTrack(theTrack) # processTrackWithRep(theTrack,rep,True)
    fitStatus   = theTrack.getFitStatus()
    if self.Debug: print("Fit result: converged chi2 Ndf",fitStatus.isFitConverged(),fitStatus.getChi2(),fitStatus.getNdf())
    if not fitStatus.isFitConverged() and 0>1:
        theTrack.Delete()
        return -1
    if self.Debug: 
        chi2 = fitStatus.getChi2()/(fitStatus.getNdf()+1E-15)
        fittedState = theTrack.getFittedState()
        P = fittedState.getMomMag()
        print("track fitted Ndf #Meas P",fitStatus.getNdf(), theTrack.getNumPointsWithMeasurement(),P)
        for p in theTrack.getPointsWithMeasurement():
            rawM = p.getRawMeasurement()
            info = p.getFitterInfo()
            if not info: continue
            detID = rawM.getDetId()
            print(detID,"weights",info.getWeights()[0],info.getWeights()[1],fitStatus.getNdf())
    return theTrack
