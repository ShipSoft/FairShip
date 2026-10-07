# Test executables for FairShip data classes

# Test for data class I/O compatibility
add_executable(testDataClassIO test_data_class_io.cxx)
target_link_libraries(
    testDataClassIO
    ShipData
    veto
    strawtubes
    splitcal
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
    splitcal
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

# Normalisation of cascade (charm/beauty) events in FixedTargetGenerator
add_executable(testFixedTargetCascadeWeight test_fixedtarget_cascade_weight.cxx)
target_link_libraries(
    testFixedTargetCascadeWeight
    ShipGen
    ROOT::EGPythia8
    ROOT::Core
    ROOT::RIO
    ROOT::Hist
    ROOT::Tree
    FairRoot::Base
    FairLogger::FairLogger
)
add_test(NAME FixedTargetCascadeWeight COMMAND testFixedTargetCascadeWeight)

# Mass and energy of ShipMCTrack, including spacelike particles
add_executable(testShipMCTrackMass test_shipmctrack_mass.cxx)
target_link_libraries(
    testShipMCTrackMass
    ShipData
    ROOT::Core
    ROOT::EG
    FairRoot::Base
    FairLogger::FairLogger
)
add_test(NAME ShipMCTrackMass COMMAND testShipMCTrackMass)

# Python unit tests. Run with the interpreter of the active environment so the
# ROOT, numpy and pytest it provides are the ones used. activate.sh already
# puts <source>/python on PYTHONPATH; set it here too so a bare ctest works.
find_package(Python3 COMPONENTS Interpreter REQUIRED)
add_test(
    NAME PythonUnitTests
    COMMAND ${Python3_EXECUTABLE} -m pytest -q ${CMAKE_CURRENT_SOURCE_DIR}
)
set_tests_properties(
    PythonUnitTests
    PROPERTIES
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
        ENVIRONMENT "PYTHONPATH=${CMAKE_SOURCE_DIR}/python:$ENV{PYTHONPATH}"
)
