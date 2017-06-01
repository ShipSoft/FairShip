from ROOT import *
from array import array

gROOT.ProcessLine(".x mystyle.C")
pdg = TDatabasePDG.Instance()

### Add what is missed:
### PDG nuclear states are 10-digit numbers
### 10LZZZAAAI e.g. deuteron is 
### 1000010020
### from http://svn.cern.ch/guest/AliRoot/trunk/STEER/STEERBase/AliPDG.cxx and https://github.com/FairRootGroup/FairRoot/blob/master/eventdisplay/FairEventManager.cxx
### https://geant4.web.cern.ch/geant4/UserDocumentation/UsersGuides/ForApplicationDeveloper/html/AllResources/TrackingAndPhysics/particleList.src/ions/index.html

def PrintEventPart(particles,pdg):
    print "Particles in the event:"
    for (pid,part) in enumerate(particles):
        print pid, pdg.GetParticle(part.GetPdgCode()).GetName(), part.GetMotherId()
    print
def PrintRPChits(rpc,pdg):
    print "Hits in the RPC:"
    for (ix,RPCpt) in enumerate(rpc):
        print ix,RPCpt.GetZ(), pdg.GetParticle(RPCpt.PdgCode()).GetName(), RPCpt.GetTrackID()
    print

if not(pdg.GetParticle(1000010020)):
    pdg.AddParticle("Deuteron","Deuteron", 1.875613e+00, kTRUE, 0,3,"Ion",1000010020)
    pdg.AddAntiParticle("AntiDeuteron", - 1000010020)
    
if not(pdg.GetParticle(1000010030)):
    pdg.AddParticle("Triton","Triton", 2.808921e+00, kFALSE, 3.885235e+17,3,"Ion",1000010030);
    pdg.AddAntiParticle("AntiTriton", - 1000010030);

if not(pdg.GetParticle(1000020040) ):
    #pdg.AddParticle("Alpha","Alpha",4*kAu2Gev+2.424e-3,kTRUE,khShGev/(12.33*kYear2Sec),6,"Ion",ionCode);
    pdg.AddParticle("Alpha","Alpha",3.727379e+00,kFALSE,0,6,"Ion",1000020040);
    pdg.AddAntiParticle("AntiAlpha", - 1000020040);
        
if not(pdg.GetParticle(1000020030) ):
    pdg.AddParticle("HE3","HE3",2.808391e+00,kFALSE,0,6,"Ion",1000020030);
    pdg.AddAntiParticle("AntiHE3", -1000020030);

if not(pdg.GetParticle(1000030070) ):
    print "TO BE CHECKED the data insert for Li7Nucleus"
    pdg.AddParticle("Li7Nucleus","Li7Nucleus",3.727379e+00/4.*7.,kFALSE,0,0,"Boson",1000030070);
    
if not(pdg.GetParticle(1000060120) ):
    print "ERROR: random values insert for C12Nucleus"
    pdg.AddParticle("C12Nucleus","C12Nucleus",0.1,kFALSE,0,0,"Isotope",1000060120);
        
if not(pdg.GetParticle(1000030060) ):
    print "ERROR: random values insert for Li6Nucleus"
    pdg.AddParticle("Li6Nucleus","Li6Nucleus",6.015121,kFALSE,0,0,"Isotope",1000030060);       

if not(pdg.GetParticle(1000070140) ):
    print "ERROR: random values insert for for N14"
    pdg.AddParticle("N14","N14",0.1,kTRUE,0,0,"Isotope",1000070140);       

if not(pdg.GetParticle(1000050100) ):
    print "TO BE CHECKED the data insert for B10"
    pdg.AddParticle("B10","B10",10.0129370,kTRUE,0,0,"Isotope",1000050100);

if not(pdg.GetParticle(1000020060) ):
    print "TO BE CHECKED the data insert for He6"
    pdg.AddParticle("He6","He6",6.0188891,kFALSE,806.7e-3,0,"Isotope",1000020060);

if not(pdg.GetParticle(1000040080) ):
    print "TO BE CHECKED the data insert for Be8"
    pdg.AddParticle("Be8","Be8",8.00530510,kFALSE,6.7e-17,0,"Isotope",1000040080);

if not(pdg.GetParticle(1000030080) ):
    print "TO BE CHECKED the data insert for Li8"
    pdg.AddParticle("Li8","Li8",8.002248736,kTRUE,178.3e-3,0,"Isotope",1000030080);    
 
