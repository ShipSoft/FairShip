import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry

# the following params should be passed through 'ConfigRegistry.loadpy' method
# muShieldDesign = 2  # 1=passive 2=active
# targetOpt      = 5  # 0=solid   >0 sliced, 5: 5 pieces of tungsten, 4 air slits, 17: molybdenum tungsten interleaved with H20
# strawOpt       = 0  # 0=simplistic tracking stations defined in veto.cxx  1=detailed strawtube design
if "muShieldDesign" not in globals():
    muShieldDesign = 5
if "targetOpt" not in globals():
    targetOpt = 5
if "strawDesign" not in globals():
    strawDesign = 4
if "HcalOption" not in globals():
    HcalOption = -1
if "Yheight" not in globals():
    Yheight = 10.

with ConfigRegistry.register_config("basic") as c:
    # global muShieldDesign, targetOpt, strawDesign, Yheight
    c.Yheight = Yheight*u.m
    # decision by the SP 
    totalLength       = 2.5*c.Yheight + 35*u.m
    extraVesselLength = totalLength - 50*u.m
    c.strawDesign = strawDesign
    c.chambers = AttrDict(z=0*u.cm)
    if strawDesign != 4:
     print "this design is not supported, use strawDesign = 4"
     1/0 
    else:
     c.chambers.Length = totalLength
     c.chambers.Tub1length = 2.5*u.m
     c.chambers.Tub2length = 17.68*u.m+extraVesselLength/2.
     c.chambers.Tub3length = 0.8*u.m
     c.chambers.Tub4length = 2.*u.m
     c.chambers.Tub5length = 0.8*u.m
     c.chambers.Tub6length = 0.1*u.m
     c.chambers.Rmin = 245.*u.cm
     c.chambers.Rmax = 250.*u.cm
     # positions and lenghts of vacuum tube segments
     c.Chamber1 = AttrDict(z=-22.28*u.m)
     c.Chamber2 = AttrDict(z=-1.9*u.m+extraVesselLength/2.)
     c.Chamber3 = AttrDict(z=16.98*u.m+extraVesselLength)
     c.Chamber4 = AttrDict(z=20.18*u.m+extraVesselLength)
     c.Chamber5 = AttrDict(z=23.38*u.m+extraVesselLength)
     c.Chamber6 = AttrDict(z=24.68*u.m+extraVesselLength)
     # 
     c.vetoStation = AttrDict(z=-1968.*u.cm)
     c.TrackStation1 = AttrDict(z=1598.*u.cm+extraVesselLength)
     c.TrackStation2 = AttrDict(z=1798.*u.cm+extraVesselLength)
     c.TrackStation3 = AttrDict(z=2238.*u.cm+extraVesselLength)
     c.TrackStation4 = AttrDict(z=2438.*u.cm+extraVesselLength)

    c.z = c.TrackStation2.z + 0.5 * (c.TrackStation3.z - c.TrackStation2.z)
    c.scintillator = AttrDict(z=0*u.cm)
    c.scintillator.Rmin = 251.*u.cm
    c.scintillator.Rmax = 260.*u.cm

    c.strawtubes = AttrDict(z=0*u.cm)
    c.strawtubes.StrawLength        = 250.*u.cm
    c.strawtubes.InnerStrawDiameter = 0.94*u.cm
    c.strawtubes.OuterStrawDiameter = 0.98*u.cm
    c.strawtubes.StrawPitch         = 1.76*u.cm
    c.strawtubes.DeltazLayer        = 1.1*u.cm
    c.strawtubes.DeltazPlane        = 2.6*u.cm
    
    c.strawtubes.StrawsPerLayer     = int(c.Yheight/c.strawtubes.StrawPitch)
    c.strawtubes.ViewAngle          = 5
    c.strawtubes.WireThickness      = 0.003*u.cm
    c.strawtubes.DeltazView         = 10.*u.cm
    c.strawtubes.VacBox_x           = 300.*u.cm
    c.strawtubes.VacBox_y           = 600.*u.cm * c.Yheight / (10.*u.m)

    c.Bfield = AttrDict(z=c.z)
    c.Bfield.max = 1.5*u.kilogauss  # was 1.15 in EOI
    c.Bfield.y   = c.Yheight

    c.ecal  =  AttrDict(z=3540*u.cm + totalLength - 60*u.m)
    c.HcalOption  =  HcalOption
    hcalSpace = 0
    hcalThickness = 300*u.cm
    if not HcalOption < 0:
     if HcalOption == 0 : 
          c.hcal  =  AttrDict(z=45*u.cm + totalLength - 60.*u.m ) 
     else:                
          c.hcal  =  AttrDict(z=c.ecal.z + 50*u.cm/2. + hcalThickness/2. + 20.*u.cm )
          hcalSpace = 20.*u.cm + hcalThickness + 5*u.cm 
    c.MuonStation0 = AttrDict(z=2600.*u.cm+extraVesselLength+hcalSpace)
    c.MuonStation1 = AttrDict(z=2700.*u.cm+extraVesselLength+hcalSpace)
    c.MuonStation2 = AttrDict(z=2800.*u.cm+extraVesselLength+hcalSpace)
    c.MuonStation3 = AttrDict(z=2900.*u.cm+extraVesselLength+hcalSpace)
    
    c.MuonFilter0 = AttrDict(z=2650.*u.cm+extraVesselLength+hcalSpace)
    c.MuonFilter1 = AttrDict(z=2750.*u.cm+extraVesselLength+hcalSpace)
    c.MuonFilter2 = AttrDict(z=2850.*u.cm+extraVesselLength+hcalSpace)
     
    c.Muon = AttrDict(z=0)
    c.Muon.XMax    =  300.*u.cm
    c.Muon.YMax    =  600.*u.cm * c.Yheight / (10.*u.m)

    c.Muon.ActiveThickness = 0.5*u.cm
    c.Muon.FilterThickness = 30.*u.cm

    # target absorber muon shield setup, decayVolume.length = nominal EOI length, only kept to define z=0
    c.decayVolume            =  AttrDict(z=0*u.cm)
    c.decayVolume.length     =   50*u.m

    c.muShield             =  AttrDict(z=0*u.cm)
    c.muShieldDesign = muShieldDesign
    # design 4 and 5
    c.muShield.LE  = 10*u.m     #- 0.5 m air - Goliath: 4.5 m - 0.5 m air - nu-tau mu-det: 3 m - 0.5 m air. finally 10m asked by Giovanni
    c.muShield.dZ0 = 1*u.m      #  extra hadron absorber
    c.muShield.dZ1 = 3.5*u.m
    c.muShield.dZ2 = 6.*u.m
    c.muShield.dZ3 = 2.5*u.m
    c.muShield.dZ4 = 3.*u.m
    c.muShield.dZ5 = 0.*u.m     # 28Oct #5 removed
    c.muShield.dZ6 = 3.*u.m
    c.muShield.dZ7 = 3.*u.m
    c.muShield.dZ8 = 3.*u.m
    c.muShield.dXgap = 0.2*u.m

    if muShieldDesign == 3: 
     c.muShield.LE  = 10*u.m     #- 0.5 m air - Goliath: 4.5 m - 0.5 m air - nu-tau mu-det: 3 m - 0.5 m air. finally 10m asked by Giovanni
     c.muShield.dZ0 = 1*u.m      #  extra hadron absorber
     c.muShield.dZ1 = 3.5*u.m
     c.muShield.dZ2 = 5.*u.m
     c.muShield.dZ3 = 3.5*u.m
     c.muShield.dZ4 = 2.0*u.m
     c.muShield.dZ5 = 1.*u.m
     c.muShield.dZ6 = 3.*u.m
     c.muShield.dZ7 = 3.*u.m
     c.muShield.dZ8 = 3.*u.m
     c.muShield.dXgap = 0.2*u.m

    if muShieldDesign == 2: 
     c.muShield.dZ0 = 0*u.m      #  extra hadron absorber
     c.muShield.dZ1 = 2.5*u.m
     c.muShield.dZ2 = 3.5*u.m
     c.muShield.dZ3 = 3.0*u.m
     c.muShield.dZ4 = 3.0*u.m
     c.muShield.dZ5 = 2.5*u.m
     c.muShield.dZ6 = 2.5*u.m
     c.muShield.length = 2*(c.muShield.dZ1+c.muShield.dZ2+c.muShield.dZ3+c.muShield.dZ4+
                         c.muShield.dZ5+c.muShield.dZ6) + c.muShield.LE  # leave some space for nu-tau detector   
    # for passive design, fDesign==1
    if muShieldDesign == 1: 
        c.muShield.length =  70*u.m 
        c.muShield.z  =  -c.decayVolume.length/2.-c.muShield.length/2. - c.muShield.LE  # leave some space for nu-tau 
    if muShieldDesign == 3 or muShieldDesign == 4 or muShieldDesign == 5 : 
     c.muShield.length = 2*(c.muShield.dZ0+c.muShield.dZ1+c.muShield.dZ2+c.muShield.dZ3+c.muShield.dZ4+c.muShield.dZ5+c.muShield.dZ6
                         +c.muShield.dZ7+c.muShield.dZ8 ) + c.muShield.LE  # leave some space for nu-tau 
     c.muShield.z  =  -c.decayVolume.length/2.-c.muShield.length/2.

    c.hadronAbsorber              =  AttrDict(z=0*u.cm)
    c.hadronAbsorber.length =  3.00*u.m
    c.hadronAbsorber.z     =  c.muShield.z - c.muShield.length/2. - c.hadronAbsorber.length/2.

    c.target               =  AttrDict(z=0*u.cm)
    c.targetOpt            =  targetOpt 
    if targetOpt < 10:
     c.target.sl            =  1*u.cm  # air slit total length
     c.target.length        =  50*u.cm + c.target.sl * (targetOpt-1) 
    else:
   #          material,length  
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
     c.target.L14 = 8.*u.cm
     c.target.M15 = "tungsten"
     c.target.L15 = 8.*u.cm
     c.target.M16 = "tungsten"
     c.target.L16 = 10.*u.cm
     c.target.M17 = "tungsten"
     c.target.L17 = 35.*u.cm
     c.target.sl  =  0.5*u.cm  # H20 slit *16 times
     c.target.xy  = 30.*u.cm   # full length in x and y
     c.target.length = 16*c.target.sl + c.target.L1 + 7*c.target.L2 + 2*c.target.L9 + c.target.L11 + 4*c.target.L12 + c.target.L16 + c.target.L17
    # interaction point, start of target
    c.target.z   =  c.hadronAbsorber.z - c.hadronAbsorber.length/2. - c.target.length/2.
    c.target.z0  =  c.target.z - c.target.length/2.

    # straws of tracking stations
    c.straw = AttrDict(z=0*u.cm)
    c.straw.length = 250.*u.cm
    c.straw.resol  = 0.01*u.cm
    c.straw.pitch  = 1.*u.cm
    c.straw.stereoAngle = 5./180.  # degrees

    #Parameters for tau magnetic Spectrometer
    c.tauMS = AttrDict(z=0*u.cm)
    c.tauMS.FeL = 5.*u.cm
    c.tauMS.AirL = 2.*u.cm
    c.tauMS.SpectroL = 4.7*u.m
    c.tauMS.GapV = 27.*u.cm
    c.tauMS.DGap = 95.*u.cm
    c.tauMS.MGap = 120*u.cm
    c.tauMS.zLS = -c.decayVolume.length/2. - c.tauMS.GapV - c.tauMS.DGap - c.tauMS.FeL/2
    c.tauMS.mf = 1.5 * u.tesla

    #Parameters for Goliath
    c.Goliath = AttrDict(z=0*u.cm)
    c.Goliath.LS = 4.5*u.m
    c.Goliath.TS = 3.6*u.m
    c.Goliath.GapTS = 25*u.cm
    c.Goliath.zC = -c.decayVolume.length/2. - c.tauMS.GapV - c.tauMS.SpectroL - c.Goliath.GapTS - c.Goliath.LS/2

    #Parameters for the RPC in tau magnetic Spectrometer
    c.Rpc = AttrDict(z=0*u.cm)
    c.Rpc.DriftL = 15*u.cm
    c.Rpc.IronL = 5.*u.cm
    c.Rpc.ScintL = 2.*u.cm
    c.Rpc.MiddleG = 120*u.cm
    c.Rpc.zRpcL = -c.decayVolume.length/2. - c.tauMS.GapV -c.tauMS.DGap + c.Rpc.ScintL/2
    c.Rpc.zDriftL = -c.decayVolume.length/2. - c.tauMS.GapV - c.Rpc.DriftL/2
