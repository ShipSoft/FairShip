# Create a library called "libShipGen" which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
${CMAKE_SOURCE_DIR}/shipgen
${CMAKE_SOURCE_DIR}/generators
${CMAKE_SOURCE_DIR}/shipdata
${CMAKE_SOURCE_DIR}/veto
${genfit2_INCDIR}
${TPYTHIA6_INCLUDE_DIR}
)

set(SYSTEM_INCLUDE_DIRECTORIES
${SYSTEM_INCLUDE_DIRECTORIES}
${PYTHIA8_INCLUDE_DIR}
${PYTHIA8_INCLUDE_DIR}/..
${HEPMC_INCLUDE_DIR}
${EVTGEN_INCLUDE_DIR}
${EVTGEN_INCLUDE_DIR}/..
)

include_directories(${INCLUDE_DIRECTORIES} ${VMC_INCLUDE_DIRS} ${FAIRROOT_INCLUDE_DIR})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

# Define PYTHIA_VERSION_INTEGER for older Pythia8 versions that don't have it
try_compile(HAS_PYTHIA_VERSION_INTEGER ${CMAKE_BINARY_DIR}/temp
    ${CMAKE_SOURCE_DIR}/cmake/test_pythia_version.cpp
    CMAKE_FLAGS "-DINCLUDE_DIRECTORIES=${PYTHIA8_INCLUDE_DIR}"
    OUTPUT_VARIABLE COMPILE_OUTPUT)

if(NOT HAS_PYTHIA_VERSION_INTEGER)
    if(PYTHIA8_VERSION)
        # Convert version string (e.g., "8.223") to integer (e.g., 8223)
        string(REPLACE "." "" PYTHIA8_VERSION_INTEGER ${PYTHIA8_VERSION})
        add_compile_definitions(PYTHIA_VERSION_INTEGER=${PYTHIA8_VERSION_INTEGER})
        message(STATUS "Defined PYTHIA_VERSION_INTEGER=${PYTHIA8_VERSION_INTEGER} for Pythia8 ${PYTHIA8_VERSION}")
    else()
        # Assume oldest supported version
        add_compile_definitions(PYTHIA_VERSION_INTEGER=8223)
        message(STATUS "Defined PYTHIA_VERSION_INTEGER=8223 for old Pythia8 version")
    endif()
else()
    message(STATUS "PYTHIA_VERSION_INTEGER already defined in Pythia8 headers")
endif()

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}
${PYTHIA8_LIBRARY_DIR}
${EVTGEN_LIBRARY_DIR}
${genfit2_LIBDIR}
${SIMPATH}/lib
)

link_directories(${LINK_DIRECTORIES})

set(SRCS
Pythia8Generator.cxx
Pythia6Generator.cxx
tPythia6Generator.cxx
HNLPythia8Generator.cxx
DPPythia8Generator.cxx
GenieGenerator.cxx
NtupleGenerator.cxx
MyGenerator.cxx
MuonBackGenerator.cxx
CosmicsGenerator.cxx
MuDISGenerator.cxx
FixedTargetGenerator.cxx
EvtCalcGenerator.cxx
TEvtGenDecayer.cxx
BeamSmearingUtils.cxx
)

set(LINKDEF GenLinkDef.h)
set(LIBRARY_NAME ShipGen)

set(DEPENDENCIES Base ShipData EvtGen EvtGenExternal
                 FairLogger::FairLogger)

GENERATE_LIBRARY()
