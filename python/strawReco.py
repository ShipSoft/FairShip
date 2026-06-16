import acts
import acts.examples
import numpy as np
import ROOT

import global_variables
import logging

logger = logging.getLogger(__name__)

def make_seed(pos, mom, charge, surface, geo_ctx, nM):

    sigma_drift = 5.0    # 5mm uncertainty (Relaxed from 0.12)
    sigma_long  = 50.0   # 50mm uncertainty (Straws are long)
    sigma_phi   = 0.05   # 50 mrad
    sigma_theta = 0.05   # 50 mrad
    sigma_qp    = 0.5 / mom.Mag() # 20% relative error on q/p
    sigma_time = 10 

    cov = np.diag([
        sigma_drift**2,
        sigma_long**2,
        sigma_phi**2,
        sigma_theta**2,
        sigma_qp**2,
        sigma_time**2
    ]).flatten().tolist()

    #Use the first surface for setting the bound state 
#    surf_center = surface.center(geo_ctx)
#    pos = ROOT.TVector3(surf_center[0], surf_center[1], surf_center[2])

    return acts.createTrackParameters(
        pos.Z() * 10, pos.Y() * 10, pos.X() * -10,
        mom.Z(), mom.Y(), -mom.X(),
        charge, surface, cov, geo_ctx
    )



def runTracking(candidates, trackingGeometry, fieldMap, strawHits):
    """
    Fit tracks in the Reco frame using truth of patrec seeds, optionally vertex
    """

    # Setup geo context 
    geo_ctx = acts.GeometryContext()

    #Hacky way of solving left/right drift ambiguity issue, 
    #move to performing a refit, making use of the residuals
    #rather than using true hit info
    for hit_idx in range(len(strawHits)):
         iHit = strawHits[hit_idx]
    
         dx = iHit[14] - iHit[12] # xbot - xtop
         dy = iHit[15] - iHit[13] # ybot - ytop
         
         wire_x = (iHit[12] + iHit[14]) / 2.0
         wire_y = (iHit[13] + iHit[15]) / 2.0
         vec_to_hit_x = iHit[6] - wire_x
         vec_to_hit_y = iHit[7] - wire_y
         
         nx = -dy
         ny = dx

         dot_product = vec_to_hit_x * nx + vec_to_hit_y * ny
         
         sign = 1.0 if dot_product > 0 else -1.0
    
         # Append sign as index 16
         iHit.push_back(sign)

    measurements = acts.processMeasurements(strawHits, trackingGeometry)

    # Setup output containers
    output_tracks = acts.examples.makeTrackContainer()

    # Loop over seeds (e.g., from PatRec or Truth)
    for cand in candidates:

        sorted_indices = sorted(cand['indices'], key=lambda i: strawHits[i][8])
        
        filtered_indices = []
        seen_layers = set()

        #Add a check to ensure only one hit per layer
        for idx in sorted_indices:
            gid = acts.getMeasurementGeoId(measurements, idx)

            if gid.layer not in seen_layers:
                filtered_indices.append(idx)
                seen_layers.add(gid.layer)

        if len(filtered_indices) < 13:
            logger.debug("Skipping track with too few hits: %d", len(filtered_indices))
            continue

        first_idx = filtered_indices[0]
        
        geo_id = acts.getMeasurementGeoId(measurements, first_idx)
       
        target_surface = acts.getSurface(trackingGeometry, geo_id)
        if not target_surface:
            logger.warning("Could not find surface for GeoID: %s", geo_id)
            continue

        # Call the make_seed function to get the required BoundTrackParameters
        initial_params = make_seed(
            cand['pos'],
            cand['mom'], 
            cand['charge'], 
            target_surface,
            geo_ctx,
            len(strawHits)
        )   

        acts.fitTrack(
            measurements,
            filtered_indices,
            initial_params,
            output_tracks,
            trackingGeometry,
            fieldMap
        )


    vertices = []
    # Define vertex cuts
    min_hits = 13
    max_chi2_ndf = 25.0
   
    good_proxies = []
    for track in output_tracks:
        if not track.hasReferenceSurface():
            continue
   
        chi2_ndf = track.chi2 / track.nDoF if track.nDoF > 0 else float('inf')
   
        if track.nMeasurements >= min_hits and chi2_ndf <= max_chi2_ndf:
            good_proxies.append(track)
   
    # Check for at least one positive and one negative track

    has_pos = any(t.charge > 0 for t in good_proxies)
    has_neg = any(t.charge < 0 for t in good_proxies)
   
    if 2 <= len(good_proxies) <= 4 and has_pos and has_neg:
        print(f"Fitting vertex for {len(good_proxies)} tracks with opposite charge candidates.")
        vertices = acts.fitVertex(good_proxies, fieldMap)
   
        for vtx in vertices:
            print(f"Vertex found at: {vtx.position()}")

    return output_tracks, vertices


def calculateSBTDOCA(output_tracks, sbt_digis, trackingGeometry, fieldMap):
    """
    Extrapolates fitted tracks to the X-plane (Reco frame) of SBT hits.
    """

    nav_cfg = acts.Navigator.Config()

    nav_cfg.trackingGeometry = trackingGeometry

    navigator = acts.Navigator(nav_cfg)

    stepper = acts.EigenStepper(fieldMap)
    propagator = acts.Propagator(stepper, navigator)

    geo_ctx = acts.GeometryContext()
    mag_ctx = acts.MagneticFieldContext()


    distMin = 99999
    hitID = -1

    veto_results = [] 

    for t_idx, track in enumerate(output_tracks):
        if not track.hasReferenceSurface(): continue
        start_params = track.parametersObject
   
        distMin = 99999
        hitID = -1
   
        for s_idx, sbt_hit in enumerate(sbt_digis):
            #Create surface
            hit_pos = np.array([sbt_hit.GetZ()*10.0, sbt_hit.GetY()*10.0, -sbt_hit.GetX()*10.0])
            normal_arr = np.array([1.0, 0.0, 0.0])
            target_surface = acts.createPlaneSurface(hit_pos, normal_arr)

            res_params = acts.extrapolateTrack(propagator, start_params, target_surface, geo_ctx, mag_ctx)
           
            if res_params is not None:
                extrapolated_pos = res_params.position(geo_ctx)

                # Calculate DOCA (Y-Z distance on the X plane)
                doca = np.linalg.norm(extrapolated_pos[1:3] - hit_pos[1:3])
           
                if doca < distMin:
                    distMin = doca
                    hitID = s_idx
   
        veto_results.append((hitID, distMin))

    return veto_results
