from __future__ import print_function
__author__ = 'Mikhail Hushchyn'

import numpy as np
from sklearn.linear_model import LinearRegression


def initialize(fgeo):
    pass



def execute(muon_tagger_track_hits, drifttubes_track_hits, debug=0):
    
    track_hits = {}
    i_track = 0
    
    for i_muon_tagger_track in muon_tagger_track_hits.keys():
    
        one_muon_tagger_track = muon_tagger_track_hits[i_muon_tagger_track]
        
        for i_drifttubes_track in drifttubes_track_hits.keys():
            
            one_drifttubes_track = drifttubes_track_hits[i_drifttubes_track]
            
            # Get linear model quality
            rmse = linear_fit_in_zx_plane(one_muon_tagger_track, one_drifttubes_track, debug)
            
            # Create tracks combination
            if rmse < 2.0:
                atrack = {}
                atrack['drifttubes_track'] = one_drifttubes_track
                atrack['muon_tagger_track'] = one_muon_tagger_track
                track_hits[i_track] = atrack
                i_track += 1
            
            if debug:
                print('rmse: ', rmse)
                print('i_muon_tagger_track: ', i_muon_tagger_track)
                print('i_drifttubes_track: ', i_drifttubes_track)
            
    
    return track_hits



def finalize():
    pass
    
    
###################################################################################################
from sklearn.metrics import mean_squared_error


def linear_fit_in_zx_plane(muon_tagger_track, drifttubes_track, debug):
    
    # Collect hit coordinates
    z_coords = []
    x_coords = []
    
    for ahit in muon_tagger_track['hits_x']:
        z_coords.append([ahit['z']])
        x_coords.append(ahit['xtop'])
        
    for ahit in drifttubes_track['34']:
        z_coords.append([ahit['z']])
        x_coords.append(ahit['xtop'])
        
    if debug:
        print('z_coords:', z_coords)
        print('x_coords:', x_coords)
        
    # Fit linear regression model
    reg = LinearRegression()
    reg.fit(z_coords, x_coords)
    
    # Make prediction
    x_coords_pred = reg.predict(z_coords)
    
    # Calculate model's quality metric
    rmse = np.sqrt(mean_squared_error(x_coords, x_coords_pred))
    
    
    return rmse





