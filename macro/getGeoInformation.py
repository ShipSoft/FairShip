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
    tmp = Info['node'].GetVolume().GetShape()
    Info['material'] = Info['node'].GetVolume().GetMaterial().GetName()
    if options.moreInfo:
     x = ROOT.gGeoManager.GetVerboseLevel()
     ROOT.gGeoManager.SetVerboseLevel(0)
     Info['weight']=Info['node'].GetVolume().Weight() # kg
     Info['cubicmeter']=Info['node'].GetVolume().Capacity()/1000000. # 
     ROOT.gGeoManager.SetVerboseLevel(x)
    o = [tmp.GetOrigin()[0],tmp.GetOrigin()[1],tmp.GetOrigin()[2]]
    Info['locorign'] = o
    local = array('d',o)
    globOrigin  = array('d',[0,0,0])
    nav.LocalToMaster(local,globOrigin)
    Info['origin'] = globOrigin
    shifts = [ [-tmp.GetDX()+o[0],o[1],o[2]],[tmp.GetDX()+o[0],o[1],o[2]],[o[0],-tmp.GetDY()+o[1],o[2]],[o[0],tmp.GetDY()+o[1],o[2]],[o[0],o[1],-tmp.GetDZ()+o[2]],[o[0],o[1],tmp.GetDZ()+o[2]]]
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
     xname =  blanks+key[0]
     if options.moreInfo:
      cubicmeter = fullInfo[name]['cubicmeter']
      weight = fullInfo[name]['weight']
      print "%-28s: z=%10.4Fcm  dZ=%10.4Fcm  [%10.4F   %10.4F] dx=%10.4Fcm [%10.4F   %10.4F] dy=%10.4Fcm [%10.4F   %10.4F] %+20s %10.4Fkg %10.4Fm3"%(xname,origin[2],\
      abs(boundingbox[2][0]-boundingbox[2][1])/2.,boundingbox[2][0],boundingbox[2][1],\
      abs(boundingbox[0][0]-boundingbox[0][1])/2.,boundingbox[0][0],boundingbox[0][1],\
      abs(boundingbox[1][0]-boundingbox[1][1])/2.,boundingbox[1][0],boundingbox[1][1],material,weight,cubicmeter)
     else:
      print "%-28s: z=%10.4Fcm  dZ=%10.4Fcm  [%10.4F   %10.4F] dx=%10.4Fcm [%10.4F   %10.4F] dy=%10.4Fcm [%10.4F   %10.4F] %+20s "%(xname,origin[2],\
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
parser.add_option("-X","--moreInfo", dest="moreInfo", help="print weight and capacity",default=False)

(options,args)=parser.parse_args()
fname = options.geometry
if not fname.find('eos')<0: fname = os.environ['EOSSHIP']+fname
fgeom = ROOT.TFile.Open(fname)
fGeo = fgeom.FAIRGeom
top = fGeo.GetTopVolume()
noz={}
fullInfo = {}
currentlevel=0
if options.moreInfo:
 print "   Detector element             z(midpoint)     halflength       volume-start volume-end   dx                x-start       x-end       dy                y-start       y-end         material          weight  capacity"
else:
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
    if options.moreInfo:
     cubicmeter = fullInfo[name]['cubicmeter']
     weight = fullInfo[name]['weight']
     print "%-28s: z=%10.4Fcm  dZ=%10.4Fcm  [%10.4F   %10.4F] dx=%10.4Fcm [%10.4F   %10.4F] dy=%10.4Fcm [%10.4F   %10.4F]    %+20s %10.1Fkg %10.1Fm3"%(name,origin[2],\
      abs(boundingbox[2][0]-boundingbox[2][1])/2.,boundingbox[2][0],boundingbox[2][1],\
      abs(boundingbox[0][0]-boundingbox[0][1])/2.,boundingbox[0][0],boundingbox[0][1],\
      abs(boundingbox[1][0]-boundingbox[1][1])/2.,boundingbox[1][0],boundingbox[1][1],mat,weight,cubicmeter)
    else:
     print "%-28s: z=%10.4Fcm  dZ=%10.4Fcm  [%10.4F   %10.4F] dx=%10.4Fcm [%10.4F   %10.4F] dy=%10.4Fcm [%10.4F   %10.4F]    %+20s "%(name,origin[2],\
      abs(boundingbox[2][0]-boundingbox[2][1])/2.,boundingbox[2][0],boundingbox[2][1],\
      abs(boundingbox[0][0]-boundingbox[0][1])/2.,boundingbox[0][0],boundingbox[0][1],\
      abs(boundingbox[1][0]-boundingbox[1][1])/2.,boundingbox[1][0],boundingbox[1][1],mat)

    if options.volume:
      if node.GetNodes() and int(options.level)>0 and options.volume==name:
         doloop(path,node,options.level,currentlevel) 
    else:
      if node.GetNodes() and int(options.level)>0:
         doloop(path,node,options.level,currentlevel)


