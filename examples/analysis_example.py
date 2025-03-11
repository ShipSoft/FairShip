#!/usr/bin/env python
"""Example script for usage of the analysis_toolkit for signal selection."""

from argparse import ArgumentParser

import ROOT
import rootUtils as ut
from experimental import analysis_toolkit


def main():
    """Sample function to analyse the pre-selection parameters."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--path", help="Path to simulation file", default="./")
    options = parser.parse_args()

    f = ROOT.TFile.Open(options.path + "/ship.conical.Pythia8-TGeant4_rec.root", "read")
    tree = f.cbmsim

    geo_file = ROOT.TFile.Open(
        options.path + "/geofile_full.conical.Pythia8-TGeant4.root", "read"
    )

    selection = analysis_toolkit.selection_check(geo_file)
    hist_dict = {}

    ut.bookHist(hist_dict, "event_weight", "Event weight", 100, 100, 100)
    ut.bookHist(
        hist_dict,
        "candidate_time",
        "candidate time @ decay vertex; ns",
        200,
        100,
        100,
    )
    ut.bookHist(hist_dict, "impact_parameter", "Impact parameter; cm", 200, 100, 100)
    ut.bookHist(
        hist_dict, "dist_to_innerwall", "Distance to inner wall; cm", 200, 100, 100
    )
    ut.bookHist(
        hist_dict,
        "dist_to_vesselentrance",
        "Distance to Decay Vessel Entrance; cm",
        200,
        100,
        100,
    )
    ut.bookHist(hist_dict, "inv_mass", "Invariant mass; GeV", 200, 100, 100)
    ut.bookHist(hist_dict, "DOCA", "Distance of closest approach; cm", 200, 100, 100)
    ut.bookHist(
        hist_dict,
        "len_Particles",
        "len(tree.Particles); Number of candidates per event",
        200,
        100,
        100,
    )
    ut.bookHist(
        hist_dict,
        "d_mom",
        "momentum of daughters; d1 (GeV); d2 (GeV)",
        200,
        100,
        100,
        200,
        100,
        100,
    )
    ut.bookHist(hist_dict, "nDOF", "nDOF; d1; d2", 200, 100, 100, 200, 100, 100)
    ut.bookHist(hist_dict, "chi2nDOF", "chi2nDOF; d1; d2", 200, 100, 100, 200, 100, 100)

    for event_nr, event in enumerate(tree):
        selection.access_event(event)
        if len(event.Particles) == 0:
            continue

        event_weight = event.MCTrack[2].GetWeight()

        hist_dict["event_weight"].Fill(event_weight)

        for candidate_id_in_event, signal in enumerate(event.Particles):
            hist_dict["candidate_time"].Fill(selection.define_candidate_time(signal))
            hist_dict["impact_parameter"].Fill(selection.impact_parameter(signal))
            hist_dict["dist_to_innerwall"].Fill(selection.dist_to_innerwall(signal))
            hist_dict["dist_to_vesselentrance"].Fill(
                selection.dist_to_vesselentrance(signal)
            )
            hist_dict["DOCA"].Fill(selection.DOCA(signal))
            hist_dict["inv_mass"].Fill(selection.invariant_mass(signal))
            hist_dict["len_Particles"].Fill(len(tree.Particles))
            hist_dict["d_mom"].Fill(*selection.daughtermomentum(signal))
            hist_dict["nDOF"].Fill(*selection.nDOF(signal))
            hist_dict["chi2nDOF"].Fill(*selection.chi2nDOF(signal))

            IP_cut = 250
            preselection_flag = selection.preselection_cut(
                signal, IP_cut=IP_cut, show_table=False
            )

            if preselection_flag:
                print(
                    f"Event:{event_nr} Candidate_index: {candidate_id_in_event} <--passes the pre-selection\n\n"
                )
            else:
                print(f"Event:{event_nr} Candidate_index: {candidate_id_in_event} \n\n")

    ut.writeHists(hist_dict, "preselectionparameters.root")


if __name__ == "__main__":
    main()
