#!/usr/bin/env python 
#prints z-coordinators of SHiP detector volumes
#WARNING: printing the entire geometry takes a lot of time
#24-02-2015 comments to EvH

from __future__ import print_function, division
from builtins import range
import operator, sys
from argparse import ArgumentParser
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
    shifts = [ [-tmp.GetDX()+o[0],o[1],o[2]],
               [tmp.GetDX()+o[0],o[1],o[2]],
               [o[0],-tmp.GetDY()+o[1],o[2]],
               [o[0],tmp.GetDY()+o[1],o[2]],
               [o[0],o[1],-tmp.GetDZ()+o[2]],[o[0],o[1],tmp.GetDZ()+o[2]]
             ]
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

def print_info(path, node, level, currentlevel, print_sub_det_info=False):
  sub_nodes = {}
  fullInfo = {}
  for subnode in node.GetNodes():
    name = subnode.GetName()
    fullInfo[name] = local2Global(path + '/' + name)
    sub_nodes[name] = fullInfo[name]['origin'][2]

  for name, _ in sorted(list(sub_nodes.items()), key=operator.itemgetter(1)):
    boundingbox = fullInfo[name]['boundingbox']

    format_string = "{:<28s}: z={:10.4F}cm  dZ={:10.4F}cm  [{:10.4F}   {:10.4F}]"+\
                    " dx={:10.4F}cm [{:10.4F}   {:10.4F}] dy={:10.4F}cm [{:10.4F}   {:10.4F}] {:>20s}"

    format_variable = ["   " * int(currentlevel) + name, fullInfo[name]['origin'][2],
      abs(boundingbox[2][0]-boundingbox[2][1])/2., boundingbox[2][0],boundingbox[2][1],
      abs(boundingbox[0][0]-boundingbox[0][1])/2., boundingbox[0][0],boundingbox[0][1],
      abs(boundingbox[1][0]-boundingbox[1][1])/2., boundingbox[1][0],boundingbox[1][1],
      fullInfo[name]['material']]

    if options.moreInfo:
      cubicmeter = fullInfo[name]['cubicmeter']
      weight = fullInfo[name]['weight']
      format_string += " {:10.1F}kg {:10.1F}m3"
      format_variable.extend([weight, cubicmeter])

    print (format_string.format(*format_variable))

    if options.volume in ["", name]:
      print_sub_det_info = True

    if print_sub_det_info and currentlevel < level and fullInfo[name]['node'].GetNodes():
      print_info(fullInfo[name]['path'], fullInfo[name]['node'], level, currentlevel + 1,
                 print_sub_det_info)

    if currentlevel == 0:
      print_sub_det_info = False


parser = ArgumentParser()
parser.add_argument("-g", "--geometry", dest="geometry", help="input geometry file",
                    required=True)
parser.add_argument("-l", "--level", dest="level", help="max subnode level", default=0)
parser.add_argument("-v", "--volume", dest="volume", help="name of volume to expand", default="")
parser.add_argument("-X", "--moreInfo", dest="moreInfo", help="print weight and capacity", default=False)

options = parser.parse_args()
fname = options.geometry
if fname.startswith('/eos/'):
    fname = os.environ['EOSSHIP'] + fname
fgeom = ROOT.TFile.Open(fname)
fGeo = fgeom.FAIRGeom
top = fGeo.GetTopVolume()


if options.moreInfo:
 print ("   Detector element             z(midpoint)     halflength       volume-start volume-end   dx"\
        "                x-start       x-end       dy                y-start       y-end         material          weight  capacity")
else:
 print ("   Detector element             z(midpoint)     halflength       volume-start volume-end   dx"\
        "                x-start       x-end       dy                y-start       y-end         material")

currentlevel = 0
print_info("", top, int(options.level), currentlevel)
