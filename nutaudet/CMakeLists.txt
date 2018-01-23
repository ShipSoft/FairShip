# Create a library called "libnutaudet” which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
${BASE_INCLUDE_DIRECTORIES}
${CMAKE_SOURCE_DIR}/shipdata
${CMAKE_SOURCE_DIR}/nutaudet
${ROOT_INCLUDE_DIR} 

)

include_directories( ${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}

)
 
link_directories( ${LINK_DIRECTORIES})

set(SRCS
NuTauMudet.cxx
ShipRpcPoint.cxx
HPT.cxx
HptPoint.cxx
NutaudetContFact.cxx
Target.cxx
EmulsionMagnet.cxx
TargetPoint.cxx
TargetTracker.cxx
TTPoint.cxx
)

Set(HEADERS )
Set(LINKDEF nutaudetLinkDef.h)
Set(LIBRARY_NAME nutaudet)
Set(DEPENDENCIES Base ShipData GeoBase ParBase Geom Core)

GENERATE_LIBRARY()
