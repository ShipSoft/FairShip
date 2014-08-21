import shipunit as u
# for the moment, do it by hand
muShieldDesign = 2  # 1=passive 2=active
targetOpt      = 5  # 0=solid   >0 sliced, 5 pieces of tungsten, 4 air slits

self.vetoStation = AttrDict(z=-2390.*u.cm)
self.TrackStation1 = AttrDict(z=1510.*u.cm)
self.TrackStation2 = AttrDict(z=1710.*u.cm)
self.TrackStation3 = AttrDict(z=2150.*u.cm)
self.TrackStation4 = AttrDict(z=2370.*u.cm)

z = self.TrackStation2.z + 0.5 * (self.TrackStation3.z - self.TrackStation2.z)

self.Bfield = AttrDict(z = self.z)
self.Bfield.max = 1.5*u.kilogauss  # was 1.15 in EOI

# target absorber muon shield setup
decayVolume                 =  AttrDict(z=0*u.cm)
self.decayVolume.length     =   50*u.m

self.muShield             =  AttrDict(z=0*u.cm)
self.muShield.dZ1 = 2.5*u.m
self.muShield.dZ2 = 3.5*u.m
self.muShield.dZ3 = 3.0*u.m
self.muShield.dZ4 = 3.0*u.m
self.muShield.dZ5 = 2.5*u.m
self.muShield.dZ6 = 2.5*u.m
self.muShield.LE  = 5*u.m
# for passive design, fDesign==1
if self.muShieldDesign == 1:  self.muShield.length =  70*u.m
# for active design, fDesign==2
if self.muShieldDesign == 2:  self.muShield.length =  2*(self.muShield.dZ1+self.muShield.dZ2+self.muShield.dZ3+self.muShield.dZ4+self.muShield.dZ5+self.muShield.dZ6) + self.muShield.LE # leave some space for nu-tau detector   
self.muShield.z  =  -self.decayVolume.length/2.-self.muShield.length/2.

hadronAbsorber       		=  AttrDict(z=0*u.cm)
self.hadronAbsorber.length =  3.00*u.m
self.hadronAbsorber.z     =  self.muShield.z - self.muShield.length/2. - self.hadronAbsorber.length/2.

target               =  AttrDict(z=0*u.cm)
self.target.sl            =  1*u.cm  # air slit total length
self.target.length        =  50*u.cm + self.target.sl*(self.targetOpt-1) 
self.target.z             =  self.hadronAbsorber.z - self.hadronAbsorber.length/2. - self.target.length/2.

# interaction point, start of target
self.target.z0  =  self.target.z - self.target.length/2.

# straws of tracking stations
straw = AttrDict(z=0*u.cm)
self.straw.length = 250.*u.cm
self.straw.resol  = 0.01*u.cm
self.straw.pitch  = 1.*u.cm
self.straw.stereoAngle = 5./180. #degrees
