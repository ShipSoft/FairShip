import ROOT,os,time
import rootUtils as ut
from argparse import ArgumentParser
cuts = {}
cuts['muTrackMatchX']= 5.
cuts['muTrackMatchY']= 10.
zTarget = -370.       # start of target: -394.328, mean z for mu from Jpsi in MC = -375cm, for all muons: -353cm
dEdxCorrection = +7.3    # most probably ~7.5, mean 6.9
cuts['zRPC1']  = 878.826706
cuts['xLRPC1'] =-97.69875
cuts['xRRPC1'] = 97.69875
cuts['yBRPC1'] =-41.46045
cuts['yTRPC1'] = 80.26905

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
parser.add_argument("-A", "--with1GeV", dest="with1GeV", help="1GeV MC", default="True")
parser.add_argument("-C", "--withcharm", dest="withCharm", help="charm 1GeV MC", default="True")
parser.add_argument("-B", "--with10GeV", dest="with10GeV", help="10GeV MC", default="True")
parser.add_argument("-x", dest="ncpus", help="number of parallel jobs", default=False)
parser.add_argument("-s", dest="nseq", help="sequence of parallel job", default=0)

options = parser.parse_args()

MCType    =  options.MCType
with1GeV  =  options.with1GeV  == "True"
withCharm =  options.withCharm == "True"
with10GeV =  options.with10GeV == "True"
if options.path != "": gPath = options.path+'/'
fdir = options.directory

if not fdir: 
    Nfiles = 2000
    fdir   = "RUN_8000_2403"
else: 
    Nfiles = len( os.listdir(gPath+fdir) )
if not options.listOfFiles:
    sTreeData = ROOT.TChain('tmuflux')
    path = gPath + fdir
    countFiles=[]
    for x in os.listdir(path):
        if not x.find('ntuple-SPILL')<0: countFiles.append(x)
    for x in countFiles:
        sTreeData.Add(path+"/"+x)
        Nfiles-=1
        if Nfiles==0: break

    sTreeMC = ROOT.TChain('tmuflux')
    if host=="ubuntu":
        gPath = "/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-48/"
    elif host=='ship-ubuntu-1710-48':
        gPath = "/home/truf/muflux/"
    else:
        gPath = "/home/truf/ship-ubuntu-1710-48/"

    if with1GeV:
        path = gPath+"simulation1GeV-"+MCType+"/pythia8_Geant4_1.0_cXXXX_mu/"
        for k in range(0,20000,1000):
            for m in range(5):
                fname = path.replace('XXXX',str(k))+"ntuple-ship.conical.MuonBack-TGeant4_dig_RT-"+str(m)+".root"
                try:
                    test = ROOT.TFile(fname)
                    if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
                except: continue
    if withCharm:
        fdir = fdir+'-charm'
        path = gPath+"simulation1GeV-"+MCType+"/pythia8_Geant4_charm_0-19_1.0_mu/"
        for m in range(5):
            fname = path+"ntuple-ship.conical.MuonBack-TGeant4_dig_RT-"+str(m)+".root"
            try:
                test = ROOT.TFile(fname)
                if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
            except: continue

    if with10GeV:
        path = gPath+"simulation10GeV-"+MCType+"/pythia8_Geant4_10.0_withCharmandBeautyXXXX_mu/"
        for k in range(0,67000,1000):
            for m in range(10):
                fname = path.replace('XXXX',str(k))+"ntuple-ship.conical.MuonBack-TGeant4_dig_RT-"+str(m)+".root"
                if not os.path.isfile(fname): continue
                try:
                    test = ROOT.TFile(fname)
                    if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
                except: continue

# small problem here when merging 1GeV and 10GeV, due to different p cutoff, px and pt cannot be used directly. 

# temp hack
#nfile = "/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-48/simulation1GeV-withDeadChannels/pythia8_Geant4_1.0_c3000_mu/ship.conical.MuonBack-TGeant4_dig_RT-0.root"
#sTreeMC.Add("ntuple-ship.conical.MuonBack-TGeant4_dig_RT-0.root")
    case = {'MC':[sTreeMC,hMC,ROOT.kRed,'hist same'],'Data':[sTreeData,hData,ROOT.kBlue,'hist']}

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
            elif not fname.find('10')<0: x = '10GeV'
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
        ut.readHists(h,'trueMoms-withDeadChannels.root')
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
            h0['0rebinned-recoMom-'+k].Rebin(5)
            h0['0rebinned-recoMom-'+k].Scale(1./5.)
            h0['0rebinned-recoMom-'+k].SetMarkerStyle(22)
            h0['0rebinned-recoMom-'+k].SetMarkerColor(h0['0rebinned-recoMom-'+k].GetLineColor())
            h0['0rebinned-recoMom-'+k].Draw('P same')
            h['leg'+t]=ROOT.TLegend(0.31,0.67,0.85,0.85)
            h['leg'+t].AddEntry(h['rebinned-trueMom-'+k],'true momentum ','PL')
            h['leg'+t].AddEntry(h0['0rebinned-recoMom-'+k],'reconstructed momentum 270#mum','PL')
            h['leg'+t].AddEntry(h['rebinned-recoMom-'+k],'reconstructed momentum 500#mum','PL')
            h['leg'+t].Draw()
            h[t].Print('True-Reco'+k+'.png')
            h[t].Print('True-Reco'+k+'.pdf')
