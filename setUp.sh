
version="2020-2"

if [ x"$SHIP_CVMFS_SETUP" != x"" ] 
then
        if [ x"$SHIP_CVMFS_SETUP" == x"$version" ]
        then
                echo "WARNING!"
                echo "WARNING! Trying to setting up again the same environment."
        else
                echo "ERROR!"
                echo "ERROR! Trying to set up a new environment on top of an old one."
                echo "ERROR! This is not allowed, hance we will NOT set up the environment"
                echo "ERROR! The solution is to exit the current shell and open a new one"
                return
        fi
fi
SHIP_CVMFS_SETUP=$version


# the source script set the PYTHONPATH to something internal.
# let's store the current python path to avoid breaking anything.
CURRENT_PYTHON_PATH=$(python -c "from __future__ import print_function; import sys; print(':'.join(sys.path)[1:]);")
PYTHONPATH="$PYTHONPATH:$CURRENT_PYTHON_PATH"

# let's source the environment with all the variables
WORK_DIR=/cvmfs/ship.cern.ch/SHiP-2020/2019/August/12/sw/ source /cvmfs/ship.cern.ch/SHiP-2020/2019/August/12/sw/slc7_x86-64/FairShip/latest/etc/profile.d/init.sh

ROOT_INCLUDE_PATH="$ROOT_INCLUDE_PATH:/cvmfs/ship.cern.ch/SHiP-2020/2019/August/12/sw/SOURCES/FairRoot/May30-ship/bdc279b900/base/"
ROOT_INCLUDE_PATH="$ROOT_INCLUDE_PATH:/cvmfs/ship.cern.ch/SHiP-2020/2019/August/12/sw/slc7_x86-64/boost/v1.64.0-alice1-1/include/"

# add aliBuild to the path, so that we can use it without installing it on the user machine
# we add it to the end of the path, so that if a local installation of aliBuild is present we will use that one
PATH="$PATH:/cvmfs/ship.cern.ch/alibuild/bin"
PYTHONPATH="$PYTHONPATH:/cvmfs/ship.cern.ch/alibuild"

# set the standard ShipDist directory as well
SHIPDIST="/cvmfs/ship.cern.ch/SHiP-2020/2019/August/12/shipdist/"

# fixup for genie
PATH="$PATH:$GENIE_ROOT/genie/bin"
LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$GENIE_ROOT/genie/lib"
ROOT_INCLUDE_PATH="$ROOT_INCLUDE_PATH:$GENIE_ROOT/genie/inc"
LHAPATH="$LHAPDF5_ROOT/share/lhapdf"

# fix the graphics driver issue
export LIBGL_DRIVERS_PATH="/cvmfs/sft.cern.ch/lcg/contrib/mesa/18.0.5/x86_64-centos7/lib64/dri"

