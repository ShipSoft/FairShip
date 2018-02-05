# Create a library called "libTimeDet" which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
${CMAKE_SOURCE_DIR}/shipdata
${CMAKE_SOURCE_DIR}/TimeDet
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
TimeDetPoint.cxx
TimeDetHit.cxx
TimeDet.cxx
)

Set(LINKDEF TimeDetLinkDef.h)
Set(LIBRARY_NAME TimeDet)
Set(DEPENDENCIES
    Base ShipData
)

GENERATE_LIBRARY()
