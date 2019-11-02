# installation on blank Ubuntu 18.04 LTS:
# FROM ubuntu:18.04
sudo apt-get update 
sudo apt-get install python3-dev python3-pip make patch sed git-all gedit environment-modules \
   libx11-dev libxpm-dev libxext-dev ncurses-dev libxml2-dev libxft-dev \
   libxmu-dev  ncurses-dev  curl bzip2  libbz2-dev gzip unzip tar gfortran libkrb5-dev \
    wget automake autoconf libtool bison  flex byacc libgif-dev libjpeg-dev libtiff5-dev\
   libexpat1-dev libcurl4-openssl-dev libssl-dev libbz2-dev libbz2-dev libglu1-mesa libglu1-mesa-dev\
   autopoint texinfo gettext libtool libtool-bin pkg-config python-tk cmake linuxbrew-wrapper 

sudo pip3 install --upgrade pip
sudo pip3 install matplotlib numpy scipy certifi ipython ipywidgets ipykernel notebook metakernel pyyaml sklearn

# sudo apt-get krb5-user
# for kinit: cp from lxplus /etc/krb5.conf

# mkdir SHiPBuild
# cd SHiPBuild
# git clone https://github.com/ShipSoft/FairShip.git
# FairShip/aliBuild.sh
