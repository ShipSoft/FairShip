import ROOT,operator,sys
import rootUtils as ut
from argparse import ArgumentParser
PDG = ROOT.TDatabasePDG.Instance()

### Add what is missed:
### PDG nuclear states are 10-digit numbers
### 10LZZZAAAI e.g. deuteron is 
### 1000010020
### from http://svn.cern.ch/guest/AliRoot/trunk/STEER/STEERBase/AliPDG.cxx and https://github.com/FairRootGroup/FairRoot/blob/master/eventdisplay/FairEventManager.cxx
### https://geant4.web.cern.ch/geant4/UserDocumentation/UsersGuides/ForApplicationDeveloper/html/AllResources/TrackingAndPhysics/particleList.src/ions/index.html

def makeHistos():
   for x in os.listdir('ship-ubuntu-1710-32_miniShip_1'):
      if x.find('pythia8')!=0: continue
      os.system('python analyze:miniShip.py -f ship-ubuntu-1710-32_miniShip_1/'+x+' &')

h = {}

parser = ArgumentParser()
parser.add_argument("-f", "--file", dest="inputFile", help="input file", default=False)
acc = [100.,100.]

options = parser.parse_args()
if options.inputFile.find('histo')<0:
   f = ROOT.TFile(options.inputFile)
   pos = ROOT.TVector3()
   mom = ROOT.TVector3()
   omom = ROOT.TVector3()
   ut.bookHist(h,'scaler','scaler',10,0.5,10.5)
   fH = f.Get('FileHeader')
   tmp = fH.GetTitle().split(' ')
   h['scaler'].SetBinContent(1,float(tmp[2]))
   h['scaler'].SetBinContent(2,float(tmp[4].split('=')[1]))
   for sTree in f.cbmsim:
      for v in sTree.vetoPoint:
          pid = v.PdgCode()
          hpid = 'p_'+str(pid)
          if not h.has_key(hpid):
               pname = hpid
               if PDG.GetParticle(pid): pname = PDG.GetParticle(pid).GetName()
               ut.bookHist(h,hpid,pname+';[GeV/c]',1000,0.,10.)
               ut.bookHist(h,'b'+hpid,pname+';[GeV/c]',1000,0.,10.)
               for l in ['1','2']:
                 ut.bookHist(h,'inAcc'+l+hpid,pname+';[GeV/c]',1000,0.,10.)
                 ut.bookHist(h,'binAcc'+l+hpid,pname+';[GeV/c]',1000,0.,10.)
                 ut.bookHist(h,'inAccPz'+l+hpid,pname+';[GeV/c]',1000,-3.,3.)
                 ut.bookHist(h,'xy'+l+hpid,pname+';X  [cm];Y  [cm]',100,-1*acc[0],acc[0],100,-1*acc[1],acc[1])
               ut.bookHist(h,'bxy'+hpid,'backsplash '+pname+';X  [cm];Y  [cm]',100,-1*acc[0],acc[0],100,-1*acc[1],acc[1])
               ut.bookHist(h,'vrz'+hpid,pname+';R  [cm];Z  [cm]',100,0,1.5*acc[0],3000,-100.,200.)
               ut.bookHist(h,'orz'+hpid,pname+';R  [cm];Z  [cm]',100,0,1.5*acc[0],3000,-100.,200.)
               ut.bookHist(h,'oorz'+hpid,pname+';R  [cm];Z  [cm]',100,0,1.5*acc[0],3000,-100.,200.)
               ut.bookHist(h,'a'+hpid,pname,100,0.9,1.)
          v.Momentum(mom)
          v.Momentum(pos)
          m = sTree.MCTrack[v.GetTrackID()]
          backsplash = False
          if m.GetStartZ()>v.GetZ(): backsplash = True
          if not backsplash: 
                rc = h[hpid].Fill(mom.Mag())
                rc = h['xy1'+hpid].Fill(v.GetX(),v.GetY())
          else: 
                rc = h['b'+hpid].Fill(mom.Mag())
                rc = h['bxy1'+hpid].Fill(v.GetX(),v.GetY())
          if ( abs(v.GetX())<acc[0] and abs(v.GetY())<acc[1] ):
             if backsplash:   rc = h['binAcc1'+hpid].Fill(mom.Mag())
             else:            rc = h['inAcc1'+hpid].Fill(mom.Mag())
             rc = h['inAcc1Pz'+hpid].Fill(mom.Z())
             m.GetMomentum(omom)
             ms = mom.Dot(omom)/(mom.Mag()*omom.Mag())
             rc = h['a'+hpid].Fill(ms)
             rc = h['orz'+hpid].Fill(ROOT.TMath.Sqrt(m.GetStartX()**2+m.GetStartY()**2),m.GetStartZ() )
             rc = h['vrz'+hpid].Fill(ROOT.TMath.Sqrt(v.GetX()**2+v.GetY()**2),v.GetZ())
             gm = sTree.MCTrack[m.GetMotherId()]
             rc = h['oorz'+hpid].Fill(ROOT.TMath.Sqrt(gm.GetStartX()**2+gm.GetStartY()**2),gm.GetStartZ() )
          # extrapolate to end of decay volume +5m
          lam = 5.*um/mom.Z()
          posB = pos+lam*mom
          rc = h['xy2'+hpid].Fill(posB.X(),posB.Y())
          if ( abs(posB.X())<acc[0] and abs(posB.Y())<acc[1] ):
             rc = h['inAcc2'+hpid].Fill(mom.Mag())
             rc = h['inAcc2Pz'+hpid].Fill(mom.Z())
   ut.writeHists(h,options.inputFile.replace('pythia8','histo-pythia8'))
   print "finished with "+options.inputFile
   sys.exit()
