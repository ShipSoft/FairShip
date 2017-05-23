__author__ = ''


#!/usr/bin/env python
#module with functions for digitization & pattern recognition
#configuration, histograms etc done in shipPatRec_config
#for documentation, see CERN-SHiP-NOTE-2015-002, https://cds.cern.ch/record/2005715/files/main.pdf
#17-04-2015 comments to EvH
import ROOT, os
import shipunit  as u
import math
import copy
from collections import OrderedDict
from ROOT import TVector3
from ROOT import gStyle
from ROOT import TGraph
from ROOT import TMultiGraph
from array import array
import operator, sys

import numpy
import rootUtils as ut

import geo_init

reconstructiblehorizontalidsfound12=0
reconstructiblestereoidsfound12=0
reconstructiblehorizontalidsfound34=0
reconstructiblestereoidsfound34=0
reconstructibleidsfound12=0
reconstructibleidsfound34=0
morethan500=0
morethan100tracks=0
falsenegative=0
falsepositive=0
reconstructibleevents=0

monitor = 0
printhelp = 0
reconstructiblerequired = 2
threeprong = 0
geoFile=''
fgeo = ''

totalaftermatching=0
totalafterpatrec=0
ReconstructibleMCTracks=[]
MatchedReconstructibleMCTracks=[]
fittedtrackids=[]
theTracks=[]

random = ROOT.TRandom()
ROOT.gRandom.SetSeed(13)

PDG=ROOT.TDatabasePDG.Instance()
fitter = ROOT.genfit.DAF()


particles=["e-","e+","mu-","mu+","pi-","pi+","other"]

i1=1 #1st layer
i2=16 #last layer
zlayer={} #dictionary with z coordinates of station1,2 layers
zlayerv2={} #z-positions for stereo views
z34layer={} #dictionary with z coordinates of station3,4 layers
z34layerv2={} #z-positions for stereo views
TStation1StartZ=0.
TStation4EndZ=0.
VetoStationZ=0.
VetoStationEndZ=0.

debug=0




def Digitization(sTree,SmearedHits):
    #digitization
    #input: Smeared TrackingHits
    #output: StrawRaw, StrawRawLink

    StrawRaw={} #raw hit dictionary: key=hit number, values=xtop,ytop,ztop,xbot,ybot,zbot,dist2Wire,strawname
    StrawRawLink={} #raw hit dictionary: key=hit number, value=the hit object
    j=0
    for i in range(len(SmearedHits)):
        xtop=SmearedHits[i]['xtop']
        xbot=SmearedHits[i]['xbot']
        ytop=SmearedHits[i]['ytop']
        ybot=SmearedHits[i]['ybot']
        ztop=SmearedHits[i]['z']
        zbot=SmearedHits[i]['z']
        distance=SmearedHits[i]['dist']
        strawname=sTree.strawtubesPoint[i].GetDetectorID()
        a=[]
        a.append(xtop)
        a.append(ytop)
        a.append(ztop)
        a.append(xbot)
        a.append(ybot)
        a.append(zbot)
        a.append(float(distance))
        a.append(str(strawname))
        StrawRaw[j]=a
        StrawRawLink[j]=[sTree.strawtubesPoint[i]]
        j=j+1

    if debug==1: print "Nbr of digitized hits",j
    return StrawRaw,StrawRawLink

