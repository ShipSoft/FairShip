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

# Test for actual RNTuple I/O operations
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

# Shell-driven FairShip regression tests. The Python harness validates the YAML
# configuration, emits test declarations, and filters/compares output; CTest
# owns execution ordering, resource locking, and parallelism.
find_package(Python3 REQUIRED COMPONENTS Interpreter)

option(
    FAIRSHIP_KEEP_TEST_OUTPUT
    "Keep FairShip regression-test working directories after CTest finishes"
    OFF
)
set(FAIRSHIP_TEST_WORKDIR_ROOT "${CMAKE_BINARY_DIR}/Testing/fairship_tests")

function(fairship_add_regression_test)
    cmake_parse_arguments(TEST "PREPARE;CLEANUP" "NAME;GROUP" "DEPENDS" ${ARGN})
    set(test_name "FairShip.${TEST_NAME}")
    set(workdir "${FAIRSHIP_TEST_WORKDIR_ROOT}/${TEST_GROUP}")
    set(lifecycle_arguments "")
    if(TEST_PREPARE)
        list(APPEND lifecycle_arguments --prepare)
    endif()
    if(TEST_CLEANUP AND NOT FAIRSHIP_KEEP_TEST_OUTPUT)
        list(APPEND lifecycle_arguments --cleanup)
    endif()

    add_test(
        NAME "${test_name}"
        COMMAND
            "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/fairship_tests/harness.py" --run
            "${TEST_NAME}" --workdir "${workdir}" ${lifecycle_arguments}
    )
    set(dependencies "")
    foreach(dependency IN LISTS TEST_DEPENDS)
        list(APPEND dependencies "FairShip.${dependency}")
    endforeach()
    set_tests_properties(
        "${test_name}"
        PROPERTIES
            DEPENDS "${dependencies}"
            LABELS "fairship;regression"
            RESOURCE_LOCK "fairship_${TEST_GROUP}"
    )
endfunction()

execute_process(
    COMMAND
        "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/fairship_tests/harness.py" --emit-cmake
    RESULT_VARIABLE fairship_test_configuration_status
    OUTPUT_VARIABLE fairship_test_declarations
    ERROR_VARIABLE fairship_test_configuration_error
)
if(NOT fairship_test_configuration_status EQUAL 0)
    message(
        FATAL_ERROR
        "Invalid FairShip regression-test configuration:\n${fairship_test_configuration_error}"
    )
endif()
cmake_language(EVAL CODE "${fairship_test_declarations}")
