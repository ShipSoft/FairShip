from ROOT import *
gROOT.ProcessLine(".x mystyle.C")

fileName = "nuNutple_debug691.root" #"nuNtupleStudy.root"
f2 = TFile(fileName)
t2 = f2.Get("t")
folder = "69x"
fileNameGeo = "../data/%s/ship.10.0.Genie-TGeant4.root"%folder
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

print "Geometry Parameters:"
print "last passive (interactionElement == 0): ",lastPassiveEl
print "entrance windows (interactionElement == 1): ", entranceWindows
print "volume (interactionElement ==2): ", volume
print "scintTankW: ", scintTankW
print "scintTankV: ", scintTankV

basicCut = "isPrimary==1 && nNu==1"
#t2.Draw("startZ_nu", "%s &&startZ_nu>-3000 && startZ_nu<-2704"%basicCut)

print fileNameGeo

print [myGeoEl["volLayer_11"]['z']-myGeoEl["volLayer_11"]['dimZ'],myGeoEl["volLayer_11"]['z']+myGeoEl["volLayer_11"]['dimZ']]
print [myGeoEl["volLayer_0"]['z']-myGeoEl["volLayer_0"]['dimZ'],myGeoEl["volLayer_0"]['z']+myGeoEl["volLayer_0"]['dimZ']]
#t2.Scan("startZ_nu", "nChargedPart_fromNu==0 && %s && startZ_nu>-2705.4 && startZ_nu<-2625.2"%basicCut)
print "PASSIVE:"
for idL in xrange(0,12):
    print idL, [myGeoEl["volLayer_%s"%idL]['z']-myGeoEl["volLayer_%s"%idL]['dimZ'],myGeoEl["volLayer_%s"%idL]['z']+myGeoEl["volLayer_%s"%idL]['dimZ']]

print
print "ACTIVE:"
for idL in xrange(0,12):
    print idL, [myGeoEl["volScintLayer_%s"%idL]['z']-myGeoEl["volScintLayer_%s"%idL]['dimZ'],myGeoEl["volScintLayer_%s"%idL]['z']+myGeoEl["volScintLayer_%s"%idL]['dimZ']]


t2.Scan("nNeutrPart_fromNu","isPrimary && nChargedPart_fromNu==0 && event==744")
t2.Scan("idStrNeutrPart_fromNu","isPrimary && nChargedPart_fromNu==0 && event==744")
t2.Scan("idStrPart_fromNu","isPrimary && nChargedPart_fromNu==0 && event==744")
t2.Draw("idStrPart_fromNu","isPrimary && nChargedPart_fromNu==0 && event==744")
  
assert(False)
## To be applied to all plots 
basicCut = "isPrimary==1 && nNu==1"
firstWindowCut = "startZ_nu>%s && startZ_nu<%s && interactionElement==1"%(entranceWindows[0][0],entranceWindows[0][1])
secondWindowCut = "startZ_nu>%s && startZ_nu<%s"%(entranceWindows[1][0],entranceWindows[1][1])

OPERACut = "interactionElement==0 || interactionElement==3 || interactionElement==999"

c = []

c.append(TCanvas('z_noChargedPart','interElem_noChargedPart'))
t2.Draw("startZ_nu", "%s && nChargedPart_fromNu==0"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())
assert(False)

c.append(TCanvas('secondWnCharged','secondWnCharged'))
t2.Draw("nChargedPart_fromNu", "%s && %s"%(basicCut,secondWindowCut))
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('secondWnNeutr','secondWnNeutr'))
t2.Draw("nNeutrPart_fromNu", "%s && %s"%(basicCut,secondWindowCut))
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('secondWCharged_oneCP','secondWCharged_oneCP'))
t2.Draw("idStrChargedPart_fromNu", "%s && %s && nChargedPart_fromNu==1"%(basicCut,secondWindowCut))
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('secondWNeutr_oneCP','secondWNeutr_oneCP'))
t2.Draw("idStrNeutrPart_fromNu", "%s && %s && nChargedPart_fromNu==1"%(basicCut,secondWindowCut))
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

assert(False)

