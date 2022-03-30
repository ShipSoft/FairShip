#!/usr/bin/env python
import ROOT
import os,sys,subprocess
import time
import ctypes
from array import array
import rootUtils as ut
import shipunit as u
import SndlhcGeo

class Monitoring():
   " set of monitor histograms "
   def __init__(self,options,FairTasks):
        self.options = options
# MuFilter mapping of planes and bars 
        self.systemAndPlanes  = {1:2,2:5,3:7}
        self.systemAndBars     = {1:7,2:10,3:60}
        self.systemAndChannels     = {1:[8,0],2:[6,2],3:[1,0]}
        self.sdict                     = {1:'Veto',2:'US',3:'DS'}

        self.freq      = 160.E6
        self.TDC2ns = 1E9/self.freq

        path     = options.path
        if path.find('eos')>0:
             path  = os.environ['EOSSHIP']+options.path
        if options.online:
             path = path.replace("raw_data","convertedData").replace("data/","")

# setup geometry
        if (options.geoFile).find('../')<0: self.snd_geo = SndlhcGeo.GeoInterface(path+options.geoFile)
        else:                                         self.snd_geo = SndlhcGeo.GeoInterface(options.geoFile[3:])
        self.MuFilter = self.snd_geo.modules['MuFilter']
        self.Scifi       = self.snd_geo.modules['Scifi']
        self.h = {}   # histogram storage

# setup input
        if options.online:
            self.eventTree = options.online.fSink.GetOutTree
            return
        else:
            self.runNr   = str(options.runNumber).zfill(6)
            partitions = 0
            if path.find('eos')>0:
                dirlist  = str( subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+options.path,shell=True) )
# single file, before Feb'22
                data = "sndsw_raw_"+self.runNr+".root"
                if  dirlist.find(data)<0:
# check for partitions
                   dirlist  = str( subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+options.path+"run_"+self.runNr,shell=True) )
                   while 1>0:
                      data = "raw-"+ str(partitions).zfill(4)
                      if dirlist.find(data)>0:
                           partitions+=1
                      else: break
            else:
# check for partitions
                 data = "sndsw_raw_"+self.runNr+".root"
                 dirlist = os.listdir(options.path)
                 if  not data in dirlist:
                     dirlist  = os.listdir(options.path+"run_"+self.runNr)
                     for x in dirlist:
                         data = "raw-"+ str(partitions).zfill(4)
                         if x.find(data)>0:
                             partitions+=1

            if options.runNumber>0:
                eventChain = ROOT.TChain('rawConv')
                if partitions==0:
                   eventChain.Add(path+'sndsw_raw_'+str(options.runNumber).zfill(6)+'.root')
                else:
                   for p in range(partitions):
                       print(partitions,path+'run_'+self.runNr+'/sndsw_raw-'+str(p).zfill(4)+'.root')
                       eventChain.Add(path+'run_'+self.runNr+'/sndsw_raw-'+str(p).zfill(4)+'.root')
            else:
# for MC data
                f=ROOT.TFile.Open(options.fname)
                eventChain = f.cbmsim

            rc = eventChain.GetEvent(0)
# start FairRunAna
            self.run      = ROOT.FairRunAna()
            ioman = ROOT.FairRootManager.Instance()
            ioman.SetTreeName(eventChain.GetName())
            outFile = ROOT.TMemFile('dummy','CREATE')
            source = ROOT.FairFileSource(eventChain.GetCurrentFile())
            if partitions>0:
                  for p in range(1,partitions):
                       source.AddFile(path+'run_'+self.runNr+'/sndsw_raw-'+str(p).zfill(4)+'.root')
            self.run.SetSource(source)
            sink = ROOT.FairRootFileSink(outFile)
            self.run.SetSink(sink)

            for t in FairTasks: 
                self.run.AddTask(t)

#avoiding some error messages
            xrdb = ROOT.FairRuntimeDb.instance()
            xrdb.getContainer("FairBaseParSet").setStatic()
            xrdb.getContainer("FairGeoParSet").setStatic()

            self.run.Init()
            if partitions>0:  self.eventTree = ioman.GetInChain()
            else:                 self.eventTree = ioman.GetInTree()

   def GetEvent(self,n):
      if self.options.online:
            self.options.online.executeEvent(n)
            self.eventTree = self.options.online.sTree
      else: 
            self.eventTree.GetEvent(n)
      return self.eventTree

   def systemAndOrientation(self,s,plane):
      if s==1 or s==2: return "horizontal"
      if plane%2==1 or plane == 6: return "vertical"
      return "horizontal"

   def getAverageZpositions(self):
      zPos={'MuFilter':{},'Scifi':{}}
      for s in systemAndPlanes:
          for plane in range(systemAndPlanes[s]):
             bar = 4
             p = plane
             if s==3 and (plane%2==0 or plane==7): 
                bar = 90
                p = plane//2
             elif s==3 and plane%2==1:
                bar = 30
                p = plane//2
             self.MuFilter.GetPosition(s*10000+p*1000+bar,A,B)
             zPos['MuFilter'][s*10+plane] = (A.Z()+B.Z())/2.
      for s in range(1,6):
         mat   = 2
         sipm = 1
         channel = 64
         for o in range(2):
             self.Scifi.GetPosition(channel+1000*sipm+10000*mat+100000*o+1000000*s,A,B)
             zPos['Scifi'][s*10+o] = (A.Z()+B.Z())/2.
      return zPos

   def smallSiPMchannel(self,i):
      if i==2 or i==5 or i==10 or i==13: return True
      else: return False

