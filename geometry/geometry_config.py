import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry
# the following params should be passed through 'ConfigRegistry.loadpy' method
# muShieldDesign = 5  # 1=passive 2=active 5=TP design 6=magnetized hadron absorber
# nuTargetDesign = 2  #1 = with active layers, 2 = only passive
# nuTauTPDesign  = 1  #1 = TP, 0 = NEW

# targetOpt      = 5  # 0=solid   >0 sliced, 5: 5 pieces of tungsten, 4 air slits, 17: molybdenum tungsten interleaved with H20
# strawOpt       = 0  # 0=simplistic tracking stations defined in veto.cxx  1=detailed strawtube design
# preshowerOption = 0 # 1=simple preShower detector for conceptual studies, moves calo and muon stations
# tankDesign = 5 #  4=TP, elliptical shape, 5=rectangular, conical
if "muShieldDesign" not in globals():
    muShieldDesign = 5
if "nuTargetDesign" not in globals():
    nuTargetDesign = 1
if "nuTauTPDesign" not in globals():
    nuTauTPDesign = 1
    if muShieldDesign == 7: nuTauTPDesign=0
if "targetOpt" not in globals():
    targetOpt = 17
if "strawDesign" not in globals():
    strawDesign = 4
if "tankDesign" not in globals():
    tankDesign = 4
if "HcalOption" not in globals():
    HcalOption = 1
if "Yheight" not in globals():
    Yheight = 10.
if "EcalGeoFile" not in globals():
    if tankDesign == 5:
        EcalGeoFile = "ecal_rect5x10m2.geo"
    else:
        EcalGeoFile = "ecal_ellipse5x10m2.geo"
if "HcalGeoFile" not in globals():
    if tankDesign == 5:
        HcalGeoFile = "hcal_rect.geo"
    else:
        HcalGeoFile = "hcal.geo"
if "preshowerOption" not in globals():
    preshowerOption = 0

