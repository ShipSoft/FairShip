import shipunit as u

class ShipGeo(): 
 def __init__(self,z=0):
  self.z = z
  
vetoStation   = ShipGeo(-2390.*u.cm)
TrackStation1 = ShipGeo(1510.*u.cm)
TrackStation2 = ShipGeo(1710.*u.cm)
TrackStation3 = ShipGeo(2150.*u.cm)
TrackStation4 = ShipGeo(2370.*u.cm)

z = TrackStation2.z + 0.5 * (TrackStation3.z - TrackStation2.z)
Bfield = ShipGeo(z)
Bfield.max = 1.15*u.kilogauss

# target absorber muon shield setup
decayVolume          =  ShipGeo(0*u.cm)
decayVolume.length   =   50*u.m

muShield             =  ShipGeo(0*u.cm)
muShield.length      =  70*u.m
muShield.z           =  -decayVolume.length/2.-muShield.length/2.

hadronAbsorber       =  ShipGeo(0*u.cm)
hadronAbsorber.length=  3.50*u.m
hadronAbsorber.z     =  muShield.z - muShield.length/2. - hadronAbsorber.length/2.

target               =  ShipGeo(0*u.cm)
target.length        =  50*u.cm
target.z             =  hadronAbsorber.z - hadronAbsorber.length/2. - target.length/2.

# interaction point, start of target
target.z0  =  target.z - target.length/2.


