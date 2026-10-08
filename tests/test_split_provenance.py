# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import itertools
import math

import numpy as np
import pytest
from split_provenance import DECAY, K_NO_PROCESS, NOT_SPLIT, SURVIVOR, SplitProvenance

G4 = 13  # any Geant4 process other than kPNoProcess


def synthetic_event(pruned=()):
    """A primary M with a per-step split kaon K, a split-once kaon K2 and a sibling.

    K (set 0, weight 1) is split at t = 2..6 with decay probabilities P, two
    clones per step. Geant4 decays it at t = 4 on a split step, so it is
    continued by C, which ends by interacting at t = 7. Secondaries are created
    along the line with the line's weight at that time. K2 (set 1) decays at
    t = 3 into four clones of weight 1/4. Clones are pushed with K's mother.
    """
    P = {2.0: 0.2, 3.0: 0.25, 4.0: 0.3, 5.0: 0.15, 6.0: 0.4}
    line = {1.0: 1.0}
    w = 1.0
    clones = []
    for t, p in P.items():
        clones += [(t, w * p / 2)] * 2
        w *= 1 - p
        line[t] = w
    rows: dict[str, tuple] = {}  # name: (mother, set, role, split weight, start, weight, proc)
    rows["M"] = (None, -1, NOT_SPLIT, 0.0, 0.0, 1.0, 0)
    rows["s"] = ("M", -1, NOT_SPLIT, 0.0, 1.0, 1.0, G4)
    rows["K"] = ("M", 0, SURVIVOR, 1.0, 1.0, line[4.0], G4)
    rows["C"] = ("M", 0, SURVIVOR, 1.0, 4.0, line[6.0], K_NO_PROCESS)
    for k, (t, wc) in enumerate(clones):
        rows[f"c{k}"] = ("M", 0, DECAY, 1.0, t, wc, K_NO_PROCESS)
    rows["y1"] = ("K", -1, NOT_SPLIT, 0.0, 2.5, line[2.0], G4)
    rows["y2"] = ("C", -1, NOT_SPLIT, 0.0, 5.5, line[5.0], G4)
    rows["z"] = ("C", -1, NOT_SPLIT, 0.0, 7.0, line[6.0], G4)
    rows["mu_a"] = ("c2", -1, NOT_SPLIT, 0.0, 3.0, clones[2][1], G4)  # from a decay at t = 3
    rows["mu_b"] = ("c6", -1, NOT_SPLIT, 0.0, 5.0, clones[6][1], G4)  # from a decay at t = 5
    rows["K2"] = ("M", 1, SURVIVOR, 1.0, 1.0, 1.0, G4)
    for k in range(4):
        rows[f"d{k}"] = ("M", 1, DECAY, 1.0, 3.0, 0.25, K_NO_PROCESS)
    rows["mu_c"] = ("d0", -1, NOT_SPLIT, 0.0, 3.0, 0.25, G4)
    names = [n for n in rows if n not in pruned]
    index = {n: i for i, n in enumerate(names)}
    cols = [[] for _ in range(7)]
    for n in names:
        mother, *rest = rows[n]
        cols[0].append(index[mother] if mother is not None else -1)
        for c, v in zip(cols[1:], rest):
            c.append(v)
    return SplitProvenance(*cols), index, line


PRUNED = ("c1", "c9", "d2", "d3")


@pytest.fixture
def event():
    return synthetic_event(PRUNED)


def test_alternatives_of_one_decay_are_incompatible(event):
    prov, ix, _ = event
    assert not prov.compatible(ix["c0"], ix["c2"])  # two decay times
    assert not prov.compatible(ix["d0"], ix["d1"])  # two clones of one decay
    assert not prov.compatible(ix["mu_a"], ix["mu_b"])  # their muons


def test_decay_versus_survivor_line_follows_time(event):
    prov, ix, _ = event
    assert prov.compatible(ix["mu_a"], ix["y1"])  # y1 emitted at 2.5, decay at 3
    assert not prov.compatible(ix["c0"], ix["y1"])  # decay at 2, before y1
    assert not prov.compatible(ix["mu_b"], ix["y2"])  # decay at 5, y2 at 5.5
    assert not prov.compatible(ix["mu_a"], ix["z"])  # z needs survival to the end
    assert prov.compatible(ix["y1"], ix["y2"])  # both on the survivor line


