import shipunit as u
# import geant4 submodules
# requires to have ${SIMPATH}/lib/Geant4/ in PYTHONPATH
from G4global import *
from G4run import *
from G4geometry import *
from G4digits_hits import *
from G4track import *
import hepunit as G4Unit
import ROOT
from array import array
gTransportationManager = G4TransportationManager.GetTransportationManager()

def addVMCFields(controlFile = 'field/BFieldSetup.txt'):
    '''
    Define VMC B fields, e.g. global field, field maps, local or local+global fields
    '''
    print 'Calling addVMCFields using input control file {0}'.format(controlFile)
    
    fieldMaker = ROOT.ShipFieldMaker()
    fieldMaker.makeFields(controlFile)

    # Return the fieldMaker object, otherwise it will "go out of scope" and its
    # content will be deleted
    return fieldMaker


def printVMCFields():
    '''
    Method to print out information about VMC fields
    '''
    print 'Printing VMC fields and associated volumes'

    fGeo = ROOT.gGeoManager  
    vols = fGeo.GetListOfVolumes()

    for v in vols:

        field =  v.GetField()
        #print 'Vol is {0}, field is {1}'.format(v.GetName(), field)

        if field:
            # Get the field value in the local volume centre
            centre = array('d',[0.0, 0.0, 0.0])
            B = array('d',[0.0, 0.0, 0.0])
            field.Field(centre, B)
            print 'Volume {0} has B = ({1}, {2}, {3}) T'.format(v.GetName(), B[0]/u.tesla,
                                                                B[1]/u.tesla, B[2]/u.tesla)


def setMagnetField(flag=None):
    print 'setMagnetField() called'
    fGeo = ROOT.gGeoManager  
    vols = fGeo.GetListOfVolumes()
    #copy field by hand to geant4
    listOfFields={}
    for v in vols:
     field =  v.GetField()
     if not field: continue
     bx = field.GetFieldValue()[0]/u.tesla*G4Unit.tesla
     by = field.GetFieldValue()[1]/u.tesla*G4Unit.tesla
     bz = field.GetFieldValue()[2]/u.tesla*G4Unit.tesla
     magFieldIron = G4UniformMagField(G4ThreeVector(bx,by,bz))
     FieldIronMgr = G4FieldManager(magFieldIron)
     FieldIronMgr.CreateChordFinder(magFieldIron)
     listOfFields[v.GetName()]=FieldIronMgr  
    gt = gTransportationManager
    gn = gt.GetNavigatorForTracking()
    world = gn.GetWorldVolume().GetLogicalVolume()
    setField = {}
    for da in range(world.GetNoDaughters()):
        vl0  = world.GetDaughter(da)
        vln  = vl0.GetName().__str__()
        lvl0 = vl0.GetLogicalVolume()
        if listOfFields.has_key(vln) :  setField[lvl0]=vln
        for dda in range(lvl0.GetNoDaughters()): 
         vl  = lvl0.GetDaughter(dda)
         vln = vl.GetName().__str__()
         lvl = vl.GetLogicalVolume()
         if listOfFields.has_key(vln) :  setField[lvl]=vln
    for lvl in setField:
       lvl.SetFieldManager(listOfFields[setField[lvl]],True)  
       if flag=='dump': 
            constField = listOfFields[setField[lvl]].GetDetectorField().GetConstantFieldValue()
            print 'set field for ',setField[lvl], constField
    g4Run = G4RunManager.GetRunManager()
    g4Run.GeometryHasBeenModified(True)

def printWF(vl):
    vln  = vl.GetName().__str__()+' '+str(vl.GetCopyNo())
    mvl  = vl.GetMotherLogical().GetName()
    if mvl !='cave': vln = mvl+'/'+vln   
    lvl  = vl.GetLogicalVolume()
    cvol = lvl.GetSolid().GetCubicVolume()/G4Unit.m3
    M    = lvl.GetMass()/G4Unit.kg
    if M  < 5000.:   print '%-35s volume = %5.2Fm3  mass = %5.2F kg'%(vln,cvol,M)
    else:            print '%-35s volume = %5.2Fm3  mass = %5.2F t'%(vln,cvol,M/1000.)
    fm = lvl.GetFieldManager() 
    if fm:  
       fi = fm.GetDetectorField()
       print '   Magnetic field:',fi.GetConstantFieldValue()/G4Unit.tesla
    magnetMass = 0
    #if vl.GetName().__str__()[0:3]=='Mag': magnetMass =  M # only count volumes starting with Mag
    name = vl.GetName().__str__()
    if "_" in name and "Mag" in name.split('_')[1]: magnetMass =  M # only count volumes starting with Mag
    return magnetMass 
def printWeightsandFields():
   gt = gTransportationManager
   gn = gt.GetNavigatorForTracking()
   world = gn.GetWorldVolume().GetLogicalVolume()
   magnetMass = 0
   for da0 in range(world.GetNoDaughters()):   
     vl0   = world.GetDaughter(da0)
     lvl0  = vl0.GetLogicalVolume()
     if lvl0.GetNoDaughters()==0: magnetMass+=printWF(vl0) 
     for da in range(lvl0.GetNoDaughters()):        
       vl1   = lvl0.GetDaughter(da)
       lvl1  = vl1.GetLogicalVolume()
       if lvl1.GetNoDaughters()==0: magnetMass+=printWF(vl1) 
       for da in range(lvl1.GetNoDaughters()):        
         vl2   = lvl1.GetDaughter(da)
         magnetMass+=printWF(vl2)
   print 'total magnet mass',magnetMass/1000.,'t'
   return
def getRunManager():
 return G4RunManager.GetRunManager()
def startUI():
 import G4interface
 G4interface.StartUISession() 
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
  print lvl.GetMass()/G4Unit.kg,lvl.GetMaterial().GetName()
  print lvl.GetFieldManager()
#
  for da in range(world.GetNoDaughters()):
   vl = world.GetDaughter(da)
   vln = vl.GetName().__str__()
   lvl = vl.GetLogicalVolume()
   fm = lvl.GetFieldManager() 
   if fm : 
    v = fm.GetDetectorField().GetConstantFieldValue()
    print vln,fm,v.getX(),v.getY()
# FairROOT view
  fgeom = ROOT.gGeoManager
  magB = fgeom.GetVolume('MagB')
  fl = magB.GetField()
  print fl.GetFieldValue()[0],fl.GetFieldValue()[1],fl.GetFieldValue()[2]
