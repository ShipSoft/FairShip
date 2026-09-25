# Test executables for FairShip data classes

# Test for data class I/O compatibility
add_executable(testDataClassIO test_data_class_io.cxx)
target_link_libraries(
    testDataClassIO
    ShipData
    veto
    strawtubes
    CaloScoringPlane
    MTCDetector
    SiliconTarget
    TimeDet
    UpstreamTagger
    EmulsionTarget
    ROOT::Core
    ROOT::RIO
    ROOT::Geom
    ROOT::GenVector
    ROOT::EG
    ROOT::Physics
    FairRoot::Base
    genfit2
    FairLogger::FairLogger
)
add_test(NAME DataClassIO COMMAND testDataClassIO)

# Test for actual RNtuple I/O operations
add_executable(testRNtupleIO test_rntuple_io.cxx)
target_link_libraries(
    testRNtupleIO
    ShipData
    veto
    strawtubes
    CaloScoringPlane
    MTCDetector
    SiliconTarget
    TimeDet
    UpstreamTagger
    EmulsionTarget
    ROOT::Core
    ROOT::RIO
    ROOT::Geom
    ROOT::GenVector
    ROOT::EG
    ROOT::Physics
    ROOT::ROOTNTuple
    FairRoot::Base
    genfit2
    FairLogger::FairLogger
)
add_test(NAME RNtupleIO COMMAND testRNtupleIO)

add_executable(testTimeDetGeometry test_timedet_geometry.cxx)
target_link_libraries(
    testTimeDetGeometry
    TimeDet
    ROOT::Core
    ROOT::Geom
    FairRoot::Base
)
add_test(NAME TimeDetGeometry COMMAND testTimeDetGeometry)
set_tests_properties(
    TimeDetGeometry
    PROPERTIES WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
)
