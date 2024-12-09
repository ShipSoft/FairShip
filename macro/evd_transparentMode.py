import eveGlobal
import ROOT

SHiPDisplay = eveGlobal.SHiPDisplay
if SHiPDisplay.TransparentMode == 0:
    SHiPDisplay.transparentMode()
else:
    SHiPDisplay.transparentMode("off")
