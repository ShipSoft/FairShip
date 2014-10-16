import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry

# the following params should be passed through 'ConfigRegistry.loadpy' method
# muShieldDesign = 2  # 1=passive 2=active
# targetOpt      = 5  # 0=solid   >0 sliced, 5 pieces of tungsten, 4 air slits

if "muShieldDesign" not in globals():
    muShieldDesign = 2
if "targetOpt" not in globals():
    targetOpt = 5

with ConfigRegistry.register_config("basic") as c:
    # global muShieldDesign, targetOpt

    c.Chamber1 = AttrDict(z=-2450.*u.cm)
    c.Chamber2 = AttrDict(z=-440.*u.cm)
    c.Chamber3 = AttrDict(z=1620.*u.cm)
    c.Chamber4 = AttrDict(z=1940.*u.cm)
    c.Chamber5 = AttrDict(z=2270.*u.cm)
    c.Chamber6 = AttrDict(z=2540.*u.cm)

    c.chambers = AttrDict(z=0*u.cm)
    c.chambers.Tub1length = AttrDict(z=50.*u.cm)
    c.chambers.Tub2length = AttrDict(z=1940.*u.cm)
    c.chambers.Tub3length = AttrDict(z=80.*u.cm)
    c.chambers.Tub4length = AttrDict(z=200.*u.cm)
    c.chambers.Tub5length = AttrDict(z=90.*u.cm)
    c.chambers.Tub6length = AttrDict(z=20.*u.cm)
    c.chambers.Rmin = AttrDict(z=245.*u.cm)
    c.chambers.Rmax = AttrDict(z=250.*u.cm)

    c.vetoStation = AttrDict(z=-2390.*u.cm)
    c.TrackStation1 = AttrDict(z=1520.*u.cm)
    c.TrackStation2 = AttrDict(z=1720.*u.cm)
    c.TrackStation3 = AttrDict(z=2160.*u.cm)
    c.TrackStation4 = AttrDict(z=2380.*u.cm)

    c.z = c.TrackStation2.z + 0.5 * (c.TrackStation3.z - c.TrackStation2.z)

    c.strawtubes = AttrDict(z=0*u.cm)
    c.strawtubes.StrawLength        = AttrDict(z=250.*u.cm)
    c.strawtubes.InnerStrawDiameter = AttrDict(z=0.94*u.cm)
    c.strawtubes.OuterStrawDiameter = AttrDict(z=0.98*u.cm)
    c.strawtubes.StrawPitch         = AttrDict(z=1.76*u.cm)
    c.strawtubes.DeltazLayer        = AttrDict(z=1.1*u.cm)
    c.strawtubes.DeltazPlane        = AttrDict(z=2.6*u.cm)
    c.strawtubes.StrawsPerLayer     = AttrDict(z=284)
    c.strawtubes.ViewAngle          = AttrDict(z=5)
    c.strawtubes.WireThickness      = AttrDict(z=0.003*u.cm)
    c.strawtubes.DeltazView         = AttrDict(z=10.*u.cm)
    c.strawtubes.VacBox_x           = AttrDict(z=300.*u.cm)
    c.strawtubes.VacBox_y           = AttrDict(z=300.*u.cm)

    c.Bfield = AttrDict(z=c.z)
    c.Bfield.max = 1.5*u.kilogauss  # was 1.15 in EOI

    # target absorber muon shield setup
    c.decayVolume                 =  AttrDict(z=0*u.cm)
    c.decayVolume.length     =   50*u.m

    c.muShield             =  AttrDict(z=0*u.cm)
    c.muShield.dZ1 = 2.5*u.m
    c.muShield.dZ2 = 3.5*u.m
    c.muShield.dZ3 = 3.0*u.m
    c.muShield.dZ4 = 3.0*u.m
    c.muShield.dZ5 = 2.5*u.m
    c.muShield.dZ6 = 2.5*u.m
    c.muShield.LE  = 5*u.m
    c.muShieldDesign = muShieldDesign
    # for passive design, fDesign==1
    if muShieldDesign == 1:
        c.muShield.length =  70*u.m
    # for active design, fDesign==2
    if muShieldDesign == 2:
        c.muShield.length = 2*(c.muShield.dZ1+c.muShield.dZ2+c.muShield.dZ3+c.muShield.dZ4+c.muShield.dZ5+c.muShield.dZ6) + c.muShield.LE  # leave some space for nu-tau detector

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

