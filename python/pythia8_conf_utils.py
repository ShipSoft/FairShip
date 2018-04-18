import ROOT, os, sys
import shipunit as u

def addHNLtoROOT(pid=9900015 ,m = 1.0, g=3.654203020370371E-21):
    pdg = ROOT.TDatabasePDG.Instance()                                                                        
    pdg.AddParticle('N2','HNL', m, False, g, 0., 'N2', pid) 

def readFromAscii(filename="branchingratios"):
    FairShip = os.environ['FAIRSHIP'] 
    ascii = open(FairShip+'/shipgen/%s.dat'%filename)
    h={}
    content = ascii.readlines()
    n = 0
    while n<len(content):
       line = content[n]
       if not line.find('TH1F')<0:
          keys = line.split('|')
          n+=1
          limits = content[n].split(',')
          hname = keys[1]
          if len(keys)<5: keys.append(',') 
          h[ hname ] = ROOT.TH1F(hname,keys[2]+';'+keys[3]+';'+keys[4],int(limits[0]),float(limits[1]),float(limits[2]) )
       else:
          keys = line.split(',')
          h[ hname ].SetBinContent(int(keys[0]),float(keys[1]) )
       n+=1
    return h

def getbr(h,histoname,mass,coupling):
    #0 MeV< mass < 3.200 GeV 
    mass = int(mass*1000) 
    try:
        br=h[histoname].GetBinContent(mass)
        br=br*coupling
    except:
        br=0
    return br

def getmaxsumbr(h,histograms,mass,couplings,totaltaubr):
    #0 MeV< mass < 3.200 GeV 
    maxsumbr=0.0
    sumbrs={}
    brdstauadded=0
    leptons=['e','mu','tau'] 
    for histoname in histograms:
       item = histoname.split('_') 
       lepton = item[len(item)-1]
       meson = item[0]
       try:
          coupling=couplings[leptons.index(lepton)]
       except:
          coupling=couplings[2] 
       if histoname[:3]=='tau': 
          coupling=couplings[2]
       if not sumbrs.has_key(meson):sumbrs[meson]=0
       sumbrs[meson]+=getbr(h,histoname,mass,coupling)
       if meson=="ds" and brdstauadded==0 and totaltaubr>0.:
          sumbrs[meson]+=totaltaubr
	  brdstauadded=1       	  
    maxsumbr=max(sumbrs.values())
    return maxsumbr

def getmaxsumbrrpvsusy(h,histograms,mass,couplings):
    #0 MeV< mass < 3.200 GeV 
    maxsumbr=0.0
    sumbrs={}
    for histoname in histograms: 
       item = histoname.split('_') 
       lepton = item[len(item)-1]
       meson = item[0]
       coupling=couplings[1]
       try:
           sumbrs[meson]+=getbr(h,histoname,mass,coupling)
       except:
           sumbrs[meson]=getbr(h,histoname,mass,coupling)
    print sumbrs.values()
    maxsumbr=max(sumbrs.values())
    return maxsumbr

def gettotalbr(h,histograms,mass,couplings,totaltaubr):
    totalbr=0.0 
    leptons=['e','mu','tau'] 
    for histoname in histograms: 
       item = histoname.split('_') 
       lepton = item[len(item)-1]
       try:
          coupling=couplings[leptons.index(lepton)] 
       except:
          coupling=couplings[2] 
       if histoname[:3]=='tau': coupling=couplings[2] 
       totalbr+=getbr(h,histoname,mass,coupling)
    return totalbr

def gettotalbrrpvsusy(h,histograms,mass,couplings):
    totalbr=0.0 
    for histoname in histograms: 
       item = histoname.split('_') 
       coupling=couplings[1]
       totalbr+=getbr(h,histoname,mass,coupling)
    return totalbr

def setChannels(P8gen,h,channels,mass,couplings,maxsumBR):
     pdg = P8gen.getPythiaInstance().particleData
     sumBR = 0
     for channel in channels:
         br = getbr(h,channel['decay'],mass,couplings[channel['coupling']])
         if br>0:
           if channel['id']=='15':
            if len(channel)==4:
             P8gen.SetParameters(channel['id']+":addChannel      1  "+str(br/maxsumBR)+"    1521       9900015      "+str(channel['idhadron']))
            else:
             P8gen.SetParameters(channel['id']+":addChannel      1  "+str(br/maxsumBR)+"    1531       9900015      "+str(channel['idlepton'])+" "+str(channel['idhadron']))
           elif len(channel)==4:
            P8gen.SetParameters(channel['id']+":addChannel      1  "+str(br/maxsumBR)+"    0       9900015      "+str(channel['idlepton']))
           else:
            P8gen.SetParameters(channel['id']+":addChannel      1  "+str(br/maxsumBR)+"   22      "+str(channel['idlepton'])+"       9900015   "+str(channel['idhadron']))
           sumBR+=br/maxsumBR
     if sumBR<1. and sumBR>0.:
           charge = pdg.charge(int(channel['id']))
           if charge>0:
            P8gen.SetParameters("431:addChannel      1   "+str(1.-sumBR)+"    0       22      -11")
           elif charge<0:
            P8gen.SetParameters("431:addChannel      1   "+str(1.-sumBR)+"    0       22       11")
           else:
            P8gen.SetParameters(channel['id']+":addChannel      1   "+str(1.-sumBR)+"    0       22      22")