if not(pdg.GetParticle(1000040170) ):
    print "ERROR: didn't find what is it particle with code 1000040170, random number inserted!"
    pdg.AddParticle("None","None",0.1,kFALSE,0,0,"Isotope",1000040170);    

if not(pdg.GetParticle(1000040100) ):
    print "TO BE CHECKED the data insert for Be10"
    pdg.AddParticle("Be10","Be10",10.0135338,kTRUE,5.004e+9,0,"Isotope",1000040100);    

if not(pdg.GetParticle(1000040070) ):
    print "TO BE CHECKED the data insert for Be7"
    pdg.AddParticle("Be7","Be7",11.021658,kTRUE,13.81,0,"Isotope",1000040070);    

if not(pdg.GetParticle(1000230470) ):
    print "ERROR: didn't find what is it particle with code 1000230470, random number inserted!"
    pdg.AddParticle("None2","None2",0.1,kFALSE,0,0,"Isotope",1000230470);    

if not(pdg.GetParticle(1000080170) ):
    print "ERROR: didn't find what is it particle with code 1000080170, random number inserted!"
    pdg.AddParticle("None3","None3",0.1,kFALSE,0,0,"Isotope",1000080170);    

if not(pdg.GetParticle(1000240500) ):
    print "ERROR: didn't find what is it particle with code 1000240500, random number inserted!"
    pdg.AddParticle("None4","None4",0.1,kFALSE,0,0,"Isotope",1000240500);    

if not(pdg.GetParticle(1000210450) ):
    print "ERROR: didn't find what is it particle with code 1000210450, random number inserted (Sc45Nucleus)!"
    pdg.AddParticle("Sc45Nucleus","Sc45Nucleus",0.1,kFALSE,0,0,"Isotope",1000210450);    

if not(pdg.GetParticle(1000040090) ):
    print "TO BE CHECKED the data insert for Be9"
    pdg.AddParticle("Be9","Be9",9.0121822,kFALSE,0,0,"Isotope",1000040090);    

if not(pdg.GetParticle(1000080160) ):
    print "TO BE CHECKED the data insert for O16"
    pdg.AddParticle("O16","O16",15.99491461956,kFALSE,0,0,"Isotope",1000080160);    

if not(pdg.GetParticle(1000220460) ):
    print "TO BE CHECKED the data insert for Ar40"
    pdg.AddParticle("Ar40","Ar40",39.9623831225,kFALSE,0,0,"Isotope",1000220460);   

if not(pdg.GetParticle(1000050110) ):
    print "TO BE CHECKED the data insert for B11"
    pdg.AddParticle("B11","B11",11.0093054,kFALSE,0,0,"Isotope",1000050110);   

KsID = 310
KLID = 130
NID = 2112

nActiveRPCstations = 2

def addVect(t,name,vectType):
    vect =  vector(vectType)()
    t.Branch( name, vect )
    return t, vect

def addVar(t,name,varType):
    var = array(varType,[-999])
    t.Branch(name,var,name+"/"+varType.upper())
    return t, var

def putToZero(var):
    #var.clear()
    #var.push_back(0)
    var[0] = 0
    
def getPartName(partId):
    return pdg.GetParticle(partId).GetName()

gridNumber = 691
folder = "69x"
print gridNumber
debug = True
if debug:
    #fileName = "../data/neutrino661/ship.10.0.Genie-TGeant4.root"
    fileName = "../data/69x/ship.10.0.Genie-TGeant4n691.root"
    outputFileName = "nuNutple_debug691.root"
else:
    #fileName = "../data/neutrino661/ship.10.0.Genie-TGeant4.root"#"../data/all/ship.10.0.Genie-TGeant4-370k.root"
    fileName = "../data/%s/ship.10.0.Genie-TGeant4n%s.root"%(folder,gridNumber)#"../data/all/ship.10.0.Genie-TGeant4-370k.root"
    outputFileName = "nuNutpleStudy%s.root"%gridNumber

fileNameGeo = "../data/%s/ship.10.0.Genie-TGeant4.root"%folder#"../data/neutrino681/ship.10.0.Genie-TGeant4.root"
    
f = TFile(fileName)
t = f.Get("cbmsim")

