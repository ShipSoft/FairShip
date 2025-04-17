#!/usr/bin/env python
import os
import sys
import ROOT

import shipunit as u
import shipRoot_conf
import rootUtils as ut
from ShipGeoConfig import ConfigRegistry
from argparse import ArgumentParser
from array import array


mcEngine     = "TGeant4"

MCTracksWithHitsOnly   = False  # copy particles which produced a hit and their history
MCTracksWithEnergyCutOnly = True # copy particles above a certain kin energy cut
MCTracksWithHitsOrEnergyCut = False # or of above, factor 2 file size increase compared to MCTracksWithEnergyCutOnly

globalDesigns = {
     '2023' : {
          'dy' : 6.,
          'dv' : 6,
          'nud' : 4,
          'caloDesign' : 3,
          'strawDesign' : 10
     }
}
default = '2023'



parser = ArgumentParser()
group = parser.add_mutually_exclusive_group()

parser.add_argument("-E",        dest="simEngine",       help="Possible options: EvtCalc,Pythia6, Pythia8, PG, Genie, nuRadiography, Ntuple, MuonBack, Nuage, muonDIS, Cosmics", required=True, default='Pythia8')
parser.add_argument("-n", "--nEvents",dest="nEvents",  help="Number of events to generate", required=False,  default=100, type=int)
parser.add_argument("-i", "--firstEvent",dest="firstEvent",  help="First event of input file to use", required=False,  default=0, type=int)
parser.add_argument("-F",        dest="deepCopy",  help="default = False: copy only stable particles to stack, except for HNL events", required=False, action="store_true")
parser.add_argument("-s", "--seed",dest="theSeed",  help="Seed for random number. Only for experts, see TRrandom::SetSeed documentation", required=False,  default=0, type=int)
parser.add_argument("-f",        dest="yaml_file",       help="Yaml configuration file for simEngine parameters", required=True, default="shipgen/shipgen_parameters.yaml")
parser.add_argument("-g",        dest="geofile",       help="geofile for muon shield geometry, for experts only", required=False, default=None)
parser.add_argument("-o", "--output",dest="outputDir",  help="Output directory", required=False,  default=".")
parser.add_argument("-Y",        dest="dy",  help="max height of vacuum tank", required=False, default=globalDesigns[default]['dy'])
parser.add_argument("--tankDesign", dest="dv",      help="4=TP elliptical tank design, 5 = optimized conical rectangular design, 6=5 without segment-1"\
                                            ,required=False, default=globalDesigns[default]['dv'], type=int)
parser.add_argument("--nuTauTargetDesign", dest="nud"\
  ,help="3: emulsion spectrometer and muon filter as in CDS, 4: not magnetized target and muon spectrometer for ECN3", default=globalDesigns[default]['nud'], type=int, choices=[3,4])
parser.add_argument("--caloDesign",
                    help="0=ECAL/HCAL TP 2=splitCal  3=ECAL/ passive HCAL",
                    default=globalDesigns[default]['caloDesign'],
                    type=int,
                    choices=[0,2,3])
parser.add_argument("--strawDesign", dest="strawDesign", help="simplistic tracker design,  4=sophisticated straw tube design, horizontal wires (default), 10=2cm straw"
                                            ,required=False, default=globalDesigns[default]['strawDesign'], type=int)
parser.add_argument("-F",        dest="deepCopy",  help="default = False: copy only stable particles to stack, except for HNL events", required=False, action="store_true")
parser.add_argument("--dry-run", dest="dryrun",  help="stop after initialize", required=False,action="store_true")
parser.add_argument("-D", "--display", dest="eventDisplay", help="store trajectories", required=False, action="store_true")
parser.add_argument("--shieldName", help="The name of the SC shield in the database. SC default: sc_v6, Warm default: warm_opt", default="sc_v6", choices=["sc_v6", "warm_opt"])
parser.add_argument("--debug",  help="1: print weights and field 2: make overlap check", required=False, default=0, type=int, choices=range(0,3))
parser.add_argument("--field_map", default=None, help="Specify spectrometer field map.")
parser.add_argument(
    "--helium",
    dest="decayVolMed",
    help="Set Decay Volume medium to helium. NOOP, as default is helium",
    action="store_const",
    const="helium",
    default="helium"
)
parser.add_argument(
    "--vacuums",
    dest="decayVolMed",
    help="Set Decay Volume medium to vacuum(vessel structure changes)",
    action="store_const",
    const="vacuums",
    default="helium"
)

