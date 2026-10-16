# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Histograms with event-level uncertainties for samples with split branches.

All branches of an event (split kaon/pion clones, their decay products and
secondaries) share the history of the primary interaction, so they are not
independent entries and sqrt(sum w^2) underestimates the error, by a large
factor when many clones of one decay land in the same bin. The independent unit
is the event: sum the weights of an event per bin first,

    t_eb = sum_{i in e, x_i in b} w_i,

and treat the per-event sums as the observations. With N generated events,
including the ones that left no entry,

    mu_b = sum_e t_eb / N,    sigma_b^2 = (sum_e t_eb^2 / N - mu_b^2) / (N - 1).

This is the numpy counterpart of the C++ class EventHistogram (libShipData).
Both write the same ROOT objects, which hadd merges correctly, and give the same
bootstrap replicas for the same event keys::

    h = EventHistogram("p_mu", np.geomspace(5, 400, 21), covariance=True)
    for event in tree:
        h.fill(momenta, weights)
        h.end_event(make_event_key(run, event_id))
    h.add_empty_events(n_generated - h.n_events)
    h.values(), h.errors(), h.n_eff()
"""

import json
import math

import numpy as np

_MASK64 = (1 << 64) - 1


def make_event_key(run: int, event: int) -> int:
    """Key of an event for the bootstrap replicas, as EventHistogram::MakeEventKey."""
    return ((run << 32) ^ event) & _MASK64


def _poisson1_cdf():
    """Poisson(1) distribution function, accumulated as in the C++ code."""
    p = math.exp(-1.0)
    cdf = [p]
    for k in range(1, 21):
        p /= k
        cdf.append(cdf[-1] + p)
    return np.array(cdf[:-1])


_CDF = _poisson1_cdf()


def replica_weights(key: int, n_replicas: int) -> np.ndarray:
    """Poisson(1) weights of one event for replicas 0..n-1 (EventHistogram::ReplicaWeight)."""
    r = np.arange(1, n_replicas + 1, dtype=np.uint64)
    with np.errstate(over="ignore"):
        x = np.uint64(key & _MASK64) ^ (r * np.uint64(0xD1B54A32D192ED03))
        x = x + np.uint64(0x9E3779B97F4A7C15)
        x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        x = x ^ (x >> np.uint64(31))
    u = (x >> np.uint64(11)).astype(np.float64) * 2.0**-53
    return np.searchsorted(_CDF, u, side="left")


def _buffer(array, n):
    array.reshape((n,))
    return np.frombuffer(array, dtype=np.float64, count=n)


def _cells(h):
    """Writable view of the bin contents of a ROOT histogram, flows included."""
    return _buffer(h.GetArray(), h.GetNcells())


def _sumw2(h):
    return _buffer(h.GetSumw2().GetArray(), h.GetNcells())


def _inner2(h):
    """In-range contents of a TH2D as a writable [x bin, y bin] view."""
    ny, nx = h.GetNbinsY(), h.GetNbinsX()
    return _cells(h).reshape(ny + 2, nx + 2)[1:-1, 1:-1].T


class EventHistogram:
    """Accumulate per-event bin sums; see the module docstring.

    Arrays returned by the accessors cover the in-range bins. Under- and
    overflow are kept internally (index 0 and nbins + 1) as in ROOT.
    """

    def __init__(self, name, edges, title="", covariance=False, n_replicas=0):
        self.name = name
        self.title = title
        self.edges = np.asarray(edges, dtype=float)
        nb = len(self.edges) - 1
        self.n_events = 0
        self.sum_t = np.zeros(nb + 2)
        self.sum_t2 = np.zeros(nb + 2)
        self.sum_w = np.zeros(nb + 2)
        self.sum_w2 = np.zeros(nb + 2)
        self.sum_tt = np.zeros((nb, nb)) if covariance else None
        self.boot = np.zeros((nb, n_replicas)) if n_replicas else None
        self._current = np.zeros(nb + 2)
        self._open = False

    @classmethod
    def uniform(cls, name, nbins, low, high, **kwargs):
        return cls(name, np.linspace(low, high, nbins + 1), **kwargs)

    @property
    def nbins(self):
        return len(self.edges) - 1

    def _bins(self, x):
        # ROOT convention: bin i covers [low_i, high_i), the upper edge is overflow.
        return np.searchsorted(self.edges, x, side="right")

    def fill(self, x, w=1.0):
        """Add branches (scalars or arrays) of the current event."""
        x = np.asarray(x, dtype=float)
        if x.size == 0:
            return
        w = np.broadcast_to(np.asarray(w, dtype=float), x.shape).ravel()
        bins = self._bins(x.ravel())
        t = np.bincount(bins, w, minlength=len(self._current))
        self._current += t
        self.sum_w += t
        self.sum_w2 += np.bincount(bins, w * w, minlength=len(self._current))
        self._open = True

    def end_event(self, key=0):
        """Close the current event. Use make_event_key(run, event) as key so the
        bootstrap replicas agree across files, jobs and the C++ class."""
        # Only the bins this event touched, as in the C++ class.
        idx = np.flatnonzero(self._current)
        t = self._current[idx]
        self.sum_t[idx] += t
        self.sum_t2[idx] += t * t
        inner = (idx >= 1) & (idx <= self.nbins)
        ii, ti = idx[inner] - 1, t[inner]
        if self.sum_tt is not None:
            self.sum_tt[np.ix_(ii, ii)] += np.outer(ti, ti)
        if self.boot is not None and ii.size:
            self.boot[ii] += ti[:, None] * replica_weights(key, self.boot.shape[1])[None, :]
        self._current[idx] = 0.0
        self._open = False
        self.n_events += 1

    def fill_event(self, x, w=1.0, key=0):
        self.fill(x, w)
        self.end_event(key)

    def add_empty_events(self, n):
        """Generated events that left no entry still count in the normalisation."""
        self.n_events += int(n)

    def __iadd__(self, other):
        self._check_closed("merge")
        other._check_closed("merge")
        if not np.array_equal(self.edges, other.edges):
            raise ValueError("EventHistogram: binning differs, cannot merge")
        if (self.sum_tt is None) != (other.sum_tt is None):
            raise ValueError("EventHistogram: only one has a covariance, cannot merge")
        if (self.boot is None) != (other.boot is None) or (
            self.boot is not None and self.boot.shape != other.boot.shape
        ):
            raise ValueError("EventHistogram: bootstrap replicas differ, cannot merge")
        for attr in ("sum_t", "sum_t2", "sum_w", "sum_w2", "sum_tt", "boot"):
            mine = getattr(self, attr)
            if mine is not None:
                mine += getattr(other, attr)
        self.n_events += other.n_events
        return self

    def _check_closed(self, where):
        if self._open:
            raise RuntimeError(f"EventHistogram.{where}: call end_event() first")

    # --- results, per generated event, in-range bins ---------------------------

    def values(self):
        self._check_closed("values")
        if self.n_events <= 0:
            return np.zeros(self.nbins)
        return self.sum_t[1:-1] / self.n_events

    def errors(self):
        """Event-level standard errors."""
        self._check_closed("errors")
        n = self.n_events
        if n <= 0:
            return np.zeros(self.nbins)
        m = self.sum_t[1:-1] / n
        if n < 2:
            return np.sqrt(self.sum_t2[1:-1]) / n
        return np.sqrt(np.maximum(self.sum_t2[1:-1] / n - m * m, 0.0) / (n - 1))

    def naive_errors(self):
        """sqrt(sum w^2)/N, which treats branches as independent. For comparison only."""
        if self.n_events <= 0:
            return np.zeros(self.nbins)
        return np.sqrt(self.sum_w2[1:-1]) / self.n_events

    def n_eff(self):
        """Independent events per bin, (sum t)^2 / sum t^2. Below about 20 the error
        estimate itself is unreliable: merge bins or check with the bootstrap."""
        s, s2 = self.sum_t[1:-1], self.sum_t2[1:-1]
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(s2 > 0, s * s / s2, 0.0)

    def covariance(self):
        if self.sum_tt is None:
            raise ValueError("EventHistogram: created without covariance=True")
        n = self.n_events
        if n < 2:
            return np.zeros((self.nbins, self.nbins))
        m = self.sum_t[1:-1] / n
        return (self.sum_tt / n - np.outer(m, m)) / (n - 1)

    def bootstrap_errors(self):
        if self.boot is None or self.boot.shape[1] < 2:
            raise ValueError("EventHistogram: needs at least two bootstrap replicas")
        if self.n_events <= 0:
            return np.zeros(self.nbins)
        return (self.boot / self.n_events).std(axis=1, ddof=1)

    # --- ROOT I/O, same objects as EventHistogram::Write/Read -----------------

    def to_root(self, directory):
        """Write hadd-mergeable objects, identical to the C++ EventHistogram::Write."""
        import ROOT

        self._check_closed("to_root")
        edges = np.ascontiguousarray(self.edges)
        nb = self.nbins

        def hist1(name, sums, sums2):
            h = ROOT.TH1D(name, self.title, nb, edges)
            h.SetDirectory(ROOT.nullptr)
            h.Sumw2()
            _cells(h)[:] = sums
            _sumw2(h)[:] = sums2
            h.SetEntries(self.n_events)
            return h

        def hist2(name, title, values, *yaxis):
            h = ROOT.TH2D(name, title, nb, edges, *yaxis)
            h.SetDirectory(ROOT.nullptr)
            _inner2(h)[:] = values
            return h

        objects: list = [
            hist1(self.name, self.sum_t, self.sum_t2),
            hist1(self.name + "_naive", self.sum_w, self.sum_w2),
        ]
        if self.sum_tt is not None:
            objects.append(hist2(self.name + "_cov", "sum over events of t_a t_b", self.sum_tt, nb, edges))
        if self.boot is not None:
            nrep = self.boot.shape[1]
            objects.append(hist2(self.name + "_boot", "bootstrap replicas;;replica", self.boot, nrep, 0.0, float(nrep)))
        objects.append(ROOT.TParameter("Long64_t")(self.name + "_nevents", self.n_events, "+"))
        for obj in objects:
            directory.WriteTObject(obj, obj.GetName(), "Overwrite")

    @classmethod
    def from_root(cls, directory, name):
        """Restore an accumulator written by to_root() or the C++ class (also after hadd)."""
        h = directory.Get(name)
        naive = directory.Get(name + "_naive")
        nevents = directory.Get(name + "_nevents")
        if not h or not naive or not nevents:
            raise KeyError(f"EventHistogram {name} not found in {directory.GetName()}")
        axis = h.GetXaxis()
        nb = axis.GetNbins()
        edges = [axis.GetBinLowEdge(i) for i in range(1, nb + 2)]
        cov = directory.Get(name + "_cov")
        boot = directory.Get(name + "_boot")
        self = cls(name, edges, title=h.GetTitle(), covariance=bool(cov), n_replicas=boot.GetNbinsY() if boot else 0)
        self.sum_t[:], self.sum_t2[:] = _cells(h), _sumw2(h)
        self.sum_w[:], self.sum_w2[:] = _cells(naive), _sumw2(naive)
        if self.sum_tt is not None:
            self.sum_tt[:] = _inner2(cov)
        if self.boot is not None:
            self.boot[:] = _inner2(boot)
        self.n_events = int(nevents.GetVal())
        return self


def generated_events(tfile) -> int:
    """Number of generated events of a FairShip output file, from its FileSummary.

    FairShip only writes events with activity, so the number of entries of the
    tree is not the normalisation.
    """
    summary = tfile.Get("FileSummary")
    if not summary:
        raise KeyError(f"{tfile.GetName()} has no FileSummary")
    fsr = json.loads(str(summary))
    for key in ("nev", "nEvents"):
        if key in fsr:
            return int(fsr[key])
    raise KeyError(f"FileSummary of {tfile.GetName()} has no event count ('nev' or 'nEvents')")
