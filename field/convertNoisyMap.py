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

import ROOT
import pandas as pd
import os

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


def run(inFileName='FieldTest.txt', rootFileName='BFieldTest.root',
        cmScale=1.0, storeCoords=False):
    createRootMap(inFileName, rootFileName, cmScale, storeCoords)


def createRootMap(inFileName, rootFileName, cmScale, storeCoords):
    print ('Create map {} from {} using cmScale = {}'.format(rootFileName,
                                                               inFileName, cmScale))
    if storeCoords is True:
        print (f'We will also store the x,y,z field coordinates in {rootFileName}')

    rangeInfo = findRanges(inFileName, cmScale)

    # Define ROOT file and its TTree
    theFile = ROOT.TFile.Open(rootFileName, 'recreate')

    rangeTree = ROOT.TTree('Range', 'Range')
    rangeTree.SetDirectory(theFile)

    # Co-ordinate ranges
    rStruct = ROOT.rangeStruct()
    rangeTree.Branch('xMin', ROOT.addressof(rStruct, 'xMin'), 'xMin/F')
    rangeTree.Branch('xMax', ROOT.addressof(rStruct, 'xMax'), 'xMax/F')
    rangeTree.Branch('dx', ROOT.addressof(rStruct, 'dx'), 'dx/F')
    rangeTree.Branch('yMin', ROOT.addressof(rStruct, 'yMin'), 'yMin/F')
    rangeTree.Branch('yMax', ROOT.addressof(rStruct, 'yMax'), 'yMax/F')
    rangeTree.Branch('dy', ROOT.addressof(rStruct, 'dy'), 'dy/F')
    rangeTree.Branch('zMin', ROOT.addressof(rStruct, 'zMin'), 'zMin/F')
    rangeTree.Branch('zMax', ROOT.addressof(rStruct, 'zMax'), 'zMax/F')
    rangeTree.Branch('dz', ROOT.addressof(rStruct, 'dz'), 'dz/F')

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
    x0 = 0#.5 * (rStruct.xMin + rStruct.xMax)
    y0 = 0#.5 * (rStruct.yMin + rStruct.yMax)
    z0 = 0.5 * (rStruct.zMin + rStruct.zMax)

    # Use this if we don't want to centre the field map
    # x0 = 0.0
    # y0 = 0.0
    # z0 = 0.0

    print (f'Centering field map using co-ordinate shift {x0} {y0} {z0} cm')

    # Center co-ordinate range limits (cm)
    rStruct.xMin = rStruct.xMin - x0
    rStruct.xMax = rStruct.xMax - x0

    rStruct.yMin = rStruct.yMin - y0
    rStruct.yMax = rStruct.yMax - y0

    rStruct.zMin = rStruct.zMin - z0
    rStruct.zMax = rStruct.zMax - z0

    print (f'x range = {rStruct.xMin} to {rStruct.xMax}')
    print (f'y range = {rStruct.yMin} to {rStruct.yMax}')
    print (f'z range = {rStruct.zMin} to {rStruct.zMax}')

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
        dataTree.Branch('x', ROOT.addressof(dStruct, 'x'), 'x/F')
        dataTree.Branch('y', ROOT.addressof(dStruct, 'y'), 'y/F')
        dataTree.Branch('z', ROOT.addressof(dStruct, 'z'), 'z/F')

    dataTree.Branch('Bx', ROOT.addressof(dStruct, 'Bx'), 'Bx/F')
    dataTree.Branch('By', ROOT.addressof(dStruct, 'By'), 'By/F')
    dataTree.Branch('Bz', ROOT.addressof(dStruct, 'Bz'), 'Bz/F')

    # Reopen the file and store the information in the ROOT file

    inData = pd.read_csv(inFileName, delim_whitespace=True, header=None)
    inData.columns=["x", "y", "z", "bx", "by", "bz"]
    inData = inData.sort_values(by=["x","y","z"])
    inData = inData.astype(float)

    count = 0.
    data_shape = float(inData.shape[0])
    for row in inData.itertuples():
        if row.Index / data_shape >= count:
            print(f"Processed: {count * 100} %")
            count += 0.1

        # Bin centre coordinates with origin shift (all in cm)
        if storeCoords is True:
            dStruct.x = row.x * cmScale - x0
            dStruct.y = row.y * cmScale - y0
            dStruct.z = row.z * cmScale - z0

        # B field components (Tesla)
        dStruct.Bx = row.bx
        dStruct.By = row.by
        dStruct.Bz = row.bz

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
    x_set = set()
    y_set = set()
    z_set = set()

    with open(inFileName) as f:

        # Read each line
        for line in f:

            # Ignore comment lines which begin with "#"
            if '#' not in line:

                sLine = line.split()

                x = float(sLine[0]) * cmScale
                y = float(sLine[1]) * cmScale
                z = float(sLine[2]) * cmScale

                if x not in x_set:
                    xArray.append(x)
                    x_set.add(x)

                if y not in y_set:
                    yArray.append(y)
                    y_set.add(y)

                if z not in z_set:
                    zArray.append(z)
                    z_set.add(z)

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
        dx = (xMax - xMin) / (Nx1 * 1.0)

    if Ny > 0:
        yMin = yArray[0]
        Ny1 = Ny - 1
        yMax = yArray[Ny1]
        dy = (yMax - yMin) / (Ny1 * 1.0)

    if Nz > 0:
        zMin = zArray[0]
        Nz1 = Nz - 1
        zMax = zArray[Nz1]
        dz = (zMax - zMin) / (Nz1 * 1.0)

    rangeInfo = {'Nx': Nx, 'xMin': xMin, 'xMax': xMax, 'dx': dx,
                 'Ny': Ny, 'yMin': yMin, 'yMax': yMax, 'dy': dy,
                 'Nz': Nz, 'zMin': zMin, 'zMax': zMax, 'dz': dz}

    print (f'rangeInfo = {rangeInfo}')

    return rangeInfo


if __name__ == "__main__":
    run(os.path.expandvars("$FAIRSHIP/files/noisy_fieldMap.csv"),
        os.path.expandvars("$FAIRSHIP/files/MuonShieldField.root"), 1, False)
