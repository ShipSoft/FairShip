# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

__author__ = "Mikhail Hushchyn"

import logging

import global_variables
import numpy as np

logger = logging.getLogger(__name__)

# Globals
ReconstructibleMCTracks = []
theTracks = []

r_scale = 1.0
max_x = global_variables.ShipGeo.strawtubes_geo.width  # == 200 * u.cm


def initialize(fgeo) -> None:
    pass


def execute(smeared_hits, ship_geo, method: str = ""):
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

    logger.debug("PatRec input: %d smeared hits, method=%s", len(smeared_hits), method or "none")

    if method == "TemplateMatching":
        recognized_tracks = template_matching_pattern_recognition(smeared_hits, ship_geo)
    elif method == "FH":
        recognized_tracks = fast_hough_transform_pattern_recognition(smeared_hits, ship_geo)
    elif method == "AR":
        recognized_tracks = artificial_retina_pattern_recognition(smeared_hits, ship_geo)
    else:
        hits_y12, hits_stereo12, hits_y34, hits_stereo34 = hits_split(smeared_hits)
        atrack = {"y12": hits_y12, "stereo12": hits_stereo12, "y34": hits_y34, "stereo34": hits_stereo34}
        recognized_tracks[0] = atrack

    logger.debug("PatRec output: %d tracks", len(recognized_tracks))

    return recognized_tracks


def finalize() -> None:
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
        print("Too large hits in the event!")
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
    recognized_tracks_combo = tracks_combination_using_extrapolation(
        recognized_tracks_12, recognized_tracks_34, ShipGeo.Bfield.z
    )

    # Prepare output of PatRec
    recognized_tracks = _prepare_output(recognized_tracks_combo, min_hits)

    return recognized_tracks


