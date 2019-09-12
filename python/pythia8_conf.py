from __future__ import print_function
from __future__ import division
import ROOT
import os
import yaml
import shipunit as u
import hnl
import rpvsusy
from pythia8_conf_utils import *
from method_logger import MethodLogger
import readDecayTable

def configurerpvsusy(P8gen, mass, couplings, sfermionmass, benchmark, inclusive, deepCopy=False, debug=True):
    # configure pythia8 for Ship usage
    if debug:
        pythia_log=open('pythia8_conf.txt','w')
        P8gen = MethodLogger(P8gen, sink=pythia_log)
    h = make_interpolators(
        os.path.expandvars("$FAIRSHIP/shipgen/branchingratiosrpvsusybench{}.dat".format(benchmark)))
    P8gen.UseRandom3() 
    P8gen.SetMom(400)  # beam momentum in GeV 
    if deepCopy: P8gen.UseDeepCopy()
    pdg = ROOT.TDatabasePDG.Instance()
    # let strange particle decay in Geant4
    make_particles_stable(P8gen, above_lifetime=1)

    if inclusive=="True":
        setup_pythia_inclusive(P8gen)

    # generate RPV neutralino from inclusive charm hadrons
    if inclusive=="c":
        P8gen.SetParameters("HardQCD::hardccbar  = on")
        # add RPVSUSY
        rpvsusy_instance = rpvsusy.RPVSUSY(mass, couplings, sfermionmass, benchmark, debug=True)
        ctau = rpvsusy_instance.computeNLifetime(system="FairShip") * u.c_light * u.cm
        print("RPVSUSY ctau ",ctau)
        P8gen.SetParameters("9900015:new = N2 N2 2 0 0 {:.12} 0.0 0.0 0.0 {:.12}  0   1   0   1   0".format(mass, ctau/u.mm))
        P8gen.SetParameters("9900015:isResonance = false")
        P8gen.SetParameters("Next:numberCount    =  0")
        # Configuring decay modes...
        rpvsusy_instance.AddChannelsToPythia(P8gen)

        # Finish HNL setup...
        P8gen.SetParameters("9900015:mayDecay = on")
        P8gen.SetHNLId(9900015)
        # also add to PDG
        gamma = u.hbarc / float(ctau) #197.3269631e-16 / float(ctau) # hbar*c = 197 MeV*fm = 197e-16 GeV*cm
        addHNLtoROOT(pid=9900015,m=mass,g=gamma)
        # 12 14 16 neutrinos replace with N2
        charmhistograms = ['d_mu','ds_mu']
        # no tau decay here to consider
        totaltauBR      = 0.0 
        maxsumBR        = getmaxsumbrrpvsusy(h,charmhistograms,mass,couplings)
        exit_if_zero_br(maxsumBR, inclusive, mass, particle='RPV neutralino')
        totalBR         = gettotalbrrpvsusy(h,charmhistograms,mass,couplings)


        #overwrite D_s+ decays
        P8gen.SetParameters("431:new  D_s+  D_s-    1   3   0    1.96849"\
                            "    0.00000    0.00000    0.00000  1.49900e-01   0   1   0   1   0")
        sumBR=0.
        if getbr_rpvsusy(h,'ds_mu',mass,couplings[1])>0.:
            P8gen.SetParameters("431:addChannel      1  {:.12}    0      -13       9900015"\
                                .format(getbr_rpvsusy(h,'ds_mu',mass,couplings[1])/maxsumBR))
            sumBR+=float(getbr_rpvsusy(h,'ds_mu',mass,couplings[1])/maxsumBR)
        if sumBR<1. and sumBR>0.:
            P8gen.SetParameters("431:addChannel      1   {:.12}    0       22      -11".format(1.-sumBR))

        #overwrite D+ decays
        P8gen.SetParameters("411:new  D+ D-    1   3   0    1.86962"\
                            "    0.00000    0.00000    0.00000  3.11800e-01   0   1   0   1   0")
        sumBR=0.
        if getbr_rpvsusy(h,'d_mu',mass,couplings[1])>0.:
            P8gen.SetParameters("411:addChannel      1  {:.12}    0      -13       9900015"\
                                .format(getbr_rpvsusy(h,'d_mu',mass,couplings[1])/maxsumBR))
            sumBR+=float(getbr_rpvsusy(h,'d_mu',mass,couplings[1])/maxsumBR)
        if sumBR<1. and sumBR>0.:
            P8gen.SetParameters("411:addChannel      1   {:.12}    0       22      -11".format(1.-sumBR))

        P8gen.List(9900015)

    if inclusive=="b":
        P8gen.SetParameters("HardQCD::hardbbbar  = on")
        # add RPVSUSY
        rpvsusy_instance = rpvsusy.RPVSUSY(mass, couplings, sfermionmass, benchmark, debug=True)
        ctau = rpvsusy_instance.computeNLifetime(system="FairShip") * u.c_light * u.cm
        P8gen.SetParameters("9900015:new = N2 N2 2 0 0 {:.12} 0.0 0.0 0.0 {:.12}  0   1   0   1   0".format(mass, ctau/u.mm))
        P8gen.SetParameters("9900015:isResonance = false")
        # Configuring decay modes...
        rpvsusy_instance.AddChannelsToPythia(P8gen)
        # Finish HNL setup...
        P8gen.SetParameters("9900015:mayDecay = on")
        P8gen.SetHNLId(9900015)
        # also add to PDG
        gamma = u.hbarc / float(ctau) #197.3269631e-16 / float(ctau) # hbar*c = 197 MeV*fm = 197e-16 GeV*cm
        addHNLtoROOT(pid=9900015,m=mass,g=gamma)
        # 12 14 16 neutrinos replace with N2
        beautyhistograms = ['b_mu','b_tau','b0_nu_mu','b0_nu_tau']
        maxsumBR=getmaxsumbrrpvsusy(h,beautyhistograms,mass,couplings)
        exit_if_zero_br(maxsumBR, inclusive, mass, particle='RPV neutralino')
        totalBR=gettotalbrrpvsusy(h,beautyhistograms,mass,couplings)

        #overwrite B+ decays
        P8gen.SetParameters("521:new  B+               B-    1   3   0    5.27925"\
                            "    0.00000    0.00000    0.00000  4.91100e-01   0   1   0   1   0")
        sumBR=0.
        if getbr_rpvsusy(h,'b_tau',mass,couplings[1])>0.:
            P8gen.SetParameters("521:addChannel      1  {:.12}    0       9900015      -15"\
                                .format(getbr_rpvsusy(h,'b_tau',mass,couplings[1])/maxsumBR))
            sumBR+=float(getbr_rpvsusy(h,'b_tau',mass,couplings[1])/maxsumBR)
        if sumBR<1. and sumBR>0.:
            P8gen.SetParameters("521:addChannel      1   {:.12}    0       22      22"\
                                .format(1.-sumBR))

        #overwrite B0 decays
        P8gen.SetParameters("511:new  B0  Bbar0    1   0   0    5.27958"\
                            "    0.00000    0.00000    0.00000  4.58700e-01   0   1   0   1   0")
        sumBR=0.
        if getbr_rpvsusy(h,'b0_nu_tau',mass,couplings[1])>0.:
            P8gen.SetParameters("511:addChannel      1  {:.12}   22       9900015      16"\
                                .format(getbr_rpvsusy(h,'b0_nu_tau',mass,couplings[1])/maxsumBR))
        if sumBR<1. and sumBR>0.:
            P8gen.SetParameters("511:addChannel      1   {:.12}    0       22      22"\
                                .format(1.-sumBR))

        P8gen.List(9900015)

    if debug: pythia_log.close()


