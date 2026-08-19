# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Helpers for locating particles of interest in the MC truth record.

Shared by the analysis macros so the conventions live in a single place rather
than being rediscovered (and hardcoded) at every call site.
"""

# Process name FairShip gives to tracks put on the stack by the generator, as
# opposed to those created by Geant during transport.
PRIMARY_PROCESS = "Primary particle emission"


def find_signal_track(mc_tracks, pdg=None):
    """Return the index of the signal particle in ``mc_tracks``, or ``None``.

    The signal (HNL, dark photon, dark scalar, ...) does not sit at a fixed
    position: the generators store a variable amount of the production chain
    ahead of it, so it can be track 0, 1 or 2 depending on the configuration.
    Its PDG code is not a reliable handle either, since external-input
    generators use placeholders. Hence this lookup.

    Parameters
    ----------
    mc_tracks : sequence
        The ``MCTrack`` branch. Indexing and ``len()`` are used rather than
        ``At()``/``GetEntriesFast()`` so that both ``std::vector<ShipMCTrack>``
        and ``TClonesArray`` work.
    pdg : int, optional
        The signal PDG code, when the caller knows it. Otherwise the signal is
        inferred from the shape of the generator record, as described below.
        Pass ``pdg`` where it is available.

    Notes
    -----
    A signal event is generated as a single production chain -- optionally a
    grandmother and a mother, then the signal -- followed by the signal's decay
    products. So among the tracks the generator put on the stack there is
    exactly one root, and the signal is the deepest one that has a daughter
    also on the stack.

    Requiring a single root is what keeps this honest on background samples,
    where the generator stack is a branching cascade with several roots: those
    give ``None`` rather than an arbitrary resonance decay.
    """
    if pdg is not None:
        for i in range(len(mc_tracks)):
            if abs(mc_tracks[i].GetPdgCode()) == abs(pdg):
                return i
        return None

    n_tracks = len(mc_tracks)
    stack = {i for i in range(n_tracks) if mc_tracks[i].GetProcName() == PRIMARY_PROCESS}

    def mother_on_stack(i):
        mother = mc_tracks[i].GetMotherId()
        return mother if mother in stack else None

    roots = [i for i in stack if mother_on_stack(i) is None]
    if len(roots) != 1:
        return None

    with_daughters = {mother_on_stack(i) for i in stack if mother_on_stack(i) is not None}
    return max(with_daughters) if with_daughters else None


def signal_weight(mc_tracks, pdg=None, default=1.0):
    """Return the event weight carried by the signal track.

    Every generator stores the per-event weight on the signal, so this is the
    robust way to read it. Falls back to ``default`` when no signal is found.
    """
    signal_id = find_signal_track(mc_tracks, pdg)
    if signal_id is None:
        return default
    weight = mc_tracks[signal_id].GetWeight()
    return weight if weight > 0.0 else default
