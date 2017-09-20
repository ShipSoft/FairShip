#! /bin/bash
if [ $# -eq 0 ]
  then
# check if SHIPBUILD is set
    if [[ ! -v SHIPBUILD ]]; then
     echo "You need to parse the path to SHIPBUILD as argument or define environment variable SHIPBUILD"
     exit
    fi
else
  export SHIPBUILD=$1
fi
echo "use SHIPBUILD from $SHIPBUILD"

if [ -f config.sh ];
then
 rm config.sh
fi

$SHIPBUILD/alibuild/alienv -w $SHIPBUILD/sw printenv FairShip/latest > config.sh

sed -i 's/\/afs\/cern.ch\/user\/t\/truf\/scratch2\/SHiPBuild/$SHIPBUILD/g' config.sh
source config.sh  # makes global FairShip environment

if [[ $HOSTNAME == *lxplus* ]]
then
  echo "Setup lcg environment"
  source genenv.sh
fi

temp=$(cat $SHIPBUILD/shipdist/defaults-fairship.sh | grep CXXFLAGS)
temx=$( cut -d ':' -f 2 <<< "$temp" )
CXXFLAGS=${temx//'"'}
temp=$(cat $SHIPBUILD/shipdist/defaults-fairship.sh | grep CMAKE_BUILD_TYPE )
temx=$( cut -d ':' -f 2 <<< "$temp" )
CMAKE_BUILD_TYPE=${temx//'"'}

if [ ! -d ../FairShipRun ];
then
 mkdir ../FairShipRun
fi
cd ../FairShipRun

INSTALLROOT=$PWD
SOURCEDIR="../FairShip"  
export FAIRROOTPATH=$FAIRROOT_ROOT
export ROOT_ROOT=$ROOTSYS 

cmake $SOURCEDIR                                                 \
      -DFAIRBASE="$FAIRROOT_ROOT/share/fairbase"                 \
      -DFAIRROOTPATH="$FAIRROOT_ROOT"                            \
      -DCMAKE_CXX_FLAGS="$CXXFLAGS"                              \
      -DCMAKE_BUILD_TYPE="$CMAKE_BUILD_TYPE"                     \
      -DROOTSYS=$ROOTSYS                                         \
      -DROOT_CONFIG_SEARCHPATH=$ROOT_ROOT/bin                    \
      -DROOT_DIR=$ROOT_ROOT                                      \
      -DHEPMC_DIR=$HEPMC_ROOT                                    \
      -DHEPMC_INCLUDE_DIR=$HEPMC_ROOT/include/HepMC              \
      -DEVTGENPATH=$EVTGEN_ROOT                                  \
      -DEVTGEN_INCLUDE_DIR=$EVTGEN_ROOT/include                  \
      -DEVTGEN_LIBRARY_DIR=$EVTGEN_ROOT/lib                      \
      -DPythia6_LIBRARY_DIR=$PYTHIA6_ROOT/lib                    \
      -DPYTHIA8_DIR=$PYTHIA_ROOT                                 \
      -DPYTHIA8_INCLUDE_DIR=$PYTHIA_ROOT/include                 \
      -DGEANT3_PATH=$GEANT3_ROOT                                 \
      -DGEANT3_LIB=$GEANT3_ROOT/lib                              \
      -DGEANT4_ROOT=$GEANT4_ROOT                                 \
      -DGEANT4_VMC_ROOT=$GEANT4_VMC_ROOT                         \
      -DVGM_ROOT=$VGM_ROOT                                       \
      -DGENIE_ROOT=$GENIE_ROOT                                   \
      -DLHAPDF5_ROOT="$LHAPDF5_ROOT"                             \
      ${CMAKE_VERBOSE_MAKEFILE:+-DCMAKE_VERBOSE_MAKEFILE=ON}     \
      ${BOOST_ROOT:+-DBOOST_ROOT=$BOOST_ROOT}                    \
      ${BOOST_ROOT:+-DBOOST_INCLUDEDIR=$BOOST_ROOT/include}      \
      ${BOOST_ROOT:+-DBOOST_LIBRARYDIR=$BOOST_ROOT/lib}          \
      ${BOOST_ROOT:+-DBoost_NO_SYSTEM=TRUE}                      \
      ${GSL_ROOT:+-DGSL_DIR=$GSL_ROOT}                           \
      -DCMAKE_INSTALL_PREFIX=$INSTALLROOT
make
# make test does not exist yet
make install

cd -
