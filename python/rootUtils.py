#---Enable Tab completion-----------------------------------------
try:
  import rlcompleter, readline
  readline.parse_and_bind( 'tab: complete' )
  readline.parse_and_bind( 'set show-all-if-ambiguous On' )
except:
  pass


from ROOT import TFile,gROOT,TH3F,TH2F,TH1F,TCanvas

def readHists(h,fname):
  f = TFile(fname)
  for akey in f.GetListOfKeys():
    name  =  akey.GetName()
    cln = f.FindObjectAny(name).Class().GetName()
    if cln.find('TH')<0: continue
    if h.has_key(name): h[name].Add(f.FindObjectAny(name))
    else: h[name] =  f.FindObjectAny(name).Clone()
    h[name].SetDirectory(gROOT)
    h[name].Sumw2() 
    if cln == 'TH2D' or cln == 'TH2F':
         for p in [ '_projx','_projy']:
           if p.find('x')>-1: h[name+p] = h[name].ProjectionX()  
           else             : h[name+p] = h[name].ProjectionY()  
           h[name+p].SetName(name+p)
           h[name+p].SetDirectory(gROOT)
  return
def bookHist(h,key=None,title='',nbinsx=100,xmin=0,xmax=1,nbinsy=0,ymin=0,ymax=1,nbinsz=0,zmin=0,zmax=1):
  if key==None : 
    print 'missing key'
    return
  if h.has_key(key):    h[key].Reset()  
  elif nbinsz >0:       h[key] = TH3F(key,title,nbinsx,xmin,xmax,nbinsy,ymin,ymax,nbinsz,zmin,zmax) 
  elif nbinsy >0:       h[key] = TH2F(key,title,nbinsx,xmin,xmax,nbinsy,ymin,ymax) 
  else:                 h[key] = TH1F(key,title,nbinsx,xmin,xmax)
  h[key].SetDirectory(gROOT)

def writeHists(h,fname):
  f = TFile(fname,'RECREATE')
  for akey in h:
    cln = h[akey].Class().GetName()
    if cln.find('TH')<0: continue
    h[akey].Write()
  f.Close()  
def bookCanvas(h,key=None,title='',nx=900,ny=600,cx=1,cy=1):
  if key==None : 
    print 'missing key'
    return
  if not h.has_key(key):
    h[key]=TCanvas(key,title,nx,ny) 
    h[key].Divide(cx,cy)

def printout(atc,name,Work):
  atc.Update()
  for x in ['.gif','.eps','.jpg'] :  
    temp = name+x
    atc.Print(temp)
    if x!='.jpg':
      os.system('cp '+temp+' '+Work)

def setAttributes(pyl,leaves,printout=False):
  names = {}
  if printout: print 'entries',leaves.GetEntries() 
  for i in range(0,leaves.GetEntries() ) :          
    leaf = leaves.At(i)                          
    name = leaf.GetName()
    if printout: print name
    names[name]=i                        
    pyl.__setattr__(name,leaf)                
  return names
# read back
class PyListOfLeaves(dict) : 
    pass  

