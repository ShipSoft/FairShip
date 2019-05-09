# Create a library called "libmillepede" which includes the source files given in
# the array .
# The extension is already found.  Any number of sources could be listed here.

# Set the build type. Possibilities are None, Debug, Release,
# RelWithDebInfo and MinSizeRel
SET(CMAKE_BUILD_TYPE Release)

Set(SRCS Mille.cc)
Set(HEADERS Mille.h)
Set(LIBRARY_NAME millepede)

GENERATE_LIBRARY()