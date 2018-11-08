__author__ = 'Mikhail Hushchyn'

import numpy as np
import pickle as cPickle

# Globals
ReconstructibleMCTracks = []
theTracks = []

r_scale = ShipGeo.strawtubes.InnerStrawDiameter / 1.975

with open("/afs/cern.ch/work/m/mhushchy/public/ship_models/triplets_rf.pkl", 'rb') as f:
    triplets_clf = cPickle.load(f)
    print "Load triplets classifier."

def initialize(fgeo):
    pass


def execute(smeared_hits, ship_geo, method=''):
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

    recognized_tracks = {}

    if method == "TemplateMatching":
        recognized_tracks = template_matching_pattern_recognition(smeared_hits, ship_geo)
    elif method == "TemplateMatchingShort":
        recognized_tracks = short_template_matching_pattern_recognition(smeared_hits, ship_geo)
    elif method == "FH":
        recognized_tracks = fast_hough_transform_pattern_recognition(smeared_hits, ship_geo)
    elif method == "AR":
        recognized_tracks = artificial_retina_pattern_recognition(smeared_hits, ship_geo)
    elif method == "TCV0":
        recognized_tracks = triplets_v0_pattern_recognition(smeared_hits, ship_geo)
    elif method == "TCV1":
        recognized_tracks = triplets_v1_pattern_recognition(smeared_hits, ship_geo)
    elif method == "TCV2":
        recognized_tracks = triplets_v2_pattern_recognition(smeared_hits, ship_geo)
    else:
        hits_y12, hits_stereo12, hits_y34, hits_stereo34 = hits_split(smeared_hits)
        atrack = {'y12': hits_y12, 'stereo12': hits_stereo12, 'y34': hits_y34, 'stereo34': hits_stereo34}
        recognized_tracks[0] = atrack

    # print "track_hits.keys(): ", recognized_tracks.keys()

    return recognized_tracks


def finalize():
    pass

########################################################################################################################
##
## Template Matching
##
########################################################################################################################

def template_matching_pattern_recognition(SmearedHits, ShipGeo):
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

    recognized_tracks = {}

    if len(SmearedHits) > 500:
        print "Too large hits in the event!"
        return recognized_tracks

    min_hits = 3

    #### Separate hits
    SmearedHits_12y, SmearedHits_12stereo, SmearedHits_34y, SmearedHits_34stereo = hits_split(SmearedHits)

    #### PatRec in 12y
    recognized_tracks_y12 = pat_rec_view(SmearedHits_12y, min_hits)
    # recognized_tracks_y12 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo12
    recognized_tracks_12 = pat_rec_stereo_views(SmearedHits_12stereo, recognized_tracks_y12, min_hits)
    # recognized_tracks_12 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    #### PatRec in 34y
    recognized_tracks_y34 = pat_rec_view(SmearedHits_34y, min_hits)
    # recognized_tracks_y34 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo34
    recognized_tracks_34 = pat_rec_stereo_views(SmearedHits_34stereo, recognized_tracks_y34, min_hits)
    # recognized_tracks_34 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### Combination of tracks before and after the magnet
    recognized_tracks_combo = tracks_combination_using_extrapolation(recognized_tracks_12, recognized_tracks_34, ShipGeo.Bfield.z)
    # recognized_tracks_combo = [{'hits_y12': [hit1, hit2, ...], 'hits_stereo12': [hit1, hit2, ...],
    #                             'hits_y34': [hit1, hit2, ...], 'hits_stereo34': [hit1, hit2, ...]}, {..}, ..]

    # Prepare output of PatRec
    recognized_tracks = {}
    i_track = 0
    for atrack_combo in recognized_tracks_combo:

        hits_y12 = atrack_combo['hits_y12']
        hits_stereo12 = atrack_combo['hits_stereo12']
        hits_y34 = atrack_combo['hits_y34']
        hits_stereo34 = atrack_combo['hits_stereo34']


        if len(hits_y12) >= min_hits and len(hits_stereo12) >= min_hits and len(hits_y34) >= min_hits and len(hits_stereo34) >= min_hits:
            atrack = {'y12': hits_y12, 'stereo12': hits_stereo12, 'y34': hits_y34, 'stereo34': hits_stereo34}
            recognized_tracks[i_track] = atrack
            i_track += 1



    return recognized_tracks


