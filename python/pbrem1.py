import ROOT,os,sys,getopt,math
import shipunit as u
import proton_bremsstrahlung

from array import array
import os,sys,getopt
#from decimal import float

lepto= False

try:
    opts, args = getopt.getopt(sys.argv[1:], "d:l:", ["date=","leptophilic="]) 
except getopt.GetoptError:
    sys.exit()
for o,a in opts:
    if o in ('-l','--leptophilic',): lepto = a
    if o in ('-d','--date',): date = a

def pbremProdRateNoFF(mass,epsilon,doprint=False):
    xswg = proton_bremsstrahlung.prodRate(mass, epsilon)
    if doprint: print "A' production rate per p.o.t: \t %.8g"%(xswg)
    penalty = proton_bremsstrahlung.penaltyFactor(mass)
    if doprint: print "A' penalty factor: \t %.8g"%penalty
    if doprint: print "A' rescaled production rate per p.o.t:\t %.8g"%(xswg*penalty)
    return xswg*penalty                           

def pbremProdRate(mass,epsilon,doprint=False):
    xswg = proton_bremsstrahlung.prodRate(mass, epsilon)
    if doprint: print "A' production rate per p.o.t: \t %.8g"%(xswg)
    rhoff = proton_bremsstrahlung.rhoFormFactor(mass)**2
    if doprint: print "A' rho form factor: \t %.8g"%rhoff
    if doprint: print "A' rescaled production rate per p.o.t:\t %.8g"%(xswg*rhoff)
    return xswg*rhoff


#prods=['meson_pi0','meson_omega','meson_eta','meson_eta1','meson','pbrem','qcd']
#prods=['meson','pbrem','qcd']
prods = ['pbrem']
for prod in prods:

    if not lepto: 
        outp="/afs/cern.ch/user/t/takmete/ShipDPAnalysis/data/"+date+"/"+prod+"1_Rate1.dat"
        inp="/afs/cern.ch/user/t/takmete/ShipDPAnalysis/data/"+date+"/"+prod+"_Rate1.dat"
    if lepto:
        outp="/afs/cern.ch/user/t/takmete/ShipDPAnalysis/data/"+date+"/"+prod+"1_Rate2.dat"
        inp="/afs/cern.ch/user/t/takmete/ShipDPAnalysis/data/"+date+"/"+prod+"_Rate2.dat" 
    f=open(inp,'r')
    k=f.readlines()
    l=open(outp,'w')
    for x in k:
        x=x.replace("\n","")
        x=x.split(" ")
        denom=pbremProdRate(float(x[0]),float(x[1]))
        nom=pbremProdRateNoFF(float(x[0]),float(x[1]))
        newR=float(x[2])*nom/denom
        l.write('%.5E %.9E %.9E' %(float(x[0]),float(x[1]),newR))
        l.write('\n')
    f.close()
    l.close()
