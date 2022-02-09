import ROOT
import numpy as np
import scipy.ndimage
import warnings
from array import array

def hit_finder(slope, intercept, box_centers, box_ds, tol = 0.) :
    """ Finds hits intersected by Hough line """
    
    # First check if track at center of box is within box limits
    d = np.abs(box_centers[0,:,1] - (box_centers[0,:,0]*slope + intercept))
    center_in_box = d < (box_ds[0,:,1]+tol)/2.

    # Now check if, assuming line is not in box at box center, the slope is large enough for line to clip the box at corner
    clips_corner = np.abs(slope) > np.abs((d - (box_ds[0,:,1]+tol)/2.)/(box_ds[0,:,0]+tol)/2.)
    
    # If either of these is true, line goes through hit:
    hit_mask = np.logical_or(center_in_box, clips_corner)

    # Return indices
    return np.where(hit_mask)[0]

class hough() :
    """ Hough transform implementation """

    def __init__(self, n_r, r_range, n_theta, theta_range, tolerance = 0., squaretheta = False) :

        self.n_r = n_r
        self.n_theta = n_theta

        self.r_range = r_range
        self.theta_range = theta_range

        self.tolerance = tolerance

        self.r_bins = np.linspace(self.r_range[0], self.r_range[1], n_r)
        if not squaretheta :
            self.theta_bins = np.linspace(self.theta_range[0], self.theta_range[1], n_theta)
        else :
            self.theta_bins = np.linspace(np.sign(self.theta_range[0])*(self.theta_range[0]**0.5), np.sign(self.theta_range[1])*(self.theta_range[1]**0.5), n_theta)
            self.theta_bins = np.sign(self.theta_bins)*np.square(self.theta_bins)
        
        self.cos_thetas = np.cos(self.theta_bins)
        self.sin_thetas = np.sin(self.theta_bins)
        
        self.theta_i = np.array(list(range(n_theta)))

    def fit(self, hit_collection, draw = False, weights = None) :

        self.accumulator = np.zeros((self.n_r, self.n_theta))
        for i_hit, hit in enumerate(hit_collection) :
            hit_r = hit[0]*self.cos_thetas + hit[1]*self.sin_thetas
            out_of_range = np.logical_and(hit_r > self.r_range[0], hit_r < self.r_range[1]) 
            hit_r_i = np.floor((hit_r[out_of_range] - self.r_range[0])/(self.r_range[1] - self.r_range[0])*self.n_r).astype(np.int)

            if weights is not None :
                self.accumulator[hit_r_i, self.theta_i[out_of_range]] += weights[i_hit]
            else :
                self.accumulator[hit_r_i, self.theta_i[out_of_range]] += 1

        # Smooth accumulator
        self.accumulator = scipy.ndimage.gaussian_filter(self.accumulator, 3)

        # This might be useful for debugging, but leave out for now.
        if draw :
            pass
#            plt.figure()
#            plt.imshow(self.accumulator, origin = "lower", extent = [self.theta_range[0], self.theta_range[-1], self.r_range[0], self.r_range[-1]], aspect = "auto")
#            plt.xlabel(r"$\theta$ [rad]")
#            plt.ylabel("r [cm]")
#            plt.tight_layout()
        
        i_max = np.unravel_index(self.accumulator.argmax(), self.accumulator.shape)

        found_r = self.r_bins[i_max[0]]
        found_theta = self.theta_bins[i_max[1]]

        slope = -1./np.tan(found_theta)
        intercept = found_r/np.sin(found_theta)
    
        return (slope, intercept)

    def fit_randomize(self, hit_collection, hit_d, n_random, draw = False, weights = None) :
        success = True
        if not len(hit_collection) :
            return (-1, -1, [[],[]], [], False)

        # Randomize hits
        if (n_random > 0) :
            random_hit_collection = []
            for i_random in range(n_random) :
                random_hits = np.random.uniform(size = hit_collection.shape) - 0.5
                random_hits *= hit_d
                random_hits += hit_collection
                random_hit_collection.append(random_hits)

            random_hit_collection = np.concatenate(random_hit_collection)
            if weights is not None :
                weights = np.tile(weights, n_random)

            fit = self.fit(random_hit_collection, draw, weights)
        else :
            fit = self.fit(hit_collection, draw, weights)

        return fit