entries = t.GetEntries()
#t2.Draw("startZ_nu","startZ_nu>-2500.8 && startZ_nu<-2400.8")

from lookAtGeo import *
myNodes_name = ["volLayer_%s"%i for i in xrange(0,12)]
myNodes_name += ["lidT1lisci_1","lidT1I_1","lidT1O_1"]
myNodes_name += ["volScintLayer_%s"%i for i in xrange(0,12)]
myNodes_name += ["lidT6lisci_1","lidT6I_1","lidT6O_1"]
myNodes_name += ["volDriftLayer%s_1"%i for i in xrange(1,6)]

myGeoEl = findPositionGeoElement(fileNameGeo, myNodes_name)
lastPassiveEl = [myGeoEl["volLayer_0"]['z']-myGeoEl["volLayer_0"]['dimZ'],myGeoEl["volLayer_0"]['z']+myGeoEl["volLayer_0"]['dimZ']]

geo = loadGeometry(fileNameGeo)
ship_geo = geo['ShipGeo']

entranceWindows = [ [myGeoEl["lidT1O_1"]['z']-myGeoEl["lidT1O_1"]['dimZ'],myGeoEl["lidT1O_1"]['z']+myGeoEl["lidT1O_1"]['dimZ']],
                    [myGeoEl["lidT1I_1"]['z']-myGeoEl["lidT1I_1"]['dimZ'],myGeoEl["lidT1I_1"]['z']+myGeoEl["lidT1I_1"]['dimZ']]
                  ]                   
volume = [myGeoEl["lidT1O_1"]['z']-myGeoEl["lidT6O_1"]['dimZ'],myGeoEl["lidT6O_1"]['z']-myGeoEl["lidT6O_1"]['dimZ']]#[myGeoEl["lidT1lisci_1"]['z']+myGeoEl["lidT1lisci_1"]['dimZ'],4100]

scintTankW = [myGeoEl["lidT1lisci_1"]['z']-myGeoEl["lidT1lisci_1"]['dimZ'],myGeoEl["lidT1lisci_1"]['z']+myGeoEl["lidT1lisci_1"]['dimZ']]
scintTankV = [myGeoEl["lidT1lisci_1"]['z']-myGeoEl["lidT1lisci_1"]['dimZ'],myGeoEl["lidT1lisci_1"]['z']+myGeoEl["lidT1lisci_1"]['dimZ']]

OPERA = [myGeoEl["volLayer_11"]['z']-myGeoEl["volLayer_11"]['dimZ'],myGeoEl["volLayer_0"]['z']+myGeoEl["volLayer_0"]['dimZ']]
OPERA_wrong = [-2705.3,-2625.3]
print "Geometry Parameters:"
print "last passive (interactionElement == 0): ",lastPassiveEl
print "entrance windows (interactionElement == 1): ", entranceWindows
print "volume (interactionElement ==2): ", volume
print "scintTankW: ", scintTankW
print "scintTankV: ", scintTankV
print "OPERA-system: ",OPERA
print "OPERA_wrong: ", OPERA_wrong


#lastPassive = [myGeoEl["volLayer2_11"]['z'],myGeoEl["volLayer2_0"]['z']]

print "I should think of a correct way to distinguish volume from entrance window around the z of the two windows"
#assert(False)

## I don't want to consider the RPC after the last passive element (removed in some later version of the geo) so index just up to 11
RPCstationsPos = [[myGeoEl["volScintLayer_%s"%i]['z']-myGeoEl["volScintLayer_%s"%i]['dimZ'],myGeoEl["volScintLayer_%s"%i]['z']+myGeoEl["volScintLayer_%s"%i]['dimZ']] for i in xrange(0,11)]
HPTstationsPos = [[myGeoEl["volDriftLayer%s_1"%i]['z']-myGeoEl["volDriftLayer%s_1"%i]['dimZ'],myGeoEl["volDriftLayer%s_1"%i]['z']+myGeoEl["volDriftLayer%s_1"%i]['dimZ']] for i in xrange(1,6)]

RPCstationsPos += HPTstationsPos

### Ntuple elements:
nf = TFile(outputFileName,"RECREATE")

nt = TTree("t","t")
nt, event = addVar(nt, 'event','i')
nt, nNu = addVar(nt, 'nNu', 'i')
nt, isPrimary = addVar(nt, 'isPrimary','i')
nt, startZ_nu = addVar(nt, 'startZ_nu', 'f')
nt, startY_nu = addVar(nt, 'startY_nu', 'f')
nt, startX_nu = addVar(nt, 'startX_nu', 'f')
nt, nuE = addVar(nt, 'nuE', 'f')