parser.add_argument("--SND", dest="SND", help="Activate SND.", action='store_true')
parser.add_argument("--noSND", dest="SND", help="Deactivate SND. NOOP, as it currently defaults to off.", action='store_false')

options = parser.parse_args()


with open(options.yaml_file) as file:
  config = yaml.safe_load(file)



ROOT.gRandom.SetSeed(options.theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure(0)     # load basic libraries, prepare atexit for python
# - targetOpt      = 5  # 0=solid   >0 sliced, 5: 5 pieces of tungsten, 4 H20 slits, 17: Mo + W +H2O (default)
#   nuTauTargetDesign = 3 #3 = 2018 design, 4 = not magnetized target + spectrometer
ship_geo = ConfigRegistry.loadpy(
     "$FAIRSHIP/geometry/geometry_config.py",
     Yheight=options.dy,
     tankDesign=options.dv,
     nuTauTargetDesign=options.nud,
     CaloDesign=options.caloDesign,
     strawDesign=options.strawDesign,
     muShieldGeo=options.geofile,
     shieldName=options.shieldName,
     DecayVolumeMedium=options.decayVolMed,
     SND=options.SND,
)


# Output file name, add dy to be able to setup geometry with ambiguities.
if options.simEngine == "PG": tag = options.simEngine + "_"+str(config['ParticleGun']['pID'])+"-"+mcEngine
else: tag = options.simEngine+"-"+mcEngine
if config['Pythia8']['charmonly'] == True: tag = options.simEngine+"CharmOnly-"+mcEngine
if options.eventDisplay: tag = tag+'_D'
if options.dv > 4 : tag = 'conical.'+tag
if not os.path.exists(options.outputDir):
  os.makedirs(options.outputDir)
outFile = f"{options.outputDir}/ship.{tag}.root"

# rm older files !!!
for x in os.listdir(options.outputDir):
  if not x.find(tag)<0: os.system(f"rm {options.outputDir}/{x}" )
# Parameter file name
parFile=f"{options.outputDir}/ship.params.{tag}.root"




# In general, the following parts need not be touched
# ========================================================================

# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
timer.Start()
# ------------------------------------------------------------------------
# -----Create simulation run----------------------------------------
run = ROOT.FairRunSim()
run.SetName(mcEngine)  # Transport engine
run.SetSink(ROOT.FairRootFileSink(outFile))  # Output file
run.SetUserConfig("g4Config.C") # user configuration file default g4Config.C
rtdb = run.GetRuntimeDb()
# -----Create geometry----------------------------------------------
# import shipMuShield_only as shipDet_conf # special use case for an attempt to convert active shielding geometry for use with FLUKA
# import shipTarget_only as shipDet_conf
import shipDet_conf
modules = shipDet_conf.configure(run,ship_geo)
# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()

SetPrimGen(primGen,options,ship_geo,modules)
if options.simEngine == "nuRadiography":
  #  add tungsten to PDG
  pdg = ROOT.TDatabasePDG.Instance()
  pdg.AddParticle('W','Ion', 1.71350e+02, True, 0., 74, 'XXX', 1000741840)
  #
  run.SetPythiaDecayer('DecayConfigPy8.C')
 # this requires writing a C macro, would have been easier to do directly in python!


if options.simEngine == "Nuage":
  run.SetPythiaDecayer("DecayConfigNuAge.C")

if options.simEngine == "MuonBack":
  MCTracksWithHitsOnly = True # otherwise, output file becomes too big



#
run.SetGenerator(primGen)
# ------------------------------------------------------------------------

#---Store the visualiztion info of the tracks, this make the output file very large!!
#--- Use it only to display but not for production!
if options.eventDisplay: run.SetStoreTraj(ROOT.kTRUE)
else:            run.SetStoreTraj(ROOT.kFALSE)
# -----Initialize simulation run------------------------------------
run.Init()
if options.dryrun: # Early stop after setting up Pythia 8
 sys.exit(0)
gMC = ROOT.TVirtualMC.GetMC()
fStack = gMC.GetStack()
EnergyCut = 10. * u.MeV if options.mudis else 100. * u.MeV

if MCTracksWithHitsOnly:
 fStack.SetMinPoints(1)
 fStack.SetEnergyCut(-100.*u.MeV)
elif MCTracksWithEnergyCutOnly:
 fStack.SetMinPoints(-1)
 fStack.SetEnergyCut(EnergyCut)
elif MCTracksWithHitsOrEnergyCut:
 fStack.SetMinPoints(1)
 fStack.SetEnergyCut(EnergyCut)
elif options.deepCopy:
 fStack.SetMinPoints(0)
 fStack.SetEnergyCut(0.*u.MeV)

if options.eventDisplay:
 # Set cuts for storing the trajectories, can only be done after initialization of run (?!)
  trajFilter = ROOT.FairTrajFilter.Instance()
  trajFilter.SetStepSizeCut(1*u.mm)
  trajFilter.SetVertexCut(-20*u.m, -20*u.m,ship_geo.target.z0-1*u.m, 20*u.m, 20*u.m, 200.*u.m)
  trajFilter.SetMomentumCutP(0.1*u.GeV)
  trajFilter.SetEnergyCut(0., 400.*u.GeV)
  trajFilter.SetStorePrimaries(ROOT.kTRUE)
  trajFilter.SetStoreSecondaries(ROOT.kTRUE)

# The VMC sets the fields using the "/mcDet/setIsLocalMagField true" option in "gconfig/g4config.in"
import geomGeant4
# geomGeant4.setMagnetField() # replaced by VMC, only has effect if /mcDet/setIsLocalMagField  false

# Define extra VMC B fields not already set by the geometry definitions, e.g. a global field,
# any field maps, or defining if any volumes feel only the local or local+global field.
# For now, just keep the fields already defined by the C++ code, i.e comment out the fieldMaker
if hasattr(ship_geo.Bfield,"fieldMap"):
     if options.field_map:
          ship_geo.Bfield.fieldMap = options.field_map
     fieldMaker = geomGeant4.addVMCFields(ship_geo, verbose=True)

# Print VMC fields and associated geometry objects
if options.debug == 1:
 geomGeant4.printVMCFields()
 geomGeant4.printWeightsandFields(onlyWithField = True,\
             exclude=['DecayVolume','Tr1','Tr2','Tr3','Tr4','Veto','Ecal','Hcal','MuonDetector','SplitCal'])
# Plot the field example
#fieldMaker.plotField(1, ROOT.TVector3(-9000.0, 6000.0, 50.0), ROOT.TVector3(-300.0, 300.0, 6.0), 'Bzx.png')
#fieldMaker.plotField(2, ROOT.TVector3(-9000.0, 6000.0, 50.0), ROOT.TVector3(-400.0, 400.0, 6.0), 'Bzy.png')

# -----Start run----------------------------------------------------
run.Run(options.nEvents)
# -----Runtime database---------------------------------------------
kParameterMerged = ROOT.kTRUE
parOut = ROOT.FairParRootFileIo(kParameterMerged)
parOut.open(parFile)
rtdb.setOutput(parOut)
rtdb.saveOutput()
rtdb.printParamContexts()
getattr(rtdb,"print")()
# ------------------------------------------------------------------------
run.CreateGeometryFile(f"{options.outputDir}/geofile_full.{tag}.root")
# save ShipGeo dictionary in geofile
import saveBasicParameters
saveBasicParameters.execute(f"{options.outputDir}/geofile_full.{tag}.root",ship_geo)

# checking for overlaps
if options.debug == 2:
 fGeo = ROOT.gGeoManager
 fGeo.SetNmeshPoints(10000)
 fGeo.CheckOverlaps(0.1)  # 1 micron takes 5minutes
 fGeo.PrintOverlaps()
 # check subsystems in more detail
 for x in fGeo.GetTopNode().GetNodes():
   x.CheckOverlaps(0.0001)
   fGeo.PrintOverlaps()
# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print(' ')
print("Macro finished successfully.")
if "P8gen" in globals() :
    if (HNL): print("number of retries, events without HNL ",P8gen.nrOfRetries())
    elif (options.DarkPhoton):
        print("number of retries, events without Dark Photons ",P8gen.nrOfRetries())
        print("total number of dark photons (including multiple meson decays per single collision) ",P8gen.nrOfDP())

print("Output file is ",  outFile)
print("Parameter file is ",parFile)
print("Real time ",rtime, " s, CPU time ",ctime,"s")

# remove empty events
if options.simEngine == "MuonBack":
 tmpFile = outFile+"tmp"
 xxx = outFile.split('/')
 check = xxx[len(xxx)-1]
 fin = False
 for ff in ROOT.gROOT.GetListOfFiles():
    nm = ff.GetName().split('/')
    if nm[len(nm)-1] == check: fin = ff
 if not fin: fin   = ROOT.TFile.Open(outFile)
 t = fin.Get("cbmsim")
 fout  = ROOT.TFile(tmpFile,'recreate')
 fSink = ROOT.FairRootFileSink(fout)

 sTree = t.CloneTree(0)
 nEvents = 0
 pointContainers = []
 for x in sTree.GetListOfBranches():
   name = x.GetName()
   if not name.find('Point')<0: pointContainers.append('sTree.'+name+'.GetEntries()') # makes use of convention that all sensitive detectors fill XXXPoint containers
 for n in range(t.GetEntries()):
     rc = t.GetEvent(n)
     empty = True
     for x in pointContainers:
        if eval(x)>0: empty = False
     if not empty:
        rc = sTree.Fill()
        nEvents+=1

 branches = ROOT.TList()
 branches.SetName('BranchList')
 branches.Add(ROOT.TObjString('MCTrack'))
 branches.Add(ROOT.TObjString('vetoPoint'))
 branches.Add(ROOT.TObjString('ShipRpcPoint'))
 branches.Add(ROOT.TObjString('TargetPoint'))
 branches.Add(ROOT.TObjString('TTPoint'))
 branches.Add(ROOT.TObjString('ScoringPoint'))
 branches.Add(ROOT.TObjString('strawtubesPoint'))
 branches.Add(ROOT.TObjString('EcalPoint'))
 branches.Add(ROOT.TObjString('sEcalPointLite'))
 branches.Add(ROOT.TObjString('smuonPoint'))
 branches.Add(ROOT.TObjString('TimeDetPoint'))
 branches.Add(ROOT.TObjString('MCEventHeader'))
 branches.Add(ROOT.TObjString('UpstreamTaggerPoint'))
 branches.Add(ROOT.TObjString('sGeoTracks'))

 sTree.AutoSave()
 fSink.WriteObject(branches, "BranchList", ROOT.TObject.kSingleKey)
 fSink.SetOutTree(sTree)

 fout.Close()
 print("removed empty events, left with:", nEvents)
 rc1 = os.system("rm  "+outFile)
 rc2 = os.system("mv "+tmpFile+" "+outFile)
 fin.SetWritable(False) # bpyass flush error

if options.simEngine == "muonDIS":

    temp_filename = outFile.replace(".root", "_tmp.root")

    with (
        ROOT.TFile.Open(outFile, "read") as f_outputfile,
        ROOT.TFile.Open(inputFile, "read") as f_muonfile,
        ROOT.TFile.Open(temp_filename, "recreate") as f_temp,
    ):
        output_tree = f_outputfile.Get("cbmsim")

        muondis_tree = f_muonfile.Get("DIS")

        new_tree = output_tree.CloneTree(0)

        cross_section = array("f", [0.0])
        cross_section_leaf = new_tree.Branch(
            "CrossSection", cross_section, "CrossSection/F"
        )

        for output_event, muondis_event in zip(output_tree, muondis_tree):
            mu = muondis_event.InMuon[0]
            cross_section[0] = mu[10]
            new_tree.Fill()

        new_tree.Write("", ROOT.TObject.kOverwrite)

    os.replace(temp_filename, outFile)
    print("Successfully added DISCrossSection to the output file:", outFile)

# ------------------------------------------------------------------------
import checkMagFields
def visualizeMagFields():
 checkMagFields.run()
def checkOverlapsWithGeant4():
 # after /run/initialize, but prints warning messages, problems with TGeo volume
 mygMC = ROOT.TGeant4.GetMC()
 mygMC.ProcessGeantCommand("/geometry/test/recursion_start 0")
 mygMC.ProcessGeantCommand("/geometry/test/recursion_depth 2")
 mygMC.ProcessGeantCommand("/geometry/test/run")
