from __future__ import print_function
import ROOT
ROOT.gROOT.LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C")
ROOT.basiclibs()
ROOT.gSystem.Load("libBase.so")
ROOT.gSystem.Load("libGen.so")

def run_sim(nEvents = 10, mcEngine = "TGeant4"):
# Output file name
  outFile ="ship.test.root"
# Parameter file name
  parFile="ship.params.root"

  # In general, the following parts need not be touched
  # ========================================================================


  # -----   Timer   --------------------------------------------------------
  timer = ROOT.TStopwatch()
  timer.Start()
  # ------------------------------------------------------------------------

  # -----   Create simulation run   ----------------------------------------
  run = ROOT.FairRunSim()
  run.SetName(mcEngine)            # Transport engine
  run.SetOutputFile(outFile)       # Output file
  rtdb = run.GetRuntimeDb()
  # ------------------------------------------------------------------------

  # -----   Create media   -------------------------------------------------
  run.SetMaterials("media.geo")        # Materials
  # ------------------------------------------------------------------------

  # -----   Create geometry   ----------------------------------------------

  cave= ROOT.ShipCave("CAVE")
  cave.SetGeometryFileName("cave.geo")
  run.AddModule(cave)

  TargetStation = ROOT.ShipTargetStation("TargetStation",7000)
  run.AddModule(TargetStation)
  MuonShield = ROOT.ShipMuonShield("MuonShield",1)
  run.AddModule(MuonShield)

  magnet = ROOT.ShipMagnet("Magnet")
  run.AddModule(magnet)


  Chamber = ROOT.ShipChamber("Chamber")
  run.AddModule(Chamber)

  Veto = ROOT.veto("Veto", ROOT.kTRUE)
  run.AddModule(Veto)


  ecal = ROOT.ecal("Ecal", ROOT.kTRUE)
  run.AddModule(ecal)


  Muon = ROOT.muon("Muon", ROOT.kTRUE)
  run.AddModule(Muon)

#-----   Magnetic field   -------------------------------------------
    # Constant Field
  fMagField = ROOT.ShipConstField()
  fMagField.SetField(0., 2. ,0. ) # values are in kG
  fMagField.SetFieldRegion(-160, 160,-160, 160, 1940, 125); # values are in cm  (xmin,xmax,ymin,ymax,zmin,zmax)
  run.SetField(fMagField)

  # -----   Create PrimaryGenerator   --------------------------------------
  primGen = ROOT.FairPrimaryGenerator()

    # Pythia8
  P8gen = ROOT.Pythia8Generator()
  P8gen.UseRandom3() # TRandom1 or TRandom3 ?
  P8gen.SetParameters("SoftQCD:inelastic = on")
  P8gen.SetParameters("PhotonCollision:gmgm2mumu = on")
  P8gen.SetParameters("PromptPhoton:all = on")
  P8gen.SetParameters("WeakBosonExchange:all = on")
  P8gen.SetMom(400)  # p momentum
  primGen.AddGenerator(P8gen)

  run.SetGenerator(primGen)
  # ------------------------------------------------------------------------

  #---Store the visualiztion info of the tracks, this make the output file very large!!
  #--- Use it only to display but not for production!
  run.SetStoreTraj(ROOT.kTRUE)



  # -----   Initialize simulation run   ------------------------------------
  run.Init()
  # ------------------------------------------------------------------------

  # -----   Runtime database   ---------------------------------------------

  kParameterMerged = ROOT.kTRUE
  parOut = ROOT.FairParRootFileIo(kParameterMerged)
  parOut.open(parFile)
  rtdb.setOutput(parOut)
  rtdb.saveOutput()
  #rtdb.print()
  # ------------------------------------------------------------------------

  # -----   Start run   ----------------------------------------------------
  run.Run(nEvents)
  run.CreateGeometryFile("geofile_full.root")
  # ------------------------------------------------------------------------

  # -----   Finish   -------------------------------------------------------
  timer.Stop()
  rtime = timer.RealTime()
  ctime = timer.CpuTime()
  print(' ')
  print("Macro finished succesfully.")
  print("Output file is ",  outFile)
  print("Parameter file is ",parFile)
  print("Real time ",rtime, " s, CPU time ",ctime,"s")
  f = run.GetOutputFile()
  f.Write()
  del run
  # ------------------------------------------------------------------------

if __name__ == '__main__' : run_sim()