def PatRec(firsttwo,zlayer,zlayerv2,StrawRaw,StrawRawLink, ShipGeo):
    global reconstructiblehorizontalidsfound12,reconstructiblestereoidsfound12,reconstructiblehorizontalidsfound34,reconstructiblestereoidsfound34
    global reconstructibleidsfound12,reconstructibleidsfound34,rawhits,totalaftermatching

    hits={}
    rawhits={}
    stereohits={}
    hitids={}
    ytan={}
    ycst={}
    horpx={}
    horpy={}
    horpz={}
    stereomom={}
    stereotan={}
    stereocst={}
    fraction={}
    trackid={}
    duplicates=[]
    j=0
    resolution=ShipGeo.strawtubes.sigma_spatial

    for item in StrawRaw:
        #y hits for horizontal straws
        rawhits[j]=copy.deepcopy(((StrawRaw[item][1]+StrawRaw[item][4])/2,(StrawRaw[item][2]+StrawRaw[item][5])/2,StrawRaw[item][6]))
        if firsttwo==True:
            if debug==1: print "rawhits[",j,"]=",rawhits[j],"trackid",StrawRawLink[item][0].GetTrackID(),"strawname",StrawRawLink[item][0].GetDetectorID(),"true x",StrawRawLink[item][0].GetX(),"true y",StrawRawLink[item][0].GetY(),"true z",StrawRawLink[item][0].GetZ()
        j=j+1

    sortedrawhits=OrderedDict(sorted(rawhits.items(),key=lambda t:t[1][1]))
    if debug==1:
        print " "
        print "horizontal view (y) hits ordered by plane: plane nr, zlayer, hits"

    y2=[]
    y3=[]
    yother=[]
    ymin2=[]
    z2=[]
    z3=[]
    zother=[]
    zmin2=[]
    for i in range(i1,i2+1):
        a=[] #the hits
        c=[] #the keys pointing to the raw hits
        d=[] #the distance to the wire
        for item in sortedrawhits:
            if (float(sortedrawhits[item][1])==float(zlayer[i][0])) :
                #difference with previous version: make each hit a dictionary so we can later get back the mc trackid
                if sortedrawhits[item][0] not in a:
                    a.append(float(sortedrawhits[item][0]))
                else:
                    #This should never happen - duplicate hits are already removed at digitization
                    if debug==1: print " wire hit again",sortedrawhits[item],"strawname=", StrawRawLink[item][0].GetDetectorID()
                    a.append(float(sortedrawhits[item][0]))
                    duplicates.append(float(zlayer[i][0]))
        a.sort()
        #find the key of the sorted hit
        for value in a:
            for item in sortedrawhits:
                if ((float(sortedrawhits[item][0])==value) & (float(sortedrawhits[item][1])==float(zlayer[i][0]))) :
                    if item not in c :
                        c.append(item)
                        d.append(float(sortedrawhits[item][2]))
                    else :
                        continue
                    break
        #indicate which hit has been used
        b=len(a)*[0]
        hits[i]=[a,b,c,d]
        if debug==1: print i,zlayer[i],hits[i]

        # split hits up by trackid for debugging

        for item in range(len(hits[i][0])):
            if StrawRawLink[hits[i][2][item]][0].GetTrackID() == 3:
                y3.append(float(hits[i][0][item]))
                z3.append(float(zlayer[i][0]))
            else:
                if StrawRawLink[hits[i][2][item]][0].GetTrackID() == 2:
                    y2.append(float(hits[i][0][item]))
                    z2.append(float(zlayer[i][0]))
                else:
                    if StrawRawLink[hits[i][2][item]][0].GetTrackID() == -2:
                        ymin2.append(float(hits[i][0][item]))
                        zmin2.append(float(zlayer[i][0]))
                    else:
                        yother.append(float(hits[i][0][item]))
                        zother.append(float(zlayer[i][0]))

    if threeprong==1 : nrtrcandv1,trcandv1=ptrack(zlayer,hits,6,0.6)
    else: nrtrcandv1,trcandv1=ptrack(zlayer,hits,7,0.7)

    foundhorizontaltrackids=[]
    horizontaltrackids=[]
    removetrackids=[]
    for t in trcandv1:
        trackids=[]
        if debug==1:
            print ' '
            print 'track found in Y view:',t,' indices of hits in planes',trcandv1[t]
        for ipl in range(len(trcandv1[t])):
            indx= trcandv1[t][ipl]
            if indx>-1:
                if debug==1: print '   plane nr, z-position, y of hit, trackid:',ipl,zlayer[ipl],hits[ipl][0][indx],StrawRawLink[hits[ipl][2][indx]][0].GetTrackID()
                trackids.append(StrawRawLink[hits[ipl][2][indx]][0].GetTrackID())
        if debug==1: print "   Largest fraction of hits in Y view:",fracMCsame(trackids)[0],"on MC track with id",fracMCsame(trackids)[1]

    for i in range(0,len(removetrackids)):
        del trcandv1[removetrackids[i]]
        nrtrcandv1=nrtrcandv1-1

    #reorder trcandv1 after removing tracks
    if len(removetrackids)>0:
        j=0
        for key in trcandv1:
            j=j+1
            if key!=j:
                trcandv1[j]=trcandv1[key]
                del trcandv1[key]


    if firsttwo==True: reconstructiblehorizontalidsfound12+=1
    else: reconstructiblehorizontalidsfound34+=1


    if debug==1: print "***************** Start of Stereo PatRec **************************"

    v2hits={}
    v2hitsMC={}

    uvview={}
    j=0
    rawxhits={}
    for item in StrawRaw:
        rawxhits[j]=copy.deepcopy((StrawRaw[item][0],StrawRaw[item][1],StrawRaw[item][3],StrawRaw[item][4],StrawRaw[item][2],StrawRaw[item][6]))
        if firsttwo==True:
            if debug==1: print "rawxhits[",j,"]=",rawxhits[j],"trackid",StrawRawLink[item][0].GetTrackID(),"true x",StrawRawLink[item][0].GetX(),"true y",StrawRawLink[item][0].GetY()
        j=j+1

    sortedrawxhits=OrderedDict(sorted(rawxhits.items(),key=lambda t:t[1][4]))

    if debug==1: print "stereo view hits ordered by plane:"
    for i in range(i1,i2+1):
        xb=[]
        yb=[]
        xt=[]
        yt=[]
        c=[]
        d=[]
        for item in sortedrawxhits:
            if (float(sortedrawxhits[item][4])==float(zlayerv2[i][0])) :
                xt.append(float(sortedrawxhits[item][0]))
                yt.append(float(sortedrawxhits[item][1]))
                xb.append(float(sortedrawxhits[item][2]))
                yb.append(float(sortedrawxhits[item][3]))
                #c is the rawxhits hit number
                c.append(item)
                #d is the distance to the wire
                d.append(float(sortedrawxhits[item][5]))
        uvview[i]=[xb,yb,xt,yt,c,d]

        if debug==1: print '   uv hits, z,xb,yb,xt,yt,dist    ',i,zlayerv2[i],uvview[i][0],uvview[i][1],uvview[i][2],uvview[i][3],uvview[i][4],uvview[i][5]

    # now do pattern recognition in view perpendicular to first search view
    # loop over tracks found in Y view, and intersect this "plane"
    # with hits in other views, and project in "x", then ptrack in "x", etc..

    #loop over tracks found in Y view
    ntracks=0
    trackkey=0
    tracks={}
    if debug==1:
        if (firsttwo==True) :
            print 'Loop over tracks found in Y view, stations 1&2'
        else :
            print 'Loop over tracks found in Y view, stations 3&4'

    foundstereotrackids=[]
    foundtrackids=[]

    for t in trcandv1:
        alltrackids=[]
        y11trackids=[]
        y12trackids=[]
        y21trackids=[]
        y22trackids=[]
        y11hitids=[]
        y12hitids=[]
        y21hitids=[]
        y22hitids=[]
        trackkey+=1

        #linear "fit" to track found in this view

        fitt,fitc=fitline(trcandv1[t],hits,zlayer,resolution)
        if debug==1: print '   Track nr',t,'in Y view: tangent, constant=',fitt,fitc

        tan=0.
        cst=0.
        px=0.
        py=0.
        pz=0.
        m=0
        if firsttwo==True: looplist=reversed(range(len(trcandv1[t])))
        else: looplist=range(len(trcandv1[t]))
        for ipl in looplist:
            indx= trcandv1[t][ipl]
            if indx>-1:
                if debug==1: print '      Plane nr, z-position, y of hit:',ipl,zlayer[ipl],hits[ipl][0][indx]
                hitpoint=[zlayer[ipl],hits[ipl][0][indx]]
                #if px==0. : px=StrawRawLink[hits[ipl][2][indx]][0].GetPx()
                #if py==0. : py=StrawRawLink[hits[ipl][2][indx]][0].GetPy()
                #if pz==0. : pz=StrawRawLink[hits[ipl][2][indx]][0].GetPz()
                px=StrawRawLink[hits[ipl][2][indx]][0].GetPx()
                py=StrawRawLink[hits[ipl][2][indx]][0].GetPy()
                pz=StrawRawLink[hits[ipl][2][indx]][0].GetPz()
                ptmp=math.sqrt(px**2+py**2+pz**2)
                if debug==1:
                    print "      p",ptmp,"px",px,"py",py,"pz",pz
                if tan==0. : tan=py/pz
                if cst==0. : cst=StrawRawLink[hits[ipl][2][indx]][0].GetY()-tan*zlayer[ipl][0]

        if debug==1: print '   Track nr',t,'in Y view: MC tangent, MC constant=',tan,cst

        for ipl in range(len(trcandv1[t])):
            indx= trcandv1[t][ipl]
            if indx>-1:
                diffy=hits[ipl][0][indx]-StrawRawLink[hits[ipl][2][indx]][0].GetY()
                if ipl<5:
                    y11trackids.append(StrawRawLink[hits[ipl][2][indx]][0].GetTrackID())
                    y11hitids.append([hits[ipl][2][indx]][0])
                if (ipl>4 and ipl<9):
                    y12trackids.append(StrawRawLink[hits[ipl][2][indx]][0].GetTrackID())
                    y12hitids.append([hits[ipl][2][indx]][0])
                if (ipl>9 and ipl<13):
                    y21trackids.append(StrawRawLink[hits[ipl][2][indx]][0].GetTrackID())
                    y21hitids.append([hits[ipl][2][indx]][0])
                if ipl>12:
                    y22trackids.append(StrawRawLink[hits[ipl][2][indx]][0].GetTrackID())
                    y22hitids.append([hits[ipl][2][indx]][0])
            else:
                if ipl<5:
                    y11trackids.append(999)
                    y11hitids.append(999)
                if (ipl>4 and ipl<9):
                    y12trackids.append(999)
                    y12hitids.append(999)
                if (ipl>9 and ipl<13):
                    y21trackids.append(999)
                    y21hitids.append(999)
                if ipl>12:
                    y22trackids.append(999)
                    y22hitids.append(999)

        #intersect this "plane", with all hits in all other views...

        v2y2=[]
        v2y3=[]
        v2yother=[]
        v2ymin2=[]
        v2z2=[]
        v2z3=[]
        v2zother=[]
        v2zmin2=[]
        for ipl in range(1,len(zlayerv2)+1):
            items=[]
            xclean=[]
            distances=[]

            xclean,items=line2plane(fitt,fitc,uvview[ipl],zlayerv2[ipl][0])


            distances=copy.deepcopy(uvview[ipl][5])
            xcleanunsorted=[]
            xcleanunsorted=list(xclean)

            xclean.sort()
            b=len(xclean)*[0]
            d=[]
            e=[]
            for item in xclean:
                d.append(items[xcleanunsorted.index(item)])
                e.append(distances[xcleanunsorted.index(item)])
            #fill hits info for ptrack, "b" records if hit has been used in ptrack
            v2hits[ipl]=[xclean,b,d,e]
            if debug==1: print '      Plane,z, projected hits:',ipl,zlayerv2[ipl],v2hits[ipl]

            for item in range(len(v2hits[ipl][0])):
                if StrawRawLink[v2hits[ipl][2][item]][0].GetTrackID() == 3:
                    v2y3.append(float(v2hits[ipl][0][item]))
                    v2z3.append(float(zlayerv2[ipl][0]))
                else:
                    if StrawRawLink[v2hits[ipl][2][item]][0].GetTrackID() == 2:
                        v2y2.append(float(v2hits[ipl][0][item]))
                        v2z2.append(float(zlayerv2[ipl][0]))
                    else:
                        if StrawRawLink[v2hits[ipl][2][item]][0].GetTrackID() == -2:
                            v2ymin2.append(float(v2hits[ipl][0][item]))
                            v2zmin2.append(float(zlayerv2[ipl][0]))
                        else:
                            v2yother.append(float(v2hits[ipl][0][item]))
                            v2zother.append(float(zlayerv2[ipl][0]))

        #pattern recognition for this track, blow up y-window, maybe make dependend of stereo angle,
        #constant now, should be 5*error/sin(alpha) :-), i.e. variable/plane if different "alphas"
        #Hence, for "real" y-view, should be small.
        nrtrcandv2,trcandv2=ptrack(zlayerv2,v2hits,6,15.)
        if len(trcandv2)>1:
            if debug==1: print "   len(trcandv2) in stereo",len(trcandv2)

        nstereotracks=0
        if nrtrcandv2==0 :
            if debug==1: print "   0 tracks found in stereo view, for Y-view track nr",t


        #if firsttwo==True: totalstereo12=reconstructiblestereoidsfound12
        #else: totalstereo34==reconstructiblestereoidsfound34

        for t1 in trcandv2:
            if debug==1: print '   Track belonging to Y-view view track',t,'found in stereo view:',t1,trcandv2[t1]

            stereofitt,stereofitc=fitline(trcandv2[t1],v2hits,zlayerv2,resolution)

            pxMC=0.
            pzMC=0.
            stereotanMCv=0.
            stereocstMCv=0.
            if firsttwo==True: looplist=reversed(range(len(trcandv2[t1])))
            else: looplist=range(len(trcandv2[t1]))
            for ipl in looplist:
                indx= trcandv2[t1][ipl]
                if indx>-1:
                    hitpointx=[zlayerv2[ipl],v2hits[ipl][0][indx]]
                    if pxMC==0. :  pxMC=StrawRawLink[v2hits[ipl][2][indx]][0].GetPx()
                    if pzMC ==0. : pzMC=StrawRawLink[v2hits[ipl][2][indx]][0].GetPz()
                    if stereotanMCv==0. : stereotanMCv=pxMC/pzMC
                    if stereocstMCv==0. : stereocstMCv=StrawRawLink[v2hits[ipl][2][indx]][0].GetX()-stereotanMCv*zlayerv2[ipl][0]


            stereotrackids=[]

            stereo11trackids=[]
            stereo12trackids=[]
            stereo21trackids=[]
            stereo22trackids=[]
            stereo11hitids=[]
            stereo12hitids=[]
            stereo21hitids=[]
            stereo22hitids=[]
            nstereotracks+=1


            for ipl in range(len(trcandv2[t1])):
                indx= trcandv2[t1][ipl]
                if indx>-1:
                    stereotrackids.append(StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID())
                    if debug==1: print "      plane nr, zpos, x of hit, hitid, trackid",ipl,zlayerv2[ipl],v2hits[ipl][0][indx],v2hits[ipl][2][indx],StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID()
                    xdiff=v2hits[ipl][0][indx]-StrawRawLink[v2hits[ipl][2][indx]][0].GetX()
                if ipl<5:
                    if indx>-1:
                        stereo11trackids.append(StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID())
                        stereo11hitids.append(v2hits[ipl][2][indx])
                    else:
                        stereo11trackids.append(999)
                        stereo11hitids.append(999)
                if (ipl>4 and ipl<9):
                    if indx>-1:
                        stereo12trackids.append(StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID())
                        stereo12hitids.append(v2hits[ipl][2][indx])
                    else:
                        stereo12trackids.append(999)
                        stereo12hitids.append(999)
                if (ipl>9 and ipl<13):
                    if indx>-1:
                        stereo21trackids.append(StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID())
                        stereo21hitids.append(v2hits[ipl][2][indx])
                    else:
                        stereo21trackids.append(999)
                        stereo21hitids.append(999)
                if ipl>12:
                    if indx>-1:
                        stereo22trackids.append(StrawRawLink[v2hits[ipl][2][indx]][0].GetTrackID())
                        stereo22hitids.append(v2hits[ipl][2][indx])
                    else:
                        stereo22trackids.append(999)
                        stereo22hitids.append(999)


            if debug==1:
                print "      Largest fraction of hits in stereo view:",fracMCsame(stereotrackids)[0],"on MC track with id",fracMCsame(stereotrackids)[1]
                #check if this trackid is the same as the track from the Y-view it belongs to

            if fracMCsame(stereotrackids)[1] not in foundstereotrackids:
                foundstereotrackids.append(fracMCsame(stereotrackids)[1])

            ntracks=ntracks+1
            alltrackids=y11trackids+stereo11trackids+stereo12trackids+y12trackids+y21trackids+stereo21trackids+stereo22trackids+y22trackids
            if debug==1: print "      Largest fraction of hits in horizontal and stereo view:",fracMCsame(alltrackids)[0],"on MC track with id",fracMCsame(alltrackids)[1]

            #calculate efficiency after joining horizontal and stereo tracks
            if fracMCsame(alltrackids)[1] not in foundtrackids:
                foundtrackids.append(fracMCsame(alltrackids)[1])

                tracks[trackkey*1000+nstereotracks]=alltrackids
                hitids[trackkey*1000+nstereotracks]=y11hitids+stereo11hitids+stereo12hitids+y12hitids+y21hitids+stereo21hitids+stereo22hitids+y22hitids

                ytan[trackkey*1000+nstereotracks]=fitt
                ycst[trackkey*1000+nstereotracks]=fitc


                fraction[trackkey*1000+nstereotracks]=fracMCsame(alltrackids)[0]
                trackid[trackkey*1000+nstereotracks]=fracMCsame(alltrackids)[1]


                horpx[trackkey*1000+nstereotracks]=px
                horpy[trackkey*1000+nstereotracks]=py
                horpz[trackkey*1000+nstereotracks]=pz

                stereotan[trackkey*1000+nstereotracks]=stereofitt
                stereocst[trackkey*1000+nstereotracks]=stereofitc

    if firsttwo==True: reconstructiblestereoidsfound12+=1
    else: reconstructiblestereoidsfound34+=1
    if firsttwo==True: reconstructibleidsfound12+=1
    else: reconstructibleidsfound34+=1

    #now Kalman fit, collect "all hits" around fitted track, outlier removal etc..
    return ntracks,tracks,hitids,ytan,ycst,stereotan,stereocst,horpx,horpy,horpz,fraction,trackid

