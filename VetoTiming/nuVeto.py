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

def paletteStyle2dHisto(c,h):
    c.SetHighLightColor(2);
    c.Range(-0.376699,-0.8106667,2.326214,4.245333);
    c.SetFillColor(0);
    c.SetBorderMode(0);
    c.SetBorderSize(2);
    c.SetTickx(1);
    c.SetTicky(1);
    c.SetLeftMargin(0.1393678);
    c.SetRightMargin(0.1206897);
    c.SetTopMargin(0.04852321);
    c.SetBottomMargin(0.1603376);
    c.SetFrameLineWidth(2);
    c.SetFrameBorderMode(0);
    c.SetFrameLineWidth(2);
    c.SetFrameBorderMode(0);
    
    palette = TPaletteAxis(2.015534,0.005333338,2.139806,4.005333,h);
    '''palette.SetLabelColor(1);
    palette.SetLabelFont(42);
    palette.SetLabelOffset(0.005);
    palette.SetLabelSize(0.05);
    palette.SetTitleOffset(0.5);
    palette.SetTitleSize(0.06);
    palette.SetFillColor(100);
    palette.SetFillStyle(1001);
    palette.SetLineWidth(2);
    h.GetListOfFunctions().Add(palette,"br");
    h.SetLineWidth(2);
    h.SetMarkerStyle(8);
    h.SetMarkerSize(1.5);
    
    '''
    h.GetZaxis().SetTitle("Occurancy");
    h.GetZaxis().SetNdivisions(3);
    h.GetZaxis().SetLabelFont(42);
    h.GetZaxis().SetLabelSize(0.05);
    h.GetZaxis().SetTitleSize(0.06);
    h.GetZaxis().SetTitleFont(42);
    return {'h':h,'c':c,'palette':palette}

def id_fromNu(histoDict,tot_nu,primary_nu):
    ### This function will make the plot with the ID of all the particles produced from the nu interactions
    hkeys = histoDict.keys()
    c_id_fromNu = TCanvas("c_id_fromNu","Id particles from nu interaction")
    h_id_fromNu = TH1F("h_id_fromNu","h_id_fromNu",len(hkeys),0,len(hkeys))
    labels = True
	
    if labels is not None:
        h_id_fromNu.LabelsOption("U") 
    for (i,pId) in enumerate(hkeys):
        h_id_fromNu.SetBinContent(i+1,histoDict[pId]['nFound'])
        if labels is not None:
            h_id_fromNu.GetXaxis().SetBinLabel(i+1, pdg.GetParticle(int(pId)).GetName())
    pave = TPaveText(0.43, 0.76, 0.72, 0.88,"TNDC")
    pave.AddText("Number of nu that had interacted: %s "%(tot_nu))
    pave.AddText("Number of nu from target %s"%(primary_nu))
    pave.SetTextAlign(11)
    pave.SetLineColor(kWhite)
    h_id_fromNu.Draw()
    pave.Draw("same")
    c_id_fromNu.Print(c_id_fromNu.GetName()+".pdf")
    return {'c':c_id_fromNu,'h':h_id_fromNu, 'pave':pave}
	###############

def nFromThisNu(fromThisNu):
    c = TCanvas("c_nFromThisNu","c_nFromThisNu")
    h_nFromThisNu = TH1F("h_nFromThisNu", "number of particles produced from the same neutrino interaction",len(fromThisNu),0,len(fromThisNu))
    for (i,el) in enumerate(fromThisNu):
        h_nFromThisNu.SetBinContent(i,el)
    h_nFromThisNu.GetXaxis().SetTitle("nu index")
    h_nFromThisNu.GetYaxis().SetTitle("n particles from nu interaction")
    h_nFromThisNu.Draw()
    return {'c':c, 'h':h_nFromThisNu}

def withSomebody(somebody,withKs):
    somebody = "KL"
    c = TCanvas("c_nWith%s"%somebody,"c_nWith%s"%somebody)
    h_withKs = TH1F("h_nWith%s"%somebody, "number of particles produced together with a %s"%somebody,len(withKs),0,len(withKs))
    for (i,el) in enumerate(withKs):
        h_withKs.SetBinContent(i+1,int(el))
    h_withKs.GetXaxis().SetTitle("%s index"%somebody)
    h_withKs.GetYaxis().SetTitle("n particles produced with %s"%somebody)
    h_withKs.Draw("p")
    return {'c':c, 'h':h_withKs}

