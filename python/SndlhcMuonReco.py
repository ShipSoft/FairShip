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

    def __init__(self, n_r, r_range, n_theta, theta_range, squaretheta = False, smooth = True) :

        self.n_r = n_r
        self.n_theta = n_theta

        self.r_range = r_range
        self.theta_range = theta_range

        self.smooth = smooth

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
        if self.smooth :
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

        print("Initializing muon reconstruction task!")
        self.lsOfGlobals  = ROOT.gROOT.GetListOfGlobals()
        self.scifiDet = self.lsOfGlobals.FindObject('Scifi')
        self.mufiDet = self.lsOfGlobals.FindObject('MuFilter')
        self.ioman = ROOT.FairRootManager.Instance()

        # Pass input data through to output.
        self.Passthrough()

        # Fetch digi hit collections.
        # Try the FairRoot way first
        self.MuFilterHits = self.ioman.GetObject("Digi_MuFilterHits")
        self.ScifiHits = self.ioman.GetObject("Digi_ScifiHits")

        # If that doesn't work, try using standard ROOT
        if self.MuFilterHits == None :
            warnings.warn("Digi_MuFilterHits not in branch list")
            self.MuFilterHits = self.ioman.GetInTree().Digi_MuFilterHits
        if self.ScifiHits == None :
            warnings.warn("Digi_ScigiHits not in branch list")
            self.ScifiHits = self.ioman.GetInTree().Digi_ScifiHits
        
        if self.MuFilterHits == None :
            raise RuntimeException("Digi_MuFilterHits not found in input file.")
        if self.ScifiHits == None :
            raise RuntimeException("Digi_ScifiHits not found in input file.")

        # Initialize hough transform
        # Reco parameters (these should be registered in the rtdb?):
        # Maximum absolute value of reconstructed angle (+/- 1 rad is the maximum angle to form a triplet in the SciFi)
        max_angle = 1.
        # Number of bins per Hough accumulator axis
        n_accumulator_rho = 1000
        n_accumulator_angle = 2500
        # Number of random throws per hit
        self.n_random = 5
        # MuFilter weight. Muon filter hits are thrown more times than scifi
        self.muon_weight = 100
        # Minimum number of planes hit in each of the downstream muon filter (if muon filter hits used) or scifi (if muon filter hits not used) views to try to reconstruct a muon
        self.min_planes_hit = 3

        # Maximum number of muons to find. To avoid spending too much time on events with lots of downstream activity.
        self.max_reco_muons = 5

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

        # How far away from Hough line hits will be assigned to the muon, for Kalman tracking
        self.tolerance = 0.

        # Which hits to use for track fitting. By default use both scifi and muon filter.
        self.hits_to_fit = "sfusds"
        # Which hits to use for triplet condition. By default use only downstream muon system hits.
        self.hits_for_triplet = "ds"

        # Initialize Hough transforms for both views:
        self.h_ZX = hough(n_accumulator_rho, [-80, 0], n_accumulator_angle, [-max_angle+np.pi/2., max_angle+np.pi/2.])
        self.h_ZY = hough(n_accumulator_rho, [0, 80], n_accumulator_angle, [-max_angle+np.pi/2., max_angle+np.pi/2.])

        # To keep temporary detector information
        self.a = ROOT.TVector3()
        self.b = ROOT.TVector3()

        # Now initialize output
        self.kalman_tracks = ROOT.TObjArray(self.max_reco_muons);
        self.ioman.Register("Reco_MuonTracks", self.ioman.GetFolderName(), self.kalman_tracks, ROOT.kTRUE);

        # Kalman filter stuff

        geoMat = ROOT.genfit.TGeoMaterialInterface()
        bfield = ROOT.genfit.ConstField(0, 0, 0)
        fM = ROOT.genfit.FieldManager.getInstance()
        fM.init(bfield)
        ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
        ROOT.genfit.MaterialEffects.getInstance().setNoEffects()
        
        self.kalman_fitter = ROOT.genfit.KalmanFitter()
        self.kalman_fitter.setMaxIterations(50)
        self.kalman_sigmaScifi_spatial = self.Scifi_dx / 12**0.5
        self.kalman_sigmaMufiUS_spatial = self.MuFilter_us_dy / 12**0.5
        self.kalman_sigmaMufiDS_spatial = self.MuFilter_ds_dy/ 12**0.5
        
        # Init() MUST return int
        return 0
    
    def SetTolerance(self, tolerance) :
        self.tolerance = tolerance

    def SetHitsToFit(self, hits_to_fit) :
        self.hits_to_fit = hits_to_fit
        
        # If only Scifi hits used, no need for accumulator smoothing.
        if hits_to_fit == "sf" :
            self.h_ZX.smooth = False
            self.h_ZY.smooth = False

    def SetHitsForTriplet(self, hits_for_triplet) :
        self.hits_for_triplet = hits_for_triplet

    def Passthrough(self) :
        T = self.ioman.GetInTree()
        
        for x in T.GetListOfBranches():
             obj_name = x.GetName()
             if self.ioman.GetObject(obj_name) == None :
                 continue
             self.ioman.Register(obj_name, self.ioman.GetFolderName(), self.ioman.GetObject(obj_name), ROOT.kTRUE) 

    def Exec(self, opt) :
        self.kalman_tracks.Clear()
        
        hit_collection = {"pos" : [[], [], []], 
                          "d" : [[], [], []], 
                          "vert" : [], 
                          "index" : [],
                          "system" : [],
                          "detectorID" : [],
                          "B" : [[], [], []]}

        if ("us" in self.hits_to_fit) or ("ds" in self.hits_to_fit) or ("ve" in self.hits_to_fit) :
            # Loop through muon filter hits
            for i_hit, muFilterHit in enumerate(self.MuFilterHits) :
                # Don't use veto for fitting
                if muFilterHit.GetSystem() == 1 :
                    if "ve" not in self.hits_to_fit :
                        continue
                elif muFilterHit.GetSystem() == 2 :
                    if "us" not in self.hits_to_fit :
                        continue
                elif muFilterHit.GetSystem() == 3 :
                    if "ds" not in self.hits_to_fit :
                        continue
                else :
                    print("WARNING! Unknown MuFilter system!!")
            
                self.mufiDet.GetPosition(muFilterHit.GetDetectorID(), self.a, self.b)
            
                hit_collection["pos"][0].append(self.a.X())
                hit_collection["pos"][1].append(self.a.Y())
                hit_collection["pos"][2].append(self.a.Z())
            
                hit_collection["B"][0].append(self.b.X())
                hit_collection["B"][1].append(self.b.Y())
                hit_collection["B"][2].append(self.b.Z())
            
                hit_collection["vert"].append(muFilterHit.isVertical())
                hit_collection["system"].append(muFilterHit.GetSystem())
            
                hit_collection["d"][0].append(self.MuFilter_ds_dx)
                hit_collection["d"][2].append(self.MuFilter_ds_dz)
            
                hit_collection["index"].append(i_hit)
                
                hit_collection["detectorID"].append(muFilterHit.GetDetectorID())
            
                # Downstream
                if muFilterHit.GetSystem() == 3 :
                    hit_collection["d"][1].append(self.MuFilter_ds_dx)
                # Upstream
                else :
                    hit_collection["d"][1].append(self.MuFilter_us_dy)
        
        if "sf" in self.hits_to_fit :
            # Loop through scifi hits
            for i_hit, scifiHit in enumerate(self.ScifiHits) :
                self.scifiDet.GetSiPMPosition(scifiHit.GetDetectorID(), self.a, self.b)
                hit_collection["pos"][0].append(self.a.X())
                hit_collection["pos"][1].append(self.a.Y())
                hit_collection["pos"][2].append(self.a.Z())
            
                hit_collection["B"][0].append(self.b.X())
                hit_collection["B"][1].append(self.b.Y())
                hit_collection["B"][2].append(self.b.Z())
            
                hit_collection["d"][0].append(self.Scifi_dx)
                hit_collection["d"][1].append(self.Scifi_dy)
                hit_collection["d"][2].append(self.Scifi_dz)
                
                hit_collection["vert"].append(scifiHit.isVertical())
                hit_collection["index"].append(i_hit)
                
                hit_collection["system"].append(0)
            
                hit_collection["detectorID"].append(scifiHit.GetDetectorID())
    
        # Make the hit collection numpy arrays.
        for key, item in hit_collection.items() :
            if key == 'vert' :
                this_dtype = np.bool
            elif key == "index" or key == "system" or key == "detectorID" :
                this_dtype = np.int32
            else :
                this_dtype = np.float
            hit_collection[key] = np.array(item, dtype = this_dtype)

        # Useful for later
        triplet_condition_system = []
        if "sf" in self.hits_for_triplet :
            triplet_condition_system.append(0)
        if "ve" in self.hits_for_triplet :
            triplet_condition_system.append(1)
        if "us" in self.hits_for_triplet :
            triplet_condition_system.append(2)
        if "ds" in self.hits_for_triplet :
            triplet_condition_system.append(3)

        # Reconstruct muons until there are not enough hits in downstream muon filter
        for i_muon in range(self.max_reco_muons) :
            triplet_hits_horizontal = np.logical_and( ~hit_collection["vert"],
                                                      np.isin(hit_collection["system"], triplet_condition_system) )
            triplet_hits_vertical = np.logical_and( hit_collection["vert"],
                                                    np.isin(hit_collection["system"], triplet_condition_system) )

            n_planes_ZY = numPlanesHit(hit_collection["system"][triplet_hits_horizontal],
                                       hit_collection["detectorID"][triplet_hits_horizontal])
            if n_planes_ZY < self.min_planes_hit :
                break

            n_planes_ZX = numPlanesHit(hit_collection["system"][triplet_hits_vertical],
                                       hit_collection["detectorID"][triplet_hits_vertical])
            if n_planes_ZX < self.min_planes_hit :
                break

            # Get hits in hough transform format
            muon_hits_horizontal = np.logical_and( ~hit_collection["vert"],
                                                   np.isin(hit_collection["system"], [1, 2, 3]))
            muon_hits_vertical = np.logical_and( hit_collection["vert"],
                                                 np.isin(hit_collection["system"], [1, 2, 3]))
            scifi_hits_horizontal = np.logical_and( ~hit_collection["vert"],
                                                    np.isin(hit_collection["system"], [0]))
            scifi_hits_vertical = np.logical_and( hit_collection["vert"],
                                                  np.isin(hit_collection["system"], [0]))


            ZY = np.dstack([np.concatenate([np.tile(hit_collection["pos"][2][muon_hits_horizontal], self.muon_weight),
                                            hit_collection["pos"][2][scifi_hits_horizontal]]),
                            np.concatenate([np.tile(hit_collection["pos"][1][muon_hits_horizontal], self.muon_weight),
                                            hit_collection["pos"][1][scifi_hits_horizontal]])])[0]

            d_ZY = np.dstack([np.concatenate([np.tile(hit_collection["d"][2][muon_hits_horizontal], self.muon_weight),
                                              hit_collection["d"][2][scifi_hits_horizontal]]),
                              np.concatenate([np.tile(hit_collection["d"][1][muon_hits_horizontal], self.muon_weight),
                                              hit_collection["d"][1][scifi_hits_horizontal]])])[0]

            ZX = np.dstack([np.concatenate([np.tile(hit_collection["pos"][2][muon_hits_vertical], self.muon_weight),
                                            hit_collection["pos"][2][scifi_hits_vertical]]),
                            np.concatenate([np.tile(hit_collection["pos"][0][muon_hits_vertical], self.muon_weight),
                                            hit_collection["pos"][0][scifi_hits_vertical]])])[0]

            d_ZX = np.dstack([np.concatenate([np.tile(hit_collection["d"][2][muon_hits_vertical], self.muon_weight),
                                              hit_collection["d"][2][scifi_hits_vertical]]),
                              np.concatenate([np.tile(hit_collection["d"][0][muon_hits_vertical], self.muon_weight),
                                              hit_collection["d"][0][scifi_hits_vertical]])])[0]

            ZY_hough = self.h_ZY.fit_randomize(ZY, d_ZY, self.n_random)
            ZX_hough = self.h_ZX.fit_randomize(ZX, d_ZX, self.n_random)

            # Check if track intersects minimum number of hits in each plane.
            track_hits_for_triplet_ZY = hit_finder(ZY_hough[0], ZY_hough[1], 
                                                   np.dstack([hit_collection["pos"][2][triplet_hits_horizontal],
                                                              hit_collection["pos"][1][triplet_hits_horizontal]]),
                                                   np.dstack([hit_collection["d"][2][triplet_hits_horizontal],
                                                              hit_collection["d"][1][triplet_hits_horizontal]]), tol = self.tolerance)

            track_hits_for_triplet_ZX = hit_finder(ZX_hough[0], ZX_hough[1], 
                                                   np.dstack([hit_collection["pos"][2][triplet_hits_vertical],
                                                              hit_collection["pos"][0][triplet_hits_vertical]]),
                                                   np.dstack([hit_collection["d"][2][triplet_hits_vertical],
                                                              hit_collection["d"][0][triplet_hits_vertical]]), tol = self.tolerance)
                                                   
            n_planes_hit_ZY = numPlanesHit(hit_collection["system"][triplet_hits_horizontal][track_hits_for_triplet_ZY],
                                           hit_collection["detectorID"][triplet_hits_horizontal][track_hits_for_triplet_ZY])
            if n_planes_hit_ZY < self.min_planes_hit :
                break
            n_planes_hit_ZX = numPlanesHit(hit_collection["system"][triplet_hits_vertical][track_hits_for_triplet_ZX],
                                           hit_collection["detectorID"][triplet_hits_vertical][track_hits_for_triplet_ZX])
            if n_planes_hit_ZX < self.min_planes_hit :
                break

