# Create a library called "libmuon" which includes the source files given in the
# array . The extension is already found.  Any number of sources could be listed
# here.

set(INCLUDE_DIRECTORIES ${CMAKE_CURRENT_SOURCE_DIR} ${genfit2_INCDIR})

include_directories(${INCLUDE_DIRECTORIES} ${CMAKE_BINARY_DIR}/include)
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES ${ROOT_LIBRARY_DIR} ${FAIRROOT_LIBRARY_DIR}
                     ${genfit2_LIBDIR})

link_directories(${LINK_DIRECTORIES})

set(SRCS # Put here your sourcefiles
    pid.cxx)

set(LINKDEF LinkDef.h)
set(LIBRARY_NAME pid)
set(DEPENDENCIES Base ShipData)

generate_library()