## 0: last passive material opera-mu-system
## 1: two windows around liquid scintillator
## 2: along vaccum tank
## 3: along all OPERA
## 4: between the two entrance windows
## 999: wrong OPERA place ## needed until we have the new production
## -1: anything else, but what???? #it should never been present

nt, interactionElement = addVar(nt, 'interactionElement','i')
### From Neutrino
nt, nPart_fromNu = addVar(nt, 'nPart_fromNu', 'i')
nt, idPart_fromNu = addVect(nt, 'idPart_fromNu', 'int')
nt, idStrPart_fromNu = addVect(nt, 'idStrPart_fromNu', 'string')

nt, nChargedPart_fromNu = addVar(nt, 'nChargedPart_fromNu', 'i')
nt, idChargedPart_fromNu =  addVect(nt, 'idChargedPart_fromNu', 'int')
nt, idStrChargedPart_fromNu =  addVect(nt, 'idStrChargedPart_fromNu', 'string')

nt, nNeutrPart_fromNu = addVar(nt, 'nNeutrPart_fromNu', 'i')
nt, idNeutrPart_fromNu = addVect(nt, 'idNeutrPart_fromNu', 'int')
nt, idStrNeutrPart_fromNu = addVect(nt, 'idStrNeutrPart_fromNu', 'string')

### With Ks
nt, nNeutrPart_withKs = addVar(nt,'nNeutrPart_withKs', 'i')
nt, idNeutrPart_withKs = addVect(nt, 'idNeutrPart_withKs', 'int')
nt, idStrNeutrPart_withKs = addVect(nt, 'idStrNeutrPart_withKs', 'string')

nt, nChargedPart_withKs = addVar(nt, 'nChargedPart_withKs', 'i')
nt, idChargedPart_withKs = addVect(nt, 'idChargedPart_withKs', 'int')
nt, idStrChargedPart_withKs = addVect(nt, 'idStrChargedPart_withKs', 'string')

nt, nPart_withKs = addVar(nt, 'nPart_withKs', 'i')
nt, idPart_withKs = addVect(nt, 'idPart_withKs', 'int')
nt, idStrPart_withKs = addVect(nt, 'idStrPart_withKs', 'string')

### With KL
nt, nNeutrPart_withKL = addVar(nt, 'nNeutrPart_withKL', 'i')
nt, idNeutrPart_withKL = addVect(nt,'idNeutrPart_withKL', 'int')
nt, idStrNeutrPart_withKL = addVect(nt,'idStrNeutrPart_withKL', 'string')

nt, nChargedPart_withKL = addVar(nt,'nChargedPart_withKL', 'i')
nt, idChargedPart_withKL = addVect(nt,'idChargedPart_withKL', 'int')
nt, idStrChargedPart_withKL = addVect(nt,'idStrChargedPart_withKL', 'string')

nt, nPart_withKL = addVar(nt, 'nPart_withKL', 'i')
nt, idPart_withKL = addVect(nt, 'idPart_withKL', 'int')
nt, idStrPart_withKL = addVect(nt, 'idStrPart_withKL', 'string')

### With N
nt, nNeutrPart_withN = addVar(nt,'nNeutrPart_withN', 'i')
nt, idNeutrPart_withN = addVect(nt,'idNeutrPart_withN', 'int')
nt, idStrNeutrPart_withN = addVect(nt,'idStrNeutrPart_withN', 'string')

nt, nChargedPart_withN = addVar(nt, 'nChargedPart_withN', 'i')
nt, idChargedPart_withN = addVect(nt,'idChargedPart_withN', 'int')
nt, idStrChargedPart_withN = addVect(nt,'idStrChargedPart_withN', 'string')

nt, nPart_withN = addVar(nt, 'nPart_withN', 'i')
nt, idPart_withN = addVect(nt, 'idPart_withN', 'int')
nt, idStrPart_withN = addVect(nt, 'idStrPart_withN', 'string')

#is there a Ks?
nt, hasKs = addVar(nt, 'hasKs', 'i')
nt, hasKL = addVar(nt, 'hasKL', 'i' )

