"""
# ==================================================================
#   Python module
#
#   This module provides methods to read a configuration file
#   storing on/off (yes/no) flags for the HNL decay channels
#   and to pass the configured decay table to a Pythia8 generator.
#
#   Created: 30/12/2014 Elena Graverini (elena.graverini@cern.ch)
#
# ==================================================================
"""
from __future__ import division
from __future__ import print_function
import ROOT, os, csv
from hnl import PDGname
from darkphoton import *

pdg = ROOT.TDatabasePDG.Instance()

def PDGcode(particle):
    """
    Read particle ID from PDG database
    """
    particle = PDGname(particle)
    tPart = pdg.GetParticle(particle)
    return int(tPart.PdgCode())


def load(conffile = os.path.expandvars('$FAIRSHIP/python/DecaySelection.conf'), verbose=True):
    f = open(conffile,'r')
    reader = csv.reader(f, delimiter=':')
    configuredDecays = {}
    for row in reader:
        if not row: continue # skip empty lines
        if str(row[0]).strip().startswith('#'):
            continue # skip comment / header lines
        channel = str(row[0]).strip()
        flag = str(row[-1]).partition('#')[0].strip() # skip line comments
        configuredDecays[channel] = flag
    if verbose:
        print('Activated decay channels (plus charge conjugates): ')
        for channel in configuredDecays.keys():
            if configuredDecays[channel] == 'yes':
                print('\t'+channel)        
    return configuredDecays 

def addHNLdecayChannels(P8Gen, hnl, conffile=os.path.expandvars('$FAIRSHIP/python/DecaySelection.conf'), verbose=True):
    """
    Configures the HNL decay table in Pythia8
    Inputs:
    - P8Gen: an instance of ROOT.HNLPythia8Generator()
    - hnl: an instance of hnl.HNL()
    - conffile: a file listing the channels one wishes to activate
    """
    # First fetch the list of kinematically allowed decays
    allowed = hnl.allowedChannels()
    # Then fetch the list of desired channels to activate
    wanted = load(conffile=conffile, verbose=verbose)
    # Add decay channels
    for dec in allowed:
        if dec not in wanted:
            print('addHNLdecayChannels ERROR: channel not configured!\t', dec)
            quit()
        if allowed[dec] == 'yes' and wanted[dec] == 'yes':
            particles = [p for p in dec.replace('->',' ').split()]
            children = particles[1:]
            childrenCodes = [PDGcode(p) for p in children]
            BR = hnl.findBranchingRatio(dec)
            # Take care of Majorana modes
            BR = BR/2.
            codes = ' '.join([str(code) for code in childrenCodes])
            P8Gen.SetParameters('9900015:addChannel =  1 {:.12} 0 {}'.format(BR, codes))
            # Charge conjugate modes
            codes = ' '.join([(str(-1*code) if pdg.GetParticle(-code)!=None else str(code)) for code in childrenCodes])
            P8Gen.SetParameters('9900015:addChannel =  1 {:.12} 0 {}'.format(BR, codes))
            # print "debug readdecay table",particles,children,BR

def addDarkPhotondecayChannels(P8gen, mDP, DP,conffile=os.path.expandvars('$FAIRSHIP/python/darkphotonDecaySelection.conf'), verbose=True):
    """
    Configures the DP decay table in Pythia8
    
    Inputs:
    - P8gen: an instance of ROOT.HNLPythia8Generator()
    - conffile: a file listing the channels one wishes to activate
    """
    isResonant = (P8gen.GetDPId()==4900023)# or P8gen.IsPbrem())
    # First fetch the list of kinematically allowed decays
    allowed = DP.allowedChannels()
    # Then fetch the list of desired channels to activate
    wanted = load(conffile=conffile, verbose=verbose)
    # Add decay channels
    for dec in allowed:
        print('channel allowed:',dec)
        if dec not in wanted:
            print('addDarkPhotondecayChannels WARNING: channel not configured! Please add also in conf file.\t', dec)
            quit()
        print('channel wanted:',dec)

        if allowed[dec] == 'yes' and wanted[dec] == 'yes':
            
            BR = DP.findBranchingRatio(dec)
            
            meMode = 0
            if isResonant: meMode = 103
            if 'hadrons' in dec:
                #P8gen.SetDecayToHadrons()
                print("debug readdecay table hadrons BR ",BR)
                #Taking decays from pythia8 Z->qqbar
                dpid = P8gen.GetDPId()
                if mDP<3.0:
                    P8gen.SetParameters("{}:addChannel =  1 {:.12} {} 1 -1"\
                                        .format(dpid, 0.167*BR, meMode))
                    P8gen.SetParameters("{}:addChannel =  1 {:.12} {} 2 -2"\
                                        .format(dpid, 0.666*BR, meMode))
                    P8gen.SetParameters("{}:addChannel =  1 {:.12} {} 3 -3"\
                                        .format(dpid, 0.167*BR, meMode))
                if mDP>=3.0:
                    P8gen.SetParameters("{}:addChannel =  1 {:.12} {} 1 -1"\
                                        .format(dpid, 0.1*BR, meMode))
                    P8gen.SetParameters("{}:addChannel =  1 {:.12} {} 2 -2"\
                                        .format(dpid, 0.4*BR, meMode))
                    P8gen.SetParameters("{}:addChannel =  1 {:.12} {} 3 -3"\
                                        .format(dpid, 0.1*BR, meMode))
                    P8gen.SetParameters("{}:addChannel =  1 {:.12} {} 4 -4"\
                                        .format(dpid, 0.4*BR, meMode))
            else:
                particles = [p for p in dec.replace('->',' ').split()]
                children = particles[1:]
                childrenCodes = [PDGcode(p) for p in children]
                codes = ' '.join(str(code) for code in childrenCodes)
                P8gen.SetParameters("{}:addChannel =  1 {:.12} {} {}"\
                                    .format(P8gen.GetDPId(), BR, meMode, codes))
                print("debug readdecay table ",particles,children,BR)


if __name__ == '__main__':
    configuredDecays = load()
    print('Activated decay channels: ')
    for channel in configuredDecays.keys():
        if configuredDecays[channel] == 'yes':
            print(channel)
