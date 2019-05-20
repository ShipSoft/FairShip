__author__ = 'Mikhail Hushchyn'

import numpy as np

# Globals
ReconstructibleMCTracks = []
theTracks = []

r_scale = ShipGeo.strawtubes.InnerStrawDiameter / 1.975

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
    elif method == "FH":
        recognized_tracks = fast_hough_transform_pattern_recognition(smeared_hits, ship_geo)
    elif method == "AR":
        recognized_tracks = artificial_retina_pattern_recognition(smeared_hits, ship_geo)
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