def TrackFit(hitPosList,theTrack,charge,pinv, ShipGeo, theTracks):

    if debug==1: fitter.setDebugLvl(1)
    resolution = ShipGeo.strawtubes.sigma_spatial
    hitCov = ROOT.TMatrixDSym(7)
    hitCov[6][6] = resolution*resolution
    for item in hitPosList:
        itemarray=array('d',[item[0],item[1],item[2],item[3],item[4],item[5],item[6]])
        ms=ROOT.TVectorD(7,itemarray)
        tp = ROOT.genfit.TrackPoint(theTrack) # note how the point is told which track it belongs to
        measurement = ROOT.genfit.WireMeasurement(ms,hitCov,1,6,tp) # the measurement is told which trackpoint it belongs to
        measurement.setMaxDistance(0.5*u.cm)
        tp.addRawMeasurement(measurement) # package measurement in the TrackPoint
        theTrack.insertPoint(tp)  # add point to Track
    theTracks.append(theTrack)
    if not debug == 1: return # leave track fitting shipDigiReco
    #check
    if not theTrack.checkConsistency():
        if debug==1: print 'Problem with track before fit, not consistent',theTrack
        return
    # do the fit
    try:  fitter.processTrack(theTrack)
    except:
        if debug==1: print "genfit failed to fit track"
        return
    #check
    if not theTrack.checkConsistency():
        if debug==1: print 'Problem with track after fit, not consistent',theTrack
        return


    fitStatus   = theTrack.getFitStatus()
    theTrack.prune("CFL")  #  http://sourceforge.net/p/genfit/code/HEAD/tree/trunk/core/include/Track.h#l280

    nmeas = fitStatus.getNdf()
    pval = fitStatus.getPVal()

    #pval close to 0 indicates a bad fit
    chi2        = fitStatus.getChi2()/nmeas



    fittedState = theTrack.getFittedState()
    fittedMom = fittedState.getMomMag()
    fittedMom = fittedMom*int(charge)


    fittedtrackDir = fittedState.getDir()
    fittedx=math.degrees(math.acos(fittedtrackDir[0]))
    fittedy=math.degrees(math.acos(fittedtrackDir[1]))
    fittedz=math.degrees(math.acos(fittedtrackDir[2]))
    fittedmass = fittedState.getMass()

    return

