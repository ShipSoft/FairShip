# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Matching of straw hits to the ACTS measurements made from them."""

import pytest

pytest.importorskip("acts")

from strawReco import align_candidate_indices, match_hits_to_measurements, straw_geometry_id


def test_hits_follow_measurements_grouped_by_straw():
    # Straws A, B, C; A has two hits. The measurements are grouped by straw,
    # in a different order than the hits, and keep hit order within a straw.
    hit_gids = ["A", "B", "A", "C"]
    measurement_gids = ["C", "A", "A", "B"]
    assert match_hits_to_measurements(hit_gids, measurement_gids) == {0: 1, 2: 2, 1: 3, 3: 0}


def test_hits_on_dropped_surfaces_are_left_out():
    # Fewer measurements than hits: straw B had no surface.
    assert match_hits_to_measurements(["A", "B", "A"], ["A", "A"]) == {0: 0, 2: 1}


def test_count_mismatch_on_a_straw_is_skipped():
    assert match_hits_to_measurements(["A", "A", "B"], ["A", "B"]) == {2: 1}


def test_candidate_keeps_straw_hit_indices():
    hit_to_measurement = {0: 1, 2: 2, 3: 0}
    assert align_candidate_indices({"indices": [3, 1, 0]}, hit_to_measurement) == [(0, 3), (1, 0)]


def test_straw_geometry_id_layer_numbering():
    first = straw_geometry_id([0, 1, 0, 0, 5])
    same_straw = straw_geometry_id([0, 1, 0, 0, 5, 99])
    next_layer = straw_geometry_id([0, 1, 1, 0, 5])
    assert first == same_straw
    assert first != next_layer
