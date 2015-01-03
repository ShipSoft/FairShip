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
import ROOT, os, csv
from hnl import PDGname

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
        print 'Activated decay channels (plus charge conjugates): '
        for channel in configuredDecays.keys():
            if configuredDecays[channel] == 'yes':
                print '\t'+channel        
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
            print 'addHNLdecayChannels ERROR: channel not configured!\t', dec
            quit()
        if allowed[dec] == 'yes' and wanted[dec] == 'yes':
            particles = [p for p in dec.replace('->',' ').split()]
            children = particles[1:]
            childrenCodes = [PDGcode(p) for p in children]
            BR = hnl.findBranchingRatio(dec)
            if not (('pi0' in dec) or ('rho0' in dec)):
                # Take care of Majorana modes
                BR = BR/2.
                codes = ' '.join([str(code) for code in childrenCodes])
                P8Gen.SetParameters("9900014:addChannel =  1 "+str(BR)+" 0 "+codes)
                # Charge conjugate modes
                codes = ' '.join([str(-1*code) for code in childrenCodes])
                P8Gen.SetParameters("9900014:addChannel =  1 "+str(BR)+" 0 "+codes)
            else:
                codes = ' '.join([str(code) for code in childrenCodes])
                P8Gen.SetParameters("9900014:addChannel =  1 "+str(BR)+" 0 "+codes)


if __name__ == '__main__':
    configuredDecays = load()
    print 'Activated decay channels: '
    for channel in configuredDecays.keys():
        if configuredDecays[channel] == 'yes':
            print channel
