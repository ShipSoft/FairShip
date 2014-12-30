"""

   Module to compute SHiP's sensitivity to HNLs
   * makes HNLs decay in SHiP's volume
   * determines the list of kinematically allowed decays
   * computes the number of expected events in SHiP
   Author: Elena Graverini (elena.graverini@cern.ch)
   Last updated: 30/12/2014
   
"""
from __future__ import division
import numpy as np
import gc
from saveHNLPdfs import *
import readDecayTable
import random
import timeit


'''
def computeEllipticalAcceptance(ntuple, ellVol, P_kick, shape='round', exclude5m='False'):
    nTot = ntuple.GetEntriesFast()
    nInAcc = 0
    for (i,event) in enumerate(ntuple):
        #if i < 100:
        vtx = r.TVector3(event.Vtx_X, event.Vtx_Y, event.Vtx_Z)
        kid1 = r.TLorentzVector(event.Kid1_Px, event.Kid1_Py, event.Kid1_Pz, event.Kid1_E)
        kid2 = r.TLorentzVector(event.Kid2_Px, event.Kid2_Py, event.Kid2_Pz, event.Kid2_E)
        nInAcc += int( inEllipticalAcceptance(vtx, [kid1, kid2], ellVol, P_kick, shape, exclude5m) )
    return float(nInAcc)/float(nTot)
'''



def makeDecayInVolume(hh, decayString, volumeIndex, config, statistic=100):
    pN = r.TLorentzVector()
    vec = r.TVector3()
    inVol = 0

    sourceHist = hh.weightedProdHistVols[volumeIndex]
    
    '''if volume == 1:
        sourceHist = hh.weightedProdHistVol1
    elif volume == 2:
        sourceHist = hh.weightedProdHistVol2
    else:
        print 'makeDecayInVolume ERROR: please select volume 1 or 2'
        return 0

    '''
    for i in xrange(statistic):
        momN, thetaN = r.Double(), r.Double()
        sourceHist.GetRandom2(momN, thetaN)
        #vec.SetMagThetaPhi(momN, thetaN, 0.)
        vec.SetMagThetaPhi(momN, thetaN, r.gRandom.Uniform(2.*math.pi))
        pN.SetVect(vec)
        pN.SetE(hh.pp.energy(momN, hh.pp.MN))
        kids = HNLDecayChain(hh, decayString, pN)
        NDecayVtx = hh.ep.makeVtxInVolume(pN, hh.pp.c*hh.pp.NLifetime, volumeIndex)
        #inVol += int( hh.ep.inAcceptance(NDecayVtx, kids, volume) )
        #inVol += int(hh.ep.inEllipticalAcceptance(NDecayVtx, kids, volumeIndex, config.P_kick_Null, config.shape, config.excludeFirst5m))
        inVol += int(hh.ep.inEllipticalAcceptance(NDecayVtx, kids, volumeIndex, config.P_kick, config.shape, config.excludeFirst5m))

    volume = hh.ep.decayVolumes[volumeIndex]
    statistic *= (math.pi*volume.a1*volume.b1) / (math.pi*volume.b1*volume.b1)
    return inVol/statistic, statistic    

def HNLDecayChain(hh, decayString, pN):
    """ Returns the 4-momenta of the final detectable daughters """
    kids = []
    if decayString == 'N -> nu nu nu':
        kids = []
    elif decayString in hh.pp.decays[:7]: # 3-body, return the first two
        hh.ev.decay.readString(decayString)
        hh.ev.decay.setPMother(pN)
        pGKid1, pGKid2, pGKid3 = hh.ev.decay.makeDecay()
        kids = [pGKid1, pGKid2]
    elif decayString == 'N -> rho nu':
        hh.ev.decay.readString(decayString)
        hh.ev.decay.setPMother(pN)
        pGKid1, pGKid2 = hh.ev.decay.makeDecay()
        hh.ev.decay.readString('rho -> pi pi')
        hh.ev.decay.setPMother(pGKid1)
        pGKid1, pGKid2 = hh.ev.decay.makeDecay()
        pPi1, pPi2 = r.TLorentzVector(pGKid1), r.TLorentzVector(pGKid2)
        kids = [pPi1, pPi2]
    elif decayString in hh.pp.decays[11:13]: # N -> rho l
        hh.ev.decay.readString(decayString)
        hh.ev.decay.setPMother(pN)
        pGKid1, pGKid2 = hh.ev.decay.makeDecay() # rho+lepton
        pLepton = r.TLorentzVector(pGKid2)
        hh.ev.decay.readString('rho -> pi pi0')
        hh.ev.decay.setPMother(pGKid1)
        pGKid1, pGKid3 = hh.ev.decay.makeDecay() # pi+pi0
        pPi = r.TLorentzVector(pGKid1)
        hh.ev.decay.readString('pi0 -> gamma gamma')
        hh.ev.decay.setPMother(pGKid3)
        pGKid3, pGKid4 = hh.ev.decay.makeDecay() # 2 gamma
        pG1, pG2 = r.TLorentzVector(pGKid3), r.TLorentzVector(pGKid4)
        kids = [pLepton, pPi, pG1, pG2] # lepton+pi+2gamma
    elif decayString == 'N -> pi0 nu': # DIFFICILE DA MISURARE, RICHIEDE STUDIO BG
        hh.ev.decay.readString(decayString)
        hh.ev.decay.setPMother(pN)
        pGKid1, pGKid2 = hh.ev.decay.makeDecay()
        hh.ev.decay.readString('pi0 -> gamma gamma')
        hh.ev.decay.setPMother(pGKid1)
        pGKid1, pGKid2 = hh.ev.decay.makeDecay()
        pG1, pG2 = r.TLorentzVector(pGKid1), r.TLorentzVector(pGKid2)
        kids = [pG1, pG2]
    else: #two-body, charged
        hh.ev.decay.readString(decayString)
        hh.ev.decay.setPMother(pN)
        pGKid1, pGKid2 = hh.ev.decay.makeDecay()
        kids = [pGKid1, pGKid2]   
    return kids


