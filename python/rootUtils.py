# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

from ROOT import TFile,gROOT,TH3D,TH2D,TH1D,TCanvas,TProfile,gSystem
import os
from collections import Counter

_error_log = Counter()

def readHists(h,fname,wanted=[]):
  if fname[0:4] == "/eos":
    eospath = gSystem.Getenv("EOSSHIP")+fname
    f = TFile.Open(eospath)
  else:
    f = TFile(fname)
  for akey in f.GetListOfKeys():
    name  =  akey.GetName()
    try:     hname = int(name)
    except:  hname = name
    if len(wanted)>0:
        if not hname in wanted: continue
    obj = akey.ReadObj()
    cln = obj.Class().GetName()
    if not cln.find('TCanv')<0:
       h[hname] =  obj.Clone()
    if cln.find('TH')<0: continue
    if hname in h:
       rc = h[hname].Add(obj)
       if not rc: print("Error when adding histogram ",hname)
    else:
      h[hname] =  obj.Clone()
      if h[hname].GetSumw2N()==0 : h[hname].Sumw2()
    h[hname].SetDirectory(gROOT)
    if cln == 'TH2D' or cln == 'TH2F':
         for p in [ '_projx','_projy']:
           if type(hname) == str: projname = hname+p
           else: projname = str(hname)+p
           if p.find('x')>-1: h[projname] = h[hname].ProjectionX()
           else             : h[projname] = h[hname].ProjectionY()
           h[projname].SetName(name+p)
           h[projname].SetDirectory(gROOT)
  return
def bookHist(h,key=None,title='',nbinsx=100,xmin=0,xmax=1,nbinsy=0,ymin=0,ymax=1,nbinsz=0,zmin=0,zmax=1):
  if key==None :
    print('missing key')
    return
  rkey = str(key) # in case somebody wants to use integers, or floats as keys
  if key in h:    h[key].Reset()
  elif nbinsz >0:       h[key] = TH3D(rkey,title,nbinsx,xmin,xmax,nbinsy,ymin,ymax,nbinsz,zmin,zmax)
  elif nbinsy >0:       h[key] = TH2D(rkey,title,nbinsx,xmin,xmax,nbinsy,ymin,ymax)
  else:                 h[key] = TH1D(rkey,title,nbinsx,xmin,xmax)
  h[key].SetDirectory(gROOT)
def bookProf(h,key=None,title='',nbinsx=100,xmin=0,xmax=1,ymin=None,ymax=None,option=""):
  if key==None :
    print('missing key')
    return
  rkey = str(key) # in case somebody wants to use integers, or floats as keys
  if key in h:    h[key].Reset()
  if ymin==None or ymax==None:  h[key] = TProfile(key,title,nbinsx,xmin,xmax,option)
  else:  h[key] = TProfile(key,title,nbinsx,xmin,xmax,ymin,ymax,option)
  h[key].SetDirectory(gROOT)
def writeHists(h,fname,plusCanvas=False):
  f = TFile(fname,'RECREATE')
  for akey in h:
    if not hasattr(h[akey],'Class'): continue
    cln = h[akey].Class().GetName()
    if not cln.find('TH')<0 or not cln.find('TP')<0:   h[akey].Write()
    if plusCanvas and not cln.find('TC')<0:   h[akey].Write()
  f.Close()
def bookCanvas(h,key=None,title='',nx=900,ny=600,cx=1,cy=1):
  if key==None :
    print('missing key')
    return
  if key not in h:
    h[key]=TCanvas(key,title,nx,ny)
    h[key].Divide(cx,cy)
def reportError(s):
 _error_log[s] += 1
def errorSummary():
 if _error_log:
    print("Summary of recorded incidents:")
 for e in _error_log:
    print(e, ':', _error_log[e])

def checkFileExists(x):

    if isinstance(x, list):
        print("I'm a list")
        for _f in x:
            if _f[0:4] == "/eos": f=gSystem.Getenv("EOSSHIP")+_f
            else: f=_f
            test = TFile.Open(f)
            if not test:
               print("input file",f," does not exist. Missing authentication?")
               os._exit(1)
            if test.FindObjectAny('cbmsim'):
             return 'tree'
            else:
             return 'ntuple'
    else:
        if x[0:4] == "/eos": f=gSystem.Getenv("EOSSHIP")+x
        else: f=x
        test = TFile.Open(f)
        if not test:
           print("input file",f," does not exist. Missing authentication?")
           os._exit(1)
        if test.FindObjectAny('cbmsim'):
         return 'tree'
        else:
         return 'ntuple'
