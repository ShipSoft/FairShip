# Create a library called "libTauSensitive” which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
${CMAKE_SOURCE_DIR}/shipdata
${CMAKE_SOURCE_DIR}/TauSensitive
)

include_directories( ${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}

)
 
link_directories( ${LINK_DIRECTORIES})

set(SRCS
ShipRpc.cxx            
ShipTauSensitiveContFact.cxx
ShipRpcPoint.cxx
)

Set(HEADERS )
Set(LINKDEF TauSensitiveLinkDef.h)
Set(LIBRARY_NAME TauSensitive)
Set(DEPENDENCIES Base ShipData GeoBase ParBase Geom Cint Core)

GENERATE_LIBRARY()