def ptrack(zlayer,ptrackhits,nrwant,window):

    # basic pattern recognition in one view
    # zlayer= dictionary with z-position of planes: zlayer[iplane][0]==z-position (list of length 1 :-).
    # ptrackhits is dictionary with hits in a projection:  ptrackhits[plane number][0]=list-of-hits
    # ndrop= nr of hits that can be missing in this projection
    # nrwant= min nr of hits on a track in this projection
    # window: is the size of the search window

    # get first and last plane number (needs to be consecutive, and also contains empty planes
    # should be included in the list!
    planes=zlayer.keys()
    planes.sort()
    i_1=planes[0]
    i_2=planes[len(planes)-1]
    ndrop=len(planes)-nrwant
    #print 'ptrack input: planes=',i_1,i_2,ndrop,window,"   ptrackhits ",ptrackhits

    nrtracks=0
    tracks={}

    #loop over maxnr hits, to max-ndrop
    for nhitw in range(i_2-i_1+1,i_2-i_1-ndrop,-1):
        # nhitw: wanted number of hits when looking for a track
        for idrop in range(ndrop):
            #only start if wanted nr hits <= the nr of planes
            nrhitmax=i_2-i_1-idrop+1
            if nhitw<=nrhitmax:
                for k in range(idrop+1):
                    #calculate the id of the first and last plane for this try.
                    ifirst=i_1+k
                    ilast=i_2-(idrop-k)
                    #now loop over hits in first/last planes, and construct line
                    dz=zlayer[ilast][0]-zlayer[ifirst][0]
                    #hits in first plane
                    for ifr in range(len(ptrackhits[ifirst][0])):
                        #for ifr in range(len(ptrackhits[ifirst][0])):
                        #has this hit been used already for a track: skip
                        if  ptrackhits[ifirst][1][ifr]==0:
                            xfirst= ptrackhits[ifirst][0][ifr]
                            #hits in last plane
                            for il in range(len(ptrackhits[ilast][0])):
                                #has this hit been used already for a track: skip
                                if  ptrackhits[ilast][1][il]==0:
                                    xlast= ptrackhits[ilast][0][il]
                                    nrhitsfound=2
                                    tancand=(xlast-xfirst)/dz
                                    #fill temporary hit list for track-candidate with -1
                                    trcand=(i_2-i_1+2)*[-1]
                                    #loop over in between planes
                                    for inbetween in range(ifirst+1,ilast):
                                        #can wanted number of hits be satisfied?
                                        if nrhitsfound+ilast-inbetween>=nhitw:
                                            #calculate candidate hit
                                            xwinlow=xfirst+tancand*(zlayer[inbetween][0]-zlayer[ifirst][0])-window
                                            for im in range(len(ptrackhits[inbetween][0])):
                                                #has this hit been used?
                                                if  ptrackhits[inbetween][1][im]==0:
                                                    xin= ptrackhits[inbetween][0][im]
                                                    #hit belwo window, try next one
                                                    if xin>xwinlow:
                                                        #if hit larger than upper edge of window: goto next plane
                                                        if xin>xwinlow+2*window:
                                                            break
                                                        #hit found, do administation
                                                        if trcand[inbetween]==-1:
                                                            nrhitsfound+=1
                                                        trcand[inbetween]=im
                                    #looped over in between planes, collected enough hits?
                                    if nrhitsfound==nhitw:
                                        #mark used hits
                                        trcand[ifirst]=ifr
                                        trcand[ilast]=il
                                        for i in range(ifirst,ilast+1):
                                            if trcand[i]>=0:
                                                ptrackhits[i][1][trcand[i]]=1
                                        #store the track
                                        nrtracks+=1
                                        #print "ptrack nrtracks",nrtracks
                                        tracks[nrtracks]=trcand
    #print "ptrack: tracks",tracks
    return nrtracks,tracks

