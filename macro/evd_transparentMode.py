# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import ROOT
import  eveGlobal
SHiPDisplay = eveGlobal.SHiPDisplay
if SHiPDisplay.TransparentMode == 0 : SHiPDisplay.transparentMode()
else: SHiPDisplay.transparentMode('off')
