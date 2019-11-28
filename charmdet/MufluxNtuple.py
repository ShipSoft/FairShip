import ROOT,os,time,operator,subprocess
import rootUtils as ut
from argparse import ArgumentParser
PDG = ROOT.TDatabasePDG.Instance()
cuts = {}
cuts['muTrackMatchX']= 5.
cuts['muTrackMatchY']= 10.
zTarget = -370.       # start of target: -394.328, mean z for mu from Jpsi in MC = -375cm, for all muons: -353cm

cuts['zRPC1']  = 878.826706
cuts['xLRPC1'] =-97.69875
cuts['xRRPC1'] = 97.69875
cuts['yBRPC1'] =-41.46045
cuts['yTRPC1'] = 80.26905

sqrt2 = ROOT.TMath.Sqrt(2.)

Debug = False

host = os.uname()[1]
if host=="ubuntu":
    gPath = "/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-32/"
elif host=='ship-ubuntu-1710-32':
    gPath = "/home/truf/muflux/"
else:
    gPath = "/home/truf/ship-ubuntu-1710-32/"

hData   = {}
hMC     = {}
h0      = {}
h = {}

parser = ArgumentParser()
parser.add_argument("-f", "--files", dest="listOfFiles", help="list of files comma separated", default=False)
parser.add_argument("-d", "--dir", dest="directory", help="directory", default=False)
parser.add_argument("-c", "--cmd", dest="command", help="command to execute", default="")
parser.add_argument("-p", "--path", dest="path", help="path to ntuple", default="")
parser.add_argument("-t", "--type", dest="MCType", help="version of MC", default="final") # other versions: "0", "multHits", "noDeadChannels", "withDeadChannels"
parser.add_argument("-A", "--with1GeV",  dest="with1GeV", help="1GeV MC", default="True")
parser.add_argument("-C", "--withcharm", dest="withCharm", help="charm 1GeV MC", default="True")
parser.add_argument("-B", "--with10GeV", dest="with10GeV", help="10GeV MC", default="True")
parser.add_argument("-D", "--withData",  dest="withData", help="use default data set", default="True")
parser.add_argument("-x", dest="ncpus", help="number of parallel jobs", default=False)
parser.add_argument("-s", dest="nseq", help="sequence of parallel job", default=0)
parser.add_argument("-r", dest="refit", help="use refitted ntuples", required=False, action="store_true")

options = parser.parse_args()

MCType    =  options.MCType
with1GeV  =  options.with1GeV  == "True"
withCharm =  options.withCharm == "True"
with10GeV =  options.with10GeV == "True"
withData  =  options.withData  == "True"
if options.path != "": gPath = options.path+'/'
fdir = options.directory

Nfiles = 0
if not fdir:
    Nfiles = 2000
    fdir   = "/eos/experiment/ship/user/truf/muflux-reco/RUN_8000_2403"
if not options.listOfFiles:
    sTreeData = ROOT.TChain('tmuflux')
    if withData:
     path = gPath + fdir
     countFiles=[]
     if fdir.find('eos')<0:
        for x in os.listdir(path):
            if x.find('ntuple-SPILL')<0: continue
            if x.find('refit')<0 and options.refit or x.find('refit')>0 and not options.refit: continue
            countFiles.append(path+'/'+x)
     else:
        temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+fdir,shell=True)
        for x in temp.split('\n'):
            if x.find('ntuple-SPILL')<0: continue
            if x.find('refit')<0 and options.refit or x.find('refit')>0 and not options.refit: continue
            countFiles.append(os.environ["EOSSHIP"]+"/"+x)
     for x in countFiles:
        tmp = ROOT.TFile.Open(x)
        if not tmp.Get('tmuflux'):
           print "Problematic file:",x
           continue
        sTreeData.Add(x)
        Nfiles-=1
        if Nfiles==0: break

    sTreeMC = ROOT.TChain('tmuflux')

    if with1GeV:
        path = os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/1GeV-"+MCType+"/pythia8_Geant4_1.0_cXXXX_mu/"
        for k in range(0,20000,1000):
            for m in range(5):
                fname = path.replace('XXXX',str(k))+"ntuple-ship.conical.MuonBack-TGeant4_dig_RT-"+str(m)+".root"
                try:
                    test = ROOT.TFile.Open(fname)
                    if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
                except:
                    print "file not found",fname
                    continue
    if withCharm:
        fdir = fdir+'-charm'
        path = os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/1GeV-"+MCType+"/pythia8_Geant4_charm_0-19_1.0_mu/"
        for m in range(5):
            fname = path+"ntuple-ship.conical.MuonBack-TGeant4_dig_RT-"+str(m)+".root"
            try:
                test = ROOT.TFile.Open(fname)
                if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
            except:
                print "file not found",fname
                continue

    if with10GeV:
        path = os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/10GeV-"+MCType+"/pythia8_Geant4_10.0_withCharmandBeautyXXXX_mu/"
        for k in range(0,67000,1000):
            for m in range(10):
                fname = path.replace('XXXX',str(k))+"ntuple-ship.conical.MuonBack-TGeant4_dig_RT-"+str(m)+".root"
                try:
                    test = ROOT.TFile.Open(fname)
                    if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
                except:
                    print "file not found",fname
                    continue

# small problem here when merging 1GeV and 10GeV, due to different p cutoff, px and pt cannot be used directly. 

# temp hack
#nfile = "/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-48/simulation1GeV-withDeadChannels/pythia8_Geant4_1.0_c3000_mu/ship.conical.MuonBack-TGeant4_dig_RT-0.root"
#sTreeMC.Add("ntuple-ship.conical.MuonBack-TGeant4_dig_RT-0.root")
    case = {'MC':[sTreeMC,hMC,ROOT.kRed,'hist same'],'Data':[sTreeData,hData,ROOT.kBlue,'hist']}

s_SQRT2i = 1./ROOT.TMath.Sqrt( 2.0 )
sqrt2pi  = ROOT.TMath.Sqrt( 2*ROOT.TMath.Pi() )
cb=ROOT.TF1("cb","crystalball",0,6.)
def TwoCrystalBall(x,par):
   bw = par[0] # should be fixed
   cb.SetParameters(par[1]*bw,par[2],par[3],par[4],par[5])
   highMass = cb.Eval(x[0])
   cb.SetParameters(par[6]*bw,par[7],par[8],par[9],par[10])
   lowMass = cb.Eval(x[0])
   Psi2s = 0
   if abs(par[13])>0:
     cb.SetParameters(par[13]*bw,3.6871+par[2]- 3.0969,par[3],par[4],par[5])
     Psi2s = cb.Eval(x[0])
   Y = highMass + lowMass + par[11] + par[12]*x[0] + Psi2s
   return Y
def CrystalBall(x,par):
   bw = par[0] # should be fixed
   cb.SetParameters(par[1]*bw,par[2],par[3],par[4],par[5])
   highMass = cb.Eval(x[0])
   lowMass = par[6]*bw/(abs(par[8])*sqrt2pi)*ROOT.TMath.Exp(-0.5*( (x[0]-par[7])/par[8])**2)
   Y = highMass + lowMass + par[9] + par[10]*x[0]
   return Y

def IP(OnlyDraw = False):
    if not OnlyDraw:
        for c in case:
            sTree = case[c][0]
            h = case[c][1]
            ut.bookHist(h,'IP','transv distance to z-axis at target',100,0.,250.)
            ut.bookHist(h,'IPx','x distance to z-axis at target',100,-100.,100.)
            ut.bookHist(h,'IPmu','transv distance to z-axis at target',100,0.,250.)
            ut.bookHist(h,'IPxmu','x distance to z-axis at target',100,-100.,100.)
            ut.bookHist(h,'IPxy','xy distance to z-axis at target',100,-100.,100.,100,-100.,100.)
            for n in range(sTree.GetEntries()):
                rc = sTree.GetEvent(n)
                for t in range(sTree.nTr):
                    if sTree.GoodTrack[t]<0: continue
                    P = ROOT.TMath.Sqrt(sTree.Px[t]**2+sTree.Py[t]**2+sTree.Pz[t]**2)
                    if P<5. : continue
                    l = (sTree.z[t] - zTarget)/sTree.Pz[t]
                    x = sTree.x[t]+l*sTree.Px[t]
                    y = sTree.y[t]+l*sTree.Py[t]
                    r = ROOT.TMath.Sqrt(x*x+y*y)
                    rc = h['IP'].Fill(r)
                    rc = h['IPx'].Fill(x)
                    rc = h['IPxy'].Fill(x,y)
                    if abs(sTree.Delx[t])<cuts['muTrackMatchX']:
                        rc = h['IPxmu'].Fill(x)
                    if abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']:
                        rc = h['IPmu'].Fill(r)
    for proj in ['','x']:
        ut.bookCanvas(hData,'TIP'+proj,'IP'+proj,1600,1200,2,2)
        ic = 1
        for mu in ['','mu']:
            tc = hData['TIP'+proj].cd(ic)
            tc.SetLogy()
            hData['MCIP'+proj+mu]=hMC['IP'+proj+mu].Clone('MCIP'+proj+mu)
            hData['MCIP'+proj+mu].Scale( hData['IP'+proj+mu].GetEntries()/hMC['IP'+proj+mu].GetEntries())
            for k in [0,2]:
                if proj=='x':      hData['leg'+proj+str(ic+k)]=ROOT.TLegend(0.33,0.17,0.67,0.24)
                else:             hData['leg'+proj+str(ic+k)]=ROOT.TLegend(0.43,0.77,0.88,0.88)
            for c in case:
                x = ''
                if c=='MC': x=c
                for k in [0,2]:
                    tc = hData['TIP'+proj].cd(ic+k)
                    hData[x+'IP'+proj+mu].SetLineColor(case[c][2])
                    hData[x+'IP'+proj+mu].Draw(case[c][3])
                    hData[x+'IP'+proj+mu].SetLineColor(case[c][2])
                    hData[x+'IP'+proj+mu].Draw(case[c][3])
                    mean = hData[x+'IP'+proj+mu].GetMean()
                    rms = hData[x+'IP'+proj+mu].GetRMS()
                    hData[x+'IP'+proj+mu].SetStats(0)
                    txt = "%s  Mean=%5.2F  Std Dev=%5.2F"%(c,mean,rms)
                    rc = hData['leg'+proj+str(ic+k)].AddEntry(hData[x+'IP'+proj+mu],txt,'PL')
            for k in [0,2]:
                tc = hData['TIP'+proj].cd(ic+k)
                hData['leg'+proj+str(ic+k)].Draw()
            ic+=1
        hData['TIP'+proj].Print('IP'+proj+'.png')
        hData['TIP'+proj].Print('IP'+proj+'.pdf')

