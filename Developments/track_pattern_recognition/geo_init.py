__author__ = 'Mikhail Hushchyn'

import ROOT
import numpy

def initialize(fGeo, ShipGeo):

    debug = 0
    #creates a dictionary with z coordinates of layers
    #and variables with station start/end coordinates
    #to be called once at the beginning of the eventloop
    i1=1 #1st layer
    i2=16 #last layer
    zlayer={} #dictionary with z coordinates of station1,2 layers
    zlayerv2={} #z-positions for stereo views
    z34layer={} #dictionary with z coordinates of station3,4 layers
    z34layerv2={} #z-positions for stereo views
    TStation1StartZ=0.
    TStation4EndZ=0.
    VetoStationZ=0.
    VetoStationEndZ=0.

    fgeo=fGeo
    #z-positions of Y-view tracking
    #4 stations, 4 views (Y,u,v,Y); each view has 2 planes and each plane has 2 layers

    for i in range(i1,i2+1):
        TStationz = ShipGeo.TrackStation1.z
        if (i>8) :
            TStationz = ShipGeo.TrackStation2.z
        # Y: vnb=0 or 3
        vnb=0.
        if (i>4): vnb=3.
        if (i>8): vnb=0.
        if (i>12): vnb=3.
        lnb = 0.
        if (i % 2 == 0) : lnb=1.
        pnb=0.
        if (i==3 or i==4 or i==7 or i==8 or i==11 or i==12 or i==15 or i==16) : pnb=1.

        #z positions of Y view of stations
        Zpos = TStationz+(vnb-3./2.)*ShipGeo.strawtubes.DeltazView+(float(pnb)-1./2.)*ShipGeo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ShipGeo.strawtubes.DeltazLayer
        zlayer[i]=[Zpos]

    #z-positions for stereo views

    for i in range(i1,i2+1):
        TStationz = ShipGeo.TrackStation1.z
        if (i>8) :
            TStationz = ShipGeo.TrackStation2.z
        #stereo views: vnb=1 or 2
        vnb=1.
        if (i>4): vnb=2.
        if (i>8): vnb=1.
        if (i>12): vnb=2.
        lnb = 0.
        if (i % 2 == 0) : lnb=1.
        pnb=0.
        if (i==3 or i==4 or i==7 or i==8 or i==11 or i==12 or i==15 or i==16) : pnb=1.

        #z positions of u,v view of stations
        Zpos_u = TStationz+(vnb-3./2.)*ShipGeo.strawtubes.DeltazView+(float(pnb)-1./2.)*ShipGeo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ShipGeo.strawtubes.DeltazLayer
        zlayerv2[i]=[Zpos_u]


    for i in range(i1,i2+1):
        TStationz = ShipGeo.TrackStation3.z
        if (i>8) :
            TStationz = ShipGeo.TrackStation4.z
        # Y: vnb=0 or 3
        vnb=0.
        if (i>4): vnb=3.
        if (i>8): vnb=0.
        if (i>12): vnb=3.
        lnb = 0.
        if (i % 2 == 0) : lnb=1.
        pnb=0.
        if (i==3 or i==4 or i==7 or i==8 or i==11 or i==12 or i==15 or i==16) : pnb=1.

        #z positions of x1 view of stations
        Zpos = TStationz+(vnb-3./2.)*ShipGeo.strawtubes.DeltazView+(float(pnb)-1./2.)*ShipGeo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ShipGeo.strawtubes.DeltazLayer
        z34layer[i]=[Zpos]


    for i in range(i1,i2+1):
        #zlayerv2[i]=[i*100.+50.]
        TStationz = ShipGeo.TrackStation3.z
        if (i>8) :
            TStationz = ShipGeo.TrackStation4.z
        #stereo views: vnb=1 or 2
        vnb=1.
        if (i>4): vnb=2.
        if (i>8): vnb=1.
        if (i>12): vnb=2.
        lnb = 0.
        if (i % 2 == 0) : lnb=1.
        pnb=0.
        if (i==3 or i==4 or i==7 or i==8 or i==11 or i==12 or i==15 or i==16) : pnb=1.

        #z positions of u,v view of stations
        Zpos_u = TStationz+(vnb-3./2.)*ShipGeo.strawtubes.DeltazView+(float(pnb)-1./2.)*ShipGeo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ShipGeo.strawtubes.DeltazLayer
        z34layerv2[i]=[Zpos_u]

    VetoStationZ = ShipGeo.vetoStation.z
    if debug==1: print "VetoStation midpoint z=",VetoStationZ
    VetoStationEndZ=VetoStationZ+(ShipGeo.strawtubes.DeltazView+ShipGeo.strawtubes.OuterStrawDiameter)/2
    for i in range(1,5):
        if i==1: TStationz = ShipGeo.TrackStation1.z
        if i==2: TStationz = ShipGeo.TrackStation2.z
        if i==3: TStationz = ShipGeo.TrackStation3.z
        if i==4: TStationz = ShipGeo.TrackStation4.z
        if debug==1:
            print "TrackStation",i," midpoint z=",TStationz
        for vnb in range(0,4):
            for pnb in range (0,2):
                for lnb in range (0,2):
                    Zpos = TStationz+(vnb-3./2.)*ShipGeo.strawtubes.DeltazView+(float(pnb)-1./2.)*ShipGeo.strawtubes.DeltazPlane+(float(lnb)-1./2.)*ShipGeo.strawtubes.DeltazLayer

    TStation1StartZ=zlayer[1][0]-ShipGeo.strawtubes.OuterStrawDiameter/2
    TStation4EndZ=z34layer[16][0]+ShipGeo.strawtubes.OuterStrawDiameter/2

    return zlayer,zlayerv2,z34layer,z34layerv2,TStation1StartZ,TStation4EndZ,VetoStationZ,VetoStationEndZ
