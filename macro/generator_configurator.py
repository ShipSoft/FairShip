#!/usr/bin/env python
"""
Generator configuration module for SHiP simulation.

This module handles the configuration of all primary generators used in the simulation,
including Pythia8, Pythia6, EvtCalc, particle guns, background generators, and cosmic generators.
"""

import os
import sys

class GeneratorConfigurator:
    """Main class for configuring primary generators"""
    
    def __init__(self, ROOT, units, utils, ship_geo, pythia_configurator, cosmics_configurator):
        """
        Initialize the generator configurator.
        
        Args:
            ROOT: ROOT module
            units: shipunit module  
            utils: rootUtils module
            ship_geo: Geometry configuration
            pythia_configurator: Pythia configurator instance
            cosmics_configurator: Cosmics configurator instance
        """
        self.ROOT = ROOT
        self.u = units
        self.ut = utils
        self.ship_geo = ship_geo
        self.pythia_configurator = pythia_configurator
        self.cosmics_configurator = cosmics_configurator

    def create_primary_generator(self):
        """Create and return a FairPrimaryGenerator instance"""
        return self.ROOT.FairPrimaryGenerator()

    def configure_pythia8_generators(self, primGen, options, config_values):
        """
        Configure Pythia8-based generators (HNL, RPVSUSY, DarkPhoton, charm-only).
        
        Args:
            primGen: Primary generator instance
            options: Command line options
            config_values: Dictionary with configuration values
        
        Returns:
            Configured P8gen generator or None if not applicable
        """
        if not options.pythia8:
            return None
            
        primGen.SetTarget(self.ship_geo.target.z0, 0.)
        
        HNL = config_values.get('HNL', False)
        inputFile = config_values.get('inputFile', None)
        inclusive = config_values.get('inclusive', 'c')
        charmonly = config_values.get('charmonly', False)
        motherMode = config_values.get('motherMode', 'pi0')
        
        theProductionCouplings = config_values.get('theProductionCouplings', None)
        theDecayCouplings = config_values.get('theDecayCouplings', None)
        theCouplings = config_values.get('theCouplings', [0.447e-9,7.15e-9,1.88e-9])
        theHNLMass = config_values.get('theHNLMass', 1.0)
        
        P8gen = None
        
        # HNL or RPVSUSY generators
        if HNL or options.RPVSUSY:
            P8gen = self.ROOT.HNLPythia8Generator()
            
            if HNL:
                print('Generating HNL events of mass %.3f GeV'%options.theMass)
                if theProductionCouplings is None and theDecayCouplings is None:
                    print('and with couplings=',theCouplings)
                    theProductionCouplings = theDecayCouplings = theCouplings
                elif theProductionCouplings is not None and theDecayCouplings is not None:
                    print('and with couplings',theProductionCouplings,'at production')
                    print('and',theDecayCouplings,'at decay')
                else:
                    raise ValueError('Either both production and decay couplings must be specified, or neither.')
                self.pythia_configurator.configure_hnl(
                    P8gen, options.theMass, theProductionCouplings, 
                    theDecayCouplings, inclusive, options.deepCopy
                )
                
            if options.RPVSUSY:
                print('Generating RPVSUSY events of mass %.3f GeV'%theHNLMass)
                print('and with couplings=[%.3f,%.3f]'%(theCouplings[0],theCouplings[1]))
                print('and with stop mass=%.3f GeV\n'%theCouplings[2])
                self.pythia_configurator.configure_rpvsusy(
                    P8gen, options.theMass, [theCouplings[0], theCouplings[1]],
                    theCouplings[2], options.RPVSUSYbench, inclusive, options.deepCopy
                )
                
            P8gen.SetParameters("ProcessLevel:all = off")
            if inputFile:
                self.ut.checkFileExists(inputFile)
                P8gen.UseExternalFile(inputFile, options.firstEvent)
        
        # Dark Photon generator
        elif options.DarkPhoton:
            P8gen = self.ROOT.DPPythia8Generator()
            if inclusive == 'qcd':
                P8gen.SetDPId(4900023)
            else:
                P8gen.SetDPId(9900015)
            passDPconf = self.pythia_configurator.configure_dark_photon(
                P8gen, options.theMass, options.theDPepsilon, inclusive, motherMode, options.deepCopy
            )
            if passDPconf != 1:
                sys.exit()
        
        # Configure common parameters for Pythia8 generators
        if P8gen and (HNL or options.RPVSUSY or options.DarkPhoton):
            P8gen.SetSmearBeam(1*self.u.cm)  # finite beam size
            P8gen.SetLmin((self.ship_geo.Chamber1.z - self.ship_geo.chambers.Tub1length) - self.ship_geo.target.z0)
            P8gen.SetLmax(self.ship_geo.TrackStation1.z - self.ship_geo.target.z0)
        
        # Charm-only generator
        if charmonly:
            primGen.SetTarget(0., 0.)  # vertex is set in pythia8Generator
            self.ut.checkFileExists(inputFile)
            if self.ship_geo.Box.gausbeam:
                primGen.SetBeam(0., 0., 0.5, 0.5)  # more central beam, for hits in downstream detectors
                primGen.SmearGausVertexXY(True)  # sigma = x
            else:
                primGen.SetBeam(0., 0., self.ship_geo.Box.TX-1., self.ship_geo.Box.TY-1.)  # Uniform distribution
                primGen.SmearVertexXY(True)
            P8gen = self.ROOT.Pythia8Generator()
            P8gen.UseExternalFile(inputFile, options.firstEvent)
            P8gen.SetTarget("volTarget_1", 0., 0.)  # will distribute PV inside target, beam offset x=y=0.
        
        if P8gen:
            primGen.AddGenerator(P8gen)
            
        return P8gen

    def configure_pythia6_generator(self, primGen, options):
        """
        Configure Pythia6 generator.
        
        Args:
            primGen: Primary generator instance
            options: Command line options
        """
        if not options.pythia6:
            return None
            
        # set muon interaction close to decay volume
        primGen.SetTarget(self.ship_geo.target.z0 + self.ship_geo.muShield.length, 0.)
        
        # Force loading of Pythia6 library
        test = self.ROOT.TPythia6()  # don't know any other way of forcing to load lib
        P6gen = self.ROOT.tPythia6Generator()
        P6gen.SetMom(50.*self.u.GeV)
        P6gen.SetTarget("gamma/mu+", "n0")  # default "gamma/mu-","p+"
        primGen.AddGenerator(P6gen)
        
        return P6gen

    def configure_fixed_target_generator(self, primGen, options):
        """
        Configure fixed target generator.
        
        Args:
            primGen: Primary generator instance
            options: Command line options
        """
        if not options.fixedTarget:
            return None
            
        P8gen = self.ROOT.FixedTargetGenerator()
        P8gen.SetZoffset(options.z_offset*self.u.mm)
        P8gen.SetTarget("cave_1/target_vacuum_box_1/TargetArea_1/HeVolume_1", 0., 0.)
        P8gen.SetMom(400.*self.u.GeV)
        P8gen.SetEnergyCut(0.)
        P8gen.SetHeartBeat(100000)
        P8gen.SetG4only()
        primGen.AddGenerator(P8gen)
        
        return P8gen

    def configure_evtcalc_generator(self, primGen, options, inputFile):
        """
        Configure EvtCalc generator.
        
        Args:
            primGen: Primary generator instance
            options: Command line options
            inputFile: Input file path
        """
        if not options.evtcalc:
            return None
            
        primGen.SetTarget(0.0, 0.0)
        print(f"Opening input file for EvtCalc generator: {inputFile}")
        self.ut.checkFileExists(inputFile)
        EvtCalcGen = self.ROOT.EvtCalcGenerator()
        EvtCalcGen.Init(inputFile, options.firstEvent)
        EvtCalcGen.SetPositions(zTa=self.ship_geo.target.z, zDV=self.ship_geo.decayVolume.z)
        primGen.AddGenerator(EvtCalcGen)
        options.nEvents = min(options.nEvents, EvtCalcGen.GetNevents())
        print(f"Generate {options.nEvents} with EvtCalc input. First event: {options.firstEvent}")
        
        return EvtCalcGen

    def configure_particle_gun(self, primGen, options):
        """
        Configure particle gun generator.
        
        Args:
            primGen: Primary generator instance
            options: Command line options
        """
        if options.command != "PG":
            return None
            
        myPgun = self.ROOT.FairBoxGenerator(options.pID, 1)
        myPgun.SetPRange(options.Estart, options.Eend)
        myPgun.SetPhiRange(0, 360)  # Azimuth angle range [degree]
        myPgun.SetThetaRange(0, 0)  # Polar angle in lab system range [degree]
        
        if options.multiplePG:
            # multiple PG sources in the x-y plane; z is always the same!
            myPgun.SetBoxXYZ(
                (options.Vx - options.Dx/2)*self.u.cm,
                (options.Vy - options.Dy/2)*self.u.cm,
                (options.Vx + options.Dx/2)*self.u.cm,
                (options.Vy + options.Dy/2)*self.u.cm,
                options.Vz*self.u.cm
            )
        else:
            # point source
            myPgun.SetXYZ(options.Vx*self.u.cm, options.Vy*self.u.cm, options.Vz*self.u.cm)
            
        primGen.AddGenerator(myPgun)
        return myPgun

    def configure_mudis_generator(self, primGen, options, inputFile):
        """
        Configure muon DIS background generator.
        
        Args:
            primGen: Primary generator instance
            options: Command line options
            inputFile: Input file path
        """
        if not options.mudis:
            return None
            
        self.ut.checkFileExists(inputFile)
        primGen.SetTarget(0., 0.)
        DISgen = self.ROOT.MuDISGenerator()
        
        # in front of UVT up to tracking station 1
        mu_start, mu_end = (self.ship_geo.Chamber1.z - self.ship_geo.chambers.Tub1length - 10.*self.u.cm,
                           self.ship_geo.TrackStation1.z)
        print('MuDIS position info input=', mu_start, mu_end)
        DISgen.SetPositions(mu_start, mu_end)
        DISgen.Init(inputFile, options.firstEvent)
        primGen.AddGenerator(DISgen)
        options.nEvents = min(options.nEvents, DISgen.GetNevents())
        print('Generate ', options.nEvents, ' with DIS input', ' first event', options.firstEvent)
        
        return DISgen

    def configure_neutrino_generators(self, primGen, run, options, inputFile):
        """
        Configure neutrino background generators (Genie and NuRadio).
        
        Args:
            primGen: Primary generator instance
            run: Simulation run instance
            options: Command line options
            inputFile: Input file path
        """
        generators = {}
        
        # Genie neutrino generator
        if options.genie:
            self.ut.checkFileExists(inputFile)
            primGen.SetTarget(0., 0.)  # do not interfere with GenieGenerator
            Geniegen = self.ROOT.GenieGenerator()
            Geniegen.Init(inputFile, options.firstEvent)
            Geniegen.SetPositions(
                self.ship_geo.target.z0,
                self.ship_geo.tauMudet.zMudetC - 5*self.u.m,
                self.ship_geo.TrackStation2.z
            )
            primGen.AddGenerator(Geniegen)
            options.nEvents = min(options.nEvents, Geniegen.GetNevents())
            run.SetPythiaDecayer("DecayConfigNuAge.C")
            print('Generate ', options.nEvents, ' with Genie input', ' first event', options.firstEvent)
            generators['genie'] = Geniegen
        
        # NuRadio generator
        if options.nuradio:
            self.ut.checkFileExists(inputFile)
            primGen.SetTarget(0., 0.)  # do not interfere with GenieGenerator
            Geniegen = self.ROOT.GenieGenerator()
            Geniegen.Init(inputFile, options.firstEvent)
            Geniegen.SetPositions(
                self.ship_geo.target.z0,
                self.ship_geo.tauMudet.zMudetC,
                self.ship_geo.MuonStation3.z
            )
            Geniegen.NuOnly()
            primGen.AddGenerator(Geniegen)
            print('Generate ', options.nEvents, ' for nuRadiography', ' first event', options.firstEvent)
            
            # add tungsten to PDG
            pdg = self.ROOT.TDatabasePDG.Instance()
            pdg.AddParticle('W', 'Ion', 1.71350e+02, True, 0., 74, 'XXX', 1000741840)
            
            run.SetPythiaDecayer('DecayConfigPy8.C')
            generators['nuradio'] = Geniegen
            
        return generators

    def configure_ntuple_generator(self, primGen, options, inputFile):
        """
        Configure ntuple generator for reading previously processed muon events.
        
        Args:
            primGen: Primary generator instance
            options: Command line options
            inputFile: Input file path
        """
        if not options.ntuple:
            return None
            
        self.ut.checkFileExists(inputFile)
        primGen.SetTarget(self.ship_geo.target.z0 + 50*self.u.m, 0.)
        Ntuplegen = self.ROOT.NtupleGenerator()
        Ntuplegen.Init(inputFile, options.firstEvent)
        primGen.AddGenerator(Ntuplegen)
        options.nEvents = min(options.nEvents, Ntuplegen.GetNevents())
        print('Process ', options.nEvents, ' from input file')
        
        return Ntuplegen

    def configure_muon_background_generator(self, primGen, options, inputFile, config_values, modules):
        """
        Configure muon background generator.
        
        Args:
            primGen: Primary generator instance
            options: Command line options
            inputFile: Input file path
            config_values: Configuration values dictionary
            modules: Detector modules dictionary
        """
        if not options.muonback:
            return None
            
        fileType = self.ut.checkFileExists(inputFile)
        if fileType == 'tree':
            # 2018 background production
            primGen.SetTarget(self.ship_geo.target.z0 + 70.845*self.u.m, 0.)
        else:
            primGen.SetTarget(self.ship_geo.target.z0 + 50*self.u.m, 0.)
        
        MuonBackgen = self.ROOT.MuonBackGenerator()
        MuonBackgen.Init(inputFile, options.firstEvent)
        MuonBackgen.SetPaintRadius(options.PaintBeam)
        MuonBackgen.SetSmearBeam(options.SmearBeam)
        MuonBackgen.SetPhiRandom(options.phiRandom)
        
        DownScaleDiMuon = config_values.get('DownScaleDiMuon', False)
        if DownScaleDiMuon:
            testf = self.ROOT.TFile.Open(inputFile)
            if not testf.FileHeader.GetTitle().find('diMu100.0') < 0:
                MuonBackgen.SetDownScaleDiMuon()  # avoid interference with boosted channels
                print("MuonBackgenerator: set downscale for dimuon on")
            testf.Close()
            
        if options.sameSeed:
            MuonBackgen.SetSameSeed(options.sameSeed)
            
        primGen.AddGenerator(MuonBackgen)
        options.nEvents = min(options.nEvents, MuonBackgen.GetNevents())
        
        # otherwise, output file becomes too big
        config_values['MCTracksWithHitsOnly'] = True
        
        print('Process ', options.nEvents, ' from input file, with 𝜎 = ', options.PaintBeam,
              ', with smear radius r = ', options.SmearBeam * self.u.cm,
              'with MCTracksWithHitsOnly', config_values['MCTracksWithHitsOnly'])
              
        if options.followMuon:
            options.fastMuon = True
            modules['Veto'].SetFollowMuon()
        if options.fastMuon:
            modules['Veto'].SetFastMuon()
            
        return MuonBackgen

    def configure_cosmics_generator(self, primGen, options, Opt_high):
        """
        Configure cosmic ray generator.
        
        Args:
            primGen: Primary generator instance
            options: Command line options
            Opt_high: Cosmic generator option
        """
        if not options.cosmics:
            return None
            
        primGen.SetTarget(0., 0.)
        Cosmicsgen = self.ROOT.CosmicsGenerator()
        self.cosmics_configurator.configure(Cosmicsgen, self.ship_geo)
        if not Cosmicsgen.Init(Opt_high):
            print("initialization of cosmic background generator failed ", Opt_high)
            sys.exit(0)
        Cosmicsgen.n_EVENTS = options.nEvents
        primGen.AddGenerator(Cosmicsgen)
        print('Process ', options.nEvents, ' Cosmic events with option ', Opt_high)
        
        return Cosmicsgen

    def configure_all_generators(self, run, options, config_values, modules):
        """
        Configure all generators based on options and return the primary generator.
        
        Args:
            run: Simulation run instance
            options: Command line options
            config_values: Configuration values dictionary
            modules: Detector modules dictionary
            
        Returns:
            Configured primary generator and generator instances dictionary
        """
        primGen = self.create_primary_generator()
        generators = {}
        
        inputFile = config_values.get('inputFile', None)
        Opt_high = config_values.get('Opt_high', None)
        
        # Configure different generator types
        p8gen = self.configure_pythia8_generators(primGen, options, config_values)
        if p8gen:
            generators['pythia8'] = p8gen
            
        p6gen = self.configure_pythia6_generator(primGen, options)
        if p6gen:
            generators['pythia6'] = p6gen
            
        ftgen = self.configure_fixed_target_generator(primGen, options)
        if ftgen:
            generators['fixed_target'] = ftgen
            
        evtgen = self.configure_evtcalc_generator(primGen, options, inputFile)
        if evtgen:
            generators['evtcalc'] = evtgen
            
        pgun = self.configure_particle_gun(primGen, options)
        if pgun:
            generators['particle_gun'] = pgun
            
        disgen = self.configure_mudis_generator(primGen, options, inputFile)
        if disgen:
            generators['mudis'] = disgen
            
        nu_generators = self.configure_neutrino_generators(primGen, run, options, inputFile)
        generators.update(nu_generators)
        
        ntgen = self.configure_ntuple_generator(primGen, options, inputFile)
        if ntgen:
            generators['ntuple'] = ntgen
            
        mbgen = self.configure_muon_background_generator(primGen, options, inputFile, config_values, modules)
        if mbgen:
            generators['muon_background'] = mbgen
            
        cosgen = self.configure_cosmics_generator(primGen, options, Opt_high)
        if cosgen:
            generators['cosmics'] = cosgen
        
        run.SetGenerator(primGen)
        
        return primGen, generators


class GeneratorConfiguratorFactory:
    """Factory for creating generator configurator instances"""
    
    @staticmethod
    def create_generator_configurator(ROOT, units, utils, ship_geo, pythia_configurator, cosmics_configurator):
        """
        Create a generator configurator instance.
        
        Args:
            ROOT: ROOT module
            units: shipunit module  
            utils: rootUtils module
            ship_geo: Geometry configuration
            pythia_configurator: Pythia configurator instance
            cosmics_configurator: Cosmics configurator instance
            
        Returns:
            GeneratorConfigurator instance
        """
        return GeneratorConfigurator(ROOT, units, utils, ship_geo, pythia_configurator, cosmics_configurator)