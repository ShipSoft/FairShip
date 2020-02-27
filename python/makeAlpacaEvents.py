import os,sys,getopt
import numpy,math
import ROOT

hGeV = 6.58211928*pow(10.,-16)* pow(10.,-9) # no units or it messes up!!
c_light = 2.99792458e+10
mres="1.0d0"
gax="1d-7"
nev="100"

def AlpacaFormatting(s):
    s=str(s)
    if s.find('d')==-1:
        s = numpy.format_float_scientific(float(s))
        s= s.replace('e','d')
    return s

#determine the path for online usage it can be /eos/../ship/data/.. BUT don't know what we shall do in local usage??
 
def Ctau(mres,gax):
    return c_light*hGeV*64.*math.pi/((float(gax)*float(gax))*(float(mres)*float(mres)*float(mres)))

def Decaylength(e,p,ctau):
    beta=p/e
    gamma=e/math.sqrt(e*e-p*p)
    return beta*gamma*ctau

def Decayweight(Lmin,Lmax,Decaylength,z_dau):
    return math.exp(-z_dau/Decaylength)*((Lmax-Lmin)/Decaylength)

def inputWrite(mres,gax,nev,Lmin,Lmax):#need to apply Rmin & Rmax as well..
    mres    = AlpacaFormatting(mres)
    gax     = AlpacaFormatting(gax)
    Lmin    = AlpacaFormatting(Lmin)
    Lmax    = AlpacaFormatting(Lmax)
    f=open("input.DAT","w")
    f.write("****************************************************************************************\n")
    f.write("***********  RE-RUN ./init IF FIRST FIVE PARAMETERS ARE CHANGED:  **********************\n")
    f.write("****************************************************************************************\n")
    f.write("*************************  Experimental parameters *************************************\n")
    f.write("****************************************************************************************\n")
    f.write("400d0        ! [ebeam] : Beam kinetic energy (GeV)\n")
    f.write("'prot'       ! [btype] : Beam type ('prot' = proton, 'elec' = electron)\n")
    f.write("95.95d0      ! [aa] : Target mass number\n")
    f.write("42d0         ! [az] : Target atomic number\n")
    f.write("%s       ! [lsh] : Shielding length (m)\n"%(Lmin))
    f.write("%s       ! [dvol] : Decay volume (m)\n"%(Lmax))
    f.write("0.15d0       ! [rmin] : Inner radius (m)\n")
    f.write("2.5d0        ! [rmax] : Outer radius (m)\n")
    f.write("0.1d0        ! [dmin] : Minimum photon separation (m)\n")
    f.write("1d0          ! [emin] : Minimum photon energy (GeV)\n")
    f.write("1d-2         ! [athetamax] : Maximum ALP theta (when adecay is false)\n")
    f.write("****************************************************************************************\n")
    f.write("********************************** ALP parameters **************************************\n")
    f.write("****************************************************************************************\n")
    f.write("%s           ! [mres] : ALP mass (GeV)\n"%(mres))
    f.write("%s           ! [gax] : ALP photon coupling (GeV^-1)\n"%(gax))
    f.write("****************************************************************************************\n")
    f.write("******************************  Output parameters **************************************\n")
    f.write("****************************************************************************************\n")
    f.write("'test'       !  [outtag] : For output file\n")
    f.write("****************************************************************************************\n")
    f.write("************************* Integration parameters ***************************************\n")
    f.write("****************************************************************************************\n")
    f.write("100000       ! [ncall] : Number of calls for preconditioning\n")
    f.write("10           ! [itmx] : Number of iterations for preconditioning\n")
    f.write("1d0          ! [prec] :  Relative accuracy (in %) in main run\n")
    f.write("100000       ! [ncall1] : Number of calls in first iteration\n")
    f.write("100000       ! [inccall] : Number of increase calls per iteration\n")
    f.write("50           ! [itend] : Maximum number of iterations\n")
    f.write("6            ! [iseed] : Random number seed (integer > 0)\n")
    f.write("****************************************************************************************\n")
    f.write("******************************* Unweighted events **************************************\n")
    f.write("****************************************************************************************\n")
    f.write(".true.       ! [genunw] : Generate unweighted events\n")
    f.write("%s           ! [nev] : Number of events ( < 1000000 recommended)\n"%(nev))
    f.write("'hepevt'     ! [erec] : Event record format ('lhe' = Les Houches, 'hepevt' = HEPEVT)\n")
    f.write("****************************************************************************************\n")
    f.write("*******************************  Cuts   ************************************************\n")
    f.write(".true.       ! [gencuts] : Generate cuts - [rmin], [rmax], [dmin], [emin]\n")
    f.write(".true.       ! [adecay] : Include ALP decay\n")
    f.write("****************************************************************************************\n")
    f.write("****************************************************************************************\n")
    f.write("****************************************************************************************\n")
    f.close()

