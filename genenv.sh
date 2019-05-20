#! /bin/bash
# was needed to remove LHCb stuff from path
# export PATH=$(pwd):"/usr/sue/bin:/usr/lib64/qt-3.3/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/opt/puppetlabs/bin"

export distribution=$(lsb_release -is)
export LCGVERSION="LCG_87"
if [ $distribution=="ScientificCERNSLC" ]
then
     export GCCVERSION="x86_64-slc6-gcc62-opt"
     gcctag="x86_64-slc6"
else
     export GCCVERSION="x86_64-centos7-gcc62-opt"
     gcctag="x86_64-centos7"
fi

# Use cvmfs on lxplus
export lcgenv="/cvmfs/sft.cern.ch/lcg/releases/lcgenv/latest/lcgenv"
source "/cvmfs/sft.cern.ch/lcg/contrib/gcc/6.2/${GCCVERSION}/setup.sh"

if [ -f cc ];
then
 rm cc
fi
ln -s $(which gcc) cc

if [ -f "c++" ];
then
 rm "c++"
fi
ln -s $(which c++) "c++"

if [ -f "lcgenv.sh" ];
then
 rm "lcgenv.sh"
fi

$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} Python >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} pip >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} ipython >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} numpy >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} scipy >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} matplotlib >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} Jinja2 >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} notebook >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} numexpr >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} metakernel >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} PyYAML >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} pandas >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} scikitlearn >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} Boost >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} mock >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} certifi >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} ipywidgets >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} ipykernel >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} decorator >> lcgenv.sh
$lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/${LCGVERSION} ${GCCVERSION} jupyter >> lcgenv.sh
source lcgenv.sh