def mufluxReco(sTree,h,nseq=0,ncpus=False):
    cuts = {'':0,'Chi2<':0.7,'Dely<':5,'Delx<':2,'All':1}
    ut.bookHist(h,'Trscalers','scalers for track counting',20,0.5,20.5)
    for c in cuts:
        for x in ['','mu']:
            for s in ["","Decay","Hadronic inelastic","Lepton pair","Positron annihilation","charm","beauty","Di-muon P8","invalid"]:
                ut.bookHist(h,c+'p/pt'+x+s,'momentum vs Pt (GeV);p [GeV/c]; p_{T} [GeV/c]',500,0.,500.,100,0.,10.)
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
    if ncpus:
      deltaN = (sTree.GetEntries()+0.5)//ncpus
      nStart = nseq*deltaN
      Ntotal=min(sTree.GetEntries(),nStart+deltaN)
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
                h[c+"p/pt"].Fill(p.Mag(),p.Pt())
                h[c+"p/px"].Fill(p.Mag(),p.x())
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
    outFile = 'sumHistos-'+'-'+fdir+'.root'
    if ncpus:
       outFile.replace('.root','-'+str(nseq)+'.root')
    ut.writeHists( h,outFile)
def invMass(sTree,h):
    ut.bookHist(h,'invMassSS','inv mass ',100,0.0,10.0)
    ut.bookHist(h,'invMassOS','inv mass ',100,0.0,10.0)
    ut.bookHist(h,'invMassJ','inv mass from Jpsi',100,0.0,10.0)
    ut.bookHist(h,'p/pt','p/pt',100,0.0,400.0,100,0.0,10.0)
    ut.bookHist(h,'p/ptJ','p/pt of Jpsi',100,0.0,400.0,100,0.0,10.0)
    ut.bookHist(h,'p/ptmu','p/pt of mu',100,0.0,400.0,100,0.0,10.0)
    ut.bookHist(h,'p/ptmuJ','p/pt of mu from Jpsi',100,0.0,400.0,100,0.0,10.0)
    MCdata = False
    if sTree.FindBranch("MCRecoDT"): MCdata = True
    if MCdata: name = "ntuple-invMass-MC.root"
    else:      name = "ntuple-invMass-"+fdir.split('-')[0]+'.root'
    h['fntuple']  = ROOT.TFile.Open(name, 'RECREATE')
    h['nt']  = ROOT.TNtuple("nt","dimuon","mult:m:mcor:mcor2:p:pt:p1:pt1:p2:pt2:Ip1:Ip2:chi21:chi22:cosTheta:Jpsi:PTRUE:PtTRUE:p1True:p2True:dTheta1:dTheta2:dMults1:dMults2")
#
    sTreeFullMC = None
    Ntotal = sTree.GetEntries()
    currentFile = ''
    for n in range(sTree.GetEntries()):
        rc = sTree.GetEvent(n)
        if n%500000==0: print 'now at event ',n,'of',Ntotal,time.ctime()
        if sTree.GetCurrentFile().GetName()!=currentFile:
            currentFile = sTree.GetCurrentFile().GetName()
            nInFile = n
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
            Ecor = P[k].E()+dEdxCorrection
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
          pTrue[j]  = [-9999.,-9999.]
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
            mothers = []
            kx = 0
            for k in [n1,n2]:
                trueMu = sTreeFullMC.MCTrack[sTreeMC.MCID[k]]
                mother = sTreeFullMC.MCTrack[trueMu.GetMotherId()]
                mothers.append(mother.GetPdgCode())
                PTRUE[j]  = mother.GetP()
                PtTRUE[j] = mother.GetPt()
