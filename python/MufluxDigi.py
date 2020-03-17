from __future__ import print_function
from __future__ import division
from builtins import range
import os
import ROOT
import global_variables
import shipunit as u
from array import array

stop  = ROOT.TVector3()
start = ROOT.TVector3()

deadChannelsForMC = [10112001, 20112003, 30002041, 30012026, 30102025, 30112013, 30112018, 40012014]
ineffiency = {1:0.1,2:0.1,3:0.1,4:0.1,5:0.1}

# defining constants for rpc properties
STRIP_XWIDTH = 0.8625  # internal STRIP V, WIDTH, in cm
EXT_STRIP_XWIDTH_L = 0.9625  # nominal (R&L) and Left measured external STRIP V, WIDTH, in cm (beam along z, out from the V plane)
EXT_STRIP_XWIDTH_R = 0.86  # measured Right external STRIP V, WIDTH,in cm (beam along z, out from the V plane)
V_STRIP_OFF = 0.200
NR_VER_STRIPS = 184
total_width = (NR_VER_STRIPS - 2) * STRIP_XWIDTH + EXT_STRIP_XWIDTH_L + EXT_STRIP_XWIDTH_R + (NR_VER_STRIPS - 1) * V_STRIP_OFF
reduced_width = total_width - (EXT_STRIP_XWIDTH_L + EXT_STRIP_XWIDTH_R)

# function for calculating the strip number from a coordinate, for MuonTagger / RPC
def StripX(x):
    if x < -total_width/2. or x > total_width/2.:
        print("WARNING: x coordinate outside sensitive volume!",x)
    if x <  -total_width/2.  + EXT_STRIP_XWIDTH_L + V_STRIP_OFF/2. : strip_x = 184
    elif x >  total_width/2. - EXT_STRIP_XWIDTH_R - V_STRIP_OFF/2. : strip_x = 1
    else:
      x_start = x - total_width/2. + EXT_STRIP_XWIDTH_R
      strip_x = -int(x_start/reduced_width*182.)+1
      if not (0 < strip_x <= NR_VER_STRIPS-1):
        print("WARNING: X strip outside range!",x,strip_x)
        strip_x = 0
    return int(strip_x)

def StripY(y):
    STRIP_YWIDTH = 0.8625  # internal STRIP H, WIDTH, in cm
    EXT_STRIP_YWIDTH = 0.3  # measured external STRIP H, WIDTH, in cm
    H_STRIP_OFF = 0.1983
    NR_HORI_STRIPS = 116
    total_height = (NR_HORI_STRIPS - 2) * STRIP_YWIDTH + 2 * EXT_STRIP_YWIDTH + (NR_HORI_STRIPS - 1) * H_STRIP_OFF
    y_start = total_height / 2.
    strip_y = (y_start - EXT_STRIP_YWIDTH + 1.5 * STRIP_YWIDTH + H_STRIP_OFF - y)//(STRIP_YWIDTH + H_STRIP_OFF)
    if not (0 < strip_y <= NR_HORI_STRIPS):
        print("WARNING: Y strip outside range!")
        strip_y = 0
    return int(strip_y)

