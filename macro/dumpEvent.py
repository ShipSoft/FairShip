from __future__ import print_function
from __future__ import division
# example for dumping an MC event
import ROOT,os,sys
import rootUtils as ut
import shipunit as u
import ShipGeoConfig
ship_geo = ShipGeoConfig.Config().loadpy("$FAIRSHIP/geometry/geometry_config.py")
PDG = ROOT.TDatabasePDG.Instance()

def printMCTrack(n,MCTrack):
   mcp = MCTrack[n]
   print(' %6i %7i %6.3F %6.3F %7.3F %7.3F %7.3F %7.3F %6i '%(n,mcp.GetPdgCode(),mcp.GetPx()/u.GeV,mcp.GetPy()/u.GeV,mcp.GetPz()/u.GeV, \
                      mcp.GetStartX()/u.m,mcp.GetStartY()/u.m,mcp.GetStartZ()/u.m,mcp.GetMotherId()   ))

def dump(i,pcut):
 tree = ROOT.gROOT.FindObjectAny('cbmsim')
 tree.GetEntry(i)
 print('   #         pid   px    py      pz     vx      vy       vz      mid')
 n=-1
 for mcp in tree.MCTrack: 
   n+=1
   if mcp.GetP()/u.GeV < pcut :  continue
   printMCTrack(n,tree.MCTrack)
def dumpStraw(i):
 tree = ROOT.gROOT.FindObjectAny('cbmsim')
 tree.GetEntry(i)
 for aStraw in tree.strawtubesPoint: 
   trID = astraw.GetTrackID()
   if not trID < 0:
      printMCTrack(trID,tree.MCTrack)
