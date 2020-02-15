# Using gcc from release
# found package sqlite-87521
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package wheel-08d81
# found package Python-806f9
# found package setuptools-0f487
# found package Python-806f9
# found package setuptools-0f487
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export WHEEL__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt";
export PIP__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package pickleshare-08af8
# found package Python-806f9
# found package sqlite-87521
# found package pathlib2-2788d
# found package Python-806f9
# found package six-079c0
# found package Python-806f9
# found package setuptools-0f487
# found package Python-806f9
# found package setuptools-0f487
# found package setuptools-0f487
# found package setuptools-0f487
# found package pip-6bb79
# found package Python-806f9
# found package wheel-08d81
# found package Python-806f9
# found package setuptools-0f487
# found package setuptools-0f487
# found package Python-806f9
# found package traitlets-83daa
# found package Python-806f9
# found package setuptools-0f487
# found package ipython_genutils-2f4f9
# found package Python-806f9
# found package setuptools-0f487
# found package six-079c0
# found package backports-d1698
# found package Python-806f9
# found package xz-7112e
# found package setuptools-0f487
# found package pip-6bb79
# found package pygments-6f09f
# found package Python-806f9
# found package setuptools-0f487
# found package prompt_toolkit-bbda8
# found package Python-806f9
# found package wcwidth-1ccd9
# found package Python-806f9
# found package setuptools-0f487
# found package six-079c0
# found package setuptools-0f487
# found package pexpect-7ba8a
# found package Python-806f9
# found package setuptools-0f487
# found package simplegeneric-e8c01
# found package Python-806f9
# found package setuptools-0f487
# found package ptyprocess-b073d
# found package Python-806f9
# found package setuptools-0f487
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython/5.0.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython/5.0.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython/5.0.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pickleshare/0.7.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pickleshare/0.7.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pathlib2/2.1.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pathlib2/2.1.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export SIX__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt";
export PATHLIB2__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pathlib2/2.1.0/x86_64-slc6-gcc62-opt";
export PICKLESHARE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pickleshare/0.7.2/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export WHEEL__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt";
export PIP__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/traitlets/4.2.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/traitlets/4.2.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export TRAITLETS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/traitlets/4.2.2/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython_genutils/0.1.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython_genutils/0.1.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export IPYTHON_GENUTILS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython_genutils/0.1.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/backports/1.0.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/backports/1.0.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export BACKPORTS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/backports/1.0.0/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pygments/2.0.2/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pygments/2.0.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pygments/2.0.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PYGMENTS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pygments/2.0.2/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/prompt_toolkit/1.0.3/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/prompt_toolkit/1.0.3/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wcwidth/0.1.7/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wcwidth/0.1.7/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export WCWIDTH__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wcwidth/0.1.7/x86_64-slc6-gcc62-opt";
export PROMPT_TOOLKIT__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/prompt_toolkit/1.0.3/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pexpect/4.2.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pexpect/4.2.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PEXPECT__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pexpect/4.2.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/simplegeneric/0.8.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/simplegeneric/0.8.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SIMPLEGENERIC__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/simplegeneric/0.8.1/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ptyprocess/0.5.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ptyprocess/0.5.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PTYPROCESS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ptyprocess/0.5.1/x86_64-slc6-gcc62-opt";
export IPYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython/5.0.0/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package setuptools-0f487
# found package Python-806f9
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export NUMPY__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package numpy-8b1f8
# found package Python-806f9
# found package setuptools-0f487
# found package Python-806f9
# found package blas-e1974
# found package setuptools-0f487
# found package lapack-779be
# found package blas-e1974
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/scipy/0.15.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/scipy/0.15.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export NUMPY__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/blas/20110419/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export BLAS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/blas/20110419/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/lapack/3.5.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export LAPACK__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/lapack/3.5.0/x86_64-slc6-gcc62-opt";
export SCIPY__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/scipy/0.15.1/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package messaging-ff222
# found package Python-806f9
# found package sqlite-87521
# found package setuptools-0f487
# found package Python-806f9
# found package distribute-4f97f
# found package Python-806f9
# found package setuptools-0f487
# found package setuptools-0f487
# found package mock-bdfc3
# found package Python-806f9
# found package setuptools-0f487
# found package Python-806f9
# found package python_dateutil-8cb24
# found package Python-806f9
# found package six-079c0
# found package Python-806f9
# found package setuptools-0f487
# found package setuptools-0f487
# found package six-079c0
# found package nose-a009e
# found package Python-806f9
# found package numpy-8b1f8
# found package Python-806f9
# found package setuptools-0f487
# found package certifi-530c8
# found package Python-806f9
# found package setuptools-0f487
# found package pytz-d9478
# found package Python-806f9
# found package pyparsing-3b383
# found package Python-806f9
# found package setuptools-0f487
# found package tornado-9e71d
# found package Python-806f9
# found package backports-d1698
# found package Python-806f9
# found package xz-7112e
# found package setuptools-0f487
# found package pip-6bb79
# found package Python-806f9
# found package wheel-08d81
# found package Python-806f9
# found package setuptools-0f487
# found package setuptools-0f487
# found package certifi-530c8
# found package setuptools-0f487
# found package cycler-84f39
# found package Python-806f9
# found package six-079c0
# found package setuptools-0f487
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/matplotlib/1.5.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/matplotlib/1.5.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/matplotlib/1.5.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/messaging/1.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/messaging/1.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export MESSAGING__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/messaging/1.0/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/distribute/0.6.49/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/distribute/0.6.49/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/distribute/0.6.49/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export DISTRIBUTE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/distribute/0.6.49/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/mock/0.8.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/mock/0.8.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export MOCK__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/mock/0.8.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/python_dateutil/2.4.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/python_dateutil/2.4.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SIX__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt";
export PYTHON_DATEUTIL__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/python_dateutil/2.4.0/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/nose/1.1.2/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/nose/1.1.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/nose/1.1.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export NOSE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/nose/1.1.2/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export NUMPY__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/certifi/14.05.14/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/certifi/14.05.14/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export CERTIFI__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/certifi/14.05.14/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pytz/2015.4/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pytz/2015.4/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PYTZ__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pytz/2015.4/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pyparsing/2.1.8/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pyparsing/2.1.8/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PYPARSING__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pyparsing/2.1.8/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/tornado/4.0.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/tornado/4.0.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/backports/1.0.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/backports/1.0.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export WHEEL__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt";
export PIP__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt";
export BACKPORTS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/backports/1.0.0/x86_64-slc6-gcc62-opt";
export TORNADO__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/tornado/4.0.2/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/cycler/0.10.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/cycler/0.10.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export CYCLER__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/cycler/0.10.0/x86_64-slc6-gcc62-opt";
export MATPLOTLIB__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/matplotlib/1.5.1/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package MarkupSafe-a9096
# found package Python-806f9
# found package setuptools-0f487
# found package Python-806f9
# found package setuptools-0f487
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Jinja2/2.7.3/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Jinja2/2.7.3/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/MarkupSafe/0.23/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/MarkupSafe/0.23/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export MARKUPSAFE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/MarkupSafe/0.23/x86_64-slc6-gcc62-opt";
export JINJA2__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Jinja2/2.7.3/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package setuptools-0f487
# found package Python-806f9
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/notebook/4.2.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/notebook/4.2.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/notebook/4.2.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export NOTEBOOK__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/notebook/4.2.1/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package numpy-8b1f8
# found package Python-806f9
# found package setuptools-0f487
# found package Python-806f9
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numexpr/2.4.3/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numexpr/2.4.3/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numexpr/2.4.3/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export NUMPY__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt";
export NUMEXPR__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numexpr/2.4.3/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package setuptools-0f487
# found package Python-806f9
# found package ipython-1c824
# found package pickleshare-08af8
# found package Python-806f9
# found package pathlib2-2788d
# found package Python-806f9
# found package six-079c0
# found package Python-806f9
# found package setuptools-0f487
# found package setuptools-0f487
# found package setuptools-0f487
# found package setuptools-0f487
# found package pip-6bb79
# found package Python-806f9
# found package wheel-08d81
# found package Python-806f9
# found package setuptools-0f487
# found package setuptools-0f487
# found package Python-806f9
# found package traitlets-83daa
# found package Python-806f9
# found package setuptools-0f487
# found package ipython_genutils-2f4f9
# found package Python-806f9
# found package setuptools-0f487
# found package six-079c0
# found package backports-d1698
# found package Python-806f9
# found package xz-7112e
# found package setuptools-0f487
# found package pip-6bb79
# found package pygments-6f09f
# found package Python-806f9
# found package setuptools-0f487
# found package prompt_toolkit-bbda8
# found package Python-806f9
# found package wcwidth-1ccd9
# found package Python-806f9
# found package setuptools-0f487
# found package six-079c0
# found package setuptools-0f487
# found package pexpect-7ba8a
# found package Python-806f9
# found package setuptools-0f487
# found package simplegeneric-e8c01
# found package Python-806f9
# found package setuptools-0f487
# found package ptyprocess-b073d
# found package Python-806f9
# found package setuptools-0f487
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/metakernel/0.13.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/metakernel/0.13.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython/5.0.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython/5.0.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython/5.0.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pickleshare/0.7.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pickleshare/0.7.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pathlib2/2.1.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pathlib2/2.1.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SIX__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt";
export PATHLIB2__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pathlib2/2.1.0/x86_64-slc6-gcc62-opt";
export PICKLESHARE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pickleshare/0.7.2/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export WHEEL__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt";
export PIP__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/traitlets/4.2.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/traitlets/4.2.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export TRAITLETS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/traitlets/4.2.2/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython_genutils/0.1.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython_genutils/0.1.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export IPYTHON_GENUTILS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython_genutils/0.1.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/backports/1.0.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/backports/1.0.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export BACKPORTS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/backports/1.0.0/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pygments/2.0.2/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pygments/2.0.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pygments/2.0.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PYGMENTS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pygments/2.0.2/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/prompt_toolkit/1.0.3/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/prompt_toolkit/1.0.3/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wcwidth/0.1.7/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wcwidth/0.1.7/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export WCWIDTH__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wcwidth/0.1.7/x86_64-slc6-gcc62-opt";
export PROMPT_TOOLKIT__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/prompt_toolkit/1.0.3/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pexpect/4.2.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pexpect/4.2.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PEXPECT__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pexpect/4.2.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/simplegeneric/0.8.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/simplegeneric/0.8.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SIMPLEGENERIC__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/simplegeneric/0.8.1/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ptyprocess/0.5.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ptyprocess/0.5.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PTYPROCESS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ptyprocess/0.5.1/x86_64-slc6-gcc62-opt";
export IPYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython/5.0.0/x86_64-slc6-gcc62-opt";
export METAKERNEL__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/metakernel/0.13.1/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package setuptools-0f487
# found package Python-806f9
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pyyaml/3.11/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pyyaml/3.11/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export PYYAML__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pyyaml/3.11/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package cython-1fb03
# found package Python-806f9
# found package sqlite-87521
# found package setuptools-0f487
# found package Python-806f9
# found package Python-806f9
# found package python_dateutil-8cb24
# found package Python-806f9
# found package six-079c0
# found package Python-806f9
# found package setuptools-0f487
# found package setuptools-0f487
# found package numpy-8b1f8
# found package Python-806f9
# found package setuptools-0f487
# found package pytz-d9478
# found package Python-806f9
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pandas/0.19.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pandas/0.19.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pandas/0.19.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/cython/0.23.4/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/cython/0.23.4/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/cython/0.23.4/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export CYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/cython/0.23.4/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/python_dateutil/2.4.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/python_dateutil/2.4.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SIX__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt";
export PYTHON_DATEUTIL__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/python_dateutil/2.4.0/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export NUMPY__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pytz/2015.4/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pytz/2015.4/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PYTZ__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pytz/2015.4/x86_64-slc6-gcc62-opt";
export PANDAS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pandas/0.19.0/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package numpy-8b1f8
# found package Python-806f9
# found package setuptools-0f487
# found package Python-806f9
# found package scipy-afc78
# found package Python-806f9
# found package numpy-8b1f8
# found package blas-e1974
# found package setuptools-0f487
# found package lapack-779be
# found package blas-e1974
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/scikitlearn/0.17.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/scikitlearn/0.17.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export NUMPY__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/numpy/1.11.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/scipy/0.15.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/scipy/0.15.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/blas/20110419/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export BLAS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/blas/20110419/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/lapack/3.5.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export LAPACK__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/lapack/3.5.0/x86_64-slc6-gcc62-opt";
export SCIPY__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/scipy/0.15.1/x86_64-slc6-gcc62-opt";
export SCIKITLEARN__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/scikitlearn/0.17.1/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Boost/1.62.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export BOOST__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Boost/1.62.0/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Boost/1.62.0/x86_64-slc6-gcc62-opt"
export CPLUS_INCLUDE_PATH=${BOOST__HOME}/include:$CPLUS_INCLUDE_PATH
export C_INCLUDE_PATH=${BOOST__HOME}/include:$C_INCLUDE_PATH
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Boost/1.62.0/x86_64-slc6-gcc62-opt
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package setuptools-0f487
# found package Python-806f9
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/mock/0.8.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/mock/0.8.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export MOCK__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/mock/0.8.0/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package setuptools-0f487
# found package Python-806f9
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/certifi/14.05.14/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/certifi/14.05.14/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export CERTIFI__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/certifi/14.05.14/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package setuptools-0f487
# found package Python-806f9
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipywidgets/5.2.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipywidgets/5.2.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export IPYWIDGETS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipywidgets/5.2.2/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package setuptools-0f487
# found package Python-806f9
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipykernel/4.3.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipykernel/4.3.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export IPYKERNEL__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipykernel/4.3.1/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package Python-806f9
# found package sqlite-87521
# found package setuptools-0f487
# found package Python-806f9
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/decorator/4.0.9/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/decorator/4.0.9/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export DECORATOR__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/decorator/4.0.9/x86_64-slc6-gcc62-opt";
# Using gcc from release
# found package jupyter_client-3245c
# found package Python-806f9
# found package sqlite-87521
# found package setuptools-0f487
# found package Python-806f9
# found package Python-806f9
# found package ipywidgets-73abf
# found package Python-806f9
# found package setuptools-0f487
# found package pyzmq-1d6a7
# found package Python-806f9
# found package zeromq-e7e57
# found package cython-1fb03
# found package Python-806f9
# found package setuptools-0f487
# found package certifi-530c8
# found package Python-806f9
# found package setuptools-0f487
# found package jupyter_core-d8636
# found package Python-806f9
# found package setuptools-0f487
# found package widgetsnbextension-3afad
# found package tornado-9e71d
# found package Python-806f9
# found package backports-d1698
# found package Python-806f9
# found package xz-7112e
# found package setuptools-0f487
# found package pip-6bb79
# found package Python-806f9
# found package wheel-08d81
# found package Python-806f9
# found package setuptools-0f487
# found package setuptools-0f487
# found package certifi-530c8
# found package setuptools-0f487
# found package ipython_genutils-2f4f9
# found package Python-806f9
# found package setuptools-0f487
# found package setuptools-0f487
# found package Python-806f9
# found package traitlets-83daa
# found package Python-806f9
# found package setuptools-0f487
# found package decorator-6f033
# found package Python-806f9
# found package setuptools-0f487
# found package jupyter_core-d8636
# found package notebook-9f147
# found package Python-806f9
# found package setuptools-0f487
# found package tornado-9e71d
# found package pygments-6f09f
# found package Python-806f9
# found package setuptools-0f487
# found package jupyter_console-a93b0
# found package Python-806f9
# found package setuptools-0f487
# found package metakernel-ad241
# found package Python-806f9
# found package setuptools-0f487
# found package ipython-1c824
# found package pickleshare-08af8
# found package Python-806f9
# found package pathlib2-2788d
# found package Python-806f9
# found package six-079c0
# found package Python-806f9
# found package setuptools-0f487
# found package setuptools-0f487
# found package setuptools-0f487
# found package setuptools-0f487
# found package pip-6bb79
# found package Python-806f9
# found package traitlets-83daa
# found package ipython_genutils-2f4f9
# found package six-079c0
# found package backports-d1698
# found package pygments-6f09f
# found package prompt_toolkit-bbda8
# found package Python-806f9
# found package wcwidth-1ccd9
# found package Python-806f9
# found package setuptools-0f487
# found package six-079c0
# found package setuptools-0f487
# found package pexpect-7ba8a
# found package Python-806f9
# found package setuptools-0f487
# found package simplegeneric-e8c01
# found package Python-806f9
# found package setuptools-0f487
# found package ptyprocess-b073d
# found package Python-806f9
# found package setuptools-0f487
# found package MarkupSafe-a9096
# found package Python-806f9
# found package setuptools-0f487
# found package ipython-1c824
# found package jsonschema-32c58
# found package Python-806f9
# found package setuptools-0f487
# found package nbconvert-4aebb
# found package Python-806f9
# found package setuptools-0f487
# found package mistune-dc4e4
# found package Python-806f9
# found package setuptools-0f487
# found package ipykernel-8892e
# found package Python-806f9
# found package setuptools-0f487
# found package notebook-9f147
# found package terminado-49368
# found package Python-806f9
# found package tornado-9e71d
# found package setuptools-0f487
# found package entrypoints-e40bf
# found package Python-806f9
# found package configparser-355b9
# found package Python-806f9
# found package setuptools-0f487
# found package pip-6bb79
# found package setuptools-0f487
# found package Jinja2-69f09
# found package Python-806f9
# found package MarkupSafe-a9096
# found package setuptools-0f487
# found package qtconsole-2f248
# found package Python-806f9
# found package setuptools-0f487
# found package nbformat-cb646
# found package Python-806f9
# found package setuptools-0f487
source /cvmfs/sft.cern.ch/lcg/releases/LCG_87/gcc/6.2.0/x86_64-slc6/setup.sh;
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter/1.0.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter/1.0.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter_client/4.3.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter_client/4.3.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter_client/4.3.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export SQLITE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/sqlite/3110100/x86_64-slc6-gcc62-opt";
export PYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt";
cd "/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt"
export PYTHONHOME="${PYTHON__HOME}"
export PYTHONVERSION=`python -c "from __future__ import print_function; import sys; print ('%d.%d' % (sys.version_info.major, sys.version_info.minor))"`
cd - 1>/dev/null # from /cvmfs/sft.cern.ch/lcg/releases/LCG_87/Python/2.7.10/x86_64-slc6-gcc62-opt
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SETUPTOOLS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/setuptools/20.1.1/x86_64-slc6-gcc62-opt";
export JUPYTER_CLIENT__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter_client/4.3.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipywidgets/5.2.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipywidgets/5.2.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export IPYWIDGETS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipywidgets/5.2.2/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pyzmq/14.5.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pyzmq/14.5.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/zeromq/4.1.4/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/zeromq/4.1.4/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PKG_CONFIG_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/zeromq/4.1.4/x86_64-slc6-gcc62-opt/lib/pkgconfig:$PKG_CONFIG_PATH";
export ZEROMQ__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/zeromq/4.1.4/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/cython/0.23.4/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/cython/0.23.4/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/cython/0.23.4/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export CYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/cython/0.23.4/x86_64-slc6-gcc62-opt";
export PYZMQ__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pyzmq/14.5.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/certifi/14.05.14/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/certifi/14.05.14/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export CERTIFI__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/certifi/14.05.14/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter_core/4.2.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter_core/4.2.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter_core/4.2.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export JUPYTER_CORE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter_core/4.2.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/widgetsnbextension/1.2.6/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/widgetsnbextension/1.2.6/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/tornado/4.0.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/tornado/4.0.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/backports/1.0.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/backports/1.0.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export WHEEL__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wheel/0.29.0/x86_64-slc6-gcc62-opt";
export PIP__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pip/8.1.2/x86_64-slc6-gcc62-opt";
export BACKPORTS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/backports/1.0.0/x86_64-slc6-gcc62-opt";
export TORNADO__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/tornado/4.0.2/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython_genutils/0.1.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython_genutils/0.1.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export IPYTHON_GENUTILS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython_genutils/0.1.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/traitlets/4.2.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/traitlets/4.2.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export TRAITLETS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/traitlets/4.2.2/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/decorator/4.0.9/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/decorator/4.0.9/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export DECORATOR__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/decorator/4.0.9/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/notebook/4.2.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/notebook/4.2.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/notebook/4.2.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export NOTEBOOK__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/notebook/4.2.1/x86_64-slc6-gcc62-opt";
export WIDGETSNBEXTENSION__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/widgetsnbextension/1.2.6/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pygments/2.0.2/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pygments/2.0.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pygments/2.0.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PYGMENTS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pygments/2.0.2/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter_console/5.0.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter_console/5.0.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter_console/5.0.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export JUPYTER_CONSOLE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter_console/5.0.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/metakernel/0.13.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/metakernel/0.13.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython/5.0.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython/5.0.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython/5.0.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pickleshare/0.7.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pickleshare/0.7.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pathlib2/2.1.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pathlib2/2.1.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SIX__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/six/1.9.0/x86_64-slc6-gcc62-opt";
export PATHLIB2__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pathlib2/2.1.0/x86_64-slc6-gcc62-opt";
export PICKLESHARE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pickleshare/0.7.2/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/prompt_toolkit/1.0.3/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/prompt_toolkit/1.0.3/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wcwidth/0.1.7/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wcwidth/0.1.7/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export WCWIDTH__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/wcwidth/0.1.7/x86_64-slc6-gcc62-opt";
export PROMPT_TOOLKIT__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/prompt_toolkit/1.0.3/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pexpect/4.2.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pexpect/4.2.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PEXPECT__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/pexpect/4.2.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/simplegeneric/0.8.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/simplegeneric/0.8.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export SIMPLEGENERIC__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/simplegeneric/0.8.1/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ptyprocess/0.5.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ptyprocess/0.5.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export PTYPROCESS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ptyprocess/0.5.1/x86_64-slc6-gcc62-opt";
export IPYTHON__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipython/5.0.0/x86_64-slc6-gcc62-opt";
export METAKERNEL__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/metakernel/0.13.1/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/MarkupSafe/0.23/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/MarkupSafe/0.23/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export MARKUPSAFE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/MarkupSafe/0.23/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jsonschema/2.4.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jsonschema/2.4.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jsonschema/2.4.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export JSONSCHEMA__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jsonschema/2.4.0/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/nbconvert/4.2.0/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/nbconvert/4.2.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/nbconvert/4.2.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export NBCONVERT__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/nbconvert/4.2.0/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/mistune/0.5.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/mistune/0.5.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export MISTUNE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/mistune/0.5.1/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipykernel/4.3.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipykernel/4.3.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export IPYKERNEL__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/ipykernel/4.3.1/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/terminado/0.5/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/terminado/0.5/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export TERMINADO__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/terminado/0.5/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/entrypoints/0.2.2/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/entrypoints/0.2.2/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/configparser/3.5.0/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/configparser/3.5.0/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export CONFIGPARSER__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/configparser/3.5.0/x86_64-slc6-gcc62-opt";
export ENTRYPOINTS__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/entrypoints/0.2.2/x86_64-slc6-gcc62-opt";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Jinja2/2.7.3/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Jinja2/2.7.3/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export JINJA2__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/Jinja2/2.7.3/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/qtconsole/4.2.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/qtconsole/4.2.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/qtconsole/4.2.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export QTCONSOLE__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/qtconsole/4.2.1/x86_64-slc6-gcc62-opt";
export PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/nbformat/4.0.1/x86_64-slc6-gcc62-opt/bin:$PATH";
export LD_LIBRARY_PATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/nbformat/4.0.1/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH";
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/nbformat/4.0.1/x86_64-slc6-gcc62-opt/lib/python2.7/site-packages:$PYTHONPATH";
export NBFORMAT__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/nbformat/4.0.1/x86_64-slc6-gcc62-opt";
export JUPYTER__HOME="/cvmfs/sft.cern.ch/lcg/releases/LCG_87/jupyter/1.0.0/x86_64-slc6-gcc62-opt";
