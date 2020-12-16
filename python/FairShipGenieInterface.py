from __future__ import print_function
from __future__ import division
import ROOT,os,sys,time

def Get1DFluxName(nupdg):
    '''returns name of TH1D p spectrum as stored in input files:
       example: nue: 12 -> 1012, anue: -12 -> 2012 
    '''
    x = ROOT.TMath.Abs(nupdg)
    if (nupdg > 0):
       return "10"+str(x)
    else:
       return "20"+str(x)

def Get2DFluxName(nupdg):
    '''returns name of TH2D p-pt flux as stored in input files:
       ie for nue: 12 -> 1212, anue: -12 -> 2212 
       nupdg: neutrino pdg
    '''
    x = ROOT.TMath.Abs(nupdg)
    if (nupdg > 0):
       return "12"+str(x)
    else:
       return "22"+str(x)

def makeSplines(nupdglist,targetcode, emax, outputfile):
    '''prepare splines with neutrino interaction cross sections
    nupdg = list of input neutrino pdgs
    targetcode = string with target material in GENIE code
    outputfile = path of outputfile
    '''
    inputnupdg = ""
    for nupdg in nupdglist:
      if (ipdg > 0):
        inputnupdg = inputnupdg + ","
      inputnupdg = inputnupdg + str(nupdg)
    print('Starting GENIE with the following command: ')
    cmd = "gmkspl -p "+inputnupdg+" -t "+targetcode+" -n 100 -e "+str(emax)+" -o "+outputfile
    os.system(cmd) 

def GenerateGenieEvents(nevents, nupdg, emin, emax, targetcode, inputflux , spline, process = None):
    '''make Genie simulation, parameters:
    events = number of events to generate
    nupdg = neutrino pdg
    targetcode = string with target material in GENIE code
    emin, emax = min and max neutrino energy to generate
    process = simulate a specific neutrino process (CCDIS, CCQE, CC, NC, CCRES, NCRES, etc.), otherwise all processes included
    inputflux = input neutrino flux
    spline = input neutrino spline
    '''
    #prepare command functions
    cmd = "gevgen -n "+str(nevents)+" -p "+ nupdg +" -t "+targetcode+" -e "+str(emin)+","+str(emax)
    cmd = cmd + " -f "+inputflux+","+pDict1[nupdg]+"  --cross-sections "+ spline 
    if (process):
        cmd = cmd + " --event-generator-list "+process #add a specific process
    print('Starting GENIE with the following command: ')
    print(cmd)
    os.system(cmd)

def makeNtuples(inputfile, outputfile):
    '''convert gntp GENIE file to gst general ROOT file
       inputfile = path of gntp inputfile (gntp.0.ghep.root)
       outputfile = path of gst outputfile
    '''

    cmd = "gntpc -i "inputfile" -f gst -o "+outfile
     print('Starting GENIE conversion with the following command: ')
    os.system(cmd)

def addHists(inputflux, simfile, nupdg):
    '''add histogram with p-pt flux to simulation file
       inputflux = path of neutrino inputflux
       simfile = path of simulation file to UPDATE
       nupdg = neutrino pdg
    '''
    inputfile = ROOT.TFile(inputflux,'read')
    simfile = ROOT.TFile(simfile,'update')
    #adding 2D histogram
    inputfile.Get(Get2DFluxName(nupdg)).Write()
    #closinsg files
    inputfile.Close()
    simfile.Close()
    