def pat_rec_view(SmearedHits, min_hits):
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

    long_recognized_tracks = []

    # Take 2 hits as a track seed
    for ahit1 in SmearedHits:
        for ahit2 in SmearedHits:

            if ahit1['z'] >= ahit2['z']:
                continue
            if ahit1['detID'] == ahit2['detID']:
                continue

            k_seed = 1. * (ahit2['ytop'] - ahit1['ytop']) / (ahit2['z'] - ahit1['z'])
            b_seed = ahit1['ytop'] - k_seed * ahit1['z']

            if abs(k_seed) > 1:
                continue

            atrack = {}
            atrack['hits_y'] = [ahit1, ahit2]
            atrack_layers = [ahit1['detID'] // 10000, ahit2['detID'] // 10000]

            # Add new hits to the seed
            for ahit3 in SmearedHits:

                if ahit3['detID'] == ahit1['detID'] or ahit3['detID'] == ahit2['detID']:
                    continue

                layer3 = ahit3['detID'] // 10000
                if layer3 in atrack_layers:
                    continue

                in_bin = hit_in_window(ahit3['z'], ahit3['ytop'], k_seed, b_seed, window_width=1.4 * r_scale)
                if in_bin:
                    atrack['hits_y'].append(ahit3)
                    atrack_layers.append(layer3)

            if len(atrack['hits_y']) >= min_hits:
                long_recognized_tracks.append(atrack)

    # Remove clones
    recognized_tracks = reduce_clones_using_one_track_per_hit(long_recognized_tracks, min_hits)

    # Track fit
    for atrack in recognized_tracks:
        z_coords = [ahit['z'] for ahit in atrack['hits_y']]
        y_coords = [ahit['ytop'] for ahit in atrack['hits_y']]
        [atrack['k_y'], atrack['b_y']] = np.polyfit(z_coords, y_coords, deg=1)

    return recognized_tracks



########################################################################################################################
##
## Short Template Matching
##
########################################################################################################################

def short_template_matching_pattern_recognition(SmearedHits, ShipGeo):
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

    recognized_tracks = {}

    if len(SmearedHits) > 500:
        print "Too large hits in the event!"
        return recognized_tracks

    min_hits = 3

    #### Separate hits
    SmearedHits_12y, SmearedHits_12stereo, SmearedHits_34y, SmearedHits_34stereo = hits_split(SmearedHits)

    #### PatRec in 12y
    recognized_tracks_y12 = short_template_matching_pat_rec_view(SmearedHits_12y, min_hits)
    # recognized_tracks_y12 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo12
    recognized_tracks_12 = pat_rec_stereo_views(SmearedHits_12stereo, recognized_tracks_y12, min_hits)
    # recognized_tracks_12 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    #### PatRec in 34y
    recognized_tracks_y34 = short_template_matching_pat_rec_view(SmearedHits_34y, min_hits)
    # recognized_tracks_y34 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo34
    recognized_tracks_34 = pat_rec_stereo_views(SmearedHits_34stereo, recognized_tracks_y34, min_hits)
    # recognized_tracks_34 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### Combination of tracks before and after the magnet
    recognized_tracks_combo = tracks_combination_using_extrapolation(recognized_tracks_12, recognized_tracks_34, ShipGeo.Bfield.z)
    # recognized_tracks_combo = [{'hits_y12': [hit1, hit2, ...], 'hits_stereo12': [hit1, hit2, ...],
    #                             'hits_y34': [hit1, hit2, ...], 'hits_stereo34': [hit1, hit2, ...]}, {..}, ..]

    # Prepare output of PatRec
    recognized_tracks = {}
    i_track = 0
    for atrack_combo in recognized_tracks_combo:

        hits_y12 = atrack_combo['hits_y12']
        hits_stereo12 = atrack_combo['hits_stereo12']
        hits_y34 = atrack_combo['hits_y34']
        hits_stereo34 = atrack_combo['hits_stereo34']


        if len(hits_y12) >= min_hits and len(hits_stereo12) >= min_hits and len(hits_y34) >= min_hits and len(hits_stereo34) >= min_hits:
            atrack = {'y12': hits_y12, 'stereo12': hits_stereo12, 'y34': hits_y34, 'stereo34': hits_stereo34}
            recognized_tracks[i_track] = atrack
            i_track += 1



    return recognized_tracks


def short_template_matching_pat_rec_view(SmearedHits, min_hits):
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

    long_recognized_tracks = []
    recognized_tracks = []

    z_hits = [ahit['z'] for ahit in SmearedHits]
    z_sorted_indeces = np.argsort(z_hits)

    SmearedHits_ordered = np.array(SmearedHits)[z_sorted_indeces]
    used_hits = [0] * len(SmearedHits_ordered)

    # Take 2 hits as a track seed
    for i_hit_start in range(len(SmearedHits_ordered)-1):

        if used_hits[i_hit_start] == 1:
            continue

        best_track = {'hits_y': []}
        best_track_hit_indeces = []
        n_best_track_hits = 0

        for i_hit_end in range(len(SmearedHits_ordered)-1, i_hit_start, -1):

            if used_hits[i_hit_end] == 1:
                continue
            if (i_hit_end - i_hit_start + 1) < n_best_track_hits:
                break

            hit_start = SmearedHits_ordered[i_hit_start]
            hit_end = SmearedHits_ordered[i_hit_end]

            if hit_start['z'] >= hit_end['z']:
                continue
            if hit_start['detID'] == hit_end['detID']:
                continue

            k_seed = 1. * (hit_end['ytop'] - hit_start['ytop']) / (hit_end['z'] - hit_start['z'])
            b_seed = hit_start['ytop'] - k_seed * hit_start['z']

            if abs(k_seed) > 1:
                continue

            atrack = {}
            atrack['hits_y'] = [hit_start, hit_end]
            atrack_layers = [hit_start['detID'] // 10000, hit_end['detID'] // 10000]
            atrack_hit_indeces = [i_hit_start, i_hit_end]

            # Add new hits to the seed
            for i_hit_middle in range(i_hit_start+1, i_hit_end):

                if used_hits[i_hit_middle] == 1:
                    continue

                hit_middle = SmearedHits_ordered[i_hit_middle]

                if hit_middle['detID'] == hit_start['detID'] or hit_middle['detID'] == hit_end['detID']:
                    continue

                layer3 = hit_middle['detID'] // 10000
                if layer3 in atrack_layers:
                    continue

                in_bin = hit_in_window(hit_middle['z'], hit_middle['ytop'], k_seed, b_seed, window_width=1.4 * r_scale)
                if in_bin:
                    atrack['hits_y'].append(hit_middle)
                    atrack_layers.append(layer3)
                    atrack_hit_indeces.append(i_hit_middle)

            if len(atrack['hits_y']) >= min_hits:
                if len(atrack['hits_y']) > n_best_track_hits:
                    best_track = atrack
                    n_best_track_hits = len(atrack['hits_y'])
                    best_track_hit_indeces = atrack_hit_indeces


        if len(best_track['hits_y']) >= min_hits:
            recognized_tracks.append(best_track)
            for ahit_index in best_track_hit_indeces:
                used_hits[ahit_index] = 1


    # Remove clones
    # recognized_tracks = reduce_clones_using_one_track_per_hit(long_recognized_tracks, min_hits)

    # Track fit
    for atrack in recognized_tracks:
        z_coords = [ahit['z'] for ahit in atrack['hits_y']]
        y_coords = [ahit['ytop'] for ahit in atrack['hits_y']]
        [atrack['k_y'], atrack['b_y']] = np.polyfit(z_coords, y_coords, deg=1)

    return recognized_tracks


########################################################################################################################
##
## Fast Hough Transform
##
########################################################################################################################

def fast_hough_transform_pattern_recognition(SmearedHits, ShipGeo):
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

    recognized_tracks = {}

    if len(SmearedHits) > 500:
        print "Too large hits in the event!"
        return recognized_tracks

    min_hits = 3

    #### Separate hits
    SmearedHits_12y, SmearedHits_12stereo, SmearedHits_34y, SmearedHits_34stereo = hits_split(SmearedHits)

    #### PatRec in 12y
    recognized_tracks_y12 = fast_hough_pat_rec_y_view(SmearedHits_12y, min_hits)
    # recognized_tracks_y12 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo12
    #recognized_tracks_12 = pat_rec_stereo_views(SmearedHits_12stereo, recognized_tracks_y12, min_hits)
    recognized_tracks_12 = fast_hough_pat_rec_stereo_views(SmearedHits_12stereo, recognized_tracks_y12, min_hits)
    # recognized_tracks_12 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    #### PatRec in 34y
    recognized_tracks_y34 = fast_hough_pat_rec_y_view(SmearedHits_34y, min_hits)
    # recognized_tracks_y34 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo34
    #recognized_tracks_34 = pat_rec_stereo_views(SmearedHits_34stereo, recognized_tracks_y34, min_hits)
    recognized_tracks_34 = fast_hough_pat_rec_stereo_views(SmearedHits_34stereo, recognized_tracks_y34, min_hits)
    # recognized_tracks_34 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### Combination of tracks before and after the magnet
    recognized_tracks_combo = tracks_combination_using_extrapolation(recognized_tracks_12, recognized_tracks_34, ShipGeo.Bfield.z)
    # recognized_tracks_combo = [{'hits_y12': [hit1, hit2, ...], 'hits_stereo12': [hit1, hit2, ...],
    #                             'hits_y34': [hit1, hit2, ...], 'hits_stereo34': [hit1, hit2, ...]}, {..}, ..]

    # Prepare output of PatRec
    recognized_tracks = {}
    i_track = 0
    for atrack_combo in recognized_tracks_combo:

        hits_y12 = atrack_combo['hits_y12']
        hits_stereo12 = atrack_combo['hits_stereo12']
        hits_y34 = atrack_combo['hits_y34']
        hits_stereo34 = atrack_combo['hits_stereo34']


        if len(hits_y12) >= min_hits and len(hits_stereo12) >= min_hits and len(hits_y34) >= min_hits and len(hits_stereo34) >= min_hits:
            atrack = {'y12': hits_y12, 'stereo12': hits_stereo12, 'y34': hits_y34, 'stereo34': hits_stereo34}
            recognized_tracks[i_track] = atrack
            i_track += 1



    return recognized_tracks


def fast_hough_pat_rec_y_view(SmearedHits, min_hits):
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

    long_recognized_tracks = []

    # Take 2 hits as a track seed
    for ahit1 in SmearedHits:
        for ahit2 in SmearedHits:

            if ahit1['z'] >= ahit2['z']:
                continue
            if ahit1['detID'] == ahit2['detID']:
                continue

            k_seed = 1. * (ahit2['ytop'] - ahit1['ytop']) / (ahit2['z'] - ahit1['z'])
            b_seed = ahit1['ytop'] - k_seed * ahit1['z']

            if abs(k_seed) > 1:
                continue

            atrack = {}
            atrack['hits_y'] = [ahit1, ahit2]
            atrack_layers = [ahit1['detID'] // 10000, ahit2['detID'] // 10000]

            # Add new hits to the seed
            for ahit3 in SmearedHits:

                if ahit3['detID'] == ahit1['detID'] or ahit3['detID'] == ahit2['detID']:
                    continue

                layer3 = ahit3['detID'] // 10000
                if layer3 in atrack_layers:
                    continue

                in_bin = hit_in_bin(ahit3['z'], ahit3['ytop'], k_seed, b_seed, k_size=0.7/2000 * r_scale, b_size=1700./1000 * r_scale)
                if in_bin:
                    atrack['hits_y'].append(ahit3)
                    atrack_layers.append(layer3)

            if len(atrack['hits_y']) >= min_hits:
                long_recognized_tracks.append(atrack)

    # Remove clones
    recognized_tracks = reduce_clones_using_one_track_per_hit(long_recognized_tracks, min_hits)

    # Track fit
    for atrack in recognized_tracks:
        z_coords = [ahit['z'] for ahit in atrack['hits_y']]
        y_coords = [ahit['ytop'] for ahit in atrack['hits_y']]
        [atrack['k_y'], atrack['b_y']] = np.polyfit(z_coords, y_coords, deg=1)

    return recognized_tracks



def fast_hough_pat_rec_stereo_views(SmearedHits_stereo, recognized_tracks_y, min_hits):

    ### PatRec in stereo
    recognized_tracks_stereo = []
    used_hits = []

    for atrack_y in recognized_tracks_y:

        k_y = atrack_y['k_y']
        b_y = atrack_y['b_y']

        # Get hit zx projections
        for ahit in SmearedHits_stereo:
            x_center  = get_zy_projection(ahit['z'], ahit['ytop'], ahit['xtop'],ahit['ybot'], ahit['xbot'], k_y, b_y)
            ahit['zx_projection'] = x_center

        long_recognized_tracks_stereo = []

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

                if abs(ahit1['zx_projection']) > 300 or abs(ahit2['zx_projection']) > 300:
                    continue

                k_seed = 1. * (ahit2['zx_projection'] - ahit1['zx_projection']) / (ahit2['z'] - ahit1['z'])
                b_seed = ahit1['zx_projection'] - k_seed * ahit1['z']

                atrack_stereo = {}
                atrack_stereo['hits_stereo'] = [ahit1, ahit2]
                atrack_stereo_layers = [ahit1['detID'] // 10000, ahit2['detID'] // 10000]

                for ahit3 in SmearedHits_stereo:

                    if ahit3['digiHit'] == ahit1['digiHit'] or ahit3['digiHit'] == ahit2['digiHit']:
                        continue
                    if ahit3['digiHit'] in used_hits:
                        continue

                    if abs(ahit3['zx_projection']) > 300:
                        continue

                    layer3 = ahit3['detID'] // 10000
                    if layer3 in atrack_stereo_layers:
                        continue

                    in_bin = hit_in_bin(ahit3['z'], ahit3['zx_projection'], k_seed, b_seed, k_size=0.6/200 * r_scale, b_size=1000./70 * r_scale)
                    if in_bin:
                        atrack_stereo['hits_stereo'].append(ahit3)
                        atrack_stereo_layers.append(layer3)

                if len(atrack_stereo['hits_stereo']) >= min_hits:
                    long_recognized_tracks_stereo.append(atrack_stereo)


        # Remove clones
        max_track = None
        max_n_hits = -999

        for atrack_stereo in long_recognized_tracks_stereo:
            if len(atrack_stereo['hits_stereo']) > max_n_hits:
                max_track = atrack_stereo
                max_n_hits = len(atrack_stereo['hits_stereo'])

        atrack = {}
        atrack['hits_y'] = atrack_y['hits_y']
        atrack['k_y'] = atrack_y['k_y']
        atrack['b_y'] = atrack_y['b_y']
        atrack['hits_stereo'] = []

        if max_track is not None:
            atrack['hits_stereo'] = max_track['hits_stereo']
            for ahit in max_track['hits_stereo']:
                used_hits.append(ahit['digiHit'])

        recognized_tracks_stereo.append(atrack)

    return recognized_tracks_stereo



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


########################################################################################################################
##
## Artificial Retina
##
########################################################################################################################

from scipy.optimize import minimize

def artificial_retina_pattern_recognition(SmearedHits, ShipGeo):
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

    recognized_tracks = {}

    if len(SmearedHits) > 500:
        print "Too large hits in the event!"
        return recognized_tracks

    min_hits = 3

    #### Separate hits
    SmearedHits_12y, SmearedHits_12stereo, SmearedHits_34y, SmearedHits_34stereo = hits_split(SmearedHits)

    #### PatRec in 12y
    recognized_tracks_y12 = artificial_retina_pat_rec_y_view(SmearedHits_12y, min_hits)
    # recognized_tracks_y12 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo12
    #recognized_tracks_12 = pat_rec_stereo_views(SmearedHits_12stereo, recognized_tracks_y12, min_hits)
    recognized_tracks_12 = artificial_retina_pat_rec_stereo_views(SmearedHits_12stereo, recognized_tracks_y12, min_hits)
    # recognized_tracks_12 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    #### PatRec in 34y
    recognized_tracks_y34 = artificial_retina_pat_rec_y_view(SmearedHits_34y, min_hits)
    # recognized_tracks_y34 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo34
    #recognized_tracks_34 = pat_rec_stereo_views(SmearedHits_34stereo, recognized_tracks_y34, min_hits)
    recognized_tracks_34 = artificial_retina_pat_rec_stereo_views(SmearedHits_34stereo, recognized_tracks_y34, min_hits)
    # recognized_tracks_34 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### Combination of tracks before and after the magnet
    recognized_tracks_combo = tracks_combination_using_extrapolation(recognized_tracks_12, recognized_tracks_34, ShipGeo.Bfield.z)
    # recognized_tracks_combo = [{'hits_y12': [hit1, hit2, ...], 'hits_stereo12': [hit1, hit2, ...],
    #                             'hits_y34': [hit1, hit2, ...], 'hits_stereo34': [hit1, hit2, ...]}, {..}, ..]

    # Prepare output of PatRec
    recognized_tracks = {}
    i_track = 0
    for atrack_combo in recognized_tracks_combo:

        hits_y12 = atrack_combo['hits_y12']
        hits_stereo12 = atrack_combo['hits_stereo12']
        hits_y34 = atrack_combo['hits_y34']
        hits_stereo34 = atrack_combo['hits_stereo34']


        if len(hits_y12) >= min_hits and len(hits_stereo12) >= min_hits and len(hits_y34) >= min_hits and len(hits_stereo34) >= min_hits:
            atrack = {'y12': hits_y12, 'stereo12': hits_stereo12, 'y34': hits_y34, 'stereo34': hits_stereo34}
            recognized_tracks[i_track] = atrack
            i_track += 1



    return recognized_tracks


def artificial_retina_pat_rec_y_view(SmearedHits, min_hits):
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

    long_recognized_tracks = []
    used_hits = np.zeros(len(SmearedHits))

    hits_z = np.array([ahit['z'] for ahit in SmearedHits])
    hits_y = np.array([ahit['ytop'] for ahit in SmearedHits])

    for i in range(len(SmearedHits)):

        hits_z_unused = hits_z[used_hits == 0]
        hits_y_unused = hits_y[used_hits == 0]

        sigma=1. * r_scale
        best_seed_params = get_best_seed(hits_z_unused, hits_y_unused, sigma, sample_weight=None)

        res = minimize(retina_func, best_seed_params, args = (hits_z_unused, hits_y_unused, sigma, None), method='BFGS',
                       jac=retina_grad, options={'gtol': 1e-6, 'disp': False, 'maxiter': 5})
        [k_seed_upd, b_seed_upd] = res.x

        atrack = {}
        atrack['hits_y'] = []
        atrack_layers = []
        hit_ids = []

        # Add new hits to the seed
        for i_hit3 in range(len(SmearedHits)):

            if used_hits[i_hit3] == 1:
                continue

            ahit3 = SmearedHits[i_hit3]
            layer3 = ahit3['detID'] // 10000
            if layer3 in atrack_layers:
                continue

            in_bin = hit_in_window(ahit3['z'], ahit3['ytop'], k_seed_upd, b_seed_upd, window_width=1.4 * r_scale)
            if in_bin:
                atrack['hits_y'].append(ahit3)
                atrack_layers.append(layer3)
                hit_ids.append(i_hit3)

        if len(atrack['hits_y']) >= min_hits:
            long_recognized_tracks.append(atrack)
            used_hits[hit_ids] = 1
        else:
            break

    # Remove clones
    recognized_tracks = reduce_clones_using_one_track_per_hit(long_recognized_tracks, min_hits)

    # Track fit
    for atrack in recognized_tracks:
        z_coords = [ahit['z'] for ahit in atrack['hits_y']]
        y_coords = [ahit['ytop'] for ahit in atrack['hits_y']]
        [atrack['k_y'], atrack['b_y']] = np.polyfit(z_coords, y_coords, deg=1)

    return recognized_tracks



def artificial_retina_pat_rec_stereo_views(SmearedHits_stereo, recognized_tracks_y, min_hits):

    ### PatRec in stereo
    recognized_tracks_stereo = []
    used_hits = []

    for atrack_y in recognized_tracks_y:

        k_y = atrack_y['k_y']
        b_y = atrack_y['b_y']

        # Get hit zx projections
        for ahit in SmearedHits_stereo:
            x_center  = get_zy_projection(ahit['z'], ahit['ytop'], ahit['xtop'],ahit['ybot'], ahit['xbot'], k_y, b_y)
            ahit['zx_projection'] = x_center

        long_recognized_tracks_stereo = []
        hits_z = []
        hits_x = []

        for ahit in SmearedHits_stereo:
            if ahit['digiHit'] in used_hits:
                continue
            if abs(ahit['zx_projection']) > 300:
                continue
            hits_z.append(ahit['z'])
            hits_x.append(ahit['zx_projection'])
        hits_z = np.array(hits_z)
        hits_x = np.array(hits_x)

        sigma=15. * r_scale
        best_seed_params = get_best_seed(hits_z, hits_x, sigma, sample_weight=None)

        res = minimize(retina_func, best_seed_params, args = (hits_z, hits_x, sigma, None), method='BFGS',
                       jac=retina_grad, options={'gtol': 1e-6, 'disp': False, 'maxiter': 5})
        [k_seed_upd, b_seed_upd] = res.x

        atrack_stereo = {}
        atrack_stereo['hits_stereo'] = []
        atrack_stereo_layers = []

        for ahit3 in SmearedHits_stereo:

            if ahit3['digiHit'] in used_hits:
                continue

            if abs(ahit3['zx_projection']) > 300:
                continue

            layer3 = ahit3['detID'] // 10000
            if layer3 in atrack_stereo_layers:
                continue

            in_bin = hit_in_window(ahit3['z'], ahit3['zx_projection'], k_seed_upd, b_seed_upd, window_width=15. * r_scale)
            if in_bin:
                atrack_stereo['hits_stereo'].append(ahit3)
                atrack_stereo_layers.append(layer3)

        if len(atrack_stereo['hits_stereo']) >= min_hits:
            long_recognized_tracks_stereo.append(atrack_stereo)


        # Remove clones
        max_track = None
        max_n_hits = -999

        for atrack_stereo in long_recognized_tracks_stereo:
            if len(atrack_stereo['hits_stereo']) > max_n_hits:
                max_track = atrack_stereo
                max_n_hits = len(atrack_stereo['hits_stereo'])

        atrack = {}
        atrack['hits_y'] = atrack_y['hits_y']
        atrack['k_y'] = atrack_y['k_y']
        atrack['b_y'] = atrack_y['b_y']
        atrack['hits_stereo'] = []

        if max_track is not None:
            atrack['hits_stereo'] = max_track['hits_stereo']
            for ahit in max_track['hits_stereo']:
                used_hits.append(ahit['digiHit'])

        recognized_tracks_stereo.append(atrack)

    return recognized_tracks_stereo


def get_best_seed(x, y, sigma, sample_weight=None):

    best_retina_val = 0
    best_seed_params = [0, 0]

    for i_1 in range(len(x)-1):
        for i_2 in range(i_1+1, len(x)):

            if x[i_1] >= x[i_2]:
                continue

            seed_k = (y[i_2] - y[i_1]) / (x[i_2] - x[i_1] + 10**-6)
            seed_b = y[i_1] - seed_k * x[i_1]

            retina_val = retina_func([seed_k, seed_b], x, y, sigma, sample_weight)

            if retina_val < best_retina_val:
                best_retina_val = retina_val
                best_seed_params = [seed_k, seed_b]

    return best_seed_params


def retina_func(track_prams, x, y, sigma, sample_weight=None):
    """
    Calculates the artificial retina function value.
    Parameters
    ----------
    track_prams : array-like
        Track parameters [k, b].
    x : array-like
        Array of x coordinates of hits.
    y : array-like
        Array of x coordinates of hits.
    sigma : float
        Standard deviation of hit form a track.
    sample_weight : array-like
        Hit weights used during the track fit.
    Retunrs
    -------
    retina : float
        Negative value of the artificial retina function.
    """

    rs = track_prams[0] * x + track_prams[1] - y

    if sample_weight == None:
        exps = np.exp(- (rs/sigma)**2)
    else:
        exps = np.exp(- (rs/sigma)**2) * sample_weight

    retina = exps.sum()

    return -retina



def retina_grad(track_prams, x, y, sigma, sample_weight=None):
    """
    Calculates the artificial retina gradient.
    Parameters
    ----------
    track_prams : array-like
        Track parameters [k, b].
    x : array-like
        Array of x coordinates of hits.
    y : array-like
        Array of x coordinates of hits.
    sigma : float
        Standard deviation of hit form a track.
    sample_weight : array-like
        Hit weights used during the track fit.
    Retunrs
    -------
    retina : float
        Negative value of the artificial retina gradient.
    """

    rs = track_prams[0] * x + track_prams[1] - y

    if sample_weight == None:
        exps = np.exp(- (rs/sigma)**2)
    else:
        exps = np.exp(- (rs/sigma)**2) * sample_weight

    dks = - 2.*rs / sigma**2 * exps * x
    dbs = - 2.*rs / sigma**2 * exps

    return -np.array([dks.sum(), dbs.sum()])


########################################################################################################################
##
## Triplets Classifier V0
##
########################################################################################################################

def triplets_v0_pattern_recognition(SmearedHits, ShipGeo):
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

    recognized_tracks = {}

    if len(SmearedHits) > 500:
        print "Too large hits in the event!"
        return recognized_tracks

    min_hits = 3

    #### Separate hits
    SmearedHits_12y, SmearedHits_12stereo, SmearedHits_34y, SmearedHits_34stereo = hits_split(SmearedHits)

    #### PatRec in 12y
    recognized_tracks_y12 = triplets_v0_pat_rec_view(SmearedHits_12y, min_hits)
    # recognized_tracks_y12 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo12
    recognized_tracks_12 = pat_rec_stereo_views(SmearedHits_12stereo, recognized_tracks_y12, min_hits)
    # recognized_tracks_12 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    #### PatRec in 34y
    recognized_tracks_y34 = triplets_v0_pat_rec_view(SmearedHits_34y, min_hits)
    # recognized_tracks_y34 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo34
    recognized_tracks_34 = pat_rec_stereo_views(SmearedHits_34stereo, recognized_tracks_y34, min_hits)
    # recognized_tracks_34 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### Combination of tracks before and after the magnet
    recognized_tracks_combo = tracks_combination_using_extrapolation(recognized_tracks_12, recognized_tracks_34, ShipGeo.Bfield.z)
    # recognized_tracks_combo = [{'hits_y12': [hit1, hit2, ...], 'hits_stereo12': [hit1, hit2, ...],
    #                             'hits_y34': [hit1, hit2, ...], 'hits_stereo34': [hit1, hit2, ...]}, {..}, ..]

    # Prepare output of PatRec
    recognized_tracks = {}
    i_track = 0
    for atrack_combo in recognized_tracks_combo:

        hits_y12 = atrack_combo['hits_y12']
        hits_stereo12 = atrack_combo['hits_stereo12']
        hits_y34 = atrack_combo['hits_y34']
        hits_stereo34 = atrack_combo['hits_stereo34']


        if len(hits_y12) >= min_hits and len(hits_stereo12) >= min_hits and len(hits_y34) >= min_hits and len(hits_stereo34) >= min_hits:
            atrack = {'y12': hits_y12, 'stereo12': hits_stereo12, 'y34': hits_y34, 'stereo34': hits_stereo34}
            recognized_tracks[i_track] = atrack
            i_track += 1



    return recognized_tracks


def triplets_v0_pat_rec_view(SmearedHits, min_hits):
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

    z_hits = [ahit['z'] for ahit in SmearedHits]
    z_sorted_indeces = np.argsort(z_hits)

    SmearedHits_ordered = np.array(SmearedHits)[z_sorted_indeces]

    triplet_features = []
    triplet_hit_ids = []
    triplet_seeds = []
    triplet_dists = []
    seed_id = -1

    # Take 2 hits as a track seed
    for i_hit1 in range(len(SmearedHits_ordered)-1):
        ahit1 = SmearedHits_ordered[i_hit1]

        for i_hit3 in range(len(SmearedHits_ordered)-1, i_hit1, -1):
            ahit3 = SmearedHits_ordered[i_hit3]

            if ahit1['z'] >= ahit3['z']:
                continue

            seed_id += 1

            for i_hit2 in range(len(SmearedHits_ordered)):
                ahit2 = SmearedHits_ordered[i_hit2]

                if i_hit2 == i_hit1 or i_hit2 == i_hit3:
                    continue
                if ahit1['z'] == ahit2['z'] or ahit2['z'] == ahit3['z']:
                    continue

                # if ahit1['z'] < ahit2['z'] and ahit2['z'] < ahit3['z']:
                #     one_triplet_dist = get_triplet_dist(ahit1, ahit2, ahit3)
                # elif ahit2['z'] < ahit1['z'] and ahit1['z'] < ahit3['z']:
                #     one_triplet_dist = get_triplet_dist(ahit2, ahit1, ahit3)
                # elif ahit1['z'] < ahit3['z'] and ahit3['z'] < ahit2['z']:
                #     one_triplet_dist = get_triplet_dist(ahit1, ahit3, ahit2)
                # else:
                #     continue
                one_triplet_dist = get_triplet_dist(ahit1, ahit2, ahit3)

                triplet_dists.append(one_triplet_dist)
                triplet_hit_ids.append([i_hit1, i_hit2, i_hit3])
                triplet_seeds.append(seed_id)

    if len(triplet_dists) == 0:
        return []

    long_recognized_tracks = []

    current_seed_id = -1
    atrack = {}
    atrack['hits_y'] = []
    atrack_layers = []

    for i_triplet in range(len(triplet_hit_ids)):

        dist = triplet_dists[i_triplet]
        seed_id = triplet_seeds[i_triplet]
        i_hit1, i_hit2, i_hit3 = triplet_hit_ids[i_triplet]

        if seed_id != current_seed_id:

            if len(atrack['hits_y']) >= min_hits:
                long_recognized_tracks.append(atrack)

            current_seed_id = seed_id
            ahit1 = SmearedHits_ordered[i_hit1]
            ahit3 = SmearedHits_ordered[i_hit3]

            atrack = {}
            atrack['hits_y'] = [ahit1, ahit3]
            atrack_layers = [ahit1['detID'] // 10000, ahit3['detID'] // 10000]

        ahit2 = SmearedHits_ordered[i_hit2]

        layer2 = ahit2['detID'] // 10000
        if layer2 in atrack_layers:
            continue

        if dist < 1.4:
            atrack['hits_y'].append(ahit2)
            atrack_layers.append(layer2)

    # Remove clones
    recognized_tracks = reduce_clones_using_one_track_per_hit(long_recognized_tracks, min_hits)

    # Track fit
    for atrack in recognized_tracks:
        z_coords = [ahit['z'] for ahit in atrack['hits_y']]
        y_coords = [ahit['ytop'] for ahit in atrack['hits_y']]
        [atrack['k_y'], atrack['b_y']] = np.polyfit(z_coords, y_coords, deg=1)

    return recognized_tracks


def get_triplet_dist(hit1, hit2, hit3):

    z1, z2, z3 = hit1['z'], hit2['z'], hit3['z']
    y1, y2, y3 = hit1['ytop'], hit2['ytop'], hit3['ytop']

    dist = get_dist(y1, y2, y3, z1, z2, z3)

    return dist

# def get_dist(y1, y2, y3, z1, z2, z3):
#
#     k = (y3 - y1) / (z3 - z1 + 10**-6)
#     b = y1 - k * z1
#
#     dist = np.abs(y2 - (k * z2 + b))
#
#     return dist


########################################################################################################################
##
## Triplets Classifier V1
##
########################################################################################################################

def triplets_v1_pattern_recognition(SmearedHits, ShipGeo):
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

    recognized_tracks = {}

    if len(SmearedHits) > 500:
        print "Too large hits in the event!"
        return recognized_tracks

    min_hits = 3

    #### Separate hits
    SmearedHits_12y, SmearedHits_12stereo, SmearedHits_34y, SmearedHits_34stereo = hits_split(SmearedHits)

    #### PatRec in 12y
    recognized_tracks_y12 = triplets_v1_pat_rec_view(SmearedHits_12y, min_hits)
    # recognized_tracks_y12 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo12
    recognized_tracks_12 = pat_rec_stereo_views(SmearedHits_12stereo, recognized_tracks_y12, min_hits)
    # recognized_tracks_12 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    #### PatRec in 34y
    recognized_tracks_y34 = triplets_v1_pat_rec_view(SmearedHits_34y, min_hits)
    # recognized_tracks_y34 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo34
    recognized_tracks_34 = pat_rec_stereo_views(SmearedHits_34stereo, recognized_tracks_y34, min_hits)
    # recognized_tracks_34 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### Combination of tracks before and after the magnet
    recognized_tracks_combo = tracks_combination_using_extrapolation(recognized_tracks_12, recognized_tracks_34, ShipGeo.Bfield.z)
    # recognized_tracks_combo = [{'hits_y12': [hit1, hit2, ...], 'hits_stereo12': [hit1, hit2, ...],
    #                             'hits_y34': [hit1, hit2, ...], 'hits_stereo34': [hit1, hit2, ...]}, {..}, ..]

    # Prepare output of PatRec
    recognized_tracks = {}
    i_track = 0
    for atrack_combo in recognized_tracks_combo:

        hits_y12 = atrack_combo['hits_y12']
        hits_stereo12 = atrack_combo['hits_stereo12']
        hits_y34 = atrack_combo['hits_y34']
        hits_stereo34 = atrack_combo['hits_stereo34']


        if len(hits_y12) >= min_hits and len(hits_stereo12) >= min_hits and len(hits_y34) >= min_hits and len(hits_stereo34) >= min_hits:
            atrack = {'y12': hits_y12, 'stereo12': hits_stereo12, 'y34': hits_y34, 'stereo34': hits_stereo34}
            recognized_tracks[i_track] = atrack
            i_track += 1



    return recognized_tracks


def triplets_v1_pat_rec_view(SmearedHits, min_hits):
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

    z_hits = [ahit['z'] for ahit in SmearedHits]
    z_sorted_indeces = np.argsort(z_hits)

    SmearedHits_ordered = np.array(SmearedHits)[z_sorted_indeces]

    triplet_features = []
    triplet_hit_ids = []
    triplet_seeds = []
    triplet_probas = []
    seed_id = -1

    # Take 2 hits as a track seed
    for i_hit1 in range(len(SmearedHits_ordered)-1):
        ahit1 = SmearedHits_ordered[i_hit1]

        for i_hit3 in range(len(SmearedHits_ordered)-1, i_hit1, -1):
            ahit3 = SmearedHits_ordered[i_hit3]

            if ahit1['z'] >= ahit3['z']:
                continue

            seed_id += 1

            for i_hit2 in range(len(SmearedHits_ordered)):
                ahit2 = SmearedHits_ordered[i_hit2]

                # if ahit1['z'] >= ahit2['z']:
                #     continue
                # if ahit2['z'] >= ahit3['z']:
                #     continue

                if i_hit2 == i_hit1 or i_hit2 == i_hit3:
                    continue
                if ahit1['z'] == ahit2['z'] or ahit2['z'] == ahit3['z']:
                    continue

                # if ahit1['z'] < ahit2['z'] and ahit2['z'] < ahit3['z']:
                #     one_triplet_features = get_triplet_features(ahit1, ahit2, ahit3)
                # elif ahit2['z'] < ahit1['z'] and ahit1['z'] < ahit3['z']:
                #     one_triplet_features = get_triplet_features(ahit2, ahit1, ahit3)
                # elif ahit1['z'] < ahit3['z'] and ahit3['z'] < ahit2['z']:
                #     one_triplet_features = get_triplet_features(ahit1, ahit3, ahit2)
                # else:
                #     continue
                one_triplet_features = get_triplet_features(ahit1, ahit3, ahit2)

                #one_triplet_features = get_triplet_features(ahit1, ahit2, ahit3)
                #dist = get_dist(ahit1['ytop'], ahit2['ytop'], ahit3['ytop'], ahit1['z'], ahit2['z'], ahit3['z'])
                #triplet_probas.append(dist)

                triplet_features.append(one_triplet_features)
                triplet_hit_ids.append([i_hit1, i_hit2, i_hit3])
                triplet_seeds.append(seed_id)

    if len(triplet_features) == 0:
        return []

    triplet_probas = triplets_clf.predict_proba(triplet_features)[:, 1]


    long_recognized_tracks = []

    current_seed_id = -1
    atrack = {}
    atrack['hits_y'] = []
    atrack_layers = []

    for i_triplet in range(len(triplet_hit_ids)):

        proba = triplet_probas[i_triplet]
        seed_id = triplet_seeds[i_triplet]
        i_hit1, i_hit2, i_hit3 = triplet_hit_ids[i_triplet]

        if seed_id != current_seed_id:

            if len(atrack['hits_y']) >= min_hits:
                long_recognized_tracks.append(atrack)

            current_seed_id = seed_id
            ahit1 = SmearedHits_ordered[i_hit1]
            ahit3 = SmearedHits_ordered[i_hit3]

            atrack = {}
            atrack['hits_y'] = [ahit1, ahit3]
            atrack_layers = [ahit1['detID'] // 10000, ahit3['detID'] // 10000]

        ahit2 = SmearedHits_ordered[i_hit2]

        layer2 = ahit2['detID'] // 10000
        if layer2 in atrack_layers:
            continue

        #if proba < 1.4:
        if proba > 0.8:
            atrack['hits_y'].append(ahit2)
            atrack_layers.append(layer2)

    # Remove clones
    recognized_tracks = reduce_clones_using_one_track_per_hit(long_recognized_tracks, min_hits)

    # Track fit
    for atrack in recognized_tracks:
        z_coords = [ahit['z'] for ahit in atrack['hits_y']]
        y_coords = [ahit['ytop'] for ahit in atrack['hits_y']]
        [atrack['k_y'], atrack['b_y']] = np.polyfit(z_coords, y_coords, deg=1)

    return recognized_tracks


def get_triplet_features(hit1, hit2, hit3):

    z1, z2, z3 = hit1['z'], hit2['z'], hit3['z']
    y1, y2, y3 = hit1['ytop'], hit2['ytop'], hit3['ytop']

    dz1, dz2, dy1, dy2 = get_deltas(y1, y2, y3, z1, z2, z3)
    cos = get_cos(y1, y2, y3, z1, z2, z3)
    dist = get_dist(y1, y2, y3, z1, z2, z3)
    k1, k2, k3 = get_slopes(y1, y2, y3, z1, z2, z3)

    triplet_fetures = [dz1, dz2, dy1, dy2, cos, dist, k1, k2, k3]

    return triplet_fetures



def get_cos(y1, y2, y3, z1, z2, z3):

    dy1, dy2 = (y1 - y3 + 10**-6), (y2 - y3 + 10**-6)
    dz1, dz2 = (z1 - z3 + 10**-6), (z2 - z3 + 10**-6)

    cos = (dz1*dz2 + dy1*dy2) / np.sqrt((dy1**2 + dz1**2)*(dy2**2 + dz2**2))

    return np.array(cos)


def get_slopes(y1, y2, y3, z1, z2, z3):

    dy1, dy2, dy3 = (y1 - y2 + 10**-6), (y3 - y2 + 10**-6), (y3 - y1 + 10**-6)
    dz1, dz2, dz3 = (z1 - z2 + 10**-6), (z3 - z2 + 10**-6), (z3 - z1 + 10**-6)

    k1 = dy1/dz1
    k2 = dy2/dz2
    k3 = dy3/dz3

    return k1, k2, k3


def get_deltas(y1, y2, y3, z1, z2, z3):

    dz1 = z2 - z1
    dz2 = z3 - z1
    dy1 = y2 - y1
    dy2 = y3 - y1

    return dz1, dz2, dy1, dy2

def get_dist(y1, y2, y3, z1, z2, z3):

    k = (y2 - y1) / (z2 - z1 + 10**-6)
    b = y1 - k * z1

    dist = np.abs(y3 - (k * z3 + b))

    return dist


########################################################################################################################
##
## Triplets Classifier V2
##
########################################################################################################################

def triplets_v2_pattern_recognition(SmearedHits, ShipGeo):
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

    recognized_tracks = {}

    if len(SmearedHits) > 500:
        print "Too large hits in the event!"
        return recognized_tracks

    min_hits = 3

    #### Separate hits
    SmearedHits_12y, SmearedHits_12stereo, SmearedHits_34y, SmearedHits_34stereo = hits_split(SmearedHits)

    #### PatRec in 12y
    recognized_tracks_y12 = triplets_v2_pat_rec_view(SmearedHits_12y, min_hits)
    # recognized_tracks_y12 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo12
    recognized_tracks_12 = pat_rec_stereo_views(SmearedHits_12stereo, recognized_tracks_y12, min_hits)
    # recognized_tracks_12 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    #### PatRec in 34y
    recognized_tracks_y34 = triplets_v2_pat_rec_view(SmearedHits_34y, min_hits)
    # recognized_tracks_y34 = [{'hits_y': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### PatRec in stereo34
    recognized_tracks_34 = pat_rec_stereo_views(SmearedHits_34stereo, recognized_tracks_y34, min_hits)
    # recognized_tracks_34 = [{'hits_y': [hit1, hit2, ...], 'hits_stereo': [hit1, hit2, ...], 'k_y': float, 'b_y': float}, {...}, ...]

    ### Combination of tracks before and after the magnet
    recognized_tracks_combo = tracks_combination_using_extrapolation(recognized_tracks_12, recognized_tracks_34, ShipGeo.Bfield.z)
    # recognized_tracks_combo = [{'hits_y12': [hit1, hit2, ...], 'hits_stereo12': [hit1, hit2, ...],
    #                             'hits_y34': [hit1, hit2, ...], 'hits_stereo34': [hit1, hit2, ...]}, {..}, ..]

    # Prepare output of PatRec
    recognized_tracks = {}
    i_track = 0
    for atrack_combo in recognized_tracks_combo:

        hits_y12 = atrack_combo['hits_y12']
        hits_stereo12 = atrack_combo['hits_stereo12']
        hits_y34 = atrack_combo['hits_y34']
        hits_stereo34 = atrack_combo['hits_stereo34']


        if len(hits_y12) >= min_hits and len(hits_stereo12) >= min_hits and len(hits_y34) >= min_hits and len(hits_stereo34) >= min_hits:
            atrack = {'y12': hits_y12, 'stereo12': hits_stereo12, 'y34': hits_y34, 'stereo34': hits_stereo34}
            recognized_tracks[i_track] = atrack
            i_track += 1



    return recognized_tracks


def triplets_v2_pat_rec_view(SmearedHits, min_hits):
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

    z_hits = [ahit['z'] for ahit in SmearedHits]
    z_sorted_indeces = np.argsort(z_hits)

    SmearedHits_ordered = np.array(SmearedHits)[z_sorted_indeces]

    triplet_features = []
    triplet_hit_ids = []
    triplet_seeds = []
    triplet_dists = []
    seed_id = -1

    # Take 2 hits as a track seed
    for i_hit1 in range(len(SmearedHits_ordered)-1):
        ahit1 = SmearedHits_ordered[i_hit1]

        for i_hit3 in range(len(SmearedHits_ordered)-1, i_hit1, -1):
            ahit3 = SmearedHits_ordered[i_hit3]

            seed_id += 1

            for i_hit2 in range(i_hit1+1, i_hit3):
                ahit2 = SmearedHits_ordered[i_hit2]

                if ahit1['z'] >= ahit2['z']:
                    continue
                if ahit2['z'] >= ahit3['z']:
                    continue

                one_triplet_dist = get_triplet_dist(ahit1, ahit2, ahit3)

                triplet_dists.append(one_triplet_dist)
                triplet_hit_ids.append([i_hit1, i_hit2, i_hit3])
                triplet_seeds.append(seed_id)

    if len(triplet_dists) == 0:
        return []

    long_recognized_tracks = []

    # Create graph
    graph = np.zeros((len(SmearedHits_ordered), len(SmearedHits_ordered)))

    # Update graph
    for i_triplet in range(len(triplet_hit_ids)):
        dist = triplet_dists[i_triplet]
        i_hit1, i_hit2, i_hit3 = triplet_hit_ids[i_triplet]
        if dist < 1.4:
            if graph[i_hit1, i_hit2] != -1:
                graph[i_hit1, i_hit2] += 1
            if graph[i_hit2, i_hit3] != -1:
                graph[i_hit2, i_hit3] += 1
            graph[i_hit1, i_hit3] = -1

    # Seed search
    seeds = []
    for i_hit in range(len(SmearedHits_ordered)):
        is_seed = 1
        for node in graph[:, i_hit]:
            if node != 0:
                is_seed = 0
                break
        if is_seed:
            seeds.append(i_hit)

    #print "seeds: ", seeds

    # Look for track candidates
    for i_hit in seeds:
        paths = find_all_paths(graph, i_hit, path=[])
         #print "paths: ", paths
        for apath in paths:
            atrack = {}
            atrack['hits_y'] = []
            for i_path_hit in apath:
                atrack['hits_y'].append(SmearedHits_ordered[i_path_hit])
            if len(atrack['hits_y']) >= min_hits:
                long_recognized_tracks.append(atrack)


    # Remove clones
    recognized_tracks = reduce_clones_using_one_track_per_hit(long_recognized_tracks, min_hits)

    # Track fit
    for atrack in recognized_tracks:
        z_coords = [ahit['z'] for ahit in atrack['hits_y']]
        y_coords = [ahit['ytop'] for ahit in atrack['hits_y']]
        [atrack['k_y'], atrack['b_y']] = np.polyfit(z_coords, y_coords, deg=1)

    return recognized_tracks


def find_all_paths(graph, start, path=[]):

    path = path + [start]

    if np.sum(graph[start] > 0) == 0:
        return [path]

    paths = []
    for node in range(len(graph[start])):
        if graph[start][node] >= 1:
            if node not in path:
                newpaths = find_all_paths(graph, node, path)
                for newpath in newpaths:
                    paths.append(newpath)
    return paths


def get_triplet_dist(hit1, hit2, hit3):

    z1, z2, z3 = hit1['z'], hit2['z'], hit3['z']
    y1, y2, y3 = hit1['ytop'], hit2['ytop'], hit3['ytop']

    dist = get_dist(y1, y2, y3, z1, z2, z3)

    return dist

# def get_dist(y1, y2, y3, z1, z2, z3):
#
#     k = (y3 - y1) / (z3 - z1 + 10**-6)
#     b = y1 - k * z1
#
#     dist = np.abs(y2 - (k * z2 + b))
#
#     return dist


########################################################################################################################
##
## The End of the PatRec Methods
##
########################################################################################################################



def hits_split(smeared_hits):
    """
    Split hits into groups of station views.

    Parameters:
    -----------
    SmearedHits : list
        Smeared hits. SmearedHits = [{'digiHit': key,
                                      'xtop': xtop, 'ytop': ytop, 'z': ztop,
                                      'xbot': xbot, 'ybot': ybot,
                                      'dist': dist2wire, 'detID': detID}, {...}, ...]
    """

    smeared_hits_12y = []
    smeared_hits_12stereo = []
    smeared_hits_34y = []
    smeared_hits_34stereo = []

    for i_hit in range(len(smeared_hits)):

        ahit = smeared_hits[i_hit]

        detID = ahit['detID']
        statnb, vnb, pnb, lnb, snb = decodeDetectorID(detID)
        is_y12 = ((statnb == 1) + (statnb == 2)) * ((vnb == 0) + (vnb == 3))
        is_stereo12 = ((statnb == 1) + (statnb == 2)) * ((vnb == 1) + (vnb == 2))
        is_y34 = ((statnb == 3) + (statnb == 4)) * ((vnb == 0) + (vnb == 3))
        is_stereo34 = ((statnb == 3) + (statnb == 4)) * ((vnb == 1) + (vnb == 2))

        if is_y12:
            smeared_hits_12y.append(ahit)
        if is_stereo12:
            smeared_hits_12stereo.append(ahit)
        if is_y34:
            smeared_hits_34y.append(ahit)
        if is_stereo34:
            smeared_hits_34stereo.append(ahit)

    return smeared_hits_12y, smeared_hits_12stereo, smeared_hits_34y, smeared_hits_34stereo


def reduce_clones_using_one_track_per_hit(recognized_tracks, min_hits=3):
    """
    Split hits into groups of station views.

    Parameters:
    -----------
    recognized_tracks : list
        Track hits. Tracks = [{'hits_y': [hit1, hit2, hit3, ...]}, {...}, ...]
    min_hits : int
        Minimal number of hits per track.
    """

    used_hits = []
    tracks_no_clones = []
    n_hits = [len(atrack['hits_y']) for atrack in recognized_tracks]

    for i_track in np.argsort(n_hits)[::-1]:

        atrack = recognized_tracks[i_track]
        new_track = {}
        new_track['hits_y'] = []

        for i_hit in range(len(atrack['hits_y'])):
            ahit = atrack['hits_y'][i_hit]
            if ahit['digiHit'] not in used_hits:
                new_track['hits_y'].append(ahit)

        if len(new_track['hits_y']) >= min_hits:
            tracks_no_clones.append(new_track)
            for ahit in new_track['hits_y']:
                used_hits.append(ahit['digiHit'])

    return tracks_no_clones


def tracks_combination_using_extrapolation(recognized_tracks_12, recognized_tracks_34, z_magnet):

    recognized_tracks_combo = []

    i_track_y12 = []
    i_track_y34 = []
    deltas_y = []

    for i_12 in range(len(recognized_tracks_12)):

        atrack_12 = recognized_tracks_12[i_12]
        y_center_y12 = atrack_12['k_y'] * z_magnet + atrack_12['b_y']

        for i_34 in range(len(recognized_tracks_34)):

            atrack_34 = recognized_tracks_34[i_34]
            y_center_y34 = atrack_34['k_y'] * z_magnet + atrack_34['b_y']

            i_track_y12.append(i_12)
            i_track_y34.append(i_34)
            deltas_y.append(abs(y_center_y12 - y_center_y34))

    max_dy = 50
    used_y12 = []
    used_y34 = []

    for i in np.argsort(deltas_y):

        dy = deltas_y[i]
        i_12 = i_track_y12[i]
        i_34 = i_track_y34[i]

        if (dy < max_dy) and (i_12 not in used_y12) and (i_34 not in used_y34):
            atrack = {}
            atrack['hits_y12'] = recognized_tracks_12[i_12]['hits_y']
            atrack['hits_stereo12'] = recognized_tracks_12[i_12]['hits_stereo']
            atrack['hits_y34'] = recognized_tracks_34[i_34]['hits_y']
            atrack['hits_stereo34'] = recognized_tracks_34[i_34]['hits_stereo']
            recognized_tracks_combo.append(atrack)
            used_y12.append(i_12)
            used_y34.append(i_34)

    for i_12 in range(len(recognized_tracks_12)):
        if i_12 not in used_y12:
            atrack = {}
            atrack['hits_y12'] = recognized_tracks_12[i_12]['hits_y']
            atrack['hits_stereo12'] = recognized_tracks_12[i_12]['hits_stereo']
            atrack['hits_y34'] = []
            atrack['hits_stereo34'] = []
            recognized_tracks_combo.append(atrack)

    for i_34 in range(len(recognized_tracks_34)):
        if i_34 not in used_y34:
            atrack = {}
            atrack['hits_y12'] = []
            atrack['hits_stereo12'] = []
            atrack['hits_y34'] = recognized_tracks_34[i_34]['hits_y']
            atrack['hits_stereo34'] = recognized_tracks_34[i_34]['hits_stereo']
            recognized_tracks_combo.append(atrack)
            recognized_tracks_combo.append(atrack)

    return recognized_tracks_combo



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


def pat_rec_stereo_views(SmearedHits_stereo, recognized_tracks_y, min_hits):

    ### PatRec in stereo
    recognized_tracks_stereo = []
    used_hits = []

    for atrack_y in recognized_tracks_y:

        k_y = atrack_y['k_y']
        b_y = atrack_y['b_y']

        # Get hit zx projections
        for ahit in SmearedHits_stereo:
            x_center  = get_zy_projection(ahit['z'], ahit['ytop'], ahit['xtop'],ahit['ybot'], ahit['xbot'], k_y, b_y)
            ahit['zx_projection'] = x_center

        long_recognized_tracks_stereo = []

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

                if abs(ahit1['zx_projection']) > 300 or abs(ahit2['zx_projection']) > 300:
                    continue

                k_seed = 1. * (ahit2['zx_projection'] - ahit1['zx_projection']) / (ahit2['z'] - ahit1['z'])
                b_seed = ahit1['zx_projection'] - k_seed * ahit1['z']

                atrack_stereo = {}
                atrack_stereo['hits_stereo'] = [ahit1, ahit2]
                atrack_stereo_layers = [ahit1['detID'] // 10000, ahit2['detID'] // 10000]

                for ahit3 in SmearedHits_stereo:

                    if ahit3['digiHit'] == ahit1['digiHit'] or ahit3['digiHit'] == ahit2['digiHit']:
                        continue
                    if ahit3['digiHit'] in used_hits:
                        continue

                    if abs(ahit3['zx_projection']) > 300:
                        continue

                    layer3 = ahit3['detID'] // 10000
                    if layer3 in atrack_stereo_layers:
                        continue

                    in_bin = hit_in_window(ahit3['z'], ahit3['zx_projection'], k_seed, b_seed, window_width=15. * r_scale)
                    if in_bin:
                        atrack_stereo['hits_stereo'].append(ahit3)
                        atrack_stereo_layers.append(layer3)

                if len(atrack_stereo['hits_stereo']) >= min_hits:
                    long_recognized_tracks_stereo.append(atrack_stereo)


        # Remove clones
        max_track = None
        max_n_hits = -999

        for atrack_stereo in long_recognized_tracks_stereo:
            if len(atrack_stereo['hits_stereo']) > max_n_hits:
                max_track = atrack_stereo
                max_n_hits = len(atrack_stereo['hits_stereo'])

        atrack = {}
        atrack['hits_y'] = atrack_y['hits_y']
        atrack['k_y'] = atrack_y['k_y']
        atrack['b_y'] = atrack_y['b_y']
        atrack['hits_stereo'] = []

        if max_track is not None:
            atrack['hits_stereo'] = max_track['hits_stereo']
            for ahit in max_track['hits_stereo']:
                used_hits.append(ahit['digiHit'])

        recognized_tracks_stereo.append(atrack)

    return recognized_tracks_stereo