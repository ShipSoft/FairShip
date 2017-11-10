# Create a library called "libMuonShieldBackground" which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
${CMAKE_SOURCE_DIR}/muonShieldOptimization ${CMAKE_SOURCE_DIR}/veto ${CMAKE_SOURCE_DIR}/shipdata /usr/include/python2.7/
)

include_directories( ${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}

)
 
link_directories( ${LINK_DIRECTORIES})

set(SRCS
exitHadronAbsorber.cxx
# pyFairModule.h  lxplus is unable to find Python.h
)

Set(HEADERS )
Set(LINKDEF muonShieldBackgroundLinkDef.h)
Set(LIBRARY_NAME ShipMuonShieldBackground)
Set(DEPENDENCIES Base GeoBase ParBase Geom Core)

GENERATE_LIBRARY()
