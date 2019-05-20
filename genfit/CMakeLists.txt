# Create a library called "libgenfit" which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.
If (Boost_Avail)
    INCLUDE_DIRECTORIES(${Boost_INCLUDE_DIR})
    MESSAGE("-- Boost is found at: ${Boost_INCLUDE_DIR}")
Else (Boost_Avail)
    MESSAGE("-- Boost is not found at... ERROR")
EndIf (Boost_Avail)

# Set the build type. Possibilities are None, Debug, Release,
# RelWithDebInfo and MinSizeRel
SET(CMAKE_BUILD_TYPE Release)

set(INCLUDE_DIRECTORIES
        ${CMAKE_SOURCE_DIR}/genfit/core/include
	${CMAKE_SOURCE_DIR}/genfit/eventDisplay/include
	${CMAKE_SOURCE_DIR}/genfit/fields/include
	${CMAKE_SOURCE_DIR}/genfit/finitePlanes/include
	${CMAKE_SOURCE_DIR}/genfit/fitters/include
	${CMAKE_SOURCE_DIR}/genfit/GBL/include
	${CMAKE_SOURCE_DIR}/genfit/measurements/include
	${CMAKE_SOURCE_DIR}/genfit/trackReps/include
	${CMAKE_SOURCE_DIR}/genfit/utilities/include
	${CMAKE_SOURCE_DIR}/field
)

include_directories( ${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}
) 

link_directories( ${LINK_DIRECTORIES})

# add the list of source code files -- careful, when a new file is added!
AUX_SOURCE_DIRECTORY( ${CMAKE_SOURCE_DIR}/genfit/core/src          library_sources )
AUX_SOURCE_DIRECTORY( ${CMAKE_SOURCE_DIR}/genfit/eventDisplay/src  library_sources )
AUX_SOURCE_DIRECTORY( ${CMAKE_SOURCE_DIR}/genfit/fields/src        library_sources )
AUX_SOURCE_DIRECTORY( ${CMAKE_SOURCE_DIR}/genfit/finitePlanes/src  library_sources )
AUX_SOURCE_DIRECTORY( ${CMAKE_SOURCE_DIR}/genfit/fitters/src       library_sources )
AUX_SOURCE_DIRECTORY( ${CMAKE_SOURCE_DIR}/genfit/GBL/src           library_sources )
AUX_SOURCE_DIRECTORY( ${CMAKE_SOURCE_DIR}/genfit/measurements/src  library_sources )
AUX_SOURCE_DIRECTORY( ${CMAKE_SOURCE_DIR}/genfit/trackReps/src     library_sources )
AUX_SOURCE_DIRECTORY( ${CMAKE_SOURCE_DIR}/genfit/utilities/src     library_sources )

string(REPLACE "/src/" "/include/"  HEADERS "${library_sources}")
string(REPLACE ".cc" ".h"  HEADERS "${HEADERS}")
set(HEADERS "${HEADERS}"
  ${CMAKE_SOURCE_DIR}/genfit/utilities/include/mySpacepointDetectorHit.h
  ${CMAKE_SOURCE_DIR}/genfit/utilities/include/mySpacepointMeasurement.h
)
Set(SRCS ${library_sources})
Set(LINKDEF ${CMAKE_SOURCE_DIR}/genfit/genfitLinkDef.h)
Set(LIBRARY_NAME genfit)
Set(DEPENDENCIES Core Geom Matrix Eve Gui Physics MathCore EG)

GENERATE_LIBRARY()

