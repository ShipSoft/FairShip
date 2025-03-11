import ROOT, os, sys, time
from subprocess import call


def get_1D_flux_name(nupdg):
    """returns name of TH1D p spectrum as stored in input files:
    example: nue: 12 -> 1012, anue: -12 -> 2012
    """
    x = ROOT.TMath.Abs(nupdg)
    if nupdg > 0:
        return "10" + str(x)
    else:
        return "20" + str(x)


def get_2D_flux_name(nupdg):
    """returns name of TH2D p-pt flux as stored in input files:
    ie for nue: 12 -> 1212, anue: -12 -> 2212
    nupdg: neutrino pdg
    """
    x = ROOT.TMath.Abs(nupdg)
    if nupdg > 0:
        return "12" + str(x)
    else:
        return "22" + str(x)


def make_splines(nupdglist, targetcode, emax, nknots, outputfile):
    """prepare splines with neutrino interaction cross sections
    nupdg = list of input neutrino pdgs
    targetcode = string with target material in GENIE code
    outputfile = path of outputfile
    """
    inputnupdg = ""
    for ipdg, nupdg in enumerate(nupdglist):
        if ipdg > 0:
            inputnupdg = inputnupdg + ","
        inputnupdg = inputnupdg + str(nupdg)
    cmd = (
        "gmkspl -p "
        + inputnupdg
        + " -t "
        + targetcode
        + " -n "
        + str(nknots)
        + " -e "
        + str(emax)
        + " -o "
        + outputfile
    )
    print("Starting GENIE with the following command: ")
    print(cmd)
    call(cmd, shell=True)


def generate_genie_events(
    nevents,
    nupdg,
    emin,
    emax,
    targetcode,
    inputflux,
    spline,
    process=None,
    seed=None,
    irun=None,
):
    """make Genie simulation, parameters:
    events = number of events to generate
    nupdg = neutrino pdg
    targetcode = string with target material in GENIE code
    emin, emax = min and max neutrino energy to generate
    process = simulate a specific neutrino process (CCDIS, CCQE, CC, NC, CCRES, NCRES, etc.),
              if not set, GENIE's comprehensive collection of event generators will be used.
    inputflux = input neutrino flux
    spline = input neutrino spline
    """
    # prepare command functions
    cmd = (
        "gevgen -n "
        + str(nevents)
        + " -p "
        + str(nupdg)
        + " -t "
        + targetcode
        + " -e "
        + str(emin)
        + ","
        + str(emax)
    )
    cmd = (
        cmd
        + " -f "
        + inputflux
        + ","
        + get_1D_flux_name(nupdg)
        + "  --cross-sections "
        + spline
    )
    # optional additional arguments
    if process is not None:
        cmd = cmd + " --event-generator-list " + process  # add a specific process
    if seed is not None:
        cmd = cmd + " --seed " + str(seed)  # set a seed for the generator
    if irun is not None:
        cmd = cmd + " --run " + str(irun)

    print("Starting GENIE with the following command: ")
    print(cmd)
    call(cmd, shell=True)


def make_ntuples(inputfile, outputfile):
    """convert gntp GENIE file to gst general ROOT file
    inputfile = path of gntp inputfile (gntp.0.ghep.root)
    outputfile = path of gst outputfile
    """

    cmd = "gntpc -i " + inputfile + " -f gst -o " + outputfile
    print("Starting GENIE conversion with the following command: ")
    print(cmd)
    call(cmd, shell=True)


def add_hists(inputflux, simfile, nupdg):
    """add histogram with p-pt flux to simulation file
    inputflux = path of neutrino inputflux
    simfile = path of simulation file to UPDATE
    nupdg = neutrino pdg
    """
    inputfile = ROOT.TFile(inputflux, "read")
    simfile = ROOT.TFile(simfile, "update")
    # adding 2D histogram
    inputfile.Get(get_2D_flux_name(nupdg)).Write()
    # closinsg files
    inputfile.Close()
    simfile.Close()
