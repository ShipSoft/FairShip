import ROOT
import numpy as np
import scipy.ndimage

def hit_finder( slope, intercept, box_centers, box_ds) :
    """ Finds hits intersected by Hough line """
    # First check if track at center of box is within box limits
    d = np.abs(box_centers[:,1] - (box_centers[:,0]*slope + intercept))
    center_in_box = d < box_ds[:,1]/2.
    
    # Now check if, assuming line is not in box at box center, the slope is large enough for line to clip the box at corner
    clips_corner = np.abs(slope) > np.abs((d - box_ds[:,1]/2.)/box_ds[:,0]/2.)
    
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

        print("Starting randomized fit. Number of hits: {0}".format(len(hit_collection)))

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
            
        # Find hits that match track
#        z0 = np.min(hit_collection[:,0])
#        z1 = np.max(hit_collection[:,0])
        
#        y0 = fit[0]*z0 + fit[1]
#        y1 = fit[0]*z1 + fit[1]
        
#        l_fit = np.array([[z0, y0], [z1, y1]])

        hit_indices = hit_finder(fit[0], fit[1], hit_collection, hit_d)

#        for i in range(len(hit_collection)) :
#            if lineseg_intersects_box(l_fit, [hit_collection[i,0], hit_collection[i,1]], [hit_d[i,0], hit_d[i,1]]) :
#                hit_indices.append(i)

        # Find track start and track end
        if len(hit_indices) :
            z_min = np.min(hit_collection[hit_indices][:,0])
            z_max = np.max(hit_collection[hit_indices][:,0])
        else :
            z_min = -1
            z_max = -1
            success = False
        return (fit[0], fit[1], np.array([[z_min, fit[0]*z_min + fit[1]], [z_max,fit[0]*z_max + fit[1]]]), hit_indices, success)

class MuonReco(ROOT.FairTask) :
    " Muon reconstruction "
    def InitTasl(self, event) :
        lsOfGlobals  = ROOT.gROOT.GetListOfGlobals()
        self.scifiDet = lsOfGlobals.FindObject('Scifi')
        self.mufiDet = lsOfGlobals.FindObject('MuFilter')
        
        
        
        
    def FinishEvent(self, event) :
        pass
    def ExecuteTask(self, option = '') :
        pass
