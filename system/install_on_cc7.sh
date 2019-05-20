# installation on blank CC7: FROM cern/cc7-base:20171114
set -e
yum -y update
yum -y install which python-devel python-pip make patch sed git-all gedit environment-modules \
   libX11-devel libXft-devel libXpm-devel libXext-devel \
   libXmu-devel mesa-libGLU-devel mesa-libGL-devel ncurses-devel \
   curl bzip2 libbz2-dev gzip unzip tar expat-devel \
   libxml2-devel wget openssl-devel curl-devel  gcc gcc-c++ \
   automake autoconf libtool bison bzip2-devel flex byacc python2-pip
pip install --upgrade pip
pip install matplotlib numpy scipy certifi ipython ipywidgets ipykernel notebook metakernel pyyaml

# for cvmfs
# sudo yum install https://ecsft.cern.ch/dist/cvmfs/cvmfs-release/cvmfs-release-latest.noarch.rpm 
# sudo yum install cvmfs cvmfs-config-default
# sudo cvmfs_config setup
# put in /etc/cvmfs/default.local 
# CVMFS_QUOTA_LIMIT='164494'
# CVMFS_HTTP_PROXY='http://ca-proxy-meyrin.cern.ch:3128;http://ca-proxy.cern.ch:3128;http://ca01.cern.ch:3128|http://ca02.cern.ch:3128|http://ca03.cern.ch:3128|http://ca04.cern.ch:3128|http://ca05.cern.ch:3128|http://ca06.cern.ch:3128'
# CVMFS_CACHE_BASE='/pool/cvmfs'
# CVMFS_FORCE_SIGNING='yes'
# CVMFS_REPOSITORIES='geant4.cern.ch,ship.cern.ch,sft.cern.ch,'

# sudo mkdir -p /cvmfs/cms.cern.ch

# mkdir SHiPBuild
# cd SHiPBuild
# git clone https://github.com/ShipSoft/FairShip.git
# FairShip/aliBuild.sh