def RPCextrap(OnlyDraw = False,pxMin=3.,pMin=10.,station1Occ=100,station1OccLow=0):
    if not OnlyDraw:
        for c in case:
            sTree = case[c][0]
            h = case[c][1]
            for l in range(1,7):
                if l<5:  txt ="x station "+str(l)+" Occupancy"
                if l==5: txt ="u station 1 Occupancy"
                if l==6: txt ="v station 2 Occupancy"
                ut.bookHist(h,'stationOcc'+str(l),txt,50,-0.5,49.5)
            ut.bookHist(h,'upStreamOcc',"station 1&2",200,-0.5,199.5)
            ut.bookHist(h,'upStreamOccwithTrack',"station 1&2",200,-0.5,199.5)
            ut.bookHist(h,'upStreamOccMuonTagged',"station 1&2",200,-0.5,199.5)
            ut.bookHist(h,'xy',   'xy at RPC',100,-150.,150.,100,-150.,150.)
            ut.bookHist(h,'xyIn', 'xy at RPC in acceptance',100,-150.,150.,100,-150.,150.)
            ut.bookHist(h,'xyInX','xy at RPC in acceptance',100,-150.,150.,100,-150.,150.)
            ut.bookHist(h,'xyTagged', 'xy at RPC for muons',100,-150.,150.,100,-150.,150.)
            ut.bookHist(h,'xyTaggedX','xy at RPC for muons',100,-150.,150.,100,-150.,150.)
            for x in ['-Tagged','-nonTagged']:
                ut.bookHist(h,'chi2Dof'+x,'chi2 per DoF',100,0.,10.)
                ut.bookHist(h,'p/pt'+x,'momentum vs Pt (GeV);p [GeV/c]; p_{T} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,'pz/Abspx'+x,'Pz vs Px (GeV);p [GeV/c]; p_{X} [GeV/c]',500,0.,500.,100,0.,10.)
            for n in range(sTree.GetEntries()):
                rc = sTree.GetEvent(n)
                upStreamOcc = sTree.stationOcc[1]+sTree.stationOcc[5]+sTree.stationOcc[2]+sTree.stationOcc[6]
                rc = h['upStreamOcc'].Fill(upStreamOcc)
                if sTree.nTr>0:
                    for l in range(1,7):
                        rc = h['stationOcc'+str(l)].Fill(sTree.stationOcc[l])
                        if sTree.stationOcc[l]>40: print l,sTree.stationOcc[l],sTree.evtnr,sTree.spillnrA,sTree.spillnrB,sTree.spillnrC ,sTree.GetCurrentFile().GetName()
                    rc = h['upStreamOccwithTrack'].Fill(upStreamOcc)
                if sTree.stationOcc[1] > station1Occ or sTree.stationOcc[1] < station1OccLow: continue
                for t in range(sTree.nTr):
                    if sTree.GoodTrack[t]<0: continue
                    Pvec = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
                    P = Pvec.Mag()
                    if abs(sTree.Px[t])<pxMin : continue
                    if P<pMin                 : continue
                    rc = h['xy'].Fill(sTree.RPCx[t],sTree.RPCy[t])
                    if sTree.RPCx[t]>cuts['xLRPC1'] and sTree.RPCx[t]<cuts['xRRPC1']: 
                        rc = h['xyInX'].Fill(sTree.RPCx[t],sTree.RPCy[t])
                        if abs(sTree.Delx[t])<cuts['muTrackMatchX']:
                            rc = h['xyTaggedX'].Fill(sTree.RPCx[t],sTree.RPCy[t])
                            rc = h['pz/Abspx-Tagged'].Fill(Pvec[2],Pvec[0])
                        else:
                            rc = h['pz/Abspx-nonTagged'].Fill(Pvec[2],Pvec[0])
                        if sTree.RPCy[t]>cuts['yBRPC1'] and sTree.RPCy[t]<cuts['yTRPC1']:
                            rc = h['xyIn'].Fill(sTree.RPCx[t],sTree.RPCy[t])
                        if abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']:
                            rc = h['xyTagged'].Fill(sTree.RPCx[t],sTree.RPCy[t])
                            rc = h['chi2Dof-Tagged'].Fill(sTree.Chi2[t])
                            rc = h['p/pt-Tagged'].Fill(P,Pvec.Pt())
                            rc = h['upStreamOccMuonTagged']
                        else:
                            rc = h['chi2Dof-nonTagged'].Fill(sTree.Chi2[t])
                            rc = h['p/pt-nonTagged'].Fill(P,Pvec.Pt())
    effDataIn = hData['xyTagged'].GetEntries()/hData['xyIn'].GetEntries()*100.
    effMCIn   = hMC['xyTagged'].GetEntries()/hMC['xyIn'].GetEntries()*100.
    effData = hData['xyTagged'].GetEntries()/hData['xy'].GetEntries()*100.
    effMC   = hMC['xyTagged'].GetEntries()/hMC['xy'].GetEntries()*100.
    print "eff xy data: %5.2F (%5.2F)  MC: %5.2F (%5.2F)"%(effDataIn,effData,effMCIn,effMC)
    effDataIn = hData['xyTaggedX'].GetEntries()/hData['xyInX'].GetEntries()*100.
    effMCIn   = hMC['xyTaggedX'].GetEntries()/hMC['xyInX'].GetEntries()*100.
    effData = hData['xyTaggedX'].GetEntries()/hData['xy'].GetEntries()*100.
    effMC   = hMC['xyTaggedX'].GetEntries()/hMC['xy'].GetEntries()*100.
    print "eff x  data: %5.2F (%5.2F)  MC: %5.2F (%5.2F)"%(effDataIn,effData,effMCIn,effMC)
    keys = ['upStreamOcc','upStreamOccwithTrack','upStreamOccMuonTagged']
    for l in range(1,7):
        keys.append('stationOcc'+str(l))
    for key in keys:
        hData['MC'+key] = hMC[key].Clone('MC'+key)
        hData['MC'+key].SetLineColor(ROOT.kRed)
        if key.find('upStreamOcc')==0:
            norm = (hMC[key].GetBinContent(15))/(hData[key].GetBinContent(15))
        else:  
            norm = (hMC[key].GetBinContent(4)+hMC[key].GetBinContent(5))/(hData[key].GetBinContent(4)+hData[key].GetBinContent(5))
        hData['MC'+key].Scale(1./norm)

def MCRPCextrap(OnlyDraw = False):
    if not OnlyDraw:
        c = 'MC'
        sTree = case[c][0]
        h = case[c][1]
        ut.bookHist(h,'P','true momentum muReconstructible;[GeV/c]',400,0.,400.)
        ut.bookHist(h,'Pt','true momentum muReconstructible;[GeV/c]',80,0.,4.)
        ut.bookHist(h,'Px','true momentum muReconstructible;[GeV/c]',80,0.,4.)
        ut.bookHist(h,'Preco1','true momentum reco track matched;[GeV/c]',400,0.,400.)
        ut.bookHist(h,'Ptreco1','true momentum reco track matched;[GeV/c]',100,0.,10.)
        ut.bookHist(h,'Pxreco1','true momentum reco track matched;[GeV/c]',100,0.,10.)
        ut.bookHist(h,'Preco2','true momentum reco track matched, good track p/pt;[GeV/c]',400,0.,400.)
        ut.bookHist(h,'Preco3','true momentum reco track matched, good track pz/px;[GeV/c]',400,0.,400.)
        for x in ['','mu']:
            ut.bookHist(h,'delP'+x,'true momentum - reco vs true P;[GeV/c]',100,-10.,10.,80,0.,400.)
            ut.bookHist(h,'delPx'+x,'true Px - reco vs true P;[GeV/c]',100,-2.,2.,80,0.,400.)
            ut.bookHist(h,'delPt'+x,'true Pt - reco vs true P;[GeV/c]',100,-2.,2.,80,0.,400.)
        for n in range(sTree.GetEntries()):
            rc = sTree.GetEvent(n)
            if sTree.MCRecoDT.size() != 1: continue # look at simple events for the moment 
            for m in sTree.MCRecoRPC:
                i = -1
                for d in sTree.MCRecoDT:
                    i+=1
                    if m!=d: continue  # require same MCTrack
                    P  = ROOT.TVector3(sTree.MCRecoDTpx[i],sTree.MCRecoDTpy[i],sTree.MCRecoDTpz[i])
                    rc = h['P'].Fill(P.Mag())
                    rc = h['Px'].Fill(abs(P.X()))
                    rc = h['Pt'].Fill(P.Pt())
                    for t in range(sTree.nTr):
                        if sTree.nTr>1: continue
                        Preco  = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
                        delP = P.Mag()-Preco.Mag()
                        delPx = P.X()-Preco.X()
                        delPt = P.Pt()-Preco.Pt()
                        rc = h['delP'].Fill(delP,P.Mag())
                        rc = h['delPx'].Fill(delPx,P.Mag())
                        rc = h['delPt'].Fill(delPt,P.Mag())
                        if abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']:
                            rc = h['Preco1'].Fill(P.Mag())
                            rc = h['Pxreco1'].Fill(abs(P.X()))
                            rc = h['Ptreco1'].Fill(P.Pt())
                            rc = h['delPmu'].Fill(delP,P.Mag())
                            rc = h['delPxmu'].Fill(delPx,P.Mag())
                            rc = h['delPtmu'].Fill(delPt,P.Mag())
        for x in ['P','Pt','Px']:
            h['tagEff'+x]=ROOT.TEfficiency(h[x+'reco1'],h[x])

def makeProjectionRMS(h,hname,proj):
    pname = hname+proj
    if not proj.find('x')<0: h[pname] = h[hname].ProjectionX(pname)
    else:                    h[pname] = h[hname].ProjectionY(pname)
    for n in range(1,h[pname].GetNbinsX()+1):
        if not proj.find('x')<0: temp = h[hname].ProjectionY('p'+str(n),n,n)
        else:                    temp = h[hname].ProjectionX('p'+str(n),n,n)
        RMS = temp.GetRMS()
        h[pname].SetBinContent(n,RMS)

def clones(OnlyDraw = False,noClones=False):
    if not OnlyDraw:
        for c in case:
            sTree = case[c][0]
            h = case[c][1]
            ut.bookHist(h,'cos alpha','cosine of angle between two tracks;cos[#alpha]',10000,0.95,1.01)
            for n in range(sTree.GetEntries()):
                rc = sTree.GetEvent(n)
                for a in range(sTree.nTr-1):
                    if sTree.GoodTrack[a]<0: continue
                    if noClones and sTree.GoodTrack[a]>1000: continue
                    A = ROOT.TVector3(sTree.Px[a],sTree.Py[a],sTree.Pz[a])
                    for b in range(a,sTree.nTr):
                        if sTree.GoodTrack[b]<0: continue
                        if noClones and sTree.GoodTrack[b]>1000: continue
                        if sTree.Sign[b]*sTree.Sign[a]>0: continue
                        B = ROOT.TVector3(sTree.Px[b],sTree.Py[b],sTree.Pz[b])
                        rc = h['cos alpha'].Fill(A.Dot(B)/(A.Mag()*B.Mag()))
    hData['cos alpha'].GetXaxis().SetRangeUser(0.999,1.0001)
    hMC['cos alpha'].SetLineColor(ROOT.kRed)
    hData['MCcos alpha'] = hMC['cos alpha'].Clone('MCcos alpha')
    hData['MCcos alpha'].Scale(hData['cos alpha'].GetEntries()/hMC['cos alpha'].GetEntries())
    hData['MCcos alpha'].SetStats(0)
    hData['cos alpha'].SetStats(0)
    ut.bookCanvas(hData,'clones','Clones',1200,900,1,1)
    hData['cos alpha'].Draw()
    hData['MCcos alpha'].Draw('same')
    hData['leg']=ROOT.TLegend(0.24,0.50,0.54,0.61)
    rc = hData['leg'].AddEntry(hData["cos alpha"],"Data",'PL')
    rc = hData['leg'].AddEntry(hData["MCcos alpha"],"MC",'PL')
    hData['leg'].Draw()
    lmax = hData['cos alpha'].GetMaximum()
    h['lcut'] =  ROOT.TArrow(0.99995,0.,0.99995,lmax*0.2,0.05,"<")
    h['lcut'].SetLineColor(ROOT.kMagenta)
    h['lcut'].SetLineWidth(2)
    h['lcut'].Draw()
    hData['clones'].Print('MC-Comparison-Clones.pdf') 
    hData['clones'].Print('MC-Comparison-Clones.png')
    ff = ROOT.TFile('Clones.root','recreate')
    hData['clones'].Write('Clones.root')

def tails(OnlyDraw = False):
    if not OnlyDraw:
        for c in case:
            sTree = case[c][0]
            h = case[c][1]
            ut.bookHist(h,'momentum','momentum',1000,0.0,1000.)
            for n in range(sTree.GetEntries()):
                rc = sTree.GetEvent(n)
                for t in range(sTree.nTr):
                    if sTree.GoodTrack[t]<0: continue
                    P = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
                    rc = h['momentum'].Fill(P.Mag())
        hData['MCmomentum'] = hMC['momentum'].Clone('MCmomentum')
        norm = hData['momentum'].Integral(5,100)/hMC['momentum'].Integral(5,100)
        hData['MCmomentum'].SetLineColor(ROOT.kRed)
        hData['MCmomentum'].Scale(norm)

deadChannels4MC = [10112001,11112012,20112003,30002042,30012026,30102021,30102025,30112013,30112018,40012014]

def reconstructible(OnlyDraw = False):
    if not OnlyDraw:
        #for c in case:
        c = 'MC'
        sTree = case[c][0]
        h = case[c][1]
        ut.bookHist(h,'reconstructibleP',"reconstructible P",400,0.0,400.)
        ut.bookHist(h,'reconstructedP',"reconstructed P",400,0.0,400.)
        for x in ['','_mu']:
            ut.bookHist(h,'delPzR'+x,"reconstructed Pz - true / true",1000,-5.,5.)
            ut.bookHist(h,'delPtR'+x,"reconstructed Pt - true / true",1000,-5.,5.)
            ut.bookHist(h,'delPz'+x,"reconstructed Pz - true ",1000,-50.,50.)
            ut.bookHist(h,'delPx'+x,"reconstructed Px - true ",1000,-1.,1.)
            ut.bookHist(h,'delPt'+x,"reconstructed Pt - true ",1000,-1.,1.)
        ut.bookHist(h,'upStreamOcc',"station 1&2",200,-0.5,199.5)
        ut.bookHist(h,'upStreamOcc-nonReco',"station 1&2",200,-0.5,199.5)
        ut.bookHist(h,'upStreamOcc-badRecoP',"station 1&2",200,-0.5,199.5)
        ut.bookHist(h,'upStreamOcc-badRecoPx',"station 1&2",200,-0.5,199.5)
        ut.bookHist(h,'upStreamOcc-reconstructible',"station 1&2",200,-0.5,199.5)
        ut.bookHist(h,'stationOcc1x1u',"station 1",50,-0.5,49.5,50,-0.5,49.5)
        ut.bookHist(h,'stationOcc2x2v',"station 2",50,-0.5,49.5,50,-0.5,49.5)
        for n in range(sTree.GetEntries()):
            rc = sTree.GetEvent(n)
            rc = h['stationOcc1x1u'].Fill(sTree.stationOcc[1],sTree.stationOcc[5])
            rc = h['stationOcc2x2v'].Fill(sTree.stationOcc[2],sTree.stationOcc[6])
            upStreamOcc = sTree.stationOcc[1]+sTree.stationOcc[5]+sTree.stationOcc[2]+sTree.stationOcc[6]
            rc = h['upStreamOcc'].Fill(upStreamOcc)
            if sTree.MCRecoDT.size()==1:
                rc = h['upStreamOcc-reconstructible'].Fill(upStreamOcc)
                m = 0
                P  = ROOT.TVector3(sTree.MCRecoDTpx[m],sTree.MCRecoDTpy[m],sTree.MCRecoDTpz[m])
                rc = h['reconstructibleP'].Fill(P.Mag())
                if sTree.nTr==1: 
                    rc = h['reconstructedP'].Fill(P.Mag())
                    Preco  = ROOT.TVector3(sTree.Px[0],sTree.Py[0],sTree.Pz[0])
                    delPz  = (sTree.Pz[0]-sTree.MCRecoDTpz[0])
                    delPx = (sTree.Px[0]-sTree.MCRecoDTpx[0])
                    delPzR = (sTree.Pz[0]-sTree.MCRecoDTpz[0])/sTree.MCRecoDTpz[0]
                    rc = h['delPz'].Fill(delPz)
                    rc = h['delPx'].Fill(delPx)
                    rc = h['delPzR'].Fill(delPzR)
                    delPt  = Preco.Pt()-P.Pt()
                    delPtR = (Preco.Pt()-P.Pt()/P.Pt())
                    rc = h['delPt'].Fill(delPt)
                    rc = h['delPtR'].Fill(delPtR)
                    if abs(sTree.Delx[0])<cuts['muTrackMatchX'] and abs(sTree.Dely[0])<cuts['muTrackMatchY']:
                        x='_mu'
                        rc = h['delPz'+x].Fill(delPz)
                        rc = h['delPx'+x].Fill(delPx)
                        rc = h['delPzR'+x].Fill(delPzR)
                        rc = h['delPt'+x].Fill(delPt)
                        rc = h['delPtR'+x].Fill(delPtR)
                    if abs(delPz)>10.: rc = h['upStreamOcc-badRecoP'].Fill(upStreamOcc)
                    if abs(delPx)>2.: rc = h['upStreamOcc-badRecoPx'].Fill(upStreamOcc)
#        if abs(delPt)>2. :                                        print "bad reco pt",n,upStreamOcc,sTree.MCRecoDT.size(),delPt,P.Pt()
#        if abs( abs(sTree.Px[0])-abs(sTree.MCRecoDTpx[0]))>2. :   print "bad reco px",n,upStreamOcc,sTree.MCRecoDT.size(),delPx,sTree.MCRecoDTpx[0]
                if sTree.nTr <1:
                    rc = h['upStreamOcc-nonReco'].Fill(upStreamOcc)
                    # print "non reco",n,upStreamOcc,sTree.MCRecoDT.size(),sTree.MCRecoDTpx[0],sTree.MCRecoDTpy[0],sTree.MCRecoDTpz[0]
        h['ineff-upStreamOcc-reconstructible']=ROOT.TEfficiency(h['upStreamOcc-nonReco'],h['upStreamOcc-reconstructible'])
        h['effP']=ROOT.TEfficiency(h['reconstructedP'],h['reconstructibleP'])
from array import array
def RecoEffFunOfOcc(OnlyDraw = False,Nevents = -1):
    pMin = 5.
    if not OnlyDraw:
        c = 'Data'
        sTree = case[c][0]
        h = case[c][1]
        if Nevents<0: Nevents=sTree.GetEntries()
        ut.bookHist(h,'Occ','N',50,0.,200.)
        ut.bookHist(h,'OccAllEvents','N',50,0.,200.)
        for n in range(Nevents):
            rc = sTree.GetEvent(n)
            upStreamOcc = sTree.stationOcc[1]+sTree.stationOcc[5]+sTree.stationOcc[2]+sTree.stationOcc[6]
            if sTree.nTr>0: rc = h['OccAllEvents'].Fill(upStreamOcc)
            for t in range(sTree.nTr):
                if sTree.GoodTrack[t]<0: continue
                Pvec = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
                P = Pvec.Mag()
                if P<pMin                 : continue
                if abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']:
                    rc = h['Occ'].Fill(upStreamOcc)
        ut.writeHists(h,'histos-DataOcc.root')
        c = 'MC'
        sTree = case[c][0]
        h = case[c][1]
# variable bin size
        paxis = []
        xv = 0.
        for x in range(100): 
            paxis.append(xv)
            xv+=1.
        for x in range(20): 
            paxis.append(xv)
            xv+=5.
        for x in range(5): 
            paxis.append(xv)
            xv+=50.
        dpaxis = array('d',paxis)
        ut.bookHist(h,'Ptrue', 'true momentum muReconstructible;[GeV/c];N',500,0.,500.)
        ut.bookHist(h,'P', 'true momentum muReconstructible;[GeV/c];N',dpaxis,50,0.,200.)
        ut.bookHist(h,'Pz','true momentum muReconstructible;[GeV/c];N',dpaxis,50,0.,200.)
        ut.bookHist(h,'Preco', 'true momentum reconstructed;[GeV/c];N',dpaxis,50,0.,200.)
        ut.bookHist(h,'Pfailed', 'true momentum no reco;[GeV/c];N',dpaxis,50,0.,200.)
        ut.bookHist(h,'Pzreco','true momentum reconstructed;[GeV/c];N',dpaxis,50,0.,200.)
        ut.bookHist(h,'Pt','true momentum muReconstructible;[GeV/c];N',80,0.,4.,50,0.,200.)
        ut.bookHist(h,'Px','true momentum muReconstructible;[GeV/c];N',80,0.,4.,50,0.,200.)
        ut.bookHist(h,'Ptreco','true momentum reconstructed;[GeV/c];N',80,0.,4.,50,0.,200.)
        ut.bookHist(h,'Pxreco','true momentum reconstructed;[GeV/c];N',80,0.,4.,50,0.,200.)
        ut.bookHist(h,'delx/y','delx vs dely;cm;cm',100,0.,20,100,0.,50.)
        ut.bookHist(h,'OccAllEvents','N',50,0.,200.)
        for x in ['','_mu']:
            ut.bookHist(h,'delP'+x,"reconstructed P - true ",1000,-50.,50.)
            ut.bookHist(h,'delPt'+x,"reconstructed Pt - true ",1000,-1.,1.)
            ut.bookHist(h,'delPx'+x,"reconstructed Px - true ",1000,-1.,1.)
        for n in range(sTree.GetEntries()):
            rc = sTree.GetEvent(n)
            upStreamOcc = sTree.stationOcc[1]+sTree.stationOcc[5]+sTree.stationOcc[2]+sTree.stationOcc[6]
            if sTree.nTr>0: rc = h['OccAllEvents'].Fill(upStreamOcc)
            if sTree.MCRecoDT.size() != 1: continue # look at 1 Track events for the moment 
            # require reco RPC tracks, otherwise cannot compare to zero field data which starts with RPC tracks
            if sTree.nRPC%10 == 0 or sTree.nRPC/10 == 0 : continue
            # starting with reconstructible RPC track, check that same MCTrack is reconstructible in DT
            for m in sTree.MCRecoRPC:
                i = -1
                for d in sTree.MCRecoDT:
                    i+=1
                    if m!=d: continue  # require same MCTrack
                    P  = ROOT.TVector3(sTree.MCRecoDTpx[i],sTree.MCRecoDTpy[i],sTree.MCRecoDTpz[i])
                    rc = h['P'].Fill(P.Mag(),upStreamOcc)
                    rc = h['Ptrue'].Fill(P.Mag())
                    rc = h['Px'].Fill(abs(P.X()),upStreamOcc)
                    rc = h['Pz'].Fill(P.Z(),upStreamOcc)
                    rc = h['Pt'].Fill(P.Pt(),upStreamOcc)
                    found = False  # avoid double counting
                    if sTree.nTr<1:
                        rc = h['Pfailed'].Fill(P.Mag(),upStreamOcc)
                        if Debug: print "no reco track  event nr ",n,sTree.GetCurrentFile().GetName(),P.Mag(),upStreamOcc
                    for t in range(sTree.nTr):
                        Preco  = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
                        delP   = P.Mag() - Preco.Mag()
                        delPx  = P.X() -   Preco.X()
                        delPt  = P.Pt() -  Preco.Pt()
                        rc = h['delP'].Fill(delP,P.Mag())
                        rc = h['delPx'].Fill(delPx,P.Mag())
                        rc = h['delPt'].Fill(delPt,P.Mag())
                        rc = h['delx/y'].Fill(sTree.Delx[t],sTree.Dely[t])
                        # if there is no muon track in event, sTree.Delx[t] = 9999. and sTree.Dely[t] = 9999.
                        if Debug and (sTree.Delx[t]>9998 or sTree.Dely[t] > 9998): print "no reco RPC track in RPC reconstructible event" 
                        if abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']:
                            if found: continue
                            rc = h['delP_mu'].Fill(delP,P.Mag())
                            rc = h['delPx_mu'].Fill(delPx,P.Mag())
                            rc = h['delPt_mu'].Fill(delPt,P.Mag())
                            rc = h['Preco'].Fill(P.Mag(),upStreamOcc)
                            rc = h['Pxreco'].Fill(abs(P.X()),upStreamOcc)
                            rc = h['Pzreco'].Fill(P.Z(),upStreamOcc)
                            rc = h['Ptreco'].Fill(P.Pt(),upStreamOcc)
                            found = True
                    if not found and sTree.nTr==1 and Debug:
                        dec = abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']
                        print "event nr ",n,P.Mag(),sTree.nTr,upStreamOcc,abs(sTree.Delx[t]),abs(sTree.Dely[t]),dec
        ut.writeHists(h,'histos-MCRecoEffFunOfOcc'+'-'+fdir+'.root')
        return
    if not hMC.has_key('P'): 
        ut.readHists(hMC,'histos-MCRecoEffFunOfOcc.root')
    if not hData.has_key('Occ'): 
        ut.readHists(hData,'histos-DataOcc.root')
        hData['Occ'].Scale(1./hData['Occ'].GetMaximum())
    # now take occupancy from zero field
    if not hMC.has_key("hDTEff"):
        hMC["hDTEff"] = {}
        hDTEff=hMC["hDTEff"]
        interestingHistos=[]
        for k in range(1,5):
            interestingHistos.append("upStreamOccWithTrack"+str(k))
            interestingHistos.append("upStreamOcc"+str(k))
        ut.readHists(hDTEff,'DTEff.root',interestingHistos)
        hDTEff['upStreamOccWithTrack']=hDTEff['upStreamOccWithTrack1'].Clone('upStreamOccWithTrack')
        hDTEff['upStreamOccWithTrack'].Add(hDTEff['upStreamOccWithTrack2'])
        hDTEff['upStreamOccWithTrack'].Add(hDTEff['upStreamOccWithTrack3'])
        hDTEff['upStreamOccWithTrack'].Add(hDTEff['upStreamOccWithTrack4'])

        hDTEff['upStreamOcc']=hDTEff['upStreamOcc1'].Clone('upStreamOcc')
        hDTEff['upStreamOcc'].Add(hDTEff['upStreamOcc2'])
        hDTEff['upStreamOcc'].Add(hDTEff['upStreamOcc3'])
        hDTEff['upStreamOcc'].Add(hDTEff['upStreamOcc4'])

        hMC['zeroFieldOcc']=hDTEff['upStreamOccWithTrack'].Rebin(4,'zeroFieldOcc')
        hMC['zeroFieldOcc'].Scale(1./hMC['zeroFieldOcc'].GetMaximum())
        hMC['zeroFieldOcc'].SetLineColor(ROOT.kGreen)
        hMC['zeroFieldOcc'].SetMarkerColor(ROOT.kGreen)
        hMC['zeroFieldOcc'].SetMarkerStyle(24)
    h = hMC
    tmp = h['P'].ProjectionY()
    T = ROOT.TLatex()
    T.SetTextColor(ROOT.kMagenta)
    ut.bookCanvas(h,'upStreamOcc','upstream occupancy',900,600,1,1)
    tc = hMC['upStreamOcc'].cd(1)
    tc.SetLogy(1)
    hData['OccAllEvents'].SetTitle('upstream occupancy;Number of hits;arbitrary scale')
    hData['OccAllEvents'].SetStats(0)
    hData['OccAllEvents'].Draw()
    hmax = hData['OccAllEvents'].GetMaximum()
    hMC['OccAllEvents'].SetLineColor(ROOT.kMagenta)
    hMC['OccAllEvents_scaled']=hMC['OccAllEvents'].Clone('OccAllEvents_scaled')
    hMC['OccAllEvents_scaled'].Scale(hmax/hMC['OccAllEvents'].GetMaximum())
    hMC['OccAllEvents_scaled'].SetStats(0)
    hMC['OccAllEvents_scaled'].Draw('same hist')
    h['upStreamOcc'].Print('upstreamOcc.pdf')
    h['upStreamOcc'].Print('upstreamOcc.png')
    variables = ['P','Px','Pz','Pt']
    fun = {}
    for var in variables:
        xmin = tmp.GetBinLowEdge(1)
        xmax = tmp.GetBinLowEdge(tmp.GetNbinsX())+tmp.GetBinWidth(tmp.GetNbinsX())
        ut.bookHist(h,'effFun'+var,'eff as function of occupancy '+var,tmp.GetNbinsX(),xmin,xmax)
        ut.bookCanvas(h,'eff'+var,'Efficiencies '+var,1200,900,5,4)
        if var=='P' or var=='Pz': fun[var] = ROOT.TF1('pol0'+var,'[0]',12.,200.)
        else:                     fun[var] = ROOT.TF1('pol0'+var,'[0]',0.,2.5)
        j=1
        for o in range(1,tmp.GetNbinsX()+1):
            h[var+'eff'+str(o)] =  ROOT.TEfficiency(h[var+'reco'].ProjectionX(var+'reco'+str(o),o,o),h[var].ProjectionX(var+str(o),o,o))
            if j<20:
                tc = h['eff'+var].cd(j)
                j+=1
                h[var+'eff'+str(o)].Draw()
                tc.Update()
                if h[var+'eff'+str(o)].GetTotalHistogram().GetEntries() == 0: continue
                g = h[var+'eff'+str(o)].GetPaintedGraph()
                x = h[var+'eff'+str(o)].GetEfficiency(20) # just to have a decent scale
                g.SetMinimum(x*0.8)
                g.SetMaximum(1.02)
                if var=='P' or var=='Pz':
                    g.GetXaxis().SetRangeUser(0.,200.)
                t = str(int(tmp.GetBinLowEdge(o)))+"-"+str(int(tmp.GetBinLowEdge(o)+tmp.GetBinWidth(o)))
                rc = T.DrawLatexNDC(0.5,0.9,t)
                rc = h[var+'eff'+str(o)].Fit(fun[var],'SRQ')
                fitResult = rc.Get()
                if fitResult:
                    eff = fitResult.Parameter(0)
                    rc = T.DrawLatexNDC(0.2,0.9,"eff=%5.2F%%"%(eff*100.))
                    h['effFun'+var].SetBinContent(o,eff)
                tc.Update()
        h['eff'+var].Print('MCEfficienciesOcc'+var+'.pdf')
        h['eff'+var].Print('MCEfficienciesOcc'+var+'.png')
    ut.bookCanvas(h,'eff final','Efficiencies ',1200,900,2,2)
    j=1
    h['occ']=hMC['OccAllEvents'].Clone('occ') # want to have MC efficiency for all events, not only 1 track
    h['occ'].Scale(1./h['occ'].GetMaximum())
    h['occ'].SetLineColor(ROOT.kMagenta)
    for var in variables:
        h['eff final'].cd(j)
        j+=1
        h['effFun'+var].SetStats(0)
        h['effFun'+var].SetMarkerStyle(20)
        h['effFun'+var].SetMarkerColor(h['effFun'+var].GetLineColor())
        h['effFun'+var].GetXaxis().SetRangeUser(0.,100.)
        h['effFun'+var].Draw('P')
        h['effFun'+var].Draw('hist same')
        h['occ'].SetMarkerStyle(8)
        h['occ'].SetMarkerColor(h['occ'].GetLineColor())
        h['occ'].Draw('same P')
        h['occ'].Draw('same hist')
    var = 'P'
    ut.bookCanvas(h,'eff final P','Efficiencies ',900,600,1,1)
    h['eff final P'].cd(1)
    h['effFun'+var].SetTitle('Tracking efficiency as function of occupancy; N hits in upstream stations;efficiency')
    h['effFun'+var].GetXaxis().SetRangeUser(0.,100.)
    h['effFun'+var].Draw('P')
    h['effFun'+var].Draw('hist same')
    h['occ'].Draw('same P') 
    h['occ'].Draw('same hist')
    h['zeroFieldOcc'].Draw('P same')
    h['zeroFieldOcc'].Draw('same hist')
    hData['Occ'].Draw('same hist')
    hData['Occ'].Draw('P same')
    rc = T.DrawLatexNDC(0.28,0.40,"upstream station occupancy MC")
    T.SetTextColor(h['zeroFieldOcc'].GetLineColor())
    rc = T.DrawLatexNDC(0.28,0.28,"upstream station occupancy zero field Data")
    T.SetTextColor(hData['Occ'].GetLineColor())
    rc = T.DrawLatexNDC(0.28,0.34,"upstream station occupancy Data")
    T.SetTextColor(ROOT.kBlue)
    rc = T.DrawLatexNDC(0.35,0.8,"tracking efficiency")
    h['eff final P'].Print("MCTrackEffFunOcc.pdf")
    h['eff final P'].Print("MCTrackEffFunOcc.png")
    finalEff  = 0
    sumEvents = 0
    for o in range(1,h['occ'].GetNbinsX()+1):
        finalEff+=h['occ'].GetBinContent(o)*h['effFun'+var].GetBinContent(o)
        sumEvents+=h['occ'].GetBinContent(o)
    finalEff=finalEff/sumEvents
    print "and the final answer is for MC: %5.2F%%"%(finalEff*100)
    finalEff  = 0
    sumEvents = 0
    for o in range(1,hData['Occ'].GetNbinsX()+1):
        finalEff+=hData['Occ'].GetBinContent(o)*h['effFun'+var].GetBinContent(o)
        sumEvents+=hData['Occ'].GetBinContent(o)
    finalEff=finalEff/sumEvents
    print "and the prediction for Data: %5.2F%%"%(finalEff*100)
    finalEff  = 0
    sumEvents = 0
    for o in range(1,h['zeroFieldOcc'].GetNbinsX()+1):
        finalEff+=h['zeroFieldOcc'].GetBinContent(o)*h['effFun'+var].GetBinContent(o)
        sumEvents+=h['zeroFieldOcc'].GetBinContent(o)
    finalEff=finalEff/sumEvents
    print "and the prediction for zeroField Data: %5.2F%%"%(finalEff*100)

def plotOccExample():
    ut.bookCanvas(h,'Occexample',' ',1200,600,1,1)
    for n in range(3,7):
        x = hMC['effP'].GetListOfPrimitives()[n]
        x.GetListOfPrimitives()[1].Draw()
        t = x.GetListOfPrimitives()[2].Clone('t2'+str(n))
        tmp = t.GetTitle().split('-')
        t.SetTitle(tmp[0]+'-'+str(int(tmp[1])-1))
        t.SetTextSize(0.09)
        t.Draw()
        t2 = x.GetListOfPrimitives()[3].Clone('t3'+str(n))
        t2.SetTextSize(0.09)
        t2.Draw()
        myPrint(h['Occexample'],x.GetName())

def trueMomPlot(Nevents=-1,onlyPlotting=False):
    h     = hMC
    sTree = sTreeMC
    MCStats    = 1.8E9
    sim10fact  = MCStats/(65.E9*(1.-0.016)) # normalize 10GeV to 1GeV stats, 1.6% of 10GeV stats not processed.
    charmNorm  = {1:0.176,10:0.424}
    beautyNorm = {1:0.,   10:0.01218}
    if not onlyPlotting:
        for x in ['charm','10GeV','1GeV']:
            for c in ['','charm','beauty']:
                ut.bookHist(h,'trueMom-'+x+c,'true MC momentum;P [GeV/c];Pt [GeV/c]',500,0.,500.,200,0.,10.)
                ut.bookHist(h,'recoMom-'+x+c,'reco MC momentum;P [GeV/c];Pt [GeV/c]',500,0.,500.,200,0.,10.)
        if Nevents<0: Nevents = sTree.GetEntries()
        for n in range(Nevents):
            rc = sTree.GetEvent(n)  
            fname = sTree.GetCurrentFile().GetName()
            x = '1GeV'
            if not fname.find('charm')<0: x = 'charm'
            elif not fname.find('pythia8_Geant4_10.0')<0: 
              x = '10GeV'
              if sTree.channel==5: x+='charm'
              if sTree.channel==6: x+='beauty'
            if sTree.MCRecoDT.size() != 1: continue # look at 1 Track events for the moment
            for d in sTree.MCRecoDT:
                i = 0
                P  = ROOT.TVector3(sTree.MCRecoDTpx[i],sTree.MCRecoDTpy[i],sTree.MCRecoDTpz[i])
                found = False
                for t in range(sTree.nTr):
                    Preco  = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
                    if abs(sTree.Delx[t])<cuts['muTrackMatchX'] and abs(sTree.Dely[t])<cuts['muTrackMatchY']:
                        rc = h['trueMom-'+x].Fill(P.Mag(),P.Pt())
                        rc = h['recoMom-'+x].Fill(Preco.Mag(),Preco.Pt())
                        break
        for x in ['trueMom-','recoMom-']:
            h[x+'10GeVnorm']=h[x+'10GeV'].Clone(x+'10GeVnorm')
            h[x+'10GeVnorm'].Add(h[x+'10GeVcharm'],charmNorm[10])
            h[x+'10GeVnorm'].Add(h[x+'10GeVbeauty'],beautyNorm[10])
            h[x+'10GeVnorm'].Scale(sim10fact)
            h[x+'1GeVnorm']=h[x+'1GeV'].Clone(x+'1GeVnorm')
            h[x+'1GeVnorm'].Add(h[x+'charm'],charmNorm[1])
            h[x+'P1GeVnorm'] =h[x+'1GeVnorm'].ProjectionX(x+'P1GeVnorm')
            h[x+'P10GeVnorm']=h[x+'10GeVnorm'].ProjectionX(x+'P10GeVnorm')
            h[x+'P']=h[x+'P10GeVnorm'].Clone(x+'P')
            for i in range(1,20): 
                h[x+'P'].SetBinContent(i,h[x+'P1GeVnorm'].GetBinContent(i))
                h[x+'P'].SetBinError(i,h[x+'P1GeVnorm'].GetBinError(i))
            for i in range(20,401): 
                h[x+'P'].SetBinContent(i,h[x+'P10GeVnorm'].GetBinContent(i))
                h[x+'P'].SetBinError(i,h[x+'P10GeVnorm'].GetBinError(i))
            h[x+'Pt1GeVnorm'] =h[x+'1GeVnorm'].ProjectionY(x+'Pt1GeVnorm',1,20)
            h[x+'Pt10GeVnorm']=h[x+'10GeVnorm'].ProjectionY(x+'Pt10GeVnorm',21,400)
            h[x+'Pt']=h[x+'Pt10GeVnorm'].Clone(x+'Pt')
            h[x+'Pt'].Add(h[x+'Pt1GeVnorm'])
        ut.writeHists(h,'trueMoms-'+MCType+'.root')
    else:
        ut.readHists(h,'trueMoms-repro.root')
        ut.readHists(h0,'trueMoms-0.root')
        for k in ['P','Pt']:
            t = "true Mom "+k
            if not h.has_key(t): ut.bookCanvas(h,t,'true and reco momentum',900,600,1,1)
            tc=h[t].cd(1)
            tc.SetLogy()
            h['trueMom-'+k].SetStats(0)
            #h['trueMom-'+k].Draw()
            h['rebinned-trueMom-'+k]=h['trueMom-'+k].Clone('rebinned-trueMom-'+k)
            h['rebinned-trueMom-'+k].Rebin(5)
            h['rebinned-trueMom-'+k].Scale(1./5.)
            h['rebinned-trueMom-'+k].SetMarkerStyle(21)
            h['rebinned-trueMom-'+k].SetMarkerColor(h['rebinned-trueMom-'+k].GetLineColor())
            if k=='P': h['rebinned-trueMom-'+k].GetXaxis().SetRangeUser(5.,400.)
            h['rebinned-trueMom-'+k].SetTitle('')
            h['rebinned-trueMom-'+k].Draw()
            h['recoMom-'+k].SetLineColor(ROOT.kMagenta)
            h['recoMom-'+k].SetStats(0)
            #h['recoMom-'+k].Draw('same')
            h['rebinned-recoMom-'+k]=h['recoMom-'+k].Clone('rebinned-recoMom-'+k)
            h['rebinned-recoMom-'+k].Rebin(5)
            h['rebinned-recoMom-'+k].Scale(1./5.)
            h['rebinned-recoMom-'+k].SetMarkerStyle(23)
            h['rebinned-recoMom-'+k].SetMarkerColor(h['rebinned-recoMom-'+k].GetLineColor())
            h['rebinned-recoMom-'+k].Draw('P same')
            h0['recoMom-'+k].SetLineColor(ROOT.kGreen)
            h0['recoMom-'+k].SetStats(0)
            #h0['recoMom-'+k].Draw('same')
            h0['0rebinned-recoMom-'+k]=h0['recoMom-'+k].Clone('0rebinned-recoMom-'+k)
            # bypass issue with different number of tracks in sim files with 270mu, -0 and 350mu -repro
            rescale = h['recoMom-'+k].GetSumOfWeights()/h0['recoMom-'+k].GetSumOfWeights()
            print "rescale ",'0rebinned-recoMom-'+k,rescale,h['recoMom-'+k].GetSumOfWeights(),h0['recoMom-'+k].GetSumOfWeights()
            h0['0rebinned-recoMom-'+k].Scale( rescale )
            h0['0rebinned-recoMom-'+k].Rebin(5)
            h0['0rebinned-recoMom-'+k].Scale(1./5.)
            h0['0rebinned-recoMom-'+k].SetMarkerStyle(22)
            h0['0rebinned-recoMom-'+k].SetMarkerColor(h0['0rebinned-recoMom-'+k].GetLineColor())
            h0['0rebinned-recoMom-'+k].Draw('P same')
            h['leg'+t]=ROOT.TLegend(0.31,0.67,0.85,0.85)
            h['leg'+t].AddEntry(h['rebinned-trueMom-'+k],'true momentum ','PL')
            h['leg'+t].AddEntry(h0['0rebinned-recoMom-'+k],'reconstructed momentum 270#mum','PL')
            h['leg'+t].AddEntry(h['rebinned-recoMom-'+k],'reconstructed momentum 350#mum','PL')
            h['leg'+t].Draw()
            h[t].Print('True-Reco'+k+'.png')
            h[t].Print('True-Reco'+k+'.pdf')
def yBeam():
    Mproton = 0.938272081
    pbeam   = 400.
    Ebeam   = ROOT.TMath.Sqrt(400.**2+Mproton**2)
    beta    = 400./Ebeam # p/E 
    sqrtS   = ROOT.TMath.Sqrt(2*Mproton**2+2*Ebeam*Mproton)
    y_beam  = ROOT.TMath.Log(sqrtS/Mproton)   # Carlos Lourenco, private communication
    return y_beam
def mufluxReco(sTree,h,nseq=0,ncpus=False):
    cuts = {'':0,'Chi2<':0.7,'Dely<':5,'Delx<':2,'All':1}
    ut.bookHist(h,'Trscalers','scalers for track counting',20,0.5,20.5)
    for c in cuts:
        for x in ['','mu']:
            for s in ["","Decay","Hadronic inelastic","Lepton pair","Positron annihilation","charm","beauty","Di-muon P8","invalid"]:
                ut.bookHist(h,c+'p/pt'+x+s,'momentum vs Pt (GeV);p [GeV/c]; p_{T} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'y'+x+s,'rapidity cm; y_{CM}',500,-1.,5.,100,0.,500.,50,0.,10.)
                ut.bookHist(h,c+'p/px'+x+s,'momentum vs Px (GeV);p [GeV/c]; p_{X} [GeV/c]',500,0.,500.,200,-10.,10.)
                ut.bookHist(h,c+'p/Abspx'+x+s,'momentum vs Px (GeV);p [GeV/c]; p_{X} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'pz/Abspx'+x+s,'Pz vs Px (GeV);p [GeV/c]; p_{X} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'p/pxy'+x+s,'momentum vs Px (GeV);p [GeV/c]; p_{X} [GeV/c]',500,0.,500.,200,-10.,10.)
                ut.bookHist(h,c+'p/Abspxy'+x+s,'momentum vs Px (GeV) tagged RPC X;p [GeV/c]; p_{X} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'pz/Abspxy'+x+s,'Pz vs Px (GeV) tagged RPC X;p [GeV/c]; p_{X} [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'TrackMult'+x+s,'track multiplicity',10,-0.5,9.5)
                ut.bookHist(h,c+'chi2'+x+s,'chi2/nDoF',100,0.,10.)
                ut.bookHist(h,c+'Nmeasurements'+x+s,'number of measurements used',25,-0.5,24.5)
                ut.bookHist(h,c+'xy'+x+s,'xy of first state;x [cm];y [cm]',100,-30.,30.,100,-30.,30.)
                ut.bookHist(h,c+'pxpy'+x+s,'px/pz py/pz of first state',100,-0.2,0.2,100,-0.2,0.2)
                ut.bookHist(h,c+'p1/p2'+x+s,'momentum p1 vs p2;p [GeV/c]; p [GeV/c]',500,0.,500.,500,0.,500.)
                ut.bookHist(h,c+'pt1/pt2'+x+s,'P_{T} 1 vs P_{T} 2;p [GeV/c]; p [GeV/c]',100,0.,10.,100,0.,10.)
                ut.bookHist(h,c+'p1/p2s'+x+s,'momentum p1 vs p2 same sign;p [GeV/c]; p [GeV/c]',500,0.,500.,500,0.,500.)
                ut.bookHist(h,c+'pt1/pt2s'+x+s,'P_{T} 1 vs P_{T} 2 same sign;p [GeV/c]; p [GeV/c]',100,0.,10.,100,0.,10.)
                ut.bookHist(h,c+'Chi2/DoF'+x+s,'Chi2/DoF',100,0.,5.,100,0.,500.)
                ut.bookHist(h,c+'DoF'+x+s,     'DoF'     ,30,0.5,30.5,100,0.,500.)
                ut.bookHist(h,c+'R'+x+s,'rpc match',100,0.,10.,100,0.,500.)
                ut.bookHist(h,c+'RPCResX/Y'+x+s,'RPC residuals',200,0.,200.,200,0.,200.)
                ut.bookHist(h,c+'RPCMatch'+x+s,'RPC matching',100,0.,10.,100,0.,10.)
                ut.bookHist(h,c+'trueMom'+x+s,'true MC momentum;P [GeV/c];Pt [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'recoMom'+x+s,'reco MC momentum;P [GeV/c];Pt [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'truePz/Abspx'+x+s,'true MC momentum;P [GeV/c];Px [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'recoPz/Abspx'+x+s,'reco MC momentum;P [GeV/c];Px [GeV/c]',500,0.,500.,100,0.,10.)
                ut.bookHist(h,c+'momResol'+x+s,'momentum resolution function of momentum;P [GeV/c];#sigma P/P', 200,-0.5,0.5,40,0.,400.)
#
    MCdata = False
    if sTree.FindBranch("MCRecoDT"): MCdata = True
#
    Ntotal = sTree.GetEntries()
    nStart = 0
    if ncpus:
      ncpus = int(ncpus)
      nseq = int(nseq)
      deltaN = (sTree.GetEntries()+0.5)//ncpus
      nStart = int(nseq*deltaN)
      Ntotal = int(min(sTree.GetEntries(),nStart+deltaN))
    for n in range(nStart,Ntotal):
        rc = sTree.GetEvent(n)
        if n%500000==0: print 'now at event ',n,'of',Ntotal,time.ctime()
        h['Trscalers'].Fill(1)
        if len(sTree.GoodTrack)>0: h['Trscalers'].Fill(2)
        tchannel = sTree.channel
        source = ''
        if MCdata:
            if (tchannel == 1):  source = "Decay"
            if (tchannel == 7):  source = "Di-muon P8"
            if (tchannel == 2):  source = "Hadronic inelastic"
            if (tchannel == 3):  source = "Lepton pair"
            if (tchannel == 4):  source = "Positron annihilation"
            if (tchannel == 5):  source = "charm"
            if (tchannel == 6):  source = "beauty"
            if (tchannel == 13): source = "invalid"
        muonTaggedTracks = {}
        for k in range(len(sTree.GoodTrack)):
            h['Trscalers'].Fill(3)
            if sTree.GoodTrack[k]<0: continue
            h['Trscalers'].Fill(4)
            muTagged  = False
            muTaggedX = False
            clone     = False
            if sTree.GoodTrack[k]%2==1: 
                muTaggedX = True
                if int(sTree.GoodTrack[k]/10)%2==1: muTagged = True
            if sTree.GoodTrack[k]>999:  clone = True
            if clone: continue
            R = (sTree.Dely[k]/3.)**2+(sTree.Delx[k]/1.5)**2
            p = ROOT.TVector3(sTree.Px[k],sTree.Py[k],sTree.Pz[k])
            rc = h['R'].Fill(R,p.Mag())
            rc = h['RPCMatch'].Fill(sTree.Delx[k],sTree.Dely[k])
            okCuts = ['']
            muonTaggedTracks['']=[]
            if sTree.Chi2[k]<cuts['Chi2<']: okCuts.append('Chi2<')
            if sTree.Dely[k]<cuts['Dely<']: okCuts.append('Dely<')
            if sTree.Delx[k]<cuts['Delx<']: okCuts.append('Delx<')
            if sTree.Chi2[k]<cuts['Chi2<'] and sTree.Dely[k]<cuts['Dely<'] and sTree.Delx[k]<cuts['Delx<']: okCuts.append('All')
            for c in okCuts:
                LV = ROOT.Math.PxPyPzMVector(p.X(),p.Y(),p.Z(),0.105658)
                y  = LV.Rapidity()-yBeam()
                h[c+"p/pt"].Fill(p.Mag(),p.Pt())
                h[c+"y"].Fill(y,p.Mag(),p.Pt())
                h[c+"p/Abspx"].Fill(p.Mag(),abs(p.x()))
                h[c+"pz/Abspx"].Fill(p.z(),abs(p.x()))
                h[c+"xy"].Fill(sTree.x[k],sTree.y[k])
                h[c+"pxpy"].Fill(p.x()/p.z(),p.y()/p.z())
                h[c+'Chi2/DoF'].Fill(sTree.Chi2[k],p.Mag())
                h[c+'DoF'].Fill(sTree.nDoF[k],p.Mag())
                if p.Mag()>300. and Debug: 
                    occ = sTree.stationOcc[1]+sTree.stationOcc[2]+sTree.stationOcc[5]+sTree.stationOcc[6]
                    print n, p.Mag(),occ,sTree.GoodTrack[k],sTree.Chi2[k],sTree.nDoF[k]
                if source != '':
                    h[c+"p/pt"+source].Fill(p.Mag(),p.Pt())
                    h[c+"y"+source].Fill(y,p.Mag(),p.Pt())
                    h[c+"p/px"+source].Fill(p.Mag(),p.x())
                    h[c+"p/Abspx"+source].Fill(p.Mag(),abs(p.x()))
                    h[c+"pz/Abspx"+source].Fill(p.z(),abs(p.x()))
                    h[c+"xy"+source].Fill(sTree.x[k],sTree.y[k])
                    h[c+"pxpy"+source].Fill(p.x()/p.z(),p.y()/p.z())
                    h[c+'R'+source].Fill(R,p.Mag())
                    h[c+'Chi2/DoF'+source].Fill(sTree.Chi2[k],p.Mag())
                    h[c+'DoF'+source].Fill(sTree.nDoF[k],p.Mag())
                h[c+'RPCResX/Y'].Fill(sTree.Delx[k],sTree.Dely[k])
                if (muTaggedX): # within ~3sigma  X from mutrack
                    h[c+"p/pxmu"].Fill(p.Mag(),p.x())
                    h[c+"p/Abspxmu"].Fill(p.Mag(),abs(p.x()))
                    h[c+"pz/Abspxmu"].Fill(p.z(),abs(p.x()))
                    if source != '':
                        h[c+"p/pxmu"+source].Fill(p.Mag(),p.x())
                        h[c+"p/Abspxmu"+source].Fill(p.Mag(),abs(p.x()))
                        h[c+"pz/Abspxmu"+source].Fill(p.z(),abs(p.x()))
                if (muTagged): #  within ~3sigma  X,Y from mutrack
                    if c=='': muonTaggedTracks[''].append(k)
                    h[c+"p/ptmu"].Fill(p.Mag(),p.Pt())
                    h[c+"ymu"].Fill(y,p.Mag(),p.Pt())
                    h[c+"p/pxymu"].Fill(p.Mag(),p.x())
                    h[c+"p/Abspxymu"].Fill(p.Mag(),abs(p.x()))
                    h[c+"pz/Abspxymu"].Fill(p.z(),abs(p.x()))
                    h[c+"xymu"].Fill(sTree.x[k],sTree.y[k])
                    h[c+"pxpymu"].Fill(p.x()/p.z(),p.y()/p.z())
                    h[c+'Rmu'].Fill(R,p.Mag())
                    h[c+'Chi2/DoFmu'].Fill(sTree.Chi2[k],p.Mag())
                    h[c+'DoFmu'].Fill(sTree.nDoF[k],p.Mag())
                    if source != '':
                        h[c+"p/ptmu"+source].Fill(p.Mag(),p.Pt())
                        h[c+"ymu"+source].Fill(y,p.Mag(),p.Pt())
                        h[c+"p/pxymu"+source].Fill(p.Mag(),p.x())
                        h[c+"p/Abspxymu"+source].Fill(p.Mag(),abs(p.x()))
                        h[c+"pz/Abspxymu"+source].Fill(p.z(),abs(p.x()))
                        h[c+"xymu"+source].Fill(sTree.x[k],sTree.y[k])
                        h[c+"pxpymu"+source].Fill(p.x()/p.z(),p.y()/p.z())
                        h[c+'Rmu'+source].Fill(R,p.Mag())
                        h[c+'Chi2/DoFmu'+source].Fill(sTree.Chi2[k],p.Mag())
                        h[c+'DoFmu'+source].Fill(sTree.nDoF[k],p.Mag())
#
                if len(muonTaggedTracks[''])==2:
                    a,b=muonTaggedTracks[''][0],muonTaggedTracks[''][1]
                    pA=ROOT.TVector3(sTree.Px[a],sTree.Py[a],sTree.Pz[a])
                    pB=ROOT.TVector3(sTree.Px[b],sTree.Py[b],sTree.Pz[b])
                    prodSign = sTree.Sign[a]*sTree.Sign[b]
                    if prodSign<0:
                        h["p1/p2"].Fill(pA.Mag(),pB.Mag())
                        h["pt1/pt2"].Fill(pA.Pt(),pB.Pt())
                        if source != '':
                            h["p1/p2"+source].Fill(pA.Mag(),pB.Mag())
                            h["pt1/pt2"+source].Fill(pA.Pt(),pB.Pt())
                    else:
                        h["p1/p2s"].Fill(pA.Mag(),pB.Mag())
                        h["pt1/pt2s"].Fill(pA.Pt(),pB.Pt())
                        if source != '':
                            h["p1/p2s"+source].Fill(pA.Mag(),pB.Mag())
                            h["pt1/pt2s"+source].Fill(pA.Pt(),pB.Pt())
# mom resolution
                if MCdata and len(sTree.GoodTrack)==1 and len(sTree.MCRecoDTpx)==1:
                    trueMom = ROOT.TVector3(sTree.MCRecoDTpx[0],sTree.MCRecoDTpy[0],sTree.MCRecoDTpz[0])
                    h["trueMom"].Fill(trueMom.Mag(),trueMom.Pt())
                    h["recoMom"].Fill(p.Mag(),p.Pt())
                    h["truePz/Abspx"].Fill(trueMom[2],ROOT.TMath.Abs(trueMom[0]))
                    h["recoPz/Abspx"].Fill(p[2],ROOT.TMath.Abs(p[0]))
                    h["momResol"].Fill((p.Mag()-trueMom.Mag())/trueMom.Mag(),trueMom.Mag())
                    if source != '':
                        h["trueMom"+source].Fill(trueMom.Mag(),trueMom.Pt());
                        h["recoMom"+source].Fill(p.Mag(),p.Pt());
                        h["truePz/Abspx"+source].Fill(trueMom[2],ROOT.TMath.Abs(trueMom[0]));
                        h["recoPz/Abspx"+source].Fill(p[2],ROOT.TMath.Abs(p[0]));
                        h["momResol"+source].Fill((p.Mag()-trueMom.Mag())/trueMom.Mag(),trueMom.Mag());
    tmp = 'RUN_8000'+fdir.split('RUN_8000')[1]
    outFile = 'sumHistos-'+'-'+tmp+'.root'
    if options.refit: outFile = 'sumHistos-'+'-'+tmp+'_refit.root'
    if ncpus:
       outFile=outFile.replace('.root','-'+str(nseq)+'.root')
    ut.writeHists( h,outFile)
    print "I have finished. ",outFile
def dEdxCorrection(p):
 # +7.3    # most probably ~7.5, mean 6.9.
 dE = -7.63907  -0.0315131  * p + 0.000168569 * p*p
 return -dE*(1-0.085)  # fudge factor reversed engineering
def invMass(sTree,h,nseq=0,ncpus=False):
    ut.bookHist(h,'invMassSS','inv mass ',100,0.0,10.0)
    ut.bookHist(h,'invMassOS','inv mass ',100,0.0,10.0)
    ut.bookHist(h,'invMassJ','inv mass from Jpsi',100,0.0,10.0)
    ut.bookHist(h,'p/pt','p/pt',100,0.0,400.0,100,0.0,10.0)
    ut.bookHist(h,'p/ptJ','p/pt of Jpsi',100,0.0,400.0,100,0.0,10.0)
    ut.bookHist(h,'p/ptmu','p/pt of mu',100,0.0,400.0,100,0.0,10.0)
    ut.bookHist(h,'p/ptmuJ','p/pt of mu from Jpsi',100,0.0,400.0,100,0.0,10.0)
    MCdata = False
    if sTree.FindBranch("MCRecoDT"): MCdata = True
    if MCdata:
       name = "ntuple-invMass-MC.root"
       if ncpus:
          name = name.replace('.root','-'+str(nseq)+'.root')
    else:      
       name = "ntuple-invMass-"+fdir.split('/')[7]+'.root'
    if options.refit: name = name.replace('.root','_refit.root')
    h['fntuple']  = ROOT.TFile.Open(name, 'RECREATE')
    variables = "mult:m:mcor:mcor2:y:ycor:p:pt:p1:pt1:p2:pt2:Ip1:Ip2:chi21:chi22:cosTheta:cosCSraw:cosCScor:\
prec1x:prec1y:prec1z:prec2x:prec2y:prec2z:rec1x:rec1y:rec1z:rec2x:rec2y:rec2z"
    if MCdata:
      variables += ":Jpsi:PTRUE:PtTRUE:p1True:p2True:dTheta1:dTheta2:dMults1:dMults2:originZ1:originZ2:p1x:p1y:p1z:p2x:p2y:p2z:ox:oy:oz"
    h['nt']  = ROOT.TNtuple("nt","dimuon",variables) 
#
    sTreeFullMC = None
    Ntotal = sTree.GetEntries()
    nStart = 0
    if ncpus:
      ncpus = int(ncpus)
      nseq = int(nseq)
      deltaN = (sTree.GetEntries()+0.5)//ncpus
      nStart = int(nseq*deltaN)
      Ntotal = int(min(sTree.GetEntries(),nStart+deltaN))
    currentFile = ''
    for n in range(0,Ntotal):
        rc = sTree.GetEvent(n)
        # if n%500000==0: print 'now at event ',n,'of',Ntotal,time.ctime()
        if sTree.GetCurrentFile().GetName()!=currentFile:
            currentFile = sTree.GetCurrentFile().GetName()
            nInFile = n
        if n<nStart: continue
        tchannel = sTree.channel
        source = ''
        if MCdata:
            if (tchannel == 1):  source = "Decay"
            if (tchannel == 7):  source = "Di-muon P8"
            if (tchannel == 2):  source = "Hadronic inelastic"
            if (tchannel == 3):  source = "Lepton pair"
            if (tchannel == 4):  source = "Positron annihilation"
            if (tchannel == 5):  source = "charm"
            if (tchannel == 6):  source = "beauty"
            if (tchannel == 13): source = "invalid"
        P    = {}
        IP   = {}
        Pcor = {}
        Pcor2 = {}
        for k in range(len(sTree.GoodTrack)):
            if sTree.GoodTrack[k]<0: continue
            if sTree.GoodTrack[k]%2!=1 or  int(sTree.GoodTrack[k]/10)%2!=1: continue
            if sTree.GoodTrack[k]>999:  continue
            P[k] = ROOT.Math.PxPyPzMVector(sTree.Px[k],sTree.Py[k],sTree.Pz[k],0.105658)
            l = (sTree.z[k] - zTarget)/(sTree.Pz[k]+ 1E-19)
            x = sTree.x[k]+l*sTree.Px[k]
            y = sTree.y[k]+l*sTree.Py[k]
            IP[k] = ROOT.TMath.Sqrt(x*x+y*y)
# make dE correction plus direction from measured point
            dline   = ROOT.TVector3(sTree.x[k],sTree.y[k],sTree.z[k]-zTarget)
            Ecor = P[k].E()+dEdxCorrection(P[k].P())
            norm = dline.Mag()
            Pcor[k]  = ROOT.Math.PxPyPzMVector(Ecor*dline.X()/norm,Ecor*dline.Y()/norm,Ecor*dline.Z()/norm,0.105658)
            Pcor2[k] = ROOT.Math.PxPyPzMVector(P[k].P()*dline.X()/norm,P[k].P()*dline.Y()/norm,P[k].P()*dline.Z()/norm,0.105658)
# now we have list of selected tracks, P.keys()
        if len(P)<2: continue
        X    = {}
        Xcor = {}
        Xcor2 = {}
        jpsi = {}
        pTrue  = {}
        dTheta = {}
        dMults = {}
        originZ = {}
        PTRUE  = {}
        PtTRUE = {}
        costheta = {}
        chi2 = {}
        nComb = {}
        j = 0
        pDict = P.keys()
        for l1 in range(len(pDict)-1):
         for l2 in range(l1+1,len(pDict)):
          n1 = pDict[l1]
          n2 = pDict[l2]
          X[j]    = P[n1]+P[n2]
          Xcor[j] = Pcor[n1]+Pcor[n2]
          Xcor2[j] = Pcor2[n1]+Pcor2[n2]
# angle between two tracks in Jpsi rest frame
          b = X[j].BoostToCM()
          moth_boost = ROOT.Math.Boost(b.x(),b.y(),b.z())
          Pcms = moth_boost*P[n1]
          v0=ROOT.TVector3(Pcms.X(),Pcms.Y(),Pcms.Z())
          v1=ROOT.TVector3(X[j].X(),X[j].Y(),X[j].Z())
          costheta[j] = v0.Dot(v1)/( v0.Mag()*v1.Mag() + 1E-19)
          if sTree.Sign[n1]*sTree.Sign[n2]<0:  rc = h["invMassOS"].Fill(X[j].M())
          else:                                rc = h["invMassSS"].Fill(X[j].M())
          chi2[j] = [sTree.Sign[n1]*sTree.Chi2[n1],sTree.Sign[n2]*sTree.Chi2[n2]]
          if X[j].M()>2.5 and X[j].M()<4.0:
             rc = h["p/pt"].Fill(X[j].P(),X[j].Pt())
             rc = h["p/ptmu"].Fill(P[n1].P(),P[n2].Pt())
             rc = h["p/ptmu"].Fill(P[n1].P(),P[n2].Pt())
          jpsi[j] = -1
          originZ[j]  = [-9999.,-9999.]
          pTrue[j]    = [ROOT.TVector3(0,0,-9999.),ROOT.TVector3(0,0,-9999.)]
          dTheta[j] = [-9999.,-9999.]
          dMults[j] = [-9999.,-9999.]
          PTRUE[j]  = -1.
          PtTRUE[j] = -1.
          nComb[j]=[n1,n2]
          if X[j].M()>-2.5 and MCdata: 
#check truth
            eospathSim = os.environ['EOSSHIP']+'/eos/experiment/ship/user/truf/muflux-sim/'
            fname = sTree.GetCurrentFile().GetName().split('simulation')[1].replace('ntuple-','').replace('-final','')
            if sTreeFullMC:
                if sTreeFullMC.GetCurrentFile().GetName().find(fname)<0:
                    fMC = ROOT.TFile.Open(eospathSim+fname)
                    sTreeFullMC = fMC.cbmsim
            else: 
                fMC = ROOT.TFile.Open(eospathSim+fname)
                sTreeFullMC = fMC.cbmsim
            rc = sTreeFullMC.GetEvent(n-nInFile)
            # print rc,sTreeFullMC,n,nInFile,n1,n2
            mothers = []
            kx = 0
            for k in [n1,n2]:
                trueMu = sTreeFullMC.MCTrack[sTreeMC.MCID[k]]
                mother = sTreeFullMC.MCTrack[trueMu.GetMotherId()]
                mothers.append(mother.GetPdgCode())
                PTRUE[j]  = mother.GetP()
                PtTRUE[j] = mother.GetPt()
# check multiple scattering
                trueMu.GetMomentum(pTrue[j][kx])
                originZ[j][kx] = trueMu.GetStartZ()
                dline   = ROOT.TVector3(sTree.x[k],sTree.y[k],sTree.z[k]-zTarget)
                dTheta[j][kx]  = pTrue[j][kx].Dot(dline)/(pTrue[j][kx].Mag()*dline.Mag())
                prec = ROOT.TVector3(P[k].Px(),P[k].Py(),P[k].Pz())
                dMults[j][kx]  = pTrue[j][kx].Dot(prec)/(pTrue[j][kx].Mag()*prec.Mag())
                kx+=1
            if len(mothers)==2: 
             if mothers[0]==mothers[1]: jpsi[j] = mothers[0]
            if jpsi[j] == 443:
                rc = h["invMassJ"].Fill(X[j].M())
                rc = h["p/ptJ"].Fill(X[j].P(),X[j].Pt())
                rc = h["p/ptmuJ"].Fill(P[n1].P(),P[n1].Pt())
                rc = h["p/ptmuJ"].Fill(P[n2].P(),P[n2].Pt())
                if Debug:
                 trueMu = sTreeFullMC.MCTrack[sTreeMC.MCID[n1]]
                 mother = sTreeFullMC.MCTrack[trueMu.GetMotherId()]
                 print X[j].M(),n,n-nInFile,sTree.GetCurrentFile()
                 print 'origin',mother.GetStartX(),mother.GetStartY(),mother.GetStartZ()
          j+=1
# now we have all combinations, j
        for j in nComb:
          n1 = nComb[j][0]
          n2 = nComb[j][1]
          if chi2[j][0] < 0: 
           nlep      = n1
           nantilep  = n2
          else: 
           nlep = n2
           nantilep  = n1
          P1pl = P[nlep].E()+P[nlep].Pz()
          P2pl = P[nantilep].E()+P[nantilep].Pz()
          P1mi = P[nlep].E()-P[nlep].Pz()
          P2mi = P[nantilep].E()-P[nantilep].Pz()
          cosCSraw = X[j].Pz()/abs(X[j].Pz()) * 1./X[j].M()/ROOT.TMath.Sqrt(X[j].M2()+X[j].Pt()**2)*(P1pl*P2mi-P2pl*P1mi)
          P1pl = Pcor[nlep].E()+Pcor[nlep].Pz()
          P2pl = Pcor[nantilep].E()+Pcor[nantilep].Pz()
          P1mi = Pcor[nlep].E()-Pcor[nlep].Pz()
          P2mi = Pcor[nantilep].E()-Pcor[nantilep].Pz()
          cosCScor = Xcor[j].Pz()/abs(Xcor[j].Pz()) * 1./Xcor[j].M()/ROOT.TMath.Sqrt(Xcor[j].M2()+Xcor[j].Pt()**2)*(P1pl*P2mi-P2pl*P1mi)
          Y    = X[j].Rapidity()
          Ycor = Xcor[j].Rapidity()
          theArray = [float(len(nComb)),X[j].M(),Xcor[j].M(),Xcor2[j].M(),Y,Ycor,X[j].P(),X[j].Pt(),P[n1].P(),P[n1].Pt(),P[n2].P(),P[n2].Pt(),\
                     IP[n1],IP[n2],chi2[j][0],chi2[j][1],costheta[j],cosCSraw,cosCScor,\
                     P[n1].X(),P[n1].Y(),P[n1].Z(),P[n2].X(),P[n2].Y(),P[n2].Z(),\
                     sTree.x[n1],sTree.y[n1] ,sTree.z[n1],sTree.x[n2],sTree.y[n2] ,sTree.z[n2] ]
          if MCdata:
             kTrueMu = sTreeMC.MCID[n1]
             if kTrueMu>0:
              ox,oy,oz = sTreeFullMC.MCTrack[kTrueMu].GetStartX(),sTreeFullMC.MCTrack[kTrueMu].GetStartY(),sTreeFullMC.MCTrack[kTrueMu].GetStartZ()
             else:
              ox,oy,oz = -9999.,9999.,-9999.
             theArray += [float(jpsi[j]),PTRUE[j],PtTRUE[j],pTrue[j][0].Mag(),pTrue[j][1].Mag(),\
                     dTheta[j][0],dTheta[j][1],dMults[j][0],dMults[j][1],originZ[j][0],originZ[j][1],\
                     pTrue[j][0].X(),pTrue[j][0].Y(),pTrue[j][0].Z(),pTrue[j][1].X(),pTrue[j][1].Y(),pTrue[j][1].Z(),ox,oy,oz]
          theTuple = array('f',theArray)
          h['nt'].Fill(theTuple)
    h['fntuple'].cd()
    h['nt'].Write()
    hname = name.replace('ntuple-','')
    ut.writeHists(h,hname)
    print "I have finished. ",hname
def myDraw(variable,cut):
 hMC['10GeV'].Draw(variable,cut)
 # too complicated to combine 1GeV
 # hMC['10GeV'].Draw(variable,str(hMC['weights']['1GeV'])+'*('+cut+')')
 # hMC['10eV'].Draw(variable.replace(">>",">>+"),str(hMC['weights']['1GeV'])+'*('+cut+')')
 
jpsiCascadeContr = 7./33.  
# The elastic proton proton cross section at ~27GeV is about 7mbar. The inelastic cross section is about 33mbar. 
# Since we have a thick target, any proton from the elastic scattering will interact inelastic somewhere else.
# last cascade production of Eric shows even larger contribution, but momentum distribution not clear.
def diMuonAnalysis():
 if options.refit :
  hData['f'] = ROOT.TFile('ntuple-InvMass-refitted.root')  # ROOT.TFile('ntuple-InvMass-refitted_intermediateField.root')
  hMC['f1']  = ROOT.TFile('ntuple-invMass-MC-1GeV-repro.root')
  hMC['f10'] = ROOT.TFile('ntuple-invMass-MC-10GeV-repro.root')
 else:
  hData['f'] = ROOT.TFile('ntuple-InvMass.root')
  hMC['f1']  = ROOT.TFile('ntuple-invMass-MC-1GeV.root')
  hMC['f10'] = ROOT.TFile('ntuple-invMass-MC-10GeV.root')
 sTreeData  = hData['f'].nt
 hMC['1GeV'] =hMC['f1'].nt
 hMC['10GeV']=hMC['f10'].nt
# make normalization
    # covered cases: cuts = '',      simpleEffCor=0.024, simpleEffCorMu=0.024
    # covered cases: cuts = 'Chi2<', simpleEffCor=0.058, simpleEffCorMu=0.058
    # covered cases: cuts = 'All', simpleEffCor=0.058,   simpleEffCorMu=0.129
    # 1GeV mbias,      1.806 Billion PoT 
    # 10GeV MC,       66.02 Billion PoT 
    # using 626 POT/mu-event and preliminary counting of good tracks -> 12.63 -> pot factor 7.02
    # using 710 POT/mu-event, full field
# 
 simpleEffCor = 0.024
 MCStats = {'1GeV': 1.806E9,'10GeV':66.02E9}
 mcSysError = 0.03
 daSysError = 0.021
 dataStats  = 324.75E9
 hMC['weights'] = {'1GeV': MCStats['1GeV']/dataStats/(1+simpleEffCor*2),'10GeV':MCStats['10GeV']/dataStats/(1+simpleEffCor*2)}
#
 InvMassPlots = [160,0.,8.]
#
 ptCutList = [0.0,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6]
 hData['fitResult'] = {}
 hMC['fitResult'] = {}
 sptCut = 'XYZ'
 theCutTemplate =  '('+sptCut+'<pt1||'+sptCut+'<pt2)&&chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&p1<300&&p2<300&&p1>20&&p2>20&&mcor>0.20'
 ut.bookHist(hMC, 'mc_theta','cos theta mother - daughter1',100,-1,1.)
 ut.bookHist(hMC, 'mc_thetaJ','cos theta mother - daughter1 Jpsi',100,-1,1.)
 ut.bookHist(hData, 'theta','cos theta mother - daughter1',100,-1,1.)
 ut.bookCanvas(hMC,'tTheta','costheta',900,600,1,1)
 ut.bookCanvas(hMC,'tMass','mass',900,600,1,1)
 ut.bookCanvas(hMC,'dummy',' ',900,600,1,1)
 hMC['mc_theta'].SetLineColor(ROOT.kRed)
 hMC['mc_thetaJ'].SetLineColor(ROOT.kMagenta)
 theCut = theCutTemplate.replace('XYZ','0')
 ROOT.gROOT.cd()
 myDraw('cosTheta>>mc_thetaJ',theCut+'&&Jpsi==443')
 myDraw('cosTheta>>mc_theta',theCut)
 sTreeData.Draw('cosTheta>>theta',theCut)
 hMC['tTheta'].cd(1)
 hMC['mc_theta'].Scale(1./hMC['mc_theta'].GetEntries())
 hMC['mc_thetaJ'].Scale(1./hMC['mc_thetaJ'].GetEntries())
 hData['theta'].Scale(1./hData['theta'].GetEntries())
 hMC['mc_theta'].Draw()
 hMC['mc_thetaJ'].Draw('same')
 hData['theta'].Draw('same')
 myPrint(hMC['tTheta'],'dimuon-theta')
 ut.bookHist(hMC, 'mc_IP','IP',100,0.,100.)
 ut.bookHist(hMC, 'mc_IPJ','IP',100,0.,100.)
 ut.bookHist(hData, 'IP','IP',100,0.,100.)
 ut.bookCanvas(hMC,'tIP','distance to target',900,600,1,1)
 hMC['mc_IP'].SetLineColor(ROOT.kRed)
 hMC['mc_IPJ'].SetLineColor(ROOT.kMagenta)
 myDraw('Ip1>>mc_IPJ',theCut+'&&Jpsi==443')
 myDraw('Ip1>>mc_IP',theCut)
 sTreeData.Draw('Ip1>>IP',theCut)
 myDraw('Ip2>>+mc_IPJ',theCut+'&&Jpsi==443')
 myDraw('Ip2>>+mc_IP',theCut)
 sTreeData.Draw('Ip2>>+IP',theCut)
 hMC['tIP'].cd()
 hMC['mc_IP'].Scale(1./hMC['mc_IP'].GetEntries())
 hMC['mc_IPJ'].Scale(1./hMC['mc_IPJ'].GetEntries())
 hData['IP'].Scale(1./hData['IP'].GetEntries())
 hMC['mc_IP'].Draw()
 hMC['mc_IPJ'].Draw('same')
 hData['IP'].Draw('same')
 myPrint(hMC['tIP'],'dimuon-IP')
 ut.bookHist(hMC, 'm_MC','inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
 ut.bookHist(hMC, 'm_MClow','inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
 hMC['dummy'].cd()
 colors = {221:ROOT.kBlue,223:ROOT.kCyan,113:ROOT.kGreen,331:ROOT.kOrange,333:ROOT.kRed,443:ROOT.kMagenta}
 nmax = 0
 for j in colors:
   pname = PDG.GetParticle(j).GetName()
   hname = 'Mass_'+pname.replace('/','')
   hMC[hname]=hMC['m_MClow'].Clone(hname)
   hMC[hname].SetTitle('inv mass '+PDG.GetParticle(j).GetName()+' ;M [GeV/c^{2}]')
   hMC[hname].SetLineColor(colors[j])
   hMC[hname].SetStats(0)
   myDraw('m>>'+hname,'Jpsi=='+str(j))
   if hMC[hname].GetMaximum()>nmax: nmax = hMC[hname].GetMaximum()
   hname = 'Masscor_'+pname.replace('/','')
   hMC[hname]=hMC['m_MClow'].Clone(hname)
   hMC[hname].SetTitle('inv mass '+PDG.GetParticle(j).GetName()+' ;M [GeV/c^{2}]')
   hMC[hname].SetLineColor(colors[j])
   hMC[hname].SetStats(0)
   myDraw('mcor>>'+hname,'Jpsi=='+str(j))
   if hMC[hname].GetMaximum()>nmax: nmax = hMC[hname].GetMaximum()
 for z in ['','cor']:
  first = True
  hMC['lMassMC'+z]=ROOT.TLegend(0.7,0.7,0.95,0.95)
  for j in colors:
    pname = PDG.GetParticle(j).GetName()
    hname = 'Mass'+z+'_'+pname.replace('/','')
    hMC[hname].SetStats(0)
    if first:
       first = False
       hMC[hname].SetMaximum(nmax*1.1)
       hMC[hname].SetTitle(';M [GeV/c^{2}]')
       hMC[hname].Draw()
    else:
       hMC[hname].Draw('same')
    hMC['lMassMC'+z].AddEntry(hMC[hname],pname,'PL')
  hMC['lMassMC'+z].Draw()
  myPrint(hMC['dummy'],'MCdiMuonMass'+z)


 bw = hMC['m_MC'].GetBinWidth(1)
 hMC['myGauss'] = ROOT.TF1('gauss','abs([0])*'+str(bw)+'/(abs([2])*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)\
            +abs([3])*'+str(bw)+'/(abs([5])*sqrt(2*pi))*exp(-0.5*((x-[4])/[5])**2)+abs( [6]+[7]*x+[8]*x**2 )\
            +abs([9])*'+str(bw)+'/(abs([2])*sqrt(2*pi))*exp(-0.5*((x-(3.6871 + [1] - 3.0969))/[2])**2)',10)
 myGauss = hMC['myGauss']
 # doesn't help really theCutTemplate +=  '&&abs(cosTheta)<0.8' 
 vText={'m':'inv mass and fits','mcor':'inv mass, dE and direction corrected, and fits','mcor2':'inv mass, direction corrected, and fits'}
 for v in vText:
  for ptCut in ptCutList:
   sptCut = str(ptCut)
   ut.bookHist(hMC, 'mc-'+v+'_'+sptCut,'inv mass MC;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   ut.bookHist(hMC, 'mc-'+v+'_Jpsi_'+sptCut,'inv mass Jpsi MC matched;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   ut.bookHist(hData,v+'_'+sptCut,'inv mass DATA;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   ut.bookHist(hData,'SS-'+v+'_'+sptCut,'SS inv mass DATA;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   ut.bookHist(hMC, 'SS-mc-'+v+'_'+sptCut,'SS inv mass MC;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   hData['SS-'+v+'_'+sptCut].SetLineColor(ROOT.kRed)
   hMC['SS-mc-'+v+'_'+sptCut].SetLineColor(ROOT.kRed)
#
   theCut =  theCutTemplate.replace('XYZ',sptCut)
   ROOT.gROOT.cd()
   hMC['dummy'].cd()
   sTreeData.Draw(v+'>>'+v+'_'+sptCut,theCut)
   sTreeData.Draw(v+'>>SS-'+v+'_'+sptCut,theCut.replace('chi21*chi22<0','chi21*chi22>0'))
   myDraw(v+'>>mc-'+v+'_'+sptCut ,theCut)
   myDraw(v+'>>SS-mc-'+v+'_'+sptCut ,theCut.replace('chi21*chi22<0','chi21*chi22>0'))
   myDraw(v+'>>mc-'+v+'_Jpsi_'+sptCut ,theCut+"&&Jpsi==443")

  ut.bookCanvas(hMC,'fits'+v,vText[v],1800,800,5,4)
  j = 1
  for ptCut in  ptCutList:
   sptCut = str(ptCut)
   tc = hMC['fits'+v].cd(j)
   init_Gauss(myGauss)
   rc = hMC['mc-'+v+'_'+sptCut].Fit(myGauss,'S','',0.5,5.)
   fitResult = rc.Get()
   if fitResult.Parameter(0)+fitResult.Parameter(3)>hMC['mc-'+v+'_'+sptCut].GetEntries()*1.5:
     myGauss.FixParameter(3,0)
     myGauss.FixParameter(4,1.)
     myGauss.FixParameter(5,1.)
     rc = hMC['mc-'+v+'_'+sptCut].Fit(myGauss,'S','',0.5,5.)
     fitResult = rc.Get()
   hMC['fitResult'][ptCut] = {}
   for n in range(10):
    hMC['fitResult'][ptCut][myGauss.GetParName(n)] = [fitResult.Parameter(n),fitResult.ParError(n)]
   if v=='mcor':
    myGauss.FixParameter(1,fitResult.Parameter(1))
    myGauss.FixParameter(2,fitResult.Parameter(2))
    myGauss.ReleaseParameter(9)
    rc = hMC['mc-'+v+'_'+sptCut].Fit(myGauss,'S','',0.5,5.)
    myGauss.ReleaseParameter(1)
    myGauss.ReleaseParameter(2)
    rc = hMC['mc-'+v+'_'+sptCut].Fit(myGauss,'S','',0.5,5.)
    fitResult = rc.Get()
    hMC['fitResult'][ptCut][myGauss.GetParName(9)] = [fitResult.Parameter(9),fitResult.ParError(9)]
   hMC['mc-'+v+'_Jpsi_'+sptCut].SetLineColor(ROOT.kMagenta)
   hMC['mc-'+v+'_Jpsi_'+sptCut].Draw('same')
   hMC['SS-mc-'+v+'_'+sptCut].Draw('same')
   tc.Update()
   stats = tc.GetPrimitive('stats')
   stats.SetOptFit(10111)
   stats.SetFitFormat('5.4g')
   stats.SetX1NDC(0.41)
   stats.SetY1NDC(0.41)
   stats.SetX2NDC(0.99)
   stats.SetY2NDC(0.84)
   tc.Update()
# data
   tc = hMC['fits'+v].cd(j+5)
   rc = hData[v+'_'+sptCut].Fit(myGauss,'S','',0.5,5.)
   fitResult = rc.Get()
   hData['fitResult'][ptCut] = {}
   for n in range(10):
    hData['fitResult'][ptCut][myGauss.GetParName(n)] = [fitResult.Parameter(n),fitResult.ParError(n)]
   if v=='mcor':
# psi(2S) 
    myGauss.FixParameter(1,fitResult.Parameter(1))
    myGauss.FixParameter(2,fitResult.Parameter(2))
    myGauss.ReleaseParameter(9)
    rc = hData[v+'_'+sptCut].Fit(myGauss,'S','',0.5,5.)
    myGauss.ReleaseParameter(1)
    myGauss.ReleaseParameter(2)
    rc = hData[v+'_'+sptCut].Fit(myGauss,'S','',0.5,5.)
    fitResult = rc.Get()
    hData['fitResult'][ptCut][myGauss.GetParName(9)] = [fitResult.Parameter(9),fitResult.ParError(9)]
   hData['SS-'+v+'_'+sptCut].Draw('same')
   tc.Update()
   stats = tc.GetPrimitive('stats')
   stats.SetOptFit(10011)
   stats.SetFitFormat('5.4g')
   stats.SetX1NDC(0.41)
   stats.SetY1NDC(0.41)
   stats.SetX2NDC(0.99)
   stats.SetY2NDC(0.84)
   tc.Update()
   j+=1
   if j==6: j+=5
   hMC['tMass'].cd()
   hMC['mc-'+v+'_'+sptCut].Draw()
   hMC['SS-mc-'+v+'_'+sptCut].Draw('same')
   myPrint(hMC['tMass'],'mc_dimuon_'+v+sptCut)
   hData[v+'_'+sptCut].Draw()
   hData['SS-'+v+'_'+sptCut].Draw('same')
   myPrint(hMC['tMass'],'m_dimuon_'+v+sptCut)
  hMC['fits'+v].Update()
  myPrint(hMC['fits'+v],v+'_dimuon_all')
#
  param = {0:'Signal',1:'Mass',2:'Sigma'}
  txt   = {0:'; pt>X GeV/c; Nsignal',1:'; pt>X GeV/c; M [GeV/c^{2}]',2:'; pt>X GeV/c; #sigma [GeV/c^{2}]'}
  choices = {'MC':hMC,'Data':hData}
  for c in choices:
   h=choices[c]
   for p in range(3):
    hname = 'evolution'+v+param[p]+c
    ut.bookHist(h,hname,v+' evolution of '+param[p]+txt[p],20,0., 2.)
    for ptCut in ptCutList:
        k = h[hname].FindBin(ptCut)
        h[hname].SetBinContent(k,h['fitResult'][ptCut][myGauss.GetParName(p)][0])
        h[hname].SetBinError(k,h['fitResult'][ptCut][myGauss.GetParName(p)][1])
        k+=1
  ut.bookCanvas(hMC,'evolutionC'+v,'evolution',1600,500,3,1)
  for p in range(3):
   tc = hMC['evolutionC'+v].cd(p+1)
   hname = 'evolution'+v+param[p]
   resetMinMax(hMC[hname+'MC'])
   resetMinMax(hData[hname+'Data'])
   hMC[hname+'MC'].SetLineColor(ROOT.kRed)
   hMC[hname+'MC'].GetXaxis().SetRangeUser(0.9,2.0)
   hData[hname+'Data'].GetXaxis().SetRangeUser(0.9,2.0)
   hMC[hname+'MC'].SetMaximum(1.1*max(hMC[hname+'MC'].GetMaximum(),hData[hname+'Data'].GetMaximum()))
   if p==1: 
        hMC[hname+'MC'].SetMaximum(3.5)
        hMC[hname+'MC'].SetMinimum(2.)
   if p==2: 
        hMC[hname+'MC'].SetMaximum(0.6)
        hMC[hname+'MC'].SetMinimum(0.3)
   hMC[hname+'MC'].Draw()
   hData[hname+'Data'].Draw('same')
  myPrint(hMC['evolutionC'+v],'EvolutionOfCuts_dimuon'+v)
# truth momentum
 ut.bookCanvas(hMC,'kin','Jpsi kinematics',1800,1000,3,2)
 ut.bookHist(hMC, 'pt','pt',100,0.,5.)
 ut.bookHist(hMC, 'ptTrue','pt vs ptTrue',100,0.,5.,100,0.,5.)
 ut.bookHist(hMC, 'pTrue' ,'p vs pTrue',100,0.,400.,100,0.,400.)
 ut.bookHist(hMC, 'delpTrue' ,'pTrue - p',100,-20.,70.)
 ut.bookHist(hMC, 'delptTrue' ,'ptTrue - pt',100,-2.,2.)
 tc = hMC['kin'].cd(1)
 myDraw('p:PTRUE>>pTrue','Jpsi==443')
 myDraw('pt:PtTRUE>>ptTrue','Jpsi==443')
 myDraw('PTRUE-p>>delpTrue','Jpsi==443')
 myDraw('PtTRUE-pt>>delptTrue','Jpsi==443')
 ROOT.gROOT.cd()
 tc = hMC['kin'].cd(1)
 hMC['pTrue'].Draw('colz')
 tc = hMC['kin'].cd(4)
 hMC['delpTrue'].Fit('gaus')
 tc.Update()
 stats = tc.GetPrimitive('stats')
 stats.SetOptFit(10011)
 stats.SetFitFormat('5.4g')
 stats.SetX1NDC(0.50)
 stats.SetY1NDC(0.41)
 stats.SetX2NDC(0.99)
 stats.SetY2NDC(0.84)
 tc.Update()
 tc = hMC['kin'].cd(2)
 hMC['ptTrue'].Draw('colz')
 tc = hMC['kin'].cd(5)
 hMC['delptTrue'].Fit('gaus')
 tc.Update()
 stats = tc.GetPrimitive('stats')
 stats.SetOptFit(10011)
 stats.SetFitFormat('5.4g')
 tc.Update()
 tc = hMC['kin'].cd(3)
 hMC['ptTrue_x']=hMC['ptTrue'].ProjectionX('ptTrue_x')
 hMC['ptTrue_y']=hMC['ptTrue'].ProjectionY('ptTrue_y')
 hMC['pTrue_x']=hMC['pTrue'].ProjectionX('pTrue_x')
 hMC['pTrue_y']=hMC['pTrue'].ProjectionY('pTrue_y')
 hMC['ptTrue_x'].SetLineColor(ROOT.kRed)
 hMC['pTrue_x'].SetLineColor(ROOT.kRed)
 hMC['pTrue_x'].Draw()
 hMC['pTrue_y'].Draw('same')
 tc = hMC['kin'].cd(6)
 hMC['ptTrue_x'].Draw()
 hMC['ptTrue_y'].Draw('same')
 myPrint(hMC['kin'],'JpsiKinematics')
# low mass
 ut.bookCanvas(hMC,'lkin','low mass kinematics',1800,1000,3,2)
 ut.bookHist(hMC, 'lpt','pt',100,0.,5.)
 ut.bookHist(hMC, 'lptTrue','pt vs ptTrue',100,0.,5.,100,0.,5.)
 ut.bookHist(hMC, 'lpTrue' ,'p vs pTrue',100,0.,400.,100,0.,400.)
 ut.bookHist(hMC, 'ldelpTrue' ,'pTrue - p',100,-20.,70.)
 ut.bookHist(hMC, 'ldelptTrue' ,'ptTrue - pt',100,-2.,2.)
 tc = hMC['lkin'].cd(1)
 select=""
 for c in colors:
  if c==443: continue
  select+="||Jpsi=="+str(c)
 select = select[2:]
 myDraw('p:PTRUE>>lpTrue',select)
 myDraw('pt:PtTRUE>>lptTrue',select)
 myDraw('PTRUE-p>>ldelpTrue',select)
 myDraw('PtTRUE-pt>>ldelptTrue',select)
 tc = hMC['lkin'].cd(1)
 hMC['lpTrue'].Draw('colz')
 tc = hMC['lkin'].cd(4)
 hMC['ldelpTrue'].Fit('gaus')
 tc.Update()
 stats = tc.GetPrimitive('stats')
 stats.SetOptFit(10011)
 stats.SetFitFormat('5.4g')
 stats.SetX1NDC(0.50)
 stats.SetY1NDC(0.41)
 stats.SetX2NDC(0.99)
 stats.SetY2NDC(0.84)
 tc.Update()
 tc = hMC['lkin'].cd(2)
 hMC['lptTrue'].Draw('colz')
 tc = hMC['lkin'].cd(5)
 hMC['ldelptTrue'].Fit('gaus')
 tc.Update()
 stats = tc.GetPrimitive('stats')
 stats.SetOptFit(10011)
 stats.SetFitFormat('5.4g')
 tc.Update()
 tc = hMC['lkin'].cd(3)
 hMC['lptTrue_x']=hMC['lptTrue'].ProjectionX('lptTrue_x')
 hMC['lptTrue_y']=hMC['lptTrue'].ProjectionY('lptTrue_y')
 hMC['lpTrue_x']=hMC['lpTrue'].ProjectionX('lpTrue_x')
 hMC['lpTrue_y']=hMC['lpTrue'].ProjectionY('lpTrue_y')
 hMC['lptTrue_x'].SetLineColor(ROOT.kRed)
 hMC['lpTrue_x'].SetLineColor(ROOT.kRed)
 hMC['lpTrue_x'].Draw()
 hMC['lpTrue_y'].Draw('same')
 tc = hMC['lkin'].cd(6)
 hMC['lptTrue_x'].Draw()
 hMC['lptTrue_y'].Draw('same')
 myPrint(hMC['lkin'],'LowMassKinematics')

# muon dEdx
 ut.bookCanvas(hMC,'dEdx','dEdx',1800,1200,1,2)
 tc = hMC['dEdx'].cd(1)
 ut.bookHist(hMC, 'delpTrue2' ,'p-pTrue vs p',40,0.,400.,50,-50.,50.)
 myDraw('(p1-p1True):p1>>delpTrue2','Jpsi==443')
 myDraw('(p2-p2True):p2>>+delpTrue2','Jpsi==443') # applying cuts does not make a difference
 ROOT.gROOT.cd()
 hMC['meanLoss']=hMC['delpTrue2'].ProjectionX('meanLoss')
 for n in range(1,hMC['delpTrue2'].GetXaxis().GetNbins()+1):
   tmp = hMC['delpTrue2'].ProjectionY('tmp',n,n)
   # hMC['meanLoss'].SetBinContent(n, tmp.GetBinCenter(ut.findMaximumAndMinimum(tmp)[3]))
   hMC['meanLoss'].SetBinContent(n, tmp.GetMean())
   hMC['meanLoss'].SetBinError(n,tmp.GetRMS())
 hMC['meanLoss'].Draw()  #-8.61544 
 tc =hMC['dEdx'].cd(2)
 ut.bookHist(hMC, 'delp' ,'p-pTrue',50,-50.,50.)
 hMC['delpFunOfPtCut']=ROOT.TGraph()
 dp = 0.1
 ptCut = 0.0
 for k in range(20):
  myDraw('(p1-p1True)>>delp','Jpsi==443&&pt1>'+str(ptCut+dp/2.)+'&&pt1<'+str(ptCut-dp/2.))
  myDraw('(p2-p2True)>>+delp','Jpsi==443&&pt2>'+str(ptCut+dp/2.)+'&&pt1<'+str(ptCut-dp/2.))
  dE = hMC['delp'].GetMean()
  hMC['delpFunOfPtCut'].SetPoint(k,ptCut,dE)
  ptCut+=dp
 ut.bookHist(hMC, 'delpt' ,'delpt',20,0.,2.)
 hMC['delpt'].SetMaximum(0.0)
 hMC['delpt'].SetMinimum(-10.0)
 hMC['delpt'].Draw()
 hMC['delpFunOfPtCut'].Draw()
# -7.97  -1.52 * ptCut + 0.93 * ptCut**2


# try Jpsi p,pt based on ptmu > 1.4
 v='mcor'
 ptCut = 1.4
 sptCut = str(ptCut)
 theCut =  theCutTemplate.replace('XYZ',sptCut)
 ut.bookHist(hMC, 'mc-JpsiPt','Pt J/#psi ;Pt [GeV/c^{2}]',10,0.,5.)
 ut.bookHist(hData, 'JpsiPt','Pt J/#psi ;Pt [GeV/c^{2}]',10,0.,5.)
 ut.bookCanvas(hMC,'MCbinsPt','mass in bins Pt',1800,1200,3,3)
 ut.bookCanvas(hData,'binsPt','mass in bins Pt',1800,1200,3,3)
 ptmin = 0
 delPt = 0.5
 for k in range(9):
   ptmax = ptmin+delPt
   ut.bookHist(hMC,  'mc-pt'+str(k),'inv mass MC '+str(ptmin)+'<Pt<'+str(ptmax)+';M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   ut.bookHist(hData,'pt'+str(k),'inv mass DATA ' +str(ptmin)+'<Pt<'+str(ptmax)+';M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   hMC['dummy'].cd()
   sTreeData.Draw(v+'>>pt'+str(k),theCut+'&&pt<'+str(ptmax)+'&&pt>'+str(ptmin))
   myDraw(v+'>>mc-pt'+str(k),theCut+'&&pt<'+str(ptmax)+'&&pt>'+str(ptmin))
   ptmin = ptmin+delPt
   cases = {'MC':hMC['mc-pt'+str(k)],'Data':hData['pt'+str(k)]}
   for c in cases:
    histo = cases[c]
    if c=='MC': tc=hMC['MCbinsPt'].cd(k+1)
    else: tc=hData['binsPt'].cd(k+1)
    init_Gauss(myGauss)
    histo.Draw()
    rc = histo.Fit(myGauss,'S','',0.5,5.)
    fitResult = rc.Get()
    N = fitResult.Parameter(0)
    E = fitResult.ParError(0)
    tc.Update()
    stats = tc.GetPrimitive('stats')
    stats.SetOptFit(10011)
    stats.SetFitFormat('5.4g')
    stats.SetX1NDC(0.41)
    stats.SetY1NDC(0.41)
    stats.SetX2NDC(0.99)
    stats.SetY2NDC(0.84)
    tc.Update()
    if c=='MC': 
        hMC['mc-JpsiPt'].SetBinContent(k+1,N)
        hMC['mc-JpsiPt'].SetBinError(k+1,E)
    else: 
        hData['JpsiPt'].SetBinContent(k+1,N)
        hData['JpsiPt'].SetBinError(k+1,E)
 myPrint(hData['binsPt'],'diMuonBinsPt')
 myPrint(hMC['MCbinsPt'],'MC-diMuonBinsPt')
 hMC['dummy'].cd()
 hMC['mc-JpsiPt'].SetLineColor(ROOT.kMagenta)
 hmax = 1.1*max(hMC['mc-JpsiPt'].GetMaximum(),hData['JpsiPt'].GetMaximum())
 hMC['mc-JpsiPt'].SetMaximum(hmax)
 hMC['mc-JpsiPt'].Draw()
 hData['JpsiPt'].Draw('same')
 myPrint(hMC['dummy'],'diMuonBinsPtSummary')
#
 ut.bookHist(hMC, 'mc-JpsiP','J/#psi ;P [GeV/c^{2}]',10,20.,220.)
 ut.bookHist(hData, 'JpsiP',' J/#psi ;Pt [GeV/c^{2}]',10,20.,220.)
 ut.bookCanvas(hMC,'MCbinsP','mass in bins P',1800,1200,3,3)
 ut.bookCanvas(hData,'binsP','mass in bins P',1800,1200,3,3)
 pmin = 20.
 delP = 20.
 for k in range(9):
   pmax = pmin+delP
   ut.bookHist(hMC,  'mc-p'+str(k),'inv mass MC '+str(pmin)+'<P<'+str(pmax)+';M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   ut.bookHist(hData,'p'+str(k),'inv mass DATA ' +str(pmin)+'<P<'+str(pmax)+';M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2])
   hMC['dummy'].cd()
   sTreeData.Draw(v+'>>p'+str(k),theCut+'&&p<'+str(pmax)+'&&p>'+str(pmin))
   myDraw(v+'>>mc-p'+str(k),theCut+'&&p<'+str(pmax)+'&&p>'+str(pmin))
   pmin = pmin+delP
   cases = {'MC':hMC['mc-p'+str(k)],'Data':hData['p'+str(k)]}
   for c in cases:
    histo = cases[c]
    if c=='MC': tc=hMC['MCbinsP'].cd(k+1)
    else: tc=hData['binsP'].cd(k+1)
    init_Gauss(myGauss)
    histo.Draw()
    rc = histo.Fit(myGauss,'S','',0.5,5.)
    fitResult = rc.Get()
    if fitResult and histo.GetEntries()>10:
     N = fitResult.Parameter(0)
     E = fitResult.ParError(0)
     tc.Update()
     stats = tc.GetPrimitive('stats')
     stats.SetOptFit(10011)
     stats.SetFitFormat('5.4g')
     stats.SetX1NDC(0.41)
     stats.SetY1NDC(0.41)
     stats.SetX2NDC(0.99)
     stats.SetY2NDC(0.84)
     tc.Update()
    else:
     N=0
     E=0
    if E>N:
     N=0
     E=0
    if c=='MC': 
        hMC['mc-JpsiP'].SetBinContent(k+1,N)
        hMC['mc-JpsiP'].SetBinError(k+1,E)
    else:
        hData['JpsiP'].SetBinContent(k+1,N)
        hData['JpsiP'].SetBinError(k+1,E)

 myPrint(hData['binsP'],'diMuonBinsP')
 myPrint(hMC['MCbinsP'],'MC-diMuonBinsP')
 hMC['dummy'].cd(1)
 hMC['mc-JpsiP'].SetLineColor(ROOT.kMagenta)
 hmax = 1.1*max(hMC['mc-JpsiP'].GetMaximum(),hData['JpsiP'].GetMaximum())
 hMC['mc-JpsiP'].SetMaximum(hmax)
 hMC['mc-JpsiP'].Draw()
 hData['JpsiP'].Draw('same')
 myPrint(hMC['dummy'],'diMuonBinsPSummary')
# low mass in bins of p and pt
 ut.bookHist(hMC, 'mc-lowMassppt','low mass pt vs p;p [GeV/c];p_{t} [GeV/c]',50,0.,400.,50,0.,5.)
 ut.bookHist(hData, 'lowMassppt','low mass pt vs p;p [GeV/c];p_{t} [GeV/c]',50,0.,400.,50,0.,5.)
 sptCut = '0'
 theCut =  '('+sptCut+'<pt1||'+sptCut+'<pt2)&&chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&p1>20&&p2>20'
 ut.bookHist(hMC, 'mc-lowMassAll','low mass ;M [GeV/c^[2]]',100,0.,5.)
 ut.bookHist(hData, 'lowMassAll', 'low mass ;M [GeV/c^[2]]',100,0.,5.)
 myDraw('mcor>>mc-lowMassAll',theCut)
 sTreeData.Draw('mcor>>lowMassAll',theCut)
 hMC['mc-lowMassAll'].Scale(1./hMC['weights']['10GeV'])
 tc=hMC['dummy'].cd()
 hMC['mc-lowMassAll'].SetLineColor(ROOT.kMagenta)
 hData['lowMassAll'].Draw()
 hMC['mc-lowMassAll'].Draw('same')
 myPrint(hMC['dummy'],'lowMassAll')
 theCut =  '('+sptCut+'<pt1||'+sptCut+'<pt2)&&chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&p1>20&&p2>20&&mcor>0.4&&mcor<2.0'
 myDraw('pt:p>>mc-lowMassppt',theCut)
 sTreeData.Draw('pt:p>>lowMassppt',theCut)
 hMC['mc-lowMassppt'].Scale(1./hMC['weights']['10GeV'])
 ut.bookCanvas(hData,'lowMass','lowMass summary',1600,1200,1,2)
 hData['lowMass1'] = hData['lowMass'].cd(1)
 hData['lowMass1'].Divide(2,1)
 tc = hData['lowMass1'].cd(1)
 tc.SetLogy(1)
 hData['lowMassppt_projx'] = hData['lowMassppt'].ProjectionX('lowMassppt_projx')
 hData['lowMassppt_projx'].GetXaxis().SetRangeUser(40.,400.)
 hData['lowMassppt_projx'].SetStats(0)
 hData['lowMassppt_projx'].SetTitle('')
 hData['lowMassppt_projx'].Draw()
 hMC['mc-lowMassppt_projx'] = hMC['mc-lowMassppt'].ProjectionX('mc-lowMassppt_projx')
 hMC['mc-lowMassppt_projx'].SetLineColor(ROOT.kMagenta)
 hMC['mc-lowMassppt_projx'].Draw('same')
 tc = hData['lowMass1'].cd(2)
 tc.SetLogy(1)
 hData['lowMassppt_projy'] = hData['lowMassppt'].ProjectionY('lowMassppt_projy')
 hData['lowMassppt_projy'].SetStats(0)
 hData['lowMassppt_projy'].SetTitle('')
 hData['lowMassppt_projy'].Draw()
 hMC['mc-lowMassppt_projy'] = hMC['mc-lowMassppt'].ProjectionY('mc-lowMassppt_projy')
 hMC['mc-lowMassppt_projy'].SetLineColor(ROOT.kMagenta)
 hMC['mc-lowMassppt_projy'].Draw('same')
 hMC['mc-ratioLowMass'] = hMC['mc-lowMassppt'].Clone('mc-ratioLowMass')
 hData['ratioLowMass']  = hData['lowMassppt'].Clone('ratioLowMass')
 hMC['mc-ratioLowMass'].Rebin2D(5,5)
 hData['ratioLowMass'].Rebin2D(5,5)
 asymVersion = False
 for mx in range(1,hMC['mc-ratioLowMass'].GetNbinsX()+1):
  for my in range(1,hMC['mc-ratioLowMass'].GetNbinsY()+1):
    Nmc = hMC['mc-ratioLowMass'].GetBinContent(mx,my)
    Nda = hData['ratioLowMass'].GetBinContent(mx,my)
    eNmc = hMC['mc-ratioLowMass'].GetBinError(mx,my)
    eNda = hData['ratioLowMass'].GetBinError(mx,my)
    if Nmc>10 and Nda>10:
         if asymVersion:
          R = (Nda-Nmc)/(Nda+Nmc)
          sig_data = ROOT.TMath.Sqrt(eNda**2+(Nda*daSysError)**2)
          sig_MC   = ROOT.TMath.Sqrt(eNmc**2+(Nmc*mcSysError)**2)
          e1 = 2*Nda/(Nda+Nmc)**2
          e2 = 2*Nmc/(Nda+Nmc)**2
          eR = ROOT.TMath.Sqrt( (e1*sig_MC)**2+(e2*sig_data)**2 )
         else: # ratio  version
          R = (Nda/Nmc)
          eR = ROOT.TMath.Sqrt( (R/Nmc*eNmc)**2+(R/Nda*eNda)**2 )
    else:      
         R  = 0. # -1      # R = 0
         eR = 0.
    hData['ratioLowMass'].SetBinContent(mx,my,R)
    hData['ratioLowMass'].SetBinError(mx,my,eR)
 tc = hData['lowMass'].cd(2)
 ROOT.gStyle.SetPaintTextFormat("5.2f")
 hData['ratioLowMass'].GetXaxis().SetRangeUser(40.,400.)
 hData['ratioLowMass'].SetStats(0)
 if asymVersion: hData['ratioLowMass'].SetTitle('data - MC / data + MC')
 else: hData['ratioLowMass'].SetTitle('data/MC')
 hData['ratioLowMass'].GetYaxis().SetRangeUser(0,3.)
 hData['ratioLowMass'].SetMarkerSize(1.8)
 hData['ratioLowMass'].Draw('texte')
 myPrint(hData['lowMass'],'lowMassSummary')

import math
def init_twoCB(myCB,bw,ptCut,h,fromPrevFit=False):
   myCB.FixParameter(0,bw)
   myCB.SetParName(0,'binwidth')
   myCB.SetParName(1,'psi(1S)')
   myCB.SetParName(2,'Mass')
   myCB.SetParName(3,'Sigma')
   myCB.SetParName(4,'alpha')
   myCB.SetParName(5,'n')
   myCB.SetParName(6,'SignalLow')
   myCB.SetParName(7,'MeanLow')
   myCB.SetParName(8,'SigmaLow')
   myCB.SetParName(9,'alphaLow')
   myCB.SetParName(10,'nLow')
   myCB.SetParName(11,'p0')
   myCB.SetParName(12,'p1')
   myCB.SetParName(13,'psi(2S)')
   if not fromPrevFit:
    myCB.SetParameter(1,h['fitResult'][ptCut]['psi(1S)'][0])
    myCB.SetParameter(2,h['fitResult'][ptCut]['Mean'][0])
    myCB.SetParameter(3,h['fitResult'][ptCut]['Sigma'][0])
    myCB.SetParameter(4,0.3)
    myCB.SetParameter(5,3.5)
    myCB.SetParameter(6,h['fitResult'][ptCut]['SignalLow'][0])
    myCB.SetParameter(7,h['fitResult'][ptCut]['MeanLow'][0])
    myCB.SetParameter(8,h['fitResult'][ptCut]['SigmaLow'][0])
    myCB.SetParameter(9,0.3)
    myCB.SetParameter(10,3.5)
    myCB.SetParameter(11,h['fitResult'][ptCut]['p1'][0])
    myCB.SetParameter(12,h['fitResult'][ptCut]['p2'][0])
    myCB.FixParameter(13,0.)
   else:
    myCB.SetParameter(1,h['fitResultCB'][ptCut]['psi(1S)'][0])
    myCB.SetParameter(2,h['fitResultCB'][ptCut]['Mass'][0])
    myCB.FixParameter(3,h['fitResultCB'][ptCut]['Sigma'][0])
    myCB.FixParameter(4,h['fitResultCB'][ptCut]['alpha'][0])
    myCB.FixParameter(5,h['fitResultCB'][ptCut]['n'][0])
    myCB.SetParameter(6,h['fitResultCB'][ptCut]['SignalLow'][0])
    myCB.SetParameter(7,h['fitResultCB'][ptCut]['MeanLow'][0])
    myCB.FixParameter(8,h['fitResultCB'][ptCut]['SigmaLow'][0])
    myCB.FixParameter(9,h['fitResultCB'][ptCut]['alphaLow'][0])
    myCB.FixParameter(10,h['fitResultCB'][ptCut]['nLow'][0])
    myCB.SetParameter(11,h['fitResultCB'][ptCut]['p0'][0])
    myCB.SetParameter(12,h['fitResultCB'][ptCut]['p1'][0])
    myCB.FixParameter(12,0.)
    myCB.FixParameter(13,0.)
    myCB.ReleaseParameter(2)
    myCB.ReleaseParameter(7)

def fitWithTwoCB():
 hMC['dummy'].cd()
 ptCutList = [0.0,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6]
 bw = hMC['m_MC'].GetBinWidth(1)
 cases = {'':hData,'mc-':hMC}
 v = 'mcor'
 for c in cases:
  h=cases[c]
  h['fitResultCB']={}
  for ptCut in ptCutList:
   h['myCB2'+str(ptCut)+c] = ROOT.TF1('2CB'+str(ptCut)+c,TwoCrystalBall,0,10,14)
   myCB = h['myCB2'+str(ptCut)+c]
   init_twoCB(myCB,bw,ptCut,h)
   hname = c+v+'_'+str(ptCut)
   print "+++++ Fit",hname
   myCB.FixParameter(9,10.) # alpha positive and large -> gauss part only
   myCB.FixParameter(5,10.) # alpha positive and large -> gauss part only
   rc = h[hname].Fit(myCB,'S','',0.5,5.)
   myCB.ReleaseParameter(5)
   rc = h[hname].Fit(myCB,'SE','',0.5,5.)
   myCB.ReleaseParameter(9)
   rc = h[hname].Fit(myCB,'SE','',0.5,5.)
   fitResult=rc.Get()
   if math.isnan(fitResult.ParError(1)) or math.isnan(fitResult.ParError(6)):
      myCB.FixParameter(4,10.)
      rc = h[hname].Fit(myCB,'S','',0.5,5.)
      myCB.ReleaseParameter(4)
      rc = h[hname].Fit(myCB,'SE','',0.5,5.)
      fitResult=rc.Get()
      if math.isnan(fitResult.ParError(1)) or math.isnan(fitResult.ParError(6)):
        myCB.FixParameter(4,10.)
        rc = h[hname].Fit(myCB,'SE','',0.5,5.)
        fitResult=rc.Get()
   h['fitResultCB'][ptCut]={}
   for n in range(1,13):
       h['fitResultCB'][ptCut][myCB.GetParName(n)] = [fitResult.Parameter(n),fitResult.ParError(n)]
   myCB.ReleaseParameter(13)
   rc = h[hname].Fit(myCB,'SE','',0.5,5.)
   fitResult=rc.Get()
   n=13
   h['fitResultCB'][ptCut][myCB.GetParName(n)] = [fitResult.Parameter(n),fitResult.ParError(n)]
   myCB.FixParameter(13,0.)
   rc = h[hname].Fit(myCB,'SE','',0.5,5.)
 for j in range(1,21): hMC['fits'+v].cd(j).Update()
 hMC['fits'+v].Update()
 myPrint(hMC['fits'+v],v+'_CBdimuon_all')
# p/pt
# try Jpsi p,pt based on ptmu > 1.4
 hMC['dummy'].cd()
 for k in range(9):
   cases = {'MC':hMC['mc-pt'+str(k)],'Data':hData['pt'+str(k)]}
   for c in cases:
    histo = cases[c]
    if c=='MC': tc=hMC['MCbinsPt'].cd(k+1)
    else: tc=hData['binsPt'].cd(k+1)
    init_twoCB(myCB,bw,ptCut,h,True)
    rc = histo.Fit(myCB,'S','',0.5,5.)
    fitResult = rc.Get()
    if fitResult and histo.GetEntries()>10 and fitResult.Parameter(2)<4.:
     N = fitResult.Parameter(1)
     E = fitResult.ParError(1)
     tc.Update()
     stats = tc.GetPrimitive('stats')
     stats.SetOptFit(10011)
     stats.SetFitFormat('5.4g')
     stats.SetX1NDC(0.41)
     stats.SetY1NDC(0.41)
     stats.SetX2NDC(0.99)
     stats.SetY2NDC(0.84)
     tc.Update()
     if c=='MC': 
        hMC['mc-JpsiPt'].SetBinContent(k+1,N)
        hMC['mc-JpsiPt'].SetBinError(k+1,E)
     else: 
        hData['JpsiPt'].SetBinContent(k+1,N)
        hData['JpsiPt'].SetBinError(k+1,E)
 myPrint(hData['binsPt'],'diMuonBinsPtCB')
 myPrint(hMC['MCbinsPt'],'MC-diMuonBinsPtCB')
 hMC['mc-JpsiPt'].SetLineColor(ROOT.kMagenta)
 hMC['mc-JpsiPt_scaled']=hMC['mc-JpsiPt'].Clone('mc-JpsiPt_scaled')
 hMC['mc-JpsiPt_scaled'].Scale(1./hMC['mc-JpsiP'].GetSumOfWeights())
 hData['JpsiPt_scaled']=hData['JpsiPt'].Clone('JpsiPt_scaled')
 hData['JpsiPt_scaled'].Scale(1./hData['JpsiPt'].GetSumOfWeights())
 hmax = 1.1*max(ut.findMaximumAndMinimum(hData['JpsiPt_scaled'])[1],ut.findMaximumAndMinimum(hMC['mc-JpsiPt_scaled'])[1])
 hData['JpsiPt_scaled'].SetMaximum(hmax)
 hMC['dummy'].cd()
 hData['JpsiPt_scaled'].Draw()
 hMC['mc-JpsiPt_scaled'].Draw('same')
 myPrint(hMC['dummy'],'diMuonBinsPtCBSummary')
#
 for k in range(9):
   cases = {'MC':hMC['mc-p'+str(k)],'Data':hData['p'+str(k)]}
   for c in cases:
    histo = cases[c]
    if c=='MC': tc=hMC['MCbinsP'].cd(k+1)
    else: tc=hData['binsP'].cd(k+1)
    init_twoCB(myCB,bw,ptCut,h,True)
    rc = histo.Fit(myCB,'S','',0.5,5.)
    fitResult = rc.Get()
    if fitResult and histo.GetEntries()>10 and fitResult.Parameter(2)<4.:
     N = fitResult.Parameter(1)
     E = fitResult.ParError(1)
     tc.Update()
     stats = tc.GetPrimitive('stats')
     stats.SetOptFit(10011)
     stats.SetFitFormat('5.4g')
     stats.SetX1NDC(0.41)
     stats.SetY1NDC(0.41)
     stats.SetX2NDC(0.99)
     stats.SetY2NDC(0.84)
     tc.Update()
    else:
     N=0
     E=0
    if E>N:
     N=0
     E=0
    if c=='MC': 
        hMC['mc-JpsiP'].SetBinContent(k+1,N)
        hMC['mc-JpsiP'].SetBinError(k+1,E)
    else: 
        hData['JpsiP'].SetBinContent(k+1,N)
        hData['JpsiP'].SetBinError(k+1,E)
 myPrint(hData['binsP'],'diMuonBinsPCB')
 myPrint(hMC['MCbinsP'],'MC-diMuonBinsPCB')
 hMC['mc-JpsiP'].SetLineColor(ROOT.kMagenta)
 hMC['mc-JpsiP_scaled']=hMC['mc-JpsiP'].Clone('mc-JpsiP_scaled')
 hMC['mc-JpsiP_scaled'].Scale(1./hMC['mc-JpsiP'].GetSumOfWeights())
 hData['JpsiP_scaled']=hData['JpsiP'].Clone('JpsiP_scaled')
 hData['JpsiP_scaled'].Scale(1./hData['JpsiP'].GetSumOfWeights())
 hmax = 1.1*max(ut.findMaximumAndMinimum(hData['JpsiP_scaled'])[1],ut.findMaximumAndMinimum(hMC['mc-JpsiP_scaled'])[1])
 hData['JpsiP_scaled'].SetMaximum(hmax)
 hMC['dummy'].cd()
 hData['JpsiP_scaled'].Draw()
 hMC['mc-JpsiP_scaled'].Draw('same')
 myPrint(hMC['dummy'],'diMuonBinsPCBSummary')
# make ratio data / mc with lumi weighted:
 hData['ratios']={}
 for ptCut in ptCutList:
   hData['ratios'][ptCut]={}
   for fit in ['','CB']:
    hData['ratios'][ptCut][fit]={}
    for M in ['psi(1S)','SignalLow']:
     N = hData['fitResult'+fit][ptCut][M][0]
     E = hData['fitResult'+fit][ptCut][M][1]
     fudgeFactor = 1.
     if M=='psi(1S)': fudgeFactor = (1.+jpsiCascadeContr)
     MCN = hMC['fitResult'+fit][ptCut][M][0]*fudgeFactor
     MCE = hMC['fitResult'+fit][ptCut][M][1]*fudgeFactor
# '10GeV':MCStats['10GeV']/dataStats/(1+simpleEffCor*2)
     R = N/MCN * hMC['weights']['10GeV']
     ER = ROOT.TMath.Sqrt( (R/N*E)**2 + (R/MCN*MCE)**2)
     hData['ratios'][ptCut][fit][M]=[R,ER]
 for M in ['psi(1S)','SignalLow']:
    print "results for ",M
    for ptCut in ptCutList:
      r = "%5.2F +/- %5.2F"%(hData['ratios'][ptCut][''][M][0],hData['ratios'][ptCut][''][M][1])
      rCB = "%5.2F +/- %5.2F"%(hData['ratios'][ptCut]['CB'][M][0],hData['ratios'][ptCut]['CB'][M][1])
      print "Ratio Data/MC with pt cut %3.2F: gauss  %s  crystalball %s"%(ptCut,r,rCB)
 print "results for mass difference Jpsi low"
 cases = {'':hData,'mc-':hMC}
 for c in cases:
   h=cases[c]
   h['delm']={}
   for ptCut in ptCutList:
     h['delm'][ptCut]={}
     for fit in ['','CB']:
       m = 'Mass'
       if fit=='': m = "Mean"
       Delm  = h['fitResult'+fit][ptCut][m][0] - h['fitResult'+fit][ptCut]['MeanLow'][0]
       eDelm = ROOT.TMath.Sqrt(h['fitResult'+fit][ptCut][m][1]**2+h['fitResult'+fit][ptCut]['MeanLow'][1]**2)
       h['delm'][ptCut][fit]=[Delm,eDelm]
 for ptCut in ptCutList:
    r1 = "%5.2F +/- %5.2F"%(hData['delm'][ptCut][''][0],hData['delm'][ptCut][''][1])
    r2 = "%5.2F +/- %5.2F"%(hData['delm'][ptCut]['CB'][0],hData['delm'][ptCut]['CB'][1])
    r3 = "%5.2F +/- %5.2F"%(hMC['delm'][ptCut][''][0],hMC['delm'][ptCut][''][1])
    r4 = "%5.2F +/- %5.2F"%(hMC['delm'][ptCut]['CB'][0],hMC['delm'][ptCut]['CB'][1])
    print "Dm high-low pt cut: %3.2F: gauss  %s  crystalball %s ||MC gauss  %s  crystalball %s  "%(ptCut,r1,r2,r3,r4)
 ptCut = 1.4
 fit = 'CB'
 m = 'Mass'
 for c in cases:
   h=cases[c]
   print "Jpsi mass measured - PDG %5s %5.3F +/-%5.3F "%(c,h['fitResult'+fit][ptCut][m][0]-3.0969,h['fitResult'+fit][ptCut][m][1])
 v = "mcor"
 param = {1:'Signal',2:'Mass',3:'Sigma'}
 txt   = {1:'; pt>X GeV/c; Nsignal',2:'; pt>X GeV/c; M [GeV/c^{2}]',3:'; pt>X GeV/c; #sigma [GeV/c^{2}]'}
 choices = {'MC':hMC,'Data':hData}
 for c in choices:
   h=choices[c]
   for p in range(1,4):
    hname = 'evolutionCB'+v+param[p]+c
    ut.bookHist(h,hname,v+' evolution of '+param[p]+txt[p],20,0., 2.)
    for ptCut in ptCutList:
        k = h[hname].FindBin(ptCut)
        h[hname].SetBinContent(k,h['fitResultCB'][ptCut][myCB.GetParName(p)][0])
        h[hname].SetBinError(k,h['fitResultCB'][ptCut][myCB.GetParName(p)][1])
        k+=1
 for p in range(1,4):
   tc = hMC['evolutionC'+v].cd(p)
   hname = 'evolutionCB'+v+param[p]
   resetMinMax(hMC[hname+'MC'])
   resetMinMax(hData[hname+'Data'])
   hMC[hname+'MC'].SetLineColor(ROOT.kRed)
   hMC[hname+'MC'].GetXaxis().SetRangeUser(0.9,2.0)
   hData[hname+'Data'].GetXaxis().SetRangeUser(0.9,2.0)
   hMC[hname+'MC'].SetMaximum(1.1*max(hMC[hname+'MC'].GetMaximum(),hData[hname+'Data'].GetMaximum()))
   if p==2: 
        hMC[hname+'MC'].SetMaximum(3.5)
        hMC[hname+'MC'].SetMinimum(3.)
   if p==3: 
        hMC[hname+'MC'].SetMaximum(0.4)
        hMC[hname+'MC'].SetMinimum(0.3)
   hMC[hname+'MC'].Draw()
   hData[hname+'Data'].Draw('same')
 myPrint(hMC['evolutionC'+v],'EvolutionOfCuts_dimuonCB'+v)

# now in bins of pt
# not needed, generated and reconstructed look the same


def MCmigration():
 sptCut = '1.4'
 theCutTemplate =  '('+sptCut+'<pt1||'+sptCut+'<pt2)&&chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&p1<200&&p2<200&&p1>20&&p2>20&&mcor>0.5'
 Nbins = 25
 ut.bookHist(hMC, 'pMigration' ,'p vs pTrue',Nbins,0.,400.,Nbins,0.,400.)
 tc = hMC['kin'].cd(1)
 myDraw('p:PTRUE>>pTrue',theCutTemplate+'&&Jpsi==443') # x axis = Ptrue, y axis Preco
 hMC['pRec'] = hMC['pMigration'].ProjectionY('pRec')
 hMC['pTRUE'] = hMC['pMigration'].ProjectionX('pTRUE')
 Prec2True = {}
 for j in range(1,Nbins+1):
  tmp = hMC['pMigration'].ProjectionX(str(j),j,j)
  if tmp.GetEntries()>0: tmp.Scale(1./tmp.GetEntries())
  Prec2True[j]={}
  for l in range(1,Nbins+1): Prec2True[j][l]=tmp.GetBinContent(l)
# cross check
 ut.bookHist(hMC, 'ptrueTest' ,'pTrue from pRec',Nbins,0.,400.)
 for j in range(1,Nbins):
    nRec = hMC['pRec'].GetBinContent(j)
    eRec = hMC['pRec'].GetBinError(j)
    for l in range(1,Nbins+1):
      nTrue = nRec*Prec2True[j][l]
      eTrue = (nRec*eRec)**2
      N,E = hMC['ptrueTest'].GetBinContent(l),hMC['ptrueTest'].GetBinError(l)
      rc = hMC['ptrueTest'].SetBinContent(l,N+nTrue)
      rc = hMC['ptrueTest'].SetBinError(l,E+eTrue)
 for l in range(1,Nbins+1):
   eTrue = (nRec*eRec)**2
   E = hMC['ptrueTest'].GetBinContent(l)
   rc = hMC['ptrueTest'].SetBinError(l,ROOT.TMath.Sqrt(E))


def fitWithCB():
 hMC['myCB'] = ROOT.TF1('CB',CrystalBall,0,10,11)
 myCB = hMC['myCB']
 myCB.SetParName(0,'binwidth')
 myCB.SetParName(1,'psi(1S)')
 myCB.SetParName(2,'Mass')
 myCB.SetParName(3,'Sigma')
 myCB.SetParName(4,'alpha')
 myCB.SetParName(5,'n')
 myCB.SetParName(6,'SignalLow')
 myCB.SetParName(7,'MeanLow')
 myCB.SetParName(8,'SigmaLow')
 myCB.SetParName(9,'p0')
 myCB.SetParName(10,'p1')
 hMC['dummy'].cd()
 ptCutList = [0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6]
 bw = hMC['m_MC'].GetBinWidth(1)
 myCB.FixParameter(0,bw)
 cases = {'':hData,'mc-':hMC}
 for c in cases:
  h=cases[c]
  h['fitResultCB']={}
  for ptCut in ptCutList:
   myCB.SetParameter(1,h['fitResult'][ptCut]['psi(1S)'][0])
   myCB.SetParameter(2,h['fitResult'][ptCut]['Mean'][0])
   myCB.SetParameter(3,h['fitResult'][ptCut]['Sigma'][0])
   myCB.SetParameter(4,0.3)
   myCB.SetParameter(5,3.5)
   myCB.SetParameter(6,h['fitResult'][ptCut]['SignalLow'][0])
   myCB.SetParameter(7,h['fitResult'][ptCut]['MeanLow'][0])
   myCB.SetParameter(8,h['fitResult'][ptCut]['SigmaLow'][0])
   myCB.SetParameter(9,h['fitResult'][ptCut]['p1'][0])
   myCB.SetParameter(10,h['fitResult'][ptCut]['p2'][0])
   hname = c+'mcor_'+str(ptCut)
   rc = h[hname].Fit(myCB,'S','',0.5,6.)
   fitResult=rc.Get()
   h['fitResultCB'][ptCut] = []
   for n in range(1,11):
      h['fitResultCB'][ptCut][myCB.GetParName(n)] = [fitResult.Parameter(n),fitResult.ParError(n)]
def resetMinMax(x):
  x.SetMinimum(-1111)
  x.SetMaximum(-1111)
def plotOccupancy(sTree):
    ut.bookHist(h,'upStreamOcc',"station 1&2 function of track mom",50,-0.5,199.5,100,0.,500.)
    for n in range(sTree.GetEntries()):
        rc = sTree.GetEvent(n)
        for k in range(len(sTree.GoodTrack)):
            if sTree.GoodTrack[k]<0: continue
            p=ROOT.TVector3(sTree.Px[k],sTree.Py[k],sTree.Pz[k])
            occ = sTree.stationOcc[1]+sTree.stationOcc[2]+sTree.stationOcc[5]+sTree.stationOcc[6]
            rc=h['upStreamOcc'].Fill(occ,p.Mag())

myExpo = ROOT.TF1('expo','abs([0])*exp(-abs([1]*x))+abs([2])*exp(-abs([3]*x))+[4]',5)
myExpo.SetParName(0,'Signal1')
myExpo.SetParName(1,'tau1')
myExpo.SetParName(2,'Signal2')
myExpo.SetParName(3,'tau2')
myExpo.SetParName(4,'const')

def myPrint(obj,name):
    obj.Print(name+'.pdf')
    obj.Print(name+'.png')

def fitExpo(h,hname):
    myExpo.SetParameter(0,12.)
    myExpo.SetParameter(1,-0.027)
    myExpo.FixParameter(2,0.)
    myExpo.FixParameter(3,-0.030)
    myExpo.SetParameter(4,1.)
    rc = h[hname].Fit(myExpo,'S','',250.,500.)
    fitresult = rc.Get()
    back = fitresult.Parameter(4)
    hnameb=hname+'_backsubtr'
    h[hnameb]= h[hname].Clone(hnameb)
    for n in range(1,h[hname].GetNbinsX()+1):
        h[hnameb].SetBinContent(n,h[hname].GetBinContent(n)-back)

def studyGhosts():
    sTree = sTreeMC
    h = hMC
    ut.bookHist(h,'gfCurv',             'ghost fraction vs curvature',100,0.,100.,100,0.,0.1)
    ut.bookHist(h,'gf',             'ghost fraction',100,0.,100.,100,0.,500.)
    ut.bookHist(h,'gftrue',         'ghost fraction',100,0.,100.,100,0.,500.)
    ut.bookHist(h,'gfDiff',         'ghost fraction vs reco - true mom',100,0.,100.,500,0.,500.)
    ut.bookHist(h,'RPCMatch',       'RPC matching no ghost',100,0.,10.,100,0.,10.)
    ut.bookHist(h,'RPCMatch_ghosts','RPC matching ghost>33',100,0.,10.,100,0.,10.)
    ut.bookHist(h,'R','rpc match',100,0.,100.,100,0.,10.)
    ut.bookHist(h,'Chi2/DoF','Chi2/DoF',100,0.,100.,100,0.,5.)
    ut.bookHist(h,'DoF','DoF',100,0.,100.,30,0.5,30.5)
    for n in range(sTree.GetEntries()):
        if n%500000==0:
            curFile = sTree.GetCurrentFile().GetName()
            tmp = curFile.split('/')
            print "now at event ",n,tmp[len(tmp)-2],'/',tmp[len(tmp)-1],time.ctime()
        rc = sTree.GetEvent(n)
        if not sTreeMC.FindBranch("MCghostfraction") : continue
        for k in range(sTree.nTr):
            muTagged  = False
            muTaggedX = False
            clone     = False
            if sTree.GoodTrack[k]<0: continue
            if sTree.GoodTrack[k]%2==1:
                muTaggedX = True
                if int(sTree.GoodTrack[k]/10)%2==1: muTagged = True
            if sTree.GoodTrack[k]>999:  clone = True
            if clone: continue
            if not muTagged: continue
            gf    = sTree.MCghostfraction[k]*100
            R = (sTree.Dely[k]/3.)**2+(sTree.Delx[k]/1.5)**2
            rc =   h['Chi2/DoF'].Fill(gf,sTree.Chi2[k])
            rc = h['DoF'].Fill(gf,sTree.nDoF[k])
            rc = h['R'].Fill(gf,R)
            # if R>5: continue
            if gf<1:  
                rc =   h['RPCMatch'].Fill(sTree.Delx[k],sTree.Dely[k])
            if gf>33: 
                rc =   h['RPCMatch_ghosts'].Fill(sTree.Delx[k],sTree.Dely[k])
            p     =ROOT.TVector3(sTree.Px[k],sTree.Py[k],sTree.Pz[k])
            pTrue =ROOT.TVector3(sTree.MCTruepx[k],sTree.MCTruepy[k],sTree.MCTruepz[k])
            rc    = h['gfDiff'].Fill(gf,p.Mag() - pTrue.Mag())
            rc    = h['gftrue'].Fill(gf, pTrue.Mag())
            rc    = h['gf'].Fill(gf,p.Mag() )
            rc = h['gfCurv'].Fill(gf,1./p.Mag() )
    h['P']       =h['gf'].ProjectionY('P')
    h['Ptrue']   =h['gftrue'].ProjectionY('Ptrue')
    h['Ptrue'].SetLineColor(ROOT.kMagenta)
    for x in ['gf','gftrue','Chi2/DoF','R','DoF']:
        if x.find('true')>0: h[x].SetLineColor(ROOT.kGreen)
        else:   h[x].SetLineColor(ROOT.kBlue)
        h[x+'_perfect']      =h[x].ProjectionY(x+'_perfect',1,1)
        h[x+'_ghosts']       =h[x].ProjectionY(x+'_ghosts',33,100)
        h[x+'_ghosts'].SetLineColor(ROOT.kRed)
    h['gf_perfect'].SetTitle(' ;P [GeV/c];N/5GeV')
    h['gf_perfect'].SetLineColor(ROOT.kGreen)
    h['gf_ghosts'].SetTitle('ghost > 33;P [GeV/c];N/5GeV')
    ut.writeHists(h,'ghostStudy.root')
def init_Gauss(myGauss):
 myGauss.SetParName(0,'psi(1S)')
 myGauss.SetParName(1,'Mean')
 myGauss.SetParName(2,'Sigma')
 myGauss.SetParName(3,'SignalLow')
 myGauss.SetParName(4,'MeanLow')
 myGauss.SetParName(5,'SigmaLow')
 myGauss.SetParName(6,'p0')
 myGauss.SetParName(7,'p1')
 myGauss.SetParName(8,'p2')
 myGauss.SetParName(9,'psi(2S)')
 myGauss.SetParameter(0,1000.)
 myGauss.SetParameter(1,3.0)
 myGauss.SetParameter(2,0.1)
 myGauss.SetParameter(3,1000.)
 myGauss.SetParameter(4,1.0)
 myGauss.SetParameter(5,0.1)
 myGauss.SetParameter(6,10.)
 myGauss.SetParameter(7,1.)
 myGauss.FixParameter(8,0.)
 myGauss.FixParameter(9,0.)
def stupidCopy():
 for x in os.listdir('.'):
  if x.find('dimuon_all.p')<0: continue
  os.system('cp '+x+' '+ x.replace('all','AND_all'))

def analzyeMuonScattering():
  nt = hMC['10GeV']
  ntD  = hData['f'].nt
  ut.bookHist(hMC, 'dEdx','dE;dE [GeV/c^{2}]',100,-50.,25.,20,0.,200.)
  ut.bookHist(hMC, 'scatteringX','theta; rad ',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hMC, 'scatteringXcor','theta; rad ',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hMC, 'scatteringY','thetaX; rad ',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hMC, 'scatteringYcor','thetaY; rad ',100,-0.05,0.05,20,0.,200.)
  ut.bookCanvas(hMC,'scattering','scattering X and Y',1600,900,4,2)

  ROOT.gROOT.cd()
  nt.Draw('p1:(p1-p1True)>>dEdx','')
  nt.Draw('p2:(p2-p2True)>>+dEdx','')
  hMC['dEdxMean']=hMC['dEdx'].ProjectionY('dEdxMean')
  hMC['dEdxMean'].Reset()
  for n in range(1,hMC['dEdxMean'].GetNbinsX()+1):
    tmp = hMC['dEdx'].ProjectionX('tmp',n,n)
    hMC['dEdxMean'].SetBinContent(n,tmp.GetMean())
    hMC['dEdxMean'].SetBinError(n,tmp.GetRMS())
  hMC['dEdxMean'].Fit('pol2','S','',10.,190.)
#
  ptCut1 = 'pt1>0'
  ptCut2 = 'pt2>0'
  nt.Draw('p1:p1x/p1z-prec1x/prec1z>>scatteringX',ptCut1 )
  nt.Draw('p2:p1x/p1z-prec1x/prec1z>>+scatteringX',ptCut2 )
  nt.Draw('p1:p1x/p1z-rec1x/(rec1z- '+str(zTarget)+')>>scatteringXcor',ptCut1 )
  nt.Draw('p2:p2x/p2z-rec2x/(rec2z- '+str(zTarget)+')>>+scatteringXcor',ptCut2 )

  nt.Draw('p1:p1y/p1z-prec1y/prec1z>>scatteringY','')
  nt.Draw('p2:p1y/p1z-prec1y/prec1z>>+scatteringY','')
  nt.Draw('p1:p1y/p1z-rec1y/(rec1z- '+str(zTarget)+')>>scatteringYcor')
  nt.Draw('p2:p2y/p2z-rec2y/(rec2z- '+str(zTarget)+')>>+scatteringYcor')
  j=1
  for x in ['scatteringX','scatteringY','scatteringXcor','scatteringYcor']:
    hMC[x+'Mean']=hMC[x].ProjectionX(x+'Mean')
    tc=hMC['scattering'].cd(j)
    hMC[x].Draw('colz')
    j+=1
  tc=hMC['scattering'].cd(5)
  hMC['scatteringXcorMean'].SetLineColor(ROOT.kGreen)
  hMC['scatteringXcorMean'].Draw()
  hMC['scatteringXMean'].Draw('same')
  tc=hMC['scattering'].cd(6)
  hMC['scatteringYcorMean'].SetLineColor(ROOT.kGreen)
  hMC['scatteringYcorMean'].Draw()
  hMC['scatteringYMean'].Draw('same')
# look at applied angle correction / does not work yet, ntuple data missing info 
  ut.bookHist(hData, 'XcorData','theta; rad ',100,-0.05,0.05,20,0.,200.)
  ut.bookHist(hMC, 'XcorMC','theta; rad '    ,100,-0.05,0.05,20,0.,200.)
  nt.Draw('p1:prec1x/prec1z-rec1x/(rec1z- '+str(zTarget)+')>>XcorMC',ptCut1 )
  nt.Draw('p2:prec2x/prec2z-rec2x/(rec2z- '+str(zTarget)+')>>XcorMC',ptCut2)
  ntD.Draw('p1:prec1x/prec1z-rec1x/(rec1z- '+str(zTarget)+')>>XcorData',ptCut1 )
  ntD.Draw('p2:prec2x/prec2z-rec2x/(rec2z- '+str(zTarget)+')>>XcorData',ptCut2)
  
  for x in ['RMS','Mean']:
    hMC['scattXcor'+x+'_MC']=hMC['XcorMC'].ProjectionY('scattXcor'+x+'_MC')
    hMC['scattXcor'+x+'_MC'].Reset()
    hData['scattXcor'+x+'_Data']=hData['XcorData'].ProjectionY('scattXcor'+x+'_Data')
    hData['scattXcor'+x+'_Data'].Reset()
  for n in range(1,hMC['scattXcorRMS_MC'].GetNbinsX()+1):
    tmp = hMC['XcorMC'].ProjectionX('tmp',n,n)
    rc = tmp.Fit('gaus','SQ')
    fitresult = rc.Get()
    hMC['scattXcorRMS_MC'].SetBinContent(n,fitresult.Parameter(2))
    hMC['scattXcorMean_MC'].SetBinContent(n,fitresult.Parameter(1))
    tmp = hData['XcorData'].ProjectionX('tmp',n,n)
    rc = tmp.Fit('gaus','SQ')
    fitresult = rc.Get()
    hData['scattXcorRMS_Data'].SetBinContent(n,fitresult.Parameter(2))
    hData['scattXcorMean_Data'].SetBinContent(n,fitresult.Parameter(1))

  ut.bookCanvas(hMC,'scatteringDataMC','scattering ',1600,900,2,1)
  hData['scattXcorMean_Data'].SetTitle('Mean; P [GeV/c]; mean correction [rad]')
  hData['scattXcorRMS_Data'].SetTitle('RMS; P [GeV/c]; sigma of correction [rad]')
  j = 1
  for x in ['RMS','Mean']:
   hMC['scatteringDataMC'].cd(j)
   hData['scattXcor'+x+'_Data'].SetMinimum( min(hData['scattXcor'+x+'_Data'].GetMinimum(),hMC['scattXcor'+x+'_MC'].GetMinimum()))
   hData['scattXcor'+x+'_Data'].SetMaximum( max(hData['scattXcor'+x+'_Data'].GetMaximum(),hMC['scattXcor'+x+'_MC'].GetMaximum()))
   hData['scattXcor'+x+'_Data'].Draw()
   hMC['scattXcor'+x+'_MC'].SetLineColor(ROOT.kMagenta)
   hMC['scattXcor'+x+'_MC'].Draw('same')
   j+=1

def JpsiAcceptance():
    hMC['f0']=ROOT.TFile.Open(os.environ['EOSSHIP']+"/eos/experiment/ship/data/jpsicascade/cascade_MSEL61_20M.root")
    nt=hMC['f0'].nt
    two = f.Get('2').Clone('2')
    primJpsi  = two.GetBinContent(1)
    totalJpsi = two.GetSumOfWeights() # = nt.GetEntries()
    print "primary: %5.2F%%,  cascade: %5.2F%% "%(primJpsi/totalJpsi*100.,100.-primJpsi/totalJpsi*100.)
#
    ut.bookHist(hMC,'Jpsi_p/pt','momentum vs Pt (GeV);p [GeV/c]; p_{T} [GeV/c]',500,0.,500.,100,0.,10.)
    ut.bookHist(hMC,'Jpsi_y',   'rapidity cm; y_{CM}',100,-1.,5.,25,0.,500.,10,0.,10.)
    for event in nt:
       mom = ROOT.TLorentzVector(event.px,event.py,event.pz,event.E)
       rc = hMC['Jpsi_p/pt'].Fill(mom.P(),mom.Pt())
       rc = hMC['Jpsi_y'].Fill(mom.Rapidity(),mom.P(),mom.Pt())

def analyzeInvMassBias():
  if not hMC.has_key('f10'):
    hMC['f10'] = ROOT.TFile('ntuple-invMass-MC-10GeV.root')
    hMC['10GeV']=hMC['f10'].nt
    hData['f'] = ROOT.TFile('ntuple-InvMass-refitted.root')
  InvMassPlots = [160,0.,8.]
  ptCutList = [0.0,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6]
  nt = hMC['10GeV']
  ut.bookHist(hMC,'deltaXY','diff xy muon1 and muon2;x [cm]; y [cm]',100,0.,20.,100,0.,20.)
  nt.Draw('abs(prec1x-prec2x):abs(prec1y-prec2y)>>deltaXY','mcor<0.25')
# muon dEdx
  ut.bookHist(hMC, 'delpTrue2' ,'p-pTrue vs pTrue',20,0.,400.,50,-50.,50.)
  nt.Draw('(p1-p1True):p1>>delpTrue2','Jpsi==443&&pt1>1.4')
  nt.Draw('(p2-p2True):p2>>+delpTrue2','Jpsi==443&&pt2>1.4') # applying cuts does not make a difference
# inv mass from true mom
  for x in ['','_truePt']:
   ut.bookHist(hMC, 'm_MCtrue'+x, 'inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2],10,0.,2.)
   ut.bookHist(hMC, 'm_MCdEdx'+x, 'inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2],10,0.,2.)
   ut.bookHist(hMC, 'm_MCmult'+x, 'inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2],10,0.,2.)
   ut.bookHist(hMC, 'm_MCcor'+x,  'inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2],10,0.,2.)
   ut.bookHist(hMC, 'm_MCcor2'+x, 'inv mass;M [GeV/c^{2}]',InvMassPlots[0],InvMassPlots[1],InvMassPlots[2],10,0.,2.)
   ut.bookHist(hMC, 'm_MCtrueSigma'+x,'sigma inv mass;M [GeV/c^{2}]',10,0.,2.)
   ut.bookHist(hMC, 'm_MCdEdxSigma'+x,'sigma inv mass;M [GeV/c^{2}]',10,0.,2.)
   ut.bookHist(hMC, 'm_MCmultSigma'+x,'sigma inv mass;M [GeV/c^{2}]',10,0.,2.)
   ut.bookHist(hMC, 'm_MCcorSigma'+x, 'sigma inv mass;M [GeV/c^{2}]',10,0.,2.)
   ut.bookHist(hMC, 'm_MCcor2Sigma'+x, 'sigma inv mass;M [GeV/c^{2}]',10,0.,2.)
  Ptrue = {}
  Prec  = {}
  Pcor  = {}
  Pcor2  = {}
  x = '_truePt'
  for event in nt:
   if event.Jpsi!=443: continue
   Ptrue[1] = ROOT.Math.PxPyPzMVector(event.p1x,event.p1y,event.p1z,0.105658)
   Ptrue[2] = ROOT.Math.PxPyPzMVector(event.p2x,event.p2y,event.p2z,0.105658)
   Prec[1]  = ROOT.Math.PxPyPzMVector(event.prec1x,event.prec1y,event.prec1z,0.105658)
   Prec[2]  = ROOT.Math.PxPyPzMVector(event.prec2x,event.prec2y,event.prec2z,0.105658)
   tdir = ROOT.TVector3(event.rec1x,event.rec1y,event.rec1z-zTarget)
   cor = Prec[1].P()/tdir.Mag()
   Pcor[1]  = ROOT.Math.PxPyPzMVector(tdir.X()*cor,tdir.Y()*cor,tdir.Z()*cor,0.105658)
   cor = Ptrue[1].P()/tdir.Mag()
   Pcor2[1]  = ROOT.Math.PxPyPzMVector(tdir.X()*cor,tdir.Y()*cor,tdir.Z()*cor,0.105658)
   tdir = ROOT.TVector3(event.rec2x,event.rec2y,event.rec2z-zTarget)
   cor = Prec[2].P()/tdir.Mag()
   Pcor[2]  = ROOT.Math.PxPyPzMVector(tdir.X()*cor,tdir.Y()*cor,tdir.Z()*cor,0.105658)
   cor = Ptrue[2].P()/tdir.Mag()
   Pcor2[2]  = ROOT.Math.PxPyPzMVector(tdir.X()*cor,tdir.Y()*cor,tdir.Z()*cor,0.105658)
   P=Ptrue[1]+Ptrue[2]
   PtMinTrue = min(Ptrue[1].Pt(),Ptrue[2].Pt())
   PtMin = min(Prec[1].Pt(),Prec[2].Pt())
   rc = hMC['m_MCtrue'].Fill(P.M(),PtMin)
   rc = hMC['m_MCtrue'+x].Fill(P.M(),PtMinTrue)
   P=Pcor[1]+Pcor[2]
   PtMin = min(Pcor[1].Pt(),Pcor[2].Pt())
   rc = hMC['m_MCcor'].Fill(P.M(),PtMin)
   rc = hMC['m_MCcor'+x].Fill(P.M(),PtMinTrue)
   P=Pcor2[1]+Pcor2[2]
   PtMin = min(Pcor2[1].Pt(),Pcor2[2].Pt())
   rc = hMC['m_MCcor2'].Fill(P.M(),PtMin)
   rc = hMC['m_MCcor2'+x].Fill(P.M(),PtMinTrue)
   PdEloss = {}
   Pmult   = {}
   for j in range(1,3): 
       dEloss=Prec[j].P()/Ptrue[j].P()
       PdEloss[j]= ROOT.Math.PxPyPzMVector(Ptrue[j].X()*dEloss,Ptrue[j].Y()*dEloss,Ptrue[j].Z()*dEloss,0.105658)
       Pmult[j]= ROOT.Math.PxPyPzMVector(Prec[j].X()/dEloss,Prec[j].Y()/dEloss,Prec[j].Z()/dEloss,0.105658)
   P=PdEloss[1]+PdEloss[2]
   PtMin = min(PdEloss[1].Pt(),PdEloss[2].Pt())
   rc = hMC['m_MCdEdx'].Fill(P.M(),PtMin)
   rc = hMC['m_MCdEdx'+x].Fill(P.M(),PtMinTrue)
   P=Pmult[1]+Pmult[2]
   PtMin = min(Pmult[1].Pt(),Pmult[2].Pt())
   rc = hMC['m_MCmult'].Fill(P.M(),PtMin)
   rc = hMC['m_MCmult'+x].Fill(P.M(),PtMinTrue)
  for z in ['','_truePt']:
   for x in ['m_MCdEdx','m_MCmult','m_MCtrue','m_MCcor','m_MCcor2']:
    hname = x+'Mean'+z
    hMC[hname] = hMC[x+z].ProjectionY(hname)
    hMC[hname].Reset()
    hMC[hname].SetStats(0)
    hMC[hname.replace('Mean','Sigma')].SetStats(0)
    Nmax = hMC[hname].GetNbinsX()
    for k in range(Nmax):
     tmp = hMC[x+z].ProjectionX('tmp',k,Nmax)
     if x.find('true')>0:
      hMC[hname].SetBinContent(k,tmp.GetMean())
      hMC[hname].SetBinError(k,0.01)
     else:
      rc = tmp.Fit('gaus','S')
      fitresult = rc.Get()
      hMC[hname].SetBinContent(k,fitresult.Parameter(1))
      hMC[hname].SetBinError(k,fitresult.ParError(1))
      hMC[hname.replace('Mean','Sigma')].SetBinContent(k,fitresult.Parameter(2))
      hMC[hname.replace('Mean','Sigma')].SetBinError(k,fitresult.ParError(2))
   ut.bookCanvas(hMC,'TinvMassBiasMean'+z,'inv mass bias, mean',1900,650,1,1)
   ut.bookCanvas(hMC,'TinvMassBiasSigma'+z,'inv mass bias, sigma',1900,650,1,1)
   for tt in ['Mean','Sigma']:
    t=tt+z
    hMC['TinvMassBias'+t].cd()
    if tt=='Mean':
     hMC['m_MCdEdx'+t].SetMinimum(2.)
     hMC['m_MCdEdx'+t].SetMaximum(4.5)
    else:
     hMC['m_MCdEdx'+t].SetMinimum(0.)
     hMC['m_MCdEdx'+t].SetMaximum(1.0)
    hMC['m_MCdEdx'+t].SetMarkerStyle(21)
    hMC['m_MCdEdx'+t].SetLineColor(ROOT.kRed)
    hMC['m_MCmult'+t].SetLineColor(ROOT.kMagenta)
    hMC['m_MCmult'+t].SetMarkerStyle(20)
    hMC['m_MCcor'+t].SetLineColor(ROOT.kBlue)
    hMC['m_MCcor'+t].SetMarkerStyle(29)
    hMC['m_MCcor'+t].SetMarkerSize(1.8)
    hMC['m_MCcor2'+t].SetLineColor(ROOT.kGreen)
    hMC['m_MCcor2'+t].SetMarkerStyle(28)
    hMC['m_MCcor2'+t].SetMarkerSize(1.8)
    hMC['m_MCdEdx'+t].Draw()
    hMC['m_MCmult'+t].Draw('same')
    hMC['m_MCtrue'+t].Draw('same')
    hMC['m_MCcor'+t].Draw('same')
    hMC['m_MCcor2'+t].Draw('same')
    hMC['legInvMassBias'+t]=ROOT.TLegend(0.11,0.66,0.48,0.92)
    rc = hMC['legInvMassBias'+t].AddEntry(hMC['m_MCdEdx'+t],'effect of dEdx','PL')
    rc = hMC['legInvMassBias'+t].AddEntry(hMC['m_MCmult'+t],'effect of multiple scattering','PL')
    rc = hMC['legInvMassBias'+t].AddEntry(hMC['m_MCcor2'+t],'true momentum, correction of direction','PL')
    rc = hMC['legInvMassBias'+t].AddEntry(hMC['m_MCcor'+t], 'reco momentum, correction of direction','PL')
    rc = hMC['legInvMassBias'+t].AddEntry(hMC['m_MCtrue'+t],'true mass','PL')
    hMC['legInvMassBias'+t].Draw()
    myPrint(hMC['TinvMassBias'+t],'invMassBias'+t)

def debug():
    Nstat = {}
    for n in range(sTreeMC.GetEntries()):
        rc = sTreeMC.GetEvent(n)  
        fname = sTreeMC.GetCurrentFile().GetName()
        if not Nstat.has_key(fname): Nstat[fname]=[sTreeMC.GetEntries(),0,0,0]
        rc = sTreeMC.GetEvent(n)
        Nstat[fname][1]+=sTreeMC.nTr
        Nstat[fname][2]+=sTreeMC.MCRecoRPC.size()
        Nstat[fname][3]+=sTreeMC.MCRecoDT.size()
    return Nstat

def debugInvMass(sTree,nMax=1000):
    stats = {}
    currentFile=""
    N=0
    for n in range(0,sTree.GetEntries()):
        rc = sTree.GetEvent(n)
        if sTree.GetCurrentFile().GetName()!=currentFile:
          currentFile = sTree.GetCurrentFile().GetName()
          nInFile = n
        P    = {}
        IP   = {}
        Pcor = {}
        Pcor2 = {}
        for k in range(len(sTree.GoodTrack)):
            if sTree.GoodTrack[k]<0: continue
            if sTree.GoodTrack[k]%2!=1 or  int(sTree.GoodTrack[k]/10)%2!=1: continue
            if sTree.GoodTrack[k]>999:  continue
            P[k] = ROOT.Math.PxPyPzMVector(sTree.Px[k],sTree.Py[k],sTree.Pz[k],0.105658)
            l = (sTree.z[k] - zTarget)/(sTree.Pz[k]+ 1E-19)
            x = sTree.x[k]+l*sTree.Px[k]
            y = sTree.y[k]+l*sTree.Py[k]
            IP[k] = ROOT.TMath.Sqrt(x*x+y*y)
# make dE correction plus direction from measured point
            dline   = ROOT.TVector3(sTree.x[k],sTree.y[k],sTree.z[k]-zTarget)
            Ecor = P[k].E()+dEdxCorrection(P[k].P())
            norm = dline.Mag()
            Pcor[k]  = ROOT.Math.PxPyPzMVector(Ecor*dline.X()/norm,Ecor*dline.Y()/norm,Ecor*dline.Z()/norm,0.105658)
            Pcor2[k] = ROOT.Math.PxPyPzMVector(P[k].P()*dline.X()/norm,P[k].P()*dline.Y()/norm,P[k].P()*dline.Z()/norm,0.105658)
# now we have list of selected tracks, P.keys()
        if len(P)<2: continue
        shortName = currentFile.split('/')[11]
        if not stats.has_key(shortName): stats[shortName]=[]
        stats[shortName].append(n-nInFile)
        N+=1
        if N>nMax: break
    return stats

if options.command=='MufluxReco':
    if fdir.find('simulation')==0: mufluxReco(sTreeMC,hMC,nseq=options.nseq,ncpus=options.ncpus)
    else: mufluxReco(sTreeData,hData)
if options.command=='RecoEffFunOfOcc':
    RecoEffFunOfOcc()
if options.command=='invMass':
    if fdir.find('simulation')==0:
      invMass(sTreeMC,hMC,nseq=options.nseq,ncpus=options.ncpus)
    else:
      invMass(sTreeData,hData)
