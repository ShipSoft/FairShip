# Create a library called "libsplitcal" which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
${CMAKE_SOURCE_DIR}/shipdata
${CMAKE_SOURCE_DIR}/splitcal
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
splitcal.cxx
splitcalContFact.cxx
splitcalPoint.cxx
splitcalHit.cxx
splitcalCluster.cxx
)

Set(LINKDEF splitcalLinkDef.h)
Set(LIBRARY_NAME splitcal)
Set(DEPENDENCIES
    Base ShipData
)

GENERATE_LIBRARY()
