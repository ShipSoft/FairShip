import yaml
import ROOT,os
import atexit
import shipunit as u

from ShipGeoConfig import ConfigRegistry, AttrDict


mcEngine  = "TGeant4"
simEngine = "Pgun"
nEvents = 5

ROOT.gROOT.LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C")
ROOT.basiclibs()

#-----prepare python exit-----------------------------------------------
def pyExit():
    global run
    del run

atexit.register(pyExit)

Yheight = 10
DecayVolumeMedium = 'helium'
shieldName = 'New_HA_Design'

# Output file name
tag = f'{simEngine}-{mcEngine}'
outFile = f"ship.{tag}.root"
os.system("rm *."+tag+".root")
# Parameter file name
parFile = f"ship.params.{tag}.root"

# In general, the following parts need not be touched
# ========================================================================

# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
timer.Start()
# ------------------------------------------------------------------------

# -----Create simulation run----------------------------------------
run = ROOT.FairRunSim()
run.SetName(mcEngine) # Transport engine
run.SetOutputFile(outFile) # Output file
run.SetUserConfig('g4Config.C')
rtdb = run.GetRuntimeDb()
# ------------------------------------------------------------------------

# -----Create media-------------------------------------------------
run.SetMaterials("media.geo")  # Materials
# ------------------------------------------------------------------------
ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight=Yheight, DecayVolumeMedium=DecayVolumeMedium, shieldName=shieldName)

# -----Create geometry----------------------------------------------
cave= ROOT.ShipCave("CAVE")
cave.SetGeometryFileName("caveWithAir.geo")
run.AddModule(cave)

TargetStation = ROOT.ShipTargetStation("TargetStation", ship_geo.target.length, ship_geo.target.z, ship_geo.targetVersion, ship_geo.target.nS)
if ship_geo.targetVersion > 10:
    TargetStation.SetLayerPosMat(ship_geo.target.xy, ship_geo.target.slices_length, ship_geo.target.slices_gap, ship_geo.target.slices_material)
run.AddModule(TargetStation)

MuonShield = ROOT.ShipMuonShield(in_params=list(ship_geo.muShield.params), z=ship_geo.muShield.z, WithConstShieldField=ship_geo.muShield.WithConstField, SC_key=ship_geo.SC_mag)
run.AddModule(MuonShield)

magnet = ROOT.ShipMagnet("Magnet")
run.AddModule(magnet)

Chamber = ROOT.ShipChamber("Chamber")
run.AddModule(Chamber)

fairship = os.environ["FAIRSHIP"]
with open(f"{fairship}/geometry/veto_config_{ship_geo.DecayVolumeMedium}.yaml") as file:
    config = yaml.safe_load(file)
veto_geo = AttrDict(config)

Veto = ROOT.veto()
Veto.SetVesselDimensions(
        veto_geo.xstartInner,
        veto_geo.xendInner,
        veto_geo.ystartInner,
        veto_geo.yendInner,
        ship_geo.decayVolume.z0,
    )
Veto.SetLiquidVeto(1)
Veto.SetVesselStructure(
        veto_geo.innerSupport,
        veto_geo.sensitiveThickness,
        veto_geo.outerSupport,
        veto_geo.innerSupportMed,
        veto_geo.lidThickness,
        veto_geo.sensitiveMed,
        veto_geo.outerSupportMed,
        veto_geo.decayMed,
        veto_geo.rib,
    )

# Veto = ROOT.veto()
run.AddModule(Veto)

ecal = ROOT.ecal("Ecal", ROOT.kTRUE, ship_geo.ecal.File)
run.AddModule(ecal)

Muon = ROOT.muon("Muon", ROOT.kTRUE)
Muon.SetZStationPositions(
    ship_geo.MuonStation0.z,
    ship_geo.MuonStation1.z,
    ship_geo.MuonStation2.z,
    ship_geo.MuonStation3.z,
)
Muon.SetZFilterPositions(
    ship_geo.MuonFilter0.z, ship_geo.MuonFilter1.z, ship_geo.MuonFilter2.z
)
Muon.SetXMax(ship_geo.Muon.XMax)
Muon.SetYMax(ship_geo.Muon.YMax)
Muon.SetActiveThickness(ship_geo.Muon.ActiveThickness)
Muon.SetFilterThickness(ship_geo.Muon.FilterThickness)
run.AddModule(Muon)

#-----   Magnetic field   -------------------------------------------
    # Constant Field
fMagField = ROOT.ShipConstField()
fMagField.SetField(0., 2. ,0. ) # values are in kG
fMagField.SetFieldRegion(-160, 160,-160, 160, 1940, 125); # values are in cm  (xmin,xmax,ymin,ymax,zmin,zmax)
run.SetField(fMagField)

# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()
pointZero = ship_geo.target.z0
mom = ROOT.TVector3(0., 0., 100.)
pos = ROOT.TVector3(0., 0., pointZero)
myPgun = ROOT.FairParticleGenerator(2212, 1, 0., 0., 100., 0., 0., pointZero)
#myPgun = ROOT.FairBoxGenerator(2212, 1)
#myPgun.SetPRange(10, 10)
#myPgun.SetPhiRange(0, 360)
#myPgun.SetThetaRange(0, 0)
primGen.AddGenerator(myPgun)

run.SetGenerator(primGen)
# ------------------------------------------------------------------------

#---Store the visualiztion info of the tracks, this make the output file very large!!
#--- Use it only to display but not for production!
run.SetStoreTraj(ROOT.kTRUE)

# -----Initialize simulation run------------------------------------
run.Init()
# ------------------------------------------------------------------------

# -----Runtime database---------------------------------------------
kParameterMerged = ROOT.kTRUE
parOut = ROOT.FairParRootFileIo(kParameterMerged)
parOut.open(parFile)
rtdb.setOutput(parOut)
rtdb.saveOutput()
#rtdb.print() does not work in python ??
rtdb.printParamContexts()
# -----Start run----------------------------------------------------
run.Run(nEvents)
run.CreateGeometryFile(f"geofile_full.{tag}.root")
# ------------------------------------------------------------------------

# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print(' ')
print("Macro finished successfully.")
print(f"Output file is {outFile}")
print(f"Parameter file is {parFile}")
print(f"Real time {rtime} s, CPU time {ctime} s")

# ------------------------------------------------------------------------

def someDebug():
    g = ROOT.gROOT
    lm = run.GetListOfModules()
    for x in lm: print(x.GetName())
    fGeo = ROOT.gGeoManager
    cave = fGeo.GetTopVolume()
    cave.Draw('ogl')

    tf = g.FindObjectAny('cbmroot')
    for l in tf.GetListOfFolders(): print(l.GetName())
    l   = tf.FindObject('MCGeoTrack')
    trs = l.FindObject('GeoTracks')
    for x in trs: print(x)
    l = tf.FindObject('Stack')
    trs = l.FindObject('MCTrack')
    for x in trs: print(x)

    gMC = ROOT.gMC # <ROOT.TVirtualMC* object ("TGeant4") at 0x2a5d3e8>
    fStack = gMC.GetStack()
    gMC.ProcessRun(1) # 1 event

    gMC.GetMC() # <ROOT.TGeant4 object ("TGeant4")
    g4.NofVolumes()
    g4.StartGeantUI()

    gPrim = run.GetPrimaryGenerator()
    mch   = gPrim.GetEvent() # <ROOT.FairMCEventHeader object ("MCEventHeader.")
    print(mch.GetEventID(),mch.GetZ())
    gPy8 = gPrim.GetListOfGenerators()[0]
