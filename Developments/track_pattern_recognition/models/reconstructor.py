__author__ = 'Oleg Alenkin', 'Mikhail Hushchyn'

import numpy as np
from sklearn.linear_model import RANSACRegressor
from copy import copy

def projection(hits, dists2w, y_resolution=1., z_magnet=3070.):
    
    density = np.zeros(int(1200 * y_resolution))
    ids = np.zeros([int(1200 * y_resolution), len(hits)])
    
    for i in range(len(hits)-1):
        y1, z1 = hits[i]
        d2w = dists2w[i]
        
        inc_ind = ((((hits[i+1:, 0]+dists2w[i+1:]-y1-d2w)/(hits[i+1:, 1]-z1)*(z_magnet-z1)+y1+d2w)\
                   +600) * y_resolution).astype(np.int32)
        mask = (inc_ind < 1200 * y_resolution) & (inc_ind >= 0)
        density[inc_ind[mask]] += 1
        ids[inc_ind[mask], np.arange(i+1, len(hits))[mask]] = 1
        ids[inc_ind[mask], i * np.ones(mask.sum()).astype(np.int32)] = 1
        
        inc_ind = ((((hits[i+1:, 0]+dists2w[i+1:]-y1+d2w)/(hits[i+1:, 1]-z1)*(z_magnet-z1)+y1-d2w)\
                   +600) * y_resolution).astype(np.int32)
        mask = (inc_ind < 1200 * y_resolution) & (inc_ind >= 0)
        density[inc_ind[mask]] += 1
        ids[inc_ind[mask], np.arange(i+1, len(hits))[mask]] = 1
        ids[inc_ind[mask], i * np.ones(mask.sum()).astype(np.int32)] = 1
        
        inc_ind = ((((hits[i+1:, 0]-dists2w[i+1:]-y1-d2w)/(hits[i+1:, 1]-z1)*(z_magnet-z1)+y1+d2w)\
                   +600) * y_resolution).astype(np.int32)
        mask = (inc_ind < 1200 * y_resolution) & (inc_ind >= 0)
        density[inc_ind[mask]] += 1
        ids[inc_ind[mask], np.arange(i+1, len(hits))[mask]] = 1
        ids[inc_ind[mask], i * np.ones(mask.sum()).astype(np.int32)] = 1
        
        inc_ind = ((((hits[i+1:, 0]-dists2w[i+1:]-y1+d2w)/(hits[i+1:, 1]-z1)*(z_magnet-z1)+y1-d2w)\
                   +600) * y_resolution).astype(np.int32)
        mask = (inc_ind < 1200 * y_resolution) & (inc_ind >= 0)
        density[inc_ind[mask]] += 1
        ids[inc_ind[mask], np.arange(i+1, len(hits))[mask]] = 1
        ids[inc_ind[mask], i * np.ones(mask.sum()).astype(np.int32)] = 1
    
    return density, ids.astype(bool)

#def projection(hits, y_resolution=1., z_magnet=3070.):
#    
#    density = np.zeros(int(1200 * y_resolution))
#    ids = np.zeros([int(1200 * y_resolution), len(hits)])
#    
#    for i in range(len(hits)-1):
#        y1, z1 = hits[i]
#        inc_ind = (((hits[i+1:, 0]-y1) / (hits[i+1:, 1]-z1) * (z_magnet - z1) + y1) + ids.shape[0] * 0.5).astype(np.int32)
#        mask = (inc_ind < 1200 * y_resolution) & (inc_ind >= 0)
#        density[inc_ind[mask]] += 1
#        ids[inc_ind[mask], np.arange(i+1, len(hits))[mask]] += 1
#        ids[inc_ind[mask], i * np.ones(mask.sum()).astype(np.int32)] += 1
#    
#    return density, ids>1

def hits2params(hits):
    
    l = len(hits)
    ys = hits[:, 0]
    zs = hits[:, 1]
    k, b = np.polyfit(zs, ys, 1)
    
    return k, b

def RANSACTrack_ext(hits, dist2wire, residual_threshold=0.5, z_magnet=3070.):
    
    xs = hits[:, 0].reshape(-1, 1)
    zs = hits[:, 1].reshape(-1, 1) - z_magnet
    dist2wire = dist2wire.reshape(-1, 1)
    mask = zs < 0
    zs_1 = np.hstack([zs * mask, zs * ~mask])
    zs = np.vstack([zs_1, zs_1])
    ransac = RANSACRegressor(residual_threshold=residual_threshold)
    ransac.fit(zs, np.vstack([xs+dist2wire, xs-dist2wire]))
    k_b, k_a = ransac.estimator_.coef_[0]
    b = ransac.estimator_.intercept_[0]
    b_b = b - z_magnet * k_b
    b_a = b - z_magnet * k_a
    inliers = ransac.inlier_mask_[:len(zs)/2] + ransac.inlier_mask_[len(zs)/2:]

    return k_b, k_a, b_b, b_a, inliers

