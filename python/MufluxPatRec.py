__author__ = 'Mikhail Hushchyn'

import numpy as np

# Globals
ReconstructibleMCTracks = []
theTracks = []


def initialize(fgeo):
    pass


def execute(SmearedHits, TaggerHits, withNTaggerHits, withDist2Wire, debug=0):
    """
    Main function of track pattern recognition.
    
    Parameters:
    -----------
    SmearedHits : list
        Smeared hits. SmearedHits = [{'digiHit': key, 
                                      'xtop': xtop, 'ytop': ytop, 'z': ztop, 
                                      'xbot': xbot, 'ybot': ybot, 
                                      'dist': dist2wire, 'detID': detID}, {...}, ...]
    """

    # withDist2Wire = False
    # withNTaggerHits = 0
    # TaggerHits = []

    
    fittedtrackids = []
    track_hits = {}
    if len(SmearedHits) > 100:
        print "Too large hits in the event!"
        return track_hits
        
    min_hits = 3
    max_shared_hits = 2
    
    #### Separate hits
    SmearedHits_y12, SmearedHits_stereo12, SmearedHits_34 = hits_split(SmearedHits)

                       
    #### PatRec in 12y
    short_tracks_y12 = pat_rec_y_views(SmearedHits_y12, min_hits, max_shared_hits)
        
    
    #### PatRec in stereo12
    short_tracks_12 = pet_rec_stereo_views(SmearedHits_stereo12, short_tracks_y12, min_hits)
    

    #### PatRec in 34
    short_tracks_34 = pat_rec_y_views(SmearedHits_34, min_hits, max_shared_hits)

    
    #### Combine tracks
    z_center=350.75
    track_combinations = combine_tracks_before_and_after_the_magnet(short_tracks_12, short_tracks_34, z_center)


    #### MuID is in other script


    # Prepare output of PatRec
    track_hits = {}
    for i_track in range(len(track_combinations)):
    
        atrack = track_combinations[i_track]

        hits_y12 = atrack['hits_y12']
        hits_stereo12 = atrack['hits_stereo12']
        hits_34 = atrack['hits_y34']
        p = atrack['p']
 
        [k, b] = np.polyfit(atrack['z_y12'], atrack['x_y12'], deg=1)
        x_in_magnet = k * z_center + b
        
        [k, b] = np.polyfit(atrack['z_stereo12'], atrack['y_stereo12'], deg=1)
        y_in_magnet = k * z_center + b

        if len(hits_y12) >= min_hits and len(hits_stereo12) >= min_hits and len(hits_34) >= min_hits:
            
            atrack = {'y12': sort_hits(hits_y12), 
                      'stereo12': sort_hits(hits_stereo12), 
                      '34': sort_hits(hits_34), 
                      'y_tagger': [],
                      'p': p, 
                      'x_in_magnet': x_in_magnet, 
                      'y_in_magnet': y_in_magnet}
            track_hits[i_track] = atrack

    
    if debug:
        print "Recognized tracks:"
        for i_track in track_hits.keys():
            atrack = track_hits[i_track]
            print "Track ", i_track
            print "Z_y12", [str(np.around(hit['z'], 2)) for hit in atrack['y12']]
            print "X_y12", [str(np.around(hit['xtop'], 2)) for hit in atrack['y12']]
            print "Z_stereo12", [str(np.around(hit['z'], 2)) for hit in atrack['stereo12']]
            print "X_stereo12", [str(np.around(hit['xtop'], 2)) for hit in atrack['stereo12']]
            print "Z_34", [str(np.around(hit['z'], 2)) for hit in atrack['34']]
            print "X_34", [str(np.around(hit['xtop'], 2)) for hit in atrack['34']]

    return track_hits


def finalize():
    pass
 
###################################################################################################    

def hits_split(SmearedHits):

    # Separate hits
    SmearedHits_12y = []
    SmearedHits_12stereo = []
    SmearedHits_34 = []
    for i_hit in range(len(SmearedHits)):
        ahit = SmearedHits[i_hit]
        detID = ahit['detID']
        statnb, vnb, pnb, lnb, snb = decodeDetectorID(detID)
        is_y12 = (statnb == 1) * (vnb == 0) + (statnb == 2) * (vnb == 1)
        is_stereo12 = (statnb == 1) * (vnb == 1) + (statnb == 2) * (vnb == 0)
        is_34 = (statnb == 3) + (statnb == 4)
        if is_y12:
            SmearedHits_12y.append(ahit)
        if is_stereo12:
            SmearedHits_12stereo.append(ahit)
        if is_34:
            SmearedHits_34.append(ahit)
            
    return SmearedHits_12y, SmearedHits_12stereo, SmearedHits_34
    