def dorot(x,y,xc,yc,alpha):
    #rotate x,y around xc,yc over angle alpha
    ca=numpy.cos(alpha)
    sa=numpy.sin(alpha)
    xout=ca*(x-xc)-sa*(y-yc)+xc
    yout=sa*(x-xc)+ca*(y-yc)+yc
    return xout,yout

def line2plane(fitt,fitc,uvview,zuv):
    #intersect horizontal plane, defined by tangent, constant in yz plane, with
    #stereo hits given in uvview,zuv with top/bottom hits of "straw"
    xb=uvview[0]
    yb=uvview[1]
    xt=uvview[2]
    yt=uvview[3]
    x=[]
    items=[]
    term=fitc+zuv*fitt
    #loop over all hits in this view
    for i in range(len(yb)):
        #f2=(term-yb[i])/(yt[i]-yb[i])
        #xint=xb[i]+f2*(xt[i]-xb[i])
        f2=(term-yb[i])/(yb[i]-yt[i])
        xint=xb[i]+f2*(xb[i]-xt[i])
        c=uvview[4][i]
        #do they cross inside sensitive volume defined by top/bottom of straw?
        if xint<max(xt[i],xb[i]) and xint>min(xb[i],xt[i]):
            x.append(xint)
            items.append(c)
    return x,items