#  Scifi specific code
   def Scifi_xPos(self,detID):
        orientation = (detID//100000)%10
        nStation = 2*(detID//1000000-1)+orientation
        mat   = (detID%100000)//10000
        X = detID%1000+(detID%10000)//1000*128
        return [nStation,mat,X]   # even numbers are Y (horizontal plane), odd numbers X (vertical plane)

   def fit_langau(self,hist,o,bmin,bmax,opt=''):
      if opt == 2:
         params = {0:'Width(scale)',1:'mostProbable',2:'norm',3:'sigma',4:'N2'}
         F = ROOT.TF1('langau',langaufun,0,200,len(params))
      else:
         params = {0:'Width(scale)',1:'mostProbable',2:'norm',3:'sigma'}
         F = ROOT.TF1('langau',twoLangaufun,0,200,len(params))
      for p in params: F.SetParName(p,params[p])
      rc = hist.Fit('landau','S'+o,'',bmin,bmax)
      res = rc.Get()
      if not res: return res
      F.SetParameter(2,res.Parameter(0))
      F.SetParameter(1,res.Parameter(1))
      F.SetParameter(0,res.Parameter(2))
      F.SetParameter(3,res.Parameter(2))
      F.SetParameter(4,0)
      F.SetParLimits(0,0,100)
      F.SetParLimits(1,0,100)
      F.SetParLimits(3,0,10)
      rc = hist.Fit(F,'S'+o,'',bmin,bmax)
      res = rc.Get()
      return res

   def twoLangaufun(self,x,par):
      N1 = self.langaufun(x,par)
      par2 = [par[0],par[1]*2,par[4],par[3]]
      N2 = self.langaufun(x,par2)
      return N1+abs(N2)

   def  langaufun(self,x,par):
   #Fit parameters:
   #par[0]=Width (scale) parameter of Landau density
   #par[1]=Most Probable (MP, location) parameter of Landau density
   #par[2]=Total area (integral -inf to inf, normalization constant)
   #par[3]=Width (sigma) of convoluted Gaussian function
   #
   #In the Landau distribution (represented by the CERNLIB approximation),
   #the maximum is located at x=-0.22278298 with the location parameter=0.
   #This shift is corrected within this function, so that the actual
   #maximum is identical to the MP parameter.
#
      # Numeric constants
      invsq2pi = 0.3989422804014   # (2 pi)^(-1/2)
      mpshift  = -0.22278298       # Landau maximum location
#
      # Control constants
      np = 100.0      # number of convolution steps
      sc =   5.0      # convolution extends to +-sc Gaussian sigmas
#
      # Variables
      summe = 0.0
#
      # MP shift correction
      mpc = par[1] - mpshift * par[0]
#
      # Range of convolution integral
      xlow = max(0,x[0] - sc * par[3])
      xupp = x[0] + sc * par[3]
#
      step = (xupp-xlow) / np
#
      # Convolution integral of Landau and Gaussian by sum
      i=1.0
      if par[0]==0 or par[3]==0: return 9999
      while i<=np/2:
         i+=1
         xx = xlow + (i-.5) * step
         fland = ROOT.TMath.Landau(xx,mpc,par[0]) / par[0]
         summe += fland * ROOT.TMath.Gaus(x[0],xx,par[3])
#
         xx = xupp - (i-.5) * step
         fland = ROOT.TMath.Landau(xx,mpc,par[0]) / par[0]
         summe += fland * ROOT.TMath.Gaus(x[0],xx,par[3])
#
      return (par[2] * step * summe * invsq2pi / par[3])

   def myPrint(self,tc,name,withRootFile=True):
     tc.Update()
     tc.Print(name+'-run'+str(self.options.runNumber)+'.png')
     tc.Print(name+'-run'+str(self.options.runNumber)+'.pdf')
     if withRootFile: tc.Print(name+'-run'+str(self.options.runNumber)+'.root')