def id_withSomebody(somebody,id_withKs,name="id_with", title="id particles produced together with a"):
    name += "_%s"%somebody
    title += " %s"%somebody
    title.replace("_"," ")
    
    dim_y = 0
    print "id_withKs",id_withKs
    for el in id_withKs:
        if len(el.keys())>dim_y:
            dim_y = len(el.keys())
    print "dimY",dim_y
    c = TCanvas("c_%s"%name,"%s"%title)
    h = TH2F("h_%s"%name,"h_%s"%name,len(id_withKs),0,len(id_withKs),dim_y,0,dim_y)
    ref = 0
    for x in id_withKs:
        for pId in x.keys():
            if x[pId]>ref:
                ref=x[pId]
            #colors = array('i', [5,7,3,6,2,4,1,1])

    h.GetYaxis().SetTitleSize(0.04)
    h.GetYaxis().SetTitleOffset(1.50)
            
    h.GetZaxis().SetRangeUser(0,ref+0.1)
    h.GetZaxis().SetNdivisions(ref+1)
    h.SetContour(ref)
    
    if ref>10:
        print "ERROR: you should increase the number of colors in the palette"
        assert(False)
    labels = True
    if labels is not None:
        h.LabelsOption("U")
    for (ix, index) in enumerate(id_withKs):
        for (iy, pId) in enumerate(index.keys()):
            h.SetBinContent(ix+1,iy+1,index[pId])
            if labels is not None:
                h.GetYaxis().SetBinLabel(iy+1, pdg.GetParticle(int(pId)).GetName())
        if labels is not None:
            h.GetXaxis().SetBinLabel(ix+1, "%s"%ix)
    
    h.GetXaxis().SetTitle("%s index"%somebody)
    h.GetYaxis().SetTitle("%s"%(title))
    h.GetZaxis().SetTitle("Occurancy")
    #h.Draw("colz")
    res = paletteStyle2dHisto(c,h)
    c = res['c']
    h = res['h']
    #lhcbStyle.SetPalette(1);
    h.Draw("COLZ");
    gPad.Update();
    #palette = h.GetListOfFunctions().FindObject("palette");
    #h.GetListOfFunctions().Print()
    #assert(False)
    #palette.SetX2NDC(0.9);
    
    c.Print(c_id_fromNu.GetName()+".pdf")
    return {'c':c,'h':h, 'palette':res['palette']}




debug = True
if debug:
    fileName = "../data/neutrino661/ship.10.0.Genie-TGeant4_D.root"
else:
    fileName = "../data/all/ship.10.0.Genie-TGeant4-370k.root"

f = TFile(fileName)
t = f.Get("cbmsim")

entries = t.GetEntries()
#entries = 1

from lookAtGeo import *
myNodes_name = ["volLayer_%s"%i for i in xrange(0,12)]
myGeoEl = findPositionGeoElement(fileName, myNodes_name)
lastPassive = [myGeoEl["volLayer_0"]['z']-myGeoEl["volLayer_0"]['dimZ'],myGeoEl["volLayer_0"]['z']+myGeoEl["volLayer_0"]['dimZ']]
#lastPassive = [myGeoEl["volLayer2_11"]['z'],myGeoEl["volLayer2_0"]['z']]

#h_id_fromNu = TH1F("h_id_fromNu","h_id_fromNu",)
histoDict = {}
primary_nu = 0
tot_nu = 0
fromThisNu = []
withKs = []
id_withKs = []
withKL = []
id_withKL = []

originKL_notFromNu = []
originKs_notFromNu = []
id_withKL_notFromNu = []
id_withKs_notFromNu = []
nKL_notFromNu = 0
nKs_notFromNu = 0

n_chargedWithKL = []
n_chargedWithKs = []
n_chargedFromNu = []
n_particlesFromNu = []

histoDict_chargedWithKL = {}
histoDict_chargedWithKs = {}
histoDict_chargedFromNu = {}

