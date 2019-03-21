# Create a library called "libShipData" which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
${CMAKE_SOURCE_DIR}/shipdata
${CMAKE_SOURCE_DIR}/genfit/core/include
${CMAKE_SOURCE_DIR}/genfit/fitters/include
)

include_directories( ${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}
${CMAKE_SOURCE_DIR}/shipdata

)
 
link_directories( ${LINK_DIRECTORIES})

set(SRCS
ShipHit.cxx 
ShipStack.cxx 
ShipMCTrack.cxx
ShipParticle.cxx
TrackInfo.cxx
)

Set(HEADERS )
Set(LINKDEF MCStackLinkDef.h)
Set(LIBRARY_NAME ShipData)
Set(DEPENDENCIES Base EG Physics Core genfit)

GENERATE_LIBRARY()

