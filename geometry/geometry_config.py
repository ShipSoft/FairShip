import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry

# the following params should be passed through 'ConfigRegistry.loadpy' method
# muShieldDesign = 2  # 1=passive 2=active
# targetOpt      = 5  # 0=solid   >0 sliced, 5 pieces of tungsten, 4 air slits
# strawOpt       = 0  # 0=simplistic tracking stations defined in veto.cxx  1=detailed strawtube design

if "muShieldDesign" not in globals():
    muShieldDesign = 2
if "targetOpt" not in globals():
    targetOpt = 5
if "strawDesign" not in globals():
    strawDesign = 1
with ConfigRegistry.register_config("basic") as c:
    # global muShieldDesign, targetOpt, strawDesign
    extraVesselLength=10*u.m
    c.strawDesign = strawDesign
    c.chambers = AttrDict(z=0*u.cm)
    if strawDesign == 1:
     extraVesselLength=0*u.m
     c.Chamber1 = AttrDict(z=-2450.*u.cm)
     c.Chamber2 = AttrDict(z=-440.*u.cm)
     c.Chamber3 = AttrDict(z=1620.*u.cm)
     c.Chamber4 = AttrDict(z=1940.*u.cm)
     c.Chamber5 = AttrDict(z=2270.*u.cm)
     c.Chamber6 = AttrDict(z=2540.*u.cm)

     c.chambers.Tub1length = AttrDict(z=50.*u.cm)
     c.chambers.Tub2length = AttrDict(z=1940.*u.cm)
     c.chambers.Tub3length = AttrDict(z=70.*u.cm) # -10
     c.chambers.Tub4length = AttrDict(z=190.*u.cm) # -10
     c.chambers.Tub5length = AttrDict(z=80.*u.cm) # -10
     c.chambers.Tub6length = AttrDict(z=20.*u.cm)
     c.chambers.Rmin = AttrDict(z=245.*u.cm)
     c.chambers.Rmax = AttrDict(z=250.*u.cm)

     c.vetoStation = AttrDict(z=-2390.*u.cm)
     c.TrackStation1 = AttrDict(z=1520.*u.cm)
     c.TrackStation2 = AttrDict(z=1715.*u.cm) # -5
     c.TrackStation3 = AttrDict(z=2160.*u.cm)
     c.TrackStation4 = AttrDict(z=2380.*u.cm)
    else:
     c.chambers.Tub1length = AttrDict(z=2.5*u.m)
     c.chambers.Tub2length = AttrDict(z=17.68*u.m+extraVesselLength/2.)
     c.chambers.Tub3length = AttrDict(z=0.8*u.m)
     c.chambers.Tub4length = AttrDict(z=2.*u.m)
     c.chambers.Tub5length = AttrDict(z=0.8*u.m)
     c.chambers.Tub6length = AttrDict(z=0.1*u.m)
     c.chambers.Rmin = AttrDict(z=245.*u.cm)
     c.chambers.Rmax = AttrDict(z=250.*u.cm)
     # positions and lenghts of vacuum tube segments
     c.Chamber1 = AttrDict(z=-22.28*u.m)
     c.Chamber2 = AttrDict(z=-1.9*u.m+extraVesselLength/2.)
     c.Chamber3 = AttrDict(z=16.98*u.m+extraVesselLength)
     c.Chamber4 = AttrDict(z=20.18*u.m+extraVesselLength)
     c.Chamber5 = AttrDict(z=23.38*u.m+extraVesselLength)
     c.Chamber6 = AttrDict(z=24.68*u.m+extraVesselLength)
      # magnet z= 20.18  +extraVesselLength
     c.vetoStation = AttrDict(z=-1968.*u.cm)
     c.TrackStation1 = AttrDict(z=1598.*u.cm+extraVesselLength)
     c.TrackStation2 = AttrDict(z=1798.*u.cm+extraVesselLength)
     c.TrackStation3 = AttrDict(z=2238.*u.cm+extraVesselLength)
     c.TrackStation4 = AttrDict(z=2438.*u.cm+extraVesselLength)

    c.z = c.TrackStation2.z + 0.5 * (c.TrackStation3.z - c.TrackStation2.z)
    c.scintillator = AttrDict(z=0*u.cm)
    c.scintillator.Rmin = AttrDict(z=251.*u.cm)
    c.scintillator.Rmax = AttrDict(z=260.*u.cm)

    c.strawtubes = AttrDict(z=0*u.cm)
    c.strawtubes.StrawLength        = AttrDict(z=250.*u.cm)
    c.strawtubes.InnerStrawDiameter = AttrDict(z=0.94*u.cm)
    c.strawtubes.OuterStrawDiameter = AttrDict(z=0.98*u.cm)
    c.strawtubes.StrawPitch         = AttrDict(z=1.76*u.cm)
    c.strawtubes.DeltazLayer        = AttrDict(z=1.1*u.cm)
    c.strawtubes.DeltazPlane        = AttrDict(z=2.6*u.cm)
    c.strawtubes.StrawsPerLayer     = AttrDict(z=568)
    c.strawtubes.ViewAngle          = AttrDict(z=5)
    c.strawtubes.WireThickness      = AttrDict(z=0.003*u.cm)
    c.strawtubes.DeltazView         = AttrDict(z=10.*u.cm)
    c.strawtubes.VacBox_x           = AttrDict(z=300.*u.cm)
    c.strawtubes.VacBox_y           = AttrDict(z=600.*u.cm)

    c.Bfield = AttrDict(z=c.z)
    c.Bfield.max = 1.5*u.kilogauss  # was 1.15 in EOI

    c.MuonStation0 = AttrDict(z=2600.*u.cm+extraVesselLength)
    c.MuonStation1 = AttrDict(z=2700.*u.cm+extraVesselLength)
    c.MuonStation2 = AttrDict(z=2800.*u.cm+extraVesselLength)
    c.MuonStation3 = AttrDict(z=2900.*u.cm+extraVesselLength)
    
    c.MuonFilter0 = AttrDict(z=2650.*u.cm+extraVesselLength)
    c.MuonFilter1 = AttrDict(z=2750.*u.cm+extraVesselLength)
    c.MuonFilter2 = AttrDict(z=2850.*u.cm+extraVesselLength)

    c.MuonXMax    =  AttrDict(x=300.*u.cm)
    c.MuonYMax    =  AttrDict(y=600.*u.cm)

    c.ActiveThickness = AttrDict(z=0.5*u.cm)
    c.FilterThickness = AttrDict(z=30.*u.cm)


    # target absorber muon shield setup
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
    if muShieldDesign == 3 or muShieldDesign == 4 or muShieldDesign == 5 : 
     c.muShield.length = 2*(c.muShield.dZ0+c.muShield.dZ1+c.muShield.dZ2+c.muShield.dZ3+c.muShield.dZ4+c.muShield.dZ5+c.muShield.dZ6
                         +c.muShield.dZ7+c.muShield.dZ8 ) + c.muShield.LE  # leave some space for nu-tau 

    c.muShield.z  =  -c.decayVolume.length/2.-c.muShield.length/2.

    c.hadronAbsorber              =  AttrDict(z=0*u.cm)
    c.hadronAbsorber.length =  3.00*u.m
    c.hadronAbsorber.z     =  c.muShield.z - c.muShield.length/2. - c.hadronAbsorber.length/2.

    c.target               =  AttrDict(z=0*u.cm)
    c.target.sl            =  1*u.cm  # air slit total length
    c.target.length        =  50*u.cm + c.target.sl * (targetOpt-1) 
    c.target.z             =  c.hadronAbsorber.z - c.hadronAbsorber.length/2. - c.target.length/2.
    c.targetOpt            =  targetOpt 
    # interaction point, start of target
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
    
    #Parameters for Goliath
    c.Goliath = AttrDict(z=0*u.cm)
    c.Goliath.LS = 4.5*u.m
    c.Goliath.TS = 3.6*u.m
    c.Goliath.GapTS = 25*u.cm
    c.Goliath.zC = -c.decayVolume.length/2. - c.tauMS.GapV - c.tauMS.SpectroL - c.Goliath.GapTS - c.Goliath.LS/2

