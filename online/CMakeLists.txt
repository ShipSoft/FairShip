set(INCLUDE_DIRECTORIES
    ${BASE_INCLUDE_DIRECTORIES}
    ${CMAKE_SOURCE_DIR}/online
    ${CMAKE_SOURCE_DIR}/shipdata
    ${CMAKE_SOURCE_DIR}/charmdet
)

Set(SYSTEM_INCLUDE_DIRECTORIES
    ${SYSTEM_INCLUDE_DIRECTORIES}
)

include_directories(${INCLUDE_DIRECTORIES})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})


set(LINK_DIRECTORIES
    ${ROOT_LIBRARY_DIR}
    ${FAIRROOT_LIBRARY_DIR}
) 

link_directories(${LINK_DIRECTORIES})

Set(SRCS
    ShipTdcSource.cxx
    ShipUnpack.cxx
    DriftTubeUnpack.cxx
    RPCUnpack.cxx
    ScalerUnpack.cxx
    PixelUnpack.cxx
    SciFiUnpack.cxx
    DummyUnpack.cxx
)

CHANGE_FILE_EXTENSION(*.cxx *.h HEADERS "${SRCS}")

Set(LINKDEF OnlineLinkDef.h)
Set(LIBRARY_NAME Online)

Set(DEPENDENCIES
    Base # MbsAPI
)

GENERATE_LIBRARY()
