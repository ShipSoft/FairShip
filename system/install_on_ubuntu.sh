# installation on blank Ubuntu 17.10: 
# FROM ubuntu:17.10
sudo apt-get update 
sudo apt-get install python-dev python-pip make patch sed git-all gedit environment-modules \
   libx11-dev libxpm-dev libxext-dev ncurses-dev libxml2-dev libxft-dev \
   libxmu-dev  ncurses-dev  curl bzip2  libbz2-dev gzip unzip tar gfortran libkrb5-dev \
    wget automake autoconf libtool bison  flex byacc libgif-dev libjpeg-dev libtiff5-dev\
   libexpat1-dev libcurl4-openssl-dev libssl-dev libbz2-dev libbz2-dev libglu1-mesa libglu1-mesa-dev\
   autopoint texinfo gettext libtool libtool-bin pkg-config python-tk cmake linuxbrew-wrapper 

sudo pip install --upgrade pip
sudo pip install matplotlib numpy scipy certifi ipython ipywidgets ipykernel notebook metakernel pyyaml

# sudo apt-get krb5-user
# for kinit: cp from lxplus /etc/krb5.conf

# mkdir SHiPBuild
# cd SHiPBuild
# git clone https://github.com/ShipSoft/FairShip.git
# FairShip/aliBuild.sh
