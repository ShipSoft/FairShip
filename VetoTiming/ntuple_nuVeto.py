from ROOT import *
from array import array

gROOT.ProcessLine(".x lhcbstyle.C")
pdg = TDatabasePDG.Instance()

### Add what is missed:
### PDG nuclear states are 10-digit numbers
### 10LZZZAAAI e.g. deuteron is 
### 1000010020
### from http://svn.cern.ch/guest/AliRoot/trunk/STEER/STEERBase/AliPDG.cxx and https://github.com/FairRootGroup/FairRoot/blob/master/eventdisplay/FairEventManager.cxx
### https://geant4.web.cern.ch/geant4/UserDocumentation/UsersGuides/ForApplicationDeveloper/html/AllResources/TrackingAndPhysics/particleList.src/ions/index.html

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
        
        
KsID = 310
KLID = 130
NID = 2112

def addVect(t,name,vectType):
    vect =  vector(vectType)()
    t.Branch( name, vect )
    return t, vect

def putToZero(var):
    var.clear()
    var.push_back(0)
    
def getPartName(partId):
    return pdg.GetParticle(partId).GetName()

debug = False
if debug:
    fileName = "../data/neutrino661/ship.10.0.Genie-TGeant4.root"
else:
    fileName = "../data/neutrino661/ship.10.0.Genie-TGeant4.root"#"../data/all/ship.10.0.Genie-TGeant4-370k.root"

f = TFile(fileName)
t = f.Get("cbmsim")

entries = t.GetEntries()

from lookAtGeo import *
myNodes_name = ["volLayer_%s"%i for i in xrange(0,12)]
myNodes_name += ["lidT1lisci_1"]
myGeoEl = findPositionGeoElement(fileName, myNodes_name)
lastPassiveEl = [myGeoEl["volLayer_0"]['z']-myGeoEl["volLayer_0"]['dimZ'],myGeoEl["volLayer_0"]['z']+myGeoEl["volLayer_0"]['dimZ']]
entranceWindow = [myGeoEl["lidT1lisci_1"]['z']-myGeoEl["lidT1lisci_1"]['dimZ'],myGeoEl["lidT1lisci_1"]['z']+myGeoEl["lidT1lisci_1"]['dimZ']]
volume = [myGeoEl["lidT1lisci_1"]['z']+myGeoEl["lidT1lisci_1"]['dimZ'],4100]
#lastPassive = [myGeoEl["volLayer2_11"]['z'],myGeoEl["volLayer2_0"]['z']]

### Ntuple elements:
nf = TFile("prova.root","RECREATE")

nt = TTree("t","t")
nt, event = addVect(nt, 'event','int')
nt, nNu = addVect(nt, 'nNu', 'int')
nt, isPrimary = addVect(nt, 'isPrimary','float')
nt, startZ_nu = addVect(nt, 'startZ_nu', 'float')
nt, interactionElement = addVect(nt, 'interactionElement','int')

### From Neutrino
nt, nPart_fromNu = addVect(nt, 'nPart_fromNu', 'int')
nt, idPart_fromNu = addVect(nt, 'idPart_fromNu', 'int')
nt, idStrPart_fromNu = addVect(nt, 'idStrPart_fromNu', 'string')

nt, nChargedPart_fromNu = addVect(nt, 'nChargedPart_fromNu', 'int')
nt, idChargedPart_fromNu =  addVect(nt, 'idChargedPart_fromNu', 'int')
nt, idStrChargedPart_fromNu =  addVect(nt, 'idStrChargedPart_fromNu', 'string')

nt, nNeutrPart_fromNu = addVect(nt, 'nNeutrPart_fromNu', 'int')
nt, idNeutrPart_fromNu = addVect(nt, 'idNeutrPart_fromNu', 'int')
nt, idStrNeutrPart_fromNu = addVect(nt, 'idStrNeutrPart_fromNu', 'string')

### With Ks
nt, nNeutrPart_withKs = addVect(nt,'nNeutrPart_withKs', 'int')
nt, idNeutrPart_withKs = addVect(nt, 'idNeutrPart_withKs', 'int')
nt, idStrNeutrPart_withKs = addVect(nt, 'idStrNeutrPart_withKs', 'string')

nt, nChargedPart_withKs = addVect(nt, 'nChargedPart_withKs', 'int')
nt, idChargedPart_withKs = addVect(nt, 'idChargedPart_withKs', 'int')
nt, idStrChargedPart_withKs = addVect(nt, 'idStrChargedPart_withKs', 'string')

nt, nPart_withKs = addVect(nt, 'nPart_withKs', 'int')
nt, idPart_withKs = addVect(nt, 'idPart_withKs', 'int')
nt, idStrPart_withKs = addVect(nt, 'idStrPart_withKs', 'string')

### With KL
nt, nNeutrPart_withKL = addVect(nt, 'nNeutrPart_withKL', 'int')
nt, idNeutrPart_withKL = addVect(nt,'idNeutrPart_withKL', 'int')
nt, idStrNeutrPart_withKL = addVect(nt,'idStrNeutrPart_withKL', 'string')

