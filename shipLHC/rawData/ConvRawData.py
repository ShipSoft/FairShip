#!/usr/bin/env python
import ROOT,os,sys
import boardMappingParser
import csv
import time

# raw data from Ettore: https://cernbox.cern.ch/index.php/s/Ten7ilKuD3qdnM2 

class ConvRawDataPY(ROOT.FairTask):
   " raw data conversion by event "
   def Init(self,options):
      self.debug        = options.debug
      self.monitoring = options.online
      local = False
      if (options.path.find('eos')<0 and not options.online) or os.path.isdir(options.path):    local = True
      if local: server = ''
      else:
           server = os.environ['EOSSHIP']
           from XRootD import client
           # https://xrootd.slac.stanford.edu/doc/python/xrootd-python-0.1.0/examples.html
      if options.runNumber>0: 
         runNr   = str(options.runNumber).zfill(6)
         path      = options.path+'run_'+ runNr+'/'
         if options.partition < 0:
             inFile   = 'data.root'
             self.outFile = "sndsw_raw_"+runNr+'.root'
         else:
             part = str(options.partition).zfill(4)
             inFile   = 'data_'+part+'.root'
             self.outFile = "sndsw_raw_"+runNr+'-'+part+'.root'
      if self.monitoring:  # this is an online stream
         server = options.server
         runNr   = str( abs(options.runNumber) ).zfill(6)
         path    = options.path+'run_'+ runNr+'/'
         inFile   = 'data_'+part+'.root'
         self.outFile = ROOT.TMemFile('monitorRawData', 'recreate')

      self.run     = ROOT.FairRunAna()
      ioman = ROOT.FairRootManager.Instance()
# open input file
      self.fiN=ROOT.TFile.Open(server+path+inFile)
      self.nEvents = 1
      if not self.monitoring:
           if options.nEvents<0:  self.nEvents = self.fiN.event.GetEntries()
           else: self.nEvents = min(options.nEvents,self.fiN.event.GetEntries())
           print('converting ',self.nEvents,' events ',' of run',options.runNumber)
  # Pass input parameters to the task - runN, paths, etc.
      ioman.RegisterInputObject('runN', ROOT.TObjString(str(options.runNumber)))
      ioman.RegisterInputObject('path', ROOT.TObjString(path))
      ioman.RegisterInputObject('nEvents', ROOT.TObjString(str(self.nEvents)))
      ioman.RegisterInputObject('nStart', ROOT.TObjString(str(options.nStart)))
      ioman.RegisterInputObject('debug', ROOT.TObjString(str(options.debug)))
      ioman.RegisterInputObject('stop', ROOT.TObjString(str(options.stop)))
      ioman.RegisterInputObject('heartBeat', ROOT.TObjString(str(options.heartBeat)))
      ioman.RegisterInputObject('withGeoFile', ROOT.TObjString(str(options.withGeoFile)))
      self.options = options
  # Pass raw data file as input object
      ioman.RegisterInputObject("rawData", self.fiN)

  # Set output
      if self.monitoring:  self.outfile = ROOT.FairRootFileSink(self.outFile)
      else:                     self.outfile = ROOT.FairRootFileSink(self.outFile.replace('.root','_CPP.root'))
      self.run.SetSink(self.outfile)

  # Don't use FairRoot's default event header settings
      self.run.SetEventHeaderPersistence(False)
      self.xrdb = ROOT.FairRuntimeDb.instance()
      self.xrdb.getContainer("FairBaseParSet").setStatic()
      self.xrdb.getContainer("FairGeoParSet").setStatic()
# Fair convRawData task
      if options.FairTask_convRaw:
          self.run.AddTask(ROOT.ConvRawData())
          self.run.Init()

