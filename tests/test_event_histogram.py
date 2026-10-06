# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import numpy as np
import pytest
from event_histogram import EventHistogram, make_event_key, replica_weights

EDGES = np.linspace(0.0, 10.0, 11)


def correlated_sample(seed, n_events, p_active=0.3, n_clones=20):
    """Events with n_clones branches of weight 1/n_clones around a common x."""
    rng = np.random.default_rng(seed)
    events: list[tuple[np.ndarray, np.ndarray] | None] = []
    for _ in range(n_events):
        if rng.random() < p_active:
            x0 = rng.uniform(0.0, 10.0)
            events.append((x0 + rng.normal(0.0, 0.3, n_clones), np.full(n_clones, 1.0 / n_clones)))
        else:
            events.append(None)
    return events


def fill(h, events, run=1):
    for i, ev in enumerate(events):
        if ev is None:
            h.add_empty_events(1)
        else:
            h.fill_event(*ev, key=make_event_key(run, i))


def test_matches_per_event_formula():
    events = correlated_sample(1, 3000)
    h = EventHistogram("x", EDGES)
    fill(h, events)
    t = np.zeros((len(events), len(EDGES) - 1))
    for i, ev in enumerate(events):
        if ev is not None:
            t[i] = np.histogram(ev[0], EDGES, weights=ev[1])[0]
    n = len(events)
    assert h.n_events == n
    assert h.values() == pytest.approx(t.sum(0) / n)
    assert h.errors() == pytest.approx(t.std(0, ddof=1) / np.sqrt(n))


def test_naive_error_is_too_small_for_clones():
    h = EventHistogram("x", EDGES)
    fill(h, correlated_sample(2, 3000))
    assert np.all(h.errors() / h.naive_errors() > 2.0)
    assert np.all(h.n_eff() < 3000)


def test_merge_equals_single_accumulator():
    a, b = correlated_sample(3, 1000), correlated_sample(4, 1500)
    ha = EventHistogram("x", EDGES, covariance=True, n_replicas=50)
    hb = EventHistogram("x", EDGES, covariance=True, n_replicas=50)
    hab = EventHistogram("x", EDGES, covariance=True, n_replicas=50)
    fill(ha, a, run=1)
    fill(hb, b, run=2)
    fill(hab, a, run=1)
    fill(hab, b, run=2)
    ha += hb
    assert ha.n_events == hab.n_events
    assert ha.errors() == pytest.approx(hab.errors())
    assert ha.covariance() == pytest.approx(hab.covariance())
    assert ha.bootstrap_errors() == pytest.approx(hab.bootstrap_errors())


def test_covariance_diagonal_is_variance():
    h = EventHistogram("x", EDGES, covariance=True)
    fill(h, correlated_sample(5, 2000))
    assert np.diag(h.covariance()) == pytest.approx(h.errors() ** 2)


def test_bootstrap_reproduces_errors():
    h = EventHistogram("x", EDGES, n_replicas=400)
    fill(h, correlated_sample(6, 4000))
    assert h.bootstrap_errors() == pytest.approx(h.errors(), rel=0.25)


def test_replica_weights_are_poisson_one():
    w = np.concatenate([replica_weights(k, 50) for k in range(4000)])
    assert w.mean() == pytest.approx(1.0, abs=0.02)
    assert w.var() == pytest.approx(1.0, abs=0.04)
    assert np.array_equal(replica_weights(42, 10), replica_weights(42, 10))


def test_open_event_is_an_error():
    h = EventHistogram("x", EDGES)
    h.fill([1.0], [1.0])
    with pytest.raises(RuntimeError):
        h.values()


def test_flows_are_kept_out_of_range():
    h = EventHistogram("x", EDGES)
    h.fill_event([-1.0, 5.0, 10.0, 11.0], [1.0, 1.0, 1.0, 1.0])
    assert h.values().sum() == pytest.approx(1.0)
    assert h.sum_t[0] == pytest.approx(1.0)
    assert h.sum_t[-1] == pytest.approx(2.0)


@pytest.fixture
def root_with_shipdata():
    ROOT = pytest.importorskip("ROOT")
    if ROOT.gSystem.Load("libShipData") < 0 or not hasattr(ROOT, "EventHistogram"):
        pytest.skip("libShipData with EventHistogram not available")
    return ROOT


def test_root_round_trip_and_cpp_agree(root_with_shipdata, tmp_path):
    ROOT = root_with_shipdata
    events = correlated_sample(7, 2000)
    h = EventHistogram("x", EDGES, covariance=True, n_replicas=20)
    fill(h, events)
    cpp = ROOT.EventHistogram("x", "", len(EDGES) - 1, 0.0, 10.0, True, 20)
    for i, ev in enumerate(events):
        if ev is None:
            cpp.AddEmptyEvents(1)
            continue
        for x, w in zip(*ev):
            cpp.Fill(x, w)
        cpp.EndEvent(make_event_key(1, i))
    result = cpp.MakeResult()
    assert [result.GetBinContent(b) for b in range(1, 11)] == pytest.approx(h.values())
    assert [result.GetBinError(b) for b in range(1, 11)] == pytest.approx(h.errors())
    assert list(cpp.GetBootstrapErrors()) == pytest.approx(h.bootstrap_errors())
    for key in (0, 1, make_event_key(7, 123456)):
        assert [cpp.ReplicaWeight(key, r) for r in range(30)] == list(replica_weights(key, 30))

    # Python writes, C++ reads; C++ writes, Python reads.
    path = str(tmp_path / "eh.root")
    f = ROOT.TFile(path, "RECREATE")
    h.to_root(f)
    f.Close()
    f = ROOT.TFile(path)
    back = ROOT.EventHistogram.Read(f, "x")
    assert back.GetNEvents() == h.n_events
    res = back.MakeResult()
    assert [res.GetBinError(b) for b in range(1, 11)] == pytest.approx(h.errors())
    f.Close()
    path2 = str(tmp_path / "eh_cpp.root")
    f = ROOT.TFile(path2, "RECREATE")
    cpp.Write(f)
    f.Close()
    f = ROOT.TFile(path2)
    again = EventHistogram.from_root(f, "x")
    assert again.errors() == pytest.approx(h.errors())
    assert again.covariance() == pytest.approx(h.covariance())
    f.Close()
