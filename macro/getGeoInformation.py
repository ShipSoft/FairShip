#!/usr/bin/env python 
#prints z-coordinators of SHiP detector volumes
#WARNING: printing the entire geometry takes a lot of time
#24-02-2015 comments to EvH

import operator, sys, getopt
from optparse import OptionParser
import os,ROOT

def doloop(node,level,currentlevel,translation):
  newcurrentlevel=int(currentlevel)+1
  blanks="   "*int(newcurrentlevel)
  snoz={}
  snox={}
  snoy={}
  for subnode in node.GetNodes():
     transsno = subnode.GetMatrix()
     snoz[subnode] = translation[2]+transsno.GetTranslation()[2]
     snox[subnode] = translation[0]+transsno.GetTranslation()[0]  
     snoy[subnode] = translation[1]+transsno.GetTranslation()[1]         
  for key in sorted(snoz.items(),key=operator.itemgetter(1)):
     transs = key[0].GetMatrix()   
     vs = key[0].GetVolume().GetShape()
     material = key[0].GetVolume().GetMaterial().GetName()
     newztranslation=snoz[key[0]]
     newxtranslation=snox[key[0]]
     newytranslation=snoy[key[0]]
     name =  blanks+key[0].GetName()
     print "%-28s: z=%10.4Fcm  dZ=%10.4Fcm  [%10.4F   %10.4F] dx=%10.4Fcm [%10.4F   %10.4F] dy=%10.4Fcm [%10.4F   %10.4F] %+20s"%(name,newztranslation,\
     vs.GetDZ(),min(newztranslation-vs.GetDZ(),newztranslation+vs.GetDZ()),max(newztranslation-vs.GetDZ(),newztranslation+vs.GetDZ()),\
     vs.GetDX(),min(newxtranslation-vs.GetDX(),newxtranslation+vs.GetDX()),max(newxtranslation-vs.GetDX(),newxtranslation+vs.GetDX()),\
     vs.GetDY(),min(newytranslation-vs.GetDY(),newytranslation+vs.GetDY()),max(newytranslation-vs.GetDY(),newytranslation+vs.GetDY()),material )
     if int(newcurrentlevel)<int(level) and key[0].GetNodes():
        doloop(key[0],level,newcurrentlevel,[newxtranslation, newytranslation, newztranslation])

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-g","--geometry", dest="geometry", help="input geometry file", default='$FAIRSHIP/geofile_full.10.0.Pythia8-TGeant4.root')
parser.add_option("-l","--level", dest="level", help="max subnode level", default=0)
parser.add_option("-v","--volume", dest="volume", help="name of volume to expand",default="")

(options,args)=parser.parse_args()
tgeom = ROOT.TGeoManager("Geometry", "Geane geometry")
tgeom.Import(options.geometry)
fGeo = ROOT.gGeoManager 
top = fGeo.GetTopVolume() 
noz={}
currentlevel=0
print "   Detector element             z(midpoint)     halflength       volume-start volume-end   dx                x-start       x-end       dy                y-start       y-end         material "
for no in top.GetNodes():
  transno = no.GetMatrix()
  noz[no]=transno.GetTranslation()[2]
for key in sorted(noz.items(),key=operator.itemgetter(1)):
    trans = key[0].GetMatrix()
    v = key[0].GetVolume().GetShape()
    mat = key[0].GetVolume().GetMaterial().GetName()
    name = key[0].GetName()
    print "%-28s: z=%10.4Fcm  dZ=%10.4Fcm  [%10.4F   %10.4F] dx=%10.4Fcm [%10.4F   %10.4F] dy=%10.4Fcm [%10.4F   %10.4F]    %+20s"%(name,trans.GetTranslation()[2],\
    v.GetDZ(),min(trans.GetTranslation()[2]-v.GetDZ(),trans.GetTranslation()[2]+v.GetDZ()),max(trans.GetTranslation()[2]-v.GetDZ(),trans.GetTranslation()[2]+v.GetDZ()),\
    v.GetDX(),min(trans.GetTranslation()[0]-v.GetDX(),trans.GetTranslation()[0]+v.GetDX()),max(trans.GetTranslation()[0]-v.GetDX(),trans.GetTranslation()[0]+v.GetDX()),\
    v.GetDY(),min(trans.GetTranslation()[1]-v.GetDY(),trans.GetTranslation()[1]+v.GetDY()),max(trans.GetTranslation()[1]-v.GetDY(),trans.GetTranslation()[1]+v.GetDY()),mat,)
    if options.volume:
      if key[0].GetNodes() and int(options.level)>0 and options.volume==key[0].GetName():
         doloop(key[0],options.level,currentlevel,trans.GetTranslation()) 
    else:
      if key[0].GetNodes() and int(options.level)>0:
         doloop(key[0],options.level,currentlevel,trans.GetTranslation())     
    