nt, hasN = addVar(nt, 'hasN', 'i')

# was the liquid scintillator window fired? 
nt, scintW = addVar(nt,'scintW', 'i' )
# accounting for an eff. of each station of 90%
nt, scintW_eff = addVar(nt,'scintW_eff', 'i' )

# was the liquid scintillator wall (around the volume) fired? 
nt, scintV = addVar(nt,'scintV', 'i' )
# accounting for an eff. of each station of 90%
nt, scintV_eff = addVar(nt,'scintV_eff', 'i' )


# was at least an RPC fired? 
nt, RPC = addVar(nt,'RPC', 'i' )
# accounting for an eff. of each station of 90%
nt, RPC_eff = addVar(nt,'RPC_eff', 'i' )

nt, nRPCstations = addVar(nt, 'nRPCstations', 'i')
nt, nRPCstations_eff = addVar(nt, 'nRPCstations_eff', 'i')

# did the neutrino interact in the last passive element of the "opera-mu-system"?
nt, lastPassive = addVar(nt, 'lastPassive', 'i' )

nt, nuKid_z = addVect(nt, "nuKid_z", "float")

for entry in xrange(entries):
    #entry = 5429
    if not (entry%1000):
        print "%s / %s"%(entry,entries)
        
        #if debug:
        #if (entry%1000):
        #    continue
        #res = {}
    t.GetEntry(entry)

    event[0] = entry
    particles = t.MCTrack
    rpc = t.ShipRpcPoint
    scint = t.vetoPoint
    
    ## initialization
    putToZero(nNu)
    putToZero(nPart_fromNu)
    putToZero(nChargedPart_fromNu)
    putToZero(nNeutrPart_fromNu)
    
    putToZero(nNeutrPart_withKs)
    putToZero(nChargedPart_withKs)
    putToZero(nPart_withKs)
    
    putToZero(nNeutrPart_withKL)
    putToZero(nChargedPart_withKL)
    putToZero(nPart_withKL)
    
    putToZero(nNeutrPart_withN)
    putToZero(nChargedPart_withN)
    putToZero(nPart_withN)
    putToZero(hasKs)
    putToZero(hasKL)
    putToZero(hasN)
    
    idPart_fromNu.clear()
    idChargedPart_fromNu.clear()
    idNeutrPart_fromNu.clear()
    idStrPart_fromNu.clear()
    idStrChargedPart_fromNu.clear()
    idStrNeutrPart_fromNu.clear()
    
    idNeutrPart_withKs.clear()
    idChargedPart_withKs.clear()
    idPart_withKs.clear()
    idStrNeutrPart_withKs.clear()
    idStrChargedPart_withKs.clear()
    idStrPart_withKs.clear()
    
    idNeutrPart_withKL.clear()
    idChargedPart_withKL.clear()
    idPart_withKL.clear()
    idStrNeutrPart_withKL.clear()
    idStrChargedPart_withKL.clear()
    idStrPart_withKL.clear()
    
    idNeutrPart_withN.clear()
    idChargedPart_withN.clear()
    idPart_withN.clear()
    idStrNeutrPart_withN.clear()
    idStrChargedPart_withN.clear()
    idStrPart_withN.clear()

    nuKid_z.clear()

    primaryDone=False
    for (ip,part) in enumerate(particles):
        
        ## exit if we have reached the empty part of the array
        if not (type(part)==type(ShipMCTrack())):
            break
        if not pdg.GetParticle(part.GetPdgCode()):
            #%print "--> to be added before continuing:", part.GetPdgCode()
            #sys.exit(0)
            pdg.AddParticle("%s"%part.GetPdgCode(),"%s"%part.GetPdgCode(),0.1,kFALSE,0,0,"Isotope",part.GetPdgCode());    
            print "ERROR: you should insert proper values for: %s"%part.GetPdgCode()
        pdgPart = pdg.GetParticle(part.GetPdgCode())
        pdgPart.GetName()
        
        ## Looking for a neutrino: it should have the correct pdg code and it should not have a mother
        if (("nu" in pdgPart.GetName())):# and part.GetMotherId()==-1):
            ## Starting the counter of how many particles were produced by the interaction of this specific nu
            #fromThisNu.push_back(0)
            nNu[0]+=1
            if part.GetMotherId()==-1:
                assert(primaryDone==False)
                primaryDone=True
                isPrimary[0] = int(True) 
                assert(len(idStrPart_fromNu)==0)
                assert(len(idStrNeutrPart_fromNu)==0)
            else: 
                isPrimary[0] = int(False) 
                continue

            startZ_nu[0] = part.GetStartZ()
            startY_nu[0] = part.GetStartY()
            startX_nu[0] = part.GetStartX()
                
            nuE[0] = part.GetEnergy()
            # Re-initialization for each interacting neutrino
            ## ---> <--- ##
            
            ## Looking for particles produced by the neutrino interaction
            interacted = False
            partKidsId = []
            for ip2 in xrange(0,len(particles)):
                part2 = particles[ip2]
                ## exit if we have reached the empty part of the array
                if not (type(part2)==type(ShipMCTrack())):
                    break
                if part2.GetMotherId()==ip:
                    interacted = True 
                    part2Id = part2.GetPdgCode()
                    partKidsId.append(part2Id)

                    #print "pID",part2Id, pdg.GetParticle(part2Id).GetName()
                    
                    nPart_fromNu[0]+=1
                    idPart_fromNu.push_back(part2Id)
                    idStrPart_fromNu.push_back(getPartName(part2Id))
                    
                    ## Counting how many particles produced by the nu-interaction are charged or neutral
                    if int(fabs(pdg.GetParticle(part2Id).Charge()))==int(0):
                        nNeutrPart_fromNu[0]+=1
                        idNeutrPart_fromNu.push_back(part2Id)
                        idStrNeutrPart_fromNu.push_back(getPartName(part2Id))
                    else:
                        nChargedPart_fromNu[0]+=1
                        idChargedPart_fromNu.push_back(part2Id)
                        idStrChargedPart_fromNu.push_back(getPartName(part2Id))

                    ## How many are produced by the interaction in the last passive element of the "opera-mu system"?
                    part2Z = part2.GetStartZ()
                    nuKid_z.push_back(part2Z)
                    somewhere = False
                    if part2Z>lastPassiveEl[0] and part2Z<lastPassiveEl[1]:
                        somewhere = True
                        interactionElement[0] = 0 
                        #RpcPassiveFlag = True
                        lastPassive[0] = int(True)
                        
                    ## To know if it was in the full OPERA-system (excluded last passive)
                    if part2Z>OPERA[0] and part2Z<OPERA[1] and somewhere==False:
                        somewhere = True
                        interactionElement[0] = 3
                        ## To account for things that are both in the correct and wrong OPERA place
                        #if part2Z>OPERA_wrong[0] and part2Z<OPERA_wrong[1]:
                        #   interactionElement.push_back(999)
                    ## To account for things that are only in the wrong OPERA place       
                    if part2Z>OPERA_wrong[0] and part2Z<OPERA_wrong[1] and somewhere==False:
                        somewhere = True
                        interactionElement[0] = 999 




                    ## To know if it was between the two windows
                    if part2Z>entranceWindows[0][1] and part2Z<entranceWindows[1][0]:
                        somewhere = True
                        interactionElement[0] = 4

                    scintElement = False        
                    for ew in entranceWindows:
                        if part2Z>ew[0] and part2Z<ew[1]:
                            somewhere = True
                            interactionElement[0] = 1
                            scintElement = True
                            
                    scintFlag = False
                    if scintElement:
                        for scintEl in scint:
                            if scintTankW[0]<scintEl.GetZ()<scintTankW[1]:
                                scintFlag=True
                    if scintFlag:
                        scintW[0] = int(True)
                        eff_flag = gRandom.Uniform(0.,1.)
                        if eff_flag<0.9:
                            scintW_eff[0] = int(True)
                        else:
                            scintW_eff[0] = int(False)
                    else:
                        scintW[0] = int(False)

                    
                        
                    scintElement = False
                    if part2Z>volume[0] and part2Z<volume[1]: ## extra check needed for the windows, and for be sure that x and y are as expected
                        interactionElement[0] = 2
                        scintElement = True
                        somewhere = True
                        
                    if scintElement:
                        for scintEl in scint:
                            if scintTankV[0]<scintEl.GetZ()<scintTankV[1]:
                                scintFlag=True
                                
                    if scintFlag:
                        scintV[0] = int(True)
                        eff_flag = gRandom.Uniform(0.,1.)
                        if eff_flag<0.9:
                            scintV_eff[0] = int(True)
                        else:
                            scintV_eff[0] = int(False)
                    else:
                        scintV[0] = int(False)

                    if somewhere==False:
                        interactionElement[0] = -1
                    ## Knowing how many particles comes with the KL
                    if fabs(part2Id) == KLID:
                        hasKL[0] = int(True)
                        for (ip3,part3) in enumerate(particles):
                            if not (type(part)==type(ShipMCTrack())):
                                break
                            ## same mother has the KL and is not the KL itself
                            if part3.GetMotherId()==ip and part3 is not part2: 
                                nPart_withKL[0] += 1
                                part3Id = part3.GetPdgCode()
                                idPart_withKL.push_back(part3Id)
                                idStrPart_withKL.push_back(getPartName(part3Id))
                                
                                if (int(pdg.GetParticle(part3Id).Charge())==int(0)):
                                    nNeutrPart_withKL[0]+=1
                                    idNeutrPart_withKL.push_back(part3Id)
                                    idStrNeutrPart_withKL.push_back(getPartName(part3Id))
                                else:
                                    nChargedPart_withKL[0]+=1
                                    idChargedPart_withKL.push_back(part3Id)    
                                    idStrChargedPart_withKL.push_back(getPartName(part3Id))

                    ## Knowing how many particles comes with the Ks
                    elif fabs(part2Id) == KsID:
                        hasKs[0] = int(True)
                        for (ip3,part3) in enumerate(particles):
                            if not (type(part)==type(ShipMCTrack())):
                                break
                            ## same mother has the Ks and is not the Ks itself
                            if part3.GetMotherId()==ip and part3 is not part2: 
                                nPart_withKs[0] += 1
                                part3Id = part3.GetPdgCode()
                                idPart_withKs.push_back(part3Id)
                                idStrPart_withKs.push_back(getPartName(part3Id))
                                
                                if (int(pdg.GetParticle(part3Id).Charge())==int(0)):
                                    nNeutrPart_withKs[0]+=1
                                    idNeutrPart_withKs.push_back(part3Id)
                                    idStrNeutrPart_withKs.push_back(getPartName(part3Id))
                                else:
                                    nChargedPart_withKs[0]+=1
                                    idChargedPart_withKs.push_back(part3Id)    
                                    idStrChargedPart_withKs.push_back(getPartName(part3Id))  
                
                    ## Knowing how many particles comes with the N
                    elif fabs(part2Id) == NID:
                        hasN[0] = int(True)
                        for (ip3,part3) in enumerate(particles):
                            if not (type(part)==type(ShipMCTrack())):
                                break
                            ## same mother has the N and is not the N itself
                            if part3.GetMotherId()==ip and part3 is not part2: 
                                nPart_withN[0] += 1
                                part3Id = part3.GetPdgCode()
                                idPart_withN.push_back(part3Id)
                                idStrPart_withN.push_back(getPartName(part3Id))
                                
                                if (int(pdg.GetParticle(part3Id).Charge())==int(0)):
                                    nNeutrPart_withN[0]+=1
                                    idNeutrPart_withN.push_back(part3Id)
                                    idStrNeutrPart_withN.push_back(getPartName(part3Id))
                                else:
                                    nChargedPart_withN[0]+=1
                                    idChargedPart_withN.push_back(part3Id)    
                                    idStrChargedPart_withN.push_back(getPartName(part3Id))   
            ####
            assert(interacted)                        
            ## In case it was in the OPERA system (wrong && correct place) 
            if somewhere and interactionElement[-1] in [0,3,999]:

                #print "ID particles from interaction:", partKidsId

                # I should find the first hit connected to the particles from the interaction
                partKidTrackID = []
                for p_ID in partKidsId:
                    for RPChit in rpc:
                        if p_ID==RPChit.PdgCode() and not (RPChit.GetTrackID() in partKidTrackID):
                            # I take the trackID to follow it
                            partKidTrackID.append(RPChit.GetTrackID())
                            ### to be conservative I take only the first trackID of the first set of hits corrisponding to the particleID (nu_daughter)
                            break
                # Now in partKidTrackID I should have the trackID connected to my charged particles
                RPCflag_eff = False
                rpcFlag = False
                nRPCstat = 0
                nRPCstat_eff = 0
                for t_ID in partKidTrackID:
                    for RPChit in rpc:
                        if RPChit.GetTrackID()==t_ID:
                            #print RPChit.GetTrackID(), t_ID
                            # check if it is in one of the considered active layer
                            for RPCpos in RPCstationsPos:
                                if RPCpos[0]<=RPChit.GetZ()<=RPCpos[1]:
                                    #print RPCpos, RPChit.GetZ()
                                    rpcFlag = True
                                    nRPCstat+=1
                                    eff_flag = gRandom.Uniform(0.,1.)
                                    if eff_flag<0.9:
                                        RPCflag_eff = RPCflag_eff or True
                                        nRPCstat_eff+=1
                                    else:
                                        RPCflag_eff = RPCflag_eff or False
 
                RPC[0] = int(rpcFlag)                    
                RPC_eff[0] = int(RPCflag_eff)

                nRPCstations[0] = int(nRPCstat)
                nRPCstations_eff[0] = int(nRPCstat_eff)

    #if entry==744:
    #    PrintEventPart(particles,pdg)
        #assert(False)

    assert(len(idStrPart_fromNu)==len(idPart_fromNu))
    assert(len(idStrChargedPart_fromNu)==len(idChargedPart_fromNu))
    assert(len(idStrNeutrPart_fromNu)==len(idNeutrPart_fromNu))
    assert(len(idStrPart_fromNu)==nChargedPart_fromNu[0]+nNeutrPart_fromNu[0])
    assert(len(idStrChargedPart_fromNu)==nChargedPart_fromNu[0])
    assert(len(idStrNeutrPart_fromNu)==nNeutrPart_fromNu[0])
    nt.Fill()
        

        
