# By //Dr.Sys 2014.11.14
# Hcal with 756 modules readout from both sides (1512 channels).
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
0000000111111110000000 # 0
0000001111111111000000 # 1
0000011111111111100000 # 2
0000111111111111110000 # 3
0000111111111111110000 # 4
0001111111111111111000 # 5
0001111111111111111000 # 6
0011111111111111111100 # 7
0011111111111111111100 # 8
0011111111111111111100 # 9
0111111111111111111110 #10
0111111111111111111110 #11
0111111111111111111110 #12
0111111111111111111110 #13
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
0111111111111111111110 #28
0111111111111111111110 #29
0111111111111111111110 #30
0111111111111111111110 #31
0011111111111111111100 #32
0011111111111111111100 #33
0011111111111111111100 #34
0001111111111111111000 #35
0001111111111111111000 #36
0000111111111111110000 #37
0000111111111111110000 #38
0000011111111111100000 #39
0000001111111111000000 #40
0000000111111110000000 #41
