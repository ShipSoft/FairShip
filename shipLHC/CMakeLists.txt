# Create a library called "libnutaudet” which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
${BASE_INCLUDE_DIRECTORIES}
${CMAKE_SOURCE_DIR}/shipdata
${CMAKE_SOURCE_DIR}/shipLHC
${CMAKE_SOURCE_DIR}/veto
${ROOT_INCLUDE_DIR}
)

include_directories( ${INCLUDE_DIRECTORIES} ${VMC_INCLUDE_DIRS} ${FAIRROOT_INCLUDE_DIR} ${FairLogger_INCDIR} ${FMT_INCLUDE_DIR}
)
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}

)
 
link_directories( ${LINK_DIRECTORIES})

set(SRCS
Floor.cxx
boxTarget.cxx
EmulsionDet.cxx
EmulsionDetPoint.cxx
EmulsionDetContFact.cxx
Scifi.cxx
ScifiPoint.cxx
MuFilter.cxx
MuFilterPoint.cxx
MuFilterHit.cxx
sndScifiHit.cxx
sndCluster.cxx
)

Set(HEADERS )
Set(LINKDEF shipLHCLinkDef.h)
Set(LIBRARY_NAME shipLHC)
Set(DEPENDENCIES Base ShipData GeoBase ParBase Geom Core)

include(FindPythonInterp)
list(APPEND PYTHONPATH  "${CMAKE_SOURCE_DIR}/shipLHC/scripts")
list(APPEND PYTHONPATH  "${CMAKE_SOURCE_DIR}/shipLHC/python")
list(APPEND PYTHONPATH  "${CMAKE_SOURCE_DIR}/shipLHC/rawData")

GENERATE_LIBRARY()
