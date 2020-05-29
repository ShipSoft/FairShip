#!/bin/python

# Python script to convert a B field map from an ascii text file into 
# a ROOT file for FairShip. The field map needs to use a regular 
# x,y,z binning structure where the co-ordinates are assumed to
# be in ascending z, y and x, in that order. Each data line needs to
# contain the values "x y z Bx By Bz", with the field components in Tesla.
# Comment lines in the datafile starting with the hash symbol # are ignored.
# Distances for FairShip need to be in cm, so we use a scaling factor 
# cmScale (default = 1.0) to convert the text file distances into cm. 
# For example, if the input data uses mm for lengths, cmScale = 0.1.

from __future__ import print_function
import ROOT

# Struct for the ROOT file TTree data: coord range and field binning

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
# For the coordinate bin (iX, iY, iZ), the field bin = (iX*Ny + iY)*Nz + iZ, 
# where Ny and Nz are the number of y and z bins

ROOT.gROOT.ProcessLine(
"struct dataStruct{\
   float x;\
   float y;\
   float z;\
   float Bx;\
   float By;\
   float Bz;\
};");


def run(inFileName = 'FieldTest.txt', rootFileName = 'BFieldTest.root', 
        cmScale = 1.0, storeCoords = False):

    createRootMap(inFileName, rootFileName, cmScale, storeCoords)


def createRootMap(inFileName, rootFileName, cmScale, storeCoords):

    print('Create map {0} from {1} using cmScale = {2}'.format(rootFileName, 
                                                                 inFileName, cmScale))
    if storeCoords is True:
        print('We will also store the x,y,z field coordinates in {0}'.format(rootFileName))

    rangeInfo = findRanges(inFileName, cmScale)

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

    rStruct.xMin = rangeInfo['xMin']
    rStruct.xMax = rangeInfo['xMax']
    rStruct.dx = rangeInfo['dx']
    rStruct.yMin = rangeInfo['yMin']
    rStruct.yMax = rangeInfo['yMax']
    rStruct.dy = rangeInfo['dy']
    rStruct.zMin = rangeInfo['zMin']
    rStruct.zMax = rangeInfo['zMax']
    rStruct.dz = rangeInfo['dz']
    
    # Centre the field map on the local origin (cm)
    x0 = 0.5*(rStruct.xMin + rStruct.xMax)
    y0 = 0.5*(rStruct.yMin + rStruct.yMax)
    z0 = 0.5*(rStruct.zMin + rStruct.zMax)

    # Use this if we don't want to centre the field map
    #x0 = 0.0
    #y0 = 0.0
    #z0 = 0.0

    print('Centering field map using co-ordinate shift {0} {1} {2} cm'.format(x0, y0, z0))
    
    # Center co-ordinate range limits (cm)
    rStruct.xMin = rStruct.xMin - x0
    rStruct.xMax = rStruct.xMax - x0
    
    rStruct.yMin = rStruct.yMin - y0
    rStruct.yMax = rStruct.yMax - y0
    
    rStruct.zMin = rStruct.zMin - z0
    rStruct.zMax = rStruct.zMax - z0

    print('x range = {0} to {1}'.format(rStruct.xMin, rStruct.xMax))
    print('y range = {0} to {1}'.format(rStruct.yMin, rStruct.yMax))
    print('z range = {0} to {1}'.format(rStruct.zMin, rStruct.zMax))
    
    # Fill info into range tree
    rangeTree.Fill()

    # Store field data components
    dataTree = ROOT.TTree('Data', 'Data')
    dataTree.SetDirectory(theFile)

    # Field components with (x,y,z) coordinate binning ordered such that
    # z, then y, then x is increased. For the coordinate bin (iX, iY, iZ),
    # the field bin = (iX*Ny + iY)*Nz + iZ, where Ny and Nz are the number 
    # of y and z bins
    dStruct = ROOT.dataStruct()
    if storeCoords is True:
        dataTree.Branch('x', ROOT.AddressOf(dStruct, 'x'), 'x/F')
        dataTree.Branch('y', ROOT.AddressOf(dStruct, 'y'), 'y/F')
        dataTree.Branch('z', ROOT.AddressOf(dStruct, 'z'), 'z/F')

    dataTree.Branch('Bx', ROOT.AddressOf(dStruct, 'Bx'), 'Bx/F')
    dataTree.Branch('By', ROOT.AddressOf(dStruct, 'By'), 'By/F')
    dataTree.Branch('Bz', ROOT.AddressOf(dStruct, 'Bz'), 'Bz/F')
                
    # Reopen the file and store the information in the ROOT file
    with open(inFileName, 'r') as f:

        # Read each line
        for line in f:

            # Ignore comment lines which begin with "#"
            if '#' not in line:

                sLine = line.split()

                # Bin centre coordinates with origin shift (all in cm)
                if storeCoords is True:
                    dStruct.x = float(sLine[0])*cmScale - x0
                    dStruct.y = float(sLine[1])*cmScale - y0
                    dStruct.z = float(sLine[2])*cmScale - z0

                # B field components (Tesla)
                dStruct.Bx = float(sLine[3])
                dStruct.By = float(sLine[4])
                dStruct.Bz = float(sLine[5])

                dataTree.Fill()
                

    theFile.cd()
    rangeTree.Write()
    dataTree.Write()
    theFile.Close()


def findRanges(inFileName, cmScale):

    # First read the data file to find the binning and coordinate ranges.
    # Store the unique (ordered) x, y and z values so we can then find the 
    # bin widths, min/max limits and central offset
    
    xArray = []
    yArray = []
    zArray = []

    with open(inFileName, 'r') as f:

        # Read each line
        for line in f:

            # Ignore comment lines which begin with "#"
            if '#' not in line:

                sLine = line.split()

                x = float(sLine[0])*cmScale
                y = float(sLine[1])*cmScale
                z = float(sLine[2])*cmScale

                if x not in xArray:
                    xArray.append(x)

                if y not in yArray:
                    yArray.append(y)

                if z not in zArray:
                    zArray.append(z)

    Nx = len(xArray)
    Ny = len(yArray)
    Nz = len(zArray)

    xMin = 0.0
    xMax = 0.0
    dx = 0.0

    if Nx > 0:
        xMin = xArray[0]
        Nx1 = Nx - 1
        xMax = xArray[Nx1]
        dx = (xMax - xMin)/(Nx1*1.0)

    if Ny > 0:
        yMin = yArray[0]
        Ny1 = Ny - 1
        yMax = yArray[Ny1]
        dy = (yMax - yMin)/(Ny1*1.0)

    if Nz > 0:
        zMin = zArray[0]
        Nz1 = Nz - 1
        zMax = zArray[Nz1]
        dz = (zMax - zMin)/(Nz1*1.0)

    rangeInfo = {'Nx': Nx, 'xMin': xMin, 'xMax': xMax, 'dx': dx,
                 'Ny': Ny, 'yMin': yMin, 'yMax': yMax, 'dy': dy,
                 'Nz': Nz, 'zMin': zMin, 'zMax': zMax, 'dz': dz}

    #print 'rangeInfo = {0}'.format(rangeInfo)

    return rangeInfo


if __name__ == "__main__":

    run('GoliathFieldMap.txt', 'GoliathFieldMap.root', 0.1, True)
    #run('BFieldTest.txt', 'BFieldTest.root', 1.0)
