#ifdef __CINT__

#pragma link off all globals;
#pragma link off all classes;
#pragma link off all functions;

// These need no special treatment.
#pragma link C++ class genfit::AbsFinitePlane+;
#pragma link C++ class genfit::AbsHMatrix+;
#pragma link C++ class genfit::RectangularFinitePlane+;
#pragma link C++ class genfit::FitStatus+;
#pragma link C++ class genfit::MaterialProperties+;
#pragma link C++ class genfit::TrackCand+;
#pragma link C++ class genfit::TrackCandHit+;
#pragma link C++ class genfit::FieldManager+;
#pragma link C++ class genfit::AbsFitter+;
#pragma link C++ class genfit::AbsBField+;
#pragma link C++ class genfit::AbsKalmanFitter+;
#pragma link C++ class genfit::KalmanFitStatus;
#pragma link C++ class genfit::KalmanFitterRefTrack+;
#pragma link C++ class genfit::GFGbl+;
#pragma link C++ class genfit::HMatrixU+;
#pragma link C++ class genfit::HMatrixUnit+;
#pragma link C++ class genfit::HMatrixV+;
#pragma link C++ class genfit::HMatrixUV+;
#pragma link C++ class genfit::ProlateSpacepointMeasurement+;
#pragma link C++ class genfit::WireMeasurement+;
#pragma link C++ class genfit::WirePointMeasurement+;

#pragma link C++ class genfit::HMatrixPhi-;
#pragma link C++ class genfit::FullMeasurement-;
#pragma link C++ class genfit::PlanarMeasurement-;
#pragma link C++ class genfit::SpacepointMeasurement-;

#pragma link C++ class genfit::WireTrackCandHit+;

#pragma link C++ class genfit::RKTrackRep-;
#pragma link C++ class genfit::RKTools+;
#pragma link C++ class genfit::TGeoMaterialInterface+;
#pragma link C++ class genfit::MaterialEffects+;

#pragma link C++ class genfit::HelixTrackModel+;
#pragma link C++ class genfit::MeasurementCreator+;
#pragma link C++ enum genfit::eMeasurementType;

// These inherit from classes with custom streamers, or reference shared_ptrs in their interfaces.
#pragma link C++ class genfit::AbsTrackRep+;
#pragma link C++ class genfit::MeasuredStateOnPlane+;
#pragma link C++ class genfit::EventDisplay+;
#pragma link C++ class genfit::ConstField+;
#pragma link C++ class genfit::GoliathField+;
#pragma link C++ class genfit::BellField+;
#pragma link C++ class genfit::FairShipFields+;
#pragma link C++ class genfit::KalmanFittedStateOnPlane+;
#pragma link C++ class genfit::ReferenceStateOnPlane+;

// These need their owners fixed up after reading.
#pragma link C++ class genfit::AbsMeasurement+; // trackPoint_

// These cannot be dealt with by default streamers because of
// shared_ptrs<> or scoped_ptrs<>.  Additionally, they may need their
// owners fixed up.
#pragma link C++ class genfit::AbsFitterInfo-; // trackPoint_, rep_, sharedPlanePtr
#pragma link C++ class genfit::DetPlane-;  // scoped_ptr<> finitePlane_
#pragma link C++ class genfit::MeasurementOnPlane-; // scoped_ptr<> hMatrix_
#pragma link C++ class genfit::StateOnPlane-;  // rep_, sharedPlanePtr
#pragma link C++ class genfit::ThinScatterer-; // sharedPlanePtr
#pragma link C++ class genfit::Track-;
#pragma link C++ class genfit::TrackPoint-; // track_, fixup the map
#pragma link C++ class std::vector<genfit::Track*>-;
#pragma link C++ class std::vector<genfit::MeasuredStateOnPlane*>-;
// Classes that needed manually written streamers:
#pragma link C++ class genfit::KalmanFitter-;
#pragma link C++ class genfit::KalmanFitterInfo-;
#pragma link C++ class genfit::DAF-;

#pragma link C++ class genfit::mySpacepointDetectorHit+;
#pragma link C++ class genfit::mySpacepointMeasurement+;


#endif

