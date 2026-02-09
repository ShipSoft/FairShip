# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import evd_fillEnergy
import eveGlobal
import ROOT


def execute():
    ROOT.gROOT.GetListOfGlobals()
    SHiPDisplay = eveGlobal.SHiPDisplay
    SHiPDisplay.NextEvent()
    if ROOT.gROOT.FindObject("Root Canvas"):
        evd_fillEnergy.execute()
    pass


if __name__ == "__main__":
    execute()
