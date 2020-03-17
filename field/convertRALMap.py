#!/bin/python

# Python script to convert B field maps into text and ROOT files for FairShip.
# Reduce the number of decimal places to try to reduce the file size.
# Also add to the file info about the binning, offsets etc..
# Input file distances are in m; convert them to centimetres

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


def run(inFileName  = 'test07_10cm_grid.table', 
        outFileName = 'MuonFilterBFieldMap1.txt'):

    # Text format
    createTextMap(inFileName, outFileName)

    # Also create ROOT file based on the restructured text output
    rootFileName = outFileName.replace('.txt', '.root')
    createRootMap(outFileName, rootFileName)


def createTextMap(inFileName, outFileName):

    print('Creating text map {0} from {1}'.format(outFileName, inFileName))

    tmpFileName = 'tmpFile.txt'
    
    inFile = open(inFileName, 'r')
    tmpFile = open(tmpFileName, 'w')

    iLine = 0
    xMin = 0.0
    xMax = 0.0
    dx = 0.0
    yMin = 0.0
    yMax = 0.0
    dy = 0.0
    zMin = 0.0
    zMax = 0.0
    dz = 0.0
    
    # Offsets (in cm)
    #ox = 0.0
    #oy = 0.0
    #oz = 0.0

    iLine = 0
    # Convert metres to centimetres
    m2cm = 100.0
    
    # For finding the delta bin widths
    xOld = 0.0
    yOld = 0.0
    zOld = 0.0
    gotdx = 0
    gotdy = 0
    gotdz = 0

    firstDataLine = 9

    for inLine in inFile:

        iLine += 1
        # Skip the first few lines
        if iLine >= firstDataLine:
            words = inLine.split()
            #print 'words = {0}'.format(words)
            # Convert the x,y,z co-ords to centimetres
            x = float(words[0])*m2cm
            y = float(words[1])*m2cm
            z = float(words[2])*m2cm
            Bx = float(words[3])
            By = float(words[4])
            Bz = float(words[5])

            BxWord = formatNumber(Bx)
            ByWord = formatNumber(By)
            BzWord = formatNumber(Bz)

            # Write out the new line. Just print out the B field components, since we
            # can infer x,y,z co-ords from the ordering
            newLine = '{0} {1} {2}\n'.format(BxWord, ByWord, BzWord)
            #newLine = '{0:.0f} {1:.0f} {2:.0f} {3:.3e} {4:.3e} {5:.3e}\n'.format(x,y,z,Bx,By,Bz)
            tmpFile.write(newLine)

            # Keep track of the min/max values
            if iLine == firstDataLine:
                xMin = x
                xMax = x
                xOld = x
                yMin = y
                yMax = y
                yOld = y
                zMin = z
                zMax = z
                zOld = z
        
            if x < xMin:
                xMin = x
            if x > xMax:
                xMax = x
            if y < yMin:
                yMin = y
            if y > yMax:
                yMax = y
            if z < zMin:
                zMin = z
            if z > zMax:
                zMax = z

            if gotdx == 0 and x != xOld:
                dx = x - xOld
                gotdx = 1
            if gotdy == 0 and y != yOld:
                dy = y - yOld
                gotdy = 1
            if gotdz == 0 and z != zOld:
                dz = z - zOld
                gotdz = 1

    print('dx = {0}, dy = {1}, dz = {2}'.format(dx,dy,dz))
    print('x = {0} to {1}, y = {2} to {3}, z = {4} to {5}'.format(xMin, xMax, yMin, yMax, zMin, zMax))

    tmpFile.close()
    inFile.close()

    # Write out the map containing the co-ordinate ranges and offsets etc
    tmpFile2 = open(tmpFileName, 'r')
    outFile = open(outFileName, 'w')

    outLine = 'CLimits {0:.0f} {1:.0f} {2:.0f} {3:.0f} {4:.0f} {5:.0f} ' \
        '{6:.0f} {7:.0f} {8:.0f}\n'.format(xMin, xMax, dx, yMin, yMax, dy, zMin, zMax, dz)
    outFile.write(outLine)

    #outLine = 'Offsets {0:.0f} {1:.0f} {2:.0f}\n'.format(ox, oy, oz)
    #outFile.write(outLine)

    # Write a line showing the variable names (for file readability)
    outLine = 'Bx(T) By(T) Bz(T)\n'
    #outLine = 'x(cm) y(cm) z(cm) Bx(T) By(T) Bz(T)\n'
    outFile.write(outLine)

    # Copy the tmp file data
    for tLine in tmpFile2:
    
        outFile.write(tLine)

    outFile.close()
    tmpFile2.close()

