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

    if "cTarget" not in globals():
      cTarget = 3

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
    #c.MufluxTargetStation.floorRPC_y=32.5*u.cm
    #c.MufluxTargetStation.floorRPC_z=110.*u.cm   
    c.MufluxTargetStation.floorRPC_y=42.5*u.cm
    c.MufluxTargetStation.floorRPC_z=175.*u.cm  
    
    #BOX (Brick!)
    c.Box = AttrDict(z=0*u.cm)
    c.Box.zBox = 106.66 * u.cm
    c.Box.EmTh = 0.0070 * u.cm
    c.Box.EmX = 12.5 * u.cm
    c.Box.EmY = 9.9 * u.cm
    c.Box.PBTh = 0.0175 * u.cm
    if cTarget == 16:
     c.Box.PasSlabTh = 0.09 * u.cm #passive slab in ECC (run with tungsten)
    else:
     c.Box.PasSlabTh = 0.1 * u.cm #passive slab in ECC (lead for July 2018 measurement, molybdenum/tungsten for SHiP target replica)
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

    #Distance between passive bricks and ECC brick
    c.Box.distancePassive2ECC = 3.0 *u.cm


    #OPTIONS FOR CHARM XSEC DETECTOR
    c.Box.gausbeam = True
    c.Box.Julytarget = True
    c.Box.GapPostTargetTh = 0.73 * u.cm #distance between end of the emulsion target and start of pixel box (Pixel origin)     
    c.Box.RunNumber =  cTarget #run configuration for charm

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
    
    #PixelModules

    c.PixelModules = AttrDict(z = 0*u.cm)

    #Spectrometer
    c.Spectrometer = AttrDict(z = 0*u.cm)
    #Parameters for Goliath by Annarita
    c.Spectrometer.LS = 4.5*u.m
    c.Spectrometer.TS = 3.6*u.m
    #c.Spectrometer.CoilR = 1.*u.m
    c.Spectrometer.CoilR = 1.6458*u.m
    c.Spectrometer.UpCoilH = 45*u.cm
    c.Spectrometer.LowCoilH = 30*u.cm
    #c.Spectrometer.CoilD = 105*u.cm
    c.Spectrometer.CoilD = 103.5575*u.cm
    #c.Spectrometer.BasisH = 57*u.cm
    c.Spectrometer.BasisH = 50.22125*u.cm
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
    c.MufluxSpectrometer.TubePitch_T1u       = 0.0009765*u.cm
    #c.MufluxSpectrometer.T1u_const           = -0.008655*u.cm  
    c.MufluxSpectrometer.T1u_const           = 0.001343*u.cm  
    c.MufluxSpectrometer.T1u_const_2           = 0.00183*u.cm    
    c.MufluxSpectrometer.T1u_const_3           = 0.001575*u.cm  
    c.MufluxSpectrometer.T1u_const_4           = 0.0010859*u.cm  
    c.MufluxSpectrometer.T2v_const           = 3.100985*u.cm  
    c.MufluxSpectrometer.T2v_const_2           = -1.09986*u.cm    
    c.MufluxSpectrometer.T2v_const_3           = -1.100305*u.cm  
    c.MufluxSpectrometer.T2v_const_4           = 3.100543*u.cm  
    c.MufluxSpectrometer.TubePitch_T2v       = 0.001695*u.cm 
    c.MufluxSpectrometer.DeltazLayer        = 3.64*u.cm
    c.MufluxSpectrometer.DeltazPlane        = 7.7*u.cm
    
    c.MufluxSpectrometer.TubesPerLayer      = 12
    c.MufluxSpectrometer.ViewAngle          = 60.2
    c.MufluxSpectrometer.ViewvAngle         = -60.
    c.MufluxSpectrometer.WireThickness      = 0.0045*u.cm
    c.MufluxSpectrometer.DeltazView         = 15.14*u.cm
    
    c.MufluxSpectrometer.diststereoT1       = 16.08*u.cm  
    c.MufluxSpectrometer.diststereoT2       = 16.27*u.cm        
    c.MufluxSpectrometer.distT1T2           = 11.*u.cm   
    if c.MufluxSpectrometer.muflux == True:
       c.MufluxSpectrometer.distT3T4           = 1.6*u.m       
    else:
       c.MufluxSpectrometer.distT3T4 = 1.0*u.m   
            
    #c.MufluxSpectrometer.goliathcentre_to_beam = 178.6*u.mm
    #from edms 1825777 + cumer email
    c.MufluxSpectrometer.goliathcentre_to_beam = 17.32*u.cm + (c.Spectrometer.UpCoilH-c.Spectrometer.LowCoilH)/2.
    c.MufluxSpectrometer.goliathcentre = 351.19*u.cm  
      
    c.MufluxSpectrometer.T1x_x=4.22*u.cm
    c.MufluxSpectrometer.T1x_y=-1.995*u.cm
    c.MufluxSpectrometer.T1x_z=0.*u.cm
    c.MufluxSpectrometer.T1z=40.13*u.cm
    c.MufluxSpectrometer.T1u_x=7.8*u.cm    
    c.MufluxSpectrometer.T1u_y=-0.16*u.cm
    c.MufluxSpectrometer.T1u_z=-0.00175*u.cm    
    c.MufluxSpectrometer.T2x_x=2.43*u.cm
    c.MufluxSpectrometer.T2x_y=-2.1875*u.cm  
    c.MufluxSpectrometer.T2x_z=-0.01074*u.cm  
    c.MufluxSpectrometer.T2z=108.822745*u.cm            
    c.MufluxSpectrometer.T2v_x=3.5*u.cm      
    c.MufluxSpectrometer.T2v_y=0.09*u.cm   
    c.MufluxSpectrometer.T2v_z=0.*u.cm        
    c.MufluxSpectrometer.T3x=2.475*u.cm
    c.MufluxSpectrometer.T3y=-7.3405*u.cm
    c.MufluxSpectrometer.T3z=585.18*u.cm      # plus 7cm offset + 5mm ad hoc
    c.MufluxSpectrometer.T3z_1=0.1350*u.cm   
    c.MufluxSpectrometer.T3z_2=-0.06250*u.cm    
    c.MufluxSpectrometer.T3z_3=-0.1150*u.cm   
    c.MufluxSpectrometer.T3z_4=-0.100*u.cm   
    c.MufluxSpectrometer.T3x_1=-0.13250*u.cm   
    c.MufluxSpectrometer.T3x_2=-0.014*u.cm    
    c.MufluxSpectrometer.T3x_3=0.1120*u.cm   
    c.MufluxSpectrometer.T3x_4=0.1270*u.cm             
    c.MufluxSpectrometer.T4x=2.95*u.cm   
    c.MufluxSpectrometer.T4y=-6.9845*u.cm 
    c.MufluxSpectrometer.T4z=748.32*u.cm      # min 7cm offset +5mm ad hoc  
    c.MufluxSpectrometer.T4z_1=0.1125*u.cm   
    c.MufluxSpectrometer.T4z_2=-0.050*u.cm    
    c.MufluxSpectrometer.T4z_3=-0.12250*u.cm   
    c.MufluxSpectrometer.T4z_4=-0.05250*u.cm 
    c.MufluxSpectrometer.T4x_1=-0.030*u.cm   
    c.MufluxSpectrometer.T4x_2=0.04250*u.cm    
    c.MufluxSpectrometer.T4x_3=-0.00750*u.cm   
    c.MufluxSpectrometer.T4x_4=-0.010*u.cm               
    
    if c.MufluxSpectrometer.muflux == True:    
       c.Spectrometer.DX = 2.*u.m
       c.Spectrometer.DY = 1.6*u.m   
       c.Spectrometer.DZ = 16.*u.cm
    else:        
       c.Spectrometer.DX = 1*u.m
       c.Spectrometer.DY = 0.5*u.m
       c.Spectrometer.DZ = 13.5 * u.cm
       c.PixelModules.DX = 1*u.m
       c.PixelModules.DY = 0.5*u.m
       c.PixelModules.DZ = 13.5 * u.cm
       
    c.MufluxSpectrometer.DX = 2.*u.m
    c.MufluxSpectrometer.DY = 1.6*u.m
    c.MufluxSpectrometer.DZ = 11.72*u.cm

    #Adding survey results for charm measurement (Daniel) 
    
    c.MufluxSpectrometer.SurveyCharm_T3ax = 876.075*u.mm 
    c.MufluxSpectrometer.SurveyCharm_T3ay = 101.6*u.mm
    c.MufluxSpectrometer.SurveyCharm_T3az = 15269*u.mm+70*u.mm-8896.09*u.mm #todo: check th 70mm (probably forgt bolt and alignement sphere before)
    c.MufluxSpectrometer.SurveyCharm_T3bx = 372.1*u.mm
    c.MufluxSpectrometer.SurveyCharm_T3by = 98.875*u.mm
    c.MufluxSpectrometer.SurveyCharm_T3bz = 15338.475*u.mm-8896.09*u.mm
    c.MufluxSpectrometer.SurveyCharm_T3cx = -323.425*u.mm
    c.MufluxSpectrometer.SurveyCharm_T3cy = 97.85*u.mm
    c.MufluxSpectrometer.SurveyCharm_T3cz = 15337.625*u.mm-8896.09*u.mm
    c.MufluxSpectrometer.SurveyCharm_T3dx = -829.3*u.mm
    c.MufluxSpectrometer.SurveyCharm_T3dy = 97.7*u.mm
    c.MufluxSpectrometer.SurveyCharm_T3dz = 15337.6*u.mm-8896.09*u.mm

    c.MufluxSpectrometer.SurveyCharm_T3tx = 13.8*u.mm
    c.MufluxSpectrometer.SurveyCharm_T3ty = 649.85*u.mm
    c.MufluxSpectrometer.SurveyCharm_T3tz = 15606.1*u.mm-8896.09*u.mm

    c.MufluxSpectrometer.SurveyCharm_T4ax = 886.15*u.mm
    c.MufluxSpectrometer.SurveyCharm_T4ay = 105.35*u.mm
    c.MufluxSpectrometer.SurveyCharm_T4az = 16572.225*u.mm-200*u.mm-8896.09*u.mm #-200 mm because of wrong sign in first calcualtion
    c.MufluxSpectrometer.SurveyCharm_T4bx = 351.9*u.mm
    c.MufluxSpectrometer.SurveyCharm_T4by = 102.45*u.mm
    c.MufluxSpectrometer.SurveyCharm_T4bz = 16570.8*u.mm-200*u.mm-8896.09*u.mm
    c.MufluxSpectrometer.SurveyCharm_T4cx = -341.575*u.mm
    c.MufluxSpectrometer.SurveyCharm_T4cy = 100.225*u.mm
    c.MufluxSpectrometer.SurveyCharm_T4cz = 16571.625*u.mm-200*u.mm-8896.09*u.mm
    c.MufluxSpectrometer.SurveyCharm_T4dx = -845.8*u.mm
    c.MufluxSpectrometer.SurveyCharm_T4dy = 99.05*u.mm
    c.MufluxSpectrometer.SurveyCharm_T4dz = 16571.3*u.mm-200*u.mm-8896.09*u.mm

    c.MufluxSpectrometer.SurveyCharm_T4tx = 13.6*u.mm
    c.MufluxSpectrometer.SurveyCharm_T4ty = 675*u.mm
    c.MufluxSpectrometer.SurveyCharm_T4tz = 16102.45*u.mm-8896.09*u.mm
    
    #These parameters are used only by the charm detector ---   
    c.Spectrometer.D1Short = 3.36 * u.cm / 2.;
    c.Spectrometer.D1Long = 4 * u.cm;
    c.Spectrometer.SX = c.Spectrometer.DX
    c.Spectrometer.SY = c.Spectrometer.DY
    c.PixelModules.DimZSi = 0.0400 * u.cm
    c.PixelModules.D1short = 3.36 * u.cm / 2.
    c.PixelModules.D1long = 4.09 * u.cm


    #position of module centres units are cm. Geometry is given with reference to the centre of all modules for the xy plane and the front of the pixel box for the z axis, precision is given to the micron range
    #module position naming: "axis"Si"Telescope number"
    
		#measured values
    c.PixelModules.xSi = []
    c.PixelModules.ySi = []
    c.PixelModules.zSi = []
    #Module 0
    c.PixelModules.xSi.append(1.5391*u.cm)
    c.PixelModules.ySi.append(0.0011*u.cm)
    c.PixelModules.zSi.append(-0.13*u.cm)
    #Module 1
    c.PixelModules.xSi.append(-0.2291*u.cm)
    c.PixelModules.ySi.append(0.0036*u.cm)
    c.PixelModules.zSi.append(0.52*u.cm)
    #Module 2 (half with positive x values did not work)
    c.PixelModules.xSi.append(0.7049*u.cm)
    c.PixelModules.ySi.append(-0.7855*u.cm)
    c.PixelModules.zSi.append(2.412*u.cm)
    #Module 3
    c.PixelModules.xSi.append(0.7054*u.cm)
    c.PixelModules.ySi.append(0.9086*u.cm)
    c.PixelModules.zSi.append(3.09*u.cm)
    #Module 4
    c.PixelModules.xSi.append(1.5496*u.cm)
    c.PixelModules.ySi.append(0.0528*u.cm)
    c.PixelModules.zSi.append(5.17*u.cm)
    #Module 5
    c.PixelModules.xSi.append(-0.2216*u.cm)
    c.PixelModules.ySi.append(0.0790*u.cm)
    c.PixelModules.zSi.append(5.79*u.cm)
    #Module 6
    c.PixelModules.xSi.append(0.6908*u.cm)
    c.PixelModules.ySi.append(-0.6959*u.cm)
    c.PixelModules.zSi.append(7.77*u.cm)
    #Module 7
    c.PixelModules.xSi.append(0.7023*u.cm)
    c.PixelModules.ySi.append(0.9547*u.cm)
    c.PixelModules.zSi.append(8.46*u.cm)
    #Module 8
    c.PixelModules.xSi.append(1.5827*u.cm)
    c.PixelModules.ySi.append(0.1024*u.cm)
    c.PixelModules.zSi.append(10.462*u.cm)
    #Module 9
    c.PixelModules.xSi.append(-0.2092*u.cm)
    c.PixelModules.ySi.append(0.1036*u.cm)
    c.PixelModules.zSi.append(11.17*u.cm)
    #Module 10
    c.PixelModules.xSi.append(0.6942*u.cm)
    c.PixelModules.ySi.append(-0.7252*u.cm)
    c.PixelModules.zSi.append(13.162*u.cm)
    #Module 11
    c.PixelModules.xSi.append(0.6832*u.cm)
    c.PixelModules.ySi.append(0.9279*u.cm)
    c.PixelModules.zSi.append(13.85*u.cm)

    #SciFi Modules
    c.SciFi = AttrDict(z = 0*u.cm)
    #mother volume dimensions
    c.SciFi.DX = 50*u.cm 
    c.SciFi.DY = 50*u.cm
    c.SciFi.DZ = 28.07 * u.cm #as difference between positions of SF_DHBR and x of SF_UHTL in the Survey document

    c.SciFi.nstations = 8  #number of stations (currently sensitive volumes)
    #dimensions of each station
    c.SciFi.StationDimX = 40 * u.cm
    c.SciFi.StationDimY = 40 * u.cm
    c.SciFi.StationDimZ = 0.0200 * u.cm
    #SciFi position values (referred to the start of SciFi mother volume)
    c.SciFi.xSi = []
    c.SciFi.ySi = []
    c.SciFi.zSi = []
    zscifigap = c.SciFi.DZ/c.SciFi.nstations - c.SciFi.StationDimZ #distance between center of two stations, for the moment equally spaced
    #Module 0
    c.SciFi.xSi.append(0.)
    c.SciFi.ySi.append(0.)
    c.SciFi.zSi.append(c.SciFi.StationDimZ/2)
    #Module 1
    c.SciFi.xSi.append(0.0)
    c.SciFi.ySi.append(0.0)
    c.SciFi.zSi.append(c.SciFi.StationDimZ/2 + zscifigap)
    #Module 2
    c.SciFi.xSi.append(0.0)
    c.SciFi.ySi.append(0.0)
    c.SciFi.zSi.append(c.SciFi.StationDimZ/2 + 2* zscifigap)
    #Module 3
    c.SciFi.xSi.append(0.0)
    c.SciFi.ySi.append(0.0)
    c.SciFi.zSi.append(c.SciFi.StationDimZ/2 + 3*zscifigap)
    #Module 4
    c.SciFi.xSi.append(0.0)
    c.SciFi.ySi.append(0.0)
    c.SciFi.zSi.append(c.SciFi.StationDimZ/2 + 4*zscifigap)
    #Module 5
    c.SciFi.xSi.append(0.0)
    c.SciFi.ySi.append(0.0)
    c.SciFi.zSi.append(c.SciFi.StationDimZ/2 + 5*zscifigap)
    #Module 6
    c.SciFi.xSi.append(0.0)
    c.SciFi.ySi.append(0.0)
    c.SciFi.zSi.append(c.SciFi.StationDimZ/2 + 6*zscifigap)
    #Module 7
    c.SciFi.xSi.append(0.0)
    c.SciFi.ySi.append(0.0)
    c.SciFi.zSi.append(c.SciFi.StationDimZ/2 + 7*zscifigap)

    c.Spectrometer.Bvalue = 1 * u.tesla;

    #-------------------------------------------------------
            
    
    #Scintillator
    c.Scintillator = AttrDict(z = 0*u.cm)
    c.Scintillator.Scoring1X           = 55.*u.cm
    c.Scintillator.Scoring1Y           = 110.*u.cm    
    c.Scintillator.DistT1              = 11.5*u.cm       
    #c.Scintillator.DistT2              = 135.25*u.cm
    c.Scintillator.DistT2              = 136.26*u.cm 
                  
    c.Spectrometer.SZ = c.Spectrometer.DZ*2 + c.PixelModules.zSi[11] - c.PixelModules.zSi[0] + c.PixelModules.DimZSi + 80 *u.cm + 4.5*u.m #4.5 m is the Goliath length
   
    c.PixelModules.DimZpixelbox = c.PixelModules.zSi[11] - c.PixelModules.zSi[0] + c.PixelModules.DimZSi    

    PixeltoGoliath = 30.45 *u.cm #25.45 + 5cm different goliath dz
    c.Spectrometer.zBox = 350.75 - c.Spectrometer.TS/2 - PixeltoGoliath - c.PixelModules.DimZpixelbox/2.
    #position of mother volumes
    c.Box.zBox = c.Spectrometer.zBox - c.PixelModules.DimZpixelbox/2. - c.Box.GapPostTargetTh
    c.PixelModules.zBox = c.Spectrometer.zBox
    PixelToSciFi = 469.05 #position of SciFi center defined with respect to distance to start of PixelBox, point PIXEL_UR-Measured in the survey document
    c.SciFi.zBox = c.PixelModules.zBox - c.PixelModules.DimZpixelbox/2.  + 469.05

