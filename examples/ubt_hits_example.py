#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Print UBT hits with the MC points they were made from (digiUBT2MC, digiUBT2MCADC)."""

from argparse import ArgumentParser

import ROOT


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("-f", "--simfile", help="MC simulation file", required=True)
    parser.add_argument("-r", "--recofile", help="Reconstruction file", required=True)
    parser.add_argument("-n", "--nEvents", help="Number of events to print", type=int, default=5)
    options = parser.parse_args()

    # Keep the files open while their trees are used.
    sim_file = ROOT.TFile.Open(options.simfile, "read")
    sim = sim_file["cbmsim"]
    reco_file = ROOT.TFile.Open(options.recofile, "read")
    reco = reco_file["ship_reco_sim"]

    for event in range(min(options.nEvents, reco.GetEntries())):
        # Entry i of the reco tree belongs to entry i of the simulation tree.
        sim.GetEntry(event)
        reco.GetEntry(event)
        print(f"Event {event}: {reco.Digi_UpstreamTaggerHits.size()} UBT hits")

        # One entry per hit in each of the three branches, in the same order.
        for hit, indices, signals in zip(reco.Digi_UpstreamTaggerHits, reco.digiUBT2MC, reco.digiUBT2MCADC):
            print(f"  tile {hit.GetTileID()}: ADC {hit.GetADC()}, triggered {bool(hit.IsTriggered())}")
            # Each point index goes with the ADC signal of that point.
            for index, signal in zip(indices, signals):
                point = sim.UpstreamTaggerPoint[index]
                print(
                    f"    point {index}: PDG {point.PdgCode()}, track {point.GetTrackID()}, "
                    f"Edep {1000.0 * point.GetEnergyLoss():.3f} MeV, ADC {signal:.1f}"
                )


if __name__ == "__main__":
    main()
