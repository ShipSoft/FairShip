#!/bin/python

# Python script to convert the B field map  for use in the G4 simulation.
# Reduce the number of decimal places to try to reduce the file size.
# Also add to the file preamble the binning, offset info etc..
# The field maps should have 10 cm binning resolution. 
# Distances are in m; to save on decimal place use, convert them to centimetres.

def run(inFileName = 'test07_10cm_grid.table', 
        outFileName= 'MuonFilterBFieldMap1.txt'):

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
            # can infer x,y,z co-ords from the ordering...
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

    print 'dx = {0}, dy = {1}, dz = {2}'.format(dx,dy,dz)
    print 'x = {0} to {1}, y = {2} to {3}, z = {4} to {5}'.format(xMin, xMax, yMin, yMax, zMin, zMax)

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


if __name__ == "__main__":

    run('test07_10cm_grid.table', 'MuonFilterBFieldMap1.txt')
    run('test08_10cm_grid.table', 'MuonFilterBFieldMap2.txt')
    run('test09_10cm_grid.table', 'MuonFilterBFieldMap3.txt')

