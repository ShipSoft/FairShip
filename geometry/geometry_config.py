from __future__ import print_function
import shipunit as u
import ROOT as r
from ShipGeoConfig import AttrDict, ConfigRegistry
# the following params should be passed through 'ConfigRegistry.loadpy' method
# muShieldDesign = 5  # 1=passive 2=active 5=TP design 6=magnetized hadron absorber 9=optimised with T4 as constraint, 8=requires config file
#                      10=with field map for hadron absorber
# nuTargetPassive = 1  #0 = with active layers, 1 = only passive
# nuTauTargetDesign  =   #0 = TP, 1 = NEW with magnet, 2 = NEW without magnet, 3 = 2018 design

# targetOpt      = 5  # 0=solid   >0 sliced, 5: 5 pieces of tungsten, 4 air slits, 17: molybdenum tungsten interleaved with H20
# strawOpt       = 0  # 0=simplistic tracking stations defined in veto.cxx  1=detailed strawtube design 4=sophisticated straw tube design, horizontal wires (default) 10=2cm straw diameter for 2018 layout
# preshowerOption = 0 # 1=simple preShower detector for conceptual studies, moves calo and muon stations
# tankDesign = 5 #  4=TP elliptical tank design, 5 = optimized conical rectangular design, 6=5 without segment-1
if "muShieldDesign" not in globals():
    muShieldDesign = 5
if "muShieldGeo" not in globals():
    muShieldGeo = None
if "nuTargetPassive" not in globals():
    nuTargetPassive = 1
if "nuTauTargetDesign" not in globals():
    nuTauTargetDesign = 0
    if muShieldDesign >= 7: 
        nuTauTargetDesign=1
if "targetOpt" not in globals():
    targetOpt = 18
if "strawDesign" not in globals():
    strawDesign = 4
if "tankDesign" not in globals():
    tankDesign = 6
if "CaloDesign" not in globals():
    CaloDesign = 0
if "Yheight" not in globals():
    Yheight = 10.
if "EcalGeoFile" not in globals():
    if tankDesign > 4:
        EcalGeoFile = "ecal_rect5x10m2.geo"
    else:
        EcalGeoFile = "ecal_ellipse5x10m2.geo"
if "HcalGeoFile" not in globals():
    if tankDesign > 4:
        HcalGeoFile = "hcal_rect.geo"
    else:
        HcalGeoFile = "hcal.geo"
if "muShieldStepGeo" not in globals():
    muShieldStepGeo = False
if "muShieldWithCobaltMagnet" not in globals():
    muShieldWithCobaltMagnet = 0

with ConfigRegistry.register_config("basic") as c:
    # global muShieldDesign, targetOpt, strawDesign, Yheight
    c.Yheight = Yheight*u.m
    # decision by the SP 
    totalLength       = 2.5*c.Yheight + 35*u.m
    extraVesselLength = totalLength - 50*u.m
    windowBulge = 1*u.m
    if tankDesign > 5: windowBulge = 25*u.cm
#
    magnet_design = 2
    if tankDesign == 5: magnet_design = 3
    if tankDesign == 6: magnet_design = 4
#
    c.strawDesign = strawDesign
    c.tankDesign = tankDesign
    c.magnetDesign = magnet_design
# cave parameters
    c.cave = AttrDict(z=0*u.cm)
    c.cave.floorHeightMuonShield = 5*u.m
    c.cave.floorHeightTankA = 4.2*u.m
    if strawDesign == 10:
        c.cave.floorHeightMuonShield = c.cave.floorHeightTankA  # avoid the gap, for 2018 geometry
    c.cave.floorHeightTankB = 2*u.m