def fitline(indices,xhits,zhits,resolution):
    #fit linear function (y=fitt*x+fitc) to list of hits,
    #"x" is the z-coordinate, "y" is the cSoordinate in tracking plane perp to z
    #use equal weights for the time being, and outlier removal (yet)?

    n=0
    sumx=0.
    sumx2=0
    sumxy=0.
    sumy=0.
    sumweight=0.
    sumweightx=0.
    sumweighty=0.
    Dw=0.
    term=0.
    for ipl in range(1,len(indices)):
        indx= indices[ipl]
        if indx>-1:
            #n+=1
            #weigh points accordint to their distance to the wire
            weight=1/math.sqrt(xhits[ipl][3][indx]**2+resolution**2)
            x=zhits[ipl][0]
            y=xhits[ipl][0][indx]
            sumweight+=weight
            sumweightx+=weight*x
            sumweighty+=weight*y
    xmean=sumweightx/sumweight
    ymean=sumweighty/sumweight
    for ipl in range(1,len(indices)):
        indx= indices[ipl]
        if indx>-1:
            n+=1
            weight=1/math.sqrt(xhits[ipl][3][indx]**2+resolution**2)
            x=zhits[ipl][0]
            y=xhits[ipl][0][indx]
            Dw+=weight*(x-xmean)**2
            term+=weight*(x-xmean)*y
            sumx+=zhits[ipl][0]
            sumx2+=zhits[ipl][0]**2
            sumxy+=xhits[ipl][0][indx]*zhits[ipl][0]
            sumy+=xhits[ipl][0][indx]
    fitt=(1/Dw)*term
    fitc=ymean-fitt*xmean
    unweightedfitt=(sumxy-sumx*sumy/n)/(sumx2-sumx**2/n)
    unweightedfitc=(sumy-fitt*sumx)/n
    return fitt,fitc

def IP(s, t, b):
    #some vector manipulations to get impact point of t-b to s
    dir=ROOT.TVector3(t-b)
    udir = ROOT.TVector3(dir.Unit())
    sep = ROOT.TVector3(t-s)
    ip = ROOT.TVector3(udir.Cross(sep.Cross(udir) ))
    return ip.Mag()

def fracMCsame(trackids):
    # determine largest fraction of hits which have benn generated by the same # MC true track
    #hits: list of pointers to true MC TrackingHits
    #return: fraction of hits from same track, and its track-ID
    track={}
    nh=len(trackids)
    for tid in trackids:
        if tid==999:
            nh-=1
            continue
        if track.has_key(tid):
            track[tid]+=1
        else:
            track[tid]=1
    #now get track with largest number of hits
    tmax=max(track, key=track.get)

    frac=0.
    if nh>0: frac=float(track[tmax])/float(nh)
    return frac,tmax

