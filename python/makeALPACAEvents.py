#!/usr/bin/env python
from __future__ import print_function
from __future__ import division
import os,sys,getopt
import numpy,math
import ROOT
import shipunit as u

#natural units were used!
hGeV      = u.hbar_Planck/u.s
c_light   = u.c_light*u.s/u.cm

naming     = "_"+str(mres)+"_"+str(gax)

def ALPACAFormatting(s):
    s=str(s)
    if s.find('d')==-1:
        s = numpy.format_float_scientific(float(s))
        s= s.replace('e','d')
        s= s.replace('+','')
    return s
 
def Ctau(mres,gax):
    return c_light*hGeV*65.*math.pi/((float(gax)*float(gax))*(float(mres)*float(mres)*float(mres)))

def Decaylength(e,p,ctau):
    beta=p/e
    gamma=e/math.sqrt(e*e-p*p)
    return beta*gamma*ctau

def Decayweight(Lmin,Lmax,Decaylength,LS):
    return math.exp(-LS/Decaylength)*((Lmax-Lmin)/Decaylength)

def addALPtoPDG(mres,gax):
    pdg = ROOT.TDatabasePDG.Instance()
    pdg.AddParticle('a','ALP', mres, False, gax, 0., 'a', 9900015)

def inputWrite(mres,gax,nev,Lmin,Lmax):#need to apply Rmin & Rmax as well..
    Mres    = ALPACAFormatting(mres)
    Gax     = ALPACAFormatting(gax)
    L   = ALPACAFormatting(float(Lmax)-float(Lmin))
    Lmin    = ALPACAFormatting(Lmin)
    Lmax    = ALPACAFormatting(Lmax)
    with open("input"+naming+".DAT","w") as f:
        f.write("****************************************************************************************")
        f.write("***********  RE-RUN ./init IF FIRST FIVE PARAMETERS ARE CHANGED:  **********************")
        f.write("****************************************************************************************")
        f.write("*************************  Experimental parameters *************************************")
        f.write("****************************************************************************************")
        f.write("4d2          ! [ebeam] : Beam kinetic energy (GeV)")
        f.write("'prot'       ! [btype] : Beam type ('prot' = proton, 'elec' = electron)")
        f.write("95.95d0      ! [aa] : Target mass number")
        f.write("42d0         ! [az] : Target atomic number")
        f.write("%s       ! [lsh] : Shielding length (m)"%(Lmin))
        f.write("%s       ! [dvol] : Decay volume (m)"%(L))
        f.write("1.5d-1       ! [rmin] : Inner radius (m)")
        f.write("2.5d0        ! [rmax] : Outer radius (m)")
        f.write("0.1d0        ! [dmin] : Minimum photon separation (m)")
        f.write("1d0          ! [emin] : Minimum photon energy (GeV)")
        f.write("1d-2         ! [athetamax] : Maximum ALP theta (when adecay is false)")
        f.write("****************************************************************************************")
        f.write("********************************** ALP parameters **************************************")
        f.write("****************************************************************************************")
        f.write("%s           ! [mres] : ALP mass (GeV)"%(Mres))
        f.write("%s           ! [gax] : ALP photon coupling (GeV^-1)"%(Gax))
        f.write("****************************************************************************************")
        f.write("******************************  Output parameters **************************************")
        f.write("****************************************************************************************")
        f.write("'_%s_%s'       !  [outtag] : For output file"%(mres,gax))
        f.write("****************************************************************************************")
        f.write("************************* Integration parameters ***************************************")
        f.write("****************************************************************************************")
        f.write("100000       ! [ncall] : Number of calls for preconditioning")
        f.write("10           ! [itmx] : Number of iterations for preconditioning")
        f.write("1d0          ! [prec] :  Relative accuracy (in %) in main run")
        f.write("100000       ! [ncall1] : Number of calls in first iteration")
        f.write("100000       ! [inccall] : Number of increase calls per iteration")
        f.write("50           ! [itend] : Maximum number of iterations")
        f.write("6            ! [iseed] : Random number seed (integer > 0)")
        f.write("****************************************************************************************")
        f.write("******************************* Unweighted events **************************************")
        f.write("****************************************************************************************")
        f.write(".true.       ! [genunw] : Generate unweighted events")
        f.write("%s           ! [nev] : Number of events ( < 1000000 recommended)"%(nev))
        f.write("'hepevt'     ! [erec] : Event record format ('lhe' = Les Houches, 'hepevt' = HEPEVT)")
        f.write("****************************************************************************************")
        f.write("*******************************  Cuts   ************************************************")
        f.write(".true.       ! [gencuts] : Generate cuts - [rmin], [rmax], [dmin], [emin]")
        f.write(".true.       ! [adecay] : Include ALP decay")
        f.write("****************************************************************************************")
        f.write("****************************************************************************************")
        f.write("****************************************************************************************")