def computeNEvents(model, mass, coupling, energy=400, save_pdf=False, root_dir_path=os.getcwd()+'/..'):
    """ Choose model 1, 2, 3, 4, 5 or 6 """
    #start_time = timeit.default_timer()

    r.gRandom.SetSeed(0)
    pp = physicsParameters(energy,root_dir_path+"/Base")
    pp.setNMass(mass)                   
    # Check kinematics
    sources = []
    if pp.MN < max(pp.m_max['charm']):
        sources.append('charm')
    if pp.MN < max(pp.m_max['beauty']) and energy==400:
        sources.append('beauty')

    if len(sources)==0:
        print "ERROR in computeNEvents function."
        quit()
        
    pp.setNCoupling([coupling*f for f in pp.models[model-1]])
    print 'Lifetime: %2.2e'%(pp.computeNLifetime() * pp.c)
    ep = experimentParams(pp, 'SHIP')

    print 'a1, b1, a2, b2, z1, z2:'
    for v in ep.decayVolumes:
        print v.a1, v.b1, v.a2, v.b2, v.z1, v.z2

    BRprod = []
    NEv = 0.

    hists = []
    accvs = []
    for source in sources:
        hh = HistoHandler(pp, ep, source, model, save_pdf)
        if hh.makeProductionPDF(ep.decayVolumes[0]):
            accvs = hh.scaleProductionPDF(pp.U2)
            print "P(vtx in volume): ", accvs
            print "Ptot(vtx in volume): ", sum(accvs)
            decList = hh.pp.HNLAllowedDecays()
            weights = [0 for accv in accvs]
            
            for dec in decList:
                if decList[dec] == 'yes' and dec != 'N -> pi0 nu' and dec != 'N -> nu nu nu':
                    #print dec
                    for index in xrange(len(accvs)):
                        if accvs[index]:
                            acc, tot = makeDecayInVolume(hh, dec, index, ep.cfg)
                        else:
                            acc = 0.
                        weights[index] += hh.pp.findBranchingRatio(dec)*acc

                    '''
                    if accv1:
                        acc1, tot1 = makeDecayInVolume(hh, dec, 1)
                    else:
                        acc1 = 0.
                    if accv2:
                        acc2, tot2 = makeDecayInVolume(hh, dec, 2)
                    else:
                        acc2 = 0.
                    weight1 += hh.pp.findBranchingRatio(dec)*acc1
                    weight2 += hh.pp.findBranchingRatio(dec)*acc2
                    '''
            fullAcc = 0.
            for index in xrange(len(accvs)):
                fullAcc += accvs[index]*weights[index]
                
            BRprod_s = 0.
            U2tot = sum(pp.U2)
            for flavour in [1,2,3]:
                BRprod_s += productionBR(pp, source, flavour) * pp.U2[flavour-1]/U2tot
            #NEv += (accv1*weight1 + accv2*weight2)*2.*BRprod_s*hh.ep.protonFlux
            NEv += fullAcc*2.*BRprod_s*hh.ep.protonFlux
            BRprod.append(BRprod_s)
        hh.sourceFile.Close()
        if save_pdf:
            hh.weightedPDFoutfile.Close()
            hh.prodPDFoutfile.Close()
        hists.append(hh)

    #elapsed = timeit.default_timer() - start_time
    #print "Time elapsed: ", elapsed

    outFilePath = root_dir_path + "/Analysis/out/TextData/sensitivityScan-HNL-model%s_E%GeV.txt"%(model,energy)
    with open(outFilePath,"a") as ofile:
        try:
            ofile.write('%s \t %s \t %s \t %s\n'%(mass, coupling, sum(BRprod), NEv))
        except KeyboardInterrupt:
            pass

    if save_pdf:
        print "I will save the PDF"
        return NEv, hists
    print "I will NOT save the PDF"
    return NEv