nu_z = []
nuKid_z = []
rpcFlag_list = []
for entry in xrange(entries):
    #entry = 5429
    #if not (entry%1000):
    #if (entry%1000):
    #    continue
    #print "%s / %s"%(entry,entries)
        #res = {}
    t.GetEntry(entry)
    particles = t.MCTrack
    rpc = t.ShipRpcPoint
    
    for (ip,part) in enumerate(particles):
        ## exit if we have reached the empty part of the array
        if not (type(part)==type(ShipMCTrack())):
            break
        #print part.GetPdgCode()
        pdgPart = pdg.GetParticle(part.GetPdgCode())
            
        ## Looking for a neutrino: it should have the correct pdg code and it should not have a mother
        if (("nu" in pdgPart.GetName())):# and part.GetMotherId()==-1):
            ## Starting the counter of how many particles were produced by the interaction of this specific nu
            fromThisNu.append(0)
            if part.GetMotherId()==-1:
                primary_nu += 1
                nu_z.append(part.GetStartZ())
            
            tot_nu += 1
            #print "Neutrino %s"%ip
            chargedFromNu_counter = 0
            partFromNu_counter = 0

            ## To know if the rpc saw something
            rpcFlag = False
            ## To know if the neutrino interaction was in the element I want
            RpcPassiveFlag = False
            ## Looking for the particles produced by the interaction of the neutrino
            for ip2 in xrange(0,len(particles)):
                part2 = particles[ip2]
                ## exit if we have reached the empty part of the array
                if not (type(part2)==type(ShipMCTrack())):
                    break
                #print "  Looking for particles produced from neutrino interaction, %s"%ip2
                if part2.GetMotherId()==ip: 
                    part2Id = part2.GetPdgCode()

                    ## How many are produced by the interaction in the last passive element of the "opera-mu system"?
                    part2Z = part2.GetStartZ()
                    nuKid_z.append(part2Z)
                    if part2Z>lastPassive[0] and part2Z<lastPassive[1]:
                        print "Situation"
                        for (ii,pp) in enumerate(particles):
                            print ii,pdg.GetParticle(pp.GetPdgCode()).GetName(),pp.GetMotherId() 
                        print 
                        RpcPassiveFlag = True
                        print entry, "----> ", part2Z, part2Id
                        print pdg.GetParticle(part2Id).GetName(),pdg.GetParticle(part2Id).Charge()
                        print lastPassive[1]
                        print 
                        for rpcEl in rpc:
                            #print rpcEl.GetZ()
                            if rpcEl.GetZ()>lastPassive[1]:
                                rpcFlag=True
                                print "######",rpcEl.GetZ(), (rpcEl.GetZ()<=-2527 and rpcEl.GetZ()>=-2542) or (rpcEl.GetZ()<=-2597 and rpcEl.GetZ()>=-2612) 
                                
                    ## How many are charged particles? 
                    if not(fabs(pdg.GetParticle(part2Id).Charge())==fabs(0)):
                        chargedFromNu_counter +=1
                        if part2Id in histoDict_chargedFromNu:
                            histoDict_chargedFromNu[part2Id]['nFound']+=1
                        else: 
                            histoDict_chargedFromNu[part2Id]={}
                            histoDict_chargedFromNu[part2Id]['nFound']=1

                    partFromNu_counter += 1
                        
                    ## For each id knowing how many
                    if part2Id in histoDict:
                        histoDict[part2Id]['nFound']+=1
                    else: 
                        histoDict[part2Id]={}
                        histoDict[part2Id]['nFound']=1

                    ## Knowing how many particles comes with the KL
                    if fabs(part2Id) == KLID:
                        #assert(False)
                        withKL.append(0)
                        id_withKL.append({})
                        #print "--->",part2.GetPdgCode, part2.GetMotherId()
                        chargedWithKL_counter = 0
                        for (ip3,part3) in enumerate(particles):
                            if not (type(part)==type(ShipMCTrack())):
                                break
                            ## same mother has the KL and is not the KL itself
                            if part3.GetMotherId()==ip and part3 is not part2: 
                                #print part3.GetPdgCode(),part3.GetMotherId()
                                withKL[-1]+=1
                                part3Id = part3.GetPdgCode()
                                if part3Id in id_withKL[-1]:
                                    id_withKL[-1][part3Id] += 1
                                else:
                                    id_withKL[-1][part3Id] = 1
                                
                                if not(int(pdg.GetParticle(part3Id).Charge())==int(0)):
                                    chargedWithKL_counter+=1
                                    if part3Id in histoDict_chargedWithKL:
                                        histoDict_chargedWithKL[part3Id]['nFound']+=1
                                    else: 
                                        histoDict_chargedWithKL[part3Id]={}
                                        histoDict_chargedWithKL[part3Id]['nFound']=1

                        n_chargedWithKL.append(chargedWithKL_counter)
                        #assert(False)
                        
                    if fabs(part2Id) == KsID:
                        withKs.append(0)
                        id_withKs.append({})
                        #print "--->",part2.GetPdgCode, part2.GetMotherId()
                        chargedWithKs_counter = 0
                        for (ip3,part3) in enumerate(particles):
                            if not (type(part)==type(ShipMCTrack())):
                                break
                            ## same mother has the Ks and is not the Ks itself
                            if part3.GetMotherId()==ip and part3 is not part2: 
                                #print part3.GetPdgCode(),part3.GetMotherId()
                                withKs[-1]+=1
                                part3Id = part3.GetPdgCode()
                                if part3Id in id_withKs[-1]:
                                    id_withKs[-1][part3Id] += 1
                                else:
                                    id_withKs[-1][part3Id] = 1
                                
                                if not(int(pdg.GetParticle(part3Id).Charge())==int(0)):
                                    chargedWithKs_counter+=1
                                    if part3Id in histoDict_chargedWithKs:
                                        histoDict_chargedWithKs[part3Id]['nFound']+=1
                                    else: 
                                        histoDict_chargedWithKs[part3Id]={}
                                        histoDict_chargedWithKs[part3Id]['nFound']=1
                                

                        n_chargedWithKs.append(chargedWithKL_counter)
                    ## Knowing how many particles comes from the interaction of this neutrino
                    fromThisNu[-1]+=1
                        
                    #if fabs(part2Id)==130 or fabs(part2Id)==310:
                    #print "%%%%%%%%%%%%%%%%%%%%%% ->", part2Id
                        #assert(False)
                    pdgPart2 = pdg.GetParticle(part2Id)
                    #print "    Found: %s (pdgcode: %s)"%(pdgPart2.GetName(), part2.GetPdgCode())
            n_chargedFromNu.append(chargedFromNu_counter)
            n_particlesFromNu.append(partFromNu_counter)
            
            ## Filled the list only if the neutrino that had interacted did it in the piece I want to analyse
            if RpcPassiveFlag:
                rpcFlag_list.append(rpcFlag)
                assert(False)
        else:
            partId = part.GetPdgCode()
            # we already have considered the one from neutrinos
            if partId == KsID and not "nu" in pdg.GetParticle(particles[part.GetMotherId()].GetPdgCode()).GetName():
                id_withKs_notFromNu.append({})
                nKs_notFromNu += 1
                ## Not expected from the target
                assert(part.GetMotherId()>=0)
                motherIndex = part.GetMotherId()
                ## I use a dictionary just to re-use the function for plotting 
                originKs_notFromNu.append({particles[motherIndex].GetPdgCode():1})
                for (ip4,part4) in enumerate(particles):
                    if not (type(part)==type(ShipMCTrack())):
                        break
                    ## same mother has the Ks and is not the Ks itself
                    if part4.GetMotherId()==motherIndex and part4 is not part: 
                        #print part4.GetPdgCode(),part4.GetMotherId()
                        part4Id = part4.GetPdgCode()
                        if part4Id in id_withKs_notFromNu [-1]:
                            id_withKs_notFromNu[-1][part4Id] += 1
                        else:
                            id_withKs_notFromNu[-1][part4Id] = 1
            else:    
                if partId == KLID and not "nu" in pdg.GetParticle(particles[part.GetMotherId()].GetPdgCode()).GetName():
                    id_withKL_notFromNu.append({})
                    nKL_notFromNu += 1
                    ## Not expected from the target
                    assert(part.GetMotherId()>=0)
                    motherIndex = part.GetMotherId()
                    ## I use a dictionary just to re-use the function for plotting 
                    originKL_notFromNu.append({particles[motherIndex].GetPdgCode():1})
                    for (ip4,part4) in enumerate(particles):
                        if not (type(part)==type(ShipMCTrack())):
                            break
                        ## same mother has the Ks and is not the Ks itself
                        if part4.GetMotherId()==motherIndex and part4 is not part: 
                            #print part4.GetPdgCode(),part4.GetMotherId()
                            part4Id = part4.GetPdgCode()
                            if part4Id in id_withKL_notFromNu [-1]:
                                id_withKL_notFromNu[-1][part4Id] += 1
                            else:
                                id_withKL_notFromNu[-1][part4Id] = 1
        '''
        print
        '''

