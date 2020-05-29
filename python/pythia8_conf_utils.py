from __future__ import print_function
from __future__ import division
import os
import sys
import re
import six
import numpy as np
import scipy.interpolate
import ROOT
import shipunit as u

def addHNLtoROOT(pid=9900015 ,m = 1.0, g=3.654203020370371E-21):
    pdg = ROOT.TDatabasePDG.Instance()
    pdg.AddParticle('N2','HNL', m, False, g, 0., 'N2', pid) 

def getbr_rpvsusy(h,histoname,mass,coupling):
    if histoname in h:
        normalized_br = h[histoname](mass)
        br = normalized_br * coupling
    else:
        br = 0
    return br

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
           sumbrs[meson]+=getbr_rpvsusy(h,histoname,mass,coupling)
       except:
           sumbrs[meson]=getbr_rpvsusy(h,histoname,mass,coupling)
    print(list(sumbrs.values()))
    maxsumbr=max(sumbrs.values())
    return maxsumbr

def gettotalbrrpvsusy(h,histograms,mass,couplings):
    totalbr=0.0 
    for histoname in histograms: 
       item = histoname.split('_') 
       coupling=couplings[1]
       totalbr+=getbr_rpvsusy(h,histoname,mass,coupling)
    return totalbr

def make_particles_stable(P8gen, above_lifetime):
    # FIXME: find time unit and add it to the docstring
    """
    Make the particles with a lifetime above the specified one stable, to allow
    them to decay in Geant4 instead.
    """
    p8 = P8gen.getPythiaInstance()
    n=1
    while n!=0:
        n = p8.particleData.nextId(n)
        p = p8.particleData.particleDataEntryPtr(n)
        if p.tau0() > above_lifetime:
            command = "{}:mayDecay = false".format(n)
            p8.readString(command)
            print("Pythia8 configuration: Made {} stable for Pythia, should decay in Geant4".format(p.name()))