# check multiple scattering
                mom = ROOT.TVector3()
                trueMu.GetMomentum(mom)
                pTrue[j][kx] = mom.Mag()
                dline   = ROOT.TVector3(sTree.x[k],sTree.y[k],sTree.z[k]-zTarget)
                dTheta[j][kx]  = mom.Dot(dline)/(mom.Mag()*dline.Mag())
                prec = ROOT.TVector3(P[k].Px(),P[k].Py(),P[k].Pz())
                dMults[j][kx]  = mom.Dot(prec)/(mom.Mag()*prec.Mag())
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
          theTuple = array('f',\
[float(len(nComb)),X[j].M(),Xcor[j].M(),Xcor2[j].M(),X[j].P(),X[j].Pt(),P[nComb[j][0]].P(),P[nComb[j][0]].Pt(),P[nComb[j][1]].P(),P[nComb[j][1]].Pt(),\
IP[nComb[j][0]],IP[nComb[j][1]],chi2[j][0],chi2[j][1],costheta[j],float(jpsi[j]),PTRUE[j],PtTRUE[j],\
pTrue[j][0],pTrue[j][1],dTheta[j][0],dTheta[j][1],dMults[j][0],dMults[j][1]])
          h['nt'].Fill(theTuple)
    h['fntuple'].cd()
    h['nt'].Write()
    ut.writeHists(h,name.replace('ntuple-',''))
def diMuonAnalysis():
 hData['f']= ROOT.TFile('ntuple-InvMass.root')
 hMC['f']  = ROOT.TFile('ntuple-invMass-MC.root')
 sTreeData = hData['f'].nt
 sTreeMC   = hMC['f'].nt
 ptCutList = [0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6]
 hData['fitResult'] = {}
 hMC['fitResult'] = {}
 sptCut = 'XYZ'
 theCutTemplate =  '('+sptCut+'<pt1||'+sptCut+'<pt2)&&chi21*chi22<0&&abs(chi21)<0.9&&abs(chi22)<0.9&&p1<200&&p2<200&&p1>20&&p2>20&&mcor>0.5'
 ut.bookHist(hMC, 'mc_theta','cos theta mother - daughter1',100,-1,1.)
 ut.bookHist(hMC, 'mc_thetaJ','cos theta mother - daughter1 Jpsi',100,-1,1.)
 ut.bookHist(hData, 'theta','cos theta mother - daughter1',100,-1,1.)
 ut.bookCanvas(hMC,'tTheta','costheta',900,600,1,1)
 ut.bookCanvas(hMC,'tMass','mass',900,600,1,1)
 hMC['mc_theta'].SetLineColor(ROOT.kRed)
 hMC['mc_thetaJ'].SetLineColor(ROOT.kMagenta)
 theCut = theCutTemplate.replace('XYZ','0')
 ROOT.gROOT.cd()
 sTreeMC.Draw('cosTheta>>mc_thetaJ',theCut+'&&Jpsi==443')
 sTreeMC.Draw('cosTheta>>mc_theta',theCut)
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
 sTreeMC.Draw('Ip1>>mc_IPJ',theCut+'&&Jpsi==443')
 sTreeMC.Draw('Ip1>>mc_IP',theCut)
 sTreeData.Draw('Ip1>>IP',theCut)
 sTreeMC.Draw('Ip2>>mc_IPJ',theCut+'&&Jpsi==443')
 sTreeMC.Draw('Ip2>>mc_IP',theCut)
 sTreeData.Draw('Ip2>>IP',theCut)
 hMC['tIP'].cd()
 hMC['mc_IP'].Scale(1./hMC['mc_IP'].GetEntries())
 hMC['mc_IPJ'].Scale(1./hMC['mc_IPJ'].GetEntries())
 hData['IP'].Scale(1./hData['IP'].GetEntries())
 hMC['mc_IP'].Draw()
 hMC['mc_IPJ'].Draw('same')
 hData['IP'].Draw('same')
 myPrint(hMC['tIP'],'dimuon-IP')
 ut.bookHist(hMC, 'm_MC','inv mass',130,0.,13.)
 bw = hMC['m_MC'].GetBinWidth(1)
 hMC['myGauss'] = ROOT.TF1('gauss','abs([0])*'+str(bw)+'/(abs([2])*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)\
            +abs([3])*'+str(bw)+'/(abs([5])*sqrt(2*pi))*exp(-0.5*((x-[4])/[5])**2)+abs( [6]+[7]*x+[8]*x**2 )',9)
 myGauss = hMC['myGauss']
 theCutTemplate +=  '&&abs(cosTheta)<0.8'
 vText={'m':'inv mass and fits','mcor':'inv mass, dE and direction corrected, and fits','mcor2':'inv mass, direction corrected, and fits'}
 for v in vText:
  for ptCut in ptCutList:
   sptCut = str(ptCut)
   ut.bookHist(hMC, 'mc-'+v+'_'+sptCut,'inv mass MC',130,0.,13.)
   ut.bookHist(hMC, 'mc-'+v+'_Jpsi_'+sptCut,'inv mass Jpsi MC matched',130,0.,13.)
   ut.bookHist(hData,v+'_'+sptCut,'inv mass DATA',130,0.,13.)