#   Need to add SciFi
    #Muon Filter
    
    c.MuonTagger = AttrDict(z = 0*u.cm)
    c.MuonTagger.PTh = 80 * u.cm;
    c.MuonTagger.PTh1 = 40 * u.cm #last 3 slabs' thickness
    c.MuonTagger.STh = 15.0 * u.cm
    
    #from survey relative to center of RPC system (18.569225 + 0.00326706 ad hoc, iron blocks were measured by hand in survey coords)
    #from survey to FairShip: subtract 8.89608294 m
          
    #from survey 
    c.MuonTagger.RPC1z = -88.160794 * u.cm
    c.MuonTagger.RPC2z = 6.799206 * u.cm  
    c.MuonTagger.RPC3z = 62.194206 * u.cm
    c.MuonTagger.RPC4z = 117.309206 * u.cm   
    c.MuonTagger.RPC5z = 172.119206 * u.cm  
             
    c.MuonTagger.RPCthickness = 8. * u.cm
    c.MuonTagger.VStripx =  0.8625 * u.cm
    c.MuonTagger.VStripx_L =  0.9625 * u.cm    
    c.MuonTagger.VStripx_R =  0.86 * u.cm 
    c.MuonTagger.HStripy =  0.8625 * u.cm 
    c.MuonTagger.HStripy_ext =  0.3 * u.cm   
    c.MuonTagger.Stripfoamz =  0.6 * u.cm       
    c.MuonTagger.Stripz =  0.003 * u.cm # same as ground plane thickness
    c.MuonTagger.HStripoffset = 0.1983 * u.cm
    c.MuonTagger.VStripoffset = 0.2 * u.cm              
    c.MuonTagger.Gapthickness =  0.2 * u.cm
    c.MuonTagger.Electrodethickness =  0.275 * u.cm  
    c.MuonTagger.NVstrips =  184
    c.MuonTagger.NHstrips =  116         
      
      
                
    c.MuonTagger.BX = 2.0 *u.m
    c.MuonTagger.BY = 1.3 * u.m
    #c.MuonTagger.BX = 195.5 * u.cm
    #c.MuonTagger.BY = 125. * u.cm
    #c.MuonTagger.BZ = c.MuonTagger.PTh * 2 + c.MuonTagger.PTh1 * 3 + c.MuonTagger.STh * 5
    #length of muon tagger from survey (260.475) + half of first rpc space (7.5) + first wall (80cm) + half of last rpc (4)
    # half length 175.9875
    #c.MuonTagger.BZ = 347.3551 * u.cm + 9. * u.cm
    c.MuonTagger.BZ = 352.301706 * u.cm 
    #c.MuonTagger.BZ = 351.975 * u.cm 
    
    if c.MufluxSpectrometer.muflux == True:
       #for the muflux measurement the muontagger has to be moved back 791.75 measured by hand, 173.6775=347.3551/2
       #c.MuonTagger.zBox = 791.*u.cm  + 173.67755*u.cm
       c.MuonTagger.zBox = 791.*u.cm  + 175.9875*u.cm
    else:    
       c.MuonTagger.zBox = c.Spectrometer.zBox + c.PixelModules.DimZpixelbox/2. + PixeltoGoliath + c.Spectrometer.TS + 261*u.cm + c.MuonTagger.BZ/2. #real position of MuonTagger

    c.MuonTagger.PX = c.MuonTagger.BX
    c.MuonTagger.PY = c.MuonTagger.BY
    c.MuonTagger.SX = 195.3975 * u.cm
    c.MuonTagger.SY = 121.7295 * u.cm
    c.MuonTagger.HX = 5 * u.cm #dimensions of central hole
    c.MuonTagger.HY = 5 * u.cm