#
    #neutrino detector
    c.nuTauTargetDesign=nuTauTargetDesign

    c.chambers = AttrDict(z=0*u.cm)
    magnetIncrease    = 100.*u.cm
    # make z coordinates for the decay volume and tracking stations relative to T4z
    # eventually, the only parameter which needs to be changed when the active shielding lenght changes.
    z4=2438.*u.cm+magnetIncrease+extraVesselLength
    if strawDesign != 4 and strawDesign != 10:
     print("this design ",strawDesign," is not supported, use strawDesign = 4 or 10")
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
     if tankDesign > 5: 
      c.Veto.outerSupport = 5.*u.mm
      c.Veto.outerSupportMed = "steel"
      c.Veto.lidThickness = 16.*u.mm
     else:
      c.Veto.outerSupport = 8.*u.mm
      c.Veto.outerSupportMed = "Aluminum"
      c.Veto.lidThickness = 80.*u.mm
     c.Veto.sensitiveThickness = 0.3*u.m
     c.Veto.sensitiveMed = "Scintillator"
     c.Veto.decayMed = "vacuums"
     c.Veto.rib = 3.*u.cm
     c.Veto.ribMed = "steel"
     # horizontal width at start and focus point, for conical/rectangular size
     # envelope (46,1.2) or (46,0.9) end at T4: (100.,2.5)  London slides, https://indico.cern.ch/event/508465/contributions/2166894/    
     c.zFocusX = +10*u.m # Decision taken 15/12/2016, Physics and Detector meeting
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
    if strawDesign==4:
     c.strawtubes.InnerStrawDiameter = 0.975*u.cm
     c.strawtubes.StrawPitch         = 1.76*u.cm  
     c.strawtubes.DeltazLayer        = 1.1*u.cm   
     c.strawtubes.DeltazPlane        = 2.6*u.cm   
     c.strawtubes.YLayerOffset = c.strawtubes.StrawPitch  / 2.
     c.strawtubes.YPlaneOffset = c.strawtubes.StrawPitch  / 4.
     c.strawtubes.FrameMaterial      = "aluminium"
     c.strawtubes.FrameLateralWidth  = 1.*u.cm
     c.strawtubes.DeltazFrame        = 10.*u.cm
    elif strawDesign==10:  # 10 - baseline for 2018 
     c.strawtubes.InnerStrawDiameter = 1.975*u.cm
     c.strawtubes.StrawPitch         = 3.60*u.cm  
     c.strawtubes.DeltazLayer        = 2.1*u.cm   
     c.strawtubes.DeltazPlane        = 4.2*u.cm   
     c.strawtubes.YLayerOffset = 1.9*u.cm        
     c.strawtubes.YPlaneOffset = 1.3*u.cm
     c.strawtubes.FrameMaterial      = "steel"
     c.strawtubes.FrameLateralWidth  = 1.2*u.m
     c.strawtubes.DeltazFrame        = 2.5*u.cm

    c.strawtubes.WallThickness      = 0.0039*u.cm
    c.strawtubes.OuterStrawDiameter = (c.strawtubes.InnerStrawDiameter + 2*c.strawtubes.WallThickness)
    
    c.strawtubes.StrawsPerLayer     = int(c.Yheight/c.strawtubes.StrawPitch)
    c.strawtubes.ViewAngle          = 5
    c.strawtubes.WireThickness      = 0.003*u.cm
    c.strawtubes.DeltazView         = 10.*u.cm
    c.strawtubes.VacBox_x           = 300.*u.cm
    c.strawtubes.VacBox_y           = 600.*u.cm * c.Yheight / (10.*u.m)
           
    c.Bfield = AttrDict(z=c.z)
    c.Bfield.max = 0 # 1.4361*u.kilogauss  # was 1.15 in EOI
    c.Bfield.y   = c.Yheight
    c.Bfield.x   = 3.*u.m
    c.Bfield.fieldMap = "field/MainSpectrometerField.txt"
    if c.magnetDesign>3:                          # MISIS design
      c.Bfield.YokeWidth=0.85*u.m  # full width       200.*cm; 
      c.Bfield.YokeDepth=1.75*u.m  # half length      200 *cm;
      c.Bfield.CoilThick=25.*u.cm  # thickness
      VesselThick=37.*u.cm;   # full thickness
      c.Bfield.x = 251.*u.cm+VesselThick; # half apertures
      c.Bfield.y = 501.*u.cm+VesselThick+c.Bfield.CoilThick

