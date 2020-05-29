from __future__ import print_function
from __future__ import division
import shipunit as u
from array import array
import hepunit as G4Unit
import ROOT
ROOT.gROOT.ProcessLine('#include "Geant4/G4TransportationManager.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4FieldManager.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4UIterminal.hh"')
ROOT.gROOT.ProcessLine('#include "Geant4/G4RunManager.hh"')
ROOT.gROOT.ProcessLine('#include "TG4GeometryServices.h"')
ROOT.gROOT.ProcessLine('#include "TG4GeometryManager.h"')

def check4OrphanVolumes(fGeo):
# fill list with volumes from nodes and compare with list of volumes
 top = fGeo.GetTopVolume()
 listOfVolumes = [top.GetName()]
 findNode(top,listOfVolumes)
 orphan = []
 gIndex = {}
 for v in fGeo.GetListOfVolumes():
   name = v.GetName()
   if not name in listOfVolumes:
     orphan.append(name)
   if not name in gIndex: gIndex[name]=[]
   gIndex[name].append(v.GetNumber())
 print("list of orphan volumes:",orphan)
 vSame = {}
 for x in gIndex:
   if len(gIndex[x])>1: vSame[x]=len(gIndex[x])
 print("list of volumes with same name",vSame)

def setMagnetField(flag=None):
    print('setMagnetField() called. Out of date, does not set field for tau neutrino detector!')
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
        vln  = vl0.GetName().c_str()
        lvl0 = vl0.GetLogicalVolume()
        if vln in listOfFields :  setField[lvl0]=vln
        for dda in range(lvl0.GetNoDaughters()): 
         vl  = lvl0.GetDaughter(dda)
         vln = vl.GetName().c_str()
         lvl = vl.GetLogicalVolume()
         if vln in listOfFields :  setField[lvl]=vln
    modified = False 
    for lvl in setField:
       # check if field already exists
       fm = lvl.GetFieldManager()
       if not fm.DoesFieldExist():
        lvl.SetFieldManager(listOfFields[setField[lvl]],True)
        modified = True  
        if flag=='dump': 
            constField = listOfFields[setField[lvl]].GetDetectorField().GetConstantFieldValue()
            print('set field for ',setField[lvl], constField)
       else:
        if flag=='dump': 
         print('field already set:',setField[lvl])
    if modified:
     g4Run = G4RunManager.GetRunManager()
     g4Run.GeometryHasBeenModified(True)

def printWF(vl,alreadyPrinted,onlyWithField=True):
    magnetMass = 0
    vname = vl.GetName().data()
    if vname in alreadyPrinted: return magnetMass
    vln  = vname+' '+str(vl.GetCopyNo())
    mvl  = vl.GetMotherLogical().GetName().data()
    alreadyPrinted[vname]=mvl
    if mvl !='cave': vln = mvl+'/'+vln   
    lvl  = vl.GetLogicalVolume()
    cvol = lvl.GetSolid().GetCubicVolume()/G4Unit.m3
    M    = lvl.GetMass()/G4Unit.kg
    fm = lvl.GetFieldManager()
    if not fm and onlyWithField: return magnetMass
    if M  < 5000.:   print('%-35s volume = %5.2Fm3  mass = %5.2F kg'%(vln,cvol,M))
    else:            print('%-35s volume = %5.2Fm3  mass = %5.2F t'%(vln,cvol,M/1000.))
    if fm:  
       fi = fm.GetDetectorField() 
       if hasattr(fi,'GetConstantFieldValue'):
         print('   Magnetic field:',fi.GetConstantFieldValue()/G4Unit.tesla)
       else:
        serv = ROOT.TG4GeometryServices.Instance()
        pos = array('d',[0,0,0])
        bf  = array('d',[0,0,0])
        name = ROOT.G4String(lvl.GetName().c_str())
        print ('debug',name,lvl.GetName(),lvl)
        serv.GetField(name,pos,bf)
        print('   Magnetic field Bx,By,Bz: %4.2F %4.2F %4.2F'%(bf[0]/G4Unit.tesla,bf[1]/G4Unit.tesla,bf[2]/G4Unit.tesla))
    #if vl.GetName().c_str()[0:3]=='Mag': magnetMass =  M # only count volumes starting with Mag
    name = vl.GetName().c_str()
    if "_" in name and "Mag" in name.split('_')[1]: magnetMass =  M # only count volumes starting with Mag
    return magnetMass
def nextLevel(lv,magnetMass,onlyWithField,exclude,alreadyPrinted):
    tmp = 0
    for da in range(lv.GetNoDaughters()):
     lvn   = lv.GetDaughter(da)
     name  = lvn.GetName().c_str()
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
      print("will not search in ",exclude)  
   gt = ROOT.G4TransportationManager.GetTransportationManager()
   gn = gt.GetNavigatorForTracking()
   world = gn.GetWorldVolume().GetLogicalVolume()
   magnetMass = 0
   alreadyPrinted = {}
   dummy,nM = nextLevel(world,magnetMass,onlyWithField,exclude,alreadyPrinted)
   print('total magnet mass',nM/1000.,'t')
   return