#
   theCut =  theCutTemplate.replace('XYZ',sptCut)
   ROOT.gROOT.cd()
   sTreeData.Draw(v+'>>'+v+'_'+sptCut,theCut)
   sTreeMC.Draw(v+'>>mc-'+v+'_'+sptCut ,theCut)
   sTreeMC.Draw(v+'>>mc-'+v+'_Jpsi_'+sptCut ,theCut+"&&Jpsi==443")

  ut.bookCanvas(hMC,'fits'+v,vText[v],1800,800,5,4)
  j = 1
  for ptCut in  ptCutList:
   sptCut = str(ptCut)
   tc = hMC['fits'+v].cd(j)
   init_Gauss(myGauss)
   rc = hMC['mc-'+v+'_'+sptCut].Fit(myGauss,'S')
   fitResult = rc.Get()
   if fitResult.Parameter(0)+fitResult.Parameter(3)>hMC['mc-'+v+'_'+sptCut].GetEntries()*1.5:
     myGauss.FixParameter(3,0)
     myGauss.FixParameter(4,1.)
     myGauss.FixParameter(5,1.)
     rc = hMC['mc-'+v+'_'+sptCut].Fit(myGauss,'S')
     fitResult = rc.Get()
   hMC['fitResult'][ptCut] = []
   for n in range(3):
    hMC['fitResult'][ptCut].append([fitResult.Parameter(n),fitResult.ParError(n)])
   hMC['mc-'+v+'_Jpsi_'+sptCut].SetLineColor(ROOT.kMagenta)
   hMC['mc-'+v+'_Jpsi_'+sptCut].Draw('same')
   tc.Update()
   stats = tc.GetPrimitive('stats')
   stats.SetOptFit(10011)
   stats.SetFitFormat('5.4g')
   stats.SetX1NDC(0.41)
   stats.SetY1NDC(0.41)
   stats.SetX2NDC(0.99)
   stats.SetY2NDC(0.84)
   tc.Update()
# data
   tc = hMC['fits'+v].cd(j+5)
   rc = hData[v+'_'+sptCut].Fit(myGauss,'S')
   fitResult = rc.Get()
   hData['fitResult'][ptCut] = []
   for n in range(3):
    hData['fitResult'][ptCut].append([fitResult.Parameter(n),fitResult.ParError(n)])
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
   myPrint(hMC['tMass'],'mc_dimuon_'+sptCut)
   hData[v+'_'+sptCut].Draw()
   myPrint(hMC['tMass'],'m_dimuon_'+sptCut)
  hMC['fits'+v].Update()
  myPrint(hMC['fits'+v],v+'_dimuon_all')
#
  param = {0:'Signal',1:'Mass',2:'Sigma'}
  for h in [hMC,hData]:
   for p in range(3):
    ut.bookHist(h,'evolution'+v+param[p],v+' evolution of '+param[p],20,0., 2.)
    for ptCut in ptCutList:
        k = h['evolution'+v+param[p]].FindBin(ptCut)
        h['evolution'+v+param[p]].SetBinContent(k,h['fitResult'][ptCut][p][0])
        h['evolution'+v+param[p]].SetBinError(k,h['fitResult'][ptCut][p][1])
        k+=1
  ut.bookCanvas(hMC,'evolutionC'+v,'evolution',1600,500,3,1)
  for p in range(3):
   tc = hMC['evolutionC'+v].cd(p+1)
   resetMinMax(hMC['evolution'+v+param[p]])
   resetMinMax(hData['evolution'+v+param[p]])
   hMC['evolution'+v+param[p]].SetLineColor(ROOT.kRed)
   hMC['evolution'+v+param[p]].GetXaxis().SetRangeUser(0.9,2.0)
   hData['evolution'+v+param[p]].GetXaxis().SetRangeUser(0.9,2.0)
   hMC['evolution'+v+param[p]].SetMaximum(1.1*max(hMC['evolution'+v+param[p]].GetMaximum(),hData['evolution'+v+param[p]].GetMaximum()))
   hMC['evolution'+v+param[p]].Draw()
   hData['evolution'+v+param[p]].Draw('same')
  myPrint(hMC['evolutionC'+v],'EvolutionOfCuts_dimuon'+v)
