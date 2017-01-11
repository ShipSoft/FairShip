import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry
# the following params should be passed through 'ConfigRegistry.loadpy' method
# none for the moment
with ConfigRegistry.register_config("basic") as c:
    c.target = AttrDict(z0=0*u.cm)
    c.Bfield = AttrDict(z=0*u.cm)
    c.Bfield.max = 0 # 1.4361*u.kilogauss for SHiP
    c.Bfield.y   = 1.*u.m # dummy value
    c.Bfield.x   = 3.*u.m # dummy value
    #BOX (Brick!)
    c.Box = AttrDict(z=0*u.cm)
    c.Box.BX = 13*u.cm
    c.Box.BY = 11*u.cm
    c.Box.BZ = 20*u.cm
    c.Box.zBox = 0 * u.cm
    c.Box.EmTh = 0.0045 * u.cm
    c.Box.EmX = 10 * u.cm #for the moment, replace the previous values for normal simulations
    c.Box.EmY = 10 * u.cm
    c.Box.PBTh = 0.0205 * u.cm
    c.Box.MolybdenumTh = 0.3 * u.cm
    c.Box.EPlW = 2* c.Box.EmTh + c.Box.PBTh
    c.Box.AllPW = c.Box.MolybdenumTh + c.Box.EPlW
    c.Box.BrX = 12.9 *u.cm
    c.Box.BrY = 10.5 *u.cm
    c.Box.BrPackZ = 0.1 * u.cm
    c.Box.BrPackX = c.Box.BrX - c.Box.EmX
    c.Box.BrPackY = c.Box.BrY - c.Box.EmY
    c.Box.BrZ = 54 * c.Box.AllPW + c.Box.EPlW +c.Box.BrPackZ
    c.Box.PX = 0*u.cm	
    c.Box.PY = 0*u.cm
    c.Box.PZ = 0*u.cm #(variables for the old brick configuration)
    c.Box.CoolX = 10 * u.cm #has this to change to adapt it at SHiP target trasversal dimensions?
    c.Box.CoolY = 10 * u.cm
    c.Box.CoolZ = 0.5 * u.cm
    c.Box.CoatX = 10 * u.cm #has this to change to adapt it at SHiP target trasversal dimensions?
    c.Box.CoatY = 10 * u.cm
    c.Box.CoatZ = 0.1 * u.cm
    c.Box.TX = 10 * u.cm
    c.Box.TY = 10 * u.cm

    #to change the run, uncheck the corresponding TZ and Checkmin 
    c.Box.TZ = 15.282 * u.cm #Run 1
    c.Box.Checkmin = -1000 *u.cm
    #c.Box.TZ = 30.388 *u.cm # Run 2
    #c.Box.Checkmin = -15.8 *u.cm
    #c.Box.TZ = 49.01 *u.cm # Run 3
    #c.Box.Checkmin= -14.6 * u.cm 
    #c.Box.TZ = 65.752 *u.cm # Run 4
    #c.Box.Checkmin = -18.2 * u.cm
    #c.Box.TZ = 79.369 *u.cm # Run 5
    #c.Box.Checkmin = -14.6 * u.cm 
    #c.Box.TZ = 90.103 *u.cm # Run 6
    #c.Box.Checkmin = -11.6 *u.cm
    #c.Box.TZ = 98.785 *u.cm # Run 7
    #c.Box.Checkmin = -9.8 *u.cm
    #c.Box.TZ = 107.335 *u.cm # Run 8
    #c.Box.Checkmin = -9.5 *u.cm
    #c.Box.TZ = 116.200 *u.cm # Run 9
    #c.Box.Checkmin = -9.7 *u.cm 
    #c.Box.TZ = 124.935 *u.cm # Run 10 
    #c.Box.Checkmin = -9.7 *u.cm 
  
    #c.Box.TZ = 136 *u.cm # All target sensitive 
    c.Box.Checkmax = 0 

    #Spectrometer
    c.Spectrometer = AttrDict(z = 0*u.cm)
   #Parameters for Goliath by Annarita
    c.Spectrometer.LS = 4.5*u.m
    c.Spectrometer.TS = 3.6*u.m
    c.Spectrometer.CoilR = 1*u.m
    c.Spectrometer.UpCoilH = 45*u.cm
    c.Spectrometer.LowCoilH = 30*u.cm
    c.Spectrometer.CoilD = 105*u.cm
    c.Spectrometer.BasisH = 57*u.cm
    c.Spectrometer.H = 2*c.Spectrometer.BasisH + c.Spectrometer.CoilD + c.Spectrometer.UpCoilH + c.Spectrometer.LowCoilH
    c.Spectrometer.DX = 1*u.m
    c.Spectrometer.DY = 0.5*u.m
    c.Spectrometer.DZ = 2*u.cm
    c.Spectrometer.SX = c.Spectrometer.DX
    c.Spectrometer.SY = c.Spectrometer.DY
    c.Spectrometer.SZ = c.Spectrometer.DZ*4 + 40 *u.cm + 4.5*u.m #4.5 m is the Goliath length
    c.Spectrometer.zBox = c.Box.PZ + c.Spectrometer.SZ/2 + 0.1 * u.cm

    #Muon Filter
    
    c.MuonTagger = AttrDict(z = 0*u.cm)
    c.MuonTagger.PTh = 34 * u.cm;
    c.MuonTagger.STh = 5.0 * u.cm
    c.MuonTagger.BX = 2 * u.m
    c.MuonTagger.BY = 1.5 * u.m
    c.MuonTagger.BZ = c.MuonTagger.PTh * 5 + c.MuonTagger.STh * 6
    c.MuonTagger.zBox = c.Spectrometer.SZ+ c.MuonTagger.BZ/2 + c.Box.PZ + 5*u.cm

    c.MuonTagger.PX = c.MuonTagger.BX
    c.MuonTagger.PY = c.MuonTagger.BY
    c.MuonTagger.SX = c.MuonTagger.BX
    c.MuonTagger.SY = c.MuonTagger.BY
