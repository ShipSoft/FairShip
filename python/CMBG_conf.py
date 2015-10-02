import ROOT, os
import shipunit as u

def configure(CMBG, ship_geo):
	#handles external variables for the Cosmic Muon Backgorund Generator within FairShip
	Z1 = ship_geo.MuonStation3.z # 3900
	Z2 = ship_geo.vetoStation.z # -1968
	Z3 = ship_geo.chambers.Tub1length # 250
	zmiddle = (Z1 + (Z2-2*Z3))/2 # 716
	
	# CMBG production area
	CMBG.xdist = 3000 # production area size [cm]
	CMBG.zdist = 9000 # production area size [cm]
	# DetectorBox
	CMBG.yBox = 600 # box top layer [cm]
	CMBG.xBox = 300 # box side layer [cm]
	CMBG.zBox = 3650 # box length [cm]
	CMBG.z0 = zmiddle # relative coordinate system [cm] (Z_muonstation + (Z_veto - 2 * Z_Tub1))/2,... Z_veto <0 ! ->z0 = 716, sets the middle of the production area
	#setup
	CMBG.n_EVENTS = 400000; # #simulated events per "spill"
	CMBG.minE = 1.0 #low energy limit for the Low-energy simulation [GeV]
	