def configure(P8gen, mass, production_couplings, decay_couplings, process_selection,
              deepCopy=False, debug=True):
    """
    This function configures a HNLPythia8Generator instance for SHiP usage.
    """

    if process_selection == True: # For backward compatibility
        process_selection = 'inclusive'

    # Wrap the Pythia8 object into a class logging all of its method calls
    if debug:
        pythia_log=open('pythia8_conf.txt','w')
        P8gen = MethodLogger(P8gen, sink=pythia_log)

    fairship_root = os.environ['FAIRSHIP'] 
    histograms = make_interpolators(fairship_root + '/shipgen/branchingratios.dat')
    P8gen.UseRandom3() # TRandom1 or TRandom3 ?
    P8gen.SetMom(400)  # beam momentum in GeV 
    if deepCopy: P8gen.UseDeepCopy()
    pdg = ROOT.TDatabasePDG.Instance()
    P8gen.SetParameters("Next:numberCount    =  0")
    # let strange particle decay in Geant4
    make_particles_stable(P8gen, above_lifetime=1)

    # Load particle & decay data
    # ==========================

    datafile = fairship_root + '/python/hnl_production.yaml'
    with open(datafile, 'rU') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    all_channels  = data['channels']

    # Inclusive
    # =========

    if process_selection=='inclusive':
        setup_pythia_inclusive(P8gen)

    # Charm decays only (with secondary production from tau)
    # ======================================================

    if process_selection=='c':

        selection = data['selections']['c']
        for cmd in selection['parameters']:
            P8gen.SetParameters(cmd)
        add_hnl(P8gen, mass, decay_couplings)

        # Add new charmed particles
        # -------------------------

        # Select all charmed particles (+ tau lepton)
        c_particles = selection['particles']
        tau_id = 15 # tau- Monte-Carlo ID
        add_particles(P8gen, c_particles + [tau_id], data)

        # Add HNL production channels from charmed particles
        # --------------------------------------------------

        # Find charm and tau decays to HNLs
        c_channels = [ch for ch in all_channels if ch['id'] in c_particles]
        tau_channels = [ch for ch in all_channels if ch['id'] == tau_id]
        # Standard model process: tau+ production from D_s+ decay
        ds_id = 431 # D_s+ Monte-Carlo ID
        ds_tau_br = 0.0548 # SM branching ratio Br(D_s+ -> tau+ nu_tau) (source: PDG 2018)

        # Compute the branching ratio scaling factor, taking into account
        # secondary production from tau
        # Decay chains are encoded as follows:
        #     [(top level id A, [br A -> B, br B -> C, ...]), ...]

        # Most charm particles directly decay to HNLs
        primary_decays = [(ch['id'], [get_br(histograms, ch, mass, production_couplings)])
                          for ch in c_channels]
        # The D_s+ can indirectly produce a HNL by first producing a tau+
        secondary_decays = [(ds_id, [ds_tau_br, get_br(histograms, ch, mass, production_couplings)])
                            for ch in tau_channels]
        all_decays = primary_decays + secondary_decays

        # Compute maximum total branching ratio (to rescale all BRs)
        max_total_br = compute_max_total_br(all_decays)
        exit_if_zero_br(max_total_br, process_selection, mass)
        print_scale_factor(1/max_total_br)

        # Add charm decays
        for ch in c_channels:
            add_channel(P8gen, ch, histograms, mass, production_couplings, 1/max_total_br)
        # Add tau production from D_s+
        # We can freely rescale Br(Ds -> tau) and Br(tau -> N X...) as long as
        # Br(Ds -> tau -> N X...) remains the same.
        # Here, we set Br(tau -> N) to unity to make event generation more efficient.
        # The implicit assumption here is that we will disregard the tau during the analysis.
        total_tau_br = sum(branching_ratios[1] for (_, branching_ratios) in secondary_decays)
        assert(ds_tau_br*total_tau_br <= max_total_br + 1e-12)
        P8gen.SetParameters("431:addChannel      1  {:.12}    0      -15       16"\
                            .format(ds_tau_br*total_tau_br/max_total_br))
        # Add secondary HNL production from tau
        for ch in tau_channels:
            # Rescale branching ratios only if some are non-zero. Otherwise leave them at zero.
            add_tau_channel(P8gen, ch, histograms, mass, production_couplings, 1/(total_tau_br or 1))

        # Add dummy channels in place of SM processes
        fill_missing_channels(P8gen, max_total_br, all_decays)

        # List channels to confirm that Pythia has been properly set up
        P8gen.List(9900015)

    # B/Bc decays only
    # ================

    if process_selection in ['b', 'bc']:

        selection = data['selections'][process_selection]
        for cmd in selection['parameters']:
            P8gen.SetParameters(cmd)
        add_hnl(P8gen, mass, decay_couplings)

        # Add particles
        particles = selection['particles']
        add_particles(P8gen, particles, data)

        # Find all decay channels
        channels = [ch for ch in all_channels if ch['id'] in particles]
        decays = [(ch['id'], [get_br(histograms, ch, mass, production_couplings)]) for ch in channels]

        # Compute scaling factor
        max_total_br = compute_max_total_br(decays)
        exit_if_zero_br(max_total_br, process_selection, mass)
        print_scale_factor(1/max_total_br)

        # Add beauty decays
        for ch in channels:
            add_channel(P8gen, ch, histograms, mass, production_couplings, 1/max_total_br)

        # Add dummy channels in place of SM processes
        fill_missing_channels(P8gen, max_total_br, decays)

        P8gen.List(9900015)

    if debug: pythia_log.close()

