# example for dumping an MC event
import ROOT,os,sys,getopt
import rootUtils as ut
import shipunit as u
import ShipGeoConfig
ship_geo = ShipGeoConfig.Config().loadpy("$FAIRSHIP/geometry/geometry_config.py")
def dump(i,pcut):
 tree = ROOT.gROOT.FindObjectAny('cbmsim')
 tree.GetEntry(i)
 print '    #  pid   px    py    pz   vx   vy   vz   mid'
 n=-1
 for mcp in tree.MCTrack: 
   n+=1
   if mcp.GetP()/u.GeV < pcut :  continue
   print '%6i %10i %6.3F %6.3F %7.3F %6.3F %6.3F %7.3F %6i '%(n,mcp.GetPdgCode(),mcp.GetPx()/u.GeV,mcp.GetPy()/u.GeV,mcp.GetPz()/u.GeV, \
                      mcp.GetStartX()/u.m,mcp.GetStartY()/u.m,mcp.GetStartZ()/u.m,mcp.GetMotherId()   )

