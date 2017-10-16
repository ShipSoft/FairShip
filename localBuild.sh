#! /bin/bash
# check if SHIPBUILD is set
if [[ -z $SHIPBUILD ]]; then
     echo "SHIPBUILD not defined. probably should be export SHIPBUILD=/cvmfs/ship.cern.ch/ShipSoft/SHiPBuild"
     exit
fi

if [ -f config.sh ];
then
 rm config.sh
fi

architecture="$(python/detectArch)"

echo "Setting environment for ${architecture} for $SHIPBUILD"
$SHIPBUILD/alibuild/alienv -a ${architecture} -w $SHIPBUILD/sw printenv FairShip/latest > config.sh

A=$SHIPBUILD/sw/$architecture/FairShip/master-1
sed -i "s,$A,$(pwd),g" config.sh
sed -i 's!/afs/cern.ch/user/t/truf/scratch2/SHiPBuild!$SHIPBUILD!g' config.sh

source config.sh  # makes global FairShip environment

echo "Setup lcg environment"
source genenv.sh

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

echo "export SHIPBUILD=${SHIPBUILD}" > config.sh
echo "echo \"setup aliBuild environment\"" >> config.sh
cat ../FairShip/config.sh >> config.sh
echo "echo \"setup lcg environment\"" >> config.sh
cat ../FairShip/lcgenv.sh >> config.sh
echo "export FAIRSHIP=$(pwd)/../FairShip" >> config.sh
echo "export FAIRSHIPRUN=$(pwd)" >> config.sh
echo "export SHIPBUILD=$SHIPBUILD" >> config.sh

echo "export LD_LIBRARY_PATH=\${LD_LIBRARY_PATH}:\${SHIPBUILD}/$architecture" >> config.sh
# ugly fix 
echo "export ROOT_INCLUDE_PATH=\${ROOT_INCLUDE_PATH}:\${SHIPBUILD}/sw/$architecture/GEANT4/latest/include:/\${SHIPBUILD}/sw/$architecture/include/Geant4:\${SHIPBUILD}/sw/$architecture/pythia/latest/include:\${SHIPBUILD}/sw/$architecture/pythia/latest/include/Pythia8" >> config.sh

chmod u+x config.sh
cd -
