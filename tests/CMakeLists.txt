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

# Data-driven J/psi sampler (ROOT GenVector and MathCore only): normalisation,
# weights, nominal data map, configuration files
add_executable(
    testJpsiSampler
    test_jpsi_sampler.cxx
    ${CMAKE_SOURCE_DIR}/shipgen/JpsiSampler.cxx
)
target_include_directories(testJpsiSampler PRIVATE ${CMAKE_SOURCE_DIR}/shipgen)
target_link_libraries(testJpsiSampler PRIVATE ROOT::GenVector ROOT::MathCore)
add_test(NAME JpsiSampler COMMAND testJpsiSampler)

# JpsiGenerator in a small TGeo geometry: target closure and track bookkeeping
add_executable(testJpsiGenerator test_jpsi_generator.cxx)
target_link_libraries(
    testJpsiGenerator
    ShipGen
    ROOT::EGPythia8
    ROOT::Core
    ROOT::Geom
    FairRoot::Base
    FairLogger::FairLogger
)
add_test(NAME JpsiGenerator COMMAND testJpsiGenerator)

# Closure of the data-map fit of macro/jpsi/JpsiDataMap.C (Minuit2)
add_executable(
    testJpsiDataMapFit
    test_jpsi_datamap_fit.cxx
    ${CMAKE_SOURCE_DIR}/shipgen/JpsiSampler.cxx
)
target_include_directories(
    testJpsiDataMapFit
    PRIVATE ${CMAKE_SOURCE_DIR}/shipgen
)
target_link_libraries(
    testJpsiDataMapFit
    PRIVATE ROOT::GenVector ROOT::MathCore ROOT::Minuit2
)
add_test(NAME JpsiDataMapFit COMMAND testJpsiDataMapFit)
