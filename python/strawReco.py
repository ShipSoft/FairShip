import acts
import acts.examples
import numpy as np
import ROOT


def make_seed(pos, mom, charge, surface, geo_ctx):
    # Rotate momentum vector reconstruction frame
    mom_rec = ROOT.TVector3(mom.Z(), mom.Y(), -mom.X())

    global_pos = acts.Vector3(pos.Z() * 10.0, pos.Y() * 10.0, -pos.X() * 10.0)
    local_pos = surface.globalToLocal(geo_ctx, global_pos, acts.Vector3(0, 0, 0)).value()

    # ACTS BoundTrackParameters
    # params: loc0, loc1, phi, theta, q/p, time
    params_vec = np.array([local_pos[0], local_pos[1], mom.Phi(), mom.Theta(), charge / mom.Mag(), 0])
    cov_matrix = np.diag([0.5, 0.5, 0.01, 0.01, 0.001, 1.0]) ** 2
    return acts.BoundTrackParameters(target_surface, params_vec, cov_matrix, acts.ParticleHypothesis.muon)


def run_tracking(self, candidates):
    """
    Fit tracks in the Reco frame using truth of patrec seeds, optionally vertex
    """

    wb = acts.examples.WhiteBoard(acts.logging.INFO)

    ctx = acts.examples.AlgorithmContext(0, 0, wb)

    cfg = acts.examples.SHiPMeasurementProvider.Config()
    cfg.inputHitArray = self.strawHits
    cfg.trackingGeometry = self.trackingGeometry
    cfg.detectorType = acts.examples.SHiPDetectorType.Straw
    cfg.outputMeasurements = "my_measurements"

    provider = acts.examples.SHiPMeasurementProvider(cfg, acts.logging.INFO)
    provider.execute(ctx)

    measurements = wb.get("my_measurements")

    # Setup Contexts
    geo_ctx = acts.GeometryContext()
    mag_ctx = acts.MagneticFieldExtendedContext()
    calib_ctx = acts.CalibrationContext()

    # Setup the fitter function
    fitter_func = acts.examples.makeKalmanFitterFunction(self.trackingGeometry, self.actsFieldMap)

    # Setup output containers
    track_container = acts.VectorTrackContainer()
    track_mtj_container = acts.VectorMultiTrajectory()
    output_tracks = acts.examples.TrackContainer(track_container, track_mtj_container)

    # Calibrator and Options
    calibrator = acts.examples.makePassThroughCalibrator()
    cal_adapter = acts.examples.MeasurementCalibratorAdapter(calibrator, measurements)

    # Loop over seeds (e.g., from PatRec or Truth)
    for cand in candidates:
        if len(cand["indices"]) < 13:
            logger.debug("Skipping track with too few hits: %d", len(cand["indices"]))
            continue

        # Create the PerigeeSurface at the Z of the first hit
        z_first_mm = cand["pos"].Z() * 10.0
        target_surface = acts.PerigeeSurface(acts.Vector3(z_first_mm, 0, 0))

        # Define Fitter Options for this track
        fit_options = acts.examples.TrackFitterFunction.GeneralFitterOptions(
            geo_ctx, mag_ctx, calib_ctx, target_surface, acts.PropagatorPlainOptions(geo_ctx, mag_ctx)
        )

        # Call the make_seed function to get the required BoundTrackParameters
        initial_params = make_seed(cand["pos"], cand["mom"], cand["charge"], target_surface, geo_ctx)
        source_links = []
        for idx in cand["indices"]:
            meas = measurements.getMeasurement(idx)
            sl = acts.examples.IndexSourceLink(meas.geometryId(), idx)
            source_links.append(acts.SourceLink(sl))

        # Perform the fit
        fitter_func(source_links, initial_params, fit_options, cal_adapter, output_tracks)

    # Vertexing (If > 2 tracks found) and vertexing enabled
    vertices = []
    if len(output_tracks) >= 2 and global_variables.vertexing:
        v_fitter = acts.FullBilloirVertexFitter(self.actsFieldMap)
        v_fitter_state = v_fitter.State()
        v_options = acts.VertexingOptions(geo_ctx, mag_ctx)

        field_cache = self.actsFieldMap.makeCache(mag_ctx)

        # Extract parameters from successful fits
        v_input_tracks = [t.parameters() for t in output_tracks if t.hasReferenceSurface()]

        v_result = v_fitter.fit(v_input_tracks, v_options, field_cache)
        if v_result.ok():
            vertices.append(v_result.value())

    self.fACTSArray.clear()
    self.fACTSVertexArray.clear()

    for track in output_tracks:
        self.fACTSArray.push_back(acts.examples.RecoTrack(track))

    for vtx in vertices:
        self.fACTSVertexArray.push_back(acts.examples.RecoVertex(vtx))

    return output_tracks


def calculate_sbt_doca(self, output_tracks, sbt_digis):
    """
    Extrapolates fitted tracks to the X-plane (Reco frame) of SBT hits.
    """

    stepper = acts.EigenStepper(self.actsFieldMap)
    navigator = acts.Navigator(trackingGeometry=self.trackingGeometry)
    propagator = acts.Propagator(stepper, navigator)

    geo_ctx = acts.GeometryContext()
    mag_ctx = acts.MagneticFieldExtendedContext()
    prop_options = acts.PropagatorPlainOptions(geo_ctx, mag_ctx)
    prop_options.pathLimit = 100000.0  # 100 meters

    distMin = 99999
    hitID = -1

    for t_idx, track in enumerate(output_tracks):
        if not track.hasReferenceSurface():
            continue
        start_params = track.parameters()

        for s_idx, sbt_hit in enumerate(sbt_digis):
            # Rotate and scale into reconstruction frame
            hit_pos = acts.Vector3(sbt_hit.GetZ() * 10.0, sbt_hit.GetY() * 10.0, -sbt_hit.GetX() * 10.0)

            # Define target as a plane at the SBT hit X
            target_surface = acts.PlaneSurface(hit_pos, acts.Vector3(1, 0, 0))

            res = propagator.propagate(start_params, target_surface, prop_options)

            if res.ok():
                extrapolated_pos = res.value().endParameters().position(geo_ctx)
                # Calculate DOCA (Y-Z distance at the X plane)
                doca = np.linalg.norm(extrapolated_pos[0:2] - hit_pos[0:2])

                if doca < distMin:
                    distMin = doca
                    hitID = t_idx

        self.vetoHitOnTrackArray.push_back(ROOT.vetoHitOnTrack(hitID, distMin))
