import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry
# the following params should be passed through 'ConfigRegistry.loadpy' method
# none for the moment
with ConfigRegistry.register_config("basic") as c:

    c.MufluxSpectrometer = AttrDict(z = 0*u.cm)  
    # False = charm cross-section; True = muon flux measurement 
    
    if "targetOpt" not in globals():
       targetOpt = 18 # add extra 20cm of tungsten as per 13/06/2017

    if "Setup" not in globals(): #muon flux or charm xsec measurement
      Setup = 0    

    if Setup == 0: 
     c.MufluxSpectrometer.muflux = True
    else: 
     c.MufluxSpectrometer.muflux = False

    c.target = AttrDict(z0=0*u.cm)
     
    c.MufluxTargetStation=AttrDict(z0=0* u.cm)
    c.MufluxTargetStation.absorber_x=120 *u.cm
    c.MufluxTargetStation.absorber_y=97.5*u.cm
    c.MufluxTargetStation.absorbercutout_x=102* u.cm
    c.MufluxTargetStation.absorbercutout_y=27.5*u.cm
    c.MufluxTargetStation.ironshield_x=20.*u.cm
    c.MufluxTargetStation.ironshield_y=82.5*u.cm
    c.MufluxTargetStation.ironshield_z=160*u.cm
    c.MufluxTargetStation.concreteshield_x=40*u.cm
    c.MufluxTargetStation.concreteshield_y=82.5*u.cm
    c.MufluxTargetStation.concreteshield_z=160.*u.cm
    c.MufluxTargetStation.abovetargetshield_x=120*u.cm
    c.MufluxTargetStation.abovetargetshield_y=42.5*u.cm
    c.MufluxTargetStation.abovetargetshield_z=160*u.cm
    c.MufluxTargetStation.aboveabsorbershield_x=120*u.cm
    c.MufluxTargetStation.aboveabsorbershield_y=40*u.cm
    c.MufluxTargetStation.aboveabsorbershield_z=80*u.cm
    c.MufluxTargetStation.aboveabovetargetshield_y=40*u.cm
    c.MufluxTargetStation.floor_x=500.*u.cm
    c.MufluxTargetStation.floor_y=80.*u.cm
    c.MufluxTargetStation.floor_z=800.*u.cm
    c.MufluxTargetStation.floorT34_x=500.*u.cm
    c.MufluxTargetStation.floorT34_y=16.*u.cm
    c.MufluxTargetStation.floorT34_z=118.875*u.cm
    c.MufluxTargetStation.floorRPC_x=500.*u.cm
    c.MufluxTargetStation.floorRPC_y=32.5*u.cm
    c.MufluxTargetStation.floorRPC_z=110.*u.cm   

    #BOX (Brick!)
    c.Box = AttrDict(z=0*u.cm)
    c.Box.zBox = 106.66 * u.cm
    c.Box.EmTh = 0.0070 * u.cm
    c.Box.EmX = 12.5 * u.cm
    c.Box.EmY = 9.9 * u.cm
    c.Box.PBTh = 0.0175 * u.cm
    c.Box.PasSlabTh = 0.1 * u.cm #passive slab in ECC (lead for July measurement, molybdenum/tungsten for SHiP target replica
    c.Box.EPlW = 2* c.Box.EmTh + c.Box.PBTh
    c.Box.AllPW = c.Box.PasSlabTh + c.Box.EPlW
    c.Box.BrX = 12.9 *u.cm
    c.Box.BrY = 10.5 *u.cm
    c.Box.BrPackZ = 0.1 * u.cm
    c.Box.BrPackX = c.Box.BrX - c.Box.EmX
    c.Box.BrPackY = c.Box.BrY - c.Box.EmY
    c.Box.BrZ = 54 * c.Box.AllPW + c.Box.EPlW +c.Box.BrPackZ
    c.Box.CoolX = c.Box.EmX #all the passive layers have the same transverse dimensions of nuclear emulsion films 
    c.Box.CoolY = c.Box.EmY
    c.Box.CoolZ = 0.5 * u.cm
    c.Box.CoatX = c.Box.EmX 
    c.Box.CoatY = c.Box.EmY
    c.Box.CoatZ = 0.15 * u.cm
    c.Box.TX = c.Box.EmX
    c.Box.TY = c.Box.EmY
    c.Box.TZ = 5.7 *u.cm #not used for July testbeam geometry
    #passive blocks thicknesses
    c.Box.Molblock1Z = 7.7 * u.cm 
    c.Box.Molblock2Z = 2.2 * u.cm 
    c.Box.Molblock3Z = 4.7 * u.cm
    c.Box.Molblock4Z = 6.2 * u.cm
    c.Box.Wblock1Z = 4.7 * u.cm
    c.Box.Wblock2Z = 7.7 * u.cm
    c.Box.Wblock3Z = 9.7 * u.cm
    c.Box.Wblock3_5Z = 19.7 * u.cm
    c.Box.Wblock4Z = 8.45 * u.cm

    #passive sampling
    c.Box.Passive3mmZ = 0.3 * u.cm
    c.Box.Passive2mmZ = 0.2 * u.cm
    c.Box.Passive1mmZ = 0.1 * u.cm

    #OPTIONS FOR CHARM XSEC DETECTOR
    c.Box.gausbeam = True
    c.Box.Julytarget = False
    #c.Box.GapPostTargetTh = 5 * u.cm #gap between charm target and T1 station
    c.Box.GapPostTargetTh = 0.73 * u.cm     
    #c.Box.GapPostTargetTh = 0*u.cm
    c.Box.RunNumber =  3 #run configuration for charm

    # target absorber muon shield setup, decayVolume.length = nominal EOI length, only kept to define z=0
    c.decayVolume            =  AttrDict(z=0*u.cm)
    c.decayVolume.length     =   50*u.m

    c.hadronAbsorber              =  AttrDict(z=0*u.cm)
    c.hadronAbsorber.length =  2.4*u.m    
    
    c.hadronAbsorber.z     =   - c.hadronAbsorber.length/2.

    c.target               =  AttrDict(z=0*u.cm)
    c.targetOpt            = targetOpt

    c.target.M1 = "molybdenummisis"
    c.target.L1 = 8.52*u.cm
    c.target.M2 = "molybdenummisis"
    c.target.L2 = 2.8*u.cm
    c.target.M3 = "molybdenummisis"
    c.target.L3 = 2.8*u.cm
    c.target.M4 = "molybdenummisis"
    c.target.L4 = 2.8*u.cm
    c.target.M5 = "molybdenummisis"
    c.target.L5 = 2.8*u.cm
    c.target.M6 = "molybdenummisis"
    c.target.L6 = 2.8*u.cm
    c.target.M7 = "molybdenummisis"
    c.target.L7 = 2.8*u.cm
    c.target.M8 = "molybdenummisis"
    c.target.L8 = 2.8*u.cm
    c.target.M9 = "molybdenummisis"
    c.target.L9 = 5.4*u.cm
    c.target.M10 = "molybdenummisis"
    c.target.L10 = 5.4*u.cm
    c.target.M11 = "molybdenummisis"
    c.target.L11 = 6.96*u.cm
    c.target.M12 = "molybdenummisis"
    c.target.L12 = 8.52*u.cm
    c.target.M13 = "molybdenummisis"
    c.target.L13 = 8.52*u.cm
    c.target.M14 = "tungstenmisis"
    c.target.L14 = 5.17*u.cm
    c.target.M15 = "tungstenmisis"
    c.target.L15 = 8.3*u.cm
    c.target.M16 = "tungstenmisis"
    c.target.L16 = 10.39*u.cm
    c.target.M17 = "tungstenmisis"
    c.target.L17 = 20.82*u.cm
    c.target.M18 = "tungstenmisis"
    c.target.L18 = 36.47*u.cm
    c.target.sl  =  0.54459*u.cm  # H20 slit *17 times; to get to the measured length by survey 
    c.target.xy  = 10.*u.cm   # new diameter of muflux target    
    
    # 5.0 cm is for front and endcaps
    
    c.target.length = 154.328*u.cm   #from survey 
    # interaction point, start of target
    
    c.target.z   =  c.hadronAbsorber.z - c.hadronAbsorber.length/2. - c.target.length/2.
    c.target.z0  =  c.target.z - c.target.length/2.
       
    #Spectrometer
    c.Spectrometer = AttrDict(z = 0*u.cm)
    #Parameters for Goliath by Annarita
    c.Spectrometer.LS = 4.5*u.m
    c.Spectrometer.TS = 3.6*u.m
    c.Spectrometer.CoilR = 1*u.m
    c.Spectrometer.UpCoilH = 45*u.cm
    c.Spectrometer.LowCoilH = 30*u.cm
    c.Spectrometer.CoilD = 105*u.cm
    c.Spectrometer.BasisH = 57*u.cm
    c.Spectrometer.H = 2*c.Spectrometer.BasisH + c.Spectrometer.CoilD + c.Spectrometer.UpCoilH + c.Spectrometer.LowCoilH

    # -----Drift tube part --------
    c.MufluxSpectrometer.v_drift = 1./(72*u.ns/u.mm) # 1300 ns max for 36.3 mm drifttubes
    c.MufluxSpectrometer.sigma_spatial = 0.027*u.cm # from Daniel 8feb2018
    
    c.MufluxSpectrometer.TubeLength         = 160.*u.cm
    c.MufluxSpectrometer.TubeLength12       = 110.*u.cm    
    c.MufluxSpectrometer.tr12ydim           = 110.*u.cm
    c.MufluxSpectrometer.tr34xdim           = 200.*u.cm
    c.MufluxSpectrometer.tr12xdim           = 50.*u.cm
    c.MufluxSpectrometer.tr34ydim           = 160.*u.cm
    
    # parameters for drift tubes
    c.MufluxSpectrometer.InnerTubeDiameter  = 3.63*u.cm 
    c.MufluxSpectrometer.WallThickness      = 0.085*u.cm
    c.MufluxSpectrometer.OuterTubeDiameter  = (c.MufluxSpectrometer.InnerTubeDiameter + 2*c.MufluxSpectrometer.WallThickness)

    c.MufluxSpectrometer.TubePitch          = 4.2*u.cm
    c.MufluxSpectrometer.DeltazLayer        = 3.64*u.cm
    c.MufluxSpectrometer.DeltazPlane        = 7.7*u.cm
    
    c.MufluxSpectrometer.TubesPerLayer      = 12
    c.MufluxSpectrometer.ViewAngle          = -60
    c.MufluxSpectrometer.WireThickness      = 0.0045*u.cm
    c.MufluxSpectrometer.DeltazView         = 15.*u.cm
    
    c.MufluxSpectrometer.diststereo         = 16.25*u.cm    
    c.MufluxSpectrometer.distT1T2           = 11.*u.cm   
    if c.MufluxSpectrometer.muflux == True:
       c.MufluxSpectrometer.distT3T4           = 1.6*u.m       
    else:
       c.MufluxSpectrometer.distT3T4 = 1.0*u.m   
            
    c.MufluxSpectrometer.goliathcentre_to_beam = 178.6*u.mm
   
    c.MufluxSpectrometer.T1x_x=4.2*u.cm
    c.MufluxSpectrometer.T1x_y=-1.995*u.cm
    c.MufluxSpectrometer.T1z=38.875*u.cm
    c.MufluxSpectrometer.T1u_x=7.79*u.cm
    c.MufluxSpectrometer.T1u_y=0.182*u.cm
    c.MufluxSpectrometer.T2x_x=2.61*u.cm
    c.MufluxSpectrometer.T2x_y=-2.1875*u.cm  
    c.MufluxSpectrometer.T2z=107.625*u.cm       
    c.MufluxSpectrometer.T2v_x=3.4804*u.cm  
    c.MufluxSpectrometer.T2v_y=-0.5*u.cm       
    c.MufluxSpectrometer.T3x=2.6*u.cm
    c.MufluxSpectrometer.T3y=-7.3405*u.cm
    c.MufluxSpectrometer.T3z=586.25*u.cm
    c.MufluxSpectrometer.T4x=2.95*u.cm   
    c.MufluxSpectrometer.T4y=-6.9845*u.cm 
    c.MufluxSpectrometer.T4z=747.25*u.cm               

     
    
    if c.MufluxSpectrometer.muflux == True:    
       c.Spectrometer.DX = 2.*u.m
       c.Spectrometer.DY = 1.6*u.m   
       c.Spectrometer.DZ = 16.*u.cm
    else:        
       c.Spectrometer.DX = 1*u.m
       c.Spectrometer.DY = 0.5*u.m
       c.Spectrometer.DZ = 13.5 * u.cm
       
    c.MufluxSpectrometer.DX = 2.*u.m
    c.MufluxSpectrometer.DY = 1.6*u.m
    c.MufluxSpectrometer.DZ = 16.*u.cm
    
    #These parameters are used only by the charm detector ---   
    c.Spectrometer.D1Short = 3.36 * u.cm / 2.;
    c.Spectrometer.D1Long = 4 * u.cm;   
    c.Spectrometer.DimZSi = 0.0200 * u.cm
    c.Spectrometer.PairSiDistance = 0.600 * u.cm +c.Spectrometer.DimZSi 
    c.Spectrometer.Sioverlap = 0.2*u.cm   
         
    c.Spectrometer.SX = c.Spectrometer.DX
    c.Spectrometer.SY = c.Spectrometer.DY    
   
    
    #position of module centres
    c.Spectrometer.zSi0 = c.Spectrometer.PairSiDistance/2. + c.Spectrometer.DimZSi/2. + c.Box.GapPostTargetTh
    c.Spectrometer.zSi1 = c.Spectrometer.zSi0 + 2.70 *u.cm
    c.Spectrometer.zSi2 = c.Spectrometer.zSi1 + 2.54 *u.cm
    c.Spectrometer.zSi3 = c.Spectrometer.zSi2 + 2.70 *u.cm
    c.Spectrometer.zSi4 = c.Spectrometer.zSi3 + 2.54 *u.cm
    c.Spectrometer.zSi5 = c.Spectrometer.zSi4 + 2.70 *u.cm    

    c.Spectrometer.DSciFi1X = 40 * u.cm;
    c.Spectrometer.DSciFi1Y = 40 * u.cm;
    c.Spectrometer.DSciFi2X = 40 * u.cm;
    c.Spectrometer.DSciFi2Y = 40 * u.cm;  

    c.Spectrometer.Bvalue = 1 * u.tesla;

    #-------------------------------------------------------
            
    
    #Scintillator
    c.Scintillator = AttrDict(z = 0*u.cm)
    c.Scintillator.Scoring1X           = 55.*u.cm
    c.Scintillator.Scoring1Y           = 110.*u.cm    
    c.Scintillator.DistT1              = 11.5*u.cm       
    c.Scintillator.DistT2              = 135.25*u.cm
                   
    if c.MufluxSpectrometer.muflux == True: 
       #these parameters are also used inside the MufluxSpectrometer.cxx
       c.Spectrometer.SZ = 2*(2*c.Spectrometer.DZ +c.MufluxSpectrometer.diststereo) + c.MufluxSpectrometer.distT1T2 +4.5*u.m + c.MufluxSpectrometer.distT3T4 + 2*(2*c.Spectrometer.DZ) + 2.5*u.cm
    else: 
       c.Spectrometer.SZ = c.Spectrometer.DZ*2 + c.Spectrometer.zSi5 - c.Spectrometer.zSi0 + c.Spectrometer.PairSiDistance + c.Spectrometer.DimZSi + 80 *u.cm + 4.5*u.m #4.5 m is the Goliath length + 80 *u.cm + 4.5*u.m #4.5 m is the Goliath length
   
    c.Spectrometer.DimZpixelbox = c.Box.GapPostTargetTh + c.Spectrometer.zSi5 - c.Spectrometer.zSi0 + c.Spectrometer.PairSiDistance + c.Spectrometer.DimZSi
    
    PixeltoGoliath = 30.45 *u.cm #25.45 + 5cm different goliath dz
    c.Spectrometer.zBox = 350.75 - c.Spectrometer.TS/2 - PixeltoGoliath - c.Spectrometer.DimZpixelbox/2.
    c.Box.zBox = c.Spectrometer.zBox - c.Spectrometer.DimZpixelbox/2. 

    #position of SciFis 
    distGoliathSciFi1 = 10*u.cm
    c.Spectrometer.Scifidist = 5 * u.cm   
    c.Spectrometer.zSciFi1 = c.Spectrometer.zBox + c.Spectrometer.DimZpixelbox/2. + PixeltoGoliath + c.Spectrometer.TS + distGoliathSciFi1 +  c.Spectrometer.DZ/2.
    c.Spectrometer.zSciFi2 = c.Spectrometer.zSciFi1 + c.Spectrometer.DZ/2. + c.Spectrometer.Scifidist + c.Spectrometer.DZ/2.

    #Muon Filter
    
    c.MuonTagger = AttrDict(z = 0*u.cm)
    c.MuonTagger.PTh = 80 * u.cm;
    c.MuonTagger.PTh1 = 40 * u.cm #last 3 slabs' thickness
    c.MuonTagger.STh = 5.0 * u.cm
    c.MuonTagger.BX = 1.936725 * u.m
    c.MuonTagger.BY = 1.215312 * u.m
    c.MuonTagger.BZ = c.MuonTagger.PTh * 2 + c.MuonTagger.PTh1 * 3 + c.MuonTagger.STh * 5
    
    if c.MufluxSpectrometer.muflux == True:
       #for the muflux measurement the muontagger has to be moved back
       c.MuonTagger.zBox = 791.75*u.cm  + 152.5*u.cm
       #c.MuonTagger.zBox = c.Spectrometer.zSi5 +c.Spectrometer.PairSiDistance/2.+c.Spectrometer.DimZSi/2. + c.Spectrometer.LS +           c.MuonTagger.BZ/2. + 199.5*u.cm#starting from 223 cm from Goliath, like in muonflux measurement

    else:    
       #c.MuonTagger.zBox = c.Spectrometer.SZ+ c.MuonTagger.BZ/2 + 5*u.cm
       c.MuonTagger.zBox = c.Spectrometer.zBox + c.Spectrometer.DimZpixelbox/2. + PixeltoGoliath + c.Spectrometer.TS + 261*u.cm + c.MuonTagger.BZ/2. #real position of MuonTagger

    c.MuonTagger.PX = c.MuonTagger.BX
    c.MuonTagger.PY = c.MuonTagger.BY
    c.MuonTagger.SX = c.MuonTagger.BX
    c.MuonTagger.SY = c.MuonTagger.BY
    c.MuonTagger.HX = 5 * u.cm #dimensions of central hole
    c.MuonTagger.HY = 5 * u.cm