# TimeDet
    c.TimeDet = AttrDict(z=0)
    c.TimeDet.dzBarRow = 1.2 * u.cm
    c.TimeDet.dzBarCol = 2.4 * u.cm
    c.TimeDet.zBar = 1 * u.cm
    c.TimeDet.DZ = (c.TimeDet.dzBarRow + c.TimeDet.dzBarCol + c.TimeDet.zBar) / 2
    c.TimeDet.DX = 250 * u.cm
    c.TimeDet.DY = 500 * u.cm
    c.TimeDet.z = c.Chamber6.z + c.chambers.Tub6length + c.Veto.lidThickness + c.TimeDet.DZ + 1*u.cm # safety margin

    if CaloDesign==0:
     c.HcalOption = 1
     c.EcalOption = 1
     c.preshowerOption = 0
     c.splitCal = 0
    elif CaloDesign==3:
     c.HcalOption = 2
     c.EcalOption = 1
     c.preshowerOption = 0
     c.splitCal = 0
    elif CaloDesign==1:
     c.HcalOption = 1
     c.EcalOption = 1
     c.preshowerOption = 1
    elif CaloDesign==2:
     c.HcalOption = -1
     c.EcalOption = 2
     c.preshowerOption = 0
    else:
     print("CaloDesign option wrong -> ",CaloDesign)
     1/0

    presShowerDeltaZ = 0.
    if c.preshowerOption >0:
     PreshowerStart = c.TimeDet.z + c.TimeDet.DZ + 5*u.cm + presShowerDeltaZ
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

    c.SplitCal = AttrDict(z=0)
    c.SplitCal.ZStart = c.TimeDet.z + c.TimeDet.DZ + 5*u.cm + presShowerDeltaZ 
    c.SplitCal.XMax = 600.*u.cm/2. #290.*u.cm  #half length
    c.SplitCal.YMax = 1200.*u.cm/2. #510.*u.cm * c.Yheight / (10.*u.m)   #half length  
    c.SplitCal.Empty = 0*u.cm
    c.SplitCal.BigGap = 100*u.cm
    c.SplitCal.ActiveECALThickness = 0.56*u.cm
    c.SplitCal.FilterECALThickness = 0.28*u.cm #  0.56*u.cm   1.757*u.cm           
    c.SplitCal.FilterECALThickness_first = 0.28*u.cm
    c.SplitCal.ActiveHCALThickness = 90*u.cm
    c.SplitCal.FilterHCALThickness = 90*u.cm
    c.SplitCal.nECALSamplings = 50
    c.SplitCal.nHCALSamplings = 0
    c.SplitCal.ActiveHCAL = 0
    c.SplitCal.FilterECALMaterial= 3    # 1=scintillator 2=Iron 3 = lead  4 =Argon  
    c.SplitCal.FilterHCALMaterial= 2
    c.SplitCal.ActiveECALMaterial= 1
    c.SplitCal.ActiveHCALMaterial= 1
    c.SplitCal.ActiveECAL_gas_Thickness=1.12*u.cm
    c.SplitCal.num_precision_layers=1
    c.SplitCal.first_precision_layer=6
    c.SplitCal.second_precision_layer=10
    c.SplitCal.third_precision_layer=13
    c.SplitCal.ActiveECAL_gas_gap=10*u.cm
    c.SplitCal.NModulesInX = 2
    c.SplitCal.NModulesInY = 4
    c.SplitCal.NStripsPerModule = 50
    c.SplitCal.StripHalfWidth = 3*u.cm # c.SplitCal.XMax/(c.SplitCal.NStripsPerModule*c.SplitCal.NModulesInX)
    c.SplitCal.StripHalfLength = 150*u.cm # c.SplitCal.YMax/c.SplitCal.NModulesInY
    c.SplitCal.SplitCalThickness=(c.SplitCal.FilterECALThickness_first-c.SplitCal.FilterECALThickness)+(c.SplitCal.FilterECALThickness+c.SplitCal.ActiveECALThickness)*c.SplitCal.nECALSamplings+c.SplitCal.BigGap

    c.ecal  =  AttrDict(z = c.TimeDet.z + c.TimeDet.DZ  + 5*u.cm + presShowerDeltaZ)  #
    c.ecal.File = EcalGeoFile
    hcalThickness = 232*u.cm
    if  c.HcalOption == 2: hcalThickness = 110*u.cm  # to have same interaction length as before
    if not c.HcalOption < 0:
     c.hcal =  AttrDict(z=c.ecal.z + hcalThickness/2. + 45.*u.cm  )
     c.hcal.hcalSpace = hcalThickness + 5.5*u.cm
     c.hcal.File  =  HcalGeoFile
    else:
     c.hcal  =  AttrDict(z=c.ecal.z)
    if c.EcalOption == 1: 
     c.MuonStation0 = AttrDict(z=c.hcal.z+hcalThickness/2.+20.5*u.cm)
    if c.EcalOption == 2: 
     c.MuonStation0 = AttrDict(z=c.SplitCal.ZStart+10*u.cm+c.SplitCal.SplitCalThickness) 

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
    c.muShield.Field = 1.8 # in units of Tesla expected by ShipMuonShield
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

    c.muShieldStepGeo = muShieldStepGeo
    c.muShieldWithCobaltMagnet = muShieldWithCobaltMagnet

    # zGap to compensate automatic shortening of magnets
    zGap = 0.5 * c.muShield.dZgap  # halflengh of gap
    if muShieldDesign == 7:
        c.muShield.dZ1 = 0.7 * u.m + zGap
        c.muShield.dZ2 = 1.7 * u.m + zGap
        c.muShield.dZ3 = 2.0*u.m + zGap
        c.muShield.dZ4 = 2.0*u.m + zGap
        c.muShield.dZ5 = 2.75*u.m + zGap
        c.muShield.dZ6 = 2.4*u.m + zGap
        c.muShield.dZ7 = 3.0*u.m + zGap
        c.muShield.dZ8 = 2.35*u.m + zGap
        c.muShield.dXgap = 0.*u.m
    elif muShieldDesign == 9 or muShieldDesign == 10:
        c.muShield.Field = 1.7  # Tesla
        c.muShield.dZ1 = 0.35 * u.m + zGap
        c.muShield.dZ2 = 2.26 * u.m + zGap
        c.muShield.dZ3 = 2.08 * u.m + zGap
        c.muShield.dZ4 = 2.07 * u.m + zGap
        c.muShield.dZ5 = 2.81 * u.m + zGap
        c.muShield.dZ6 = 2.48 * u.m + zGap
        c.muShield.dZ7 = 3.05 * u.m + zGap
        c.muShield.dZ8 = 2.42 * u.m + zGap
        c.muShield.dXgap = 0. * u.m
    elif muShieldDesign == 8:
        assert muShieldGeo
        c.muShieldGeo = muShieldGeo
        print("Load geo")
        f = r.TFile.Open(muShieldGeo)
        params = r.TVectorD()
        params.Read('params')
        f.Close()
        c.muShield.dZ1 = 0.35*u.m + zGap
        c.muShield.dZ2 = 2.26*u.m + zGap
        c.muShield.dZ3 = params[2]
        c.muShield.dZ4 = params[3]
        c.muShield.dZ5 = params[4]
        c.muShield.dZ6 = params[5]
        c.muShield.dZ7 = params[6]
        c.muShield.dZ8 = params[7]
        c.muShield.dXgap = 0.*u.m
    if muShieldDesign in range(7, 11):
        c.muShield.length = 2 * (
              c.muShield.dZ1 + c.muShield.dZ2 +
              c.muShield.dZ3 + c.muShield.dZ4 +
              c.muShield.dZ5 + c.muShield.dZ6 +
              c.muShield.dZ7 + c.muShield.dZ8
        ) + c.muShield.LE
        c.muShield.z = -(c.decayVolume.length + c.muShield.length) / 2.

    if muShieldDesign == 3:
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
    if muShieldDesign > 9:  c.hadronAbsorber.WithConstField =  True

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
     c.target.L14 = 5.*u.cm
     c.target.M15 = "tungsten"
     c.target.L15 = 8.*u.cm
     c.target.M16 = "tungsten"
     c.target.L16 = 10.*u.cm
     c.target.M17 = "tungsten"
     c.target.L17 = 20.*u.cm
     c.target.M18 = "tungsten"
     c.target.L18 = 35.*u.cm
     c.target.sl  =  0.5*u.cm  # H20 slit *17 times
     c.target.xy  = 30.*u.cm   # full length in x and y
     c.target.length = 17*c.target.sl + c.target.L1 + 7*c.target.L2 + 3*c.target.L9 + c.target.L11 + 3*c.target.L12 + c.target.L16 + c.target.L17 + c.target.L18
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
       zF = c.target.z0+c.zFocusY
       c.strawtubes.vetoydim           = c.Yheight/2.*(c.vetoStation.z-c.strawtubes.DeltazView-zF)/(z4-zF)
       c.strawtubes.tr12ydim           = c.Yheight/2.*(c.TrackStation1.z-2*c.strawtubes.DeltazView-zF)/(z4-zF)
       c.strawtubes.tr34ydim           = int(c.Yheight/2.)  
    else:
       c.strawtubes.StrawLength12   = c.strawtubes.StrawLength
       c.strawtubes.StrawLengthVeto = c.strawtubes.StrawLength
       if tankDesign > 5: c.strawtubes.StrawLengthVeto = 0.5 # switch of veto strawtracker
       c.strawtubes.vetoydim           = int(c.Yheight/2.)
       c.strawtubes.tr12ydim           = int(c.Yheight/2.)
       c.strawtubes.tr34ydim           = int(c.Yheight/2.)

    #Parameters for tau neutrino target Magnet
    if nuTauTargetDesign!=2:
        c.EmuMagnet = AttrDict(z=0*u.cm)
        c.EmuMagnet.Design = nuTauTargetDesign
        c.EmuMagnet.B=1.25*u.tesla
        c.EmuMagnet.GapDown = 25*u.cm
        if c.EmuMagnet.Design==3:
            scale=1.
            c.EmuMagnet.WithConstField=False  #now loaded field map
            c.EmuMagnet.X = scale*2.2*u.m
            c.EmuMagnet.Y = scale*4.0*u.m
            c.EmuMagnet.Z = 7.2*u.m
            c.EmuMagnet.BaseX = scale*c.EmuMagnet.X 
            c.EmuMagnet.BaseY = scale*0.7*u.m
            c.EmuMagnet.BaseZ = scale*c.EmuMagnet.Z
            c.EmuMagnet.GapDown = 25*u.cm
            c.EmuMagnet.GapUp = 27*u.cm
            #c.EmuMagnet.ColX =scale*25*u.cm
            c.EmuMagnet.ColX = scale*60*u.cm
            c.EmuMagnet.ColY = scale*c.EmuMagnet.Y - 2 *scale * c.EmuMagnet.BaseY #avoid overlapping between bases and columns
            c.EmuMagnet.ColZ = scale*c.EmuMagnet.Z
            c.EmuMagnet.CutLength = scale * 45*u.cm
            c.EmuMagnet.CutHeight = scale * 144*u.cm
            c.EmuMagnet.CoilX = c.EmuMagnet.X-2*c.EmuMagnet.ColX
            c.EmuMagnet.CoilY = 50 *u.cm
            c.EmuMagnet.Height1 = c.EmuMagnet.Y-2*c.EmuMagnet.BaseY
            c.EmuMagnet.Height2 = c.EmuMagnet.Height1-2*c.EmuMagnet.CoilY
            c.EmuMagnet.Thickness = scale*40*u.cm
            c.EmuMagnet.PillarX = 0.5*u.m
            c.EmuMagnet.PillarZ = 0.5*u.m
            c.EmuMagnet.PillarY = 10*u.m - c.EmuMagnet.Y/2 - 0.1*u.mm - c.cave.floorHeightMuonShield
        if c.EmuMagnet.Design<2:
            c.EmuMagnet.WithConstField=True  #older geometries still use constant fields
            c.EmuMagnet.Z = 4.5*u.m
            c.EmuMagnet.GapUp = 27*u.cm
        if c.EmuMagnet.Design == 1:
          scale = 1.
          c.EmuMagnet.X = scale*1.7*u.m
          c.EmuMagnet.Y = scale*3.2*u.m
          c.EmuMagnet.Radius = scale*1.1*u.m
          c.EmuMagnet.Height1 = scale*30*u.cm
          c.EmuMagnet.Height2 = scale*c.EmuMagnet.Height1
          c.EmuMagnet.Distance = scale*c.EmuMagnet.X-2*c.EmuMagnet.Height1
          c.EmuMagnet.ColX =scale*c.EmuMagnet.Distance
          c.EmuMagnet.ColY = scale*0.7*u.m
          c.EmuMagnet.ColZ = 0.9*u.m
          c.EmuMagnet.BaseX = scale*c.EmuMagnet.Height1
          c.EmuMagnet.BaseY = scale*c.EmuMagnet.Y
          c.EmuMagnet.BaseZ = scale*c.EmuMagnet.Z
          c.EmuMagnet.PillarX = 0.5*u.m
          c.EmuMagnet.PillarZ = 0.5*u.m
          c.EmuMagnet.PillarY = 10*u.m - c.EmuMagnet.Y/2 - 0.1*u.mm - c.cave.floorHeightMuonShield
      #10m is the half-height of the cave
        if c.EmuMagnet.Design == 0: #TP MagnetConfig
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
          c.EmuMagnet.PillarX = 0 *u.m
          c.EmuMagnet.PillarZ = 0 * u.m
          c.EmuMagnet.PillarY = 0 * u.m
       
        

   
    #Parameters for tau muon detector
    c.tauMudet = AttrDict(z=0*u.cm)
    if nuTauTargetDesign<=2:
        c.tauMudet.NFe = 12
        c.tauMudet.NRpc= 11
        if nuTauTargetDesign==0: #TP
            c.tauMudet.YRyoke = 90*u.cm
            c.tauMudet.YRyoke_s = c.tauMudet.YRyoke-30*u.cm
            c.tauMudet.Xtot = 4.*u.m  
            c.tauMudet.YFe = 8*u.m
            c.tauMudet.Ytot = c.tauMudet.YFe + 2*c.tauMudet.YRyoke
            c.tauMudet.PillarX = 0*u.cm
            c.tauMudet.PillarZ = 0*u.cm
            c.tauMudet.PillarY=0 *u.cm
        if nuTauTargetDesign>=1: #NEW with Davide or without magnet
            scaleMudet=1.0
            c.tauMudet.YRyoke = scaleMudet*40*u.cm
            c.tauMudet.YRyoke_s = scaleMudet*27*u.cm
            c.tauMudet.Xtot = scaleMudet*1.5*u.m 
            c.tauMudet.Ytot = scaleMudet*3.8*u.m
            c.tauMudet.YFe = c.tauMudet.Ytot - 2*c.tauMudet.YRyoke
            c.tauMudet.PillarX = 40*u.cm
            c.tauMudet.PillarZ = 50*u.cm
            c.tauMudet.PillarY = 10*u.m - c.cave.floorHeightMuonShield - c.tauMudet.Ytot/2 -10*u.cm - 0.1*u.mm
        c.tauMudet.XRyoke = c.tauMudet.Xtot+20*u.cm
        c.tauMudet.XRyoke_s = c.tauMudet.Xtot
        c.tauMudet.Ztot = 4.76*u.m
        c.tauMudet.XFe = c.tauMudet.Xtot
        c.tauMudet.XRpc = c.tauMudet.Xtot
        c.tauMudet.YRpc = c.tauMudet.YFe-20*u.cm
        c.tauMudet.ZFe = 5.*u.cm
        c.tauMudet.ZRpc = 2.*u.cm
        c.tauMudet.ZArm = c.tauMudet.NFe*c.tauMudet.ZFe + c.tauMudet.NRpc*c.tauMudet.ZRpc
        c.tauMudet.GapD = 27.*u.cm
        c.tauMudet.GapM = 122*u.cm
        c.tauMudet.ZRyoke = 2*c.tauMudet.ZArm + c.tauMudet.GapM
        c.tauMudet.ZRyoke_s = c.tauMudet.GapM
        c.tauMudet.CoilH = 5*u.cm
        c.tauMudet.CoilW = 2*u.cm
        c.tauMudet.CoilG = 2*u.cm
        c.tauMudet.N =20
        c.tauMudet.zMudetC = -c.decayVolume.length/2. - c.tauMudet.GapD - c.tauMudet.Ztot/2
        c.tauMudet.B = 1.5 * u.tesla
    if nuTauTargetDesign==3:
        scaleMudet=1.
        c.tauMudet.NFethick = 4 #upstream slabs, more thick
        c.tauMudet.NFethin = 4 #downstream slabs, less thick
        c.tauMudet.NRpc= 8
        
        c.tauMudet.XFe = scaleMudet*1.950*u.m #layer dimensions, excluded supports
        c.tauMudet.YFe = scaleMudet*3.850*u.m

        c.tauMudet.ZFethick = 15.*u.cm
        c.tauMudet.ZFethin = 10.* u.cm

        c.tauMudet.XRpc = c.tauMudet.XFe
        c.tauMudet.YRpc = c.tauMudet.YFe
        c.tauMudet.ZRpc = 8.*u.cm
        #support structure
        c.tauMudet.UpperSupportX = 30 * u.cm
        c.tauMudet.UpperSupportY = 32 * u.cm
        c.tauMudet.LowerSupportX = 30 * u.cm
        c.tauMudet.LowerSupportY = 40 * u.cm
        c.tauMudet.LateralSupportX = 30.5 * u.cm
        c.tauMudet.LateralSupportY = 32 * u.cm

        c.tauMudet.Xtot = c.tauMudet.XFe + 2 * c.tauMudet.LateralSupportX#now we need to include also supports.
        c.tauMudet.Ytot = c.tauMudet.YFe + c.tauMudet.UpperSupportY + c.tauMudet.LowerSupportY 
        c.tauMudet.Ztot = c.tauMudet.NRpc*c.tauMudet.ZRpc+c.tauMudet.NFethick*c.tauMudet.ZFethick + c.tauMudet.NFethin*c.tauMudet.ZFethin
        #c.tauMudet.zMudetC = -c.decayVolume.length/2. - c.tauMudet.Ztot/2
        c.tauMudet.zMudetC = c.Chamber1.z -c.chambers.Tub1length - c.tauMudet.Ztot/2 -31*u.cm;
        #lateral cuts
        c.tauMudet.CutHeight = 78.548 * u.cm
        c.tauMudet.CutLength = (c.tauMudet.CutHeight / 2) / (r.TMath.Tan(r.TMath.DegToRad() * 55))
        #upper cover
        c.tauMudet.XCov = c.tauMudet.XFe
        c.tauMudet.YCov = 6*u.cm
        c.tauMudet.ZCov = c.tauMudet.NFethick*c.tauMudet.ZFethick+c.tauMudet.NRpc*c.tauMudet.ZRpc+c.tauMudet.NFethin*c.tauMudet.ZFethin
        
        c.tauMudet.YSpacing = 28.5*u.cm
        #lateral cover
        c.tauMudet.XLateral = 7*u.cm
        c.tauMudet.YLateral = c.tauMudet.LateralSupportY
        c.tauMudet.ZLateral = c.tauMudet.ZCov
        #lateral cross
        c.tauMudet.XCross = 2*u.cm
        c.tauMudet.YCross = c.tauMudet.YFe-2*c.tauMudet.YLateral-2*c.tauMudet.YSpacing - 8*u.cm
        c.tauMudet.ZCross = c.tauMudet.ZCov
        c.tauMudet.WidthArm = 2* u.cm
        #RPC frame
        c.tauMudet.XRpc_outer = 284.5*u.cm
        c.tauMudet.YRpc_outer = 428.2*u.cm
        c.tauMudet.ZRpc_outer = 2.2*u.cm
        c.tauMudet.XRpc_inner = 190*u.cm
        c.tauMudet.YRpc_inner = 372*u.cm
        c.tauMudet.ZRpc_inner = 1.7*u.cm
        #RPC Gap
        c.tauMudet.XRpcGap = c.tauMudet.XRpc_inner
        c.tauMudet.YRpcGap = 120*u.cm
        c.tauMudet.ZRpcGap = 0.2*u.cm
        
        c.tauMudet.PillarX = 40*u.cm
        c.tauMudet.PillarZ = 50*u.cm
        c.tauMudet.PillarY = 10*u.m - c.cave.floorHeightMuonShield - c.tauMudet.Ytot/2 - 0.1*u.mm
    c.tauMudet.XGas =  c.tauMudet.XRpc
    c.tauMudet.YGas =  c.tauMudet.YRpc
    c.tauMudet.ZGas = 1*u.mm
    c.tauMudet.XStrip =  c.tauMudet.XRpc
    c.tauMudet.YStrip =  c.tauMudet.YRpc
    c.tauMudet.ZStrip = 0.02*u.mm
    c.tauMudet.XPet =  c.tauMudet.XRpc
    c.tauMudet.YPet =  c.tauMudet.YRpc
    c.tauMudet.ZPet = 0.1*u.mm
    c.tauMudet.XEle =  c.tauMudet.XRpc
    c.tauMudet.YEle =  c.tauMudet.YRpc
    c.tauMudet.ZEle = 1*u.mm

    if nuTauTargetDesign==0 or nuTauTargetDesign==1:
       c.EmuMagnet.zC = -c.decayVolume.length/2. - c.tauMudet.GapD - c.tauMudet.Ztot - c.EmuMagnet.GapDown - c.EmuMagnet.Z/2

    if nuTauTargetDesign==3:
       c.EmuMagnet.zC = c.tauMudet.zMudetC - c.tauMudet.Ztot/2 - c.EmuMagnet.GapDown - c.EmuMagnet.Z/2   
       
    #tau Bricks
    c.NuTauTarget = AttrDict(z=0*u.cm)
    c.NuTauTarget.Design = nuTauTargetDesign
    if nuTauTargetDesign!=2:
        c.NuTauTarget.zC = c.EmuMagnet.zC
    if nuTauTargetDesign==2:
        c.NuTauTarget.zC = -c.decayVolume.length/2. - c.tauMudet.GapD - c.tauMudet.Ztot -2.5*u.m

    if c.NuTauTarget.Design == 0: #TP                         
        c.NuTauTarget.row=7
        c.NuTauTarget.col=15
        c.NuTauTarget.wall=11
    if c.NuTauTarget.Design == 1: #NEW with magnet
        c.NuTauTarget.row=14
        c.NuTauTarget.col=6
        c.NuTauTarget.wall=11
    if c.NuTauTarget.Design == 2: #NEW with NO magnet
        c.NuTauTarget.row=20
        c.NuTauTarget.col=9
        c.NuTauTarget.wall=20
    if c.NuTauTarget.Design == 3: #One unique magnet, eventually more than one target volume 
        #c.NuTauTarget.n_plates = 56 
        c.NuTauTarget.row = 7
        c.NuTauTarget.col = 7
        c.NuTauTarget.wall = 19
    c.NuTauTarget.n_plates = 56
     
    c.NuTauTarget.target = 1  #number of neutrino target volumes

    c.NuTauTarget.nuTargetPassive = nuTargetPassive

    # space for the structure that holds the brick
    c.NuTauTarget.Ydist = 0.2*u.cm
    c.NuTauTarget.SingleEmFilm = True
    c.NuTauTarget.EmTh = 0.0070 * u.cm
    c.NuTauTarget.EmX = 12.5 * u.cm
    c.NuTauTarget.EmY = 9.9 * u.cm
    c.NuTauTarget.PBTh = 0.0175 * u.cm
    c.NuTauTarget.LeadTh = 0.1 * u.cm
    c.NuTauTarget.EPlW = 2* c.NuTauTarget.EmTh + c.NuTauTarget.PBTh
    c.NuTauTarget.AllPW = c.NuTauTarget.LeadTh + c.NuTauTarget.EPlW
    c.NuTauTarget.BrX = 12.9 * u.cm
    c.NuTauTarget.BrY = 10.5 * u.cm
    c.NuTauTarget.BrPackZ = 0.1045 * u.cm
    c.NuTauTarget.BrPackX = c.NuTauTarget.BrX - c.NuTauTarget.EmX
    c.NuTauTarget.BrPackY = c.NuTauTarget.BrY - c.NuTauTarget.EmY
    c.NuTauTarget.BrZ = c.NuTauTarget.n_plates * c.NuTauTarget.AllPW + c.NuTauTarget.EPlW + c.NuTauTarget.BrPackZ

 #TargetTrackers!
    c.NuTauTT = AttrDict(z=0*u.cm)
    c.NuTauTT.design = nuTauTargetDesign
    c.NuTauTT.n_hor_planes = 11
    c.NuTauTT.n_vert_planes = 7
    c.NuTauTT.scifimat_width = 13.06 * u.cm # old value 13.045
    c.NuTauTT.scifimat_hor = 94.315 * u.cm #13.045 * 7 + endpieces = length of hor. mats
    c.NuTauTT.scifimat_vert = 146.495 * u.cm #13.045 * 11 + endpieces = length of vert. mats
    c.NuTauTT.scifimat_z = 0.145 * u.cm   # Scintillating fiber mat
    c.NuTauTT.support_z = 0.02 * u.cm     # Support carbon composite
    c.NuTauTT.honeycomb_z = 2 * u.cm      # Airex (or Nomex)
    c.NuTauTT.TTX = c.NuTauTT.scifimat_hor
    c.NuTauTT.TTY = c.NuTauTT.scifimat_vert
    c.NuTauTT.TTZ = 2 * c.NuTauTT.support_z + 2 * c.NuTauTT.scifimat_z + c.NuTauTT.honeycomb_z 
    c.NuTauTT.n = c.NuTauTarget.wall
    # should be called after TTX, TTY
    c.NuTauTarget.xdim = c.NuTauTT.TTX 
    c.NuTauTarget.ydim = c.NuTauTT.TTY 
    c.NuTauTarget.WallXDim = c.NuTauTarget.col*c.NuTauTarget.BrX
    c.NuTauTarget.WallYDim = c.NuTauTarget.row*c.NuTauTarget.BrY+(c.NuTauTarget.row-1)*c.NuTauTarget.Ydist
    c.NuTauTarget.WallZDim = c.NuTauTarget.BrZ

 #HPT
    c.tauHPT = AttrDict(z=0*u.cm)
    c.tauHPT.design = nuTauTargetDesign
    c.tauHPT.n_hor_planes = 11
    c.tauHPT.n_vert_planes = 7
    c.tauHPT.scifimat_width = c.NuTauTT.scifimat_width
    c.tauHPT.scifimat_hor = c.NuTauTT.scifimat_hor
    c.tauHPT.scifimat_vert = c.NuTauTT.scifimat_vert
    c.tauHPT.scifimat_z = c.NuTauTT.scifimat_z
    c.tauHPT.support_z = c.NuTauTT.support_z
    c.tauHPT.honeycomb_z = c.NuTauTT.honeycomb_z
    c.tauHPT.TX = c.tauHPT.scifimat_hor
    c.tauHPT.TY = c.tauHPT.scifimat_vert
    c.tauHPT.TZ = 2 * c.tauHPT.support_z + 2 * c.tauHPT.scifimat_z + c.tauHPT.honeycomb_z 

    if nuTauTargetDesign<3:
        c.tauHPT.DZ = 15*u.cm
        c.tauHPT.DX = c.tauMudet.XFe
        c.tauHPT.DY = c.tauMudet.YFe
        c.tauHPT.ConcreteX = c.tauHPT.DX
        c.tauHPT.ConcreteY = c.tauMudet.Ytot/2 - c.tauHPT.DY/2
        c.tauHPT.ConcreteZ = c.tauHPT.DZ
    if nuTauTargetDesign==3:
        c.tauHPT.SRDY = 10 * u.cm  #additional detectors for improving acceptance
        c.tauHPT.DX = c.tauHPT.TX
        c.tauHPT.DY = c.tauHPT.TY
        c.tauHPT.DZ = c.tauHPT.TZ
        c.tauHPT.nHPT = 5 # number of downstream trackers after neutrino target

    if nuTauTargetDesign!=2: #TP or NEW with magnet
        c.NuTauTarget.RohG = 1.5 * u.cm
        c.NuTauTarget.LayerCESW = c.NuTauTarget.RohG + c.NuTauTarget.EPlW
        c.NuTauTarget.CESPack = 0.3055 * u.cm
        c.NuTauTarget.CESW = 2 * c.NuTauTarget.LayerCESW + c.NuTauTarget.EPlW + c.NuTauTarget.CESPack
        c.NuTauTarget.CellW = c.NuTauTarget.BrZ + c.NuTauTarget.CESW
        if nuTauTargetDesign!=3:
            c.NuTauTarget.zdim = c.NuTauTarget.wall* c.NuTauTarget.CellW + (c.NuTauTarget.wall+1)*c.NuTauTT.TTZ
        if nuTauTargetDesign ==3:
            c.NuTauTarget.zdim = c.NuTauTarget.wall* c.NuTauTarget.CellW + c.NuTauTarget.wall*c.NuTauTT.TTZ
            c.NuTauTarget.zC = c.EmuMagnet.zC - c.NuTauTarget.zdim/2.
            c.tauHPT.TotalDZ = (c.EmuMagnet.Z - c.EmuMagnet.Height1) - c.NuTauTarget.zdim # MagRegion-Target 
            c.tauHPT.distHPT = (c.tauHPT.TotalDZ - c.tauHPT.nHPT * c.tauHPT.DZ) / (c.tauHPT.nHPT - 1)                    

    if nuTauTargetDesign == 2:  #NEW with NO magnet
        c.NuTauTarget.RohG = 0 * u.cm
        c.NuTauTarget.LayerCESW =0 *u.cm
        c.NuTauTarget.CESPack = 0* u.cm
        c.NuTauTarget.CESW = 0*u.cm
        c.NuTauTarget.CellW = c.NuTauTarget.BrZ
        c.NuTauTarget.zdim = c.NuTauTarget.wall* c.NuTauTarget.CellW + (c.NuTauTarget.wall+1)*c.NuTauTT.TTZ

    c.NuTauTarget.BaseX =  c.NuTauTarget.xdim + 20*u.cm
    c.NuTauTarget.BaseY = 20*u.cm
    c.NuTauTarget.BaseZ = c.NuTauTarget.zdim +40*u.cm
    c.NuTauTarget.PillarX = 0.5*u.m
    c.NuTauTarget.PillarZ = 0.5*u.m
    c.NuTauTarget.PillarY = 10*u.m - c.NuTauTarget.ydim/2 -c.NuTauTarget.BaseY- 0.1*u.mm - c.cave.floorHeightMuonShield

    #Upstream Tagger
    c.UpstreamTagger = AttrDict(z=0)
    c.UpstreamTagger.Z_Glass = 0.2 * u.cm
    c.UpstreamTagger.Y_Glass = 105 * u.cm   
    c.UpstreamTagger.X_Glass = 223 * u.cm   
    c.UpstreamTagger.Z_Glass_Border = 0.2 * u.cm
    c.UpstreamTagger.Y_Glass_Border = 1.0 * u.cm
    c.UpstreamTagger.X_Glass_Border = 1.0 * u.cm
    c.UpstreamTagger.Z_PMMA = 0.8 * u.cm
    c.UpstreamTagger.Y_PMMA = 108 * u.cm
    c.UpstreamTagger.X_PMMA = 226 * u.cm
    c.UpstreamTagger.DY_PMMA = 1.5 * u.cm
    c.UpstreamTagger.DX_PMMA = 1.5 * u.cm
    c.UpstreamTagger.DZ_PMMA = 0.1 * u.cm
    c.UpstreamTagger.Z_FreonSF6 = 0.1 * u.cm
    c.UpstreamTagger.Y_FreonSF6 = 107 * u.cm
    c.UpstreamTagger.X_FreonSF6 = 225 * u.cm
    c.UpstreamTagger.Z_FreonSF6_2 = 0.8 * u.cm
    c.UpstreamTagger.Y_FreonSF6_2 = 0.5 * u.cm
    c.UpstreamTagger.X_FreonSF6_2 = 0.5 * u.cm
    c.UpstreamTagger.Z_FR4 = 0.15 * u.cm
    c.UpstreamTagger.Y_FR4 = 111 * u.cm
    c.UpstreamTagger.X_FR4 = 229 * u.cm
    c.UpstreamTagger.Z_Aluminium = 1.1503 * u.cm
    c.UpstreamTagger.Y_Aluminium = 111 * u.cm
    c.UpstreamTagger.X_Aluminium = 233 * u.cm
    c.UpstreamTagger.DZ_Aluminium = 0.1 * u.cm
    c.UpstreamTagger.DY_Aluminium = 1 * u.cm
    c.UpstreamTagger.DX_Aluminium = 0.2 * u.cm
    c.UpstreamTagger.Z_Air = 1.1503 * u.cm
    c.UpstreamTagger.Y_Air = 0 * u.cm
    c.UpstreamTagger.X_Air = 2 * u.cm
    c.UpstreamTagger.Z_Strip = 0.0003 * u.cm
    c.UpstreamTagger.Y_Strip = 3.1 * u.cm
    c.UpstreamTagger.X_Strip = 229 * u.cm
    c.UpstreamTagger.X_Strip64 = 3.3 * u.cm
    c.UpstreamTagger.Y_Strip64 = 111 * u.cm
    c.UpstreamTagger.Z_Position = c.tauMudet.zMudetC + (c.tauMudet.Ztot)/2 + 12.0*u.cm
