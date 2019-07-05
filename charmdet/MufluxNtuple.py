import ROOT,os
import rootUtils as ut
cuts = {}
cuts['muTrackMatchX']= 5.
cuts['muTrackMatchY']= 10.
zTarget = -394.328
cuts['zRPC1']  = 878.826706
cuts['xLRPC1'] =-97.69875
cuts['xRRPC1'] = 97.69875
cuts['yBRPC1'] =-41.46045
cuts['yTRPC1'] = 80.26905


hData   = {}
hMC     = {}
sTreeData = ROOT.TChain('tmuflux')
path = "/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-32/RUN_8000_2403/"
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519319240_20180723_160408_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519319310_20180723_160422_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519319400_20180723_160440_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519319470_20180723_160454_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519319560_20180723_160512_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519319635_20180723_160527_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519319725_20180723_160545_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519319795_20180723_160559_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519319885_20180723_160617_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519312030_20180723_154006_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519312220_20180723_154044_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519312405_20180723_154121_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519312590_20180723_154158_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519312775_20180723_154235_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519312960_20180723_154312_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519313150_20180723_154350_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519313335_20180723_154427_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519313520_20180723_154504_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519313705_20180723_154541_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519313890_20180723_154618_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519314080_20180723_154656_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519314265_20180723_154733_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519314450_20180723_154810_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519314635_20180723_154847_RT.root")
sTreeData.Add(path+"ntuple-SPILLDATA_8000_0519314820_20180723_154924_RT.root")


sTreeMC = ROOT.TChain('tmuflux')
with1GeV=False
if with1GeV:
 path = "/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-48/simulation1GeV-withDeadChannels/pythia8_Geant4_1.0_cXXXX_mu/"
 for k in range(0,21000,1000):
  for m in range(5):
   fname = path.replace('XXXX',str(k))+"ntuple-ship.conical.MuonBack-TGeant4_dig_RT-"+str(m)+".root"
   try:
    test = ROOT.TFile(fname)
    if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
   except: continue
withCharm=False
if withCharm:
 path = "/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-48/simulation1GeV-withDeadChannels/pythia8_Geant4_charm_0-19_1.0_mu/"
 for m in range(5):
   fname = path+"ntuple-ship.conical.MuonBack-TGeant4_dig_RT-"+str(m)+".root"
   try:
    test = ROOT.TFile(fname)
    if test.tmuflux.GetEntries()>0:   sTreeMC.Add(fname)
   except: continue
 