c.append(TCanvas('allCharged','allCharged'))
t2.Draw("idStrChargedPart_fromNu", "%s"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('allNeutr','allNeutr'))
t2.Draw("idStrNeutrPart_fromNu", "%s"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('nCharged','nCharged'))
t2.Draw("nChargedPart_fromNu", "%s"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('nNeutr','nNeutr'))
t2.Draw("nNeutrPart_fromNu", "%s"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('Neutr_fromNu_noCharged','Neutr_fromNu_noCharged'))
t2.Draw("idStrNeutrPart_fromNu", "%s && nChargedPart_fromNu==0"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())

c.append(TCanvas('interElem_noChargedPart','interElem_noChargedPart'))
t2.Draw("interactionElement", "%s && nChargedPart_fromNu==0"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())

c.append(TCanvas('firstWCharged','firstWCharged'))
t2.Draw("idStrChargedPart_fromNu", "%s && %s"%(basicCut,firstWindowCut))
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('firstWNeutr','firstWNeutr'))
t2.Draw("idStrNeutrPart_fromNu", "%s && %s"%(basicCut,firstWindowCut))
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('secondWCharged','secondWCharged'))
t2.Draw("idStrChargedPart_fromNu", "%s && %s"%(basicCut,secondWindowCut))
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('secondWNeutr','secondWNeutr'))
t2.Draw("idStrNeutrPart_fromNu", "%s && %s"%(basicCut,secondWindowCut))
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

## Is the opera-mu-system enought to veto the nu-background before the vacuum tank, assuming an eff. of 90% on each station? 
c.append(TCanvas("effMuSystem","effMuSystem"))
t2.Draw("RPC_eff","%s"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())

## Check interaction place:
## Opera+Entrance Windows
c.append(TCanvas("intPlace_operaEntrW","interactionPlace_operaEntrW"))
t2.Draw("startZ_nu", "%s &&startZ_nu>-3000 && startZ_nu<-2478"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())

c.append(TCanvas("intPlace_volume","interactionPlace_volume"))
t2.Draw("startZ_nu", "%s &&startZ_nu>-2478"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())

