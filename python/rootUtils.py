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
    try:     hname = int(name)
    except:  hname = name
    cln = f.FindObjectAny(name).Class().GetName()
    if cln.find('TH')<0: continue
    if h.has_key(hname): h[hname].Add(f.FindObjectAny(name))
    else: h[hname] =  f.FindObjectAny(name).Clone()
    h[hname].SetDirectory(gROOT)
    h[hname].Sumw2() 
    if cln == 'TH2D' or cln == 'TH2F':
         for p in [ '_projx','_projy']:
           if p.find('x')>-1: h[hname+p] = h[hname].ProjectionX()  
           else             : h[hname+p] = h[hname].ProjectionY()  
           h[hname+p].SetName(name+p)
           h[hname+p].SetDirectory(gROOT)
  return
def bookHist(h,key=None,title='',nbinsx=100,xmin=0,xmax=1,nbinsy=0,ymin=0,ymax=1,nbinsz=0,zmin=0,zmax=1):
  if key==None : 
    print 'missing key'
    return
  rkey = str(key) # in case somebody wants to use integers, or floats as keys 
  if h.has_key(key):    h[key].Reset()  
  elif nbinsz >0:       h[key] = TH3F(rkey,title,nbinsx,xmin,xmax,nbinsy,ymin,ymax,nbinsz,zmin,zmax) 
  elif nbinsy >0:       h[key] = TH2F(rkey,title,nbinsx,xmin,xmax,nbinsy,ymin,ymax) 
  else:                 h[key] = TH1F(rkey,title,nbinsx,xmin,xmax)
  h[key].SetDirectory(gROOT)

def writeHists(h,fname,plusCanvas=False):
  f = TFile(fname,'RECREATE')
  for akey in h:
    cln = h[akey].Class().GetName()
    if not cln.find('TH')<0:   h[akey].Write()
    if plusCanvas and not cln.find('TC')<0:   h[akey].Write()
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


def container_sizes(f):
 f = TFile(f)
 t = f.FindObjectAny('cbmsim')
 print "name      ZipBytes    TotBytes    TotalSize"
 for b in t.GetListOfBranches():
  print b.GetName(),b.GetZipBytes(),b.GetTotBytes(),b.GetTotalSize()