def formatNumber(x):

    # To save disk space, reduce the precision of the field value
    # as we go below various thresholds
    
    # Let the general precision be 0.01 mT. Anything below this 
    # is set to zero.
    xWord = '{0:.5f}'.format(x)

    if abs(x) < 1e-5:

        # Set to zero
        xWord = '0'

    return xWord

def createRootMap(inFileName, outFileName):

    print('Create ROOT map {0} from {1}'.format(outFileName, inFileName))

    # Define ROOT file and its TTree
    theFile = ROOT.TFile.Open(outFileName, 'recreate')

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

    # Open text file and process the information
    iLine = 0

    # Number of bins initialised by reading first line
    Nx = 0
    Ny = 0
    Nz = 0
    Nzy = 0

    with open(inFileName, 'r') as f:

        for line in f:
            iLine += 1
            sLine = line.split()

            # First line contains ranges
            if iLine == 1:
                rStruct.xMin = float(sLine[1])
                rStruct.xMax = float(sLine[2])
                rStruct.dx = float(sLine[3])
                rStruct.yMin = float(sLine[4])
                rStruct.yMax = float(sLine[5])
                rStruct.dy = float(sLine[6])
                rStruct.zMin = float(sLine[7])
                rStruct.zMax = float(sLine[8])
                rStruct.dz = float(sLine[9])

                Nx = int(((rStruct.xMax - rStruct.xMin)/rStruct.dx) + 1.0)
                Ny = int(((rStruct.yMax - rStruct.yMin)/rStruct.dy) + 1.0)
                Nz = int(((rStruct.zMax - rStruct.zMin)/rStruct.dz) + 1.0)
                Nzy = Nz*Ny

                print('Nx = {0}, Ny = {1}, Nz = {2}'.format(Nx, Ny, Nz))

                rangeTree.Fill()

            elif iLine > 2:

                # B field components
                dStruct.Bx = float(sLine[0])
                dStruct.By = float(sLine[1])
                dStruct.Bz = float(sLine[2])

                # Also store bin centre coordinates.
                # Map is ordered in ascending z, y, then x
                #iBin = iLine - 3
                #zBin = iBin%Nz
                #yBin = int((iBin/Nz))%Ny
                #xBin = int(iBin/Nzy)
                #dStruct.x = rStruct.dx*(xBin + 0.5) + rStruct.xMin
                #dStruct.y = rStruct.dy*(yBin + 0.5) + rStruct.yMin
                #dStruct.z = rStruct.dz*(zBin + 0.5) + rStruct.zMin

                dataTree.Fill()
                
    theFile.cd()
    rangeTree.Write()
    dataTree.Write()
    theFile.Close()


if __name__ == "__main__":

    run('test07_10cm_grid.table', 'MuonFilterBFieldMap1.txt')
    #run('test08_10cm_grid.table', 'MuonFilterBFieldMap2.txt')
    #run('test09_10cm_grid.table', 'MuonFilterBFieldMap3.txt')
    #run('test10_10cm_grid.table', 'MuonFilterBFieldMap4.txt')
    #run('test12_10cm_grid.table', 'MuonFilterBFieldMap5.txt')
