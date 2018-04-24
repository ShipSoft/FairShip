import shipunit as u
from array import array
import hepunit as G4Unit
import ROOT
# requires to have ${SIMPATH}/include/Geant4/ in PYTHONPATH
ROOT.gROOT.ProcessLine('#include "Geant4/G4TransportationManager.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4FieldManager.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4UIterminal.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4RunManager.hh"')
ROOT.gROOT.ProcessLine('#include "TG4GeometryServices.h"')
ROOT.gROOT.ProcessLine('#include "TG4GeometryManager.h"')

def setMagnetField(flag=None):
    print 'setMagnetField() called. Out of date, does not set field for tau neutrino detector!'
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
    gt = ROOT.G4TransportationManager.GetTransportationManager()
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
    modified = False 
    for lvl in setField:
       # check if field already exists
       fm = lvl.GetFieldManager()
       if not fm.DoesFieldExist():
        lvl.SetFieldManager(listOfFields[setField[lvl]],True)
        modified = True  
        if flag=='dump': 
            constField = listOfFields[setField[lvl]].GetDetectorField().GetConstantFieldValue()
            print 'set field for ',setField[lvl], constField
       else:
        if flag=='dump': 
         print 'field already set:',setField[lvl]
    if modified:
     g4Run = G4RunManager.GetRunManager()
     g4Run.GeometryHasBeenModified(True)

def printWF(vl,alreadyPrinted,onlyWithField=True):
    magnetMass = 0
    vname = vl.GetName().data()
    if alreadyPrinted.has_key(vname): return magnetMass
    vln  = vname+' '+str(vl.GetCopyNo())
    mvl  = vl.GetMotherLogical().GetName().data()
    alreadyPrinted[vname]=mvl
    if mvl !='cave': vln = mvl+'/'+vln   
    lvl  = vl.GetLogicalVolume()
    cvol = lvl.GetSolid().GetCubicVolume()/G4Unit.m3
    M    = lvl.GetMass()/G4Unit.kg
    fm = lvl.GetFieldManager()
    if not fm and onlyWithField: return magnetMass
    if M  < 5000.:   print '%-35s volume = %5.2Fm3  mass = %5.2F kg'%(vln,cvol,M)
    else:            print '%-35s volume = %5.2Fm3  mass = %5.2F t'%(vln,cvol,M/1000.)
    if fm:  
       fi = fm.GetDetectorField() 
       if hasattr(fi,'GetConstantFieldValue'):
         print '   Magnetic field:',fi.GetConstantFieldValue()/G4Unit.tesla
       else:
        serv = ROOT.TG4GeometryServices.Instance()
        pos = array('d',[0,0,0])
        bf  = array('d',[0,0,0])
        name = ROOT.G4String(lvl.GetName().__str__())
        serv.GetField(name,pos,bf)
        print '   Magnetic field Bx,By,Bz: %4.2F %4.2F %4.2F'%(bf[0]/G4Unit.tesla,bf[1]/G4Unit.tesla,bf[2]/G4Unit.tesla)
    #if vl.GetName().__str__()[0:3]=='Mag': magnetMass =  M # only count volumes starting with Mag
    name = vl.GetName().__str__()
    if "_" in name and "Mag" in name.split('_')[1]: magnetMass =  M # only count volumes starting with Mag
    return magnetMass
def nextLevel(lv,magnetMass,onlyWithField,exclude,alreadyPrinted):
    tmp = 0
    for da in range(lv.GetNoDaughters()):
     lvn   = lv.GetDaughter(da)
     name  = lvn.GetName().__str__()
     if name in exclude: continue
     lvln  = lvn.GetLogicalVolume()
     if lvln.GetNoDaughters()>0:
        xtmp,dummy = nextLevel(lvln,magnetMass,onlyWithField,exclude,alreadyPrinted)
        magnetMass+=xtmp
     else:
       tmp+=printWF(lvn,alreadyPrinted,onlyWithField)
    return tmp,magnetMass
def printWeightsandFields(onlyWithField = True,exclude=[]):
   if len(exclude)!=0:
      print "will not search in ",exclude  
   gt = ROOT.G4TransportationManager.GetTransportationManager()
   gn = gt.GetNavigatorForTracking()
   world = gn.GetWorldVolume().GetLogicalVolume()
   magnetMass = 0
   alreadyPrinted = {}
   dummy,nM = nextLevel(world,magnetMass,onlyWithField,exclude,alreadyPrinted)
   print 'total magnet mass',nM/1000.,'t'
   return

def addVMCFields(controlFile = 'field/BFieldSetup.txt', verbose = False):
    '''
    Define VMC B fields, e.g. global field, field maps, local or local+global fields
    '''
    print 'Calling addVMCFields using input control file {0}'.format(controlFile)
    
    fieldMaker = ROOT.ShipFieldMaker(controlFile, verbose)

    # Reset the fields in the VMC to use info from the fieldMaker object
    geom = ROOT.TG4GeometryManager.Instance()
    geom.SetUserPostDetConstruction(fieldMaker)
    geom.ConstructSDandField()

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
        print 'Vol is {0}, field is {1}'.format(v.GetName(), field)

        if field:
            # Get the field value assuming the global co-ordinate origin.
            # This needs to be modified to use the local volume centre
            centre = array('d',[0.0, 0.0, 0.0])
            B = array('d',[0.0, 0.0, 0.0])
            field.Field(centre, B)
            print 'Volume {0} has B = ({1}, {2}, {3}) T'.format(v.GetName(), B[0]/u.tesla,
                                                                B[1]/u.tesla, B[2]/u.tesla)

def getRunManager():
 return G4RunManager.GetRunManager()
def startUI():
 session = ROOT.G4UIterminal()
 session.SessionStart()
def debug():
  gt = ROOT.G4TransportationManager.GetTransportationManager()
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
