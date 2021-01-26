import ROOT
import  eveGlobal
SHiPDisplay = eveGlobal.SHiPDisplay
if SHiPDisplay.TransparentMode == 0 : SHiPDisplay.transparentMode()
else: SHiPDisplay.transparentMode('off')
