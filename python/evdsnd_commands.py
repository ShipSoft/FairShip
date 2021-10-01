import ROOT
import  eveGlobal
import sys

def nextEvent():
  SHiPDisplay = eveGlobal.SHiPDisplay
  SHiPDisplay.NextEvent()
  pass

def transparentMode():
  SHiPDisplay = eveGlobal.SHiPDisplay
  if SHiPDisplay.TransparentMode == 0 : SHiPDisplay.transparentMode()
  else: SHiPDisplay.transparentMode('off')

def light(step):
  SHiPDisplay = eveGlobal.SHiPDisplay
  SHiPDisplay.light(step)