nt, nChargedPart_withKL = addVect(nt,'nChargedPart_withKL', 'int')
nt, idChargedPart_withKL = addVect(nt,'idChargedPart_withKL', 'int')
nt, idStrChargedPart_withKL = addVect(nt,'idStrChargedPart_withKL', 'string')

nt, nPart_withKL = addVect(nt, 'nPart_withKL', 'int')
nt, idPart_withKL = addVect(nt, 'idPart_withKL', 'int')
nt, idStrPart_withKL = addVect(nt, 'idStrPart_withKL', 'string')

### With N
nt, nNeutrPart_withN = addVect(nt,'nNeutrPart_withN', 'int')
nt, idNeutrPart_withN = addVect(nt,'idNeutrPart_withN', 'int')
nt, idStrNeutrPart_withN = addVect(nt,'idStrNeutrPart_withN', 'string')

nt, nChargedPart_withN = addVect(nt, 'nChargedPart_withN', 'int')
nt, idChargedPart_withN = addVect(nt,'idChargedPart_withN', 'int')
nt, idStrChargedPart_withN = addVect(nt,'idStrChargedPart_withN', 'string')

nt, nPart_withN = addVect(nt, 'nPart_withN', 'int')
nt, idPart_withN = addVect(nt, 'idPart_withN', 'int')
nt, idStrPart_withN = addVect(nt, 'idStrPart_withN', 'string')

#is there a Ks?
nt, hasKs = addVect(nt, 'hasKs', 'int')
nt, hasKL = addVect(nt, 'hasKL', 'int' )

nt, hasN = addVect(nt, 'hasN', 'int')

# was at leas an RPC fired? 
nt, RPC = addVect(nt,'RPC', 'int' )

# did the neutrino interact in the last passive element of the "opera-mu-system"?
nt, lastPassive = addVect(nt, 'lastPassive', 'int' )

nt, nuKid_z = addVect(nt, "nuKid_z", "float")

for entry in xrange(entries):
    #entry = 5429
    if not (entry%1000):
        print "%s / %s"%(entry,entries)
        
    if debug:
        if (entry%1000):
            continue
        #res = {}
    t.GetEntry(entry)

    ## initialization
    event.clear()
     
    event.push_back(entry)
    
    particles = t.MCTrack
    rpc = t.ShipRpcPoint

    ## initialization
    isPrimary.clear()
    startZ_nu.clear()
    hasKs.clear()
    hasKL.clear()
    hasN.clear()
    interactionElement.clear() 
    
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
    
    idPart_fromNu.clear()
    idChargedPart_fromNu.clear()
    idStrChargedPart_fromNu.clear()
    idNeutrPart_fromNu.clear()
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
    RPC.clear()
    lastPassive.clear()
    
    for (ip,part) in enumerate(particles):
       
        ## exit if we have reached the empty part of the array
        if not (type(part)==type(ShipMCTrack())):
            break
        #print part.GetPdgCode()
        pdgPart = pdg.GetParticle(part.GetPdgCode())

        ## Looking for a neutrino: it should have the correct pdg code and it should not have a mother
        if (("nu" in pdgPart.GetName())):# and part.GetMotherId()==-1):
            ## Starting the counter of how many particles were produced by the interaction of this specific nu
            #fromThisNu.push_back(0)
            nNu[0]+=1
            if part.GetMotherId()==-1:
                isPrimary.push_back(int(True))
                startZ_nu.push_back(part.GetStartZ())

            # Re-initialization for each interacting neutrino
            ## ---> <--- ##
            
            ## Looking for particles produced by the neutrino interaction
            for ip2 in xrange(0,len(particles)):
                part2 = particles[ip2]
                ## exit if we have reached the empty part of the array
                if not (type(part2)==type(ShipMCTrack())):
                    break
                if part2.GetMotherId()==ip: 
                    part2Id = part2.GetPdgCode()
                    nPart_fromNu[0]+=1
                    idPart_fromNu.push_back(part2Id)
                    idStrPart_fromNu.push_back(getPartName(part2Id))
                    
                    ## Counting how many particles produced by the nu-interaction are charged or neutral
                    if fabs(pdg.GetParticle(part2Id).Charge())==0:
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
                    if part2Z>lastPassiveEl[0] and part2Z<lastPassiveEl[1]:
                        interactionElement.push_back(0)
                        RpcPassiveFlag = True
                        lastPassive.push_back(int(True))
                        for rpcEl in rpc:
                            if rpcEl.GetZ()>lastPassiveEl[1]:
                                rpcFlag=True
                                
                        if not rpcFlag:
                           RPC.push_back(int(False))
                        else:
                           RPC.push_back(int(True)) 

                    if part2Z>entranceWindow[0] and part2Z<entranceWindow[1]:
                        interactionElement.push_back(1)

                    if part2Z>volume[0] and part2Z<volume[1]:
                        interactionElement.push_back(2)
                           
                    ## Knowing how many particles comes with the KL
                    if fabs(part2Id) == KLID:
                        hasKL.push_back(int(True))
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
                        hasKs.push_back(int(True))
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
                        hasN.push_back(int(True))
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

                                    
    
    nt.Fill()
        

        
nt.Write()
nf.Save()
nf.Close()

f2 = TFile("prova.root")
t2 = f2.Get("t")
t2.Print()