nt.Write()
nf.Save()
nf.Close()
print "Wrote file %s"%outputFileName
'''f2 = TFile("prova.root")
t2 = f2.Get("t")
t2.Print()

t2.Draw("nuE", "nNu==1 && isPrimary==1")
#t2.Draw("startZ_nu", "nNu==1 && isPrimary==1 && startZ_nu>=-2501.8 && startZ_nu<=-2478.8")
'''


'''### Looking for the first RPC station that can be fired (i.e. after the interaction point)   
                leftRPC = None#tmp_firstRPCStation = None
                rightRPC = None
                for (indexRPC,RPCs) in enumerate(RPCstationsPos):
                    if part2Z<RPCs[1]:
                        #tmp_firstRPCStation = indexRPC
                        leftRPC = indexRPC-1
                        rightRPC = indexRPC
                        break
                    #if tmp_firstRPCStation is None:
                if leftRPC is None:
                    print "ERROR: need to debug event %s"%entry
                    print "part2z = ",part2Z
                    print "RPCstationPos = ",RPCstationsPos
                    sys.exit(0)
                    #if tmp_firstRPCStation is not 0:
                    # print "Did you change and you are not looking anymore at the last passive element? If not it should be a bug in the code, if yes remove this part (used only as a safety check)"
                    #sys.exit(0)
                print "###", leftRPC, rightRPC, RPCstationsPos[leftRPC], RPCstationsPos[rightRPC], part2Z
                # I used a list in case we would like to include more than the two RPC layers around the passive element where we had the interaction
                potentiallyFiredRPCindex = [leftRPC,rightRPC]

                ## checking if I have one of the two active stations around the interaction point with hits
                RPCflag = False
                RPCflag_eff = False
                for RPCpt in rpc:
                    print RPCpt.GetZ(), pdg.GetParticle(RPCpt.PdgCode()).GetName(), RPCpt.GetTrackID()
                assert(False)
                for RPCpt in rpc:
                    for potRPCindex in potentiallyFiredRPCindex:
                        print RPCpt.GetZ(), RPCstationsPos[potRPCindex]
                        if RPCpt.GetZ()<RPCstationsPos[potRPCindex][1] and RPCpt.GetZ()>RPCstationsPos[potRPCindex][0]:
                            RPCflag = True
                            
                            ## For each station after the interaction point I simulate a 90% efficiency of the detector
                            ## only if one station is still fired I put a positive flag
                            eff_flag = gRandom.Uniform(0.,1.)
                            if eff_flag<0.9:
                                RPCflag_eff = True
                        print RPCflag, RPCflag_eff

                for (pid,part) in enumerate(particles):
                    print pid, pdg.GetParticle(part.GetName(), part.GetMotherId()
                assert(False)
'''     
