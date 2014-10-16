import shipunit as u
import ROOT
fDesign = 2
class ShipGeo():
 def __init__(self,z=0):
  self.z = z

Chamber1 = ShipGeo(-2450.*u.cm)
Chamber2 = ShipGeo(-440.*u.cm)
Chamber3 = ShipGeo(1620.*u.cm)
Chamber4 = ShipGeo(1940.*u.cm)
Chamber5 = ShipGeo(2270.*u.cm)
Chamber6 = ShipGeo(2540.*u.cm)
chambers = ShipGeo(0*u.cm)
chambers.Tub1length = ShipGeo(50.*u.cm)
chambers.Tub2length = ShipGeo(1890.*u.cm)
chambers.Tub3length = ShipGeo(80.*u.cm)
chambers.Tub4length = ShipGeo(200.*u.cm)
chambers.Tub5length = ShipGeo(90.*u.cm)
chambers.Tub6length = ShipGeo(20.*u.cm)
chambers.Rmin = 245.*u.cm
chambers.Rmax = 250.*u.cm




vetoStation   = ShipGeo(-2390.*u.cm)
TrackStation1 = ShipGeo(1520.*u.cm)
TrackStation2 = ShipGeo(1720.*u.cm)
TrackStation3 = ShipGeo(2160.*u.cm)
TrackStation4 = ShipGeo(2380.*u.cm)

strawtubes                    = ShipGeo(0*u.cm)
strawtubes.StrawLength        = 250.*u.cm
strawtubes.InnerStrawDiameter = 0.94*u.cm
strawtubes.OuterStrawDiameter = 0.98*u.cm
strawtubes.StrawPitch         = 1.76*u.cm
strawtubes.DeltazLayer        = 1.1*u.cm
strawtubes.DeltazPlane        = 2.6*u.cm
strawtubes.StrawsPerLayer     = 284
strawtubes.ViewAngle          = 5
strawtubes.WireThickness      = 0.003*u.cm
strawtubes.DeltazView         = 10.*u.cm
strawtubes.VacBox_x           = 300.*u.cm
strawtubes.VacBox_y           = 300.*u.cm

z = TrackStation2.z + 0.5 * (TrackStation3.z - TrackStation2.z)
Bfield = ShipGeo(z)
Bfield.max = 1.5*u.kilogauss   # was 1.15 in EOI

# target absorber muon shield setup
decayVolume          =  ShipGeo(0*u.cm)
decayVolume.length   =   50*u.m

muShield             =  ShipGeo(0*u.cm)
muShield.dZ1 = 2.5*u.m
muShield.dZ2 = 3.5*u.m
muShield.dZ3 = 3.0*u.m
muShield.dZ4 = 3.0*u.m
muShield.dZ5 = 2.5*u.m
muShield.dZ6 = 2.5*u.m
muShield.LE  = 5*u.m
# for passive design, fDesign==1
if fDesign == 1:  muShield.length =  70*u.m
# for active design, fDesign==2
if fDesign == 2:  muShield.length =  2*(muShield.dZ1+muShield.dZ2+muShield.dZ3+muShield.dZ4+muShield.dZ5+muShield.dZ6) + muShield.LE # leave some space for nu-tau detector
muShield.z  =  -decayVolume.length/2.-muShield.length/2.

hadronAbsorber       =  ShipGeo(0*u.cm)
hadronAbsorber.length=  3.0*u.m
hadronAbsorber.z     =  muShield.z - muShield.length/2. - hadronAbsorber.length/2.

target               =  ShipGeo(0*u.cm)
target.length        =  50*u.cm
target.z             =  hadronAbsorber.z - hadronAbsorber.length/2. - target.length/2.

# interaction point, start of target
target.z0  =  target.z - target.length/2.



