import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry
# the following params should be passed through 'ConfigRegistry.loadpy' method
# none for the moment
with ConfigRegistry.register_config("basic") as c:

    c.MufluxSpectrometer = AttrDict(z = 0*u.cm)  
    # False = charm cross-section; True = muon flux measurement
    c.MufluxSpectrometer.muflux  = True 
    
    if "targetOpt" not in globals():
       targetOpt = 18 # add extra 20cm of tungsten as per 13/06/2017
    
    c.target = AttrDict(z0=0*u.cm)

    #BOX (Brick!)
    c.Box = AttrDict(z=0*u.cm)
    c.Box.BX = 13*u.cm
    c.Box.BY = 11*u.cm
    c.Box.BZ = 20*u.cm
    c.Box.zBox = 0 * u.cm
    c.Box.EmTh = 0.0045 * u.cm
    c.Box.EmX = 10 * u.cm #for the moment, replace the previous values for normal simulations
    c.Box.EmY = 10 * u.cm
    c.Box.PBTh = 0.0205 * u.cm
    c.Box.MolybdenumTh = 0.3 * u.cm
    c.Box.EPlW = 2* c.Box.EmTh + c.Box.PBTh
    c.Box.AllPW = c.Box.MolybdenumTh + c.Box.EPlW
    c.Box.BrX = 12.9 *u.cm
    c.Box.BrY = 10.5 *u.cm
    c.Box.BrPackZ = 0.1 * u.cm
    c.Box.BrPackX = c.Box.BrX - c.Box.EmX
    c.Box.BrPackY = c.Box.BrY - c.Box.EmY
    c.Box.BrZ = 54 * c.Box.AllPW + c.Box.EPlW +c.Box.BrPackZ
    c.Box.PX = 0*u.cm	
    c.Box.PY = 0*u.cm
    c.Box.PZ = 0*u.cm #(variables for the old brick configuration)
    c.Box.CoolX = 10 * u.cm #has this to change to adapt it at SHiP target trasversal dimensions?
    c.Box.CoolY = 10 * u.cm
    c.Box.CoolZ = 0.5 * u.cm
    c.Box.CoatX = 10 * u.cm #has this to change to adapt it at SHiP target trasversal dimensions?
    c.Box.CoatY = 10 * u.cm
    c.Box.CoatZ = 0.1 * u.cm
    c.Box.TX = 10 * u.cm
    c.Box.TY = 10 * u.cm

    #to change the run, uncheck the corresponding TZ and Checkmin 
    c.Box.TZ = 15.282 * u.cm #Run 1
    c.Box.Checkmin = -1000 *u.cm
    #c.Box.TZ = 30.388 *u.cm # Run 2
    #c.Box.Checkmin = -15.8 *u.cm
    #c.Box.TZ = 49.01 *u.cm # Run 3
    #c.Box.Checkmin= -14.6 * u.cm 
    #c.Box.TZ = 65.752 *u.cm # Run 4
    #c.Box.Checkmin = -18.2 * u.cm
    #c.Box.TZ = 79.369 *u.cm # Run 5
    #c.Box.Checkmin = -14.6 * u.cm 
    #c.Box.TZ = 90.103 *u.cm # Run 6
    #c.Box.Checkmin = -11.6 *u.cm
    #c.Box.TZ = 98.785 *u.cm # Run 7
    #c.Box.Checkmin = -9.8 *u.cm
    #c.Box.TZ = 107.335 *u.cm # Run 8
    #c.Box.Checkmin = -9.5 *u.cm
    #c.Box.TZ = 116.200 *u.cm # Run 9
    #c.Box.Checkmin = -9.7 *u.cm 
    #c.Box.TZ = 124.935 *u.cm # Run 10 
    #c.Box.Checkmin = -9.7 *u.cm 
  
    #c.Box.TZ = 136 *u.cm # All target sensitive 
    c.Box.Checkmax = 0
    
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
    c.target.sl  =  0.5*u.cm  # H20 slit *17 times
    #c.target.xy  = 15.*u.cm   # diameter of muflux target
    c.target.xy  = 10.*u.cm   # new diameter of muflux target    
    # 5.0 cm is for front and endcaps
    c.target.length = 17*c.target.sl + c.target.L1 + 7*c.target.L2 + 3*c.target.L9 + c.target.L11 + 3*c.target.L12 + c.target.L16 + c.target.L17 + c.target.L18 + 5.0*u.cm
    
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
    #c.MufluxSpectrometer.v_drift = 1./(30*u.ns/u.mm) # for baseline NA62 5mm radius straws)
    c.MufluxSpectrometer.v_drift = 1./(72*u.ns/u.mm) # 1300 ns max for 36.3 mm drifttubes
    c.MufluxSpectrometer.sigma_spatial = 0.027*u.cm # from Daniel 8feb2018
    #c.MufluxSpectrometer.sigma_spatial = 0.035*u.cm # 25% worse   
    c.MufluxSpectrometer.TubeLength         = 160.*u.cm
    c.MufluxSpectrometer.TubeLength12       = 100.*u.cm    
    c.MufluxSpectrometer.tr12ydim           = 100.*u.cm
    c.MufluxSpectrometer.tr34xdim           = 200.*u.cm
    c.MufluxSpectrometer.tr12xdim           = 50.*u.cm
    c.MufluxSpectrometer.tr34ydim           = 160.*u.cm
    
    # parameters for drift tubes
    c.MufluxSpectrometer.InnerTubeDiameter  = 3.63*u.cm 
    c.MufluxSpectrometer.WallThickness      = 0.085*u.cm
    c.MufluxSpectrometer.OuterTubeDiameter  = (c.MufluxSpectrometer.InnerTubeDiameter + 2*c.MufluxSpectrometer.WallThickness)

    c.MufluxSpectrometer.TubePitch          = 4.2*u.cm
    c.MufluxSpectrometer.DeltazLayer        = 3.8*u.cm
    c.MufluxSpectrometer.DeltazPlane        = 8.*u.cm
    
    c.MufluxSpectrometer.TubesPerLayer      = 12
    c.MufluxSpectrometer.ViewAngle          = 60
    c.MufluxSpectrometer.WireThickness      = 0.0045*u.cm
    c.MufluxSpectrometer.DeltazView         = 16.*u.cm
    
    c.MufluxSpectrometer.diststereo         = 16.*u.cm  
    c.MufluxSpectrometer.distT1T2           = 11.*u.cm   
    c.MufluxSpectrometer.distT3T4           = 1.6*u.m       
        
    if c.MufluxSpectrometer.muflux == True:    
       c.Spectrometer.DX = 2.*u.m
       c.Spectrometer.DY = 1.6*u.m   
       c.Spectrometer.DZ = 16.*u.cm
    else:        
       c.Spectrometer.DX = 1*u.m
       c.Spectrometer.DY = 0.5*u.m
       c.Spectrometer.DZ = 2*u.cm    
       
    c.Spectrometer.SX = c.Spectrometer.DX
    c.Spectrometer.SY = c.Spectrometer.DY
    
    #Scintillator
    c.Scintillator = AttrDict(z = 0*u.cm)
    c.Scintillator.Scoring1X           = 55.*u.cm
    c.Scintillator.Scoring1Y           = 110.*u.cm    
    c.Scintillator.DistT1               = 3.7*u.cm       
    c.Scintillator.DistT2               = 2*(2*c.Spectrometer.DZ +c.MufluxSpectrometer.diststereo) + c.MufluxSpectrometer.distT1T2 + 10*u.cm
                   
    if c.MufluxSpectrometer.muflux == True: 
       #these parameters are also used inside the MufluxSpectrometer.cxx
       c.Spectrometer.SZ = 2*(2*c.Spectrometer.DZ +c.MufluxSpectrometer.diststereo) + c.MufluxSpectrometer.distT1T2 +4.5*u.m + c.MufluxSpectrometer.distT3T4 + 2*(2*c.Spectrometer.DZ) + 2.5*u.cm
    else: 
       c.Spectrometer.SZ = c.Spectrometer.DZ*4 + 40 *u.cm + 4.5*u.m #4.5 m is the Goliath length
 
    c.Spectrometer.zBox = c.Box.PZ + c.Spectrometer.SZ/2 + 0.1 * u.cm        
    
    #Muon Filter
    
    c.MuonTagger = AttrDict(z = 0*u.cm)
    c.MuonTagger.PTh = 34 * u.cm;
    c.MuonTagger.STh = 5.0 * u.cm
    c.MuonTagger.BX = 2 * u.m
    c.MuonTagger.BY = 1.5 * u.m
    c.MuonTagger.BZ = c.MuonTagger.PTh * 5 + c.MuonTagger.STh * 6
    
    if c.MufluxSpectrometer.muflux == True:
       #for the muflux measurement the muontagger has to be moved back
       c.MuonTagger.zBox = c.Spectrometer.SZ+ c.MuonTagger.BZ*3./2. + c.Box.PZ + 5*u.cm -310*u.cm
    else:    
       c.MuonTagger.zBox = c.Spectrometer.SZ+ c.MuonTagger.BZ/2 + c.Box.PZ + 5*u.cm

    c.MuonTagger.PX = c.MuonTagger.BX
    c.MuonTagger.PY = c.MuonTagger.BY
    c.MuonTagger.SX = c.MuonTagger.BX
    c.MuonTagger.SY = c.MuonTagger.BY
