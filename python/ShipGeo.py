from __future__ import print_function
import shipunit as u
import ROOT
fDesign = 2
class ShipGeo(): 
 def __init__(self,z=0):
  self.z = z

def zPositions():
 main = sys.modules['__main__']
 if hasattr(main,'ShipGeo'):
  for x in ShipGeo:
   if hasattr(eval('ShipGeo.'+x),'z'): print(x,'z=',eval('ShipGeo.'+x+'.z'))
  
vetoStation   = ShipGeo(-2390.*u.cm)
TrackStation1 = ShipGeo(1510.*u.cm)
TrackStation2 = ShipGeo(1710.*u.cm)
TrackStation3 = ShipGeo(2150.*u.cm)
TrackStation4 = ShipGeo(2370.*u.cm)

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

# straws of tracking stations
straw = ShipGeo(0*u.cm)
straw.length = 250.*u.cm
straw.resol  = 0.01*u.cm
straw.pitch  = 1.*u.cm
straw.stereoAngle = 5./180.*ROOT.TMath.Pi()

