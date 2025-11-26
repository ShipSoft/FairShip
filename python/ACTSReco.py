import sys
import os
import global_variables

import acts
import acts.examples
import ROOT

from acts.examples.simulation import (
    EtaConfig,
    PhiConfig,
    MomentumConfig,
    ParticleConfig,
    addDigitization,
    ParticleSelectorConfig,
    addDigiParticleSelection,
)

from acts.examples.reconstruction import (
    addSeeding,
    SeedFinderConfigArg,
    SeedFinderOptionsArg,
    SeedingAlgorithm,
    addKalmanTracks,
    addVertexFitting,
    VertexFinder,
    addTrackWriters,
    TrackSmearingSigmas,
)

currentPath = os.path.dirname(__file__)
sourcePath = os.path.abspath(os.path.join(currentPath,".."))
fgeo = ROOT.TFile.Open(global_variables.geoFile)

from ShipGeoConfig import load_from_root_file
ShipGeo = load_from_root_file(fgeo, 'ShipGeo')

def runTracking():
    customLogLevel=acts.examples.defaultLogging(logLevel=acts.logging.VERBOSE)
    u = acts.UnitConstants

    if global_variables.detector == "SiliconTarget":
       field = acts.ConstantBField(acts.Vector3(0.0, 0.0, 0.0 * u.T))
       simHitTree="siHits"
       digiConfigFile = currentPath + "/SiliconTarget-digi-config.json"
       detector = acts.examples.SiTargetBuilder(fileName=str(global_variables.geoFile),
                                                surfaceLogLevel=customLogLevel(),
                                                layerLogLevel=customLogLevel(),
                                                volumeLogLevel=customLogLevel(),
                                               )

    if global_variables.detector == "MTC":
        #MTC setup to be updated.
       field = acts.ConstantBField(acts.Vector3(0.0, -1.2, 0.0 * u.T))
       simHitTree="mtcHits"
       digiConfigFile = currentPath + "/MTC-digi-config.json"
       detector = acts.examples.MTCBuilder(fileName=str(global_variables.geoFile),
                                                surfaceLogLevel=customLogLevel(),
                                                layerLogLevel=customLogLevel(),
                                                volumeLogLevel=customLogLevel(),
                                               )

    if global_variables.detector == "StrawTracker":
       #Bfield x/y non-zero, offsets manually set to zero.
       field = acts.examples.MagneticFieldMapXyz(file=str(sourcePath+"/"+ShipGeo.Bfield.fieldMap),
                                                 tree="Data", lengthUnit=u.cm, BFieldUnit = u.T,
                                                 translateToGlobal=acts.Vector3(0, 0,
                                                                                ShipGeo.Bfield.z),
                                                 rotateAxis = True, firstOctant = False)
       simHitTree="strawHits"
       digiConfigFile = currentPath + "/StrawTracker-digi-config.json"
       detector = acts.examples.StrawtubeBuilder(fileName=str(global_variables.geoFile),
                                                    surfaceLogLevel=customLogLevel(),
                                                    layerLogLevel=customLogLevel(),
                                                    volumeLogLevel=customLogLevel(),
                                                   )

    trackingGeometry = detector.trackingGeometry()

    s = acts.examples.Sequencer(events=global_variables.nEvents, numThreads=-1, trackFpes=False)
    s.config.logLevel = acts.logging.INFO
    rnd = acts.examples.RandomNumbers(seed=42)

    s.addReader(
        acts.examples.RootParticleReader(
            level=acts.logging.INFO,
            filePath=str(global_variables.inputFile),
            outputParticles="particles_generated",
            treeName="particles"
        )
    )

    s.addWhiteboardAlias("particles", "particles_generated")
    s.addWhiteboardAlias("particles_simulated_selected", "particles_generated")

    s.addReader(
                acts.examples.RootSimHitReader(
                    level=acts.logging.INFO,
                    filePath=str(global_variables.inputFile),
                    outputSimHits="simhits",
                    treeName=simHitTree
                )
            )

    addDigitization(
        s,
        trackingGeometry,
        field,
        digiConfigFile=str(digiConfigFile),
        rnd=rnd,
        logLevel=acts.logging.INFO,
    )

    addDigiParticleSelection(
        s,
        ParticleSelectorConfig(
            pt=(global_variables.minPt * u.GeV, None),
            measurements=(global_variables.minHits, None),
            removeNeutral=True,
            removeSecondaries=True,
        ),
    )

    if not global_variables.realPR:
        addSeeding(
                s,
                trackingGeometry,
                field,
                rnd=rnd,
                inputParticles="particles_generated",
                seedingAlgorithm=SeedingAlgorithm.TruthSmeared,
                particleHypothesis=acts.ParticleHypothesis.muon,
                trackSmearingSigmas=TrackSmearingSigmas(
                    loc0=0,
                    loc0PtA=0,
                    loc0PtB=0,
                    loc1=0,
                    loc1PtA=0,
                    loc1PtB=0,
                    time=0,
                    phi=0,
                    theta=0,
                    ptRel=0,
                    ),
                initialSigmas=[
                    1 * u.mm,
                    1 * u.mm,
                    1 * u.degree,
                    1 * u.degree,
                    0 / u.GeV,
                    1 * u.ns,
                ],
                initialSigmaQoverPt=0.1 / u.GeV,
                initialSigmaPtRel=0.1,
                initialVarInflation=[1e0, 1e0, 1e0, 1e0, 1e0, 1e0],
            )

    addKalmanTracks(
        s,
        trackingGeometry,
        field,
    )

    s.addAlgorithm(
        acts.examples.TrackSelectorAlgorithm(
            level=acts.logging.INFO,
            inputTracks="tracks",
            outputTracks="selected-tracks",
            selectorConfig=acts.TrackSelector.Config(
                minMeasurements=global_variables.minHits,
            ),
        )
    )

    s.addWhiteboardAlias("tracks", "selected-tracks")

    s.addWriter(
        acts.examples.SHiPTrackWriter(
           level=acts.logging.INFO,
           inputTracks="tracks",
           inputParticles="particles_selected",
           inputTrackParticleMatching="track_particle_matching",
           filePath=str(global_variables.outputDir) + "/recoTracks.root",
           writeCovMat=True,
        )
    )

    if global_variables.vertexing:

        s.addReader(
            acts.examples.RootVertexReader(
                level=acts.logging.INFO,
                filePath=global_variables.inputFile,
                outputVertices="vertices_truth",
                treeName="vertices"
            )
        )

        addVertexFitting(
            s,
            field,
            vertexFinder=VertexFinder.Truth,
            outputDirRoot=global_variables.outputDir
        )


    if global_variables.DQM:

        s.addWriter(
            acts.examples.RootTrackStatesWriter(
                level=acts.logging.INFO,
                inputTracks="tracks",
                inputParticles="particles_selected",
                inputTrackParticleMatching="track_particle_matching",
                inputSimHits="simhits",
                inputMeasurementSimHitsMap="measurement_simhits_map",
                filePath=str(global_variables.outputDir) + "/trackstates_kf.root",
            )
        )

        s.addWriter(
            acts.examples.TrackFitterPerformanceWriter(
                level=acts.logging.INFO,
                inputTracks="tracks",
                inputParticles="particles_selected",
                inputTrackParticleMatching="track_particle_matching",
                filePath=str(global_variables.outputDir) + "/performance_kf.root",
            )
        )

        s.addWriter(
            acts.examples.RootTrackSummaryWriter(
                level=acts.logging.INFO,
                inputTracks="tracks",
                inputParticles="particles_selected",
                inputTrackParticleMatching="track_particle_matching",
                filePath=str(global_variables.outputDir) + "/tracksummary_kf.root",
                writeCovMat=True,
            )
        )

    s.run()