h = {}
ut.readHists(h,options.inputFile)
pot = 50000
if h.has_key('scaler'):  pot = h['scaler'].GetBinContent(1)
particles = {}
meanMom   = {}
for p in h:
  if not p.find('p')==0: continue
  particles[p]=h[p].GetEntries()
  meanMom[p]=[h[p].GetTitle(),h[p].GetMean(),h['inAcc1'+p].GetEntries(),h['inAcc1'+p].GetMean(),h['inAcc2'+p].GetEntries(),h['inAcc2'+p].GetMean()]

sorted_pnames = sorted(particles.items(), key=operator.itemgetter(1))

for x in  sorted_pnames:
   pname = meanMom[x[0]][0]
   mean1 = meanMom[x[0]][1]
   mean2 = meanMom[x[0]][3]
   mean3 = meanMom[x[0]][5]
   entries = x[1]
   inAcc1 = meanMom[x[0]][2]
   inAcc2 = meanMom[x[0]][4]
   if entries < 2: sn1 = "<%3.1E"%(2./pot)
   else: sn1 = " %3.1E"%(float(entries)/pot)
   if inAcc1 < 2: sn2 = "<%3.1E"%(2./pot)
   else: sn2 = " %3.1E"%(float(inAcc1)/pot)
   if inAcc2 < 2: sn3 = "<%3.1E"%(2./pot)
   else: sn3 = " %3.1E"%(float(inAcc2)/pot)
   print "%20s %7.2F MeV/c %s | %7.2F MeV/c %s  | %7.2F MeV/c %s /event"%(pname,mean1*1000.,sn1,mean2*1000.,sn2,mean3*1000.,sn3)

def addTitles():
 for x in h:
   if x.find('orz')==0: 
       h[x].GetYaxis().SetTitle("Z  [cm]")
       h[x].GetXaxis().SetTitle("R  [cm]")
def drawPath(v,proj='x',x=''):
    m = v.GetTrackID()
    t = sTree.MCTrack[m]
    g = 'g'+str(m)+x
    h[g]=ROOT.TGraph()
    if proj=='x': h[g].SetPoint(0,v.GetZ(),v.GetX())
    else:        h[g].SetPoint(0,v.GetZ(),v.GetY())
    n=0
    while m>0:
       n+=1
       if proj=='x': h[g].SetPoint(n,t.GetStartZ(),t.GetStartX())
       else: h[g].SetPoint(n,t.GetStartZ(),t.GetStartY())
       m = t.GetMotherId()
       t = sTree.MCTrack[m]
    h[g].Draw()
def nuclearProperties():
    D = open('/mnt/hgfs/microDisk/summary_prop_table.dat.txt')
    first = True
    for l in D.readlines():
        z = l.replace('\n','').split(' ')
        arg = []
        for x in z:
            if x=='':continue
            arg.append(x)
        if first:
          txt = ""
          for x in arg: txt+=x+':'
          N = ROOT.TNtuple("N","nuclearProperties",txt[:len(txt)-2])
          first = False
        else:
          rc =  N.Fill(float(arg[0]),float(arg[1]),float(arg[2]),float(arg[3]),float(arg[4]),float(arg[5]),float(arg[6]),float(arg[7]),float(arg[8]))
    N.Draw('Z','density>0.01&&lam_I/density<10')
    N.Draw('lam_I/density:A','density>0.01&&lam_I/density<30','box')
    N.Draw('Xo/density:A','density>0.01&&Xo/density<2','box')
