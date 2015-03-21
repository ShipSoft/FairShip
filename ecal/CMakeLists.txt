# Create a library called "libecal" which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
#put here all directories where header files are located
${CMAKE_SOURCE_DIR}/shipdata
${CMAKE_SOURCE_DIR}/ecal
)

include_directories( ${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}

) 

link_directories( ${LINK_DIRECTORIES})

set(SRCS
#Put here your sourcefiles
ecal.cxx
ecalContFact.cxx
ecalPoint.cxx
ecalLightMap.cxx
ecalCell.cxx
ecalCellMC.cxx
ecalModule.cxx
ecalInf.cxx
ecalStructure.cxx
ecalStructureFiller.cxx
ecalDigi.cxx
ecalPrepare.cxx
ecalAnalysisSimple.cxx
ecalAnalysisMaterial.cxx
ecalMaximum.cxx
ecalMaximumLocator.cxx
ecalCluster.cxx
ecalClusterFinder.cxx
ecalClusterCalibration.cxx
ecalDrawer.cxx
ecalReconstructed.cxx
ecalReco.cxx
ecalMatch.cxx
)

Set(LINKDEF ecalLinkDef.h)
Set(LIBRARY_NAME ecal)
Set(DEPENDENCIES
    Base ShipData
)

GENERATE_LIBRARY()
