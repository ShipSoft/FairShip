# Create a library called "libMuonShieldBackground" which includes the source
# files given in the array . The extension is already found.  Any number of
# sources could be listed here.
find_package(Python3 COMPONENTS Development REQUIRED)

set(INCLUDE_DIRECTORIES ${CMAKE_CURRENT_SOURCE_DIR} ${VMC_INCLUDE_DIRS}
                        ${Python3_INCLUDE_DIRS})

include_directories(${INCLUDE_DIRECTORIES} ${FAIRROOT_INCLUDE_DIR}
                    ${CMAKE_BINARY_DIR}/include)
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES ${ROOT_LIBRARY_DIR} ${FAIRROOT_LIBRARY_DIR})

link_directories(${LINK_DIRECTORIES})

set(SRCS exitHadronAbsorber.cxx pyFairModule.cxx simpleTarget.cxx)

set(LINKDEF LinkDef.h)
set(LIBRARY_NAME ShipMuonShieldBackground)
set(DEPENDENCIES
    Base
    veto
    GeoBase
    ParBase
    Geom
    Core
    FairLogger::FairLogger)

generate_library()