#print histoDict
#print tot_nu
#print primary_nu
    
def n_plotty(a,name,title,xtitle,ytitle,labels=True,):
    nbins = max(10,min(len(a),20))
    c = TCanvas("c_"+name,title)
    h = TH1F("h_"+name,title,nbins,0,nbins)
    h.GetXaxis().SetTitle(xtitle)
    h.GetYaxis().SetTitle(ytitle)
    
    if labels is not None:
        h.LabelsOption("U") 
        
    for el in a:
        h.Fill(el)
    for i in xrange(h.GetNbinsX()):
        if labels is not None:
            h.GetXaxis().SetBinLabel(i+1, str(i))
    h.Draw()
    return {'h':h,'c':c}


def id_plotty(histoDict,name,title,xtitle,ytitle,labels=True,):
    ### This function will make the plot with the ID of all the particles produced from the nu interactions
    hkeys = histoDict.keys()
    c = TCanvas("c_"+name,title)
    h = TH1F("h_"+name,title,len(hkeys),0,len(hkeys))
    
    if labels is not None:
        h.LabelsOption("U") 
    for (i,pId) in enumerate(hkeys):
        h.SetBinContent(i+1,histoDict[pId]['nFound'])
        if labels is not None:
            h.GetXaxis().SetBinLabel(i+1, pdg.GetParticle(int(pId)).GetName())
    
    h.Draw()
    
    c.Print(c.GetName()+".pdf")
    return {'c':c,'h':h}
	###############

