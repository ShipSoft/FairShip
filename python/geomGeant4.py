import shipunit as u
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

def setMagnetField(flag=None):
    print 'setMagnetField() called'
    fGeo = ROOT.gGeoManager
    vols = fGeo.GetListOfVolumes()
    #copy field by hand to geant4
    listOfFields={}
    for v in vols:
     field =  v.GetField()
     print 'Volume is {0}'.format(v.GetName())
     if not field: continue
     bx = field.GetFieldValue()[0]/u.tesla*G4Unit.tesla
     by = field.GetFieldValue()[1]/u.tesla*G4Unit.tesla
     bz = field.GetFieldValue()[2]/u.tesla*G4Unit.tesla
     print 'Volume {0} has B field: {1}, {2}, {3}'.format(v.GetName(), bx, by, bz)
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
        if listOfFields.has_key(vln) :
            print 'Setting field A for {0}'.format(vln)
            setField[lvl0]=vln
        else:
            print 'No field A for {0}'.format(vln)
        for dda in range(lvl0.GetNoDaughters()):
         vl  = lvl0.GetDaughter(dda)
         vln = vl.GetName().__str__()
         lvl = vl.GetLogicalVolume()
         if listOfFields.has_key(vln) :
             print 'Setting field B for {0}'.format(vln)
             setField[lvl]=vln
         else:
             print 'No field B for {0}'.format(vln)

         for ddda in range(lvl.GetNoDaughters()):
             vlC  = lvl.GetDaughter(ddda)
             vlnC = vlC.GetName().__str__()
             lvlC = vlC.GetLogicalVolume()
             if listOfFields.has_key(vlnC) :
                 print 'Setting field C for {0}'.format(vlnC)
                 setField[lvlC]=vlnC
             else:
                 print 'No field C for {0}'.format(vlnC)

    #print '***********************************************************'
    #print 'listOfFields dictionary {0}'.format(listOfFields)
    #print '***********************************************************'
    #print 'setField dictionary {0}'.format(setField)

    for lvl in setField:
       print 'In setField loop, lvl = {0}'.format(lvl.GetName())
       lvl.SetFieldManager(listOfFields[setField[lvl]],True)
       if flag=='dump':
            constField = listOfFields[setField[lvl]].GetDetectorField().GetConstantFieldValue()
            print 'set field for ',setField[lvl], constField
    g4Run = G4RunManager.GetRunManager()
    g4Run.GeometryHasBeenModified(True)


def addVMCFields(controlFile = 'field/BFieldSetup.txt', verbose = False):
    '''
    Define VMC B fields, e.g. global field, field maps, local or local+global fields
    '''
    print 'Calling addVMCFields using input control file {0}'.format(controlFile)
    
    fieldMaker = ROOT.ShipFieldMaker(verbose)
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

def printWF(vl):

    vln  = vl.GetName().__str__()+' '+str(vl.GetCopyNo())
    mvl  = vl.GetMotherLogical().GetName()
    if mvl !='cave': vln = mvl+'/'+vln   
    lvl  = vl.GetLogicalVolume()
    cvol = lvl.GetSolid().GetCubicVolume()/G4Unit.m3
    M    = lvl.GetMass()/G4Unit.kg
    if M  < 5000.:   print '%-35s volume = %5.2Fm3  mass = %5.2F kg'%(vln,cvol,M)
    else:            print '%-35s volume = %5.2Fm3  mass = %5.2F t'%(vln,cvol,M/1000.)

    name = vl.GetName().__str__()

    # Get the B field via the VMC interface using the given G4 volume name
    fGeo = ROOT.gGeoManager
    vol = fGeo.GetVolume(name)
    fl = vol.GetField()
    if fl:
      centre = array('d',[0.0, 0.0, 0.0])
      B = array('d',[0.0, 0.0, 0.0])
      fl.Field(centre, B)
      print 'Volume {0} has magnetic field: ({1}, {2}, {3}) T'.format(name, B[0]/u.tesla,
                                                                      B[1]/u.tesla, B[2]/u.tesla)

    magnetMass = 0
    # only count volumes starting with Mag
    if "_" in name and "Mag" in name.split('_')[1]: magnetMass =  M

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