def getXS(wdir,mres,gax):
    with open(wdir+"/outputs/output"+naming+".dat","r") as fp:
        for line in fp:
            if "Cross section" in line:
                line=line.split()
                return line[3]

def ntupleWrite(ctau,fn,Lmin,Lmax,startZ,endZ,SmearBeam,mres,gax,old):
    Lmin        = float(Lmin)
    Lmax        = float(Lmax)
    startZ      = float(startZ)
    endZ        = float(endZ)
    SmearBeam   = float(SmearBeam)
    wdir = os.environ['ALPACABIN']
    fn=fn.readlines()
    xs=getXS(wdir,mres,gax)
    inputFile=old+"/"+"alp_m"+str(mres)+"_g"+str(gax)+"_xs"+str(xs)+".root"
    f=ROOT.TFile(inputFile,"recreate")
    ntup=ROOT.TNtuple("MCTrack","Track Informations","event:track:pdg:px:py:pz:x:y:z:parent:decay:e:tof:w")
    for i,j in enumerate(range(5,len(fn),9)):
        LS = ROOT.gRandom.Uniform(Lmin*100.,Lmax*100.)
        zinter = ROOT.gRandom.Uniform(startZ,endZ)
        dx, dy = ROOT.gRandom.Uniform(-1,+1)*SmearBeam, ROOT.gRandom.Uniform(-1,+1)*SmearBeam
        tr=fn[j].split()
        dau1=fn[j+1].split()
        dau2=fn[j+2].split()
        px,py,pz=float(tr[7]),float(tr[8]),float(tr[9])
        p = math.sqrt(px**2.+py**2.+pz**2.)
        lam = LS/p
        daux,dauy,dauz= dx+lam*px,dy+lam*py,zinter+lam*pz
        dl=Decaylength(float(tr[10]),p,ctau)
        w = Decayweight(Lmin*100.,Lmax*100.,dl,LS)
        ntup.Fill(int(i),int(0),int(9900015),px,py,pz,dx,dy,zinter,int(-1),float(0),float(tr[10]),float(0),w)
        #ntup.Fill(int(i),int(1),int(dau1[1]),float(dau1[7]),float(dau1[8]),float(dau1[9]),float(dau1[12])/10.+dx,float(dau1[13])/10.+dy,float(dau1[14])/10.+zinter,int(0),float(1),float(dau1[10]),float(dau1[15])/10./c_light,w)
        #ntup.Fill(int(i),int(2),int(dau2[1]),float(dau2[7]),float(dau2[8]),float(dau2[9]),float(dau2[12])/10.+dx,float(dau2[13])/10.+dy,float(dau2[14])/10.+zinter,int(0),float(1),float(dau2[10]),float(dau2[15])/10./c_light,w)
        ntup.Fill(int(i),int(1),int(dau1[1]),float(dau1[7]),float(dau1[8]),float(dau1[9]),daux,dauy,dauz,int(0),float(1),float(dau1[10]),float(dau1[15])/10./c_light,w)
        ntup.Fill(int(i),int(2),int(dau2[1]),float(dau2[7]),float(dau2[8]),float(dau2[9]),daux,dauy,dauz,int(0),float(1),float(dau2[10]),float(dau2[15])/10./c_light,w)
    ntup.Write()
    f.Close()
    print("ALP -> Gamma + Gamma events are produced with cross-section of {} pb at mass of {} GeV and photon coupling of {} GeV^-1".format(xs,mres,gax))
    return inputFile