def addVMCFields(shipGeo, controlFile = '', verbose = False, withVirtualMC = True):
    '''
    Define VMC B fields, e.g. global field, field maps, local or local+global fields
    '''
    print('Calling addVMCFields')
    
    fieldMaker = ROOT.ShipFieldMaker(verbose)

    # Read the input control file. If this is empty then the only fields that are 
    # defined (so far) are those within the C++ geometry classes
    if controlFile != '':
      fieldMaker.readInputFile(controlFile)

    # Set the main spectrometer field map as a global field
    if hasattr(shipGeo, 'Bfield'):
      fieldMaker.defineFieldMap('MainSpecMap', 'files/MainSpectrometerField.root',
                                ROOT.TVector3(0.0, 0.0, shipGeo.Bfield.z))      
      withConstFieldNuTauDet = False
      if hasattr(shipGeo.EmuMagnet,'WithConstField'): withConstFieldNuTauDet = shipGeo.EmuMagnet.WithConstField
      if not withConstFieldNuTauDet:
       fieldMaker.defineFieldMap('NuMap','files/nuTauDetField.root', ROOT.TVector3(0.0,0.0,shipGeo.EmuMagnet.zC))       
      withConstFieldHadronAbs = True
      if hasattr(shipGeo.hadronAbsorber,'WithConstField'): withConstFieldHadronAbs = shipGeo.hadronAbsorber.WithConstField
      if not withConstFieldHadronAbs:
       fieldMaker.defineFieldMap('HadronAbsorberMap','files/FieldHadronStopper_raised_20190411.root', ROOT.TVector3(0.0,0.0,shipGeo.hadronAbsorber.z))       
    # Combine the fields to obtain the global field
      if not withConstFieldNuTauDet or not withConstFieldHadronAbs:
       if not withConstFieldNuTauDet and withConstFieldHadronAbs: fieldMaker.defineComposite('TotalField', 'MainSpecMap', 'NuMap')
       if withConstFieldNuTauDet and not withConstFieldHadronAbs: fieldMaker.defineComposite('TotalField', 'MainSpecMap', 'HadronAbsorberMap')
       if not withConstFieldNuTauDet and not withConstFieldHadronAbs: fieldMaker.defineComposite('TotalField', 'MainSpecMap', 'HadronAbsorberMap','NuMap')
       fieldMaker.defineGlobalField('TotalField')
      else:
       fieldMaker.defineGlobalField('MainSpecMap')
    if withVirtualMC:
    # Force the VMC to update/reset the fields defined by the fieldMaker object.
    # Get the ROOT/Geant4 geometry manager
     geom = ROOT.TG4GeometryManager.Instance()
    # Let the geometry know about the fieldMaker object
     geom.SetUserPostDetConstruction(fieldMaker)
    # Update the fields via the overriden ShipFieldMaker::Contruct() function
     geom.ConstructSDandField()

    # Return the fieldMaker object, otherwise it will "go out of scope" and its
    # content will be deleted
    return fieldMaker


def printVMCFields():
    '''
    Method to print out information about VMC fields
    '''
    print('Printing VMC fields and associated volumes')

    fGeo = ROOT.gGeoManager  
    vols = fGeo.GetListOfVolumes()

    for v in vols:

        field =  v.GetField()
        if field:
         print('Vol is {0}, field is {1}'.format(v.GetName(), field))
        else: 
         print('Vol is {0}'.format(v.GetName()))

        if field:
            # Get the field value assuming the global co-ordinate origin.
            # This needs to be modified to use the local volume centre
            centre = array('d',[0.0, 0.0, 0.0])
            B = array('d',[0.0, 0.0, 0.0])
            field.Field(centre, B)
            print('Volume {0} has B = ({1}, {2}, {3}) T'.format(v.GetName(), B[0]/u.tesla,
                                                                B[1]/u.tesla, B[2]/u.tesla))

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
   vmap[vl.GetName().c_str()] = vl
   print(da, vl.GetName())
  lvl = vmap['MagB'].GetLogicalVolume() 
  print(lvl.GetMass()/G4Unit.kg,lvl.GetMaterial().GetName())
  print(lvl.GetFieldManager())
#
  for da in range(world.GetNoDaughters()):
   vl = world.GetDaughter(da)
   vln = vl.GetName().c_str()
   lvl = vl.GetLogicalVolume()
   fm = lvl.GetFieldManager() 
   if fm : 
    v = fm.GetDetectorField().GetConstantFieldValue()
    print(vln,fm,v.getX(),v.getY())
# FairROOT view
  fgeom = ROOT.gGeoManager
  magB = fgeom.GetVolume('MagB')
  fl = magB.GetField()
  print(fl.GetFieldValue()[0],fl.GetFieldValue()[1],fl.GetFieldValue()[2])
