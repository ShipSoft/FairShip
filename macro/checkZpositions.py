from __future__ import print_function
import ROOT,sys
from rootpyPickler import Unpickler
badBoys={}
f1,f2 = sys.argv[1], sys.argv[2]
fgeoOld=ROOT.TFile(f1)
upkl    = Unpickler(fgeoOld)
ShipGeoOld = upkl.load('ShipGeo')
fgeoNew=ROOT.TFile(f2)
upkl    = Unpickler(fgeoNew)
ShipGeoNew = upkl.load('ShipGeo')
for x in ShipGeoNew:
   if hasattr(eval('ShipGeoNew.'+x),'z'): 
     zold,znew = eval('ShipGeoOld.'+x+'.z'),eval('ShipGeoNew.'+x+'.z')
     print(x,'z=',znew, ' old:', zold)
     if  zold!=znew: badBoys[x]=[znew,zold]
if len(badBoys)>0: print("following differences detected:")
for x in badBoys:
  print(x,badBoys[x])

