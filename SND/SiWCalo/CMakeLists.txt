# Create a library called "SiWCalo" which includes the source files given in
# the array . The extension is already found.  Any number of sources could be
# listed here.

ship_add_library(NAME SiWCalo
  SOURCES SiWCalo.cxx SiWCaloPoint.cxx SiWCaloHit.cxx
  LINKDEF SiWCaloLinkDef.h
  EXTRA_DICT_HEADERS ${CMAKE_SOURCE_DIR}/Detector/Detector.h
  DEPENDENCIES Detector Base ShipData Detector GeoBase ParBase Geom Core FairLogger::FairLogger
)
