# Create a library called "libnutaudet” which includes the source files given in
# the array . The extension is already found.  Any number of sources could be
# listed here.

set(INCLUDE_DIRECTORIES
    ${BASE_INCLUDE_DIRECTORIES}
    ${CMAKE_SOURCE_DIR}/shipdata
    ${CMAKE_SOURCE_DIR}/charmdet
    ${genfit2_INCDIR})

include_directories(${INCLUDE_DIRECTORIES} ${VMC_INCLUDE_DIRS}
                    ${FAIRROOT_INCLUDE_DIR})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES ${ROOT_LIBRARY_DIR} ${FAIRROOT_LIBRARY_DIR}
                     ${genfit2_LIBDIR})

link_directories(${LINK_DIRECTORIES})

set(SRCS
    Box.cxx
    BoxPoint.cxx
    BoxContFact.cxx
    Spectrometer.cxx
    SpectrometerPoint.cxx
    PixelModules.cxx
    PixelModulesPoint.cxx
    MufluxSpectrometer.cxx
    MufluxSpectrometerPoint.cxx
    SciFi.cxx
    SciFiPoint.cxx
    MuonTagger.cxx
    MuonTaggerPoint.cxx
    Scintillator.cxx
    ScintillatorPoint.cxx)

set(HEADERS)
set(LINKDEF BoxLinkDef.h)
set(LIBRARY_NAME charmdet)
set(DEPENDENCIES
    Base
    ShipData
    GeoBase
    ParBase
    Geom
    Core
    genfit2
    FairLogger::FairLogger)

generate_library()
