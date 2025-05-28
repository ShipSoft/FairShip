set(INCLUDE_DIRECTORIES
${CMAKE_SOURCE_DIR}/shipdata
${CMAKE_SOURCE_DIR}/prestrawdetector
${genfit2_INCDIR}
)

include_directories(${INCLUDE_DIRECTORIES} ${VMC_INCLUDE_DIRS} ${FAIRROOT_INCLUDE_DIR})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}
${genfit2_LIBDIR}
)

link_directories( ${LINK_DIRECTORIES})

set(SRCS
#Put here your sourcefiles
prestrawdetector.cxx
prestrawdetectorPoint.cxx
)

Set(LINKDEF prestrawdetectorLinkDef.h)
Set(LIBRARY_NAME prestrawdetector)
Set(DEPENDENCIES
    Base ShipData FairLogger::FairLogger
)

GENERATE_LIBRARY()
