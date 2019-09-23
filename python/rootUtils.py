from __future__ import print_function
from __future__ import division
#---Enable Tab completion-----------------------------------------
try:
  import rlcompleter, readline
  readline.parse_and_bind( 'tab: complete' )
  readline.parse_and_bind( 'set show-all-if-ambiguous On' )
except:
  pass


from ROOT import TFile,gROOT,TH3D,TH2D,TH1D,TCanvas,TProfile,gSystem
import os,sys

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
           if type(hname) == type('s'): projname = hname+p
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
 l = sys.modules['__main__'].log
 if s not in l: l[s]=0
 l[s]+=1  
def errorSummary():
 l = sys.modules['__main__'].log
 if len(l) > 0: "Summary of recorded incidents:"
 for e in l:
    print(e,':',l[e])
def printout(atc,name,Work):
  atc.Update()
  for x in ['.gif','.eps','.jpg'] :  
    temp = name+x
    atc.Print(temp)
    if x!='.jpg':
      os.system('cp '+temp+' '+Work)

def setAttributes(pyl,leaves,printout=False):
  names = {}
  if printout: print('entries',leaves.GetEntries()) 
  for i in range(0,leaves.GetEntries() ) :          
    leaf = leaves.At(i)                          
    name = leaf.GetName()
    if printout: print(name)
    names[name]=i                        
    pyl.__setattr__(name,leaf)                
  return names
# read back
class PyListOfLeaves(dict) : 
    pass  

import operator
def container_sizes(sTree,perEvent=False):
 counter = {}
 print("name      ZipBytes[MB]    TotBytes[MB]    TotalSize[MB]")
 counter['total']=[0,0,0]
 for l in sTree.GetListOfLeaves():
  b = l.GetBranch()
  nm = b.GetName()
  print("%30s :%8.3F   %8.3F    %8.3F "%(nm,b.GetZipBytes()/1.E6,b.GetTotBytes()/1.E6,b.GetTotalSize()/1.E6))
  bnm = nm.split('.')[0] 
  if bnm not in counter: counter[bnm]=[0,0,0]
  counter[bnm][0]+=b.GetZipBytes()/1.E6
  counter[bnm][1]+=b.GetTotBytes()/1.E6
  counter[bnm][2]+=b.GetTotalSize()/1.E6
  counter['total'][0]+=b.GetZipBytes()/1.E6
  counter['total'][1]+=b.GetTotBytes()/1.E6
  counter['total'][2]+=b.GetTotalSize()/1.E6
 print("---> SUMMARY <---------------")
 N = sTree.GetEntries()/1000.
 if perEvent:
  print("                     name     ZipBytes[kB]/ev  TotBytes[kB]/ev  TotalSize[kB]/ev") 
 else:
  print("                     name     ZipBytes[MB]  TotBytes[MB]  TotalSize[MB]") 
 sorted_c = sorted(counter.items(), key=operator.itemgetter(1))
 sorted_c.reverse()
 for i in range(len(sorted_c)):
  x = sorted_c[i][0]
  if perEvent:
   print("%30s :%8.3F      %8.3F       %8.3F"%(x,counter[x][0]/N,counter[x][1]/N,counter[x][2]/N))
  else:
   print("%30s :%8.3F   %8.3F    %8.3F"%(x,counter[x][0],counter[x][1],counter[x][2]))

def stripOffBranches(fout):
    f = TFile(fout)
    sTree = f.cbmsim
    nEvents = sTree.GetEntries() 
    strip = False
    oldTargetClass = False
    if sTree.GetBranch("SmearedHits"): 
         sTree.SetBranchStatus("SmearedHits",0)
         strip = True
    if sTree.GetBranch("TargetPoint"): 
         if sTree.GetLeaf("cbmroot.Target.TargetPoint.fEmTop"): oldTargetClass = True # old class
         else: 
           for x in sTree.GetListOfLeaves():
              if not x.GetName().find("TargetPoint")<0: 
               b = x.GetBranch().GetName()
               sTree.SetBranchStatus(b,0)
         strip = True
    if not strip: return 
    sFile = fout.replace("_rec.root","_recs.root")
    recf = TFile(sFile,"recreate")
    if not oldTargetClass: newTree = sTree.CloneTree(-1,'fast')
    else:
     newTree = sTree.CloneTree(0)
     for n in range(nEvents):
      sTree.GetEntry(n)
      if oldTargetClass: sTree.TargetPoint.Clear()
      rc = newTree.Fill()
      sTree.FitTracks.Delete() # stupid ROOT or whoever, otherwise huge memory leak, does not help
    sTree.Clear()
    newTree.AutoSave()
    f.Close() 
    recf.Close() 
    # should do some sanity checks before deleting old file
    f = TFile(sFile)
    sTree = f.cbmsim
    if nEvents == sTree.GetEntries(): print("looks ok, could be deleted",os.path.abspath('.'))
    else:  print("stripping failed, keep old file",os.path.abspath('.'))
    # os.system('mv '+sFile +' '+fout)
def checkFileExists(x):
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
def findMaximumAndMinimum(histo):
 amin,amax = 1E30, -130
 nmin,nmax = 0, 0
 for n in range(1,histo.GetNbinsX()+1):
  c =  histo.GetBinContent(n)
  if c>amax:
    amax = c
    nmax = n
  if c<amin:
    amin = c
    nmin = n
 return amin,amax,nmin,nmax
def makeIntegralDistrib(h,key):
 name = 'I-'+key
 h[name]=h[key].Clone(name)
 h[name].SetTitle('Integral > '+h[key].GetTitle())
 for n in range(1,h[key].GetNbinsX()+1):
   if n==1: h[name].SetBinContent(1,h[key].GetSumOfWeights())
   else: h[name].SetBinContent(n,h[name].GetBinContent(n-1)-h[key].GetBinContent(n-1))