#-------end of init for cpp ------------------------------------
      else:
       if options.makeCalibration:
         if  local:
           fqdc_cal = open(path+'/qdc_cal.csv')
           Lqdc = fqdc_cal.readlines()
           ftdc_cal = open(path+'/tdc_cal.csv')
           Ltdc = ftdc_cal.readlines()
         else:
           with client.File() as f:
               f.open(server+path+"/qdc_cal.csv")
               status, L = f.read()
               Lqdc = L.decode().split('\n')
               f.close()
               f.open(server+path+"/tdc_cal.csv")
               status, L = f.read()
               Ltdc = L.decode().split('\n')
               f.close()
  # calibration data
         self.qdc_cal = {}
         qdc_cal = self.qdc_cal
         L = Lqdc
         for l in range(1,len(L)):
               tmp = L[l].replace('\n','').split(',')
               if len(tmp)<10:continue
               board_id = int(tmp[0])
               if not board_id in qdc_cal: qdc_cal[board_id]={}
               fe_id = int(tmp[1])
               if not fe_id in qdc_cal[board_id]: qdc_cal[board_id][fe_id]={}
               channel = int(tmp[2])
               if not channel in qdc_cal[board_id][fe_id]: qdc_cal[board_id][fe_id][channel]={}
               tac = int(tmp[3])
               if not tac in qdc_cal[board_id][fe_id][channel]: qdc_cal[board_id][fe_id][channel][tac]={}
               X = qdc_cal[board_id][fe_id][channel][tac]
               X['a']=float(tmp[4])
               X['b']=float(tmp[5])
               X['c']=float(tmp[6])
               X['d']=float(tmp[8])
               X['e']=float(tmp[10])
               if float(tmp[9]) < 2: X['chi2Ndof'] = 999999.
               else:                  X['chi2Ndof']=float(tmp[7])/float(tmp[9])

         L=Ltdc
         for l in range(1,len(L)):
               tmp = L[l].replace('\n','').split(',')
               if len(tmp)<9:continue
               board_id = int(tmp[0])
               if not board_id in qdc_cal: qdc_cal[board_id]={}
               fe_id = int(tmp[1])
               if not fe_id in qdc_cal[board_id]: qdc_cal[board_id][fe_id]={}
               channel = int(tmp[2])
               if not channel in qdc_cal[board_id][fe_id]: qdc_cal[board_id][fe_id][channel]={}
               tac = int(tmp[3])
               if not tac in qdc_cal[board_id][fe_id][channel]: qdc_cal[board_id][fe_id][channel][tac]={}
               tdc = int(tmp[4])
               if not tdc in qdc_cal[board_id][fe_id][channel][tac]: qdc_cal[board_id][fe_id][channel][tac][tdc]={}
               X = qdc_cal[board_id][fe_id][channel][tac][tdc]
               X['a']=float(tmp[5])
               X['b']=float(tmp[6])
               X['c']=float(tmp[7])
               X['d']=float(tmp[9])
               if float(tmp[10]) < 2: X['chi2Ndof'] = 999999.
               else:                  X['chi2Ndof']=float(tmp[8])/float(tmp[10])

  # read MuFilter mappings of SiPM channel to tofpet_id and tofpet_channel
       SiPMmap={}
       self.TofpetMap = {}
       key = {'DS':2,'US':1,'Veto':0}
       sndswPath = os.environ['SNDSW_ROOT']
       for system in key:
           infile = sndswPath+"/geometry/"+system+"_SiPM_mapping.csv"
           SiPMmap[system] = {}
           if os.path.isdir(sndswPath+"/geometry"):
               with open(infile, "r") as f:
                   reader = csv.DictReader(f, delimiter=',')
                   for i, row in enumerate(reader):
                       SiPMmap[system][int(row['SiPM'])] = [int(row['CN']), int(row['pin']), int(row['TOFPET']), int(row['CHANNEL'])]
                   self.TofpetMap[key[system]] = {}
                   for channel in SiPMmap[system]:
                      row = SiPMmap[system][channel]
                      self.TofpetMap[key[system]][row[2]*1000+row[3]] = channel
       if local:
           with open(path+'board_mapping.json') as f:
               jsonStr = f.read()
       else:
           with client.File() as f:
                f.open(server+path+"/board_mapping.json")
                status, jsonStr = f.read()
  # pass the read string to getBoardMapping()
       self.boardMaps = boardMappingParser.getBoardMapping(jsonStr)

       self.slots = {0:'A',1:'A',2:'B',3:'B',4:'C',5:'C',6:'D',7:'D'}

       self.MufiSystem = {}
       for b in self.boardMaps['MuFilter']:
           board_id = int(b.split('_')[1])
           self.MufiSystem[board_id]={}
           for x in self.boardMaps['MuFilter'][b]:
               for slot in self.slots:
                  s = 0
                  tmp = self.boardMaps['MuFilter'][b][x].split('_')[0]
                  if tmp=='US': s = 1
                  elif tmp=='DS': s = 2
                  if self.slots[slot]==x: self.MufiSystem[board_id][slot]=s

       self.offMap={}
                                        # first bar, number of sipm channels / bar and direction
       for s in range(1,3):
           for o in ['Left','Right']: 
              self.offMap['Veto_'+str(s)+o] =[10000 + (s-1)*1000+ 0,8,2]    # first channel, nSiPMs, nSides, from bottom to top
       for s in range(1,6):
           for o in ['Left','Right']: 
              self.offMap['US_'+str(s)+o] =[20000 + (s-1)*1000+ 9,-8,2]     # from top to bottom
       for s in range(1,5):
           for o in ['Vert']: 
              self.offMap['DS_'+str(s)+o] =[30000 + (s-1)*1000+ 119, -1,1] # direction not known
           if s>3: continue
           for o in ['Left','Right']: 
              self.offMap['DS_'+str(s)+o] =[30000 + (s-1)*1000+ 59,-1,2]   # direction not known

       self.boards = {}
       for b in self.fiN.GetListOfKeys():
          name = b.GetName()
          if name.find('board')!=0: continue
          self.boards[name]=self.fiN.Get(name)

       self.fSink  = ROOT.FairRootFileSink(self.outFile)
       self.sTree = ROOT.TTree('rawConv','raw data converted')
       ROOT.gDirectory.pwd()
       self.header  = ROOT.FairEventHeader()
       eventSND  = self.sTree.Branch("EventHeader",self.header,32000,-1)

       self.digiSciFi   = ROOT.TClonesArray("sndScifiHit")
       self.digiSciFiBranch   = self.sTree.Branch("Digi_ScifiHits",self.digiSciFi,32000,1)
       self.digiMuFilter   = ROOT.TClonesArray("MuFilterHit")
       self.digiMuFilterHitBranch   = self.sTree.Branch("Digi_MuFilterHits",self.digiMuFilter,32000,1)
  #scifi clusters
       if self.options.withGeoFile:
           self.clusScifi   = ROOT.TClonesArray("sndCluster")
           self.clusScifiBranch    = self.sTree.Branch("Cluster_Scifi",self.clusScifi,32000,1)
           self.scifiDet = ROOT.gROOT.GetListOfGlobals().FindObject('Scifi')

       B = ROOT.TList()
       B.SetName('BranchList')
       B.Add(ROOT.TObjString('sndScifiHit'))
       B.Add(ROOT.TObjString('MuFilterHit'))
       B.Add(ROOT.TObjString('FairEventHeader'))
       self.fSink.WriteObject(B,"BranchList", ROOT.TObject.kSingleKey)

