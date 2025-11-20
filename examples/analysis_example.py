#!/usr/bin/env python
"""Example script for usage of the analysis_toolkit for signal selection."""

from argparse import ArgumentParser

import ROOT
import rootUtils as ut
from experimental import analysis_toolkit
from backports import tdirectory634


def main():
    """Sample function to analyse the pre-selection parameters."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("-f", "--simfile", help="MC simulation file", default="ship.conical.Pythia8-TGeant4.root")
    parser.add_argument("-r", "--recofile", help="Reconstruction file", default="ship.conical.Pythia8-TGeant4_rec.root")
    parser.add_argument("-g", "--geofile", help="Geometry file", default="geofile_full.conical.Pythia8-TGeant4.root")
    options = parser.parse_args()

    # Open MC simulation file
    f = ROOT.TFile.Open(options.simfile, "read")
    if not f or f.IsZombie():
        import os
        print(f"ERROR: Cannot open MC simulation file: {options.simfile}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Files in current directory:")
        os.system("ls -lh *.root")
        raise RuntimeError(f"Cannot open MC simulation file: {options.simfile}")

    # Check what trees are in the file
    keys = [k.GetName() for k in f.GetListOfKeys()]
    print(f"Keys in {options.simfile}: {keys}")

    if "cbmsim" not in keys:
        print(f"ERROR: MC simulation file {options.simfile} does not contain 'cbmsim' tree")
        print(f"Available keys: {keys}")
        raise RuntimeError(f"MC simulation file does not contain 'cbmsim' tree")

    tree = f["cbmsim"]

    # Add reconstruction data as friend tree
    reco_f = ROOT.TFile.Open(options.recofile, "read")
    if not reco_f or reco_f.IsZombie():
        raise RuntimeError(f"Cannot open reconstruction file: {options.recofile}")

    reco_keys = [k.GetName() for k in reco_f.GetListOfKeys()]
    print(f"Keys in {options.recofile}: {reco_keys}")

    tree.AddFriend("ship_reco_sim", options.recofile)

    geo_file = ROOT.TFile.Open(options.geofile, "read")
    if not geo_file or geo_file.IsZombie():
        raise RuntimeError(f"Cannot open geometry file: {options.geofile}")

    selection = analysis_toolkit.selection_check(geo_file)
    inspector = analysis_toolkit.event_inspector()

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

        print(f"Event{event_nr}:")
        inspector.dump_event(event, mom_threshold=0.5)  # in GeV

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

    ut.writeHists(hist_dict, "preselectionparameters.root")


if __name__ == "__main__":
    main()