'''
if len(withKs)>0:
    res_withKs = withSomebody("Ks",withKs)
    res_id_withKs = id_withSomebody("Ks",id_withKs)
if len(withKL)>0:
    res_withKL = withSomebody("KL",withKL)
    res_id_withKL = id_withSomebody("KL",id_withKL)

if len(id_withKs_notFromNu)>0:
    ####res_withKs_notFromNu = withSomebody("Ks_notFromNu",withKs_notFromNu)
    res_id_withKs_notFromNu = id_withSomebody("Ks_notFromNu",id_withKs_notFromNu)
    res_originKs_notFromNu = id_withSomebody("Ks_notFromNu",originKs_notFromNu,"origin_of_","origin of")
if len(id_withKL_notFromNu)>0:
    #res_withKL_notFromNu = withSomebody("KL_notFromNu",withKL_notFromNu)
    res_id_withKL_notFromNu = id_withSomebody("KL_notFromNu",id_withKL_notFromNu)
    res_originKL_notFromNu = id_withSomebody("KL_notFromNu",originKL_notFromNu,"origin_of","origin of")
'''

'''    
### This function will make the plot with the ID of all the particles produced from the nu interactions
res_id_fromNu = id_fromNu(histoDict,tot_nu,primary_nu)
res_nFromThisNu = nFromThisNu(fromThisNu)

res_chargedWithKL = n_plotty(n_chargedWithKL,"n_chargedWithKL","n_chargedWithKL","n of charged particles with KL","occurancy")
res_chargedFromNu = n_plotty(n_chargedFromNu,"n_chargedFromNu","n_chargedFromNu","n of charged particles from nu","occurancy")
res_partFromNu = n_plotty(n_particlesFromNu,"n_partFromNu","n_partFromNu","n of particles from nu","occurancy")


res_idChargedFromNu = id_plotty(histoDict_chargedFromNu,'id_chargedFromNu',"id charged particles from nu", 'id charged particles from nu', 'occurancy')
if len(histoDict_chargedWithKs.keys())>0:
    res_idChargedWithKs = id_plotty(histoDict_chargedWithKs,'id_chargedWithKs',"id charged particles produced with Ks", 'id charged particles with Ks', 'occurancy')
res_idChargedWithKL = id_plotty(histoDict_chargedWithKL,'id_chargedWithKL',"id charged particles WithKL", 'id charged particles WithKL', 'occurancy')

#print withKs
#print id_withKs
print id_withKL_notFromNu
print id_withKs_notFromNu
print nKL_notFromNu
print nKs_notFromNu
print originKL_notFromNu
print originKs_notFromNu
'''
c = TCanvas("c_nu_z","c_nu_z")
h_nu_z = TH1F("nu_z","nu_z",500,-3000,5000)
h_nu_z.GetXaxis().SetTitle("neutrino startZ")
for z in nu_z:
    h_nu_z.Fill(z)
h_nu_z.Draw()

cKid = TCanvas("c_nuKid_z","c_nuKid_z")
h_nuKid_z = TH1F("nuKid_z","nuKid_z",500,-3000,5000)
h_nuKid_z.GetXaxis().SetTitle("particle from neutrino interaction startZ")
for z in nuKid_z:
    h_nuKid_z.Fill(z)
h_nuKid_z.Draw()

print rpcFlag_list
