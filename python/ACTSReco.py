import sys
import os
import global_variables
from rootpyPickler import Unpickler

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
)

fgeo = ROOT.TFile.Open(global_variables.geoFile)
upkl = Unpickler(fgeo)
ShipGeo = upkl.load('ShipGeo')
#if hasattr(ShipGeo.Bfield,"fieldMap"):
#fieldMapFile = ShipGeo.Bfield.fieldMap

def runTracking():
    customLogLevel=acts.examples.defaultLogging(logLevel=acts.logging.VERBOSE)
    u = acts.UnitConstants

    if global_variables.detector == "SiliconTarget":
       field = acts.ConstantBField(acts.Vector3(0.0, 0.0, 0.0 * u.T))
       digiConfigFile = "SiliconTarget-digi-config.json"
       detector = acts.examples.SiTargetBuilder(fileName=str(global_variables.geoFile),
                                                surfaceLogLevel=customLogLevel(),
                                                layerLogLevel=customLogLevel(),
                                                volumeLogLevel=customLogLevel(),
                                               )
    if global_variables.detector == "MTC":
        return

    if global_variables.detector == "StrawTracker":
       field = acts.MagneticFieldMapXyz(ShipGeo.Bfield.fieldMap, "Data", u.cm, u.T, 
                                        translateToGlobal=ROOT.TVector3(ShipGeo.Bfield.x,
                                                                        ShipGeo.Bfield.y,
                                                                        ShipGeo.Bfield.z)) 
       digiConfigFile = "StrawTracker-digi-config.json"
       detector = acts.examples.StrawTrackerBuilder(fileName=str(global_variables.geoFile),
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
                    treeName="hitTree"
                )
            )

    addDigitization(
        s,
        trackingGeometry,
        field,
        digiConfigFile=str(digiConfigFile),
        rnd=rnd,
        outputDirRoot=global_variables.outputDir
    )

    addDigiParticleSelection(
        s,
        ParticleSelectorConfig(
            pt=(0.9 * u.GeV, None),
            measurements=(7, None),
            removeNeutral=True,
            removeSecondaries=True,
        ),
    )

    addSeeding(
            s,
            trackingGeometry,
            field,
            rnd=rnd,
            inputParticles="particles_generated",
            seedingAlgorithm=SeedingAlgorithm.TruthSmeared,
            particleHypothesis=acts.ParticleHypothesis.muon,
        )

    reverseFilteringMomThreshold=0 * u.GeV

    addKalmanTracks(
        s,
        trackingGeometry,
        field,
        reverseFilteringMomThreshold,
    )

    s.addAlgorithm(
        acts.examples.TrackSelectorAlgorithm(
            level=acts.logging.INFO,
            inputTracks="tracks",
            outputTracks="selected-tracks",
            selectorConfig=acts.TrackSelector.Config(
                minMeasurements=7,
            ),
        )
    )

    addTrackWriters(
        s,
        tracks="tracks",
        writeCovMat=True,
        logLevel=acts.logging.VERBOSE,
        outputDirRoot=global_variables.outputFile
            )


    if global_variables.vertexing:

        s.addReader(
            acts.examples.RootVertexReader(
                level=acts.logging.DEBUG,
                filePath=str(inputHitsPath),
                outputVertices="vertices_generated",
                treeName="vertices"
            )
        )
        #s.addWhiteboardAlias("vertices_truth", "particles_generated")

        addVertexFitting(
            s,
            field,
            vertexFinder=VertexFinder.Truth,
            outputDirRoot=global_variables.outputFile
        )


    if global_variables.DQM:

        s.addWhiteboardAlias("tracks", "selected-tracks")
        s.addWriter(
            acts.examples.TrackFitterPerformanceWriter(
                level=acts.logging.VERBOSE,
                inputTracks="tracks",
                inputParticles="particles_selected",
                inputTrackParticleMatching="track_particle_matching",
                filePath=str(global_variables.outputDir) + "/performance_kf.root",
            )
        )

        if global_variables.vertexing:
            s.addWriter(
                acts.examples.VertexNTupleWriter(
                    level=acts.logging.INFO,
                    inputTracks="tracks",
                    inputTrackParticleMatching="track_particle_matching",
                    inputParticles="particles_selected",
                    inputSelectedParticles=selectedParticles,
                    inputTruthVertices="vertices_truth",
                    writeTrackInfo=True,
                    treeName="vertexing",
                    filePath=str(global_variables.outputDir) + "/performance_vertexing.root",
                )
            )

    s.run()