def runEvents(mres,gax,nev,Lmin,Lmax,startZ,endZ,SmearBeam):
    mres = float(mres)
    gax  = float(gax)
    print('ALPACA is starting for mass of {} GeV with photon coupling coeffiecient {} GeV^-1.'.format(mres,gax))
    addALPtoPDG(float(mres),float(gax))
    wdir = os.environ['ALPACABIN']
    old=os.getcwd()
    os.chdir(wdir)
    inputWrite(mres,gax,nev,Lmin,Lmax)
    rn="./alpaca < "+"input"+naming+".DAT"
    os.system(rn)
    print('ALPACA generated the events.')
    pa="./evrecs/evrec"+naming+".dat"
    fn=open(pa,"r")
    ctau=Ctau(mres,gax)
    print('Events are recording into a ntuple.')
    inputFile = ntupleWrite(ctau,fn,Lmin,Lmax,startZ,endZ,SmearBeam,mres,gax,old)
    os.chdir(old)
    os.remove(wdir+"/input"+naming+".DAT")
    os.remove(wdir+"/evrecs/evrec"+naming+".dat")
    os.remove(wdir+"/outputs/output"+naming+".dat")
    print('Ntuple is ready for the reading.')
    return inputFile
 
def main():
    from argparse import ArgumentParser
    mres      = 1.0e-1
    gax       = 1.0e-5
    nev       = 100
    Lmin      = 4.7505e0
    Lmax      = 9.826511e0
    startZ    = -7228.5000
    endZ      = -7084.0000
    SmearBeam = 1.0
    print("ALPACA is running standalone")
    parser = ArgumentParser()
    parser.add_argument("-m", "--mres", dest="mres",  help="to set mass in GeV for ALP", required=False, default=None, type=float)
    parser.add_argument("-g", "--gax", dest="gax",  help="to set photon coupling coefficient", required=False,default=None, type=float)
    parser.add_argument("-Ls", "--Lmin", dest="Lmin",  help="to set starting length(m) of Decay Volume", required=False,default=None, type=float)
    parser.add_argument("-Le", "--Lmax", dest="Lmax",  help="to set ending length(m) of Decay Volume", required=False,default=None, type=float)
    parser.add_argument("-sZ", "--startZ", dest="startZ",  help="to set starting coordinate(cm) of Target", required=False,default=None, type=float)
    parser.add_argument("-eZ", "--endZ", dest="endZ",  help="to set ending coordinate(cm) of Target", required=False,default=None, type=float)
    parser.add_argument("-n", "--nev",dest="nev",  help="Number of events to generate", required=False,  default=None, type=int)
    options = parser.parse_args()
    if options.mres: 
        mres=options.mres
        print("mas is set to {} GeV".format(mres))
    else: print("default mass is {} GeV".format(mres))
    if options.gax:
        gax=options.gax
        print("photon coupling is set to {} GeV^-1".format(gax))
    else: print("default photon coupling is {} GeV^-1".format(gax))
    if options.Lmin:
        Lmin=options.Lmin 
        print("Lmin is set to {} m".format(Lmin))
    else: print("default Lmin is {} m".format(Lmin))
    if options.Lmax:
        Lmax=options.Lmax 
        print("Lmax is set to {} m".format(Lmax))
    else: print("default Lmax is {} m".format(Lmax))
    if options.startZ:
        startZ=options.startZ 
        print("startZ is set to {} cm".format(startZ))
    else: print("default startZ is {} cm".format(startZ)r_Planck/u.s)
    if options.endZ:
        endZ=options.endZ
        print("endZ is set to {} cm".format(endZ))
    else: print("default endZ is {} cm".format(endZ))
    if options.nev:
        nev=options.nev  
        print("nEvents is set to {}".format(nev))
    else: print("default nEvents is {}".format(nev))
    runEvents(mres,gax,nev,Lmin,Lmax,startZ,endZ,SmearBeam)   
 
if __name__='__main__':
    main()
