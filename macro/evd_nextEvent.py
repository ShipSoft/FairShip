import ROOT#,evd_fillEnergy
import  eveGlobal
def execute():
  lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
  SHiPDisplay = eveGlobal.SHiPDisplay
  SHiPDisplay.NextEvent()
  if ROOT.gROOT.FindObject('Root Canvas'): evd_fillEnergy.execute()
  pass
if __name__=="__main__":
  execute()