######## WITH KS #########
c.append(TCanvas('withKsCharged','withKsCharged'))
t2.Draw("idStrChargedPart_withKs", "%s"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('withKsNeutr','withKsNeutr'))
t2.Draw("idStrNeutrPart_withKs", "%s"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('nChargedwithKs','nChargedwithKs'))
t2.Draw("nChargedPart_withKs", "%s"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.eps"%c[-1].GetName())

c.append(TCanvas('nNeutrwithKs','nNeutrwithKs'))
t2.Draw("nNeutrPart_withKs", "%s"%basicCut)
c[-1].Print("%s.eps"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.pdf"%c[-1].GetName())

c.append(TCanvas('Neutr_withKs_noCharged','Neutr_withKs_noCharged'))
t2.Draw("idStrNeutrPart_withKs", "%s && nChargedPart_withKs==0"%basicCut)
c[-1].Print("%s.pdf"%c[-1].GetName())

######## WITH KL #########
c.append(TCanvas('withKLCharged','withKLCharged'))
t2.Draw("idStrChargedPart_withKL", "%s"%basicCut)
c[-1].Print("%s.pdf"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.pdf"%c[-1].GetName())

c.append(TCanvas('withKLNeutr','withKLNeutr'))
t2.Draw("idStrNeutrPart_withKL", "%s"%basicCut)
c[-1].Print("%s.pdf"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.pdf"%c[-1].GetName())

c.append(TCanvas('nChargedwithKL','nChargedwithKL'))
t2.Draw("nChargedPart_withKL", "%s"%basicCut)
c[-1].Print("%s.pdf"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.pdf"%c[-1].GetName())

c.append(TCanvas('nNeutrwithKL','nNeutrwithKL'))
t2.Draw("nNeutrPart_withKL", "%s"%basicCut)
c[-1].Print("%s.pdf"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.pdf"%c[-1].GetName())

c.append(TCanvas('Neutr_withKL_noCharged','Neutr_withKL_noCharged'))
t2.Draw("idStrNeutrPart_withKL", "%s && nChargedPart_withKL==0"%basicCut)
c[-1].Print("%s.pdf"%c[-1].GetName())

######## WITH N #########
c.append(TCanvas('withNCharged','withNCharged'))
t2.Draw("idStrChargedPart_withN", "%s"%basicCut)
c[-1].Print("%s.pdf"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.pdf"%c[-1].GetName())

c.append(TCanvas('withNNeutr','withNNeutr'))
t2.Draw("idStrNeutrPart_withKL", "%s"%basicCut)
c[-1].Print("%s.pdf"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.pdf"%c[-1].GetName())

c.append(TCanvas('nChargedwithN','nChargedwithN'))
t2.Draw("nChargedPart_withN", "%s"%basicCut)
c[-1].Print("%s.pdf"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.pdf"%c[-1].GetName())

c.append(TCanvas('nNeutrwithN','nNeutrwithN'))
t2.Draw("nNeutrPart_withN", "%s"%basicCut)
c[-1].Print("%s.pdf"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("%s_logScale.pdf"%c[-1].GetName())

c.append(TCanvas('Neutr_withN_noCharged','Neutr_withN_noCharged'))
t2.Draw("idStrNeutrPart_withN", "%s && nChargedPart_withN==0"%basicCut)
c[-1].Print("%s.pdf"%c[-1].GetName())

assert(False)






ptype = ['', 'Neutr', 'Charged']
stype = ['fromNu','withKs','withKL','withN']

def extendToAllTypes(plotVars, strBase, mytype):
    plotVars += [strBase %i for i in mytype ]



## Is the opera-mu-system enought to veto the nu-background before the vacuum tank, assuming an eff. of 90% on each station? 
c_muSystEff = TCanvas("c_effMuSyst","c_effMuSyst")
t2.Draw("RPC_eff","%s"%basicCut)

## How much background is produced by the vacuum tank windows? 
## From first window:
#firstWindowCut = "startZ_nu>-2501.8 && startZ_nu<-2498.8"
#t2.Draw("idStrPart_fromNu", "isPrimary==1 && nNu==1 && nChargedPart_fromNu==1")
#t2.Draw("idStrChargedPart_fromNu", "isPrimary==1 && nNu==1 && startZ_nu>-2501.8 && startZ_nu<-2478 && nChargedPart_fromNu==1")
#t2.Draw("idStrNeutrPart_fromNu", "isPrimary==1 && nNu==1 && startZ_nu>-2501.8 && startZ_nu<-2478 && nChargedPart_fromNu==1")

## From second window:
secondWindowCut = "startZ_nu>-2478.8 && startZ_nu<-2478"
#t2.Draw("idStrPart_fromNu", "%s && %s "%(basicCut, secondWindowCut))

#t2.Draw("idStrNeutrPart_fromNu", "isPrimary==1 && nNu==1 && startZ_nu>-2501.8 && startZ_nu<-2478 && nChargedPart_fromNu==1")

c.append(TCanvas('allCharged','allCharged'))
t2.Draw("idStrPart_fromNu", "%s"%basicCut)
c[-1].Print("plot/%s.pdf"%c[-1].GetName())
c[-1].SetLogy(kTRUE)
c[-1].Print("plot/%s_logScale.pdf"%c[-1].GetName())


#c.append(TCanvas('allNeutr','allCharged')
#t2.Draw("idStrPart_fromNu", "isPrimary==1 && nNu==1 && nChargedPart_fromNu==1")
#c[-1].Print("plot/%s.pdf"%c[-1].GetName())
#c[-1].SetLogY(kTRUE)
#c[-1].Print("plot/%s_logScale.pdf"%c[-1].GetName())

assert(False)




## The leaves name are of type idStrChargedPart_fromNu for example. 
## The part that can vary are "Charged" and "fromNu". The possibilities 
## are listed in ptype and stype. Then the string are automatically 
## generated

plotVars_part0 = []
plotVars_part1 = []

strBase0 = "Part_%s"
extendToAllTypes(plotVars_part1,strBase0,stype)

strBase = "idStr%s"
#for strBase in strsBase: 
extendToAllTypes(plotVars_part0,strBase,ptype)

plotVar = [p0+p1 for (p0,p1) in zip(plotVars_part0, plotVars_part1)]
print plotVar

c = []
for pv in plotVar:
    print pv
    c.append(TCanvas("c_%s"%pv,"c_%s"%pv))
    t.Draw(pv,"%s"%(basicCut))
