import ROOT#,evd_fillEnergy

def execute():
  lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
  SHiPDisplay = lsOfGlobals.FindObject('SHiP Displayer')
  SHiPDisplay.NextEvent()
  if ROOT.gROOT.FindObject('Root Canvas'): evd_fillEnergy.execute()
  pass
if __name__=="__main__":
  execute()
