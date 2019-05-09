# Create a library called "libmillepede" which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

# Set the build type. Possibilities are None, Debug, Release,
# RelWithDebInfo and MinSizeRel
SET(CMAKE_BUILD_TYPE Release)

set(INCLUDE_DIRECTORIES
        ${CMAKE_SOURCE_DIR}/millepede
)

include_directories( ${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}
) 

link_directories( ${LINK_DIRECTORIES})

Set(SRCS Mille.cc)
Set(HEADERS Mille.h)
Set(LINKDEF millepedeLinkDef.h)
Set(LIBRARY_NAME millepede)
Set(DEPENDENCIES Core Geom Matrix Eve Gui Physics MathCore EG)

GENERATE_LIBRARY()