def pat_rec_view(SmearedHits, min_hits: int):
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
    n_seeds_tried = 0
    n_seeds_slope_cut = 0

    # Take 2 hits as a track seed
    for ahit1 in SmearedHits:
        for ahit2 in SmearedHits:
            if ahit1["z"] >= ahit2["z"]:
                continue
            if ahit1["detID"] == ahit2["detID"]:
                continue

            n_seeds_tried += 1
            k_seed = 1.0 * (ahit2["ytop"] - ahit1["ytop"]) / (ahit2["z"] - ahit1["z"])
            b_seed = ahit1["ytop"] - k_seed * ahit1["z"]

            if abs(k_seed) > 1:
                n_seeds_slope_cut += 1
                continue

            atrack = {}
            atrack["hits_y"] = [ahit1, ahit2]
            atrack_layers = [ahit1["detID"] // 10000, ahit2["detID"] // 10000]

            # Add new hits to the seed
            for ahit3 in SmearedHits:
                if ahit3["detID"] == ahit1["detID"] or ahit3["detID"] == ahit2["detID"]:
                    continue

                layer3 = ahit3["detID"] // 10000
                if layer3 in atrack_layers:
                    continue

                in_bin = hit_in_window(ahit3["z"], ahit3["ytop"], k_seed, b_seed, window_width=1.4 * r_scale)
                if in_bin:
                    atrack["hits_y"].append(ahit3)
                    atrack_layers.append(layer3)

            if len(atrack["hits_y"]) >= min_hits:
                long_recognized_tracks.append(atrack)

    # Remove clones
    recognized_tracks = reduce_clones_using_one_track_per_hit(long_recognized_tracks, min_hits)

    logger.debug(
        "pat_rec_view: %d hits, %d seeds tried, %d cut by slope, %d tracks before clone removal, %d after",
        len(SmearedHits),
        n_seeds_tried,
        n_seeds_slope_cut,
        len(long_recognized_tracks),
        len(recognized_tracks),
    )

    # Track fit
    for atrack in recognized_tracks:
        z_coords = [ahit["z"] for ahit in atrack["hits_y"]]
        y_coords = [ahit["ytop"] for ahit in atrack["hits_y"]]
        [atrack["k_y"], atrack["b_y"]] = np.polyfit(z_coords, y_coords, deg=1)

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
        print("Too large hits in the event!")
        return recognized_tracks

    min_hits = 3

    #### Separate hits
    SmearedHits_12y, SmearedHits_12stereo, SmearedHits_34y, SmearedHits_34stereo = hits_split(SmearedHits)

    #### PatRec in 12y
    recognized_tracks_y12 = fast_hough_pat_rec_y_view(SmearedHits_12y, min_hits)

    ### PatRec in stereo12
    recognized_tracks_12 = fast_hough_pat_rec_stereo_views(SmearedHits_12stereo, recognized_tracks_y12, min_hits)

    #### PatRec in 34y
    recognized_tracks_y34 = fast_hough_pat_rec_y_view(SmearedHits_34y, min_hits)

    ### PatRec in stereo34
    recognized_tracks_34 = fast_hough_pat_rec_stereo_views(SmearedHits_34stereo, recognized_tracks_y34, min_hits)

    ### Combination of tracks before and after the magnet
    recognized_tracks_combo = tracks_combination_using_extrapolation(
        recognized_tracks_12, recognized_tracks_34, ShipGeo.Bfield.z
    )

    # Prepare output of PatRec
    recognized_tracks = _prepare_output(recognized_tracks_combo, min_hits)

    return recognized_tracks


def fast_hough_pat_rec_y_view(SmearedHits, min_hits: int):
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
    n_seeds_tried = 0
    n_seeds_slope_cut = 0

    # Take 2 hits as a track seed
    for ahit1 in SmearedHits:
        for ahit2 in SmearedHits:
            if ahit1["z"] >= ahit2["z"]:
                continue
            if ahit1["detID"] == ahit2["detID"]:
                continue

            n_seeds_tried += 1
            k_seed = 1.0 * (ahit2["ytop"] - ahit1["ytop"]) / (ahit2["z"] - ahit1["z"])
            b_seed = ahit1["ytop"] - k_seed * ahit1["z"]

            if abs(k_seed) > 1:
                n_seeds_slope_cut += 1
                continue

            atrack = {}
            atrack["hits_y"] = [ahit1, ahit2]
            atrack_layers = [ahit1["detID"] // 10000, ahit2["detID"] // 10000]

            # Add new hits to the seed
            for ahit3 in SmearedHits:
                if ahit3["detID"] == ahit1["detID"] or ahit3["detID"] == ahit2["detID"]:
                    continue

                layer3 = ahit3["detID"] // 10000
                if layer3 in atrack_layers:
                    continue

                in_bin = hit_in_bin(
                    ahit3["z"],
                    ahit3["ytop"],
                    k_seed,
                    b_seed,
                    k_size=0.7 / 2000 * r_scale,
                    b_size=1700.0 / 1000 * r_scale,
                )
                if in_bin:
                    atrack["hits_y"].append(ahit3)
                    atrack_layers.append(layer3)

            if len(atrack["hits_y"]) >= min_hits:
                long_recognized_tracks.append(atrack)

    # Remove clones
    recognized_tracks = reduce_clones_using_one_track_per_hit(long_recognized_tracks, min_hits)

    logger.debug(
        "fast_hough_y_view: %d hits, %d seeds tried, %d cut by slope, %d tracks before clone removal, %d after",
        len(SmearedHits),
        n_seeds_tried,
        n_seeds_slope_cut,
        len(long_recognized_tracks),
        len(recognized_tracks),
    )

    # Track fit
    for atrack in recognized_tracks:
        z_coords = [ahit["z"] for ahit in atrack["hits_y"]]
        y_coords = [ahit["ytop"] for ahit in atrack["hits_y"]]
        [atrack["k_y"], atrack["b_y"]] = np.polyfit(z_coords, y_coords, deg=1)

    return recognized_tracks


def fast_hough_pat_rec_stereo_views(SmearedHits_stereo, recognized_tracks_y, min_hits: int):
    ### PatRec in stereo
    recognized_tracks_stereo = []
    used_hits = []
    n_y_tracks_with_stereo = 0

    for atrack_y in recognized_tracks_y:
        k_y = atrack_y["k_y"]
        b_y = atrack_y["b_y"]

        # Get hit zx projections
        for ahit in SmearedHits_stereo:
            x_center = get_zy_projection(ahit["z"], ahit["ytop"], ahit["xtop"], ahit["ybot"], ahit["xbot"], k_y, b_y)
            ahit["zx_projection"] = x_center

        long_recognized_tracks_stereo = []

        for ahit1 in SmearedHits_stereo:
            for ahit2 in SmearedHits_stereo:
                if ahit1["z"] >= ahit2["z"]:
                    continue
                if ahit1["detID"] == ahit2["detID"]:
                    continue
                if ahit1["digiHit"] in used_hits:
                    continue
                if ahit2["digiHit"] in used_hits:
                    continue

                if abs(ahit1["zx_projection"]) > max_x or abs(ahit2["zx_projection"]) > max_x:
                    continue

                k_seed = 1.0 * (ahit2["zx_projection"] - ahit1["zx_projection"]) / (ahit2["z"] - ahit1["z"])
                b_seed = ahit1["zx_projection"] - k_seed * ahit1["z"]

                atrack_stereo = {}
                atrack_stereo["hits_stereo"] = [ahit1, ahit2]
                atrack_stereo_layers = [ahit1["detID"] // 10000, ahit2["detID"] // 10000]

                for ahit3 in SmearedHits_stereo:
                    if ahit3["digiHit"] == ahit1["digiHit"] or ahit3["digiHit"] == ahit2["digiHit"]:
                        continue
                    if ahit3["digiHit"] in used_hits:
                        continue

                    if abs(ahit3["zx_projection"]) > max_x:
                        continue

                    layer3 = ahit3["detID"] // 10000
                    if layer3 in atrack_stereo_layers:
                        continue

                    in_bin = hit_in_bin(
                        ahit3["z"],
                        ahit3["zx_projection"],
                        k_seed,
                        b_seed,
                        k_size=0.6 / 200 * r_scale,
                        b_size=1000.0 / 70 * r_scale,
                    )
                    if in_bin:
                        atrack_stereo["hits_stereo"].append(ahit3)
                        atrack_stereo_layers.append(layer3)

                if len(atrack_stereo["hits_stereo"]) >= min_hits:
                    long_recognized_tracks_stereo.append(atrack_stereo)

        # Remove clones
        max_track = None
        max_n_hits = -999

        for atrack_stereo in long_recognized_tracks_stereo:
            if len(atrack_stereo["hits_stereo"]) > max_n_hits:
                max_track = atrack_stereo
                max_n_hits = len(atrack_stereo["hits_stereo"])

        atrack = {}
        atrack["hits_y"] = atrack_y["hits_y"]
        atrack["k_y"] = atrack_y["k_y"]
        atrack["b_y"] = atrack_y["b_y"]
        atrack["hits_stereo"] = []

        if max_track is not None:
            atrack["hits_stereo"] = max_track["hits_stereo"]
            n_y_tracks_with_stereo += 1
            for ahit in max_track["hits_stereo"]:
                used_hits.append(ahit["digiHit"])

        recognized_tracks_stereo.append(atrack)

    logger.debug(
        "fast_hough_stereo: %d stereo hits, %d y-tracks, %d matched with stereo",
        len(SmearedHits_stereo),
        len(recognized_tracks_y),
        n_y_tracks_with_stereo,
    )

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

    sel = (b_left >= b_bin - 0.5 * b_size) * (b_right <= b_bin + 0.5 * b_size) + (b_left <= b_bin + 0.5 * b_size) * (
        b_right >= b_bin - 0.5 * b_size
    )

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
        print("Too large hits in the event!")
        return recognized_tracks

    min_hits = 3

    #### Separate hits
    SmearedHits_12y, SmearedHits_12stereo, SmearedHits_34y, SmearedHits_34stereo = hits_split(SmearedHits)

    #### PatRec in 12y
    recognized_tracks_y12 = artificial_retina_pat_rec_y_view(SmearedHits_12y, min_hits)

    ### PatRec in stereo12
    recognized_tracks_12 = artificial_retina_pat_rec_stereo_views(SmearedHits_12stereo, recognized_tracks_y12, min_hits)

    #### PatRec in 34y
    recognized_tracks_y34 = artificial_retina_pat_rec_y_view(SmearedHits_34y, min_hits)

    ### PatRec in stereo34
    recognized_tracks_34 = artificial_retina_pat_rec_stereo_views(SmearedHits_34stereo, recognized_tracks_y34, min_hits)

    ### Combination of tracks before and after the magnet
    recognized_tracks_combo = tracks_combination_using_extrapolation(
        recognized_tracks_12, recognized_tracks_34, ShipGeo.Bfield.z
    )

    # Prepare output of PatRec
    recognized_tracks = _prepare_output(recognized_tracks_combo, min_hits)

    return recognized_tracks


def artificial_retina_pat_rec_y_view(SmearedHits, min_hits: int):
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

    hits_z = np.array([ahit["z"] for ahit in SmearedHits])
    hits_y = np.array([ahit["ytop"] for ahit in SmearedHits])

    for i in range(len(SmearedHits)):
        hits_z_unused = hits_z[used_hits == 0]
        hits_y_unused = hits_y[used_hits == 0]

        sigma = 1.0 * r_scale
        best_seed_params = get_best_seed(hits_z_unused, hits_y_unused, sigma, sample_weight=None)

        res = minimize(
            retina_func,
            best_seed_params,
            args=(hits_z_unused, hits_y_unused, sigma, None),
            method="BFGS",
            jac=retina_grad,
            options={"gtol": 1e-6, "disp": False, "maxiter": 5},
        )
        [k_seed_upd, b_seed_upd] = res.x

        atrack = {}
        atrack["hits_y"] = []
        atrack_layers = []
        hit_ids = []

        # Add new hits to the seed
        for i_hit3 in range(len(SmearedHits)):
            if used_hits[i_hit3] == 1:
                continue

            ahit3 = SmearedHits[i_hit3]
            layer3 = ahit3["detID"] // 10000
            if layer3 in atrack_layers:
                continue

            in_bin = hit_in_window(ahit3["z"], ahit3["ytop"], k_seed_upd, b_seed_upd, window_width=1.4 * r_scale)
            if in_bin:
                atrack["hits_y"].append(ahit3)
                atrack_layers.append(layer3)
                hit_ids.append(i_hit3)

        if len(atrack["hits_y"]) >= min_hits:
            long_recognized_tracks.append(atrack)
            used_hits[hit_ids] = 1
        else:
            break

    # Remove clones
    recognized_tracks = reduce_clones_using_one_track_per_hit(long_recognized_tracks, min_hits)

    logger.debug(
        "ar_y_view: %d hits, %d tracks before clone removal, %d after",
        len(SmearedHits),
        len(long_recognized_tracks),
        len(recognized_tracks),
    )

    # Track fit
    for atrack in recognized_tracks:
        z_coords = [ahit["z"] for ahit in atrack["hits_y"]]
        y_coords = [ahit["ytop"] for ahit in atrack["hits_y"]]
        [atrack["k_y"], atrack["b_y"]] = np.polyfit(z_coords, y_coords, deg=1)

    return recognized_tracks


def artificial_retina_pat_rec_stereo_views(SmearedHits_stereo, recognized_tracks_y, min_hits: int):
    ### PatRec in stereo
    recognized_tracks_stereo = []
    used_hits = []
    n_y_tracks_with_stereo = 0

    for atrack_y in recognized_tracks_y:
        k_y = atrack_y["k_y"]
        b_y = atrack_y["b_y"]

        # Get hit zx projections
        for ahit in SmearedHits_stereo:
            x_center = get_zy_projection(ahit["z"], ahit["ytop"], ahit["xtop"], ahit["ybot"], ahit["xbot"], k_y, b_y)
            ahit["zx_projection"] = x_center

        long_recognized_tracks_stereo = []
        hits_z = []
        hits_x = []

        for ahit in SmearedHits_stereo:
            if ahit["digiHit"] in used_hits:
                continue
            if abs(ahit["zx_projection"]) > max_x:
                continue
            hits_z.append(ahit["z"])
            hits_x.append(ahit["zx_projection"])
        hits_z = np.array(hits_z)
        hits_x = np.array(hits_x)

        sigma = 15.0 * r_scale
        best_seed_params = get_best_seed(hits_z, hits_x, sigma, sample_weight=None)

        res = minimize(
            retina_func,
            best_seed_params,
            args=(hits_z, hits_x, sigma, None),
            method="BFGS",
            jac=retina_grad,
            options={"gtol": 1e-6, "disp": False, "maxiter": 5},
        )
        [k_seed_upd, b_seed_upd] = res.x

        atrack_stereo = {}
        atrack_stereo["hits_stereo"] = []
        atrack_stereo_layers = []

        for ahit3 in SmearedHits_stereo:
            if ahit3["digiHit"] in used_hits:
                continue

            if abs(ahit3["zx_projection"]) > max_x:
                continue

            layer3 = ahit3["detID"] // 10000
            if layer3 in atrack_stereo_layers:
                continue

            in_bin = hit_in_window(
                ahit3["z"], ahit3["zx_projection"], k_seed_upd, b_seed_upd, window_width=15.0 * r_scale
            )
            if in_bin:
                atrack_stereo["hits_stereo"].append(ahit3)
                atrack_stereo_layers.append(layer3)

        if len(atrack_stereo["hits_stereo"]) >= min_hits:
            long_recognized_tracks_stereo.append(atrack_stereo)

        # Remove clones
        max_track = None
        max_n_hits = -999

        for atrack_stereo in long_recognized_tracks_stereo:
            if len(atrack_stereo["hits_stereo"]) > max_n_hits:
                max_track = atrack_stereo
                max_n_hits = len(atrack_stereo["hits_stereo"])

        atrack = {}
        atrack["hits_y"] = atrack_y["hits_y"]
        atrack["k_y"] = atrack_y["k_y"]
        atrack["b_y"] = atrack_y["b_y"]
        atrack["hits_stereo"] = []

        if max_track is not None:
            atrack["hits_stereo"] = max_track["hits_stereo"]
            n_y_tracks_with_stereo += 1
            for ahit in max_track["hits_stereo"]:
                used_hits.append(ahit["digiHit"])

        recognized_tracks_stereo.append(atrack)

    logger.debug(
        "ar_stereo: %d stereo hits, %d y-tracks, %d matched with stereo",
        len(SmearedHits_stereo),
        len(recognized_tracks_y),
        n_y_tracks_with_stereo,
    )

    return recognized_tracks_stereo


def get_best_seed(x, y, sigma: float, sample_weight=None):
    best_retina_val = 0
    best_seed_params = [0, 0]

    for i_1 in range(len(x) - 1):
        for i_2 in range(i_1 + 1, len(x)):
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
    Returns
    -------
    retina : float
        Negative value of the artificial retina function.
    """

    rs = track_prams[0] * x + track_prams[1] - y

    if sample_weight is None:
        exps = np.exp(-((rs / sigma) ** 2))
    else:
        exps = np.exp(-((rs / sigma) ** 2)) * sample_weight

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
    Returns
    -------
    retina : float
        Negative value of the artificial retina gradient.
    """

    rs = track_prams[0] * x + track_prams[1] - y

    if sample_weight is None:
        exps = np.exp(-((rs / sigma) ** 2))
    else:
        exps = np.exp(-((rs / sigma) ** 2)) * sample_weight

    dks = -2.0 * rs / sigma**2 * exps * x
    dbs = -2.0 * rs / sigma**2 * exps

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

        detID = ahit["detID"]
        decode = global_variables.modules["strawtubes"].StrawDecode(detID)
        # StrawDecode returns a tuple of (statnb, vnb, lnb, snb).
        is_y12 = ((decode[0] == 1) + (decode[0] == 2)) * ((decode[1] == 0) + (decode[1] == 3))
        is_stereo12 = ((decode[0] == 1) + (decode[0] == 2)) * ((decode[1] == 1) + (decode[1] == 2))
        is_y34 = ((decode[0] == 3) + (decode[0] == 4)) * ((decode[1] == 0) + (decode[1] == 3))
        is_stereo34 = ((decode[0] == 3) + (decode[0] == 4)) * ((decode[1] == 1) + (decode[1] == 2))

        if is_y12:
            smeared_hits_12y.append(ahit)
        if is_stereo12:
            smeared_hits_12stereo.append(ahit)
        if is_y34:
            smeared_hits_34y.append(ahit)
        if is_stereo34:
            smeared_hits_34stereo.append(ahit)

    logger.debug(
        "hits_split: y12=%d, stereo12=%d, y34=%d, stereo34=%d",
        len(smeared_hits_12y),
        len(smeared_hits_12stereo),
        len(smeared_hits_34y),
        len(smeared_hits_34stereo),
    )

    return smeared_hits_12y, smeared_hits_12stereo, smeared_hits_34y, smeared_hits_34stereo


def reduce_clones_using_one_track_per_hit(recognized_tracks, min_hits: int = 3):
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
    n_hits = [len(atrack["hits_y"]) for atrack in recognized_tracks]

    for i_track in np.argsort(n_hits)[::-1]:
        atrack = recognized_tracks[i_track]
        new_track = {}
        new_track["hits_y"] = []

        for i_hit in range(len(atrack["hits_y"])):
            ahit = atrack["hits_y"][i_hit]
            if ahit["digiHit"] not in used_hits:
                new_track["hits_y"].append(ahit)

        if len(new_track["hits_y"]) >= min_hits:
            tracks_no_clones.append(new_track)
            for ahit in new_track["hits_y"]:
                used_hits.append(ahit["digiHit"])

    return tracks_no_clones


def tracks_combination_using_extrapolation(recognized_tracks_12, recognized_tracks_34, z_magnet):
    recognized_tracks_combo = []

    i_track_y12 = []
    i_track_y34 = []
    deltas_y = []

    for i_12 in range(len(recognized_tracks_12)):
        atrack_12 = recognized_tracks_12[i_12]
        y_center_y12 = atrack_12["k_y"] * z_magnet + atrack_12["b_y"]

        for i_34 in range(len(recognized_tracks_34)):
            atrack_34 = recognized_tracks_34[i_34]
            y_center_y34 = atrack_34["k_y"] * z_magnet + atrack_34["b_y"]

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
            atrack["hits_y12"] = recognized_tracks_12[i_12]["hits_y"]
            atrack["hits_stereo12"] = recognized_tracks_12[i_12]["hits_stereo"]
            atrack["hits_y34"] = recognized_tracks_34[i_34]["hits_y"]
            atrack["hits_stereo34"] = recognized_tracks_34[i_34]["hits_stereo"]
            atrack["k_y12"] = recognized_tracks_12[i_12]["k_y"]
            atrack["b_y12"] = recognized_tracks_12[i_12]["b_y"]
            atrack["k_y34"] = recognized_tracks_34[i_34]["k_y"]
            atrack["b_y34"] = recognized_tracks_34[i_34]["b_y"]
            recognized_tracks_combo.append(atrack)
            used_y12.append(i_12)
            used_y34.append(i_34)

    for i_12 in range(len(recognized_tracks_12)):
        if i_12 not in used_y12:
            atrack = {}
            atrack["hits_y12"] = recognized_tracks_12[i_12]["hits_y"]
            atrack["hits_stereo12"] = recognized_tracks_12[i_12]["hits_stereo"]
            atrack["hits_y34"] = []
            atrack["hits_stereo34"] = []
            atrack["k_y12"] = recognized_tracks_12[i_12]["k_y"]
            atrack["b_y12"] = recognized_tracks_12[i_12]["b_y"]
            atrack["k_y34"] = None
            atrack["b_y34"] = None
            recognized_tracks_combo.append(atrack)

    for i_34 in range(len(recognized_tracks_34)):
        if i_34 not in used_y34:
            atrack = {}
            atrack["hits_y12"] = []
            atrack["hits_stereo12"] = []
            atrack["hits_y34"] = recognized_tracks_34[i_34]["hits_y"]
            atrack["hits_stereo34"] = recognized_tracks_34[i_34]["hits_stereo"]
            atrack["k_y12"] = None
            atrack["b_y12"] = None
            atrack["k_y34"] = recognized_tracks_34[i_34]["k_y"]
            atrack["b_y34"] = recognized_tracks_34[i_34]["b_y"]
            recognized_tracks_combo.append(atrack)

    logger.debug(
        "tracks_combo: %d 12-tracks, %d 34-tracks, %d matched pairs, %d total combos",
        len(recognized_tracks_12),
        len(recognized_tracks_34),
        len(used_y12),
        len(recognized_tracks_combo),
    )

    return recognized_tracks_combo


def _legendre_peak(z_pts, val_pts, r_pts, z_ref, m_range=(-0.1, 0.1), b_range=(-300.0, 300.0), n_m=200, n_b=400):
    """Legendre-transform peak finder for circles in a 2D plane.

    Each input is a drift circle at (z, val) with radius r. The tangent
    lines to the set of circles form a peak in (m, b) space, where the
    line is parametrised as val = m*(z - z_ref) + b. Each circle maps to
    two curves b(m) = (val - m*(z - z_ref)) +/- r*sqrt(1 + m^2). Returns
    (m_star, b_star, peak_count). Implementation ported verbatim from
    macro/probe_bistability.py.
    """
    if len(z_pts) < 2:
        return None, None, 0
    m_vals = np.linspace(m_range[0], m_range[1], n_m)
    sqrt1m2 = np.sqrt(1.0 + m_vals * m_vals)
    b_lo, b_hi = b_range
    H = np.zeros((n_m, n_b), dtype=np.int32)
    db = (b_hi - b_lo) / n_b
    for z, v, r in zip(z_pts, val_pts, r_pts):
        zp = z - z_ref
        b_centre = v - m_vals * zp
        for sign in (+1, -1):
            b_curve = b_centre + sign * r * sqrt1m2
            ib = ((b_curve - b_lo) / db).astype(np.int32)
            mask = (ib >= 0) & (ib < n_b)
            for im in range(n_m):
                if mask[im]:
                    H[im, ib[im]] += 1
    flat_idx = int(np.argmax(H))
    im, ib = np.unravel_index(flat_idx, H.shape)
    return float(m_vals[im]), float(b_lo + (ib + 0.5) * db), int(H[im, ib])


def _legendre_lr_for_half(y_hits, s_hits):
    """Compute per-hit L/R signs via two-stage Legendre for one track half.

    Augments each hit dict with an 'lr' field in {-1, 0, +1} (0 = DAF auto
    on failure). y_hits are Y-view hits (vertical projection wires along x,
    dy = 0). s_hits are stereo hits (tilted wires).

    Falls back to lr=0 for all hits if the y-Legendre cannot find a peak
    or has fewer than 2 hits.
    """
    if len(y_hits) < 2:
        for h in y_hits + s_hits:
            h.setdefault("lr", 0)
        return

    import math as _math

    zs_y = [h["z"] for h in y_hits]
    ys_y = [h["ytop"] for h in y_hits]
    rs_y = [h["dist"] for h in y_hits]
    z_ref = sum(zs_y) / len(zs_y)
    wy_min, wy_max = min(ys_y), max(ys_y)
    r_max = max(rs_y) + 0.1
    b_pad = max(r_max + 1.0, 5.0)
    m_y, b_y, _peak = _legendre_peak(
        zs_y, ys_y, rs_y, z_ref, m_range=(-0.05, 0.05), b_range=(wy_min - b_pad, wy_max + b_pad), n_m=200, n_b=400
    )
    if m_y is None:
        for h in y_hits + s_hits:
            h.setdefault("lr", 0)
        return

    # Stage 2: stereo Legendre in (z, x) using the y-track
    m_x, b_x = None, None
    if len(s_hits) >= 2:
        zs_s, xs_s, rs_s_eff = [], [], []
        for h in s_hits:
            y_track = m_y * (h["z"] - z_ref) + b_y
            dy_w = h["ybot"] - h["ytop"]
            dx_w = h["xbot"] - h["xtop"]
            wlen = _math.sqrt(dx_w * dx_w + dy_w * dy_w)
            if abs(dy_w) < 1e-6 or wlen < 1e-6:
                continue
            x_at_y = h["xtop"] + (y_track - h["ytop"]) / dy_w * dx_w
            stereo_sin = abs(dy_w) / wlen
            r_eff = h["dist"] / max(stereo_sin, 1e-3)
            zs_s.append(h["z"])
            xs_s.append(x_at_y)
            rs_s_eff.append(r_eff)
        if len(zs_s) >= 2:
            xs_min, xs_max = min(xs_s), max(xs_s)
            r_pad = max(rs_s_eff) + 1.0
            m_x, b_x, _peak_x = _legendre_peak(
                zs_s,
                xs_s,
                rs_s_eff,
                z_ref,
                m_range=(-0.1, 0.1),
                b_range=(xs_min - r_pad, xs_max + r_pad),
                n_m=200,
                n_b=400,
            )

    # Apply L/R per Y-view hit (sign of y_track - wy)
    for h in y_hits:
        wz = h["z"]
        y_track = m_y * (wz - z_ref) + b_y
        d = y_track - h["ytop"]
        h["lr"] = 1 if d > 0 else -1

    # Apply L/R per stereo hit (sign of perpendicular distance)
    for h in s_hits:
        wz = h["z"]
        y_track = m_y * (wz - z_ref) + b_y
        if m_x is None:
            h["lr"] = 0
            continue
        x_track = m_x * (wz - z_ref) + b_x
        dy_w = h["ybot"] - h["ytop"]
        dx_w = h["xbot"] - h["xtop"]
        wlen = _math.sqrt(dx_w * dx_w + dy_w * dy_w)
        if wlen < 1e-6:
            h["lr"] = 0
            continue
        ux = dx_w / wlen
        uy = dy_w / wlen
        nx, ny = -uy, ux
        d_perp = (x_track - h["xtop"]) * nx + (y_track - h["ytop"]) * ny
        h["lr"] = 1 if d_perp > 0 else -1


def _compute_legendre_lr_per_track(atrack):
    """Augment each hit dict in atrack with an 'lr' field in {-1, 0, +1}.

    Applied to the four hit-list views per track (y12, stereo12, y34, stereo34).
    Each track half (upstream / downstream of the magnet) is processed
    independently because the track is straight only within a half.
    Failure modes (no Legendre peak) leave 'lr' = 0, interpreted downstream
    as 'DAF auto resolution'.
    """
    _legendre_lr_for_half(atrack.get("y12", []), atrack.get("stereo12", []))
    _legendre_lr_for_half(atrack.get("y34", []), atrack.get("stereo34", []))
    return atrack


def _prepare_output(recognized_tracks_combo, min_hits):
    """Prepare PatRec output, filtering tracks with too few hits and preserving track parameters."""
    recognized_tracks = {}
    i_track = 0
    n_rejected = 0
    for atrack_combo in recognized_tracks_combo:
        hits_y12 = atrack_combo["hits_y12"]
        hits_stereo12 = atrack_combo["hits_stereo12"]
        hits_y34 = atrack_combo["hits_y34"]
        hits_stereo34 = atrack_combo["hits_stereo34"]

        if (
            len(hits_y12) >= min_hits
            and len(hits_stereo12) >= min_hits
            and len(hits_y34) >= min_hits
            and len(hits_stereo34) >= min_hits
        ):
            atrack = {
                "y12": hits_y12,
                "stereo12": hits_stereo12,
                "y34": hits_y34,
                "stereo34": hits_stereo34,
                "k_y12": atrack_combo.get("k_y12"),
                "b_y12": atrack_combo.get("b_y12"),
                "k_y34": atrack_combo.get("k_y34"),
                "b_y34": atrack_combo.get("b_y34"),
            }
            # Per-hit L/R drift-isochrone resolution via the Legendre transform
            # (Aliev et al., NIM A 592, 456, 2008). Augments each hit dict with
            # an 'lr' field in {-1, 0, +1} that shipDigiReco passes to
            # WireMeasurement::setLeftRightResolution. The fall-back lr = 0
            # means the DAF resolves the side iteratively.
            _compute_legendre_lr_per_track(atrack)
            recognized_tracks[i_track] = atrack
            i_track += 1
        else:
            n_rejected += 1

    logger.debug(
        "output: %d tracks accepted, %d rejected by min_hits=%d filter",
        i_track,
        n_rejected,
        min_hits,
    )

    return recognized_tracks


def hit_in_window(x, y, k_bin, b_bin, window_width=1.0) -> bool:
    """
    Check whether a hit falls within a window around a straight-line track.

    Parameters
    ---------
    x : float
        Z coordinate of the hit.
    y : float
        Y (or projected X) coordinate of the hit.
    k_bin : float
        Track slope: y = k_bin * x + b_bin
    b_bin : float
        Track intercept: y = k_bin * x + b_bin
    window_width : float
        Half-width of the acceptance window in the y direction.

    Return
    ------
    flag : bool
        True if the hit is within the window.
    """

    y_approx = k_bin * x + b_bin

    flag = False
    if np.abs(y_approx - y) <= window_width:
        flag = True

    return flag


def get_zy_projection(z, xtop, ytop, xbot, ybot, k_y, b_y):
    """
    Project a stereo straw hit onto the ZX plane using the Y-view track parameters.

    A stereo straw is tilted: its top-end is at (xtop, ytop) and bottom-end at
    (xbot, ybot), both at the same z. The Y-view track gives the y position at
    this z as y_track = k_y * z + b_y. This function finds the x coordinate
    where the straw wire crosses y_track by parameterising the wire as a line
    in the XY plane and evaluating it at y = y_track.

    Note: the caller passes (ytop, xtop, ybot, xbot) — the argument names here
    are swapped relative to the geometric meaning because the call sites swap
    the x/y coordinates. This is intentional: the straw wire is parameterised
    as x(y), not y(x), because the stereo straws are nearly vertical.

    Parameters
    ----------
    z : float
        Z coordinate of the hit.
    xtop : float
        First coordinate of wire top-end (actually ytop at call site).
    ytop : float
        Second coordinate of wire top-end (actually xtop at call site).
    xbot : float
        First coordinate of wire bottom-end (actually ybot at call site).
    ybot : float
        Second coordinate of wire bottom-end (actually xbot at call site).
    k_y : float
        Slope of the Y-view track: y = k_y * z + b_y.
    b_y : float
        Intercept of the Y-view track.

    Returns
    -------
    y : float
        The projected x coordinate of the hit in the ZX plane.
    """
    x = k_y * z + b_y
    k = (ytop - ybot) / (xtop - xbot + 10**-6)
    b = ytop - k * xtop
    y = k * x + b

    return y


def pat_rec_stereo_views(SmearedHits_stereo, recognized_tracks_y, min_hits: int):
    ### PatRec in stereo
    recognized_tracks_stereo = []
    used_hits = []
    n_y_tracks_with_stereo = 0

    for atrack_y in recognized_tracks_y:
        k_y = atrack_y["k_y"]
        b_y = atrack_y["b_y"]

        # Get hit zx projections
        for ahit in SmearedHits_stereo:
            x_center = get_zy_projection(ahit["z"], ahit["ytop"], ahit["xtop"], ahit["ybot"], ahit["xbot"], k_y, b_y)
            ahit["zx_projection"] = x_center

        long_recognized_tracks_stereo = []

        for ahit1 in SmearedHits_stereo:
            for ahit2 in SmearedHits_stereo:
                if ahit1["z"] >= ahit2["z"]:
                    continue
                if ahit1["detID"] == ahit2["detID"]:
                    continue
                if ahit1["digiHit"] in used_hits:
                    continue
                if ahit2["digiHit"] in used_hits:
                    continue

                if abs(ahit1["zx_projection"]) > max_x or abs(ahit2["zx_projection"]) > max_x:
                    continue

                k_seed = 1.0 * (ahit2["zx_projection"] - ahit1["zx_projection"]) / (ahit2["z"] - ahit1["z"])
                b_seed = ahit1["zx_projection"] - k_seed * ahit1["z"]

                atrack_stereo = {}
                atrack_stereo["hits_stereo"] = [ahit1, ahit2]
                atrack_stereo_layers = [ahit1["detID"] // 10000, ahit2["detID"] // 10000]

                for ahit3 in SmearedHits_stereo:
                    if ahit3["digiHit"] == ahit1["digiHit"] or ahit3["digiHit"] == ahit2["digiHit"]:
                        continue
                    if ahit3["digiHit"] in used_hits:
                        continue

                    if abs(ahit3["zx_projection"]) > max_x:
                        continue

                    layer3 = ahit3["detID"] // 10000
                    if layer3 in atrack_stereo_layers:
                        continue

                    in_bin = hit_in_window(
                        ahit3["z"], ahit3["zx_projection"], k_seed, b_seed, window_width=15.0 * r_scale
                    )
                    if in_bin:
                        atrack_stereo["hits_stereo"].append(ahit3)
                        atrack_stereo_layers.append(layer3)

                if len(atrack_stereo["hits_stereo"]) >= min_hits:
                    long_recognized_tracks_stereo.append(atrack_stereo)

        # Remove clones
        max_track = None
        max_n_hits = -999

        for atrack_stereo in long_recognized_tracks_stereo:
            if len(atrack_stereo["hits_stereo"]) > max_n_hits:
                max_track = atrack_stereo
                max_n_hits = len(atrack_stereo["hits_stereo"])

        atrack = {}
        atrack["hits_y"] = atrack_y["hits_y"]
        atrack["k_y"] = atrack_y["k_y"]
        atrack["b_y"] = atrack_y["b_y"]
        atrack["hits_stereo"] = []

        if max_track is not None:
            atrack["hits_stereo"] = max_track["hits_stereo"]
            n_y_tracks_with_stereo += 1
            for ahit in max_track["hits_stereo"]:
                used_hits.append(ahit["digiHit"])

        recognized_tracks_stereo.append(atrack)

    logger.debug(
        "pat_rec_stereo: %d stereo hits, %d y-tracks, %d matched with stereo",
        len(SmearedHits_stereo),
        len(recognized_tracks_y),
        n_y_tracks_with_stereo,
    )

    return recognized_tracks_stereo
