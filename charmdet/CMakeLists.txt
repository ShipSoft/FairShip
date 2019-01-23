# Create a library called "libnutaudet” which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

set(INCLUDE_DIRECTORIES
${BASE_INCLUDE_DIRECTORIES}
${CMAKE_SOURCE_DIR}/shipdata
${CMAKE_SOURCE_DIR}/charmdet
${CMAKE_SOURCE_DIR}/online
${CMAKE_SOURCE_DIR}/genfit/core/include
${ROOT_INCLUDE_DIR} 
)

include_directories( ${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES
${ROOT_LIBRARY_DIR}
${FAIRROOT_LIBRARY_DIR}
${GENFIT_LIBRARY_DIR}

)
 
link_directories( ${LINK_DIRECTORIES})

set(SRCS
Box.cxx
BoxPoint.cxx
BoxContFact.cxx
Spectrometer.cxx
SpectrometerPoint.cxx
MufluxSpectrometer.cxx
MufluxSpectrometerHit.cxx
MufluxSpectrometerPoint.cxx
MuonTagger.cxx
MuonTaggerPoint.cxx
MuonTaggerHit.cxx
Scintillator.cxx
ScintillatorPoint.cxx
ScintillatorHit.cxx
ShipPixelHit.cxx
ReProcessAbsorber.cxx
RPCTrack.cxx
)

Set(HEADERS )
Set(LINKDEF BoxLinkDef.h)
Set(LIBRARY_NAME charmdet)
Set(DEPENDENCIES Base ShipData GeoBase ParBase Geom Core genfit)

GENERATE_LIBRARY()
