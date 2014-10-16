import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry
# the following params should be passed through 'ConfigRegistry.loadpy' method
# muShieldDesign = 1  # 1=passive 2=active
# targetOpt      = 5  # 0=solid   >0 sliced, 5 pieces of tungsten, 4 air slits

with ConfigRegistry.register_config("basic") as c:
    c.vetoStation = AttrDict(z=-2390.*u.cm)
    c.TrackStation1 = AttrDict(z=1510.*u.cm)
    c.TrackStation2 = AttrDict(z=1709.*u.cm)
    c.TrackStation3 = AttrDict(z=2191.*u.cm)
    c.TrackStation4 = AttrDict(z=2364.*u.cm)

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

    c.Bfield = AttrDict(z=c.z)
    c.Bfield.max = 1.5*u.kilogauss  # was 1.15 in EOI

    # target absorber muon shield setup
    c.decayVolume            =  AttrDict(z=0*u.cm)
    c.decayVolume.length     =   50*u.m

    c.muShield               =  AttrDict(z=0*u.cm)
    c.muShield.dZ1 = 2.5*u.m
    c.muShield.dZ2 = 3.5*u.m
    c.muShield.dZ3 = 3.0*u.m
    c.muShield.dZ4 = 3.0*u.m
    c.muShield.dZ5 = 2.5*u.m
    c.muShield.dZ6 = 2.5*u.m
    c.muShield.LE  = 5*u.m


with ConfigRegistry.register_config("passive_active", base="basic") as c:
    # for passive design, fDesign==1
    assert "muShieldDesign" in globals(), "'muShieldDesign' should be specified"
    if muShieldDesign == 1:  c.muShield.length =  70*u.m
    # for active design, fDesign==2
    if muShieldDesign == 2:  
        c.muShield.length = 2*(c.muShield.dZ1+c.muShield.dZ2+c.muShield.dZ3+c.muShield.dZ4+c.muShield.dZ5+c.muShield.dZ6)\
            + c.muShield.LE  # leave some space for nu-tau detector   
    c.muShield.z  =  -c.decayVolume.length/2.-c.muShield.length/2.

    c.hadronAbsorber        =  AttrDict(z=0*u.cm)
    c.hadronAbsorber.length =  3.00*u.m
    c.hadronAbsorber.z      =  c.muShield.z - c.muShield.length/2. - c.hadronAbsorber.length/2.

    c.target               =  AttrDict(z=0*u.cm)
    c.target.sl            =  1*u.cm  # air slit total length
    c.target.length        =  50*u.cm + c.target.sl*(targetOpt-1) 
    c.target.z             =  c.hadronAbsorber.z - c.hadronAbsorber.length/2. - c.target.length/2.

    # interaction point, start of target
    c.target.z0  =  c.target.z - c.target.length/2.


