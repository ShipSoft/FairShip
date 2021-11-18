# Create a library called "libnutaudet” which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
${BASE_INCLUDE_DIRECTORIES}
${CMAKE_SOURCE_DIR}/shipdata
${CMAKE_SOURCE_DIR}/shipLHC
${CMAKE_SOURCE_DIR}/sndFairTasks
${CMAKE_SOURCE_DIR}/veto
${ROOT_INCLUDE_DIR}
${FAIRROOT_INCLUDE_DIR}
${FairLogger_INCDIR}
${FMT_INCLUDE_DIR}

)

include_directories( ${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}

)
 
link_directories( ${LINK_DIRECTORIES})

set(SRCS
DigiTaskSND.cxx
)

Set(HEADERS)
Set(LINKDEF sndFairTasksLinkDef.h)
Set(LIBRARY_NAME sndFairTasks)
Set(DEPENDENCIES Base ShipData shipLHC GeoBase ParBase Geom Core)

GENERATE_LIBRARY()