def match_tracks(t1,t2,zmagnet,Bdl):
    # match tracks before to after magnet
    # t1,t2: x,y,z,tgx,tgy of two input tracks
    # zmagnet: middle of the magnet
    # BdL: Bdl in Tm
    # returns:
    #     dx,dy: distance between tracks at zmagnet
    #     1./pmom:  innverse momentum*q estimated

    #linear extrapoaltion to centre of the magnet
    dz1=zmagnet-t1[2]
    x1m=t1[0]+dz1*t1[3]
    y1m=t1[1]+dz1*t1[4]
    dz2=zmagnet-t2[2]
    x2m=t2[0]+dz2*t2[3]
    y2m=t2[1]+dz2*t2[4]
    dx=x1m-x2m
    dy=y1m-y2m

    alpha=math.atan(t1[4])-math.atan(t2[4])
    pinv=math.sin(alpha)/(Bdl*0.3)
    return dx,dy,alpha,pinv

def dist2line(tan,cst,points):
    #points = (x,y)
    #tan, cst are the tangens & constant of the fitted track
    dist = tan*points[0][0] + cst - points[1]
    return dist

def hit2wire(ahit,bot,top, ShipGeo, no_amb=None):
    detID = ahit.GetDetectorID()
    ex = ahit.GetX()
    ey = ahit.GetY()
    ez = ahit.GetZ()
    #distance to wire, and smear it.
    dw  = ahit.dist2Wire()
    smear = dw
    if not no_amb: smear = ROOT.fabs(random.Gaus(dw,ShipGeo.strawtubes.sigma_spatial))
    smearedHit = {'mcHit':ahit,'xtop':top.x(),'ytop':top.y(),'z':top.z(),'xbot':bot.x(),'ybot':bot.y(),'z':bot.z(),'dist':smear}
    return smearedHit