with10GeV=True
if with10GeV:
 path = "/media/truf/disk2/home/truf/ShipSoft/ship-ubuntu-1710-48/simulation10GeV-withDeadChannels/pythia8_Geant4_10.0_withCharmandBeautyXXXX_mu/"
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
   ut.bookHist(h,'cos alpha','cosine of angle between two tracks',10000,0.95,1.01)
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
 hData['clones'].Print('MC-Comparison-Clones.pdf') 
 hData['clones'].Print('MC-Comparison-Clones.png')

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
def RecoEffFunOfOcc(OnlyDraw = False):
 pMin = 5.
 if not OnlyDraw:
   c = 'Data'
   sTree = case[c][0]
   h = case[c][1]
   ut.bookHist(h,'Occ','N',50,0.,200.)
   for n in range(sTree.GetEntries()):
    rc = sTree.GetEvent(n)
    upStreamOcc = sTree.stationOcc[1]+sTree.stationOcc[5]+sTree.stationOcc[2]+sTree.stationOcc[6]
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
   ut.bookHist(h,'P', 'true momentum muReconstructible;[GeV/c];N',dpaxis,50,0.,200.)
   ut.bookHist(h,'Pz','true momentum muReconstructible;[GeV/c];N',dpaxis,50,0.,200.)
   ut.bookHist(h,'Preco', 'true momentum reconstructed;[GeV/c];N',dpaxis,50,0.,200.)
   ut.bookHist(h,'Pzreco','true momentum reconstructed;[GeV/c];N',dpaxis,50,0.,200.)
   ut.bookHist(h,'Pt','true momentum muReconstructible;[GeV/c];N',80,0.,4.,50,0.,200.)
   ut.bookHist(h,'Px','true momentum muReconstructible;[GeV/c];N',80,0.,4.,50,0.,200.)
   ut.bookHist(h,'Ptreco','true momentum reconstructed;[GeV/c];N',80,0.,4.,50,0.,200.)
   ut.bookHist(h,'Pxreco','true momentum reconstructed;[GeV/c];N',80,0.,4.,50,0.,200.)
   ut.bookHist(h,'delx/y','delx vs dely;cm;cm',100,-20.,20,100,-50.,50.)
   for x in ['','_mu']:
    ut.bookHist(h,'delP'+x,"reconstructed P - true ",1000,-50.,50.)
    ut.bookHist(h,'delPt'+x,"reconstructed Pt - true ",1000,-1.,1.)
    ut.bookHist(h,'delPx'+x,"reconstructed Px - true ",1000,-1.,1.)
   for n in range(sTree.GetEntries()):
    rc = sTree.GetEvent(n)
    if sTree.MCRecoDT.size() != 1: continue # look at 1 Track events for the moment 
    upStreamOcc = sTree.stationOcc[1]+sTree.stationOcc[5]+sTree.stationOcc[2]+sTree.stationOcc[6]
    for m in sTree.MCRecoRPC:
       i = -1
       for d in sTree.MCRecoDT:
         i+=1
         if m!=d: continue  # require same MCTrack
         P  = ROOT.TVector3(sTree.MCRecoDTpx[i],sTree.MCRecoDTpy[i],sTree.MCRecoDTpz[i])
         rc = h['P'].Fill(P.Mag(),upStreamOcc)
         rc = h['Px'].Fill(abs(P.X()),upStreamOcc)
         rc = h['Pz'].Fill(P.Z(),upStreamOcc)
         rc = h['Pt'].Fill(P.Pt(),upStreamOcc)
         found = False  # avoid double counting
         for t in range(sTree.nTr):
           Preco  = ROOT.TVector3(sTree.Px[t],sTree.Py[t],sTree.Pz[t])
           delP   = P.Mag() - Preco.Mag()
           delPx  = P.X() -   Preco.X()
           delPt  = P.Pt() -  Preco.Pt()
           rc = h['delP'].Fill(delP,P.Mag())
           rc = h['delPx'].Fill(delPx,P.Mag())
           rc = h['delPt'].Fill(delPt,P.Mag())
           rc = h['delx/y'].Fill(sTree.Delx[t],sTree.Dely[t])
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
#         if not found:
#           print "event nr ",n,P.Mag(),upStreamOcc

   ut.writeHists(h,'histos-MCRecoEffFunOfOcc.root')
 if not hMC.has_key('P'): 
   ut.readHists(h,'histos-MCRecoEffFunOfOcc.root')
 if not hData.has_key('Occ'): 
   ut.readHists(h,'histos-DataOcc.root')
 c = 'MC'
 sTree = case[c][0]
 h = case[c][1]
 tmp = h['P'].ProjectionY()
 T = ROOT.TLatex()
 T.SetTextColor(ROOT.kMagenta)
 variables = ['P','Px','Pz','Pt']
 fun = {}
 for var in variables:
  xmin = tmp.GetBinLowEdge(1)
  xmax = tmp.GetBinLowEdge(tmp.GetNbinsX())+tmp.GetBinWidth(tmp.GetNbinsX())
  ut.bookHist(h,'effFun'+var,'eff as function of occupancy '+var,tmp.GetNbinsX(),xmin,xmax)
  ut.bookCanvas(h,'eff'+var,'Efficiencies '+var,1200,900,5,4)
  if var=='P' or var=='Pz': fun[var] = ROOT.TF1('pol0'+var,'[0]',12.,100.)
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
    t = str(int(tmp.GetBinLowEdge(o)))+"-"+str(int(tmp.GetBinLowEdge(o)+tmp.GetBinWidth(o)))
    rc = T.DrawLatexNDC(0.5,0.9,t)
    rc = h[var+'eff'+str(o)].Fit(fun[var],'SRQ')
    fitResult = rc.Get()
    if fitResult:
      eff = fitResult.Parameter(0)
      rc = T.DrawLatexNDC(0.2,0.9,"eff=%5.2F%%"%(eff*100.))
      h['effFun'+var].SetBinContent(o,eff)
    tc.Update()
 ut.bookCanvas(h,'eff final','Efficiencies ',1200,900,2,2)
 j=1
 h['occ']=tmp.Clone('occ')
 h['occ'].Scale(1./tmp.GetMaximum())
 h['occ'].SetLineColor(ROOT.kMagenta)
 for var in variables:
   h['eff final'].cd(j)
   j+=1
   h['effFun'+var].Draw()
   h['occ'].Draw('same hist')
 var = 'P'
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
 print "and the final answer is for Data: %5.2F%%"%(finalEff*100)
 # now take occupancy from zero field
 hDTEff = {}
 ut.readHists(hDTEff,'DTEff.root',['upStreamOccWithTrack','upStreamOcc'])
 h['zeroFieldOcc']=hDTEff['upStreamOccWithTrack'].Rebin(4,'zeroFieldOcc')
 finalEff  = 0
 sumEvents = 0
 for o in range(1,hData['Occ'].GetNbinsX()+1):
   finalEff+=hData['Occ'].GetBinContent(o)*h['effFun'+var].GetBinContent(o)
   sumEvents+=hData['Occ'].GetBinContent(o)
 finalEff=finalEff/sumEvents
 print "and the final answer is for zeroField Data: %5.2F%%"%(finalEff*100)


  