def parse_histograms(filepath):
    """
    This function parses a file containing histograms of branching ratios.

    It places them in a dictionary indexed by the decay string (e.g. 'd_K0_e'),
    as a pair ([masses...], [branching ratios...]), where the mass is expressed
    in GeV.
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()
    # Define regular expressions matching (sub-)headers and data lines
    th1f_exp      = re.compile(r'^TH1F\|.+')
    header_exp    = re.compile(r'^TH1F\|(.+?)\|B(?:R|F)/U2(.+?)\|.+? mass \(GeV\)\|?')
    subheader_exp = re.compile(r'^\s*?(\d+?),\s*(\d+?\.\d+?),\s*(\d+\.\d+)\s*$')
    data_exp      = re.compile(r'^\s*(\d+?)\s*,\s*(\d+\.\d+)\s*$')
    # Locate beginning of each histogram
    header_line_idx = [i for i in range(len(lines)) if th1f_exp.match(lines[i]) is not None]
    # Iterate over histograms
    histograms = {}
    for offset in header_line_idx:
        # Parse header
        mh = header_exp.match(lines[offset])
        if mh is None or len(mh.groups()) != 2:
            raise ValueError("Malformed header encountered: {0}".format(lines[offset]))
        decay_code = mh.group(1)
        # Parse sub-header (min/max mass and number of points)
        ms = subheader_exp.match(lines[offset+1])
        if ms is None or len(ms.groups()) != 3:
            raise ValueError("Malformed sub-header encountered: {0}".format(lines[offset+1]))
        npoints  = int(ms.group(1))
        min_mass = float(ms.group(2))
        max_mass = float(ms.group(3))
        masses = np.linspace(min_mass, max_mass, npoints, endpoint=False)
        branching_ratios = np.zeros(npoints)
        # Now read the data lines (skipping the two header lines)
        for line in lines[offset+2:offset+npoints+1]:
            md = data_exp.match(line)
            if md is None or len(md.groups()) != 2:
                raise ValueError("Malformed data row encountered: {0}".format(line))
            idx = int(md.group(1))
            br  = float(md.group(2))
            branching_ratios[idx] = br
        histograms[decay_code] = (masses, branching_ratios)
    return histograms

def make_interpolators(filepath, kind='linear'):
    """
    This function reads a file containing branching ratio histograms, and
    returns a dictionary of interpolators of the branching ratios, indexed by
    the decay string.
    """
    histogram_data = parse_histograms(filepath)
    histograms = {}
    for (hist_string, (masses, br)) in six.iteritems(histogram_data):
        histograms[hist_string] = scipy.interpolate.interp1d(
            masses, br, kind=kind, bounds_error=False, fill_value=0, assume_sorted=True)
    return histograms

def get_br(histograms, channel, mass, couplings):
    """
    Utility function used to reliably query the branching ratio for a given
    channel at a given mass, taking into account the correct coupling.
    """
    hist = histograms[channel['decay']]
    coupling = couplings[channel['coupling']]
    normalized_br = hist(mass)
    return normalized_br * coupling

def add_particles(P8gen, particles, data):
    """
    Adds the corresponding particles to PYTHIA.

    `particles` must be a list containing either the particles PDG IDs, or
    their PYTHIA names. The commands needed to add the particles are queried
    from `data`.

    If the particle is not self-conjugate, the antiparticle is automatically
    added by PYTHIA.
    """
    for particle_id in particles:
        # Find particle in database (None: particle not found)
        particle = next((p for p in data['particles']
                         if particle_id in [p['id'], p['name']]), None)
        if particle is None:
            raise ValueError("Could not find particle ID {0} in file {1}"
                             .format(particle, datafile))
        # Add the particle
        P8gen.SetParameters(particle['cmd'])

def add_channel(P8gen, ch, histograms, mass, couplings, scale_factor):
    "Add to PYTHIA a leptonic or semileptonic decay channel to HNL."
    if 'idlepton' in ch:
        br = get_br(histograms, ch, mass, couplings)
        if br <= 0: # Ignore kinematically closed channels
            return
        if 'idhadron' in ch: # Semileptonic decay
            P8gen.SetParameters('{}:addChannel      1  {:.17}   22      {}       9900015   {}'.format(ch['id'], br*scale_factor, ch['idlepton'], ch['idhadron']))
        else: # Leptonic decay
            P8gen.SetParameters('{}:addChannel      1  {:.17}    0       9900015      {}'.format(ch['id'], br*scale_factor, ch['idlepton']))
    else: # Wrong decay
        raise ValueError("Missing key 'idlepton' in channel {0}".format(ch))

def add_tau_channel(P8gen, ch, histograms, mass, couplings, scale_factor):
    "Add to PYTHIA a tau decay channel to HNL."
    if 'idhadron' in ch:
        br = get_br(histograms, ch, mass, couplings)
        if br <= 0: # Ignore kinematically closed channels
            return
        if 'idlepton' in ch: # 3-body leptonic decay
            P8gen.SetParameters('{}:addChannel      1  {:.16}    1531       9900015      {} {}'.format(ch['id'], br*scale_factor, ch['idlepton'], ch['idhadron']))
        else: # 2-body semileptonic decay
            P8gen.SetParameters('{}:addChannel      1  {:.16}    1521       9900015      {}'.format(ch['id'], br*scale_factor, ch['idhadron']))
    else:
        raise ValueError("Missing key 'idhadron' in channel {0}".format(ch))

def fill_missing_channels(P8gen, max_total_br, decay_chains, epsilon=1e-6):
    """
    Add dummy channels for correct rejection sampling.

    Even after rescaling the branching ratios, they do not sum up to unity
    for most particles since we are ignoring SM processes.

    This function adds a "filler" channel for each particle, in order to
    preserve the ratios between different branching ratios.
    """
    top_level_particles = get_top_level_particles(decay_chains)
    for particle in top_level_particles:
        my_total_br = compute_total_br(particle, decay_chains)
        remainder = 1 - my_total_br / max_total_br
        assert(remainder > -epsilon)
        assert(remainder < 1 + epsilon)
        if remainder > epsilon:
            add_dummy_channel(P8gen, particle, remainder)

def add_dummy_channel(P8gen, particle, remainder):
    """
    Add a dummy channel to PYTHIA, with branching ratio equal to `remainder.`

    The purpose of this function is to compensate for the absence of SM
    channels, which are ignored when investigating rare processes. A dummy
    decay channel is instead added to each particle in order to maintain the
    correct ratios between the branching ratios of each particle to rare
    processes. This is usually combined with a global reweighting of the
    branching ratios.

    In order to keep PYTHIA from complaining about charge conservation, a
    suitable process is added which conserves electric charge.

    All dummy channels can be identified by the presence of a photon among the
    decay products.
    """
    pdg = P8gen.getPythiaInstance().particleData
    charge = pdg.charge(particle)
    if charge > 0:
        P8gen.SetParameters('{}:addChannel      1   {:.16}    0       22      -11'.format(particle, remainder))
    elif charge < 0:
        P8gen.SetParameters('{}:addChannel      1   {:.16}    0       22       11'.format(particle, remainder))
    else:
        P8gen.SetParameters('{}:addChannel      1   {:.16}    0       22      22'.format(particle, remainder))

def compute_max_total_br(decay_chains):
    """
    This function computes the maximum total branching ratio for all decay chains.

    In order to make the event generation as efficient as possible when
    studying very rare processes, it is necessary to rescale the branching
    ratios, while enforcing the invariant that any total branching ratio must
    remain lower that unity.

    This is accomplished by computing, for each particle, the total branching
    ratio to processes of interest, and then dividing all branching ratios by
    the highest of those.

    Note: the decay chain length must be at most 2.
    """
    # For each top-level charmed particle, sum BR over all its decay chains
    top_level_particles = get_top_level_particles(decay_chains)
    total_branching_ratios = [compute_total_br(particle, decay_chains)
                              for particle in top_level_particles]
    # Find the maximum total branching ratio
    return max(total_branching_ratios)

def compute_total_br(particle, decay_chains):
    """
    Returns the total branching ratio to HNLs for a given particle.
    """
    return sum(np.prod(branching_ratios)
               for (top, branching_ratios) in decay_chains
               if top == particle)

def get_top_level_particles(decay_chains):
    """
    Returns the set of particles which are at the top of a decay chain.
    """
    return set(top for (top, branching_ratios) in decay_chains)

def exit_if_zero_br(max_total_br, selection, mass, particle='HNL'):
    if max_total_br <= 0:
        print("No phase space for {0} from {1} at this mass: {2}. Quitting."
              .format(particle, selection, mass))
        sys.exit()

def print_scale_factor(scaling_factor):
    "Prints the scale factor used to make event generation more efficient."
    print("One simulated event per {0:.4g} meson decays".format(scaling_factor))
