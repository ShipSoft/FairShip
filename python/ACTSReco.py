import sys
import os
import global_variables

env = os.environ.get("ACTS_ROOT")
python_dir=f"{env}/python"
sys.path.append(python_dir)

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
)


def runTracking():
    customLogLevel=acts.examples.defaultLogging(logLevel=acts.logging.VERBOSE)

    if global_variables.detector == "SiliconTarget":
       digiConfigFile = "SiliconTarget-digi-config.json"
       detector = acts.examples.SiTargetBuilder(fileName=str(global_variables.geoFile),
                                              surfaceLogLevel=customLogLevel(),
                                              layerLogLevel=customLogLevel(),
                                              volumeLogLevel=customLogLevel(),
                                             )
    if global_variables.detector == "StrawTracker":
       digiConfigFile = "StrawTracker-digi-config.json"
       detector = acts.examples.StrawTrackerBuilder(fileName=str(global_variables.geoFile),
                                              surfaceLogLevel=customLogLevel(),
                                              layerLogLevel=customLogLevel(),
                                              volumeLogLevel=customLogLevel(),
                                             )

    trackingGeometry = detector.trackingGeometry()

    s = acts.examples.Sequencer(events=-1, numThreads=-1)
    s.config.logLevel = acts.logging.INFO
    rnd = acts.examples.RandomNumbers(seed=42)
    u = acts.UnitConstants
    field = acts.ConstantBField(acts.Vector3(0.0, 0.0, 0.0 * u.T))

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
    s.addWhiteboardAlias("tracks", "selected-tracks")

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
        acts.examples.RootTrackSummaryWriter(
            level=acts.logging.INFO,
            inputTracks="tracks",
            inputParticles="particles_selected",
            inputTrackParticleMatching="track_particle_matching",
            filePath=str(global_variables.outputDir) + "/tracksummary_kf.root",
        )
    )

    if global_variables.vertexing:
        s.addWhiteboardAlias("vertices_truth", "particles_generated")

        addVertexFitting(
            s,
            field,
            vertexFinder=VertexFinder.Truth,
            outputDirRoot=global_variables.outputDir
        )

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
