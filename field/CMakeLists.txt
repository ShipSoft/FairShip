# Create a library called "libField” which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
${CMAKE_SOURCE_DIR}/field 
${ROOT_INCLUDE_DIR}
${GEANT4VMC_INCLUDE_DIR}
${GEANT4_INCLUDE_DIR}

)

include_directories( ${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}
${GEANT4VMC_LIBRARY_DIR}
${GEANT4_LIBRARY_DIR}

)
 
link_directories( ${LINK_DIRECTORIES})

set(SRCS
ShipConstField.cxx   
ShipFieldCreator.cxx 
ShipFieldPar.cxx
ShipBellField.cxx
ShipBFieldMap.cxx
ShipCompField.cxx
ShipFieldMaker.cxx
ShipGoliathField.cxx
)

set(LINKDEF FieldLinkDef.h)
Set(LIBRARY_NAME ShipField)
Set(DEPENDENCIES
    Base 
)

GENERATE_LIBRARY()