#-------end of init for py ------------------------------------

   def channel(self,tofpet_id,tofpet_channel,position):
      return (64 * tofpet_id + 63 - tofpet_channel + 512*position) # 512 channels per mat, 1536 channels per plane
                                                                                                                                     # one channel covers all 6 layers of fibres

  # following procedure in https://gitlab.cern.ch/scifi-telescope/scifi-rec/-/blob/ettore-tofpet/lib/processors/applycalibration.cpp
   def qdc_chi2(self,board_id,tofpet_id,channel,tac,TDC=0):
      qdc_cal = self.qdc_cal
      par    = qdc_cal[board_id][tofpet_id][channel][tac]
      parT = qdc_cal[board_id][tofpet_id][channel][tac][TDC]
      return max(par['chi2Ndof'],parT['chi2Ndof'])

   def qdc_sat(self,board_id,tofpet_id,channel,tac,v_fine):
      qdc_cal = self.qdc_cal
      par = qdc_cal[board_id][tofpet_id][channel][tac]
      return v_fine/par['d']
    
   def comb_calibration(self,board_id,tofpet_id,channel,tac,v_coarse,v_fine,t_coarse,t_fine,GQDC = 1.0, TDC=0): # max gain QDC = 3.6
      qdc_cal = self.qdc_cal
      par  = qdc_cal[board_id][tofpet_id][channel][tac]
      parT = par[TDC]
      x    = t_fine
      ftdc = (-parT['b']-ROOT.TMath.Sqrt(parT['b']**2-4*parT['a']*(parT['c']-x)))/(2*parT['a']) #   Ettore 28/01/2022 +parT['d']
      timestamp = t_coarse + ftdc
      tf = timestamp - t_coarse
      x = v_coarse - tf
      fqdc = -par['c']*ROOT.TMath.Log(1+ROOT.TMath.Exp( par['a']*(x-par['e'])**2-par['b']*(x-par['e']) )) + par['d']
      value = (v_fine-fqdc)/GQDC
      return timestamp,value,max(par['chi2Ndof'],parT['chi2Ndof']),v_fine/par['d']

   def calibrationReport(self):
      qdc_cal = self.qdc_cal
      report = {}
      TDC = 0
      for b in qdc_cal:
           for t in  qdc_cal[b]:
                for c in qdc_cal[b][t]:
                     for tac in qdc_cal[b][t][c]:
                               par    = qdc_cal[b][t][c][tac]
                               if 'chi2Ndof' in par:                             chi2 = par['chi2Ndof']
                               else: chi2=-1
                               parT = qdc_cal[b][t][c][tac][TDC]
                               if 'chi2Ndof' in parT:   chi2T = parT['chi2Ndof']
                               else: chi2T=-1
                               key = tac +10*c + t*10*100 + b*10*100*100
                               if not key in report: report[key]=[chi2,chi2T]
      return report

   def debugMapping(self,board,tofpet_id,tofpet_channel):
                  key = (tofpet_id%2)*1000 + tofpet_channel
                  tmp = boardMaps['MuFilter'][board][self.slots[tofpet_id]]
                  sipmChannel = TofpetMap[system][key]-1
                  nSiPMs =   abs(offMap[tmp][1])
                  nSides =   abs(offMap[tmp][2])
                  direction            = int(offMap[tmp][1]/nSiPMs)
                  detID                   = offMap[tmp][0] + direction*(sipmChannel//(nSiPMs))
                  sipm_number = sipmChannel%(nSiPMs)
                  print(sipmChannel,nSiPMs,nSides,detID,sipm_number)

   def printChannelInfo(self):
         runNr   = str( abs(self.options.runNumber) ).zfill(6)
         path    = self.options.path+'run_'+ runNr+'/'
         from XRootD import client
         with client.File() as f:
               f.open(self.options.server+path+"/channels.csv")
               status, L = f.read()
               self.Lchannel = L.decode().split('\n')
               f.close()
         for l in self.Lchannel: print(l)

   def printCurrentRun(self):
         filename = "currently_processed_file.txt"
         path    = self.options.path
         from XRootD import client
         with client.File() as f:
               f.open(self.options.server+path+filename)
               status, L = f.read()
               self.Lcrun = L.decode().split('\n')
               f.close()
         for l in self.Lcrun: print(l)

  # reading hits and converting to event information

  # https://gitlab.cern.ch/snd-scifi/software/-/wikis/Raw-data-format 
  # tac: 0-3, identifies the Time-To-Analogue converter used for this hit (each channel has four of them and they require separate calibration).
  # t_coarse: Coarse timestamp of the hit, running on a 4 times the LHC clock
  # t_fine: 0-1023, fine timestamp of the hit. It contains the raw value of the charge digitized by the TDC and requires calibration.
  # v_coarse: 0-1023, QDC mode: it represents the number of clock cycles the charge integration lasted.
  # v_fine = 0-1023, QDC mode: represents the charge measured. Requires calibration.

   def Run(self):
      if self.options.FairTask_convRaw:
          self.run.Run(self.options.nStart, self.nEvents)
      else:
          for eventNumber in range(self.options.nStart,self.nEvents):
             self.executeEvent(eventNumber)
   def executeEvent(self,eventNumber):
     if eventNumber%self.options.heartBeat==0 or self.debug:
               print('run ',self.options.runNumber, ' event',eventNumber," ",time.ctime())
     event = self.fiN.event
     rc = event.GetEvent(eventNumber)
     self.header.SetEventTime(event.timestamp)
     self.header.SetRunId( self.options.runNumber )

     indexSciFi=0
     self.digiSciFi.Delete()
     digiSciFiStore = {}
     indexMuFilter = 0
     self.digiMuFilter.Delete()
     digiMuFilterStore = {}
     if self.options.withGeoFile:
           self.clusScifi.Delete()

     for board in self.boards:
        board_id = int(board.split('_')[1])
        scifi = True
        if board in self.boardMaps['Scifi']:
            station,mat = self.boardMaps['Scifi'][board]
        elif board in self.boardMaps['MuFilter']:
            scifi = False
        else: 
             print(board+' not known. Serious error, stop')
             1/0
        bt = self.boards[board]
        rc  = bt.GetEvent(eventNumber)
        for n in range(bt.n_hits):
           mask = False
           tofpet_id = bt.tofpet_id[n]
           tofpet_channel = bt.tofpet_channel[n]
           if self.options.makeCalibration:
               if self.options.debug:
                    print(scifi,board_id,bt.tofpet_id[n],bt.tofpet_channel[n],bt.tac[n],bt.t_coarse[n],bt.t_fine[n],bt.v_coarse[n],bt.v_fine[n])
               tac = bt.tac[n]
               TDC,QDC,Chi2ndof,satur = self.comb_calibration(board_id,tofpet_id,tofpet_channel,tac,bt.v_coarse[n],bt.v_fine[n],bt.t_coarse[n],bt.t_fine[n])
           else:
               TDC = bt.timestamp[n]
               QDC = bt.value[n]
               Chi2ndof = 1
               satur = 0.
           if Chi2ndof > self.options.chi2Max:
                         if QDC>1E20:    QDC = 997.   # checking for inf
                         if QDC != QDC:  QDC = 998.   # checking for nan
                         if QDC>0: QDC = -QDC
                         mask = True
           elif satur  > self.options.saturationLimit or QDC>1E20 or QDC != QDC:
                         if QDC>1E20:    QDC = 987.   # checking for inf
                         if self.options.debug: 
                                print('inf',board_id,bt.tofpet_id[n],bt.tofpet_channel[n],bt.tac[n],bt.v_coarse[n],bt.v_fine[n],TDC-bt.t_coarse[n],eventNumber,Chi2ndof)
                         if QDC != QDC:  QDC = 988.   # checking for nan
                         if self.options.debug: 
                                 print('nan',board_id,bt.tofpet_id[n],bt.tofpet_channel[n],bt.tac[n],bt.v_coarse[n],bt.v_fine[n],\
                                          TDC-bt.t_coarse[n],TDC,bt.t_coarse[n],eventNumber,Chi2ndof)
                         A = int(min( QDC,1000))
                         B = min(satur,999)/1000.
                         QDC = A+B
                         mask = True
           elif Chi2ndof > self.options.chi2Max:
                         if QDC>0: QDC = -QDC
                         mask = True
           if self.options.debug:
                    print('calibrated: tdc = ',TDC,'  qdc = ',QDC)  # TDC clock cycle = 160 MHz or 6.25ns

           if not scifi:
  # mufi encoding
                  system = self.MufiSystem[board_id][tofpet_id]
                  key = (tofpet_id%2)*1000 + tofpet_channel
                  tmp = self.boardMaps['MuFilter'][board][self.slots[tofpet_id]]
                  if self.options.debug or not tmp.find('not')<0: print('debug',tmp,system,key,board,tofpet_id,tofpet_id%2,tofpet_channel)
                  sipmChannel = 99
                  if not key in self.TofpetMap[system]:
                          print('key does not exist',key)
                          print(system, key,board,tofpet_id, self.TofpetMap[system])
                  else:
                         sipmChannel = self.TofpetMap[system][key]-1
                  nSiPMs = abs(self.offMap[tmp][1])
                  nSides =   abs(self.offMap[tmp][2])
                  direction            = int(self.offMap[tmp][1]/nSiPMs)
                  detID                   = self.offMap[tmp][0] + direction*(sipmChannel//(nSiPMs))
                  sipm_number = sipmChannel%(nSiPMs)
                  if tmp.find('Right')>0:
                         sipm_number += nSiPMs
                  if not detID in digiMuFilterStore:
                          digiMuFilterStore[detID] =  ROOT.MuFilterHit(detID,nSiPMs,nSides)
                  test = digiMuFilterStore[detID].GetSignal(sipm_number)
                  digiMuFilterStore[detID].SetDigi(QDC,TDC,sipm_number)
                  if mask: digiMuFilterStore[detID].SetMasked(sipm_number)

                  if self.options.debug:
                      print('create mu hit: ',detID,tmp,system,tofpet_id,self.offMap[tmp],sipmChannel,nSiPMs,nSides,test)
                      print('                ',detID,sipm_number,QDC,TDC)
                  if test>0 or detID%1000>200 or sipm_number>15:
                      print('what goes wrong?',detID,sipm_number,system,key,board,tofpet_id,tofpet_channel,test)

           else:
  # scifi encoding
                  chan = self.channel(tofpet_id,tofpet_channel,mat)
                  orientation = 1
                  if station[2]=="Y": orientation = 0
                  sipmLocal = (chan - mat*512)
                  sipmID = 1000000*int(station[1]) + 100000*orientation + 10000*mat + 1000*(sipmLocal//128) + chan%128
                  if not sipmID in digiSciFiStore: digiSciFiStore[sipmID] =  ROOT.sndScifiHit(sipmID)
                  digiSciFiStore[sipmID].SetDigi(QDC,TDC)
                  if mask: digiSciFiStore[sipmID].setInvalid()
                  if self.options.debug:
                      print('create scifi hit: tdc = ',board,sipmID,QDC,TDC)
                      print('tofpet:', tofpet_id,tofpet_channel,mat,chan)
                      print(station[1],station[2],mat,chan,int(chan/128)%4,chan%128)

# copy hits to detector branches
     for sipmID in digiSciFiStore:
               if self.digiSciFi.GetSize() == indexSciFi: self.digiSciFi.Expand(indexSciFi+100)
               self.digiSciFi[indexSciFi]=digiSciFiStore[sipmID]
               indexSciFi+=1
     for detID in digiMuFilterStore:
               if self.digiMuFilter.GetSize() == indexMuFilter: self.digiMuFilter.Expand(indexMuFilter+100)
               self.digiMuFilter[indexMuFilter]=digiMuFilterStore[detID]
               indexMuFilter+=1

  # make simple clustering for scifi, only works with geometry file.
     if self.options.withGeoFile:
      index = 0
      hitDict = {}
      for k in range(self.digiSciFi.GetEntries()):
          d = self.digiSciFi[k]
          if not d.isValid(): continue 
          hitDict[d.GetDetectorID()] = k
          hitList = list(hitDict.keys())
          if len(hitList)>0:
                hitList.sort()
                tmp = [ hitList[0] ]
                cprev = hitList[0]
                ncl = 0
                last = len(hitList)-1
                hitlist = ROOT.std.vector("sndScifiHit*")()
                for i in range(len(hitList)):
                     if i==0 and len(hitList)>1: continue
                     c=hitList[i]
                     if (c-cprev)==1: 
                          tmp.append(c)
                     if (c-cprev)!=1 or c==hitList[last]:
                          first = tmp[0]
                          N = len(tmp)
                          hitlist.clear()
                          for aHit in tmp: 
                                  hitlist.push_back( self.digiSciFi[hitDict[aHit]])
                                  if self.options.debug: print(aHit,hitDict[aHit],self.digiSciFi[hitDict[aHit]].GetDetectorID())
                          if self.options.debug: print(hitlist.size())
                          aCluster = ROOT.sndCluster(first,N,hitlist,self.scifiDet,False)
                          if self.options.debug: print("cluster created")
                          if  self.clusScifi.GetSize() == index: self.clusScifi.Expand(index+10)
                          self.clusScifi[index]=aCluster
                          index+=1
                          if c!=hitList[last]:
                               ncl+=1
                               tmp = [c]
                     cprev = c
   def Finalize(self):
      if self.options.FairTask_convRaw:
  # overwrite cbmsim 
          F = self.outfile.GetRootFile()
          T = F.Get("cbmsim")
          T.SetName('rawConv')
          T.Write()
          self.fiN.Close()
          self.outfile.Close()
      else:
  # fill TTree
         self.sTree.Fill()
         if self.options.debug:
             print('number of events processed',self.sTree.GetEntries(),self.fiN.event.GetEntries())
         self.sTree.Write()
         self.fiN.Close()
         self.fSink.Close()
      print("File closed ",self.fiN.GetName())
