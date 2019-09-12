from __future__ import print_function
__author__ = 'Mikhail Hushchyn'

import numpy as np

def initialize(fgeo):
    pass


def execute(TaggerHits, debug=0):
    """
    Main function of muon tagger track pattern recognition.
    
    Parameters:
    -----------
    TaggerHits : list
        Muon tagger hits. TaggerHits = [{'digiHit': key, 
                                         'xtop': xtop, 'ytop': ytop, 'z': ztop, 
                                         'xbot': xbot, 'ybot': ybot, 
                                         'detID': detID}, {...}, ...]
    """
    
    track_hits = {}
    
    if debug:
        print("From MuonTaggerPatRec.py: ")
        print("Input hits: ")
        #print TaggerHits
        print([hit['digiHit'] for hit in TaggerHits])
        
    if len(TaggerHits) > 200:
        print("Too many hits.")
        return track_hits
        
    min_hits = 3
    max_shared_hits = 0
        
    # Split hits into ortogonal planes
    TaggerHits_x, TaggerHits_y = split_hits(TaggerHits)
    
    # PatRec in zx plane
    tracks_zx = pat_rec_plane(TaggerHits_x, coord='x', min_hits=min_hits, max_shared_hits=max_shared_hits)
    
    # PatRec in zy plane
    tracks_zy = pat_rec_plane(TaggerHits_y, coord='y', min_hits=min_hits, max_shared_hits=max_shared_hits)
    
    # Combine tracks
    track_combinations = combine_tracks(tracks_zx, tracks_zy)
    
    # Generate output
    for i_track in range(len(track_combinations)):
        
        atrack = track_combinations[i_track]
        
        if len(atrack['hits_x']) >= min_hits and len(atrack['hits_y']) >= min_hits:
            track_hits[i_track] = {}
            track_hits[i_track]['hits_x'] = sort_hits(atrack['hits_x'])
            track_hits[i_track]['hits_y'] = sort_hits(atrack['hits_y'])
        
        
    if debug:
        print("From MuonTaggerPatRec.py: ")
        print("tracks_zx: ")
        print(len(tracks_zx))
        print("tracks_zy: ")
        print(len(tracks_zy))
        print("track_combinations: ")
        print(len(track_combinations))
        print("Recognized tracks: ")
        for i_track in track_hits.keys():
            print("Track ", i_track)
            print("Hits_x: ", [hit['digiHit'] for hit in track_hits[i_track]['hits_x']])
            print("Hits_y: ", [hit['digiHit'] for hit in track_hits[i_track]['hits_y']])

    return track_hits



def finalize():
    pass
    
    
###################################################################################################


def split_hits(TaggerHits):

    TaggerHits_x = []
    TaggerHits_y = []
    for ahit in TaggerHits:
        if abs(ahit['xtop'] - ahit['xbot']) < 10:
            TaggerHits_x.append(ahit)
        if abs(ahit['ytop'] - ahit['ybot']) < 10:
            TaggerHits_y.append(ahit)
            
    return TaggerHits_x, TaggerHits_y


def pat_rec_plane(TaggerHits, coord='x', min_hits=3, max_shared_hits=2):

    long_tracks = []

    # Take 2 hits as a track seed
    for ahit1 in TaggerHits:
        for ahit2 in TaggerHits:

            if ahit1['z'] >= ahit2['z']:
                continue
            if ahit1['detID'] == ahit2['detID']:
                continue

            x1 = 0.5 * (ahit1[coord+'top'] + ahit1[coord+'bot'])
            x2 = 0.5 * (ahit2[coord+'top'] + ahit2[coord+'bot'])
            z1 = ahit1['z']
            z2 = ahit2['z']
            layer1 = ahit1['detID'] // 10000
            layer2 = ahit2['detID'] // 10000

            k_bin = 1. * (x2 - x1) / (z2 - z1)
            b_bin = x1 - k_bin * z1

            if abs(k_bin) > 1:
                continue

            atrack = {}
            atrack['hits_'+coord] = [ahit1, ahit2]
            atrack[coord+'_'+coord] = [x1, x2]
            atrack['z_'+coord] = [z1, z2]
            atrack['layer'] = [layer1, layer2]

            # Add new hits to the seed
            for ahit3 in TaggerHits:

                if ahit3['detID'] == ahit1['detID'] or ahit3['detID'] == ahit2['detID']:
                    continue

                x3 = 0.5 * (ahit3[coord+'top'] + ahit3[coord+'bot'])
                z3 = ahit3['z']
                layer3 = ahit3['detID'] // 10000

                if layer3 in atrack['layer']:
                    continue
                    #pass

                in_bin = hit_in_window(z3, x3, k_bin, b_bin, window_width=5.0)
                if in_bin:
                    atrack['hits_'+coord].append(ahit3)
                    atrack['z_'+coord].append(z3)
                    atrack[coord+'_'+coord].append(x3)
                    atrack['layer'].append(layer3)

            if len(atrack['hits_'+coord]) >= min_hits:
                long_tracks.append(atrack)
                
    # Reduce number of clones
    short_tracks = reduce_clones(long_tracks, coord, min_hits, max_shared_hits)
                
    # Fit tracks y12
    for atrack in short_tracks:
        [atrack['k_'+coord], atrack['b_'+coord]] = np.polyfit(atrack['z_'+coord], atrack[coord+'_'+coord], deg=1)
                
    return short_tracks
    
    
def combine_tracks(tracks_zx, tracks_zy):

    track_combinations = []
    for atrack_zx in tracks_zx:
        for atrack_zy in tracks_zy:
            atrack_comb = atrack_zx.copy()
            atrack_comb.update(atrack_zy)
            track_combinations.append(atrack_comb)
            
    return track_combinations
    
    
    
def reduce_clones(long_tracks, coord='x', min_hits=3, max_shared_hits=2):

    # Remove clones
    used_hits = []
    short_tracks = []
    n_hits = [len(atrack['hits_'+coord]) for atrack in long_tracks]

    for i_track in np.argsort(n_hits)[::-1]:

        atrack = long_tracks[i_track]
        n_shared_hits = 0

        for i_hit in range(len(atrack['hits_'+coord])):
            ahit = atrack['hits_'+coord][i_hit]
            if ahit['digiHit'] in used_hits: #digiHit
                n_shared_hits += 1

        if len(atrack['hits_'+coord]) >= min_hits and n_shared_hits <= max_shared_hits:
            short_tracks.append(atrack)
            for ahit in atrack['hits_'+coord]:
                used_hits.append(ahit['digiHit']) #digiHit
                
    return short_tracks


def hit_in_window(x, y, k_bin, b_bin, window_width=1.):
    """
        Counts hits in a bin of track parameter space (b, k).

        Parameters
        ---------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        k_bin : float
            Track parameter: y = k_bin * x + b_bin
        b_bin : float
            Track parameter: y = k_bin * x + b_bin

        Return
        ------
        track_inds : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        """


    y_approx = k_bin * x + b_bin

    flag = False
    if np.abs(y_approx - y) <= window_width:
        flag = True

    return flag


def sort_hits(hits):

    sorted_hits = []
    hits_z = [ahit['z'] for ahit in hits]
    sort_index = np.argsort(hits_z)
    for i_hit in sort_index:
        sorted_hits.append(hits[i_hit])
        
    return sorted_hits