# truth momentum
 ut.bookCanvas(hMC,'kin','Jpsi kinematics',1800,1000,3,2)
 ut.bookHist(hMC, 'pt','pt',100,0.,5.)
 ut.bookHist(hMC, 'ptTrue','pt vs ptTrue',100,0.,5.,100,0.,5.)
 ut.bookHist(hMC, 'pTrue' ,'p vs pTrue',100,0.,400.,100,0.,400.)
 ut.bookHist(hMC, 'delpTrue' ,'pTrue - p',100,-20.,70.)
 ut.bookHist(hMC, 'delptTrue' ,'ptTrue - pt',100,-2.,2.)
 sTreeMC.Draw('p:PTRUE>>pTrue','Jpsi==443')
 sTreeMC.Draw('pt:PtTRUE>>ptTrue','Jpsi==443')
 sTreeMC.Draw('PTRUE-p>>delpTrue','Jpsi==443')
 sTreeMC.Draw('PtTRUE-pt>>delptTrue','Jpsi==443')
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
# muon dEdx
 ut.bookHist(hMC, 'delpTrue2' ,'p-pTrue vs pTrue',20,0.,400.,50,-25.,25.)
 sTreeMC.Draw('(p1-p1True):p1True>>delpTrue2','Jpsi==443')
 sTreeMC.Draw('(p2-p2True):p2True>>+delpTrue2','Jpsi==443')
 ROOT.gROOT.cd()
 hMC['meanLoss']=hMC['delpTrue2'].ProjectionX('meanLoss')
 for n in range(1,hMC['delpTrue2'].GetXaxis().GetNbins()+1):
   tmp = hMC['delpTrue2'].ProjectionY('tmp',n,n)
   hMC['meanLoss'].SetBinContent(n,tmp.GetMean())
   hMC['meanLoss'].SetBinError(n,tmp.GetRMS())
 hMC['meanLoss'].Draw()
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
    h['Ptrue']       =h['gftrue'].ProjectionY('Ptrue')
    h['Ptrue'].SetLineColor(ROOT.kMagenta)
    for x in ['gf','gftrue','Chi2/DoF','R','DoF']:
        if x.find('true')>0: h[x].SetLineColor(ROOT.kGreen)
        else:   h[x].SetLineColor(ROOT.kBlue)
        h[x+'_perfect']      =h[x].ProjectionY(x+'_perfect',1,1)
        h[x+'_ghosts']       =h[x].ProjectionY(x+'_ghosts',33,100)
        h[x+'_ghosts'].SetLineColor(ROOT.kRed)
    h['gf_perfect'].SetTitle('perfect;P [GeV/c];N/5GeV')
    h['gf_perfect'].SetLineColor(ROOT.kGreen)
    h['gf_ghosts'].SetTitle('ghost > 33;P [GeV/c];N/5GeV')
    ut.writeHists(h,'ghostStudy.root')
def init_Gauss(myGauss):
 myGauss.SetParName(0,'Signal')
 myGauss.SetParName(1,'Mean')
 myGauss.SetParName(2,'Sigma')
 myGauss.SetParName(3,'SignalLow')
 myGauss.SetParName(4,'MeanLow')
 myGauss.SetParName(5,'SigmaLow')
 myGauss.SetParName(6,'p0')
 myGauss.SetParName(7,'p1')
 myGauss.SetParName(8,'p2')
 myGauss.SetParameter(0,1000.)
 myGauss.SetParameter(1,3.0)
 myGauss.SetParameter(2,0.1)
 myGauss.SetParameter(3,1000.)
 myGauss.SetParameter(4,1.0)
 myGauss.SetParameter(5,0.1)
 myGauss.SetParameter(6,10.)
 myGauss.SetParameter(7,1.)
 myGauss.FixParameter(8,0.)
def stupidCopy():
 for x in os.listdir('.'):
  if x.find('dimuon_all.p')<0: continue
  os.system('cp '+x+' '+ x.replace('all','AND_all'))
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

if options.command=='MufluxReco':
    if fdir.find('simulation')==0: mufluxReco(sTreeMC,hMC,nseq=options.nseq,ncpus=options.ncpus)
    else: mufluxReco(sTreeData,hData)
if options.command=='RecoEffFunOfOcc':
    RecoEffFunOfOcc()
if options.command=='invMass':
    invMass(sTreeData,hData)
