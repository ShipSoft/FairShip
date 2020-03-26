import os,sys,getopt
import numpy,math
import ROOT

hGeV = 6.58211928*pow(10.,-16)* pow(10.,-9) # no units or it messes up!!
c_light = 2.99792458e+10
mres="1.0d0"
gax="1d-7"
nev="100"

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

def inputWrite(mres,gax,nev,Lmin,Lmax):#need to apply Rmin & Rmax as well..
    Mres    = ALPACAFormatting(mres)
    Gax     = ALPACAFormatting(gax)
    L   = ALPACAFormatting(float(Lmax)-float(Lmin))
    Lmin    = ALPACAFormatting(Lmin)
    Lmax    = ALPACAFormatting(Lmax)
    with open("input.DAT","w") as f:
        f.write("****************************************************************************************\n")
        f.write("***********  RE-RUN ./init IF FIRST FIVE PARAMETERS ARE CHANGED:  **********************\n")
        f.write("****************************************************************************************\n")
        f.write("*************************  Experimental parameters *************************************\n")
        f.write("****************************************************************************************\n")
        f.write("4d2          ! [ebeam] : Beam kinetic energy (GeV)\n")
        f.write("'prot'       ! [btype] : Beam type ('prot' = proton, 'elec' = electron)\n")
        f.write("95.95d0      ! [aa] : Target mass number\n")
        f.write("42d0         ! [az] : Target atomic number\n")
        f.write("%s       ! [lsh] : Shielding length (m)\n"%(Lmin))
        f.write("%s       ! [dvol] : Decay volume (m)\n"%(L))
        f.write("1.5d-1       ! [rmin] : Inner radius (m)\n")
        f.write("2.5d0        ! [rmax] : Outer radius (m)\n")
        f.write("0.1d0        ! [dmin] : Minimum photon separation (m)\n")
        f.write("1d0          ! [emin] : Minimum photon energy (GeV)\n")
        f.write("1d-2         ! [athetamax] : Maximum ALP theta (when adecay is false)\n")
        f.write("****************************************************************************************\n")
        f.write("********************************** ALP parameters **************************************\n")
        f.write("****************************************************************************************\n")
        f.write("%s           ! [mres] : ALP mass (GeV)\n"%(Mres))
        f.write("%s           ! [gax] : ALP photon coupling (GeV^-1)\n"%(Gax))
        f.write("****************************************************************************************\n")
        f.write("******************************  Output parameters **************************************\n")
        f.write("****************************************************************************************\n")
        f.write("'_%s_%s'       !  [outtag] : For output file\n"%(mres,gax))
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

def ntupleWrite(ctau,fn,Lmin,Lmax,startZ,endZ,SmearBeam,mres,gax,old):
    Lmin        = float(Lmin)
    Lmax        = float(Lmax)
    startZ      = float(startZ)
    endZ        = float(endZ)
    SmearBeam   = float(SmearBeam)
    wdir = os.environ['ALPACABIN']
    with open(wdir+"/outputs/output_"+str(mres)+"_"+str(gax)+".dat","r") as fp:
        for line in fp:
            if "Cross section" in line:
                line=line.split()
                xs=line[3]+"_"+line[5]
    fn=fn.readlines()
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
    return inputFile

def runEvents(mres,gax,nev,Lmin,Lmax,startZ,endZ,SmearBeam):
    print('ALPACA is starting for mass of {} GeV with photon coupling coeffiecient {} GeV^-1.'.format(mres,gax))
    pdg = ROOT.TDatabasePDG.Instance()
    pdg.AddParticle('a','ALP', mres, False, gax, 0., 'a', 9900015)
    wdir = os.environ['ALPACABIN']
    old=os.getcwd()
    os.chdir(wdir)
    inputWrite(mres,gax,nev,Lmin,Lmax)
    rn="./alpaca < input.DAT"
    os.system(rn)
    print('ALPACA generated the events.')
    pa="./evrecs/evrec_"+str(mres)+"_"+str(gax)+".dat"
    fn=open(pa,"r")
    ctau=Ctau(mres,gax)
    print('Events are recording into a ntuple.')
    inputFile = ntupleWrite(ctau,fn,Lmin,Lmax,startZ,endZ,SmearBeam,mres,gax,old)
    os.chdir(old)
    print('Ntuple is ready for the reading.')
    return inputFile
#runEvents()