def numPlanesHit(systems, detector_ids) :
    scifi_stations = []
    mufi_ds_planes = []
    mufi_us_planes = []

    scifi_stations.append( detector_ids[systems == 0]//1000000 )
    mufi_ds_planes.append( (detector_ids[systems == 3]%10000)//1000 )
    mufi_us_planes.append( (detector_ids[systems == 2]%10000)//1000 )

    return len(np.unique(scifi_stations)) + len(np.unique(mufi_ds_planes)) + len(np.unique(mufi_us_planes))
    
class MuonReco(ROOT.FairTask) :
    " Muon reconstruction "
    def Init(self) :

        print("Initializing task!")
        self.lsOfGlobals  = ROOT.gROOT.GetListOfGlobals()
        self.scifiDet = self.lsOfGlobals.FindObject('Scifi')
        self.mufiDet = self.lsOfGlobals.FindObject('MuFilter')
        ioman = ROOT.FairRootManager.Instance()

        # Fetch digi hit collections.
        # Try the FairRoot way first
        self.MuFilterHits = ioman.GetObject("Digi_MuFilterHits")
        self.ScifiHits = ioman.GetObject("Digi_ScifiHits")

        # If that doesn't work, try using standard ROOT
        if self.MuFilterHits == None :
            warnings.warn("Digi_MuFilterHits not in branch list")
            self.MuFilterHits = ioman.GetInTree().Digi_MuFilterHits
        if self.ScifiHits == None :
            warnings.warn("Digi_ScigiHits not in branch list")
            self.ScifiHits = ioman.GetInTree().Digi_ScifiHits
        
        if self.MuFilterHits == None :
            raise RuntimeException("Digi_MuFilterHits not found in input file.")
        if self.ScifiHits == None :
            raise RuntimeException("Digi_ScifiHits not found in input file.")

        # Initialize hough transform
        # Reco parameters (these should be registered in the rtdb?):
        # Maximum absolute value of reconstructed angle
        max_angle = np.pi*0.1
        # Number of bins per Hough accumulator axis
        n = 1000
        # Number of random throws per hit
        self.n_random = 5
        # MuFilter weight. Muon filter hits are thrown more times than scifi
        self.muon_weight = 100
        # Minimum number of planes hit in each of the downstream muon filter (if muon filter hits used) or scifi (if muon filter hits not used) views to try to reconstruct a muon
        self.min_planes_hit = 3

        # Maximum number of muons to find. To avoid spending too much time on events with lots of downstream activity.
        self.max_reco_muons = 5

        # How far away from Hough line hits will be assigned to the muon, for Kalman tracking
        self.tolerance = 1.

        # Which hits to use. By default use both scifi and muon filter.
        self.use_scifi = True
        self.use_mufi = True

        # Get sensor dimensions from geometry
        self.MuFilter_ds_dx = self.mufiDet.GetConfParF("MuFilter/DownstreamBarY") # Assume y dimensions in vertical bars are the same as x dimensions in horizontal bars.
        self.MuFilter_ds_dy = self.mufiDet.GetConfParF("MuFilter/DownstreamBarY") # Assume y dimensions in vertical bars are the same as x dimensions in horizontal bars.
        self.MuFilter_ds_dz = self.mufiDet.GetConfParF("MuFilter/DownstreamBarZ")

        self.MuFilter_us_dx = self.mufiDet.GetConfParF("MuFilter/UpstreamBarX")
        self.MuFilter_us_dy = self.mufiDet.GetConfParF("MuFilter/UpstreamBarY")
        self.MuFilter_us_dz = self.mufiDet.GetConfParF("MuFilter/UpstreamBarZ")

        self.Scifi_dx = self.scifiDet.GetConfParF("Scifi/channel_width")
        self.Scifi_dy = self.scifiDet.GetConfParF("Scifi/channel_width")
        self.Scifi_dz = self.scifiDet.GetConfParF("Scifi/epoxymat_z") # From Scifi.cxx This is the variable used to define the z dimension of SiPM channels, so seems like the right dimension to use.
        
        # Initialize Hough transforms for both views:
        self.h_ZX = hough(n, [-80, 0], n, [-max_angle+np.pi/2., max_angle+np.pi/2.], tolerance = self.tolerance, squaretheta = False)
        self.h_ZY = hough(n, [0, 80], n, [-max_angle+np.pi/2., max_angle+np.pi/2.], tolerance = self.tolerance, squaretheta = False)

        # To keep temporary detector information
        self.a = ROOT.TVector3()
        self.b = ROOT.TVector3()

        # Now initialize output
        self.muon_tracks = ROOT.TClonesArray("sndRecoTrack", self.max_reco_muons)
        ioman.Register("Reco_MuonTracks", "", self.muon_tracks, ROOT.kTRUE);

#        self.kalman_tracks = ROOT.TClonesArray(ROOT.genfit.Track().ClassName(), self.max_reco_muons);
        self.kalman_tracks = ROOT.TObjArray(self.max_reco_muons);
        ioman.Register("Reco_KalmanTracks", "", self.kalman_tracks, ROOT.kTRUE);

        # Kalman filter stuff

        geoMat = ROOT.genfit.TGeoMaterialInterface()
        bfield = ROOT.genfit.ConstField(0, 0, 0)
        fM = ROOT.genfit.FieldManager.getInstance()
        fM.init(bfield)
        ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
        ROOT.genfit.MaterialEffects.getInstance().setNoEffects()
        
        self.kalman_fitter = ROOT.genfit.KalmanFitter()
        self.kalman_fitter.setMaxIterations(50)
        self.kalman_sigmaScifi_spatial = self.scifiDet.GetConfParF("Scifi/channel_width") / 12**0.5
        self.kalman_sigmaMufiUS_spatial = self.mufiDet.GetConfParF("MuFilter/UpstreamBarY") / 12**0.5
        self.kalman_sigmaMufiDS_spatial = self.mufiDet.GetConfParF("MuFilter/DownstreamBarY") / 12**0.5
        
        # Init() MUST return int
        return 0
    
    def SetTolerance(self, tolerance) :
        self.tolerance = tolerance

    def SetUseSciFi(self, use_scifi) :
        self.use_scifi = use_scifi

    def SetUseMuFi(self, use_mufi) :
        self.use_mufi = use_mufi

    def Exec(self, opt) :
        self.muon_tracks.Clear()
        self.kalman_tracks.Clear()
        
        # Read hits
        # For downstream muon filter hits
        mu_ds = {"pos" : [[], [], []], 
                 "d" : [[], [], []], 
                 "vert" : [], 
                 "index" : [],
                 "system" : [],
                 "detectorID" : [],
                 "B" : [[], [], []]}

        # For upstream muon filter hits
        mu_us = {"pos" : [[], [], []], 
                 "d" : [[], [], []], 
                 "vert" : [],
                 "index" : [],
                 "system" : [],
                 "detectorID" : [],
                 "B" : [[], [], []]}

        # For scifi hits
        scifi = {"pos" : [[], [], []], 
                 "d" : [[], [], []], 
                 "vert" : [],
                 "index" : [], 
                 "system" : [],
                 "detectorID" : [],
                 "B" : [[], [], []]}
        
        if self.use_mufi :
            # Loop through muon filter hits
            for i_hit, muFilterHit in enumerate(self.MuFilterHits) :
                
                # Don't use veto for fitting
                if muFilterHit.GetSystem() == 1 :
                    continue
                elif muFilterHit.GetSystem() == 2 :
                    mu = mu_us
                elif muFilterHit.GetSystem() == 3 :
                    mu = mu_ds
                else :
                    print("WARNING! Unknown MuFilter system!!")
            
                self.mufiDet.GetPosition(muFilterHit.GetDetectorID(), self.a, self.b)
            
                mu["pos"][0].append(self.a.X())
                mu["pos"][1].append(self.a.Y())
                mu["pos"][2].append(self.a.Z())
            
                mu["B"][0].append(self.b.X())
                mu["B"][1].append(self.b.Y())
                mu["B"][2].append(self.b.Z())
            
                mu["vert"].append(muFilterHit.isVertical())
                mu["system"].append(muFilterHit.GetSystem())
            
                mu["d"][0].append(self.MuFilter_ds_dx)
                mu["d"][2].append(self.MuFilter_ds_dz)
            
                mu["index"].append(i_hit)
                
                mu["detectorID"].append(muFilterHit.GetDetectorID())
            
                # Downstream
                if muFilterHit.GetSystem() == 3 :
                    mu["d"][1].append(self.MuFilter_ds_dx)
                # Upstream
                else :
                    mu["d"][1].append(self.MuFilter_us_dy)
        
        if self.use_scifi :
            # Loop through scifi hits
            for i_hit, scifiHit in enumerate(self.ScifiHits) :
                self.scifiDet.GetSiPMPosition(scifiHit.GetDetectorID(), self.a, self.b)
                scifi["pos"][0].append(self.a.X())
                scifi["pos"][1].append(self.a.Y())
                scifi["pos"][2].append(self.a.Z())
            
                scifi["B"][0].append(self.b.X())
                scifi["B"][1].append(self.b.Y())
                scifi["B"][2].append(self.b.Z())
            
                scifi["d"][0].append(self.Scifi_dx)
                scifi["d"][1].append(self.Scifi_dy)
                scifi["d"][2].append(self.Scifi_dz)
                
                scifi["vert"].append(scifiHit.isVertical())
                scifi["index"].append(i_hit)
                
                scifi["system"].append(0)
            
                scifi["detectorID"].append(scifiHit.GetDetectorID())
    
        # Make the hit collections numpy arrays.
        for hit_collection in [mu_ds, mu_us, scifi] :
            for key, item in hit_collection.items() :
                if key == 'vert' :
                    this_dtype = np.bool
                elif key == "index" or key == "system" or key == "detectorID" :
                    this_dtype = np.int32
                else :
                    this_dtype = np.float
                hit_collection[key] = np.array(item, dtype = this_dtype)

        # Reconstruct muons until there are not enough hits in downstream muon filter
        for i_muon in range(self.max_reco_muons) :

            # Minimum plane conditions
            if self.use_mufi :
                n_planes_ds_ZX = numPlanesHit(mu_ds["system"][mu_ds["vert"]], mu_ds["detectorID"][mu_ds["vert"]])
                if n_planes_ds_ZX < self.min_planes_hit :
                    break
                n_planes_ds_ZY = numPlanesHit(mu_ds["system"][~mu_ds["vert"]], mu_ds["detectorID"][~mu_ds["vert"]])
                if n_planes_ds_ZY < self.min_planes_hit :
                    break
            

            if (not self.use_mufi) and self.use_scifi :
                print("ABOUT TO GET NPLANES")
                n_planes_sf_ZX = numPlanesHit(scifi["system"][scifi["vert"]], scifi["detectorID"][scifi["vert"]])
                if n_planes_sf_ZX < self.min_planes_hit :
                    break
                n_planes_sf_ZY = numPlanesHit(scifi["system"][~scifi["vert"]], scifi["detectorID"][~scifi["vert"]])
                if n_planes_sf_ZY < self.min_planes_hit :
                    break
            elif self.use_mufi :
                pass
            else :
                raise RuntimeException("Invalid triplet condition. Need at least Scifi or Muon filter hits enabled")


  
            print("Finding muon {0}".format(i_muon))    
            
            # Get hits in hough transform format
            ZX = np.dstack([np.concatenate([np.tile(mu_ds["pos"][2][mu_ds["vert"]], self.muon_weight), 
                                            np.tile(mu_us["pos"][2][mu_us["vert"]], self.muon_weight), 
                                            scifi["pos"][2][scifi["vert"]]]), 
                            np.concatenate([np.tile(mu_ds["pos"][0][mu_ds["vert"]], self.muon_weight),
                                            np.tile(mu_us["pos"][0][mu_us["vert"]], self.muon_weight), 
                                            scifi["pos"][0][scifi["vert"]]])])[0]

            d_ZX = np.dstack([np.concatenate([np.tile(mu_ds["d"][2][mu_ds["vert"]], self.muon_weight), 
                                              np.tile(mu_us["d"][2][mu_us["vert"]], self.muon_weight), 
                                              scifi["d"][2][scifi["vert"]]]), 
                              np.concatenate([np.tile(mu_ds["d"][0][mu_ds["vert"]], self.muon_weight), 
                                              np.tile(mu_us["d"][0][mu_us["vert"]], self.muon_weight), 
                                              scifi["d"][0][scifi["vert"]]])])[0]

            ZY = np.dstack([np.concatenate([np.tile(mu_ds["pos"][2][~mu_ds["vert"]], self.muon_weight), 
                                            np.tile(mu_us["pos"][2][~mu_us["vert"]], self.muon_weight), 
                                            scifi["pos"][2][~scifi["vert"]]]), 
                            np.concatenate([np.tile(mu_ds["pos"][1][~mu_ds["vert"]], self.muon_weight), 
                                            np.tile(mu_us["pos"][1][~mu_us["vert"]], self.muon_weight), 
                                            scifi["pos"][1][~scifi["vert"]]])])[0]

            d_ZY = np.dstack([np.concatenate([np.tile(mu_ds["d"][2][~mu_ds["vert"]], self.muon_weight), 
                                              np.tile(mu_us["d"][2][~mu_us["vert"]], self.muon_weight), 
                                              scifi["d"][2][~scifi["vert"]]]), 
                              np.concatenate([np.tile(mu_ds["d"][1][~mu_ds["vert"]], self.muon_weight), 
                                              np.tile(mu_us["d"][1][~mu_us["vert"]], self.muon_weight), 
                                              scifi["d"][1][~scifi["vert"]]])])[0]

            ZX_hough = self.h_ZX.fit_randomize(ZX, d_ZX, self.n_random)
            ZY_hough = self.h_ZY.fit_randomize(ZY, d_ZY, self.n_random)
            
            # Check if track intersects minimum number of hits in each plane.
            track_hits_ds_ZX = hit_finder(ZX_hough[0], ZX_hough[1], 
                                          np.dstack([mu_ds["pos"][2][mu_ds["vert"]], 
                                                     mu_ds["pos"][0][mu_ds["vert"]]]), 
                                          np.dstack([mu_ds["d"][2][mu_ds["vert"]], 
                                                     mu_ds["d"][0][mu_ds["vert"]]]))

            track_hits_ds_ZY = hit_finder(ZY_hough[0], ZY_hough[1], 
                                          np.dstack([mu_ds["pos"][2][~mu_ds["vert"]], 
                                                     mu_ds["pos"][1][~mu_ds["vert"]]]), 
                                          np.dstack([mu_ds["d"][2][~mu_ds["vert"]],
                                                     mu_ds["d"][1][~mu_ds["vert"]]]))

            # Triplet conditions. At least three unique planes in MuFi if use_mufi or scifi if not use_mufi
            if self.use_mufi :
                n_planes_ds_ZX = numPlanesHit(mu_ds["system"][track_hits_ds_ZX], mu_ds["detectorID"][track_hits_ds_ZX])
                if n_planes_ds_ZX < self.min_planes_hit :
                    break
                n_planes_ds_ZY = numPlanesHit(mu_ds["system"][track_hits_ds_ZY], mu_ds["detectorID"][track_hits_ds_ZY])
                if n_planes_ds_ZY < self.min_planes_hit :
                    break
                

            print("Found {0} downstream ZX hits associated to muon track".format(len(track_hits_ds_ZX)))
#            if len(track_hits_ds_ZX) < self.min_planes_hit :
#                break
            
            print("Found {0} downstream ZY hits associated to muon track".format(len(track_hits_ds_ZY)))
#            if len(track_hits_ds_ZY) < self.min_planes_hit :
#                break

            
            # This time with non-zero tolerance, for kalman filter
            track_hits_ds_ZX = hit_finder(ZX_hough[0], ZX_hough[1], 
                                          np.dstack([mu_ds["pos"][2][mu_ds["vert"]], 
                                                     mu_ds["pos"][0][mu_ds["vert"]]]), 
                                          np.dstack([mu_ds["d"][2][mu_ds["vert"]], 
                                                     mu_ds["d"][0][mu_ds["vert"]]]), tol = self.tolerance)

            track_hits_ds_ZY = hit_finder(ZY_hough[0], ZY_hough[1], 
                                          np.dstack([mu_ds["pos"][2][~mu_ds["vert"]], 
                                                     mu_ds["pos"][1][~mu_ds["vert"]]]), 
                                          np.dstack([mu_ds["d"][2][~mu_ds["vert"]],
                                                     mu_ds["d"][1][~mu_ds["vert"]]]), tol = self.tolerance)



            track_hits_us_ZY = hit_finder(ZY_hough[0], ZY_hough[1], 
                                          np.dstack([mu_us["pos"][2][~mu_us["vert"]],
                                                     mu_us["pos"][1][~mu_us["vert"]]]), 
                                          np.dstack([mu_us["d"][2][~mu_us["vert"]], 
                                                     mu_us["d"][1][~mu_us["vert"]]]), tol = self.tolerance)
            
            track_hits_sf_ZX = hit_finder(ZX_hough[0], ZX_hough[1], 
                                          np.dstack([scifi["pos"][2][scifi["vert"]], 
                                                     scifi["pos"][0][scifi["vert"]]]), 
                                          np.dstack([scifi["d"][2][scifi["vert"]], 
                                                     scifi["d"][0][scifi["vert"]]]), tol = self.tolerance)
            
            track_hits_sf_ZY = hit_finder(ZY_hough[0], ZY_hough[1], 
                                          np.dstack([scifi["pos"][2][~scifi["vert"]], 
                                                     scifi["pos"][1][~scifi["vert"]]]), 
                                          np.dstack([scifi["d"][2][~scifi["vert"]], 
                                                     scifi["d"][1][~scifi["vert"]]]), tol = self.tolerance)
            
            # Triplet conditions. At least three unique planes in MuFi if use_mufi or scifi if not use_mufi
            if (not self.use_mufi) and self.use_scifi :
                print("ABOUT TO GET NPLANES")
                n_planes_sf_ZX = numPlanesHit(scifi["system"][track_hits_sf_ZX], scifi["detectorID"][track_hits_sf_ZX])
                if n_planes_sf_ZX < self.min_planes_hit :
                    break
                n_planes_sf_ZY = numPlanesHit(scifi["system"][track_hits_sf_ZY], scifi["detectorID"][track_hits_sf_ZY])
                if n_planes_sf_ZY < self.min_planes_hit :
                    break
            elif self.use_mufi :
                pass
            else :
                raise RuntimeException("Invalid triplet condition. Need at least Scifi or Muon filter hits enabled")

            print("Muon found!")

            # Get hit detectorIDs and add to reco track collection
            hit_detectorIDs = np.concatenate([mu_ds["detectorID"][mu_ds["vert"]][track_hits_ds_ZX],
                                              mu_ds["detectorID"][~mu_ds["vert"]][track_hits_ds_ZY],
                                              mu_us["detectorID"][~mu_us["vert"]][track_hits_us_ZY],
                                              scifi["detectorID"][scifi["vert"]][track_hits_sf_ZX],
                                              scifi["detectorID"][~scifi["vert"]][track_hits_sf_ZY]])

            # Find start and stop position
            hit_z = np.concatenate([mu_ds["pos"][2][mu_ds["vert"]][track_hits_ds_ZX],
                                    mu_ds["pos"][2][~mu_ds["vert"]][track_hits_ds_ZY],
                                    mu_us["pos"][2][~mu_us["vert"]][track_hits_us_ZY],
                                    scifi["pos"][2][scifi["vert"]][track_hits_sf_ZX],
                                    scifi["pos"][2][~scifi["vert"]][track_hits_sf_ZY]])
            
            min_z = np.min(hit_z)
            max_z = np.max(hit_z)

            min_x = ZX_hough[0]*min_z + ZX_hough[1]
            max_x = ZX_hough[0]*max_z + ZX_hough[1]

            min_y = ZY_hough[0]*min_z + ZY_hough[1]
            max_y = ZY_hough[0]*max_z + ZY_hough[1]

            # Save track
            this_track = self.muon_tracks.ConstructedAt(i_muon)
            this_track.setStart(ROOT.TVector3(min_x, min_y, min_z))
            this_track.setStop(ROOT.TVector3(max_x, max_y, max_z))
            this_track.setHits(hit_detectorIDs)
            this_track.setHitsLoose(hit_detectorIDs)
            
            # Onto Kalman fitter (based on SndlhcTracking.py)
            posM    = ROOT.TVector3(0, 0, 0.)
            momM = ROOT.TVector3(0,0,100.)  # default track with high momentum

            # approximate covariance
            covM = ROOT.TMatrixDSym(6)
            res = self.kalman_sigmaScifi_spatial
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
#            theTrack = self.kalman_tracks.ConstructedAt(i_muon)
#            theTrack.addTrackRep(rep)
#            theTrack.setStateSeed(seedState)
#            theTrack.setCovSeed(seedCov)
            
            theTrack = ROOT.genfit.Track(rep, seedState, seedCov)
            
            # Sort measurements in Z
            # Start with Scifi
            hit_z_scifi = np.concatenate([scifi["pos"][2][scifi["vert"]][track_hits_sf_ZX],
                                          scifi["pos"][2][~scifi["vert"]][track_hits_sf_ZY]])
            hit_A0_scifi = np.concatenate([scifi["pos"][0][scifi["vert"]][track_hits_sf_ZX],
                                           scifi["pos"][0][~scifi["vert"]][track_hits_sf_ZY]])
            hit_A1_scifi = np.concatenate([scifi["pos"][1][scifi["vert"]][track_hits_sf_ZX],
                                           scifi["pos"][1][~scifi["vert"]][track_hits_sf_ZY]])
            hit_B0_scifi = np.concatenate([scifi["B"][0][scifi["vert"]][track_hits_sf_ZX],
                                           scifi["B"][0][~scifi["vert"]][track_hits_sf_ZY]])
            hit_B1_scifi = np.concatenate([scifi["B"][1][scifi["vert"]][track_hits_sf_ZX],
                                           scifi["B"][1][~scifi["vert"]][track_hits_sf_ZY]])
            hit_B2_scifi = np.concatenate([scifi["B"][2][scifi["vert"]][track_hits_sf_ZX],
                                           scifi["B"][2][~scifi["vert"]][track_hits_sf_ZY]])
            hit_detid_scifi = np.concatenate([scifi["detectorID"][scifi["vert"]][track_hits_sf_ZX],
                                              scifi["detectorID"][~scifi["vert"]][track_hits_sf_ZY]])
            hitID = 0 # Does it matter? We don't have a global hit ID.
            for i_z_sorted in hit_z_scifi.argsort() :
                tp = ROOT.genfit.TrackPoint()
                hitCov = ROOT.TMatrixDSym(7)
                maxDis = 0.1
                hitCov[6][6] = self.kalman_sigmaScifi_spatial**2
                measurement = ROOT.genfit.WireMeasurement(ROOT.TVectorD(7, array('d', [hit_A0_scifi[i_z_sorted],
                                                                                       hit_A1_scifi[i_z_sorted],
                                                                                       hit_z_scifi[i_z_sorted],
                                                                                       hit_B0_scifi[i_z_sorted],
                                                                                       hit_B1_scifi[i_z_sorted],
                                                                                       hit_B2_scifi[i_z_sorted],
                                                                                       0.])),
                                                          hitCov,
                                                          1, # detid?
                                                          6, # hitid?
                                                          tp)
                
                measurement.setMaxDistance(maxDis)
                measurement.setDetId(int(hit_detid_scifi[i_z_sorted]))
                measurement.setHitId(int(hitID))
                hitID += 1
                tp.addRawMeasurement(measurement)
                theTrack.insertPoint(tp)

            # Repeat for upstream
            hit_z_mu_us = mu_us["pos"][2][~mu_us["vert"]][track_hits_us_ZY]
            hit_A0_mu_us = mu_us["pos"][0][~mu_us["vert"]][track_hits_us_ZY]
            hit_A1_mu_us = mu_us["pos"][1][~mu_us["vert"]][track_hits_us_ZY]
            hit_B0_mu_us = mu_us["B"][0][~mu_us["vert"]][track_hits_us_ZY]
            hit_B1_mu_us = mu_us["B"][1][~mu_us["vert"]][track_hits_us_ZY]
            hit_B2_mu_us = mu_us["B"][2][~mu_us["vert"]][track_hits_us_ZY]
            hit_detid_mu_us = mu_us["detectorID"][~mu_us["vert"]][track_hits_us_ZY]
            
            for i_z_sorted in hit_z_mu_us.argsort() :
                tp = ROOT.genfit.TrackPoint()
                hitCov = ROOT.TMatrixDSym(7)
                maxDis = 5.0
                hitCov[6][6] = self.kalman_sigmaMufiUS_spatial**2
                measurement = ROOT.genfit.WireMeasurement(ROOT.TVectorD(7, array('d', [hit_A0_mu_us[i_z_sorted],
                                                                                       hit_A1_mu_us[i_z_sorted],
                                                                                       hit_z_mu_us[i_z_sorted],
                                                                                       hit_B0_mu_us[i_z_sorted],
                                                                                       hit_B1_mu_us[i_z_sorted],
                                                                                       hit_B2_mu_us[i_z_sorted],
                                                                                       0.])),
                                                          hitCov,
                                                          1, # detid?
                                                          6, # hitid?
                                                          tp)
                measurement.setMaxDistance(maxDis)
                measurement.setDetId(int(hit_detid_mu_us[i_z_sorted]))
                measurement.setHitId(int(hitID))
                hitID += 1
                tp.addRawMeasurement(measurement)
                theTrack.insertPoint(tp)

            # And for downstream
            hit_z_mu_ds = np.concatenate([mu_ds["pos"][2][mu_ds["vert"]][track_hits_ds_ZX],
                                          mu_ds["pos"][2][~mu_ds["vert"]][track_hits_ds_ZY]])
            hit_A0_mu_ds = np.concatenate([mu_ds["pos"][0][mu_ds["vert"]][track_hits_ds_ZX],
                                           mu_ds["pos"][0][~mu_ds["vert"]][track_hits_ds_ZY]])
            hit_A1_mu_ds = np.concatenate([mu_ds["pos"][1][mu_ds["vert"]][track_hits_ds_ZX],
                                           mu_ds["pos"][1][~mu_ds["vert"]][track_hits_ds_ZY]])
            hit_B0_mu_ds = np.concatenate([mu_ds["B"][0][mu_ds["vert"]][track_hits_ds_ZX],
                                           mu_ds["B"][0][~mu_ds["vert"]][track_hits_ds_ZY]])
            hit_B1_mu_ds = np.concatenate([mu_ds["B"][1][mu_ds["vert"]][track_hits_ds_ZX],
                                           mu_ds["B"][1][~mu_ds["vert"]][track_hits_ds_ZY]])
            hit_B2_mu_ds = np.concatenate([mu_ds["B"][2][mu_ds["vert"]][track_hits_ds_ZX],
                                           mu_ds["B"][2][~mu_ds["vert"]][track_hits_ds_ZY]])
            hit_detid_mu_ds = np.concatenate([mu_ds["detectorID"][mu_ds["vert"]][track_hits_ds_ZX],
                                              mu_ds["detectorID"][~mu_ds["vert"]][track_hits_ds_ZY]])
            
            for i_z_sorted in hit_z_mu_ds.argsort() :
                tp = ROOT.genfit.TrackPoint()
                hitCov = ROOT.TMatrixDSym(7)
                maxDis = 1.0
                hitCov[6][6] = self.kalman_sigmaMufiDS_spatial**2
                measurement = ROOT.genfit.WireMeasurement(ROOT.TVectorD(7, array('d', [hit_A0_mu_ds[i_z_sorted],
                                                                                       hit_A1_mu_ds[i_z_sorted],
                                                                                       hit_z_mu_ds[i_z_sorted],
                                                                                       hit_B0_mu_ds[i_z_sorted],
                                                                                       hit_B1_mu_ds[i_z_sorted],
                                                                                       hit_B2_mu_ds[i_z_sorted],
                                                                                       0.])),
                                                          hitCov,
                                                          1, # detid?
                                                          6, # hitid?
                                                          tp)
                measurement.setMaxDistance(maxDis)
                measurement.setDetId(int(hit_detid_mu_ds[i_z_sorted]))
                measurement.setHitId(int(hitID))
                hitID += 1
                tp.addRawMeasurement(measurement)
                theTrack.insertPoint(tp)

            if not theTrack.checkConsistency():
                theTrack.Delete()
                raise RuntimeException("Kalman fitter track consistency check failed.")

            # do the fit
            self.kalman_fitter.processTrack(theTrack) # processTrackWithRep(theTrack,rep,True)

            fitStatus = theTrack.getFitStatus()
            if not fitStatus.isFitConverged() and 0>1:
                theTrack.Delete()
                raise RuntimeException("Kalman fit did not converge.")
            
            # Now save the track!
#            savedTrack = self.kalman_tracks.ConstructedAt(i_muon)
#            savedTrack.swap(theTrack)

#            self.kalman_tracks[i_muon] = theTrack
            self.kalman_tracks.Add(theTrack)

            # Remove track hits and try to find an additional track
            # Find array index to be removed
            index_ZX = np.where(np.in1d(mu_ds["detectorID"], mu_ds["detectorID"][mu_ds["vert"]][track_hits_ds_ZX]))[0]
            index_ZY = np.where(np.in1d(mu_ds["detectorID"], mu_ds["detectorID"][~mu_ds["vert"]][track_hits_ds_ZY]))[0]
            index_to_remove = np.concatenate( [index_ZX, index_ZY] )

            # Remove dictionary entries
            for key in mu_ds.keys() :
                if len(mu_ds[key].shape) == 1 :
                    mu_ds[key] = np.delete(mu_ds[key], index_to_remove)
                elif len(mu_ds[key].shape) == 2 :
                    mu_ds[key] = np.delete(mu_ds[key], index_to_remove, axis = 1)
                else :
                    raise Exception("Wrong number of dimensions found when deleting hits in iterative muon identification algorithm.")

    def FinishTask(self) :
        self.muon_tracks.Delete()