#                print("Found {0} downstream ZX planes associated to muon track".format(n_planes_ds_ZX))
#                print("Found {0} downstream ZY planes associated to muon track".format(n_planes_ds_ZY))
            
            # This time with all the hits, not just triplet condition.
            track_hits_ZY = hit_finder(ZY_hough[0], ZY_hough[1], 
                                       np.dstack([hit_collection["pos"][2][~hit_collection["vert"]], 
                                                  hit_collection["pos"][1][~hit_collection["vert"]]]), 
                                       np.dstack([hit_collection["d"][2][~hit_collection["vert"]],
                                                  hit_collection["d"][1][~hit_collection["vert"]]]), tol = self.tolerance)

            track_hits_ZX = hit_finder(ZX_hough[0], ZX_hough[1], 
                                       np.dstack([hit_collection["pos"][2][hit_collection["vert"]], 
                                                  hit_collection["pos"][0][hit_collection["vert"]]]), 
                                       np.dstack([hit_collection["d"][2][hit_collection["vert"]], 
                                                  hit_collection["d"][0][hit_collection["vert"]]]), tol = self.tolerance)

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
            
            theTrack = ROOT.genfit.Track(rep, seedState, seedCov)
            
            # Sort measurements in Z
            hit_z = np.concatenate([hit_collection["pos"][2][hit_collection["vert"]][track_hits_ZX],
                                    hit_collection["pos"][2][~hit_collection["vert"]][track_hits_ZY]])

            hit_A0 = np.concatenate([hit_collection["pos"][0][hit_collection["vert"]][track_hits_ZX],
                                     hit_collection["pos"][0][~hit_collection["vert"]][track_hits_ZY]])

            hit_A1 = np.concatenate([hit_collection["pos"][1][hit_collection["vert"]][track_hits_ZX],
                                     hit_collection["pos"][1][~hit_collection["vert"]][track_hits_ZY]])
            
            hit_B0 = np.concatenate([hit_collection["B"][0][hit_collection["vert"]][track_hits_ZX],
                                     hit_collection["B"][0][~hit_collection["vert"]][track_hits_ZY]])

            hit_B1 = np.concatenate([hit_collection["B"][1][hit_collection["vert"]][track_hits_ZX],
                                     hit_collection["B"][1][~hit_collection["vert"]][track_hits_ZY]])
            
            hit_B2 = np.concatenate([hit_collection["B"][2][hit_collection["vert"]][track_hits_ZX],
                                     hit_collection["B"][2][~hit_collection["vert"]][track_hits_ZY]])
            
            hit_detid = np.concatenate([hit_collection["detectorID"][hit_collection["vert"]][track_hits_ZX],
                                        hit_collection["detectorID"][~hit_collection["vert"]][track_hits_ZY]])

            kalman_spatial_sigma = np.concatenate([hit_collection["d"][0][hit_collection["vert"]][track_hits_ZX] / 12**0.5,
                                                   hit_collection["d"][1][~hit_collection["vert"]][track_hits_ZY] / 12**0.5])

            # Maximum distance. Use (d_xy/2**2 + d_z/2**2)**0.5
            kalman_max_dis = np.concatenate([((hit_collection["d"][0][hit_collection["vert"]][track_hits_ZX]/2.)**2 +
                                              (hit_collection["d"][2][hit_collection["vert"]][track_hits_ZX]/2.)**2)**0.5,
                                             ((hit_collection["d"][1][~hit_collection["vert"]][track_hits_ZY]/2.)**2 +
                                              (hit_collection["d"][2][~hit_collection["vert"]][track_hits_ZY]/2.)**2)**0.5])
            
            hitID = 0 # Does it matter? We don't have a global hit ID.
            
            for i_z_sorted in hit_z.argsort() :
                tp = ROOT.genfit.TrackPoint()
                hitCov = ROOT.TMatrixDSym(7)
                hitCov[6][6] = kalman_spatial_sigma[i_z_sorted]**2
                
                measurement = ROOT.genfit.WireMeasurement(ROOT.TVectorD(7, array('d', [hit_A0[i_z_sorted],
                                                                                       hit_A1[i_z_sorted],
                                                                                       hit_z[i_z_sorted],
                                                                                       hit_B0[i_z_sorted],
                                                                                       hit_B1[i_z_sorted],
                                                                                       hit_B2[i_z_sorted],
                                                                                       0.])),
                                                          hitCov,
                                                          1, # detid?
                                                          6, # hitid?
                                                          tp)
                
                measurement.setMaxDistance(kalman_max_dis[i_z_sorted])
                measurement.setDetId(int(hit_detid[i_z_sorted]))
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
            self.kalman_tracks.Add(theTrack)
            

            # Remove track hits and try to find an additional track
            # Find array index to be removed
            index_to_remove_ZX = np.where(np.in1d(hit_collection["detectorID"], hit_collection["detectorID"][hit_collection["vert"]][track_hits_ZX]))[0]
            index_to_remove_ZY = np.where(np.in1d(hit_collection["detectorID"], hit_collection["detectorID"][~hit_collection["vert"]][track_hits_ZY]))[0]

            index_to_remove = np.concatenate([index_to_remove_ZX, index_to_remove_ZY])
            
            # Remove dictionary entries 
            print("BEFORE")
            print(hit_collection["detectorID"])
            for key in hit_collection.keys() :
                if len(hit_collection[key].shape) == 1 :
                    hit_collection[key] = np.delete(hit_collection[key], index_to_remove)
                elif len(hit_collection[key].shape) == 2 :
                    hit_collection[key] = np.delete(hit_collection[key], index_to_remove, axis = 1)
                else :
                    raise Exception("Wrong number of dimensions found when deleting hits in iterative muon identification algorithm.")
            print("AFTER")
            print(hit_collection["detectorID"])


    def FinishTask(self) :
        pass
