# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Provenance of split kaon/pion tracks: which tracks can exist together.

Splitting (exitHadronAbsorber, --kaon-pion-splits) replaces the decay of a
kaon or pion by weighted alternatives. They are mutually exclusive histories,
not particles that exist together, but in the MC track tree they look like
siblings of the split track. ShipMCTrack records them in split sets:

* every track created for one split track shares its split set
  (GetSplitSet(), -1 if none);
* the split track and its continuations are the survivor line
  (kSplitSurvivor), the clones each stand for one of its decays
  (kSplitDecay), with probability weight / GetSplitWeight();
* GetSplitWeight() is the weight of the split track before splitting.

Single-particle quantities need none of this: sum weights as usual. Anything
that combines several tracks of an event does:

* compatible(i, j): can tracks i and j exist in the same real event? Two
  different decay alternatives of one set cannot. A decay at time t and a
  track that left the survivor line at time t' can only if t' < t.
* pair_weight(i, j): the weight that makes pair observables unbiased,
  w_i w_j / w_a, where w_a is the weight of the line at the point where the
  two tracks part. It is 0 for incompatible pairs.
* desplit(rng): draw one outcome per split set with the right probabilities
  and return which tracks exist in that analog-like event. Each kept track
  then stands for the event with the weight of its primary. Useful for
  multiplicities, coincidences, triggers and occupancy, which weights cannot
  describe.

The weights of a survivor line's secondaries must be the line's weight when
they were created. Times are the start times of the tracks (ns).

A minimal example::

    prov = SplitProvenance.from_tracks(event.MCTrack)
    w = prov.pair_weight(mu1, mu2)          # 0 if the muons are alternatives
    keep = prov.desplit(rng).keeps_track    # analog-like selection of tracks
