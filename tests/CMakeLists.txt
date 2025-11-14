# Test executables for FairShip data classes

# Add link directories
link_directories(${ROOT_LIBRARY_DIR} ${FAIRROOT_LIBRARY_DIR} ${genfit2_LIBDIR})

# Test for data class I/O compatibility
add_executable(testDataClassIO test_data_class_io.cxx)

target_include_directories(testDataClassIO PRIVATE
    ${CMAKE_SOURCE_DIR}/shipdata
    ${CMAKE_SOURCE_DIR}/veto
    ${CMAKE_SOURCE_DIR}/strawtubes
    ${CMAKE_SOURCE_DIR}/splitcal
    ${CMAKE_SOURCE_DIR}/SND/MTC
    ${CMAKE_SOURCE_DIR}/SND/SiliconTarget
    ${CMAKE_SOURCE_DIR}/SND/EmulsionTarget
    ${CMAKE_SOURCE_DIR}/TimeDet
    ${CMAKE_SOURCE_DIR}/UpstreamTagger
)

target_link_libraries(testDataClassIO
    ShipData
    veto
    strawtubes
    splitcal
    MTCDetector
    SiliconTarget
    TimeDet
    UpstreamTagger
    EmulsionTarget
    Core
    RIO
    Geom
    GenVector
    EG
    Physics
    Base
    genfit2
    FairLogger::FairLogger
)

# Add test to CTest
add_test(NAME DataClassIO COMMAND testDataClassIO)

# Test for actual RNtuple I/O operations (requires ROOT >= 6.36)
if(ROOT_VERSION VERSION_GREATER_EQUAL "6.36")
  message(STATUS "Building RNtuple I/O test (ROOT ${ROOT_VERSION})")
  add_executable(testRNtupleIO test_rntuple_io.cxx)

  target_include_directories(testRNtupleIO PRIVATE
      ${CMAKE_SOURCE_DIR}/shipdata
      ${CMAKE_SOURCE_DIR}/veto
      ${CMAKE_SOURCE_DIR}/strawtubes
      ${CMAKE_SOURCE_DIR}/splitcal
      ${CMAKE_SOURCE_DIR}/SND/MTC
      ${CMAKE_SOURCE_DIR}/SND/SiliconTarget
      ${CMAKE_SOURCE_DIR}/SND/EmulsionTarget
      ${CMAKE_SOURCE_DIR}/TimeDet
      ${CMAKE_SOURCE_DIR}/UpstreamTagger
  )

  target_link_libraries(testRNtupleIO
      ShipData
      veto
      strawtubes
      splitcal
      MTCDetector
      SiliconTarget
      TimeDet
      UpstreamTagger
      EmulsionTarget
      Core
      RIO
      Geom
      GenVector
      EG
      Physics
      ROOTNTuple
      Base
      genfit2
      FairLogger::FairLogger
  )

  add_test(NAME RNtupleIO COMMAND testRNtupleIO)
else()
  message(STATUS "Skipping RNtuple I/O test (requires ROOT >= 6.36, found ${ROOT_VERSION})")
endif()