class MufluxDigi:
    " convert FairSHiP MC hits / digitized hits to measurements"
    def __init__(self,fout):

        self.iEvent = 0

        outdir=os.getcwd()
        outfile=outdir+"/"+fout
        self.fn = ROOT.TFile(fout,'update')
        self.sTree = self.fn.cbmsim

        # event header
        self.header  = ROOT.FairEventHeader()
        self.eventHeader  = self.sTree.Branch("ShipEventHeader",self.header,32000,1)
        self.digiMufluxSpectrometer    = ROOT.TClonesArray("MufluxSpectrometerHit")
        self.digiMufluxSpectrometerBranch   = self.sTree.Branch("Digi_MufluxSpectrometerHits",self.digiMufluxSpectrometer,32000,1)
        self.digiLateMufluxSpectrometer    = ROOT.TClonesArray("MufluxSpectrometerHit")
        self.digiLateMufluxSpectrometerBranch   = self.sTree.Branch("Digi_LateMufluxSpectrometerHits",self.digiMufluxSpectrometer,32000,1)
        #muon taggger
        if self.sTree.GetBranch("MuonTaggerPoint"):
            self.digiMuonTagger = ROOT.TClonesArray("MuonTaggerHit")
            self.digiMuonTaggerBranch = self.sTree.Branch("Digi_MuonTaggerHits", self.digiMuonTagger, 32000, 1)
        # setup random number generator
        ROOT.gRandom.SetSeed()
        self.PDG = ROOT.TDatabasePDG.Instance()
        # for the digitizing and reconstruction step
        self.v_drift       = global_variables.ShipGeo['MufluxSpectrometer']['v_drift']
        self.sigma_spatial = global_variables.ShipGeo['MufluxSpectrometer']['sigma_spatial']
        self.viewangle     = global_variables.ShipGeo['MufluxSpectrometer']['ViewvAngle']

        self.gMan  = ROOT.gGeoManager

    def digitize(self):

        self.sTree.t0 = ROOT.gRandom.Rndm()*1*u.microsecond
        self.header.SetEventTime( self.sTree.t0 )
        self.header.SetRunId( self.sTree.MCEventHeader.GetRunID() )
        self.header.SetMCEntryNumber( self.sTree.MCEventHeader.GetEventID() )  # counts from 1
        self.eventHeader.Fill()
        self.digiMufluxSpectrometer.Delete()
        self.digiLateMufluxSpectrometer.Delete()
        self.digitizeMufluxSpectrometer()
        self.digiMufluxSpectrometerBranch.Fill()
        self.digiLateMufluxSpectrometerBranch.Fill()
        self.digiMuonTagger.Delete() # produces a lot of warnings, rpc station 0
        self.digitizeMuonTagger()
        self.digiMuonTaggerBranch.Fill()

    def digitizeMuonTagger(self, fake_clustering=False):

        station = 0
        strip = 0
        nav = ROOT.gGeoManager.GetCurrentNavigator()
        DetectorID = set()  # set of detector ids - already deduplicated
        for MuonTaggerHit in self.sTree.MuonTaggerPoint:
            # getting rpc nodes, name and matrix
            detID = MuonTaggerHit.GetDetectorID()
            s = str(detID//10000)
            nav.cd('/VMuonBox_1/VSensitive'+s+'_'+s)
            # translation from top to MuonBox_1
            point = array('d', [
                MuonTaggerHit.GetX(),
                MuonTaggerHit.GetY(),
                MuonTaggerHit.GetZ(), 1])
            # translation to local frame
            point_local = array('d', [0, 0, 0, 1])
            nav.MasterToLocal(point, point_local)

            xcoord = point_local[0]
            ycoord = point_local[1]

            # identify individual rpcs
            station = detID//10000
            if station not in range(1, 6):  # limiting the range of rpcs
                print("WARNING: Invalid RPC number, something's wrong with the geometry ",station)

            # calculate strip
            # x gives vertical direction
            direction = 1
            strip = StripX(xcoord)
            if not strip:
                continue
            # sampling number of strips around the exact strip for emulating clustering
            detectorid = station*10000 + direction*1000 + strip
            DetectorID.add(detectorid)
            if fake_clustering:
                s = ROOT.gRandom.Poisson(2)
                if ROOT.gRandom.Rndm() < 0.5:  strip = strip - int(s/2)
                else:                          strip = strip + int(s/2)
                for i in range(0, s):
                        detectorid = station*10000 + direction*1000 + strip + i
                        DetectorID.add(detectorid)

            # y gives horizontal direction
            direction = 0
            strip = StripY(ycoord)
            if not strip:
                continue
            # sampling number of strips around the exact strip for emulating clustering
            detectorid = station*10000 + direction*1000 + strip
            DetectorID.add(detectorid)
            if fake_clustering:
                s = ROOT.gRandom.Poisson(2)
                if ROOT.gRandom.Rndm() < 0.5:  strip = strip - int(s/2)
                else:                          strip = strip + int(s/2)
                for i in range(0, s):
                        detectorid = station*10000 + direction*1000 + strip + i
                        DetectorID.add(detectorid)

        self.digiMuonTagger.Expand(len(DetectorID))
        for index, detID in enumerate(DetectorID):
            hit = ROOT.MuonTaggerHit(detID, 0)
            self.digiMuonTagger[index] = hit

        if fake_clustering:
            # cluster size loop - plotting the cluster size distribution
            cluster_size = list()
            DetectorID_list = list(DetectorID)  # turn set into list to allow indexing
            DetectorID_list.sort()  # sorting the list
            if len(DetectorID_list) > 1:
                clusters = [[DetectorID_list[0]]]
                for x in DetectorID_list[1:]:
                    if abs(x - clusters[-1][-1]) <= 1:
                        clusters[-1].append(x)
                    else:
                        clusters.append([x])
                    cluster_size = [len(x) for x in clusters]

    def digitizeMufluxSpectrometer(self):

        # digitize FairSHiP MC hits
        index = 0
        hitsPerDetId = {}

        for aMCPoint in self.sTree.MufluxSpectrometerPoint:
            aHit = ROOT.MufluxSpectrometerHit(aMCPoint,self.sTree.t0)
            aHit.setValid()
            if index>0 and self.digiMufluxSpectrometer.GetSize() == index: self.digiMufluxSpectrometer.Expand(index+1000)
            self.digiMufluxSpectrometer[index]=aHit
            detID = aHit.GetDetectorID()
            if detID in hitsPerDetId:
                if self.digiMufluxSpectrometer[hitsPerDetId[detID]].tdc() > aHit.tdc():
                    # second hit with smaller tdc
                    self.digiMufluxSpectrometer[hitsPerDetId[detID]].setInvalid()
                    hitsPerDetId[detID] = index
            else:
                hitsPerDetId[detID] = index
            if aMCPoint.GetDetectorID() in deadChannelsForMC: aHit.setInvalid()
            station = int(aMCPoint.GetDetectorID()//10000000)
            if ROOT.gRandom.Rndm() < ineffiency[station]: aHit.setInvalid()
            index+=1

    def finish(self):
        print('finished writing tree')
        self.sTree.Write()
