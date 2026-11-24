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
    products, which can decay further (quarks, hadrons). So among the tracks
    the generator put on the stack there is exactly one root, each member of
    the production chain has the next one as its only daughter, and the signal
    is the first track whose daughters are its decay products: more than one
    daughter, or a single daughter that has none of its own.

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
    mothers = {i: mc_tracks[i].GetMotherId() for i in stack}

    roots = [i for i in stack if mothers[i] not in stack]
    if len(roots) != 1:
        return None

    # Walk down the production chain from the root to the signal.
    signal = roots[0]
    while True:
        daughters = [i for i in stack if mothers[i] == signal]
        if not daughters:
            return None
        if len(daughters) > 1 or not any(mothers[i] == daughters[0] for i in stack):
            return signal
        signal = daughters[0]


def is_signal_product(mc_tracks, index, signal_id):
    """Return whether track ``index`` is a decay product of the signal.

    A decay product is a track the generator put on the stack whose chain of
    mothers leads to ``signal_id``. That includes the hadrons of a hadronic
    decay, which are granddaughters or deeper because the generator also
    stores the quarks and resonances in between. Geant secondaries, such as a
    delta ray knocked out by a decay product, are not decay products.
    """
    if mc_tracks[index].GetProcName() != PRIMARY_PROCESS:
        return False
    mother = mc_tracks[index].GetMotherId()
    while mother >= 0:
        if mother == signal_id:
            return True
        mother = mc_tracks[mother].GetMotherId()
    return False


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
