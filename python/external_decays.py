# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Let the VMC external decayer decay charm and bottom hadrons.

Geant4 gives every charm and bottom hadron a placeholder decay table, a
single hadronic channel with a branching ratio of 1 decayed by phase space
(``G4HadronicBuilder::BuildDecayTableForBCHadrons``). It builds them while
constructing the physics, after FairRoot has run ``DecayConfig()``, so
``gMC->SetUserDecay`` and ``/mcPhysics/setExtDecayerSelection`` cannot remove
them. Geant4 uses the external decayer only for particles without a decay
table, so the tables are removed here, after ``run.Init()``.
"""

import ROOT

ROOT.gROOT.ProcessLine('#include "Geant4/G4ParticleTable.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4HadParticles.hh"')


def use_external_decayer_for_heavy_flavour() -> list[int]:
    """Remove Geant4's decay tables of charm and bottom hadrons.

    Call after ``run.Init()``, with an external decayer set. Returns the PDG
    codes whose decay table was removed.
    """
    mc = ROOT.TVirtualMC.GetMC()
    if not mc or not mc.GetDecayer():
        raise RuntimeError("No VMC external decayer: charm and bottom hadrons would not decay")
    table = ROOT.G4ParticleTable.GetParticleTable()
    removed = []
    for pdg in ROOT.G4HadParticles.GetBCHadrons():
        particle = table.FindParticle(int(pdg))
        if particle and particle.GetDecayTable():
            particle.SetDecayTable(ROOT.nullptr)
            removed.append(int(pdg))
    return removed