with ConfigRegistry.register_config("basic") as c:
    # global muShieldDesign, targetOpt, strawDesign, Yheight
    c.Yheight = Yheight*u.m
    # decision by the SP 
    totalLength       = 2.5*c.Yheight + 35*u.m
    extraVesselLength = totalLength - 50*u.m
    windowBulge = 1*u.m
    c.strawDesign = strawDesign
    c.tankDesign = tankDesign
    c.chambers = AttrDict(z=0*u.cm)
    magnetIncrease    = 100.*u.cm
    # make z coordinates for the decay volume and tracking stations relative to T4z
    # eventually, the only parameter which needs to be changed when the active shielding lenght changes.
    z4=2438.*u.cm+magnetIncrease+extraVesselLength
    if strawDesign != 4:
     print "this design is not supported, use strawDesign = 4"
     1/0 
    else:
     c.chambers.Length = totalLength
     c.chambers.Tub1length = 2.5*u.m
     c.chambers.Tub2length = 17.68*u.m+extraVesselLength/2.
     c.chambers.Tub3length = 0.8*u.m
     c.chambers.Tub4length = 2.*u.m+magnetIncrease/2.
     c.chambers.Tub5length = 0.8*u.m
     c.chambers.Tub6length = 0.1*u.m+windowBulge/2.
     c.chambers.Rmin = 245.*u.cm
     c.chambers.Rmax = 250.*u.cm
     # positions and lenghts of vacuum tube segments
     zset=z4-4666.*u.cm-magnetIncrease-extraVesselLength
     c.Chamber1 = AttrDict(z=zset)
     zset=z4-2628.*u.cm-magnetIncrease-extraVesselLength/2.
     c.Chamber2 = AttrDict(z=zset)
     zset=z4-740.*u.cm-magnetIncrease
     c.Chamber3 = AttrDict(z=zset)  
     zset=z4-420.*u.cm-magnetIncrease/2.  
     c.Chamber4 = AttrDict(z=zset)
     zset=z4-100.*u.cm
     c.Chamber5 = AttrDict(z=zset)
     zset=z4+30.*u.cm+windowBulge/2.
     c.Chamber6 = AttrDict(z=zset)
     c.Veto = AttrDict(z=0*u.cm)
     c.Veto.innerSupport = 3.*u.cm 
     c.Veto.innerSupportMed = "steel"
     c.Veto.outerSupport = 8.*u.mm
     c.Veto.outerSupportMed = "Aluminum"
     c.Veto.sensitiveThickness = 0.3*u.m
     c.Veto.sensitiveMed = "Scintillator"
     c.Veto.decayMed = "vacuums"
     c.Veto.rib = 3.*u.cm
     c.Veto.ribMed = "steel"
     # horizontal width at start and focus point, for conical/rectangular size
     # envelope (46,1.2) or (46,0.9) end at T4: (100.,2.5)  London slides, https://indico.cern.ch/event/508465/contributions/2166894/    
     c.zFocusX = -5*u.m # +15*u.m # (latest with charm) downstream from target, will have neutrinos going from outside to inside, not so good for vacuum option.
     c.zFocusY = -5*u.m # for the moment, identical to X
     c.xMax    = +2.5*u.m # max horizontal width at T4
     # 
     c.TrackStation4 = AttrDict(z=z4)
     zset=z4-200.*u.cm
     c.TrackStation3 = AttrDict(z=zset)
     zset=z4-640.*u.cm-magnetIncrease
     c.TrackStation2 = AttrDict(z=zset)
     zset=z4-840.*u.cm-magnetIncrease
     c.TrackStation1 = AttrDict(z=zset)
     zset=z4-4406.*u.cm-magnetIncrease-extraVesselLength
     c.vetoStation   = AttrDict(z=zset)

    c.z = c.TrackStation2.z + 0.5 * (c.TrackStation3.z - c.TrackStation2.z)
    c.scintillator = AttrDict(z=0*u.cm)
    c.scintillator.Rmin = 251.*u.cm
    c.scintillator.Rmax = 260.*u.cm

    c.strawtubes = AttrDict(z=0*u.cm)
    
    c.strawtubes.InnerStrawDiameter = 0.975*u.cm
    c.strawtubes.WallThickness      = 0.0039*u.cm
    c.strawtubes.OuterStrawDiameter = (c.strawtubes.InnerStrawDiameter + 2*c.strawtubes.WallThickness)

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
    c.Bfield.max = 1.4361*u.kilogauss  # was 1.15 in EOI
    c.Bfield.y   = c.Yheight
    c.Bfield.x   = 3.*u.m

    presShowerDeltaZ = 0. 
    c.preshowerOption = preshowerOption
    if preshowerOption >0:
     PreshowerStart = c.Chamber6.z + windowBulge + 2*u.cm   
     c.PreshowerFilter0  = AttrDict(z= PreshowerStart )
     c.PreshowerStation0 = AttrDict(z= c.PreshowerFilter0.z + 10*u.cm )

     c.Preshower = AttrDict(z=0)
     c.Preshower.XMax    =  300.*u.cm
     c.Preshower.YMax    =  600.*u.cm * c.Yheight / (10.*u.m)
     c.Preshower.ActiveThickness = 0.5*u.cm
     c.Preshower.FilterThickness0 = 1.4*u.cm

     PreshowerLeverArm=1*u.m

     c.PreshowerFilter1  = AttrDict(z= c.PreshowerStation0.z +PreshowerLeverArm )
     c.PreshowerStation1 = AttrDict(z= c.PreshowerFilter1.z + 10*u.cm )
     c.Preshower.FilterThickness1 = 2.*u.cm

     presShowerDeltaZ = PreshowerLeverArm + 2*10*u.cm + 2*2.*u.cm

    c.ecal  =  AttrDict(z = c.Chamber6.z + windowBulge + 2*u.cm + presShowerDeltaZ)
    c.ecal.File = EcalGeoFile
    c.HcalOption  =  HcalOption
    hcalThickness = 232*u.cm
    if not HcalOption < 0:
     c.hcal =  AttrDict(z=c.ecal.z + hcalThickness/2. + 45.*u.cm  )
     c.hcal.hcalSpace = hcalThickness + 5.5*u.cm
     c.hcal.File  =  HcalGeoFile
    else:
     c.hcal  =  AttrDict(z=c.ecal.z)     
    c.MuonStation0 = AttrDict(z=c.hcal.z+hcalThickness/2.+20.5*u.cm)
    c.MuonStation1 = AttrDict(z=c.MuonStation0.z+1*u.m)
    c.MuonStation2 = AttrDict(z=c.MuonStation0.z+2*u.m)
    c.MuonStation3 = AttrDict(z=c.MuonStation0.z+3*u.m)

    c.MuonFilter0 = AttrDict(z=c.MuonStation0.z+50.*u.cm)
    c.MuonFilter1 = AttrDict(z=c.MuonStation0.z+150.*u.cm)
    c.MuonFilter2 = AttrDict(z=c.MuonStation0.z+250.*u.cm)

    c.Muon = AttrDict(z=0)
    c.Muon.XMax    =  300.*u.cm
    c.Muon.YMax    =  600.*u.cm * c.Yheight / (10.*u.m)

    c.Muon.ActiveThickness = 0.5*u.cm
    c.Muon.FilterThickness = 30.*u.cm

    # target absorber muon shield setup, decayVolume.length = nominal EOI length, only kept to define z=0
    c.decayVolume            =  AttrDict(z=0*u.cm)
    c.decayVolume.length     =   50*u.m

    c.muShield       =  AttrDict(z=0*u.cm)
    c.muShieldDesign = muShieldDesign
    # design 4,5,6
    c.muShield.LE  = 10*u.m     # - 0.5 m air - Goliath: 4.5 m - 0.5 m air - nu-tau mu-det: 3 m - 0.5 m air. finally 10m asked by Giovanni
    c.muShield.dZ0 = 2.5*u.m if muShieldDesign == 6 else 1*u.m
    c.muShield.dZ1 = 3.5*u.m
    c.muShield.dZ2 = 6.*u.m
    c.muShield.dZ3 = 2.5*u.m
    c.muShield.dZ4 = 3.*u.m
    c.muShield.dZ5 = 0.*u.m     # 28Oct #5 removed
    c.muShield.dZ6 = 3.*u.m
    c.muShield.dZ7 = 3.*u.m
    c.muShield.dZ8 = 3.*u.m
    c.muShield.dXgap = 0.2*u.m
    c.muShield.dZgap = 0.1*u.m

    # zGap to compensate automatic shortening of magnets
    zGap = 0.5 * c.muShield.dZgap  # halflengh of gap
    if muShieldDesign == 7:
        c.muShield.dZ1 = 0.7*u.m
        c.muShield.dZ2 = 1.7*u.m
        c.muShield.dZ3 = 4.0*u.m + zGap
        c.muShield.dZ4 = 2.75*u.m + zGap
        c.muShield.dZ5 = 2.4*u.m + zGap
        c.muShield.dZ6 = 3.0*u.m + zGap
        c.muShield.dZ7 = 2.35*u.m + zGap
        c.muShield.dZ8 = 0.*u.m
        c.muShield.dXgap = 0.*u.m
        c.muShield.length = 2*(c.muShield.dZ1+c.muShield.dZ2+c.muShield.dZ3+c.muShield.dZ4+c.muShield.dZ5+c.muShield.dZ6
                         +c.muShield.dZ7+c.muShield.dZ8 ) + c.muShield.LE  # leave some space for nu-tau 
        c.muShield.z  =  -c.decayVolume.length/2.-c.muShield.length/2.

    if muShieldDesign == 3:
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
    if muShieldDesign == 3 or muShieldDesign == 4 or muShieldDesign == 5: 
     c.muShield.length = 2*(c.muShield.dZ0+c.muShield.dZ1+c.muShield.dZ2+c.muShield.dZ3+c.muShield.dZ4+c.muShield.dZ5+c.muShield.dZ6
                         +c.muShield.dZ7+c.muShield.dZ8 ) + c.muShield.LE  # leave some space for nu-tau 
     c.muShield.z  =  -c.decayVolume.length/2.-c.muShield.length/2.
    if muShieldDesign == 6: 
     c.muShield.length = 2*(c.muShield.dZ1+c.muShield.dZ2+c.muShield.dZ3+c.muShield.dZ4+c.muShield.dZ5+c.muShield.dZ6
                         +c.muShield.dZ7+c.muShield.dZ8 ) + c.muShield.LE  # leave some space for nu-tau 
     c.muShield.z  =  -c.decayVolume.length/2.-c.muShield.length/2.

    c.hadronAbsorber              =  AttrDict(z=0*u.cm)
    if muShieldDesign > 5:  c.hadronAbsorber.length =  5.00*u.m
    if muShieldDesign > 6:  c.hadronAbsorber.length =     0*u.m # magnetized, counted inside muonshield 
    else:                   c.hadronAbsorber.length =  3.00*u.m
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

