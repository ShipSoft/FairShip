#! /bin/bash
# check if SHIPBUILD is set
if [[ -z $SHIPBUILD ]]; then
     echo "SHIPBUILD not defined. probably should be export SHIPBUILD=/cvmfs/ship.cern.ch/SHiPBuild"
     exit
fi

if [ -f config.sh ];
then
 rm config.sh
fi

if [ $# -eq 0 ]
  then
    architecture="$(python/detectArch)"
  else
    architecture=$1
fi

echo "Setting environment for ${architecture} for $SHIPBUILD"
echo "SHIPBUILD=$SHIPBUILD" > config.sh

"$SHIPBUILD"/alibuild/alienv -a "${architecture}" -w "$SHIPBUILD"/sw printenv FairShip/latest CMake/latest >> config.sh

python/tweakConfig

source config.sh  # makes global FairShip environment

echo "Setup lcg environment"
source genenv.sh

temp=$(grep CXXFLAGS < "$SHIPBUILD"/shipdist/defaults-fairship.sh)
temx=$( cut -d ':' -f 2 <<< "$temp" )
CXXFLAGS=${temx//'"'}
temp=$(grep CMAKE_BUILD_TYPE < "$SHIPBUILD"/shipdist/defaults-fairship.sh)
temx=$( cut -d ':' -f 2 <<< "$temp" )
CMAKE_BUILD_TYPE=${temx//'"'}

SOURCEDIR=$PWD
INSTALLROOT="$SOURCEDIR/../FairShipRun"

if [ ! -d "$INSTALLROOT" ];
then
 mkdir "$INSTALLROOT" || exit 1
fi

cd "$INSTALLROOT" || exit 1

export FAIRROOTPATH=$FAIRROOT_ROOT
export ROOT_ROOT=$ROOTSYS 

echo "DEBUG -DCMAKE_BINARY_DIR=$INSTALLROOT    $SOURCEDIR  "

cmake "$SOURCEDIR"                                                 \
      -DFAIRBASE="$FAIRROOT_ROOT"/share/fairbase                 \
      -DFAIRROOTPATH="$FAIRROOT_ROOT"                            \
      -DCMAKE_CXX_FLAGS="$CXXFLAGS"                              \
      -DCMAKE_BUILD_TYPE="$CMAKE_BUILD_TYPE"                     \
      -DROOTSYS="$ROOTSYS"                                         \
      -DROOT_CONFIG_SEARCHPATH="$ROOT_ROOT"/bin                    \
      -DROOT_DIR="$ROOT_ROOT"                                      \
      -DHEPMC_DIR="$HEPMC_ROOT"                                    \
      -DHEPMC_INCLUDE_DIR="$HEPMC_ROOT"/include/HepMC              \
      -DEVTGEN_INCLUDE_DIR="$EVTGEN_ROOT"/include                  \
      -DEVTGEN_LIBRARY_DIR="$EVTGEN_ROOT"/lib                      \
      -DPythia6_LIBRARY_DIR="$PYTHIA6_ROOT"/lib                    \
      -DPYTHIA8_DIR="$PYTHIA_ROOT"                                 \
      -DPYTHIA8_INCLUDE_DIR="$PYTHIA_ROOT"/include                 \
      -DGEANT3_PATH="$GEANT3_ROOT"                                 \
      -DGEANT3_LIB="$GEANT3_ROOT"/lib                              \
      -DGEANT4_ROOT="$GEANT4_ROOT"                                 \
      -DGEANT4_VMC_ROOT="$GEANT4_VMC_ROOT"                         \
      -DVGM_ROOT="$VGM_ROOT"                                       \
      ${CMAKE_VERBOSE_MAKEFILE:+-DCMAKE_VERBOSE_MAKEFILE=ON}     \
      ${BOOST_ROOT:+-DBOOST_ROOT="$BOOST_ROOT"}                    \
      ${BOOST_ROOT:+-DBOOST_INCLUDEDIR="$BOOST_ROOT"/include}      \
      ${BOOST_ROOT:+-DBOOST_LIBRARYDIR="$BOOST_ROOT"/lib}          \
      -DCMAKE_BINARY_DIR="$INSTALLROOT"                            \
      -DCMAKE_INSTALL_PREFIX="$INSTALLROOT"
make

cp "$SOURCEDIR"/config.sh  config.sh
{
  echo "echo \"setup aliBuild environment\""
  echo "export SHIPBUILD=${SHIPBUILD}"
  cat "$SOURCEDIR"/lcgenv.sh
  echo "echo \"setup lcg environment\""
  echo "export FAIRSHIP=$SOURCEDIR"
  echo "export FAIRSHIPRUN=$INSTALLROOT"
  echo "export EOSSHIP=root://eospublic.cern.ch/"
  echo "export LD_LIBRARY_PATH=\${LD_LIBRARY_PATH}:\${SHIPBUILD}/$architecture"
  echo "export LD_LIBRARY_PATH=$INSTALLROOT/lib:\${LD_LIBRARY_PATH}"
  # ugly fix
  echo "export ROOT_INCLUDE_PATH=\${FAIRSHIP}/nutaudet:\${ROOT_INCLUDE_PATH}:\${GEANT4_ROOT}/include:\${PYTHIA_ROOT}/include:\${PYTHIA_ROOT}/include/Pythia8:\${GEANT4_VMC_ROOT}/include/geant4vmc:\${GEANT4_VMC_ROOT}/include:\${BOOST_ROOT}/include:\${SHIPBUILD}/sw/SOURCES/FairRoot/May30-ship/May30-ship/base"
} >> config.sh

chmod u+x config.sh
cd -

