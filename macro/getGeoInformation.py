#!/usr/bin/env python 
#prints z-coordinators of SHiP detector volumes
#WARNING: printing the entire geometry takes a lot of time
#24-02-2015 comments to EvH

import operator, sys, getopt
from optparse import OptionParser
from array import array
import os,ROOT

def local2Global(n):
    Info={}
    nav = ROOT.gGeoManager.GetCurrentNavigator()
    nav.cd(n)
    Info['node'] = nav.GetCurrentNode()
    Info['path'] = n
    tmp = nav.GetCurrentNode().GetVolume().GetShape()
    Info['material'] = nav.GetCurrentNode().GetVolume().GetMaterial().GetName()
    local = array('d',[0,0,0])
    globOrigin  = array('d',[0,0,0])
    nav.LocalToMaster(local,globOrigin)
    Info['origin'] = globOrigin
    shifts = [ [-tmp.GetDX(),0,0],[tmp.GetDX(),0,0],[0,-tmp.GetDY(),0],[0,tmp.GetDY(),0],[0,0,-tmp.GetDZ()],[0,0,tmp.GetDZ()]]
    shifted = []
    for s in shifts:
     local = array('d',s)
     glob  = array('d',[0,0,0])
     nav.LocalToMaster(local,glob)
     shifted.append([glob[0],glob[1],glob[2]])
    Info['boundingbox']={}
    for j in range(3):
     jmin = 1E30
     jmax = -1E30
     for s in shifted:
       if s[j]<jmin: jmin = s[j]
       if s[j]>jmax: jmax = s[j]
     Info['boundingbox'][j]=[jmin,jmax]
    return Info

def doloop(path,node,level,currentlevel):
  newcurrentlevel=int(currentlevel)+1
  blanks="   "*int(newcurrentlevel)
  snoz={}
  fullInfo = {}
  for subnode in node.GetNodes():
     name = subnode.GetName()
     fullInfo[name] = local2Global(path+'/'+name)
     snoz[name] = fullInfo[name]['origin'][2]
  for key in sorted(snoz.items(),key=operator.itemgetter(1)):
     name = key[0]
     boundingbox = fullInfo[name]['boundingbox']
     origin = fullInfo[name]['origin']
     material = fullInfo[name]['material']
     name =  blanks+key[0]
     print "%-28s: z=%10.4Fcm  dZ=%10.4Fcm  [%10.4F   %10.4F] dx=%10.4Fcm [%10.4F   %10.4F] dy=%10.4Fcm [%10.4F   %10.4F] %+20s"%(name,origin[2],\
     abs(boundingbox[2][0]-boundingbox[2][1])/2.,boundingbox[2][0],boundingbox[2][1],\
     abs(boundingbox[0][0]-boundingbox[0][1])/2.,boundingbox[0][0],boundingbox[0][1],\
     abs(boundingbox[1][0]-boundingbox[1][1])/2.,boundingbox[1][0],boundingbox[1][1],material)
     if int(newcurrentlevel)<int(level) and key[0].GetNodes():
        doloop(path+'/'+key[0].GetName(),key[0],level,newcurrentlevel)

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
fullInfo = {}
currentlevel=0
print "   Detector element             z(midpoint)     halflength       volume-start volume-end   dx                x-start       x-end       dy                y-start       y-end         material "
for no in top.GetNodes():
  name = no.GetName()
  fullInfo[name] = local2Global('/'+name)
  noz[name] = fullInfo[name]['origin'][2]
for key in sorted(noz.items(),key=operator.itemgetter(1)):
    name = key[0]
    path = fullInfo[name]['path']
    node = fullInfo[name]['node']
    mat  = fullInfo[name]['material']
    boundingbox = fullInfo[name]['boundingbox']
    origin = fullInfo[name]['origin']
    print "%-28s: z=%10.4Fcm  dZ=%10.4Fcm  [%10.4F   %10.4F] dx=%10.4Fcm [%10.4F   %10.4F] dy=%10.4Fcm [%10.4F   %10.4F]    %+20s"%(name,origin[2],\
     abs(boundingbox[2][0]-boundingbox[2][1])/2.,boundingbox[2][0],boundingbox[2][1],\
     abs(boundingbox[0][0]-boundingbox[0][1])/2.,boundingbox[0][0],boundingbox[0][1],\
     abs(boundingbox[1][0]-boundingbox[1][1])/2.,boundingbox[1][0],boundingbox[1][1],mat)
    if options.volume:
      if node.GetNodes() and int(options.level)>0 and options.volume==name:
         doloop(path,node,options.level,currentlevel) 
    else:
      if node.GetNodes() and int(options.level)>0:
         doloop(path,node,options.level,currentlevel)
    


