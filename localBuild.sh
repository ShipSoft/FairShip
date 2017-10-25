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

if [ $# -eq 0 ]
  then
    architecture="$(python/detectArch)"
  else
    architecture=$1
fi

echo "Setting environment for ${architecture} for $SHIPBUILD"
echo "export SHIPBUILD=$SHIPBUILD" > config.sh
echo "SHIPBUILD=$SHIPBUILD" > config.sh

$SHIPBUILD/alibuild/alienv -a ${architecture} -w $SHIPBUILD/sw printenv FairShip/latest >> config.sh

P="$(python/tweakConfig)"

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
SOURCEDIR=$PWD

cd ../FairShipRun
INSTALLROOT=$PWD

export FAIRROOTPATH=$FAIRROOT_ROOT
export ROOT_ROOT=$ROOTSYS 

echo "DEBUG -DCMAKE_BINARY_DIR=$INSTALLROOT    $SOURCEDIR  "

cmake $SOURCEDIR                                                 \
      -DFAIRBASE=$FAIRROOT_ROOT/share/fairbase                 \
      -DFAIRROOTPATH=$FAIRROOT_ROOT                            \
      -DCMAKE_CXX_FLAGS="$CXXFLAGS"                              \
      -DCMAKE_BUILD_TYPE="$CMAKE_BUILD_TYPE"                     \
      -DROOTSYS=$ROOTSYS                                         \
      -DROOT_CONFIG_SEARCHPATH=$ROOT_ROOT/bin                    \
      -DROOT_DIR=$ROOT_ROOT                                      \
      -DHEPMC_DIR=$HEPMC_ROOT                                    \
      -DHEPMC_INCLUDE_DIR=$HEPMC_ROOT/include/HepMC              \
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
      ${CMAKE_VERBOSE_MAKEFILE:+-DCMAKE_VERBOSE_MAKEFILE=ON}     \
      ${BOOST_ROOT:+-DBOOST_ROOT=$BOOST_ROOT}                    \
      ${BOOST_ROOT:+-DBOOST_INCLUDEDIR=$BOOST_ROOT/include}      \
      ${BOOST_ROOT:+-DBOOST_LIBRARYDIR=$BOOST_ROOT/lib}          \
      -DCMAKE_BINARY_DIR=$INSTALLROOT                            \
      -DCMAKE_INSTALL_PREFIX=$INSTALLROOT
make
# make test does not exist yet

cp ../FairShip/config.sh  config.sh
echo "echo \"setup aliBuild environment\"" >> config.sh
echo "export SHIPBUILD=${SHIPBUILD}" >> config.sh
cat ../FairShip/lcgenv.sh >> config.sh
echo "echo \"setup lcg environment\"" >> config.sh
echo "export FAIRSHIP=$(pwd)/../FairShip" >> config.sh
echo "export FAIRSHIPRUN=$(pwd)" >> config.sh

echo "export LD_LIBRARY_PATH=\${LD_LIBRARY_PATH}:\${SHIPBUILD}/$architecture" >> config.sh
echo "export LD_LIBRARY_PATH=$INSTALLROOT/lib:\${LD_LIBRARY_PATH}" >> config.sh
# ugly fix 
echo "export ROOT_INCLUDE_PATH=\${ROOT_INCLUDE_PATH}:\${SHIPBUILD}/sw/$architecture/GEANT4/latest/include:/\${SHIPBUILD}/sw/$architecture/include/Geant4:\${SHIPBUILD}/sw/$architecture/pythia/latest/include:\${SHIPBUILD}/sw/$architecture/pythia/latest/include/Pythia8:\${SHIPBUILD}/sw/$architecture/GEANT4_VMC/latest/include/geant4vmc:\${SHIPBUILD}/sw/$architecture/GEANT4_VMC/latest/include" >> config.sh

chmod u+x config.sh
cd -

