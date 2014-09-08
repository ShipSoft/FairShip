import shipunit as u
# import geant4 submodules
# requires to have ${SIMPATH}/lib/Geant4/ in PYTHONPATH
from G4global import *
from G4run import *
from G4geometry import *
import hepunit as G4Unit
gTransportationManager = G4TransportationManager.GetTransportationManager()


def setMagnetField():
    ironField = G4Unit.tesla * 1.85
    magFieldIron = G4UniformMagField(G4ThreeVector(0.,ironField,0.))
    FieldIronMgr = G4FieldManager(magFieldIron)
    FieldIronMgr.CreateChordFinder(magFieldIron)
    RetField    = G4UniformMagField(G4ThreeVector(0.,-ironField,0.))
    RetFieldMgr = G4FieldManager(RetField)
    RetFieldMgr.CreateChordFinder(RetField)    
    ConLField    = G4UniformMagField(G4ThreeVector(ironField,0.,0.))
    ConLFieldMgr = G4FieldManager(ConLField)
    ConLFieldMgr.CreateChordFinder(ConLField)    
    ConRField    = G4UniformMagField(G4ThreeVector( -ironField,0.,0.))
    ConRFieldMgr = G4FieldManager(ConRField)
    ConRFieldMgr.CreateChordFinder(ConRField)    
    gt = gTransportationManager
    gn = gt.GetNavigatorForTracking()
    world = gn.GetWorldVolume().GetLogicalVolume()
    for da in range(world.GetNoDaughters()):
        vl = world.GetDaughter(da)
        vln = vl.GetName().__str__()
        lvl = vl.GetLogicalVolume()
        if vln in ['MagRetA','MagRetB','MagRetC1','MagRetC2','MagRetC3','MagRetC4']:
          lvl.SetFieldManager(RetFieldMgr,True)   
        if vln in ['MagA','MagB','MagC1','MagC2','MagC3','MagC4']:        
          lvl.SetFieldManager(FieldIronMgr,True) 
        if vln in ['MagConAL']: 
          lvl.SetFieldManager(ConLFieldMgr,True) 
        if vln in ['MagConAR']: 
          lvl.SetFieldManager(ConRFieldMgr,True) 
    g4Run = G4RunManager.GetRunManager()
    g4Run.GeometryHasBeenModified(True)
def debug():
  gt = gTransportationManager
  gn = gt.GetNavigatorForTracking()
  world = gn.GetWorldVolume().GetLogicalVolume()
  vmap = {}
  for da in range(world.GetNoDaughters()):
   vl = world.GetDaughter(da)
   vmap[vl.GetName().__str__()] = vl
   print da, vl.GetName()
  lvl = vmap['MagB'].GetLogicalVolume() 
  print lvl.GetMass()/kg,lvl.GetMaterial().GetName()
  print lvl.GetFieldManager()
# FairROOT view
  fgeom = ROOT.gGeoManager
  magB = fgeom.GetVolume('MagB')
  fl = magB.GetField()
  print fl.GetFieldValue()[0],fl.GetFieldValue()[1],fl.GetFieldValue()[2]