# for the digitizing step
    c.strawtubes.v_drift = 1./(30*u.ns/u.mm) # for baseline NA62 5mm radius straws)
    c.strawtubes.sigma_spatial = 0.012*u.cm # according to Massi's TP section
# size of straws
    c.strawtubes.StrawLength     = c.xMax
    if tankDesign == 5:
       zF = c.target.z0+c.zFocusX
       c.strawtubes.StrawLength12   = c.xMax*(c.TrackStation1.z-2*c.strawtubes.DeltazView-zF)/(z4-zF)
       c.strawtubes.StrawLengthVeto = c.xMax*(c.vetoStation.z-c.strawtubes.DeltazView-zF)/(z4-zF)   
    else:
       c.strawtubes.StrawLength12   = c.strawtubes.StrawLength
       c.strawtubes.StrawLengthVeto = c.strawtubes.StrawLength  
# height of tracking stations
    if tankDesign == 5:
     zF = c.target.z0+c.zFocusY
     c.strawtubes.vetoydim           = c.Yheight/2.*(c.vetoStation.z-c.strawtubes.DeltazView-zF)/(z4-zF)
     c.strawtubes.tr12ydim           = c.Yheight/2.*(c.TrackStation1.z-2*c.strawtubes.DeltazView-zF)/(z4-zF)
     c.strawtubes.tr34ydim           = int(c.Yheight/2.)  
    else:
     c.strawtubes.vetoydim           = int(c.Yheight/2.)
     c.strawtubes.tr12ydim           = int(c.Yheight/2.)
     c.strawtubes.tr34ydim           = int(c.Yheight/2.)  


    #Parameters for tau neutrino target Magnet
    c.EmuMagnet = AttrDict(z=0*u.cm)
    c.EmuMagnet.TPDesign = nuTauTPDesign
    c.EmuMagnet.Z = 4.5*u.m
    c.EmuMagnet.GapDown = 25*u.cm
    c.EmuMagnet.GapUp = 27*u.cm
    c.EmuMagnet.B=1*u.tesla
    if c.EmuMagnet.TPDesign == 0: #new MagnetConfig
      scale = 1.
      c.EmuMagnet.X = scale*1.7*u.m
      c.EmuMagnet.Y = scale*3.2*u.m
      c.EmuMagnet.Radius = 1.1*u.m
      c.EmuMagnet.Height1 = 30*u.cm
      c.EmuMagnet.Height2 = c.EmuMagnet.Height1
      c.EmuMagnet.Distance = c.EmuMagnet.X-2*c.EmuMagnet.Height1
      c.EmuMagnet.ColX = c.EmuMagnet.Distance
      c.EmuMagnet.ColY = 0.7*u.m
      c.EmuMagnet.ColZ = 0.9*u.m
      c.EmuMagnet.BaseX = c.EmuMagnet.Height1
      c.EmuMagnet.BaseY = c.EmuMagnet.Y
      c.EmuMagnet.BaseZ = c.EmuMagnet.Z
    if c.EmuMagnet.TPDesign == 1: #TP MagnetConfig
      c.EmuMagnet.X = 3.6*u.m
      c.EmuMagnet.Radius = 1*u.m
      c.EmuMagnet.Height1 = 45*u.cm
      c.EmuMagnet.Height2 = 30*u.cm
      c.EmuMagnet.Distance = 105*u.cm
      c.EmuMagnet.BaseX = c.EmuMagnet.X
      c.EmuMagnet.BaseY = 57*u.cm
      c.EmuMagnet.BaseZ = c.EmuMagnet.Z
      c.EmuMagnet.ColX = 0*u.m
      c.EmuMagnet.ColY = c.EmuMagnet.BaseY
      c.EmuMagnet.ColZ = 0*u.m
      c.EmuMagnet.Y = 2*c.EmuMagnet.BaseY+c.EmuMagnet.Height1+c.EmuMagnet.Height2+c.EmuMagnet.Distance
    

    #Parameters for tau magnetic Spectrometer
    c.tauMS = AttrDict(z=0*u.cm)
    if c.EmuMagnet.TPDesign==1:
        c.tauMS.YRyoke = 90*u.cm
        c.tauMS.YRyoke_s = c.tauMS.YRyoke-30*u.cm
        c.tauMS.Xtot = 4.*u.m  
        c.tauMS.YFe = 8*u.m
        c.tauMS.Ytot = c.tauMS.YFe + 2*c.tauMS.YRyoke
    if c.EmuMagnet.TPDesign==0:
        scaleMS=1.0
        c.tauMS.YRyoke = scale*40*u.cm
        c.tauMS.YRyoke_s = scale*27*u.cm
        c.tauMS.Xtot = scaleMS*1.9*u.m 
        c.tauMS.Ytot = scaleMS*3.8*u.m
        c.tauMS.YFe = c.tauMS.Ytot - 2*c.tauMS.YRyoke
    c.tauMS.XRyoke = c.tauMS.Xtot+20*u.cm
    c.tauMS.XRyoke_s = c.tauMS.Xtot
    c.tauMS.Ztot = 4.76*u.m
    c.tauMS.NFe = 12
    c.tauMS.NRpc= 11
    c.tauMS.XFe = c.tauMS.Xtot
    c.tauMS.XRpc = c.tauMS.Xtot
    c.tauMS.YRpc = c.tauMS.YFe-20*u.cm
    c.tauMS.ZFe = 5.*u.cm
    c.tauMS.ZRpc = 2.*u.cm
    c.tauMS.ZArm = c.tauMS.NFe*c.tauMS.ZFe + c.tauMS.NRpc*c.tauMS.ZRpc
    c.tauMS.GapD = 27.*u.cm
    c.tauMS.GapM = 122*u.cm
    c.tauMS.ZRyoke = 2*c.tauMS.ZArm + c.tauMS.GapM
    c.tauMS.ZRyoke_s = c.tauMS.GapM
    c.tauMS.CoilH = 5*u.cm
    c.tauMS.CoilW = 2*u.cm
    c.tauMS.CoilG = 2*u.cm
    c.tauMS.N =20
    c.tauMS.zMSC = -c.decayVolume.length/2. - c.tauMS.GapD - c.tauMS.Ztot/2
    c.tauMS.B = 1.5 * u.tesla
    c.tauMS.XGas =  c.tauMS.Xtot
    c.tauMS.YGas =  c.tauMS.YRpc
    c.tauMS.ZGas = 1*u.mm
    c.tauMS.XStrip =  c.tauMS.Xtot
    c.tauMS.YStrip =  c.tauMS.YRpc
    c.tauMS.ZStrip = 0.05*u.mm
    c.tauMS.XPet =  c.tauMS.Xtot
    c.tauMS.YPet =  c.tauMS.YRpc
    c.tauMS.ZPet = 0.1*u.mm
    c.tauMS.XEle =  c.tauMS.Xtot
    c.tauMS.YEle =  c.tauMS.YRpc
    c.tauMS.ZEle = 1*u.mm


    c.tauHPT = AttrDict(z=0*u.cm)
    c.tauHPT.DZ = 15*u.cm
    c.tauHPT.DX = c.tauMS.XFe
    c.tauHPT.DY = c.tauMS.YFe
   

    c.EmuMagnet.zC = -c.decayVolume.length/2. - c.tauMS.GapD - c.tauMS.Ztot - c.EmuMagnet.GapDown - c.EmuMagnet.Z/2    

    #tau Bricks
    c.NuTauTarget = AttrDict(z=0*u.cm)

    if c.EmuMagnet.TPDesign == 0: #NEW
        c.NuTauTarget.row=14
        c.NuTauTarget.col=6
        c.NuTauTarget.wall=11
    if c.EmuMagnet.TPDesign == 1: #TP                                                                                                                       
        c.NuTauTarget.row=7
        c.NuTauTarget.col=15
        c.NuTauTarget.wall=11

    c.NuTauTarget.nuTargetDesign = nuTargetDesign

    c.NuTauTarget.Ydist = 0.2*u.cm
    
    c.NuTauTarget.EmTh = 0.0045 * u.cm
    c.NuTauTarget.EmX = 12.5 * u.cm
    c.NuTauTarget.EmY = 9.9 * u.cm
    c.NuTauTarget.PBTh = 0.0205 * u.cm
    c.NuTauTarget.LeadTh = 0.1 * u.cm
    c.NuTauTarget.EPlW = 2* c.NuTauTarget.EmTh + c.NuTauTarget.PBTh
    c.NuTauTarget.AllPW = c.NuTauTarget.LeadTh + c.NuTauTarget.EPlW
    c.NuTauTarget.BrX = 12.9 *u.cm
    c.NuTauTarget.BrY = 10.5 *u.cm
    c.NuTauTarget.xdim = c.NuTauTarget.col*c.NuTauTarget.BrX
    c.NuTauTarget.ydim = c.NuTauTarget.row*(c.NuTauTarget.BrY+c.NuTauTarget.Ydist)    

    c.NuTauTarget.BrPackZ = 0.1 * u.cm
    c.NuTauTarget.BrPackX = c.NuTauTarget.BrX - c.NuTauTarget.EmX
    c.NuTauTarget.BrPackY = c.NuTauTarget.BrY - c.NuTauTarget.EmY
    c.NuTauTarget.BrZ = 56 * c.NuTauTarget.AllPW + c.NuTauTarget.EPlW +c.NuTauTarget.BrPackZ
    c.NuTauTarget.RohG = 1.5 * u.cm
    c.NuTauTarget.LayerCESW = c.NuTauTarget.RohG + c.NuTauTarget.EPlW
    c.NuTauTarget.CESPack = 0.1 * u.cm
    c.NuTauTarget.CESW = 2 * c.NuTauTarget.LayerCESW + c.NuTauTarget.EPlW + c.NuTauTarget.CESPack
    c.NuTauTarget.CellW = c.NuTauTarget.BrZ + c.NuTauTarget.CESW

    #TargetTrackers!
    c.NuTauTT = AttrDict(z=0*u.cm)
    c.NuTauTT.TTX = c.NuTauTarget.xdim
    c.NuTauTT.TTY = c.NuTauTarget.ydim
    c.NuTauTT.TTZ= 6.0*u.cm
     
    c.NuTauTarget.zdim = 11* c.NuTauTarget.CellW + 12*c.NuTauTT.TTZ