def test_independent_splits_and_siblings_are_compatible(event):
    prov, ix, _ = event
    assert prov.compatible(ix["mu_a"], ix["mu_c"])  # different kaons
    assert prov.compatible(ix["mu_a"], ix["s"])  # real sibling


def test_pair_weights_by_hand(event):
    prov, ix, line = event
    pw = prov.pair_weight
    assert pw(ix["mu_a"], ix["y1"]) == pytest.approx(prov.weight[ix["mu_a"]])
    assert pw(ix["mu_b"], ix["y2"]) == 0.0
    assert pw(ix["y1"], ix["y2"]) == pytest.approx(line[5.0])  # survive to 5.5
    assert pw(ix["mu_a"], ix["mu_c"]) == pytest.approx(prov.weight[ix["mu_a"]] * 0.25)
    assert pw(ix["s"], ix["mu_a"]) == pytest.approx(prov.weight[ix["mu_a"]])


def _desplit_rates(prov, n_draws, seed):
    rng = np.random.default_rng(seed)
    keep = np.array([prov.desplit(rng).keeps_track for _ in range(n_draws)])
    return keep, keep.mean(axis=0)


def test_desplit_reproduces_weights_and_pair_weights(event):
    prov, ix, line = event
    n = 40000
    keep, rate = _desplit_rates(prov, n, seed=1)
    expected = {name: prov.weight[i] for name, i in ix.items()}
    # Survivor tracks exist from their start: the original always, the
    # continuation if the line survived to t = 4.
    expected.update(K=1.0, K2=1.0, C=line[4.0])
    for name, i in ix.items():
        p = expected[name]
        tol = 4 * math.sqrt(max(p * (1 - p), 1e-12) / n) + 1e-12
        assert rate[i] == pytest.approx(p, abs=tol), name
    # Pairs of non-survivor tracks: kept together at the pair weight.
    others = [i for name, i in ix.items() if name not in ("K", "C", "K2", "M")]
    for i, j in itertools.combinations(others, 2):
        p = prov.pair_weight(i, j)
        together = np.mean(keep[:, i] & keep[:, j])
        tol = 4 * math.sqrt(max(p * (1 - p), 1e-12) / n) + 1e-12
        assert together == pytest.approx(p, abs=tol), (i, j)


def test_pruning_does_not_change_the_answer():
    full, ix_full, _ = synthetic_event()
    pruned, ix, _ = synthetic_event(PRUNED)
    for a, b in [("mu_a", "y1"), ("y1", "y2"), ("mu_a", "mu_c"), ("mu_b", "z")]:
        assert pruned.pair_weight(ix[a], ix[b]) == pytest.approx(full.pair_weight(ix_full[a], ix_full[b]))


def test_desplit_is_reproducible(event):
    prov, _, _ = event
    a = prov.desplit(np.random.default_rng(7)).keeps_track
    b = prov.desplit(np.random.default_rng(7)).keeps_track
    assert np.array_equal(a, b)


def test_from_tracks_reads_ship_mc_track():
    ROOT = pytest.importorskip("ROOT")
    if ROOT.gSystem.Load("libShipData") < 0 or not hasattr(ROOT.ShipMCTrack, "GetSplitSet"):
        pytest.skip("libShipData with split sets not available")
    mother = ROOT.ShipMCTrack(321, -1, 0.0, 0.0, 50.0, 0.4937, 0.0, 0.0, 0.0, 1.0, 0, 0, 0, 1.0)
    clone = ROOT.ShipMCTrack(321, -1, 0.0, 0.0, 50.0, 0.4937, 0.0, 0.0, 10.0, 2.0, 0, 0, 1, 0.5)
    clone.SetSplitSet(0, DECAY, 1.0)
    clone.SetProcID(K_NO_PROCESS)
    mother.SetSplitSet(0, SURVIVOR, 1.0)
    mother.SetProcID(G4)  # the constructor defaults to kPNoProcess
    prov = SplitProvenance.from_tracks([mother, clone])
    assert prov.sets[0]["decays"] == [1]
    assert prov.sets[0]["survivors"] == [0]
    assert prov.continuation.tolist() == [False, False]