def ntupleWrite(ctau,fn,Lmin,Lmax,startZ,endZ,SmearBeam):
    Lmin        = float(Lmin)
    Lmax        = float(Lmax)
    startZ      = float(startZ)
    endZ        = float(endZ)
    SmearBeam   = float(SmearBeam)
    fn=fn.readlines()
    inputFile="alp_m"+str(mres)+"_g"+str(gax)+".root"
    f=ROOT.TFile(inputFile,"recreate")
    ntup=ROOT.TNtuple("MCTrack","Track Informations","event:track:pdg:px:py:pz:x:y:z:parent:decay:e:tof:w")
    for i,j in enumerate(range(5,len(fn),9)):
        zinter = ROOT.gRandom.Uniform(startZ,endZ)
        dx, dy = ROOT.gRandom.Uniform(-1,+1)*SmearBeam, ROOT.gRandom.Uniform(-1,+1)*SmearBeam
        tr=fn[j].split()
        dau1=fn[j+1].split()
        dau2=fn[j+2].split()
        p = math.sqrt(float(tr[7])**2.+float(tr[8])**2.+float(tr[9])**2.)
        #print float(tr[10]),p
        dl=Decaylength(float(tr[10]),p,ctau)
        print SmearBeam,zinter,dx,dy
        w = Decayweight(Lmin*100.,Lmax*100.,dl,float(dau1[14])/10.+zinter)
        print dl,w
        ntup.Fill(int(i),int(0),int(9900015),float(tr[7]),float(tr[8]),float(tr[9]),float(tr[12])+dx,float(tr[13])/10.+dy,float(tr[14])/10.+zinter,int(-1),float(0),float(tr[10]),float(0),w)
        ntup.Fill(int(i),int(1),int(dau1[1]),float(dau1[7]),float(dau1[8]),float(dau1[9]),float(dau1[12])/10.+dx,float(dau1[13])/10.+dy,float(dau1[14])/10.+zinter,int(0),float(1),float(dau1[10]),float(dau1[15])/10./c_light,w)
        ntup.Fill(int(i),int(2),int(dau2[1]),float(dau2[7]),float(dau2[8]),float(dau2[9]),float(dau2[12])/10.+dx,float(dau2[13])/10.+dy,float(dau2[14])/10.+zinter,int(0),float(1),float(dau2[10]),float(dau2[15])/10./c_light,w)
    ntup.Write()
    f.Close()
    return inputFile

def runEvents(mres,gax,nev,Lmin,Lmax,startZ,endZ,SmearBeam):
    pid=9900015
    m = mres
    g= gax
    pdg = ROOT.TDatabasePDG.Instance()
    pdg.AddParticle('a','ALP', m, False, g, 0., 'a', pid)
    wdir = os.environ['ALPACABIN']
    #wdir="/home/atakan/ShipSoft/sw/ubuntu1804_x86-64/alpaca/v1.1-2/bin"
    os.chdir(wdir)
    inputWrite(mres,gax,nev,Lmin,Lmax)
    rn="./alpaca < input.DAT"
    os.system(rn)
    fn=open("./evrecs/evrectest.dat","r")
    ctau=Ctau(mres,gax)
    print ctau
    inputFile = ntupleWrite(ctau,fn,Lmin,Lmax,startZ,endZ,SmearBeam)
    return wdir+"/"+inputFile
#runEvents()