"""

import math
from dataclasses import dataclass

import numpy as np

NOT_SPLIT, SURVIVOR, DECAY = 0, 1, 2
K_NO_PROCESS = 44  # TMCProcess kPNoProcess: clones and continuations


@dataclass(frozen=True)
class _Link:
    """How a lineage passes through one split set."""

    split_set: int
    role: int
    member: int  # the set member on the lineage
    branch_time: float  # decay: start of the clone; survivor: where the lineage leaves the line
    branch_weight: float  # weight of the line at branch_time (survivor) or of the clone (decay)


class SplitProvenance:
    """Split-set structure of one event; see the module docstring."""

    def __init__(self, mother, split_set, split_role, split_weight, start_t, weight, proc_id=None):
        self.mother = np.asarray(mother, dtype=int)
        self.split_set = np.asarray(split_set, dtype=int)
        self.split_role = np.asarray(split_role, dtype=int)
        self.split_weight = np.asarray(split_weight, dtype=float)
        self.start_t = np.asarray(start_t, dtype=float)
        self.weight = np.asarray(weight, dtype=float)
        # Continuations are pushed by the splitting code (no process); the
        # original split track was made by Geant4.
        self.continuation = (
            np.zeros(len(self.mother), dtype=bool)
            if proc_id is None
            else (np.asarray(proc_id, dtype=int) == K_NO_PROCESS) & (self.split_role == SURVIVOR)
        )
        self.sets = {}
        for i in np.flatnonzero(self.split_set >= 0):
            entry = self.sets.setdefault(
                int(self.split_set[i]), {"W": float(self.split_weight[i]), "decays": [], "survivors": []}
            )
            entry["decays" if self.split_role[i] == DECAY else "survivors"].append(int(i))
        for entry in self.sets.values():
            entry["decays"].sort(key=lambda c: self.start_t[c])
            entry["survivors"].sort(key=lambda c: self.start_t[c])
            entry["stored"] = float(sum(self.weight[c] for c in entry["decays"]))
        self._lineages = {}

    @classmethod
    def from_tracks(cls, tracks):
        """From a sequence of ShipMCTrack (e.g. event.MCTrack)."""
        rows = [
            (
                t.GetMotherId(),
                t.GetSplitSet(),
                t.GetSplitRole(),
                t.GetSplitWeight(),
                t.GetStartT(),
                t.GetWeight(),
                t.GetProcID(),
            )
            for t in tracks
        ]
        if not rows:
            return cls([], [], [], [], [], [], [])
        return cls(*zip(*rows))

    def __len__(self):
        return len(self.mother)

    # --- structure -------------------------------------------------------------

    def lineage(self, i):
        """Track i and its ancestors, nearest first."""
        if i not in self._lineages:
            line = [i]
            while self.mother[line[-1]] >= 0 and len(line) <= len(self):
                line.append(int(self.mother[line[-1]]))
            self._lineages[i] = line
        return self._lineages[i]

    def initial_weight(self, i):
        """Weight of track i when it was created (before any split of its own)."""
        return self.split_weight[i] if self.split_set[i] >= 0 else self.weight[i]

    def _line_weight_at_start(self, a):
        """Weight of the survivor line where survivor track a starts."""
        if not self.continuation[a]:
            return self.split_weight[a]
        # A continuation starts where the track it continues ended, with that
        # track's final weight. If that track was not stored, a's own final
        # weight is the closest lower bound.
        earlier = [b for b in self.sets[int(self.split_set[a])]["survivors"] if self.start_t[b] < self.start_t[a]]
        return self.weight[earlier[-1]] if earlier else self.weight[a]

    def _links(self, i, t_obs, at_start=False):
        """Split sets on the lineage of i (at most one member each, since members are siblings).

        If i is itself on a survivor line, it is observed at t_obs with its
        stored weight (the weight at the end of its path, e.g. at the scoring
        plane where tracks stop), or with at_start at its own start.
        """
        line = self.lineage(i)
        links = {}
        for k, a in enumerate(line):
            s = self.split_set[a]
            if s < 0:
                continue
            if self.split_role[a] == DECAY:
                links[int(s)] = _Link(int(s), DECAY, a, self.start_t[a], self.weight[a])
            elif k == 0 and at_start:
                links[int(s)] = _Link(int(s), SURVIVOR, a, self.start_t[a], self._line_weight_at_start(a))
            elif k == 0:
                links[int(s)] = _Link(int(s), SURVIVOR, a, t_obs, self.weight[a])
            else:
                child = line[k - 1]
                links[int(s)] = _Link(int(s), SURVIVOR, a, self.start_t[child], self.initial_weight(child))
        return links

    # --- pairs -------------------------------------------------------------------

    def compatible(self, i, j, t_i=math.inf, t_j=math.inf):
        """Whether tracks i and j can exist in the same real event.

        t_i, t_j: when a survivor-line track is itself the observed object (e.g.
        a hit of the split kaon), the time of that observation.
        """
        li, lj = self._links(i, t_i), self._links(j, t_j)
        for s in li.keys() & lj.keys():
            a, b = li[s], lj[s]
            if a.member == b.member:
                continue
            if a.role == DECAY and b.role == DECAY:
                return False
            if a.role == DECAY and not b.branch_time < a.branch_time:
                return False
            if b.role == DECAY and not a.branch_time < b.branch_time:
                return False
        return True

    def pair_weight(self, i, j, t_i=math.inf, t_j=math.inf):
        """Weight of the pair (i, j) for unbiased pair observables; 0 if incompatible."""
        if i == j or not self.compatible(i, j, t_i, t_j):
            return 0.0
        line_i, line_j = self.lineage(i), self.lineage(j)
        on_j = set(line_j)
        m = next((a for a in line_i if a in on_j), None)
        if m is None:
            # No common ancestor: two primaries of the same event.
            w_a = max(self.initial_weight(line_i[-1]), self.initial_weight(line_j[-1]))
            return self.weight[i] * self.weight[j] / w_a
        if m in (i, j):
            # One is an ancestor of the other: the pair stands for the descendant.
            return self.weight[j] if m == i else self.weight[i]
        ci = line_i[line_i.index(m) - 1]
        cj = line_j[line_j.index(m) - 1]
        s = self.split_set[ci]
        if s >= 0 and s == self.split_set[cj]:
            # The lineages part inside one split set: at a decay on the survivor
            # line, or where each leaves the survivor line.
            a, b = self._links(i, t_i)[int(s)], self._links(j, t_j)[int(s)]
            if a.role == DECAY:
                w_a = b.branch_weight
            elif b.role == DECAY:
                w_a = a.branch_weight
            else:
                w_a = max(a.branch_weight, b.branch_weight)
        else:
            # The lineages part at m; its weight there is that of the earlier child.
            w_a = max(self.initial_weight(ci), self.initial_weight(cj))
        return self.weight[i] * self.weight[j] / w_a

    # --- de-splitting --------------------------------------------------------------

    def desplit(self, rng):
        """Draw one outcome per split set; see Desplit."""
        return Desplit(self, rng)


class Desplit:
    """One analog-like realisation of a split event.

    For every split set one outcome is drawn with probability proportional to
    its weight: one of the stored decay alternatives, or "something else" (a
    decay whose clones were pruned, or no decay at all). In the latter case a
    second number decides how far along the survivor line the track got, so
    that survivor-line tracks are kept consistently. A kept track stands for
    the event with the weight of its primary, analog_weight(i).
    """

    def __init__(self, prov, rng):
        self.prov = prov
        self.choice = {}
        for s, e in prov.sets.items():
            u = rng.random() * e["W"]
            chosen, cum = None, 0.0
            for c in e["decays"]:
                if u < cum + prov.weight[c]:
                    chosen = c
                    break
                cum += prov.weight[c]
            # Given no stored alternative, u - stored is uniform on [0, W - stored).
            self.choice[s] = (chosen, u - e["stored"])
        self.keeps_track = np.array([self.keeps(i) for i in range(len(prov))], dtype=bool)

    def _survives_to(self, s, branch_time, branch_weight):
        prov = self.prov
        chosen, v = self.choice[s]
        if chosen is not None:
            return branch_time < prov.start_t[chosen]
        later = sum(prov.weight[c] for c in prov.sets[s]["decays"] if prov.start_t[c] > branch_time)
        return v < branch_weight - later

    def keeps(self, i, t_obs=None):
        """Whether track i exists, or for t_obs its observation at that time."""
        links = self.prov._links(i, math.inf, at_start=True) if t_obs is None else self.prov._links(i, t_obs)
        for s, link in links.items():
            if link.role == DECAY:
                if self.choice[s][0] != link.member:
                    return False
            elif not self._survives_to(s, link.branch_time, link.branch_weight):
                return False
        return True

    def keeps_point(self, i, t):
        """Whether a hit of track i at time t exists (matters for survivor-line tracks)."""
        return self.keeps(i, t_obs=t)

    def analog_weight(self, i):
        """Weight a kept track carries in the de-split event: that of its primary."""
        return self.prov.initial_weight(self.prov.lineage(i)[-1])
