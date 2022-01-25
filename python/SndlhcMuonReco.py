import ROOT
import numpy as np
import scipy.ndimage
import warnings

def hit_finder(slope, intercept, box_centers, box_ds) :
    """ Finds hits intersected by Hough line """

    # First check if track at center of box is within box limits
    d = np.abs(box_centers[0,:,1] - (box_centers[0,:,0]*slope + intercept))
    center_in_box = d < box_ds[0,:,1]/2.

    # Now check if, assuming line is not in box at box center, the slope is large enough for line to clip the box at corner
    clips_corner = np.abs(slope) > np.abs((d - box_ds[0,:,1]/2.)/box_ds[0,:,0]/2.)

    # If either of these is true, line goes through hit:
    hit_mask = np.logical_or(center_in_box, clips_corner)

    # Return indices
    return np.where(hit_mask)[0]

class hough() :
    """ Hough transform implementation """

    def __init__(self, n_r, r_range, n_theta, theta_range, squaretheta = False) :

        self.n_r = n_r
        self.n_theta = n_theta

        self.r_range = r_range
        self.theta_range = theta_range

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
        # Minimum number of hits in each of the downstream muon filter views to try to reconstruct a muon
        self.min_hits = 3

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
        
        # Initialize Hough transforms for both views:
        self.h_ZX = hough(n, [-80, 0], n, [-max_angle+np.pi/2., max_angle+np.pi/2.], False)
        self.h_ZY = hough(n, [0, 80], n, [-max_angle+np.pi/2., max_angle+np.pi/2.], False)

        # Now initialize output
        self.muon_tracks = ROOT.TClonesArray("sndRecoTrack", 10)
        ioman.Register("Reco_MuonTracks", "", self.muon_tracks, ROOT.kTRUE);

        # To keep temporary detector information
        self.a = ROOT.TVector3()
        self.b = ROOT.TVector3()

        return 0
        
    def Exec(self, opt) :
        self.muon_tracks.Clear()

        # Read hits
        # For downstream muon filter hits
        mu_ds = {"pos" : [[], [], []], 
                 "d" : [[], [], []], 
                 "vert" : [], 
                 "index" : [],
                 "system" : [],
                 "detectorID" : []}

        # For upstream muon filter hits
        mu_us = {"pos" : [[], [], []], 
                 "d" : [[], [], []], 
                 "vert" : [],
                 "index" : [],
                 "system" : [],
                 "detectorID" : []}

        # For scifi hits
        scifi = {"pos" : [[], [], []], 
                 "d" : [[], [], []], 
                 "vert" : [],
                 "index" : [], 
                 "system" : [],
                 "detectorID" : []}
        
        # Loop through hits
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
        
        for i_hit, scifiHit in enumerate(self.ScifiHits) :
            self.scifiDet.GetSiPMPosition(scifiHit.GetDetectorID(), self.a, self.b)
            scifi["pos"][0].append(self.a.X())
            scifi["pos"][1].append(self.a.Y())
            scifi["pos"][2].append(self.a.Z())

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

            vertical_ds_hits = mu_ds["vert"].sum()
            if vertical_ds_hits < self.min_hits :
                break
            
            horizontal_ds_hits = len(mu_ds["vert"]) - vertical_ds_hits
            if horizontal_ds_hits < self.min_hits :
                break
                
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
            print("Found {0} downstream ZX hits associated to muon track".format(len(track_hits_ds_ZX)))
            if len(track_hits_ds_ZX) < self.min_hits :
                break
            
            track_hits_ds_ZY = hit_finder(ZY_hough[0], ZY_hough[1], 
                                          np.dstack([mu_ds["pos"][2][~mu_ds["vert"]], 
                                                     mu_ds["pos"][1][~mu_ds["vert"]]]), 
                                          np.dstack([mu_ds["d"][2][~mu_ds["vert"]],
                                                     mu_ds["d"][1][~mu_ds["vert"]]]))

            print("Found {0} downstream ZY hits associated to muon track".format(len(track_hits_ds_ZY)))
            if len(track_hits_ds_ZY) < self.min_hits :
                break

            print("Muon found!")
            track_hits_us_ZY = hit_finder(ZY_hough[0], ZY_hough[1], 
                                          np.dstack([mu_us["pos"][2][~mu_us["vert"]],
                                                     mu_us["pos"][1][~mu_us["vert"]]]), 
                                          np.dstack([mu_us["d"][2][~mu_us["vert"]], 
                                                     mu_us["d"][1][~mu_us["vert"]]]))
            
            track_hits_sf_ZX = hit_finder(ZX_hough[0], ZX_hough[1], 
                                          np.dstack([scifi["pos"][2][scifi["vert"]], 
                                                     scifi["pos"][0][scifi["vert"]]]), 
                                          np.dstack([scifi["d"][2][scifi["vert"]], 
                                                     scifi["d"][0][scifi["vert"]]]))
            
            track_hits_sf_ZY = hit_finder(ZY_hough[0], ZY_hough[1], 
                                          np.dstack([scifi["pos"][2][~scifi["vert"]], 
                                                     scifi["pos"][1][~scifi["vert"]]]), 
                                          np.dstack([scifi["d"][2][~scifi["vert"]], 
                                                     scifi["d"][1][~scifi["vert"]]]))
            
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
