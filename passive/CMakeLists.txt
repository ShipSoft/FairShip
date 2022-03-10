# Create a library called "libPassive" which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.
include(CMakePrintHelpers)

set(INCLUDE_DIRECTORIES
${CMAKE_SOURCE_DIR}/passive ${GEANT4_INCLUDE_DIR} ${VMC_INCLUDE_DIRS} ${FAIRROOT_INCLUDE_DIR} ${FairLogger_INCDIR} ${FMT_INCLUDE_DIR}
)

include_directories( ${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

cmake_print_variables(INCLUDE_DIRECTORIES)
cmake_print_variables(FAIRROOT_INCLUDE_DIR)

Message(STATUS "?? include directories ${FAIRROOT_INCLUDE_DIR} ")
set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}

)
 
link_directories( ${LINK_DIRECTORIES})

set(SRCS
ShipCave.cxx            
ShipGeoCave.cxx        
ShipMagnet.cxx         
ShipChamber.cxx
ShipTargetStation.cxx
MufluxTargetStation.cxx
ShipMuonShield.cxx
ShipPassiveContFact.cxx
ShipTAUMagneticSpectrometer.cxx
ShipGoliath.cxx
)

Set(HEADERS )
Set(LINKDEF PassiveLinkDef.h)
Set(LIBRARY_NAME ShipPassive)
Set(DEPENDENCIES Base GeoBase ParBase Geom Core)

GENERATE_LIBRARY()
