import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry
# the following params should be passed through 'ConfigRegistry.loadpy' method
# none for the moment
with ConfigRegistry.register_config("basic") as c:

    c.MufluxSpectrometer = AttrDict(z = 0*u.cm)  
    # False = charm cross-section; True = muon flux measurement
    c.MufluxSpectrometer.muflux  = False 
    
    if "targetOpt" not in globals():
       targetOpt = 18 # add extra 20cm of tungsten as per 13/06/2017
    
    c.target = AttrDict(z0=0*u.cm)

    c.Bfield = AttrDict(z=0*u.cm)
    c.Bfield.max = 10.*u.kilogauss  # 1.4361*u.kilogauss for SHiP
    c.Bfield.y   = 1.8*u.m # dummy value
    c.Bfield.x   = 5.0*u.m # dummy value
    c.Bfield.z   = 3.571*u.m
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

    c.target.M1 = "molybdenum"
    c.target.L1 = 8.*u.cm
    c.target.M2 = "molybdenum"
    c.target.L2 = 2.5*u.cm
    c.target.M3 = "molybdenum"
    c.target.L3 = 2.5*u.cm
    c.target.M4 = "molybdenum"
    c.target.L4 = 2.5*u.cm
    c.target.M5 = "molybdenum"
    c.target.L5 = 2.5*u.cm
    c.target.M6 = "molybdenum"
    c.target.L6 = 2.5*u.cm
    c.target.M7 = "molybdenum"
    c.target.L7 = 2.5*u.cm
    c.target.M8 = "molybdenum"
    c.target.L8 = 2.5*u.cm
    c.target.M9 = "molybdenum"
    c.target.L9 = 5.0*u.cm
    c.target.M10 = "molybdenum"
    c.target.L10 = 5.0*u.cm
    c.target.M11 = "molybdenum"
    c.target.L11 = 6.5*u.cm
    c.target.M12 = "molybdenum"
    c.target.L12 = 8.*u.cm
    c.target.M13 = "molybdenum"
    c.target.L13 = 8.*u.cm
    c.target.M14 = "tungsten"
    c.target.L14 = 5.*u.cm
    c.target.M15 = "tungsten"
    c.target.L15 = 8.*u.cm
    c.target.M16 = "tungsten"
    c.target.L16 = 10.*u.cm
    c.target.M17 = "tungsten"
    c.target.L17 = 20.*u.cm
    c.target.M18 = "tungsten"
    c.target.L18 = 35.*u.cm
    c.target.sl  =  0.5*u.cm  # H20 slit *17 times
    c.target.xy  = 15.*u.cm   # diameter of muflux target
    c.target.length = 17*c.target.sl + c.target.L1 + 7*c.target.L2 + 3*c.target.L9 + c.target.L11 + 3*c.target.L12 + c.target.L16 + c.target.L17 + c.target.L18
    
    # interaction point, start of target
    c.target.z   =  c.hadronAbsorber.z - c.hadronAbsorber.length/2. - c.target.length/2.
    c.target.z0  =  c.target.z - c.target.length/2.

    #Scintillator
    c.Scintillator = AttrDict(z = 0*u.cm)
    c.Scintillator.Scoring1X           = 200.*u.cm
    c.Scintillator.Scoring1Y           = 200.*u.cm    
    
    
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
    c.MufluxSpectrometer.v_drift = 1./(30*u.ns/u.mm) # for baseline NA62 5mm radius straws)
    c.MufluxSpectrometer.sigma_spatial = 0.030*u.cm # according to Massi's TP section
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
    c.MufluxSpectrometer.ViewAngle          = 5
    c.MufluxSpectrometer.WireThickness      = 0.0045*u.cm
    c.MufluxSpectrometer.DeltazView         = 16.*u.cm
    c.MufluxSpectrometer.VacBox_x           = 205.*u.cm
    c.MufluxSpectrometer.VacBox_y           = 165.*u.cm    
    
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
               
    if c.MufluxSpectrometer.muflux == True: 
       #these parameters are also used inside the MufluxSpectrometer.cxx
       c.Spectrometer.SZ = c.Spectrometer.DZ*6 + 286 *u.cm + 4.5*u.m + 3*u.cm #4.5 m is the Goliath length; 286=6+80+200 Scint SA, T1,2 & T3,4 dist, 3 for SB
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
       c.MuonTagger.zBox = c.Spectrometer.SZ+ c.MuonTagger.BZ*3./2. + c.Box.PZ + 5*u.cm -250*u.cm
    else:    
       c.MuonTagger.zBox = c.Spectrometer.SZ+ c.MuonTagger.BZ/2 + c.Box.PZ + 5*u.cm

    c.MuonTagger.PX = c.MuonTagger.BX
    c.MuonTagger.PY = c.MuonTagger.BY
    c.MuonTagger.SX = c.MuonTagger.BX
    c.MuonTagger.SY = c.MuonTagger.BY
