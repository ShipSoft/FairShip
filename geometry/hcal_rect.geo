# By //Dr.Sys 2016.05.31
# Hcal with 924 modules readout from both sides (1848 channels).
# Module size is 24x24 cm
# length about 2 m (8.5 \lambda). 
XPos=0		#Position of Hcal center	[cm]
YPos=0		#Position of Hcal center	[cm]
ZPos=4500	#Position of Hcal center	[cm]
NLayers=66	#Total number of layers		
N1Layers=18	#Number of layers in first section		
ModuleSize=24.0	#Module size			[cm]
Absorber=1.5	#Absorber thickness in layer	[cm]
AbsorberMaterial=ECALSteel #Material of absorber. See media.geo
Scin=.5		#Scintillator thickness in layer[cm]
Tyveec=.006	#Tyveec thickness in layer	[cm]
HoleRadius=.075 #Radius of hole in the calorimeter		[cm]
FiberRadius=.06 #Radius of fiber				[cm]
Steel=0.01	#Thickness of steel tapes			[cm]
TileEdging=0.01	#Thickness of white coating near tiles edges 	[cm]
XSemiAxis=315	#X semiaxis of keeping volume	[cm]
YSemiAxis=630	#Y semiaxis of keeping volume	[cm]
CF=1		#Is there clear fiber in cell type 1
NH=12		#Number of holes for cell type 1
LightMap=none	#Light collection
usesimplegeo=1	#Use simplified geometry
HcalZSize=232.0	#Z size of HCAL container	[cm]
ECut=100e-6	#Geant cuts CUTGAM CUTELE BCUTE BCUTM DCUTE [GeV]
HCut=300e-6	#Geant cuts CUTNEU CUTHAD CUTMUO DCUTM PPCUTM [GeV]
FastMC=0	#0 for full MC (with showers in HCAL), 1 for fast MC (only hits at sensitive plane before HCAL)
structure
#Zero for no module here.
#         1         2   
#1234567890123456789012
1111111111111111111111 # 0
1111111111111111111111 # 1
1111111111111111111111 # 2
1111111111111111111111 # 3
1111111111111111111111 # 4
1111111111111111111111 # 5
1111111111111111111111 # 6
1111111111111111111111 # 7
1111111111111111111111 # 8
1111111111111111111111 # 9
1111111111111111111111 #10
1111111111111111111111 #11
1111111111111111111111 #12
1111111111111111111111 #13
1111111111111111111111 #14
1111111111111111111111 #15
1111111111111111111111 #16
1111111111111111111111 #17
1111111111111111111111 #18
1111111111111111111111 #19
1111111111111111111111 #20
1111111111111111111111 #21
1111111111111111111111 #22
1111111111111111111111 #23
1111111111111111111111 #24
1111111111111111111111 #25
1111111111111111111111 #26
1111111111111111111111 #27
1111111111111111111111 #28
1111111111111111111111 #29
1111111111111111111111 #30
1111111111111111111111 #31
1111111111111111111111 #32
1111111111111111111111 #33
1111111111111111111111 #34
1111111111111111111111 #35
1111111111111111111111 #36
1111111111111111111111 #37
1111111111111111111111 #38
1111111111111111111111 #39
1111111111111111111111 #40
1111111111111111111111 #41
