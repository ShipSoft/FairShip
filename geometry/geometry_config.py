import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry
# the following params should be passed through 'ConfigRegistry.loadpy' method
# muShieldDesign = 5  # 1=passive 2=active 5=TP design 6=magnetized hadron absorber
# nuTargetDesign = 2  #1 = with active layers, 2 = only passive
# targetOpt      = 5  # 0=solid   >0 sliced, 5: 5 pieces of tungsten, 4 air slits, 17: molybdenum tungsten interleaved with H20
# strawOpt       = 0  # 0=simplistic tracking stations defined in veto.cxx  1=detailed strawtube design
# preshowerOption = 0 # 1=simple preShower detector for conceptual studies, moves calo and muon stations
# tankDesign = 5 #  4=TP, elliptical shape, 5=rectangular, conical
if "muShieldDesign" not in globals():
    muShieldDesign = 5
if "nuTargetDesign" not in globals():
    nuTargetDesign = 1
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
     # horizontal width at start and focus point, for conical/rectangular size
     # Hans proposal: envelope (46,1.2), end at T4: (100.,2.7)  
     # 
     c.zFocus = +2.8*u.m # downstream from target, will have neutrinos going from outside to inside, not so good for vacuum option.
     c.xMax = +2.7*u.m # max horizontal width at T4
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
    
    if tankDesign == 5:
       c.strawtubes.StrawLength        = c.xMax
    else:
       c.strawtubes.StrawLength        = 250.*u.cm
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
    if tankDesign == 5:
       c.strawtubes.StrawLength12   = c.xMax*(c.TrackStation1['z']-2*c.strawtubes.DeltazView-c.zFocus)/(z4-c.zFocus)
       c.strawtubes.StrawLengthVeto = abs(c.xMax*(c.vetoStation['z']-c.strawtubes.DeltazView-c.zFocus)/(z4-c.zFocus))    
    else:
       c.strawtubes.StrawLength12   = c.strawtubes.StrawLength
       c.strawtubes.StrawLengthVeto = c.strawtubes.StrawLength  
# for the digitizing step
    c.strawtubes.v_drift = 1./(30*u.ns/u.mm) # for baseline NA62 5mm radius straws)
    c.strawtubes.sigma_spatial = 120*u.micrometer
       
    c.Bfield = AttrDict(z=c.z)
    c.Bfield.max = 1.4361*u.kilogauss  # was 1.15 in EOI
    c.Bfield.y   = c.Yheight

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
    c.muShield.LE  = 10*u.m     #- 0.5 m air - Goliath: 4.5 m - 0.5 m air - nu-tau mu-det: 3 m - 0.5 m air. finally 10m asked by Giovanni
    if muShieldDesign == 6: c.muShield.dZ0 = 2.5*u.m 
    else:                   c.muShield.dZ0 = 1*u.m      #  extra hadron absorber
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
    if muShieldDesign == 6 : 
     c.muShield.length = 2*(c.muShield.dZ1+c.muShield.dZ2+c.muShield.dZ3+c.muShield.dZ4+c.muShield.dZ5+c.muShield.dZ6
                         +c.muShield.dZ7+c.muShield.dZ8 ) + c.muShield.LE  # leave some space for nu-tau 
     c.muShield.z  =  -c.decayVolume.length/2.-c.muShield.length/2.

    c.hadronAbsorber              =  AttrDict(z=0*u.cm)
    if muShieldDesign == 6: c.hadronAbsorber.length =  5.00*u.m
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

    # straws of tracking stations
    c.straw = AttrDict(z=0*u.cm)
    c.straw.length = 250.*u.cm
    c.straw.resol  = 0.012*u.cm # according to Massi's TP section
    c.straw.pitch  = 1.*u.cm
    c.straw.stereoAngle = 5./180.  # degrees

    #Parameters for tau magnetic Spectrometer
    c.tauMS = AttrDict(z=0*u.cm)
    c.tauMS.zSize = 4.76*u.m
    c.tauMS.FeSlab = 5. *u.cm
    c.tauMS.RpcW = 2.*u.cm
    c.tauMS.ArmW = 12*c.tauMS.FeSlab + 11*c.tauMS.RpcW
    c.tauMS.GapV = 27.*u.cm
    c.tauMS.MGap = 122*u.cm
    c.tauMS.RetYokeH = 90*u.cm
    c.tauMS.CoilH = 10*u.cm
    c.tauMS.CoilW = 2*u.cm
    c.tauMS.CoilG = 2*u.cm
    c.tauMS.N =20
    c.tauMS.zMSC = -c.decayVolume.length/2. - c.tauMS.GapV - c.tauMS.zSize/2
    c.tauMS.Mfield = 1.5 * u.tesla

    c.tauHPT = AttrDict(z=0*u.cm)
    c.tauHPT.DX = 4*u.m
    c.tauHPT.DY = 8*u.m
    c.tauHPT.DZ = 15*u.cm

    #Parameters for Goliath
    c.NuTauTarget = AttrDict(z=0*u.cm)
    c.NuTauTarget.nuTargetDesign = nuTargetDesign
    c.NuTauTarget.LS = 4.5*u.m
    c.NuTauTarget.TS = 3.6*u.m
    c.NuTauTarget.GapTS = 25*u.cm
    c.NuTauTarget.CoilR = 1*u.m
    c.NuTauTarget.UpCoilH = 45*u.cm
    c.NuTauTarget.LowCoilH = 30*u.cm
    c.NuTauTarget.CoilD = 105*u.cm
    c.NuTauTarget.BasisH = 57*u.cm
    c.NuTauTarget.H = 2*c.NuTauTarget.BasisH + c.NuTauTarget.CoilD + c.NuTauTarget.UpCoilH + c.NuTauTarget.LowCoilH
    c.NuTauTarget.zC = -c.decayVolume.length/2. - c.tauMS.GapV - c.tauMS.zSize - c.NuTauTarget.GapTS - c.NuTauTarget.LS/2

    #tau Bricks
    c.NuTauTarget.xdim = 2.0 * u.m
    c.NuTauTarget.ydim = 1.0 * u.m
    
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
    c.NuTauTT.TTX = 2.0*u.m
    c.NuTauTT.TTY = 0.9*u.m
    c.NuTauTT.TTZ= 6.0*u.cm
     
    c.NuTauTarget.zdim = 11* c.NuTauTarget.CellW + 12*c.NuTauTT.TTZ


    