def computeHNLAcceptance(model, mass, coupling, energy=400, save_pdf=False, root_dir_path=os.getcwd()+'/..'):
    """ Choose model 1, 2, 3, 4, 5 or 6 """
    #start_time = timeit.default_timer()
    r.gRandom.SetSeed(0)
    pp = physicsParameters(energy,root_dir_path+"/Base")
    pp.setNMass(mass)                   
    # Check kinematics
    sources = []
    if pp.MN < max(pp.m_max['charm']):
        sources.append('charm')
    #if pp.MN < max(pp.m_max['beauty']) and energy==400:
    #    sources.append('beauty')
    if len(sources)==0:
        print "ERROR: no HNL sources found"
        sys.exit(-1)
    pp.setNCoupling([coupling*f for f in pp.models[model-1]])
    print 'Lifetime: %2.2e m'%(pp.computeNLifetime() * pp.c)
    ep = experimentParams(pp, 'SHIP')
    print 'a1, b1, a2, b2, z1, z2:'
    for v in ep.decayVolumes:
        print v.a1, v.b1, v.a2, v.b2, v.z1, v.z2
    BRprod = []
    NEv = 0.
    accvs = []
    #for source in sources:
    hh = HistoHandler(pp, ep, 'charm', model, save_pdf)
    AcceptanceTable = {}
    if hh.makeProductionPDF(ep.decayVolumes[0]):
        accvs = hh.scaleProductionPDF(pp.U2)
        print "P(vtx in volume): ", accvs
        print "Ptot(vtx in volume): ", sum(accvs)
        decList = hh.pp.HNLAllowedDecays()
        configuredDecays = readDecayTable.load(verbose=True)
        weights = [0 for accv in accvs]
        for dec in decList:
            if dec not in configuredDecays:
                print 'ERROR: channel not configured!\t', dec
                sys.exit(-1)
            if decList[dec] == 'yes' and configuredDecays[dec] == 'yes':
                AcceptanceTable[dec] = {}
                AcceptanceTable[dec]['VtxProbability'] = []
                AcceptanceTable[dec]['DaughtersAcceptance'] = []
                #print dec
                total_acc = 0.
                for index in xrange(len(accvs)):
                    if accvs[index]:
                        acc, tot = makeDecayInVolume(hh, dec, index, ep.cfg, 500)
                    else:
                        acc = 0.
                    total_acc += acc*accvs[index]
                    weights[index] += hh.pp.findBranchingRatio(dec)*acc
                    AcceptanceTable[dec]['VtxProbability'].append(accvs[index])
                    AcceptanceTable[dec]['DaughtersAcceptance'].append(acc)
                AcceptanceTable[dec]['BR'] = hh.pp.findBranchingRatio(dec)

                AcceptanceTable[dec]['TotalAcceptance'] = total_acc
        fullAcc = 0.
        for index in xrange(len(accvs)):
            fullAcc += accvs[index]*weights[index]
        #BRprod_s = 0.
        #U2tot = sum(pp.U2)
        #for flavour in [1,2,3]:
        #    BRprod_s += productionBR(pp, source, flavour) * pp.U2[flavour-1]/U2tot
        #NEv += fullAcc*2.*BRprod_s*hh.ep.protonFlux
        #BRprod.append(BRprod_s)
    hh.sourceFile.Close()
    if save_pdf:
        hh.weightedPDFoutfile.Close()
        hh.prodPDFoutfile.Close()
    #elapsed = timeit.default_timer() - start_time
    #print "Time elapsed: ", elapsed
    print 'Computed acceptance: ', fullAcc
    return AcceptanceTable










"""
if __name__ == '__main__':
    pp = physicsParameters()
    pp.setNMass(1.)
    pp.setNCoupling([0.25e-08, 1.e-08, 0.5e-08])
    ep = experimentParams(pp, 'SHIP')
    hh = HistoHandler(pp, ep)
    rawPDF = hh.makeProductionPDF()
    accv1, accv2 = hh.scaleProductionPDF([0.25e-08, 1.e-08, 0.5e-08])
    print accv1, accv2
    decList = HNLAllowedDecays(hh.pp)
    #print decList
    tot = 0.
    weight1 = 0.
    weight2 = 0.
    for dec in decList:
        if decList[dec] == 'yes' and dec != 'N -> pi0 nu' and dec != 'N -> nu nu nu':
            acc1, tot1 = makeDecayInVolume(hh, dec, 1)
            acc2, tot2 = makeDecayInVolume(hh, dec, 2)
            print dec + '\t', acc1, acc2, '\t BR: ', hh.pp.findBranchingRatio(dec)
            tot += hh.pp.findBranchingRatio(dec)
            weight1 += hh.pp.findBranchingRatio(dec)*acc1
            weight2 += hh.pp.findBranchingRatio(dec)*acc2
    #fracV1, tot = makeDecayInVolume(hh, 'N -> mu mu nu', 1)
    print tot, weight1, weight2
    NEv = (accv1*weight1 + accv2*weight2)*2.*hh.pp.Xcc*hh.pp.computeNProdBR(2)*hh.ep.protonFlux
    #print fracV1, tot
    print 'NEv: ', NEv
    hh.weightedPDFoutfile.Close()
    hh.prodPDFoutfile.Close()
    hh.charmFile.Close()

"""