def add_hnl(P8gen, mass, decay_couplings):
    "Adds the HNL to Pythia and ROOT"
    hnl_instance = hnl.HNL(mass, decay_couplings, debug=True)
    ctau = hnl_instance.computeNLifetime(system="FairShip") * u.c_light * u.cm
    print("HNL ctau {}".format(ctau))
    P8gen.SetParameters("9900015:new = N2 N2 2 0 0 {:.12} 0.0 0.0 0.0 {:.12}  0   1   0   1   0".format(mass, ctau/u.mm))
    P8gen.SetParameters("9900015:isResonance = false")
    # Configuring decay modes...
    readDecayTable.addHNLdecayChannels(P8gen, hnl_instance, conffile=os.path.expandvars('$FAIRSHIP/python/DecaySelection.conf'), verbose=False)
    # Finish HNL setup...
    P8gen.SetParameters("9900015:mayDecay = on")
    P8gen.SetHNLId(9900015)
    # also add to PDG
    gamma = u.hbarc / float(ctau) #197.3269631e-16 / float(ctau) # hbar*c = 197 MeV*fm = 197e-16 GeV*cm
    addHNLtoROOT(pid=9900015,m=mass,g=gamma)

def setup_pythia_inclusive(P8gen):
    P8gen.SetParameters("SoftQCD:inelastic = on")
    P8gen.SetParameters("PhotonCollision:gmgm2mumu = on")
    P8gen.SetParameters("PromptPhoton:all = on")
    P8gen.SetParameters("WeakBosonExchange:all = on")
