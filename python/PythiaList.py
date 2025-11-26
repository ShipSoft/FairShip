# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import ROOT,time,sys
id=int(sys.argv[1])
ROOT.gSystem.Load("libEG")
ROOT.gSystem.Load("libpythia8")
ROOT.gSystem.Load("libEGPythia8")
myPythia = ROOT.TPythia8()
PDG = ROOT.TDatabasePDG.Instance()
myPythia.Plist(id)
