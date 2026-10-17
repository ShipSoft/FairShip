# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Add the DIS cross section to the output of a legacy ``--MuDIS`` simulation."""

import os
from array import array

import ROOT


def add_cross_section(output_file: str, dis_file: str, first_event: int = 0) -> None:
    """Add a ``CrossSection`` branch to ``cbmsim`` with the DIS cross section of each event.

    ``MuDISGenerator`` reads only ``dis_file`` (the first input file), starting
    at entry ``first_event`` and starting again from entry 0 after the last
    one, so output event ``i`` comes from DIS entry ``(first_event + i) % n``.
    The cross section is ``InMuon[0][10]`` of that entry, in mbarn.
    """
    temp_file = output_file.replace(".root", "_tmp.root")
    with (
        ROOT.TFile.Open(output_file, "read") as source,
        ROOT.TFile.Open(dis_file, "read") as dis_source,
        ROOT.TFile.Open(temp_file, "recreate") as destination,
    ):
        output_tree = source["cbmsim"]
        dis_tree = dis_source["DIS"]
        n_dis = dis_tree.GetEntries()

        destination.cd()
        new_tree = output_tree.CloneTree(0)
        cross_section = array("f", [0.0])
        new_tree.Branch("CrossSection", cross_section, "CrossSection/F")

        for entry in range(output_tree.GetEntries()):
            output_tree.GetEntry(entry)
            dis_tree.GetEntry((first_event + entry) % n_dis)
            cross_section[0] = dis_tree.InMuon[0][10]
            new_tree.Fill()

        new_tree.Write("", ROOT.TObject.kOverwrite)

    os.replace(temp_file, output_file)
