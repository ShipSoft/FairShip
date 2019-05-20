# Create a library called "libstrawtubes" which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
${CMAKE_SOURCE_DIR}/shipdata
${CMAKE_SOURCE_DIR}/strawtubes
)

include_directories( ${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}
) 

link_directories( ${LINK_DIRECTORIES})

set(SRCS
#Put here your sourcefiles
strawtubes.cxx
strawtubesContFact.cxx
strawtubesPoint.cxx
strawtubesHit.cxx
Tracklet.cxx
)

Set(LINKDEF strawtubesLinkDef.h)
Set(LIBRARY_NAME strawtubes)
Set(DEPENDENCIES
    Base ShipData
)

GENERATE_LIBRARY()
