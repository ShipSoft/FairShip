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

# add the list of source code files -- careful, when a new file is added!
AUX_SOURCE_DIRECTORY( ${CMAKE_SOURCE_DIR}/millepede          library_sources )

string(REPLACE "/src/" "/include/"  HEADERS "${library_sources}")
string(REPLACE ".cc" ".h"  HEADERS "${HEADERS}")
set(HEADERS "${HEADERS}"
  ${CMAKE_SOURCE_DIR}/genfit/utilities/include/mySpacepointDetectorHit.h
  ${CMAKE_SOURCE_DIR}/genfit/utilities/include/mySpacepointMeasurement.h
)
Set(SRCS ${library_sources})
Set(LINKDEF ${CMAKE_SOURCE_DIR}/genfit/millepedeLinkDef.h)
Set(LIBRARY_NAME millepede)
Set(DEPENDENCIES Core Geom Matrix Eve Gui Physics MathCore EG)

GENERATE_LIBRARY()

