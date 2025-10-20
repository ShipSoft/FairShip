import ROOT,sys
from ShipGeoConfig import load_from_root_file
badBoys={}
f1,f2 = sys.argv[1], sys.argv[2]
fgeoOld=ROOT.TFile(f1)
ShipGeoOld = load_from_root_file(fgeoOld, 'ShipGeo')
fgeoNew=ROOT.TFile(f2)
ShipGeoNew = load_from_root_file(fgeoNew, 'ShipGeo')
for x in ShipGeoNew:
   if hasattr(eval('ShipGeoNew.'+x),'z'):
     zold,znew = eval('ShipGeoOld.'+x+'.z'),eval('ShipGeoNew.'+x+'.z')
     print(x,'z=',znew, ' old:', zold)
     if  zold!=znew: badBoys[x]=[znew,zold]
if len(badBoys)>0: print("following differences detected:")
for x in badBoys:
  print(x,badBoys[x])
