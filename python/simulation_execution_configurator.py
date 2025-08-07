#!/usr/bin/env python
"""Simulation execution and post-processing configurator for SHiP simulation.

This module handles the execution of the simulation, stack configuration,
field setup, trajectory filtering, and post-processing of results.
"""

import os
import sys
from array import array


class SimulationExecutionConfigurator:
    """Main class for configuring simulation execution and post-processing."""

    def __init__(
        self, ROOT, units, config_manager, geom_configurator, utility_configurator
    ):
        """Initialize the simulation execution configurator.

        Args:
            ROOT: ROOT module
            units: shipunit module
            config_manager: Configuration manager instance
            geom_configurator: Geometry configurator instance
            utility_configurator: Utility configurator instance

        """
        self.ROOT = ROOT
        self.u = units
        self.config_manager = config_manager
        self.geom_configurator = geom_configurator
        self.utility_configurator = utility_configurator

    def configure_trajectory_storage(self, run, options):
        """Configure trajectory storage for event display.

        Args:
            run: Simulation run instance
            options: Command line options

        """
        if options.eventDisplay:
            run.SetStoreTraj(self.ROOT.kTRUE)
        else:
            run.SetStoreTraj(self.ROOT.kFALSE)

    def initialize_simulation_run(self, run, options):
        """Initialize the simulation run and return MC objects.

        Args:
            run: Simulation run instance
            options: Command line options

        Returns:
            Tuple of (gMC, fStack) objects

        """
        run.Init()

        if options.dryrun:  # Early stop after setting up
            sys.exit(0)

        gMC = self.ROOT.TVirtualMC.GetMC()
        fStack = gMC.GetStack()

        return gMC, fStack

    def configure_stack_parameters(self, fStack, options, config_values):
        """Configure stack parameters for track storage.

        Args:
            fStack: VMC stack instance
            options: Command line options
            config_values: Configuration values dictionary

        """
        EnergyCut = 10.0 * self.u.MeV if options.mudis else 100.0 * self.u.MeV

        MCTracksWithHitsOnly = config_values.get("MCTracksWithHitsOnly", False)
        MCTracksWithEnergyCutOnly = config_values.get(
            "MCTracksWithEnergyCutOnly", False
        )
        MCTracksWithHitsOrEnergyCut = config_values.get(
            "MCTracksWithHitsOrEnergyCut", False
        )

        if MCTracksWithHitsOnly:
            fStack.SetMinPoints(1)
            fStack.SetEnergyCut(-100.0 * self.u.MeV)
        elif MCTracksWithEnergyCutOnly:
            fStack.SetMinPoints(-1)
            fStack.SetEnergyCut(EnergyCut)
        elif MCTracksWithHitsOrEnergyCut:
            fStack.SetMinPoints(1)
            fStack.SetEnergyCut(EnergyCut)
        elif options.deepCopy:
            fStack.SetMinPoints(0)
            fStack.SetEnergyCut(0.0 * self.u.MeV)

    def configure_trajectory_filter(self, options, ship_geo):
        """Configure trajectory filter for event display.

        Args:
            options: Command line options
            ship_geo: Geometry configuration

        """
        if not options.eventDisplay:
            return

        trajFilter = self.ROOT.FairTrajFilter.Instance()
        trajFilter.SetStepSizeCut(1 * self.u.mm)
        trajFilter.SetVertexCut(
            -20 * self.u.m,
            -20 * self.u.m,
            ship_geo.target.z0 - 1 * self.u.m,
            20 * self.u.m,
            20 * self.u.m,
            200.0 * self.u.m,
        )
        trajFilter.SetMomentumCutP(0.1 * self.u.GeV)
        trajFilter.SetEnergyCut(0.0, 400.0 * self.u.GeV)
        trajFilter.SetStorePrimaries(self.ROOT.kTRUE)
        trajFilter.SetStoreSecondaries(self.ROOT.kTRUE)

    def configure_magnetic_fields(self, ship_geo, options):
        """Configure magnetic field settings.

        Args:
            ship_geo: Geometry configuration
            options: Command line options

        Returns:
            fieldMaker instance if created, None otherwise

        """
        fieldMaker = None

        if hasattr(ship_geo.Bfield, "fieldMap"):
            if options.field_map:
                ship_geo.Bfield.fieldMap = options.field_map
            fieldMaker = self.geom_configurator.add_vmc_fields(ship_geo, verbose=True)

        return fieldMaker

    def print_debug_info(self, options):
        """Print debug information for fields and geometry.

        Args:
            options: Command line options

        """
        if options.debug == 1:
            self.geom_configurator.print_vmc_fields()
            self.geom_configurator.print_weights_and_fields(
                only_with_field=True,
                exclude=[
                    "DecayVolume",
                    "Tr1",
                    "Tr2",
                    "Tr3",
                    "Tr4",
                    "Veto",
                    "Ecal",
                    "Hcal",
                    "MuonDetector",
                    "SplitCal",
                ],
            )

    def run_simulation(self, run, options):
        """Execute the main simulation run.

        Args:
            run: Simulation run instance
            options: Command line options

        """
        run.Run(options.nEvents)

    def save_runtime_database(self, rtdb, parFile):
        """Save runtime database parameters.

        Args:
            rtdb: Runtime database instance
            parFile: Parameter file path

        """
        kParameterMerged = self.ROOT.kTRUE
        parOut = self.ROOT.FairParRootFileIo(kParameterMerged)
        parOut.open(parFile)
        rtdb.setOutput(parOut)
        rtdb.saveOutput()
        rtdb.printParamContexts()
        getattr(rtdb, "print")()

    def save_geometry_file(self, run, runtime_config, ship_geo):
        """Save geometry file and parameters.

        Args:
            run: Simulation run instance
            runtime_config: Runtime configuration
            ship_geo: Geometry configuration

        """
        run.CreateGeometryFile(runtime_config.geometry_file)
        self.utility_configurator.save_basic_parameters(
            runtime_config.geometry_file, ship_geo
        )

    def check_geometry_overlaps(self, options):
        """Check for geometry overlaps if debug mode is enabled.

        Args:
            options: Command line options

        """
        if options.debug != 2:
            return

        # Workaround for ROOT issue
        self.ROOT.gROOT.SetWebDisplay("off")

        fGeo = self.ROOT.gGeoManager
        fGeo.SetNmeshPoints(10000)
        fGeo.CheckOverlaps(0.1)  # 1 micron takes 5 minutes
        fGeo.PrintOverlaps()

        # Check subsystems in more detail
        for x in fGeo.GetTopNode().GetNodes():
            x.CheckOverlaps(0.0001)
            fGeo.PrintOverlaps()

    def print_simulation_results(
        self, timer, outFile, parFile, generators, options, HNL
    ):
        """Print simulation results and timing information.

        Args:
            timer: Timer instance
            outFile: Output file path
            parFile: Parameter file path
            generators: Dictionary of generator instances
            options: Command line options
            HNL: HNL flag

        """
        timer.Stop()
        rtime = timer.RealTime()
        ctime = timer.CpuTime()

        print(" ")
        print("Macro finished successfully.")

        # Print generator-specific statistics
        P8gen = generators.get("pythia8", None)
        if P8gen:
            if HNL:
                print("number of retries, events without HNL ", P8gen.nrOfRetries())
            elif options.DarkPhoton:
                print(
                    "number of retries, events without Dark Photons ",
                    P8gen.nrOfRetries(),
                )
                print(
                    "total number of dark photons (including multiple meson decays per single collision) ",
                    P8gen.nrOfDP(),
                )

        print("Output file is ", outFile)
        print("Parameter file is ", parFile)
        print("Real time ", rtime, " s, CPU time ", ctime, "s")

    def print_comprehensive_summary(self, USING_LAZY_LOADING, import_manager):
        """Print comprehensive simulation summary.

        Args:
            USING_LAZY_LOADING: Flag indicating if lazy loading was used
            import_manager: Import manager instance

        """
        print("\n" + "=" * 60)
        print("SIMULATION SUMMARY")
        print("=" * 60)
        print(self.config_manager.get_summary())
        print()

        if USING_LAZY_LOADING and import_manager:
            print("Lazy Loading Summary:")
            print(import_manager.get_import_summary())
            print()
        else:
            print("Used direct imports (lazy loading not available)")
            print()

    def post_process_muon_background(self, options, outFile):
        """Post-process muon background simulation to remove empty events.

        Args:
            options: Command line options
            outFile: Output file path

        """
        if not options.muonback:
            return

        tmpFile = outFile + "tmp"
        xxx = outFile.split("/")
        check = xxx[len(xxx) - 1]

        # Find the file in ROOT's list
        fin = None
        for ff in self.ROOT.gROOT.GetListOfFiles():
            nm = ff.GetName().split("/")
            if nm[len(nm) - 1] == check:
                fin = ff
                break

        if not fin:
            fin = self.ROOT.TFile.Open(outFile)

        t = fin["cbmsim"]
        fout = self.ROOT.TFile(tmpFile, "recreate")
        fSink = self.ROOT.FairRootFileSink(fout)

        sTree = t.CloneTree(0)
        nEvents = 0
        pointContainers = []

        # Identify point containers using naming convention
        for x in sTree.GetListOfBranches():
            name = x.GetName()
            if "Point" in name:
                pointContainers.append("sTree." + name + ".GetEntries()")

        # Filter out empty events
        for n in range(t.GetEntries()):
            rc = t.GetEvent(n)
            empty = True
            for x in pointContainers:
                if eval(x) > 0:
                    empty = False
                    break
            if not empty:
                rc = sTree.Fill()  # noqa: F841 - Return code not checked, could add error handling
                nEvents += 1

        # Create branch list
        branches = self.ROOT.TList()
        branches.SetName("BranchList")
        branch_names = [
            "MCTrack",
            "vetoPoint",
            "ShipRpcPoint",
            "TargetPoint",
            "TTPoint",
            "ScoringPoint",
            "strawtubesPoint",
            "EcalPoint",
            "sEcalPointLite",
            "smuonPoint",
            "TimeDetPoint",
            "MCEventHeader",
            "UpstreamTaggerPoint",
            "MTCdetPoint",
            "sGeoTracks",
        ]
        for name in branch_names:
            branches.Add(self.ROOT.TObjString(name))

        sTree.AutoSave()
        fSink.WriteObject(branches, "BranchList", self.ROOT.TObject.kSingleKey)
        fSink.SetOutTree(sTree)

        fout.Close()
        print("removed empty events, left with:", nEvents)

        # Replace original file
        os.system("rm " + outFile)
        os.system("mv " + tmpFile + " " + outFile)
        fin.SetWritable(False)  # bypass flush error

    def post_process_mudis(self, options, outFile, inputFile):
        """Post-process muon DIS simulation to add cross-section information.

        Args:
            options: Command line options
            outFile: Output file path
            inputFile: Input file path

        """
        if not options.mudis:
            return

        temp_filename = outFile.replace(".root", "_tmp.root")

        with (
            self.ROOT.TFile.Open(outFile, "read") as f_outputfile,
            self.ROOT.TFile.Open(inputFile, "read") as f_muonfile,
            self.ROOT.TFile.Open(temp_filename, "recreate") as f_temp,  # noqa: F841
        ):
            output_tree = f_outputfile["cbmsim"]
            muondis_tree = f_muonfile["DIS"]
            new_tree = output_tree.CloneTree(0)

            cross_section = array("f", [0.0])
            cross_section_leaf = new_tree.Branch(  # noqa: F841 - Branch accessed via tree
                "CrossSection", cross_section, "CrossSection/F"
            )

            for output_event, muondis_event in zip(output_tree, muondis_tree):
                mu = muondis_event.InMuon[0]
                cross_section[0] = mu[10]
                new_tree.Fill()

            new_tree.Write("", self.ROOT.TObject.kOverwrite)

        os.replace(temp_filename, outFile)
        print("Successfully added DISCrossSection to the output file:", outFile)

    def execute_full_simulation(
        self,
        run,
        rtdb,
        options,
        config_values,
        ship_geo,
        runtime_config,
        timer,
        outFile,
        parFile,
        inputFile,
        generators,
        HNL,
        USING_LAZY_LOADING,
        import_manager,
    ):
        """Execute the complete simulation workflow.

        Args:
            run: Simulation run instance
            rtdb: Runtime database instance
            options: Command line options
            config_values: Configuration values dictionary
            ship_geo: Geometry configuration
            runtime_config: Runtime configuration
            timer: Timer instance
            outFile: Output file path
            parFile: Parameter file path
            inputFile: Input file path
            generators: Dictionary of generator instances
            HNL: HNL flag
            USING_LAZY_LOADING: Lazy loading flag
            import_manager: Import manager instance

        """
        # Configure trajectory storage
        self.configure_trajectory_storage(run, options)

        # Initialize simulation run
        gMC, fStack = self.initialize_simulation_run(run, options)

        # Configure stack parameters
        self.configure_stack_parameters(fStack, options, config_values)

        # Configure trajectory filter
        self.configure_trajectory_filter(options, ship_geo)

        # Configure magnetic fields
        fieldMaker = self.configure_magnetic_fields(ship_geo, options)

        # Print debug information
        self.print_debug_info(options)

        # Run simulation
        self.run_simulation(run, options)

        # Save runtime database
        self.save_runtime_database(rtdb, parFile)

        # Save geometry file
        self.save_geometry_file(run, runtime_config, ship_geo)

        # Check geometry overlaps
        self.check_geometry_overlaps(options)

        # Print results
        self.print_simulation_results(timer, outFile, parFile, generators, options, HNL)
        self.print_comprehensive_summary(USING_LAZY_LOADING, import_manager)

        # Post-processing
        self.post_process_muon_background(options, outFile)
        self.post_process_mudis(options, outFile, inputFile)

        return gMC, fStack, fieldMaker


class SimulationExecutionConfiguratorFactory:
    """Factory for creating simulation execution configurator instances."""

    @staticmethod
    def create_simulation_execution_configurator(
        ROOT, units, config_manager, geom_configurator, utility_configurator
    ):
        """Create a simulation execution configurator instance.

        Args:
            ROOT: ROOT module
            units: shipunit module
            config_manager: Configuration manager instance
            geom_configurator: Geometry configurator instance
            utility_configurator: Utility configurator instance

        Returns:
            SimulationExecutionConfigurator instance

        """
        return SimulationExecutionConfigurator(
            ROOT, units, config_manager, geom_configurator, utility_configurator
        )