def pat_rec_y_views(SmearedHits, min_hits=3, max_shared_hits=2):

    long_tracks = []

    # Take 2 hits as a track seed
    for ahit1 in SmearedHits:
        for ahit2 in SmearedHits:

            if ahit1['z'] >= ahit2['z']:
                continue
            if ahit1['detID'] == ahit2['detID']:
                continue

            x1 = ahit1['xtop']
            x2 = ahit2['xtop']
            z1 = ahit1['z']
            z2 = ahit2['z']
            layer1 = ahit1['detID'] // 10000
            layer2 = ahit2['detID'] // 10000

            k_bin = 1. * (x2 - x1) / (z2 - z1)
            b_bin = x1 - k_bin * z1

            if abs(k_bin) > 1:
                continue

            atrack = {}
            atrack['hits_y'] = [ahit1, ahit2]
            atrack['x_y'] = [x1, x2]
            atrack['z_y'] = [z1, z2]
            atrack['layer'] = [layer1, layer2]

            # Add new hits to the seed
            for ahit3 in SmearedHits:

                if ahit3['detID'] == ahit1['detID'] or ahit3['detID'] == ahit2['detID']:
                    continue

                x3 = ahit3['xtop']
                z3 = ahit3['z']
                layer3 = ahit3['detID'] // 10000

                if layer3 in atrack['layer']:
                    continue

                in_bin = hit_in_window(z3, x3, k_bin, b_bin, window_width=3.0)#3
                if in_bin:
                    atrack['hits_y'].append(ahit3)
                    atrack['z_y'].append(z3)
                    atrack['x_y'].append(x3)
                    atrack['layer'].append(layer3)

            if len(atrack['hits_y']) >= min_hits:
                long_tracks.append(atrack)
                
    # Reduce number of clones
    short_tracks = reduce_clones(long_tracks, min_hits, max_shared_hits)
                
    # Fit tracks y12
    for atrack in short_tracks:
        [atrack['k_y'], atrack['b_y']] = np.polyfit(atrack['z_y'], atrack['x_y'], deg=1)
                
    return short_tracks
    
    
def pet_rec_stereo_views(SmearedHits_stereo, short_tracks_y, min_hits=3):

    ### PatRec in stereo12
    long_tracks_stereo = []
    short_tracks_stereo = []
    used_hits = []
    # deg = np.deg2rad(ShipGeo['MufluxSpectrometer']['ViewAngle'])

    for i_track_y in range(len(short_tracks_y)):

        atrack_y = short_tracks_y[i_track_y]
        k_y = atrack_y['k_y']
        b_y = atrack_y['b_y']
        
        # Get hit zx projections
        for ahit in SmearedHits_stereo:
            y_center  = get_zy_projection(ahit['z'], ahit['xtop'], ahit['ytop'], ahit['xbot'], ahit['ybot'], k_y, b_y)
            ahit['zy_projection'] = y_center

        
        temp_tracks_stereo = []

        for ahit1 in SmearedHits_stereo:
            for ahit2 in SmearedHits_stereo:

                if ahit1['z'] >= ahit2['z']:
                    continue
                if ahit1['detID'] == ahit2['detID']:
                    continue
                if ahit1['digiHit'] in used_hits:
                    continue
                if ahit2['digiHit'] in used_hits:
                    continue

                y1_center  = ahit1['zy_projection']
                y2_center  = ahit2['zy_projection']

                if abs(y1_center ) > 70 or abs(y2_center ) > 70:
                    continue

                y1 = y1_center
                y2 = y2_center
                z1 = ahit1['z']
                z2 = ahit2['z']
                layer1 = ahit1['detID'] // 10000
                layer2 = ahit2['detID'] // 10000

                k_bin = 1. * (y2 - y1) / (z2 - z1)
                b_bin = y1 - k_bin * z1

                atrack = {}
                atrack['hits_stereo'] = [ahit1, ahit2]
                atrack['y_stereo'] = [y1, y2]
                atrack['z_stereo'] = [z1, z2]
                atrack['layer'] = [layer1, layer2]

                for ahit3 in SmearedHits_stereo:

                    if ahit3['digiHit'] == ahit1['digiHit'] or ahit3['digiHit'] == ahit2['digiHit']:
                        continue
                    if ahit3['digiHit'] in used_hits:
                        continue

                    y3_center = ahit3['zy_projection']
                    z3 = ahit3['z']
                    layer3 = ahit3['detID'] // 10000

                    if abs(y3_center) > 70:
                        continue

                    if layer3 in atrack['layer']:
                        continue

                    in_bin = hit_in_window(z3, y3_center, k_bin, b_bin, window_width=10.0)#10.0
                    if in_bin:
                        atrack['hits_stereo'].append(ahit3)
                        atrack['z_stereo'].append(z3)
                        atrack['y_stereo'].append(y3_center)
                        atrack['layer'].append(layer3)

                if len(atrack['hits_stereo']) >= min_hits:
                    temp_tracks_stereo.append(atrack)
                    long_tracks_stereo.append(atrack)
                            
        # Remove clones
        max_track = None
        max_n_hits = -999

        for atrack in temp_tracks_stereo:
            if len(atrack['hits_stereo']) > max_n_hits:
                max_track = atrack
                max_n_hits = len(atrack['hits_stereo'])

        if max_track is not None:
            atrack = {}
            atrack['hits_y'] = atrack_y['hits_y']
            atrack['z_y'] = atrack_y['z_y']
            atrack['x_y'] = atrack_y['x_y']
            atrack['k_y'] = atrack_y['k_y']
            atrack['b_y'] = atrack_y['b_y']
            atrack['hits_stereo'] = max_track['hits_stereo']
            atrack['z_stereo'] = max_track['z_stereo']
            atrack['y_stereo'] = max_track['y_stereo']
            
            short_tracks_stereo.append(atrack)
            for ahit in max_track['hits_stereo']:
                #used_hits.append(ahit['digiHit'])
                pass
                
    return short_tracks_stereo
    
    