def execute(SmearedHits, sTree, ShipGeo):

    global totalaftermatching,morethan500,falsepositive,falsenegative,totalafterpatrec
    global reconstructibleevents,morethan100tracks,theTracks

    ############################################## SHiP geometry init ##################################################

    zlayer, \
    zlayerv2, \
    z34layer, \
    z34layerv2, \
    TStation1StartZ, \
    TStation4EndZ, \
    VetoStationZ, \
    VetoStationEndZ = geo_init.initialize(ShipGeo)

    ####################################################################################################################

    fittedtrackids=[]
    reconstructibles12=0
    reconstructibles34=0
    theTracks=[]

    reco_tracks = {}
    track_id = 0

    if debug==1: print "************* PatRect START **************"

    nShits=sTree.strawtubesPoint.GetEntriesFast()
    nMCTracks = sTree.MCTrack.GetEntriesFast()

    #if nMCTracks < 100:
    if nShits < 500:

        ############################################# Digitization #####################################################

        StrawRaw,StrawRawLink=Digitization(sTree,SmearedHits)
        reconstructibleevents+=1

        ########################################## Looking tracks in station 1&2 #######################################

        nr12tracks, \
        tracks12, \
        hitids12, \
        xtan12, \
        xcst12, \
        stereotan12, \
        stereocst12, \
        px12, \
        py12, \
        pz12, \
        fraction12, \
        trackid12 = PatRec(True,zlayer,zlayerv2,StrawRaw,StrawRawLink, ShipGeo)


        ########################################## Looking tracks in station 3&4 #######################################

        nr34tracks, \
        tracks34, \
        hitids34, \
        xtan34, \
        xcst34, \
        stereotan34, \
        stereocst34, \
        px34, \
        py34, \
        pz34, \
        fraction34, \
        trackid34 = PatRec(False,z34layer,z34layerv2,StrawRaw,StrawRawLink, ShipGeo)



        if debug==1:
            if (nr12tracks>0) :
                print nr12tracks,"tracks12  ",tracks12
                print "hitids12  ",hitids12
                print "xtan  ",xtan12,"xcst",xcst12
                print "stereotan  ",stereotan12,"stereocst  ",stereocst12
                print "fraction12",fraction12,"trackid12",trackid12
            else :
                print "No tracks found in stations 1&2."

            if (nr34tracks>0) :
                print nr34tracks,"tracks34  ",tracks34
                print "hitids34  ",hitids34
                print "xtan34 ",xtan34,"xcst34 ",xcst34
                print "stereotan34  ",stereotan34,"stereocst34  ",stereocst34
                print "px34",px34
            else :
                print "No tracks found in stations 3&4."


        ################################# Matching tracks before and after the magnet ##################################

        zmagnet=ShipGeo.Bfield.z
        matches=0

        for item in xtan12:
            z1=0.
            tgy1=xtan12[item]
            tgx1=stereotan12[item]
            y1=xcst12[item]
            x1=stereocst12[item]
            t1=[x1,y1,z1,tgx1,tgy1]
            for ids in hitids12[item]:
                #cheated
                if ids != 999 :
                    #loop until we get the particle of this track
                    particle12   = PDG.GetParticle(StrawRawLink[ids][0].PdgCode())
                    try:
                        charge12=particle12.Charge()/3.
                        break
                    except:
                        continue

            falsenegativethistrack=0
            falsepositivethistrack=0
            for item1 in xtan34:
                rawlinkindex=0
                for ids in hitids34[item1]:
                    if ids != 999 :
                        particle34   = PDG.GetParticle(StrawRawLink[ids][0].PdgCode())
                        try:
                            charge34=particle34.Charge()/3.
                            break
                        except:
                            continue
                z2=0.
                tgx2=stereotan34[item1]
                tgy2=xtan34[item1]
                y2=xcst34[item1]
                x2=stereocst34[item1]
                t2=[x2,y2,z2,tgx2,tgy2]

                dx,dy,alpha,pinv=match_tracks(t1,t2,zmagnet,-0.75)
                p2x=px34[item1]
                p2y=py34[item1]
                p2z=pz34[item1]
                p2true=1./math.sqrt(p2x**2+p2y**2+p2z**2)
                if debug==1: print "Matching 1&2 track",item,"with 3&4 track",item1,"dx",dx,"dy",dy,"alpha",alpha,"pinv",pinv,"1/p2true",p2true
                if ((abs(dx)<20) & (abs(dy)<2)) :
                    #match found between track nr item in stations 12 & item1 in stations 34
                    #get charge from deflection and check if it corresponds to the MC truth
                    #field is horizontal (x) hence deflection in y
                    tantheta=(tgy1-tgy2)/(1+tgy1*tgy2)
                    if tantheta>0 :
                        charge="-1"
                        if charge34>0:
                            falsenegative+=1
                            falsenegativethistrack=1
                    else:
                        charge="1"
                        if charge34<0:
                            falsepositive+=1
                            falsepositivethistrack=1

                    #reject track (and event) if it doesn't correspond to MC truth
                    if matches==0:
                        matches==1
                        totalaftermatching+=1

                    if debug==1:
                        print "******* MATCH FOUND stations 12 track id",trackid12[item],"(fraction",fraction12[item]*100,"%) and stations 34 track id",trackid34[item1],"(fraction",fraction34[item1]*100,"%)"


                    ####################################### True Momentum Estimation ###################################

                    p2true=p2true*int(charge)

                    ################################### Collect recognized tracks ######################################

                    hits = []
                    hitPosList=[]

                    for ids in range(0,len(hitids12[item])):
                        if hitids12[item][ids]!=999 :
                            m=[]
                            if ids in range(0,32):
                                for z in range(0,7):
                                    m.append(StrawRaw[hitids12[item][ids]][z])
                            hitPosList.append(m)
                            hits.append(hitids12[item][ids])


                    for ids in range(0,len(hitids34[item1])):
                        if hitids34[item1][ids]!=999 :
                            m=[]
                            if ids in range(0,32):
                                for z in range(0,7):
                                    m.append(StrawRaw[hitids34[item1][ids]][z])
                            hitPosList.append(m)
                            hits.append(hitids34[item1][ids])


                    reco_tracks[track_id] = {'hits': numpy.array(hits),
                                             'hitPosList': hitPosList,
                                             'charge': int(charge),
                                             'pinv': pinv,
                                             'params12': [[tgy1, y1], [tgx1, x1]],
                                             'params34': [[tgy2, y2], [tgx2, x2]]}
                    track_id += 1


                    ########################################### Track fit ##############################################

                    nM = len(hitPosList)
                    if nM<25:
                        if debug==1: print "Only",nM,"hits on this track. Insufficient for fitting."
                        return
                    #all particles are assumed to be muons
                    if int(charge)<0:
                        pdg=13
                    else:
                        pdg=-13
                    rep = ROOT.genfit.RKTrackRep(pdg)
                    posM = ROOT.TVector3(0, 0, 0)
                    #would be the correct way but due to uncertainties on small angles the sqrt is often negative
                    if math.fabs(pinv) > 0.0 : momM = ROOT.TVector3(0,0,int(charge)/pinv)
                    else: momM = ROOT.TVector3(0,0,999)
                    covM = ROOT.TMatrixDSym(6)
                    resolution = ShipGeo.strawtubes.sigma_spatial
                    for  i in range(3):   covM[i][i] = resolution*resolution
                    covM[0][0]=resolution*resolution*100.
                    for  i in range(3,6): covM[i][i] = ROOT.TMath.Power(resolution / nM / ROOT.TMath.Sqrt(3), 2)
                    # smeared start state
                    stateSmeared = ROOT.genfit.MeasuredStateOnPlane(rep)
                    rep.setPosMomCov(stateSmeared, posM, momM, covM)
                    # create track
                    seedState = ROOT.TVectorD(6)
                    seedCov   = ROOT.TMatrixDSym(6)
                    rep.get6DStateCov(stateSmeared, seedState, seedCov)
                    theTrack=ROOT.genfit.Track(rep, seedState, seedCov)
                    TrackFit(hitPosList,theTrack,charge,pinv, ShipGeo, theTracks)
                    fittedtrackids.append(trackid34[item1])

                else :
                    if debug==1: print "******* MATCH NOT FOUND stations 12 track id",trackid12[item],"(fraction",fraction12[item]*100,"%) and stations 34 track id",trackid34[item1],"(fraction",fraction34[item1]*100,"%)"
                    if trackid12[item]==trackid34[item1] :
                        if debug==1: print "trackids the same, but not matched."

    else:
        #remove events with >500 hits
        morethan500+=1
        return

        #else:
        #morethan100tracks+=1
        #return
    return reco_tracks, theTracks#fittedtrackids


def finalize():
    pass
