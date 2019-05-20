import ROOT
lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
SHiPDisplay = lsOfGlobals.FindObject('SHiP Displayer')
if SHiPDisplay.TransparentMode == 0 : SHiPDisplay.transparentMode()
else: SHiPDisplay.transparentMode('off')
