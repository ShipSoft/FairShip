#!/usr/bin/env python
"""Example script for usage of the analysis_toolkit for signal selection ."""

import analysis_toolkit
import ROOT

geo_file = "geofile_full.conical.Pythia8-TGeant4.root"
input_file = "ship.conical.Pythia8-TGeant4_rec.root"

f = ROOT.TFile.Open(input_file)
tree = f.cbmsim

selection = analysis_toolkit.selection_check(geo_file)

for event_nr, event in enumerate(tree):
    if event_nr > 200:
        break

    selection.access_event(event)

    if len(event.Particles) == 0:
        continue

    for candidate_id_in_event, signal in enumerate(tree.Particles):
        print(f"Event:{event_nr} Candidate_index: {candidate_id_in_event}")

        print(f"\t vertex time: {selection.define_candidate_time(signal)} ns")
        print(f"\t Impact Parameter: {selection.impact_parameter(signal)} cm")
        print(f"\t is within Fiducial volume: {selection.is_in_fiducial(signal)}")
        print(f"\t\tDist2InnerWall: {selection.dist_to_innerwall(signal)} cm")
        print(f"\t\tDist2EntranceLid: {selection.dist_to_entrance_vessel(signal)} cm")
        print(f"\t Daughter momentum>1 GeV: {selection.daughtermomentum(signal)} GeV")
        print(f"\t Invariant mass: {selection.invariant_mass(signal)} GeV")
        print(f"\t Degrees of Freedom ([d1,d2],Cut(>25)): {selection.nDOF(signal)}")
        print(f"\t Reduced Chi^2  ([d1,d2],Cut(<5): {selection.chi2nDOF(signal)}")
        print(f"\t DOCA: {selection.DOCA(signal)} cm")

        print(
            f"\t Preselection Cut passed:{selection.preselection_cut(signal,IP_cut=250)}"
        )
        print("------------------------------------------------------------")