def combine_tracks_before_and_after_the_magnet(short_tracks_12, short_tracks_34, z_center):

    # Combine track y12 and 34 and momentum calculation
    i_track_12 = []
    i_track_34 = []
    deltas_y = []
    momentums = []
    for i_12 in range(len(short_tracks_12)):
        atrack_12 = short_tracks_12[i_12]
        y_center_12 = atrack_12['k_y'] * z_center + atrack_12['b_y']
        alpha_12 = np.arctan(atrack_12['k_y'])
        for i_34 in range(len(short_tracks_34)):
            atrack_34 = short_tracks_34[i_34]
            y_center_34 = atrack_34['k_y'] * z_center + atrack_34['b_y']
            alpha_34 = np.arctan(atrack_34['k_y'])
            i_track_12.append(i_12)
            i_track_34.append(i_34)
            deltas_y.append(abs(y_center_12 - y_center_34))
            momentums.append(1.03 / (alpha_12 - alpha_34))

    max_dy = 50
    used_12 = []
    used_34 = []
    track_combinations = []
    for i in np.argsort(deltas_y):
        dy = deltas_y[i]
        mom = momentums[i]
        i_12 = i_track_12[i]
        i_34 = i_track_34[i]
        if dy < max_dy:
            if i_12 not in used_12:
                if i_34 not in used_34:
                    atrack = {}
                    for key in short_tracks_12[i_12].keys():
                        atrack[key+'12'] = short_tracks_12[i_12][key]
                    for key in short_tracks_34[i_34].keys():
                        atrack[key+'34'] = short_tracks_34[i_34][key]
                    atrack['p'] = abs(mom)
                    track_combinations.append(atrack)
                    #used_12.append(i_12)
                    #used_34.append(i_34)
                    
    return track_combinations
    

def reduce_clones(long_tracks, min_hits=3, max_shared_hits=2):

    # Remove clones in y12
    used_hits = []
    short_tracks = []
    n_hits = [len(atrack['hits_y']) for atrack in long_tracks]

    for i_track in np.argsort(n_hits)[::-1]:

        atrack = long_tracks[i_track]
        n_shared_hits = 0

        for i_hit in range(len(atrack['hits_y'])):
            ahit = atrack['hits_y'][i_hit]
            if ahit['digiHit'] in used_hits: #digiHit
                n_shared_hits += 1

        if len(atrack['hits_y']) >= min_hits and n_shared_hits <= max_shared_hits:
            short_tracks.append(atrack)
            for ahit in atrack['hits_y']:
                used_hits.append(ahit['digiHit']) #digiHit
                
    return short_tracks
    
    
###################################################################################################


def decodeDetectorID(detID):
    """
    Decodes detector ID.

    Parameters
    ----------
    detID : int or array-like
        Detector ID values.

    Returns
    -------
    statnb : int or array-like
        Station numbers.
    vnb : int or array-like
        View numbers.
    pnb : int or array-like
        Plane numbers.
    lnb : int or array-like
        Layer numbers.
    snb : int or array-like
        Straw tube numbers.
    """

    statnb = detID // 10000000
    vnb = (detID - statnb * 10000000) // 1000000
    pnb = (detID - statnb * 10000000 - vnb * 1000000) // 100000
    lnb = (detID - statnb * 10000000 - vnb * 1000000 - pnb * 100000) // 10000
    snb = detID - statnb * 10000000 - vnb * 1000000 - pnb * 100000 - lnb * 10000 - 2000

    return statnb, vnb, pnb, lnb, snb


def hit_in_bin(x, y, k_bin, b_bin, k_size, b_size):
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


    b_left = y - (k_bin - 0.5 * k_size) * x
    b_right = y - (k_bin + 0.5 * k_size) * x

    sel = (b_left >= b_bin - 0.5 * b_size) * (b_right <= b_bin + 0.5 * b_size) + \
    (b_left <= b_bin + 0.5 * b_size) * (b_right >= b_bin - 0.5 * b_size)

    return sel

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


def get_zy_projection(z, xtop, ytop, xbot, ybot, k_y, b_y):
    
    x = k_y * z + b_y
    
    k = (ytop - ybot) / (xtop - xbot + 10**-6)
    b = ytop - k * xtop
    y = k * x + b
    
    return y
    

def sort_hits(hits):

    sorted_hits = []
    hits_z = [ahit['z'] for ahit in hits]
    sort_index = np.argsort(hits_z)
    for i_hit in sort_index:
        sorted_hits.append(hits[i_hit])
        
    return sorted_hits







    
    
