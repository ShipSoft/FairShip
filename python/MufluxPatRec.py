__author__ = 'Mikhail Hushchyn'

import numpy as np

# Globals
ReconstructibleMCTracks = []
theTracks = []


def initialize(fgeo):
    pass


def execute(SmearedHits):
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
    
    fittedtrackids = []
    track_hits = {}
    if len(SmearedHits) > 100:
        print "Too large hits in the event!"
        return track_hits
    
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
            
            
    #### PatRec in 12y
    min_hits = 3
    long_tracks_y12 = []

    # Take 2 hits as a track seed
    for ahit1 in SmearedHits_12y:
        for ahit2 in SmearedHits_12y:
            
            if ahit1['z'] >= ahit2['z']:
                continue
            if ahit1['detID'] == ahit2['detID']:
                continue

            # +- dist2wire
            for sign1 in [-1, 1]:
                for sign2 in [-1, 1]:

                    x1 = ahit1['xtop'] + sign1 * ahit1['dist']
                    x2 = ahit2['xtop'] + sign2 * ahit2['dist']
                    z1 = ahit1['z']
                    z2 = ahit2['z']
                    layer1 = ahit1['detID'] // 10000
                    layer2 = ahit2['detID'] // 10000

                    k_bin = 1. * (x2 - x1) / (z2 - z1)
                    b_bin = x1 - k_bin * z1

                    if abs(k_bin) > 1:
                        continue

                    atrack = {}
                    atrack['hits'] = [ahit1, ahit2]
                    atrack['x'] = [x1, x2]
                    atrack['z'] = [z1, z2]
                    atrack['layer'] = [layer1, layer2]
                    
                    # Add new hits to the seed
                    for ahit3 in SmearedHits_12y:

                        if ahit3['detID'] == ahit1['detID'] or ahit3['detID'] == ahit2['detID']:
                            continue

                        dist3 = ahit3['dist']
                        x3 = ahit3['xtop']
                        z3 = ahit3['z']
                        layer3 = ahit3['detID'] // 10000

                        # if hit_in_bin(z3, x3+dist3, k_bin, b_bin, k_size=2./100, b_size=140./100):
                        if hit_in_window(z3, x3+dist3, k_bin, b_bin, window_width=0.1): #0.1
                            if layer3 not in atrack['layer']:
                                atrack['hits'].append(ahit3)
                                atrack['x'].append(x3+dist3)
                                atrack['z'].append(z3)
                                atrack['layer'].append(layer3)
                        # elif hit_in_bin(z3, x3-dist3, k_bin, b_bin, k_size=2./100, b_size=140./100):
                        elif hit_in_window(z3, x3-dist3, k_bin, b_bin, window_width=0.1): #0.1
                            if layer3 not in atrack['layer']:
                                atrack['hits'].append(ahit3)
                                atrack['x'].append(x3-dist3)
                                atrack['z'].append(z3)
                                atrack['layer'].append(layer3)

                    if len(atrack['hits']) >= min_hits:
                        long_tracks_y12.append(atrack)
    
    # Remove clones in y12
    used_hits = []
    short_tracks_y12 = []
    n_hits = [len(atrack['hits']) for atrack in long_tracks_y12]

    for i_track in np.argsort(n_hits)[::-1]:

        atrack = long_tracks_y12[i_track]
        new_track = {}
        new_track['hits'] = []
        new_track['x'] = []
        new_track['z'] = []
        new_track['layer'] = []

        for i_hit in range(len(atrack['hits'])):
            ahit = atrack['hits'][i_hit]
            if ahit['digiHit'] not in used_hits:
                new_track['hits'].append(ahit)
                new_track['x'].append(atrack['x'][i_hit])
                new_track['z'].append(atrack['z'][i_hit]) 

        if len(new_track['hits']) >= min_hits:
            short_tracks_y12.append(new_track)
            for ahit in new_track['hits']:
                used_hits.append(ahit['digiHit'])
                
    # Fit tracks y12
    for atrack in short_tracks_y12:
        [atrack['k'], atrack['b']] = np.polyfit(atrack['z'], atrack['x'], deg=1)
        
        
    # Extrapolation to the center of the magnet
    # ShipGeo is defined in macro/MufluxReco.py
    z_center = 350.75# ShipGeo.Bfield.z
    
    """
    #### PatRec in 34
    long_tracks_34 = []
    short_tracks_34 = []
    used_hits = []

    for i_track_y12 in range(len(short_tracks_y12)):

        atrack_y12 = short_tracks_y12[i_track_y12]
        x_center = atrack_y12['k'] * z_center + atrack_y12['b']
        
        temp_tracks_34 = []

        for ahit1 in SmearedHits_34:

            if ahit1['digiHit'] in used_hits:
                continue

            for sign1 in [-1, 1]:

                x1 = ahit1['xtop'] + sign1 * ahit1['dist']
                z1 = ahit1['z']
                layer1 = ahit1['detID'] // 10000

                k_bin = 1. * (x1 - x_center) / (z1 - z_center)
                b_bin = x1 - k_bin * z1

                if abs(k_bin) > 1:
                    continue

                atrack = {}
                atrack['hits'] = [ahit1]
                atrack['x'] = [x1]
                atrack['z'] = [z1]
                atrack['layer'] = [layer1]
                atrack['i_track_y12'] = i_track_y12
                
                for ahit2 in SmearedHits_34:

                    if ahit2['digiHit'] in used_hits:
                        continue
                    if ahit1['detID'] == ahit2['detID']:
                            continue

                    dist2 = ahit2['dist']
                    x2 = ahit2['xtop']
                    z2 = ahit2['z']
                    layer2 = ahit2['detID'] // 10000

                    # if hit_in_bin(z2, x2+dist2, k_bin, b_bin, k_size=2./100, b_size=140./100):
                    if hit_in_window(z2, x2+dist2, k_bin, b_bin, window_width=3.0): #1.5
                        if layer2 not in atrack['layer']:
                            atrack['hits'].append(ahit2)
                            atrack['x'].append(x2+dist2)
                            atrack['z'].append(z2)
                            atrack['layer'].append(layer2)
                    # elif hit_in_bin(z2, x2-dist2, k_bin, b_bin, k_size=2./100, b_size=140./100):
                    elif hit_in_window(z2, x2-dist2, k_bin, b_bin, window_width=3.0): #1.5
                        if layer2 not in atrack['layer']:
                            atrack['hits'].append(ahit2)
                            atrack['x'].append(x2-dist2)
                            atrack['z'].append(z2)
                            atrack['layer'].append(layer2)

                if len(atrack['hits']) >= min_hits:
                    temp_tracks_34.append(atrack)
                    long_tracks_34.append(atrack)
                    
        # Remove clones in 34
        max_track = None
        max_n_hits = -999

        for atrack in temp_tracks_34:
            if len(atrack['hits']) > max_n_hits:
                max_track = atrack
                max_n_hits = len(atrack['hits'])

        if max_track is not None:
            short_tracks_34.append(max_track)
            for ahit in max_track['hits']:
                used_hits.append(ahit['digiHit'])
    """

    #### PatRec in 34
    min_hits = 3
    long_tracks_34 = []

    # Take 2 hits as a track seed
    for ahit1 in SmearedHits_34:
        for ahit2 in SmearedHits_34:

            if ahit1['z'] >= ahit2['z']:
                continue
            if ahit1['detID'] == ahit2['detID']:
                continue

            # +- dist2wire
            for sign1 in [-1, 1]:
                for sign2 in [-1, 1]:

                    x1 = ahit1['xtop'] + sign1 * ahit1['dist']
                    x2 = ahit2['xtop'] + sign2 * ahit2['dist']
                    z1 = ahit1['z']
                    z2 = ahit2['z']
                    layer1 = ahit1['detID'] // 10000
                    layer2 = ahit2['detID'] // 10000

                    k_bin = 1. * (x2 - x1) / (z2 - z1)
                    b_bin = x1 - k_bin * z1

                    if abs(k_bin) > 1:
                        continue

                    atrack = {}
                    atrack['hits'] = [ahit1, ahit2]
                    atrack['x'] = [x1, x2]
                    atrack['z'] = [z1, z2]
                    atrack['layer'] = [layer1, layer2]
                    atrack['i_track_y12'] = -999

                    # Add new hits to the seed
                    for ahit3 in SmearedHits_34:

                        if ahit3['detID'] == ahit1['detID'] or ahit3['detID'] == ahit2['detID']:
                            continue

                        dist3 = ahit3['dist']
                        x3 = ahit3['xtop']
                        z3 = ahit3['z']
                        layer3 = ahit3['detID'] // 10000

                        # if hit_in_bin(z3, x3+dist3, k_bin, b_bin, k_size=2./100, b_size=140./100):
                        if hit_in_window(z3, x3+dist3, k_bin, b_bin, window_width=0.1): #0.1
                            if layer3 not in atrack['layer']:
                                atrack['hits'].append(ahit3)
                                atrack['x'].append(x3+dist3)
                                atrack['z'].append(z3)
                                atrack['layer'].append(layer3)
                        # elif hit_in_bin(z3, x3-dist3, k_bin, b_bin, k_size=2./100, b_size=140./100):
                        elif hit_in_window(z3, x3-dist3, k_bin, b_bin, window_width=0.1): #0.1
                            if layer3 not in atrack['layer']:
                                atrack['hits'].append(ahit3)
                                atrack['x'].append(x3-dist3)
                                atrack['z'].append(z3)
                                atrack['layer'].append(layer3)

                    if len(atrack['hits']) >= min_hits:
                        long_tracks_34.append(atrack)

    # Remove clones in 34
    used_hits = []
    short_tracks_34 = []
    n_hits = [len(atrack['hits']) for atrack in long_tracks_34]

    for i_track in np.argsort(n_hits)[::-1]:

        atrack = long_tracks_34[i_track]
        new_track = {}
        new_track['hits'] = []
        new_track['x'] = []
        new_track['z'] = []
        new_track['layer'] = []
        new_track['i_track_y12'] = -999

        for i_hit in range(len(atrack['hits'])):
            ahit = atrack['hits'][i_hit]
            if ahit['digiHit'] not in used_hits:
                new_track['hits'].append(ahit)
                new_track['x'].append(atrack['x'][i_hit])
                new_track['z'].append(atrack['z'][i_hit])

        if len(new_track['hits']) >= min_hits:
            short_tracks_34.append(new_track)
            for ahit in new_track['hits']:
                used_hits.append(ahit['digiHit'])

    # Fit tracks 34
    for atrack in short_tracks_34:
        [atrack['k'], atrack['b']] = np.polyfit(atrack['z'], atrack['x'], deg=1)

    # Combine track y12 and 34
    i_track_y12 = []
    i_track_34 = []
    deltas_y = []
    for i_y12 in range(len(short_tracks_y12)):
        atrack_y12 = short_tracks_y12[i_y12]
        y_center_y12 = atrack_y12['k'] * z_center + atrack_y12['b']
        for i_34 in range(len(short_tracks_34)):
            atrack_34 = short_tracks_34[i_34]
            y_center_34 = atrack_34['k'] * z_center + atrack_34['b']
            i_track_y12.append(i_y12)
            i_track_34.append(i_34)
            deltas_y.append(abs(y_center_y12 - y_center_34))

    max_dy = 20
    used_y12 = []
    used_34 = []
    for i in np.argsort(deltas_y):
        dy = deltas_y[i]
        i_y12 = i_track_y12[i]
        i_34 = i_track_34[i]
        if dy < max_dy:
            if i_y12 not in used_y12:
                if i_34 not in used_34:
                    atrack = short_tracks_34[i_34]
                    atrack['i_track_y12'] = i_y12
                    used_y12.append(i_y12)
                    used_34.append(i_34)



    ### PatRec in stereo12
    long_tracks_stereo12 = []
    short_tracks_stereo12 = []
    used_hits = []
    deg = np.deg2rad(ShipGeo['MufluxSpectrometer']['ViewAngle'])

    for i_track_y12 in range(len(short_tracks_y12)):

        atrack_y12 = short_tracks_y12[i_track_y12]
        k_y12 = atrack_y12['k']
        b_y12 = atrack_y12['b']
        
        temp_tracks_stereo12 = []

        for ahit1 in SmearedHits_12stereo:
            for ahit2 in SmearedHits_12stereo:

                if ahit1['z'] >= ahit2['z']:
                    continue
                if ahit1['detID'] == ahit2['detID']:
                    continue
                if ahit1['digiHit'] in used_hits:
                    continue
                if ahit2['digiHit'] in used_hits:
                    continue
                    
                y1_center  = get_zy_projection(ahit1['z'],
                                               ahit1['xtop'], ahit1['ytop'],
                                               ahit1['xbot'], ahit1['ybot'], k_y12, b_y12)
                y2_center  = get_zy_projection(ahit2['z'],
                                               ahit2['xtop'], ahit2['ytop'],
                                               ahit2['xbot'], ahit2['ybot'], k_y12, b_y12)

                if abs(y1_center ) > 50 or abs(y2_center ) > 50:
                    continue

                for sign1 in [-1, 1]:
                    for sign2 in [-1, 1]:

                        y1 = y1_center + sign1 * ahit1['dist'] / np.sin(deg)
                        y2 = y2_center + sign2 * ahit2['dist'] / np.sin(deg)
                        z1 = ahit1['z']
                        z2 = ahit2['z']
                        layer1 = ahit1['detID'] // 10000
                        layer2 = ahit2['detID'] // 10000

                        k_bin = 1. * (y2 - y1) / (z2 - z1)
                        b_bin = y1 - k_bin * z1

                        atrack = {}
                        atrack['hits'] = [ahit1, ahit2]
                        atrack['y'] = [y1, y2]
                        atrack['z'] = [z1, z2]
                        atrack['layer'] = [layer1, layer2]
                        atrack['i_track_y12'] = i_track_y12

                        for ahit3 in SmearedHits_12stereo:
                            
                            if ahit3['digiHit'] == ahit1['digiHit'] or ahit3['digiHit'] == ahit2['digiHit']:
                                continue
                            if ahit3['digiHit'] in used_hits:
                                continue
                            
                            dist3 = ahit3['dist'] / np.sin(deg)
                            y3_center = get_zy_projection(ahit3['z'],
                                                          ahit3['xtop'], ahit3['ytop'],
                                                          ahit3['xbot'], ahit3['ybot'], k_y12, b_y12)
                            z3 = ahit3['z']
                            layer3 = ahit3['detID'] // 10000

                            if abs(y3_center) > 50:
                                continue

                            # if hit_in_bin(z3, y3_center+dist3, k_bin, b_bin, k_size=2./100, b_size=10000./100):
                            if hit_in_window(z3, y3_center+dist3, k_bin, b_bin, window_width=20.):
                                if layer3 not in atrack['layer']:
                                    atrack['hits'].append(ahit3)
                                    atrack['y'].append(y3_center+dist3)
                                    atrack['z'].append(z3)
                                    atrack['layer'].append(layer3)
                            # elif hit_in_bin(z3, y3_center-dist3, k_bin, b_bin, k_size=2./100, b_size=10000./100):
                            elif hit_in_window(z3, y3_center-dist3, k_bin, b_bin, window_width=20.):
                                if layer3 not in atrack['layer']:
                                    atrack['hits'].append(ahit3)
                                    atrack['y'].append(y3_center-dist3)
                                    atrack['z'].append(z3)
                                    atrack['layer'].append(layer3)

                        if len(atrack['hits']) >= min_hits:
                            temp_tracks_stereo12.append(atrack)
                            long_tracks_stereo12.append(atrack)
                            
        # Remove clones
        max_track = None
        max_n_hits = -999

        for atrack in temp_tracks_stereo12:
            if len(atrack['hits']) > max_n_hits:
                max_track = atrack
                max_n_hits = len(atrack['hits'])

        if max_track is not None:
            short_tracks_stereo12.append(max_track)
            for ahit in max_track['hits']:
                used_hits.append(ahit['digiHit'])
        


    # Prepare output of PatRec
    track_hits = {}
    for i_track in range(len(short_tracks_y12)):

        hits_y12 = []
        hits_stereo12 = []
        hits_34 = []
        
        for ahit in short_tracks_y12[i_track]['hits']:
            hits_y12.append(ahit)
            
        for atrack in short_tracks_stereo12:
            if atrack['i_track_y12'] == i_track:
                for ahit in atrack['hits']:
                    hits_stereo12.append(ahit)
                break
                    
        for atrack in short_tracks_34:
            if atrack['i_track_y12'] == i_track:
                for ahit in atrack['hits']:
                    hits_34.append(ahit)
                break

        if len(hits_y12) >= min_hits and len(hits_stereo12) >= min_hits and len(hits_34) >= min_hits:
            atrack = {'y12': hits_y12, 'stereo12': hits_stereo12, '34': hits_34}
            track_hits[i_track] = atrack



    return track_hits


def finalize():
    pass


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
    
    