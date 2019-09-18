#!/bin/python

# Python script to convert B field maps from MISIS text files into 
# ROOT files for FairShip. Text files are assumed to contain two
# preamble lines giving the binning details and variable names, followed 
# by data lines x y z Bx By Bz, where the co-ordinates are assumed to
# be in ascending z, y and x, in that order. Need distances in cm

from __future__ import print_function
import ROOT

# Struct for the ROOT file TTree data: coord range and field info

ROOT.gROOT.ProcessLine(
"struct rangeStruct{\
   float xMin;\
   float xMax;\
   float dx;\
   float yMin;\
   float yMax;\
   float dy;\
   float zMin;\
   float zMax;\
   float dz;\
};");

# The field map is assumed to obey the following co-ordinate bin ordering:
# z is increased first, y is increased 2nd, x is increased last.
# So we only store the field components (x,y,z is known from the ordering).
# For the coordinate bin (iX, iY, iZ), the field bin = (iX*Ny + iY)*Nz + iZ, 
# where Ny and Nz are the number of y and z bins

ROOT.gROOT.ProcessLine(
"struct dataStruct{\
   float Bx;\
   float By;\
   float Bz;\
};");


def run(inFileName  = 'BFieldTest.txt',
        rootFileName = 'BFieldTest.root'):

    createRootMap(inFileName, rootFileName)


def createRootMap(inFileName, rootFileName):

    print('Create ROOT map {0} from {1}'.format(rootFileName, inFileName))

    # Define ROOT file and its TTree
    theFile = ROOT.TFile.Open(rootFileName, 'recreate')

    rangeTree = ROOT.TTree('Range', 'Range')
    rangeTree.SetDirectory(theFile)

    # Co-ordinate ranges
    rStruct = ROOT.rangeStruct()
    rangeTree.Branch('xMin', ROOT.AddressOf(rStruct, 'xMin'), 'xMin/F')
    rangeTree.Branch('xMax', ROOT.AddressOf(rStruct, 'xMax'), 'xMax/F')
    rangeTree.Branch('dx', ROOT.AddressOf(rStruct, 'dx'), 'dx/F')
    rangeTree.Branch('yMin', ROOT.AddressOf(rStruct, 'yMin'), 'yMin/F')
    rangeTree.Branch('yMax', ROOT.AddressOf(rStruct, 'yMax'), 'yMax/F')
    rangeTree.Branch('dy', ROOT.AddressOf(rStruct, 'dy'), 'dy/F')
    rangeTree.Branch('zMin', ROOT.AddressOf(rStruct, 'zMin'), 'zMin/F')
    rangeTree.Branch('zMax', ROOT.AddressOf(rStruct, 'zMax'), 'zMax/F')
    rangeTree.Branch('dz', ROOT.AddressOf(rStruct, 'dz'), 'dz/F')

    dataTree = ROOT.TTree('Data', 'Data')
    dataTree.SetDirectory(theFile)

    # Field components with (x,y,z) coordinate binning ordered such that
    # z, then y, then x is increased. For the coordinate bin (iX, iY, iZ),
    # the field bin = (iX*Ny + iY)*Nz + iZ, where Ny and Nz are the number 
    # of y and z bins
    dStruct = ROOT.dataStruct()
    dataTree.Branch('Bx', ROOT.AddressOf(dStruct, 'Bx'), 'Bx/F')
    dataTree.Branch('By', ROOT.AddressOf(dStruct, 'By'), 'By/F')
    dataTree.Branch('Bz', ROOT.AddressOf(dStruct, 'Bz'), 'Bz/F')

    # mm to cm conversion
    mm2cm = 0.1
    # m to cm conversion
    m2cm = 100.0

    # Open text file and process the information
    iLine = 0

    # Number of bins initialised by reading first line
    Nx = 0
    Ny = 0
    Nz = 0
    Nzy = 0

    # Field centering co-ordinates
    x0 = 0.0
    y0 = 0.0
    z0 = 0.0

    with open(inFileName, 'r') as f:

        for line in f:
            iLine += 1

            # First line contains ranges
            if iLine == 1:
                # Remove extraneous, unneeded symbols in the line
                line = line.replace('[','')
                line = line.replace(']','')
                line = line.replace('mm','')
                sLine = line.split()

                # Bin info line assumed to be formatted as:
                # Grid Output Min: xMin yMin zMin Max: xMax yMax zMax Grid Size: dx dy dz
                # These co-ordinate limits are in mm, but the actual data lines use m

                print('sLine = {0}'.format(sLine))
                # For each value, convert from mm to cm
                rStruct.xMin = float(sLine[3])*mm2cm
                rStruct.xMax = float(sLine[7])*mm2cm
                rStruct.dx = float(sLine[12])*mm2cm
                rStruct.yMin = float(sLine[4])*mm2cm
                rStruct.yMax = float(sLine[8])*mm2cm
                rStruct.dy = float(sLine[13])*mm2cm
                rStruct.zMin = float(sLine[5])*mm2cm
                rStruct.zMax = float(sLine[9])*mm2cm
                rStruct.dz = float(sLine[14])*mm2cm

                Nx = int(((rStruct.xMax - rStruct.xMin)/rStruct.dx) + 1.0)
                Ny = int(((rStruct.yMax - rStruct.yMin)/rStruct.dy) + 1.0)
                Nz = int(((rStruct.zMax - rStruct.zMin)/rStruct.dz) + 1.0)
                Nzy = Nz*Ny

                print('Nx = {0}, Ny = {1}, Nz = {2}'.format(Nx, Ny, Nz))

                # Centre the field map on the local origin (cm)
                x0 = 0.5*(rStruct.xMin + rStruct.xMax)
                y0 = 0.5*(rStruct.yMin + rStruct.yMax)
                z0 = 0.5*(rStruct.zMin + rStruct.zMax)

                print('Centering field map using co-ordinate shift {0} {1} {2} cm'.format(x0, y0, z0))

                # Center co-ordinate range limits (cm)
                rStruct.xMin = rStruct.xMin - x0
                rStruct.xMax = rStruct.xMax - x0

                rStruct.yMin = rStruct.yMin - y0
                rStruct.yMax = rStruct.yMax - y0

                rStruct.zMin = rStruct.zMin - z0
                rStruct.zMax = rStruct.zMax - z0

                # Fill info into range tree
                rangeTree.Fill()
                

            # Field data values start from line 3
            elif iLine > 2:

                sLine = line.split()

                # Bin centre coordinates (m to cm), with origin shift (cm)
                dStruct.x = float(sLine[0])*m2cm - x0
                dStruct.y = float(sLine[1])*m2cm - y0
                dStruct.z = float(sLine[2])*m2cm - z0

                # B field components (Tesla)
                dStruct.Bx = float(sLine[3])
                dStruct.By = float(sLine[4])
                dStruct.Bz = float(sLine[5])

                dataTree.Fill()
                
    theFile.cd()
    rangeTree.Write()
    dataTree.Write()
    theFile.Close()


if __name__ == "__main__":

    run('BFieldTest.txt', 'BFieldTest.root')