def RANSACTrack(hits, residual_threshold=0.5):
    
    xs = hits[:, 0].reshape(-1, 1)
    zs = hits[:, 1].reshape(-1, 1)
    ransac = RANSACRegressor(residual_threshold=residual_threshold)
    ransac.fit(zs, xs)
    k = ransac.estimator_.coef_[0, 0]
    b = ransac.estimator_.intercept_[0]
    inliers = ransac.inlier_mask_

    return k, b, inliers

def get_x_points(points_x, k, b):
    
    Wx1 = points_x[:, 0]
    Wx2 = points_x[:, 1]
    Wy1 = points_x[:, 2]
    Wy2 = points_x[:, 3]
    Wz = points_x[:, 4]
    y = k * Wz + b
    
    x = Wx1 * (1. - (Wy1 - y) / (Wy1 - Wy2)) + Wx2 * ((Wy1 - y) / (Wy1 - Wy2))
    return np.vstack([x, Wz]).T

class Reconstructor(object):
    
    def __init__(self, z_magnet=3070., y_resolution=1., residual_threshold_x=2., residual_threshold_y=0.8):
        
        self.y_resolution = y_resolution
        self.z_magnet = z_magnet
        self.labels_ = None
        self.tracks_params_ = None
        self.rtx = residual_threshold_x
        self.rty = residual_threshold_y
        
    def fit(self, event):
        
        mask_before = event[:, 1] < 3
        mask_after = event[:, 1] > 2
        mask_y = (event[:, 0]==0) + (event[:, 0]==3)
        event_y = event[mask_y]
        mask_y_b = event_y[:, 0] < 3
        points_y = event_y[:, [4, 6]]
        points_y_before = event_y[mask_y_b][:, [4, 6]]
        points_y_after = event_y[~mask_y_b][:, [4, 6]]
        dist2wire_y_before = event_y[mask_y_b][:, 7]
        dist2wire_y_after = event_y[~mask_y_b][:, 7]

        mask_x = ~mask_y
        event_x = event[mask_x]
        mask_x_b = event_x[:, 1] < 3
        points_x_before = event_x[mask_x_b][:, 2:]
        points_x_after = event_x[~mask_x_b][:, 2:]
        
        # track 1
        density_b, ids_b_0 = projection(points_y_before, dist2wire_y_before, y_resolution=self.y_resolution)
        density_a, ids_a_0 = projection(points_y_after, dist2wire_y_after, y_resolution=self.y_resolution)
        density = density_b * density_a
        
        #track_y_b_0 = ids_b_0[np.argmax(density)]
        #track_y_a_0 = ids_a_0[np.argmax(density)]
        #k_y_b_0, b_y_b_0, inliers_y_before = RANSACTrack(points_y_before[track_y_b_0], residual_threshold=self.rty)
        #k_y_a_0, b_y_a_0, inliers_y_after = RANSACTrack(points_y_after[track_y_a_0], residual_threshold=self.rty)
        #track_y_b_0[track_y_b_0] = inliers_y_before
        #track_y_a_0[track_y_a_0] = inliers_y_after
        
        track_y_b_0 = ids_b_0[np.argmax(density)]
        track_y_a_0 = ids_a_0[np.argmax(density)]
        points_y_0 = np.vstack([points_y_before[track_y_b_0], points_y_after[track_y_a_0]])
        dist2wire_y_0 = np.hstack([dist2wire_y_before[track_y_b_0], dist2wire_y_after[track_y_a_0]])
        k_y_b_0, k_y_a_0, b_y_b_0, b_y_a_0, inliers = RANSACTrack_ext(points_y_0, dist2wire_y_0, residual_threshold=self.rty)
        inliers_before = inliers[:np.sum(track_y_b_0)]
        inliers_after = inliers[np.sum(track_y_b_0):]
        track_y_b_0[track_y_b_0] = inliers_before
        track_y_a_0[track_y_a_0] = inliers_after
        
        points_x_before_0 = get_x_points(points_x_before, k_y_b_0, b_y_b_0)
        l_b = len(points_x_before)
        points_x_after_0 = get_x_points(points_x_after, k_y_a_0, b_y_a_0)
        points_x_0 = np.vstack([points_x_before_0, points_x_after_0])
        
        mask_x_t_0 = (points_x_0[:, 0] > -250) & (points_x_0[:, 0] < 250)

        k_x_0, b_x_0, inliers_x = RANSACTrack(points_x_0[mask_x_t_0], residual_threshold=self.rtx)
        mask_x_t_0[mask_x_t_0] = inliers_x
        
        mask_y_before = copy(mask_y)
        mask_y_before[mask_y_before] = mask_y_b
        mask_y_after = copy(mask_y)
        mask_y_after[mask_y_after] = ~mask_y_b
        mask_x_before = copy(mask_x)
        mask_x_before[mask_x_before] = mask_x_b
        mask_x_after = copy(mask_x)
        mask_x_after[mask_x_after] = ~mask_x_b
        
        used_0 = np.zeros(len(event))
        used_0[mask_y_before] = track_y_b_0
        used_0[mask_y_after] = track_y_a_0
        used_0[mask_x_before] = mask_x_t_0[:l_b]
        used_0[mask_x_after] = mask_x_t_0[l_b:]
        used_0 = used_0.astype(bool)
        
        #track 2
        density_b, ids_b_1 = projection(points_y_before[~track_y_b_0], dist2wire_y_before[~track_y_b_0],\
                                        y_resolution=self.y_resolution)
        density_a, ids_a_1 = projection(points_y_after[~track_y_a_0], dist2wire_y_after[~track_y_a_0],\
                                        y_resolution=self.y_resolution)
        density = density_b * density_a

        #track_y_b_1 = ~track_y_b_0
        #track_y_b_1[track_y_b_1] = ids_b_1[np.argmax(density)]
        #track_y_a_1 = ~track_y_a_0
        #track_y_a_1[track_y_a_1] = ids_a_1[np.argmax(density)]
        #k_y_b_1, b_y_b_1, inliers_y_before = RANSACTrack(points_y_before[track_y_b_1], residual_threshold=self.rty)
        #k_y_a_1, b_y_a_1, inliers_y_after = RANSACTrack(points_y_after[track_y_a_1], residual_threshold=self.rty)
        #track_y_b_1[track_y_b_1] = inliers_y_before
        #track_y_a_1[track_y_a_1] = inliers_y_after
        
        track_y_b_1 = ~track_y_b_0
        track_y_b_1[track_y_b_1] = ids_b_1[np.argmax(density)]
        track_y_a_1 = ~track_y_a_0
        track_y_a_1[track_y_a_1] = ids_a_1[np.argmax(density)]
        points_y_1 = np.vstack([points_y_before[track_y_b_1], points_y_after[track_y_a_1]])
        dist2wire_y_1 = np.hstack([dist2wire_y_before[track_y_b_1], dist2wire_y_after[track_y_a_1]])
        k_y_b_1, k_y_a_1, b_y_b_1, b_y_a_1, inliers = RANSACTrack_ext(points_y_1, dist2wire_y_1, residual_threshold=self.rty)
        inliers_before = inliers[:np.sum(track_y_b_1)]
        inliers_after = inliers[np.sum(track_y_b_1):]
        track_y_b_1[track_y_b_1] = inliers_before
        track_y_a_1[track_y_a_1] = inliers_after
        
        points_x_before_1 = get_x_points(points_x_before, k_y_b_1, b_y_b_1)
        points_x_after_1 = get_x_points(points_x_after, k_y_a_1, b_y_a_1)
        points_x_1 = np.vstack([points_x_before_1, points_x_after_1])
        
        mask_x_t_1 = (points_x_1[:, 0] > -250) & (points_x_1[:, 0] < 250)
        mask_x_t_1 = mask_x_t_1 & (~mask_x_t_0)
        
        k_x_1, b_x_1, inliers_x = RANSACTrack(points_x_1[mask_x_t_1], residual_threshold=self.rtx)
        mask_x_t_1[mask_x_t_1] = inliers_x
        
        used_1 = np.zeros(len(event))
        used_1[mask_y_before] = track_y_b_1
        used_1[mask_y_after] = track_y_a_1
        used_1[mask_x_before] = mask_x_t_1[:l_b]
        used_1[mask_x_after] = mask_x_t_1[l_b:]
        used_1 = used_1.astype(bool)
        
        #labeling
        indexes = np.arange(len(event))
        labels = np.ones(len(event)) * -1
        labels[used_0] = 0
        labels[used_1] = 1
        self.labels_ = [labels[mask_before], labels[mask_after]]
        self.mask_before = mask_before
        self.mask_after = mask_after
        self.labels = labels

        atrack0 = indexes[used_0]
        atrack1 = indexes[used_1]

        self.track_inds_ = []
        track_params12 = []
        track_params34 = []

        if len(atrack0) >= 2:
            self.track_inds_.append(atrack0)
            track_params12.append([[k_y_b_0, b_y_b_0], [k_x_0, b_x_0]])
            track_params34.append([[k_y_a_0, b_y_a_0], [k_x_0, b_x_0]])
        if len(atrack1) >= 2:
            self.track_inds_.append(atrack1)
            track_params12.append([[k_y_b_1, b_y_b_1], [k_x_1, b_x_1]])
            track_params34.append([[k_y_a_1, b_y_a_1], [k_x_1, b_x_1]])
        
        #define params
        self.tracks_params_ = np.array([track_params12, track_params34])