import os,subprocess,ROOT,time,multiprocessing,socket
ncpus = multiprocessing.cpu_count() - 2
interactive = not socket.gethostname().find('ubuntu')<0

pathToMacro = '' # $SHIPBUILD/FairShip/charmdet/

commandToHist = {"anaResiduals":"histos-analysis-","momResolution":"histos-momentumResolution-","plotDTPoints":"histos-DTPoints-",
                     "hitmaps":"histos-HitmapsFromFittedTracks-","alignment":"histos-residuals-","MCJpsiProd":"histos-Jpsi"}
commandToSum  = {"anaResiduals":"momDistributions-","momResolution":"momentumResolution-","plotDTPoints":"DTPoints-","alignment":"residuals-",
                     "hitmaps":"HitmapsFromFittedTracks-","MCJpsiProd":"JpsiKinematics"}

def count_python_processes(macroName):
# only works if screen is wide enough to print full name!
    status = subprocess.check_output('ps -f -u truf',shell=True)
    n=0
    for x in status.split('\n'):
        if not x.find(macroName)<0 and not x.find('python') <0: n+=1
    return n

fileList = {}
badFiles = []
eospath='/eos/experiment/ship/data/Mbias/background-prod-2018/'

def JpsiProdP8(run):
    for n in range(run,run+15):
      os.system("python $FAIRSHIP/macro/JpsiProdWithPythia8.py -n 100000000 -r "+str(n)+" &")
def mergeJpsiProdP8():
    cmd = 'hadd Jpsi-Pythia8_XXXX_0-74.root'
    N=0
    for n in range(75):
        fname = "Jpsi-Pythia8_100000000_"+str(n)+".root"
        if not os.path.isfile(fname): continue
        f = ROOT.TFile(fname)
        if not f: continue
        if not f.Get('pythia6'): continue
        N+=100000000
        cmd += " "+fname
    cmd=cmd.replace('XXXX',str(N))
    os.system(cmd)

def JpsiProdP8_withHTCondor(run=10000,njobs=1000,NPot=1000000,merge=False):
# microcentury = 1h ok with 1000000 NPot, 45min
# workday      = 8h whould be ok with 5000000
    eosLocation = os.environ['EOSSHIP']+"/eos/experiment/ship/user/truf/muflux-sim/JpsiProduction_P8/"
    temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l /eos/experiment/ship/user/truf/muflux-sim/JpsiProduction_P8",shell=True)
    cmd = "hadd Jpsi-Pythia8_XXXX_"+str(run)+"-"+str(run+njobs)+".root"
    Ntot = 0
    for n in range(run,run+njobs):
       output = "Jpsi-Pythia8_"+str(NPot)+"_"+str(n)+".root"
       if not merge:
    # create condor sub
          fc = open('condorJ.sub','w')
          fc.write('executable  = JpsiProd.sh\n')
          fc.write('arguments   = '+str(NPot)+' '+str(n)+' '+output+' '+eosLocation+output +' \n')
          fc.write('should_transfer_files = YES\n')
          fc.write('when_to_transfer_output = ON_EXIT\n')
          x = 'run_'+str(n)
          fc.write('output                = output/'+x+'.out\n')
          fc.write('error                 = error/'+x+'.err\n')
          fc.write('log                   = log/'+x+'.log\n')
          fc.write('+JobFlavour = "workday"\n')  #"microcentury" workday
          fc.write('queue\n')
          fc.close()
          os.system('condor_submit condorJ.sub')
       else:
          eosfile = (eosLocation+output)
          if output in temp:
             f=ROOT.TFile.Open(eosfile)
             if f.Get('pythia6'):
               cmd += " "+eosfile
               Ntot+=NPot
    if merge:
         cmd = cmd.replace('XXXX',str(Ntot))
         tmp = cmd.split(' ')
         outfile = tmp[1]
         cmd = 'hadd -f '+outfile
         N=0
         for n in range(2,len(tmp)):
            N+=1
            cmd += ' ' + tmp[n]
            if N>500:
              os.system(cmd)
              os.system('cp '+outfile+' tmp.root')
              cmd = "hadd -f "+outfile+' tmp.root '
              N=0
         os.system(cmd)

def run_FixedTarget(start):
    N = 10000
    for n in range(start,start+ncpus):
        cmd = "python $FAIRSHIP/muonShieldOptimization/run_MufluxfixedTarget.py -n "+str(N)+" -e 1 -P -o run-"+str(n)+" &"
        os.system(cmd)
        while 1>0:
            if count_python_processes('run_MufluxfixedTarget')<ncpus: break
            time.sleep(100)
    print "finished all the tasks."
def mergeFiles():
    N = 0
    cmd = 'hadd -f pythia8_Geant4_1000_1.0-XXX.root '
    for d in os.listdir('.'):
        if d.find('run')<0:continue
        if os.path.isdir(d):
            fname = d+'/pythia8_Geant4_1000_1.0.root'
            if  not os.path.isfile(fname): continue
            f = ROOT.TFile(fname)
            if f.Get('cbmsim'):
                cmd += fname+' '
                N+=1
    os.system(cmd.replace('XXX',str(N)))

def submit2Condor(eospath,directory,filename):
    sub = filename.replace('root','sub')
    f = open(sub,'w')
    f.write("executable            = /afs/cern.ch/user/t/trufship/muflux/runDriftTubeScript.sh\n")
    f.write("arguments             = "+command+" "+eospath+directory+"/"+filename+"\n")
    f.write("output                = "+filename.replace('root','out')+"\n")
    f.write("error                 = "+filename.replace('root','error')+"\n")
    f.write("log                   = "+filename.replace('root','log')+"\n")
    f.write("queue\n")
    f.close()
    os.system("condor_submit "+sub)

def getFilesFromEOS(E="10.0_withCharmandBeauty"):   # E="1.0"
# list of files
    temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospath,shell=True)
    for x in temp.split('\n'):
        if x.find(E)<0 or x.find('_mu')<0: continue # includes charm
        fname =  x[x.find('/eos'):]
        nentries = 0
        f=ROOT.TFile.Open(os.environ['EOSSHIP']+fname)
        nentries=f.cbmsim.GetEntries()
        fileList[fname]=nentries
    return fileList

def getFilesLocal(d='.'):
# list of files
    fl = []
    temp = os.listdir(d)
    for x in temp:
        if os.path.isdir(d+'/'+x): fl.append(x)
    return fl


def getFilesEOS(D):
    eospathSim = '/eos/experiment/ship/user/truf/muflux-sim/'+D
    temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim,shell=True)
    fl = []
    for x in temp.split('\n'):
        if x.find('pythia8_Geant4')<0: continue
        d = x[x.rfind('/')+1:]
        fl.append(eospathSim+'/'+d)
    return fl

def simulationStep(fnames=[],E="10.0_withCharmandBeauty",overwrite=False,Gfield=''):
    if len(fnames)==0: fnames = getFilesFromEOS(E)
    Nfiles = len(fnames)
    print "fileList established ",Nfiles
    for fname in fnames:
        N = fnames[fname]-1
        odir = fname[fname.rfind('/')+1:].replace('.root','')
        if not overwrite and odir in os.listdir('.'): continue
        cmd = "python $FAIRSHIP/macro/run_simScript.py -n "+str(N)+" --MuonBack --charm=1 --CharmdetSetup=0 --fieldMap="+Gfield+" --output "+odir+" -f "+fname+" &"
        print 'step 1:', cmd
        os.system(cmd)
        while 1>0:
            if count_python_processes('run_simScript')<ncpus: break
            time.sleep(100)
    print "finished all the tasks."
def digiStep(fnames=[]):
    mcFile = 'ship.conical.MuonBack-TGeant4.root'
    geoFile = 'geofile_full.conical.MuonBack-TGeant4.root'
    if len(fnames)==0: fnames = getFilesLocal()
    Nfiles = len(fnames)
    print "fileList established ",Nfiles
    for fname in fnames:
        if not mcFile in os.listdir(fname):continue
        os.chdir(fname)
        cmd = "python $FAIRSHIP/macro/runMufluxDigi.py -n 9999999 -f "+mcFile+" -g "+geoFile+" &"
        print 'step 2:', fname,cmd
        os.system(cmd)
        os.chdir('../')
        while 1>0:
            if count_python_processes('runMufluxDigi')<ncpus: break 
            time.sleep(100)
    print "finished all the tasks."

def findDirWithSim():
    fnames = getFilesLocal()
    stats = {'simOnly':[],'tmp':[],'failed':[],'digi':[],'digireco':{}}
    for fname in fnames:
        geo  = False
        digi = False
        tmp  = False
        digiSplit = 0
        reco = 0
        for x in os.listdir(fname):
            if not x.find('geofile_full.conical.MuonBack-TGeant4')<0: geo = True
            if not x.find('roottmp')<0: tmp  = True
            if not x.find('dig.root')<0:       digi    = True
            if not x.find('dig_RT')<0:         reco+=1
            if not x.find('dig-')<0:         digiSplit+=1
        if tmp: stats['tmp'].append(fname)
        elif digi: stats['digi'].append(fname)
        elif geo: 
            if reco==0 and digiSplit==0: stats['simOnly'].append(fname)
        else : stats['failed'].append(fname)
        stats['digireco'][fname]=[digiSplit,reco]
    for x in stats['tmp']:
        f = ROOT.TFile(x+'/ship.conical.MuonBack-TGeant4.roottmp')
        try: 
            if f.cbmsim.GetEntries()>0: 
                print 'tmp file ok, replace root file',x
                os.system('mv '+x+'/ship.conical.MuonBack-TGeant4.roottmp '+x+'/ship.conical.MuonBack-TGeant4.root')
        except:
            print 'tmp file not ok',x
    return stats

def splitDigiFiles(splitFactor=10,fnames=[],eosdir='10GeV'):
    eospath = os.environ["EOSSHIP"]+"/eos/experiment/ship/user/truf/muflux-sim/"+eosdir
    if len(fnames)==0: fnames = getFilesLocal()
    Nfiles = len(fnames)
    print "fileList established ",Nfiles
    for fname in fnames:
        os.chdir(fname)
        ofile = 'ship.conical.MuonBack-TGeant4_dig.root'
        origin = ROOT.TFile.Open(eospath+"/"+fname+"/"+ofile)
        if not origin:
            print "File not found",fname
            os.chdir('../')
            continue
        if not origin.GetKey('cbmsim'):
            print "corrupted file",fname
            os.chdir('../')
            continue
        sTree = origin.cbmsim
        N = 0
        deltaN = int(sTree.GetEntries()/float(splitFactor))
        for i in range(splitFactor):
            nf = ofile.replace('.root','-'+str(i)+'.root')
            if nf in os.listdir('.'): 
                print "file exists",fname,nf
            else:
                print "creating ",fname,nf
                newFile = ROOT.TFile(nf,'RECREATE')
                newTree = sTree.CloneTree(0)
                for n in range(N,N+deltaN):
                    rc = sTree.GetEntry(n)
                    rc = newTree.Fill()
                newFile.Write()
            N+=deltaN
        os.chdir('../')

def recoStep(splitFactor=5,fnames=[],eospath=False,Gfield=''):
    addOption = ""
    if Gfield == 'inter': addOption = " -F inter "
    eospathSim = '/eos/experiment/ship/user/truf/muflux-sim/'
    if len(fnames)==0: fnames = getFilesLocal()
    Nfiles = len(fnames)
    print "fileList established #directories",Nfiles
    for fname in fnames:
        os.chdir(fname)
        mcFile = 'ship.conical.MuonBack-TGeant4_dig_RT.root'
        ofile = 'ship.conical.MuonBack-TGeant4_dig.root'
        for i in range(splitFactor):
            recoFile = mcFile.replace('.root','-'+str(i)+'.root')
            if recoFile in os.listdir('.'):
                test = ROOT.TFile(recoFile)
                sTree = test.Get('cbmsim')
                if sTree:
                    if sTree.GetBranch("FitTracks"): continue
                test.Close()
            digiFile = ofile.replace('.root','-'+str(i)+'.root')
            if digiFile in os.listdir('.'): 
                os.system('cp '+ofile.replace('.root','-'+str(i)+'.root')+' '+recoFile)
            elif not recoFile in os.listdir('.'):
                if eospath:
                    print "copy from EOS",recoFile
                    os.system('xrdcp  $EOSSHIP'+eospathSim+'/'+eospath+'/'+fname+'/'+digiFile+ ' '+recoFile)
                else:
                    print "digiFile missing",fname,digiFile
                    continue
            cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c recoStep1 --Display False -u 1 -f "+recoFile+addOption+' &'
            print 'step 2:', cmd,' in directory ',fname
            os.system(cmd)
            while 1>0:
                if count_python_processes('drifttubeMonitoring')<ncpus: break 
                time.sleep(100)
        os.chdir('../')
    print "finished all the tasks."

def checkFilesWithTracks(D='.',splitFactor=5,dimuon=False):
    eos = ''
    if D=='.': fnames = getFilesLocal()
    elif D.find('1GeV')==0 or D.find('10GeV')==0: 
        fnames = getFilesEOS(D)
        eos = os.environ['EOSSHIP']
    fileList=[]
    fileListPer={}
    failedList = []
    for fname in fnames:
        fileListPer[fname]={}
        mcFile = 'ship.conical.MuonBack-TGeant4_dig_RT.root'
        for i in range(splitFactor):
            recoFile = fname+'/'+mcFile.replace('.root','-'+str(i)+'.root')
            if dimuon: recoFile = recoFile.replace('.root','_dimuon99.root')
            if D=='.': dirList = os.listdir(fname)
            else: dirList = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+fname,shell=True)
            if recoFile.replace(fname+'/','') in dirList:
                test = ROOT.TFile.Open(eos+recoFile)
                if not test: continue
                sTree = test.Get('cbmsim')
                if sTree:
                    if sTree.GetBranch("FitTracks"): 
                        fileList.append(recoFile)
                        size = sTree.GetBranch('FitTracks').GetTotalSize()/float(sTree.GetEntries())
                        fileListPer[fname][recoFile.replace(D+'.'+fname+'/','')]=size
                        # print "check",fname,recoFile,size
                else:
                    failedList.append(fname+'/'+recoFile)
    fileList.sort()
    return fileList,fileListPer,failedList

def cleanUp():
    reco,x,y = checkFilesWithTracks()
    for f in reco:
        df = f.replace('_RT','')
        if os.path.isfile(df): os.system('rm ' +df)

def makeHistos(D='.',splitFactor=5,command="anaResiduals",fnames=[],Gfield=''):
    addOption = ""
    if Gfield == 'inter': addOption = " -F inter "
    if D=='.':
        fileList,x,y = checkFilesWithTracks(D,splitFactor)
        print "fileList established ",len(fileList)
        for df in fileList:
            tmp = df.split('/')
            if len(tmp)>1: os.chdir(tmp[0])
            if not commandToHist[command]+tmp[1] in os.listdir('.'):
                cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c "+command+" -f "+tmp[1]+addOption+' --Display False  &'
                print 'execute:', cmd
                os.system(cmd)
            if len(tmp)>1: os.chdir('../')
            while 1>0:
                if count_python_processes('drifttubeMonitoring')<ncpus: break 
                time.sleep(100)
    elif D.find('1GeV')==0 or D.find('10GeV')==0:
        eospathSim = '/eos/experiment/ship/user/truf/muflux-sim/'+D
        temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim,shell=True)
        for x in temp.split('\n'):
            if x.find('pythia8_Geant4')<0: continue
            d = x[x.rfind('/')+1:]
            if not d in os.listdir('.'): os.system('mkdir '+d)
            os.chdir(d)
            temp2 = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim+'/'+d,shell=True)
            fileList = []
            for y in temp2.split('\n'):
                f = os.environ['EOSSHIP'] + y[y.find('/eos'):]
                if not f[f.rfind('/')+1:].find('ship')==0: continue
                if  f.find('RT_mu')<0: continue
                histFile = commandToHist[command]+y[y.rfind('/')+1:]
                if histFile in os.listdir('.') : continue
                if interactive:
                    cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -d False -c "+command+" -f "+f+addOption+' >'+histFile.replace('histo','log')+' --Display False  &'
                    print 'execute:', cmd
                    os.system(cmd)
                    while 1>0:
                        if count_python_processes('drifttubeMonitoring')<ncpus: break 
                        time.sleep(100)
                else: submit2Condor(eospathSim,d,y[y.rfind('/')+1:])
            os.chdir('../')
    else:
        eospathSim10GeV = '/eos/experiment/ship/data/muflux/MC/19feb2019'
        fileList = []
        temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim10GeV,shell=True)
        for x in temp.split('\n'):
            if x.find('RT.root')<0: continue
            fileList.append( os.environ['EOSSHIP'] + x[x.find('/eos'):])
        for fname in fileList:
            if os.path.isfile(commandToHist[command]+fname[fname.rfind('/')+1:]): continue
            cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -d False -c "+command+" -f "+fname+addOption+' &'
            print 'command:', cmd
            os.system(cmd)
            while 1>0:
                if count_python_processes('drifttubeMonitoring')<ncpus: break 
                time.sleep(10)
    print "finished all the tasks."
def makeHistosWithHTCondor(D='10GeV-repro',splitFactor=10,command="anaResiduals",fnames=[]):
    eospathSim = '/eos/experiment/ship/user/truf/muflux-sim/'+D
    temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+eospathSim,shell=True)
    for d in temp.split('\n'):
      if d.find('pythia8_Geant4')<0: continue
      temp2 = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+d,shell=True)
      fileList = []
      for fname in temp2.split('\n'):
              if not fname[fname.rfind('/')+1:].find('ship')==0: continue
              if  fname.find('RT-')<0: continue
              hfile = commandToHist[command]+fname[fname.rfind('/')+1:]
              nfile = 'ntuple-'+fname[fname.rfind('/')+1:]
              if command == "alignment": nfile = "histos-HitmapsFromFittedTracks-"+fname[fname.rfind('/')+1:]
              if os.path.isfile(eospathSim+'/'+d+'/'+hfile): continue
    # create condor sub
              fc = open('condorX.sub','w')
              fc.write('executable            = batchScript.sh\n')
              fc.write('arguments             = '+fname+' '+command+' '+hfile+' '+os.environ['EOSSHIP']+eospathSim+'/'+d+'/'+hfile+' '+nfile+' '+os.environ['EOSSHIP']+eospathSim+'/'+d+'/'+nfile+' \n')
              fc.write('should_transfer_files = YES\n')
              fc.write('when_to_transfer_output = ON_EXIT\n')
              x = fname[fname.rfind('/')+1:]
              fc.write('output                = output/'+x+'.out\n')
              fc.write('error                 = error/'+x+'.err\n')
              fc.write('log                   = log/'+x+'.log\n')
              fc.write('+JobFlavour = "microcentury"\n')
              fc.write('queue\n')
              fc.close()
              os.system('condor_submit condorX.sub')
              time.sleep(0.1)
def HTCondorStats(D='10GeV-repro',command="anaResiduals",fnames=[]):
    eospathSim = '/eos/experiment/ship/user/truf/muflux-sim/'+D
    stats = {}
    if len(fnames)==0:
            temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+eospathSim,shell=True)
            fnames = temp.split('\n')
    for x in fnames:
            if x.find("pythia8")<0: continue
            run = x[x.rfind('/')+1:]
            eospathSimR = eospathSim+'/'+run
            stats[run]={'recoFiles':[],'histoFiles':[]}
            temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+eospathSimR,shell=True)
            for z in temp.split('\n'):
              if z.find('.root')<0: continue
              stats[run]['recoFiles'].append( os.environ['EOSSHIP'] + z[z.find('/eos'):])
    # all RT files with tracks
            temp2 = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+eospathSimR,shell=True)
            for fname in stats[run]['recoFiles']:
              if not fname.find('sys')<0: continue
              hfile = commandToHist[command]+fname[fname.rfind('/')+1:]
              if not temp2.find(hfile)<0:
                   stats[run]['histoFiles'].append(hfile)
    total = [0,0]
    for x in stats:
      print x,len(stats[x]['recoFiles']),len(stats[x]['histoFiles']),'missing:',len(stats[x]['recoFiles'])-len(stats[x]['histoFiles'])
      total[0]+=len(stats[x]['recoFiles'])
      total[1]+=len(stats[x]['histoFiles'])
    print "summary total reco",total[0],' histos',total[1],' missing',total[0]-total[1]
    return stats
def makeMomResolutions(D='.',splitFactor=5):
    if D=='.':
        fileList,x,y = checkFilesWithTracks(D,splitFactor)
        print "fileList established ",len(fileList)
        for df in fileList:
            tmp = df.split('/')
            if len(tmp)>1: os.chdir(tmp[0])
            if not "histos-momentumResolution-"+tmp[1] in os.listdir('.'):
                cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c momResolution -f "+tmp[1]+' &'
                print 'execute:', cmd
                os.system(cmd)
            if len(tmp)>1: os.chdir('../')
            while 1>0:
                if count_python_processes('drifttubeMonitoring')<ncpus: break 
                time.sleep(100)
    elif D.find('1GeV')==0 or D.find('10GeV')==0:
        eospathSim = '/eos/experiment/ship/user/truf/muflux-sim/'+D
        temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim,shell=True)
        for x in temp.split('\n'):
            if x.find('pythia8_Geant4')<0: continue
            d = x[x.rfind('/')+1:]
            if not d in os.listdir('.'): os.system('mkdir '+d)
            os.chdir(d)
            temp2 = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim+'/'+d,shell=True)
            fileList = []
            for y in temp2.split('\n'):
                f = os.environ['EOSSHIP'] + y[y.find('/eos'):]
                if not f.find('histos')<0: continue
                if  f.find('RT')<0: continue
                histFile = 'histos-momentumResolution-'+y[y.rfind('/')+1:]
                if histFile in os.listdir('.') : continue
                cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py --c momResolution -f "+f+' &'
                print 'execute:', cmd
                os.system(cmd)
                while 1>0:
                    if count_python_processes('drifttubeMonitoring')<ncpus: break 
                    time.sleep(100)
            os.chdir('../')
    print "finished all the tasks."


def checkAlignment(D='.',splitFactor=5):
    if D=='.':
        fileList,x,y = checkFilesWithTracks(D,splitFactor)
        print "fileList established ",len(fileList)
        for df in fileList:
            tmp = df.split('/')
            if len(tmp)>1: os.chdir(tmp[0])
            if not "histos-residuals-"+tmp[1] in os.listdir('.'):
                cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c alignment -f "+tmp[1]+' &'
                print 'execute:', cmd
                os.system(cmd)
            if len(tmp)>1: os.chdir('../')
            while 1>0:
                if count_python_processes('drifttubeMonitoring')<ncpus: break 
                time.sleep(100)
    elif D.find('1GeV')==0 or D.find('10GeV')==0:
        eospathSim = '/eos/experiment/ship/user/truf/muflux-sim/'+D
        temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim,shell=True)
        for x in temp.split('\n'):
            if x.find('pythia8_Geant4')<0: continue
            d = x[x.rfind('/')+1:]
            if not d in os.listdir('.'): os.system('mkdir '+d)
            os.chdir(d)
            temp2 = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim+'/'+d,shell=True)
            fileList = []
            for y in temp2.split('\n'):
                f = os.environ['EOSSHIP'] + y[y.find('/eos'):]
                test = f[f.rfind('/')+1:]
                if not test.find('ship.')==0: continue
                if  f.find('RT')<0: continue
                histFile = 'histos-residuals-'+y[y.rfind('/')+1:]
                if histFile in os.listdir('.') : continue
                cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c alignment -f "+f+' &'
                print 'execute:', cmd
                os.system(cmd)
                while 1>0:
                    if count_python_processes('drifttubeMonitoring')<ncpus: break 
                    time.sleep(100)
            os.chdir('../')
    print "finished all the tasks."


def exportToEos(fnames=[],destination="/eos/experiment/ship/user/truf/muflux-sim/1GeV",update=True,tag=None):
    remote = []
    for r in subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+destination,shell=True).split('\n'):
           if r.find('eos')<0: continue
           remote.append('pythia'+r.split('pythia')[1])
    fnames = getFilesLocal()
    for D in fnames:
        if not D in remote:
            os.system("xrdfs "+os.environ['EOSSHIP']+" mkdir  "+destination+"/"+D)
        remoteD = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+destination+'/'+D,shell=True)
        for f in os.listdir(D):
            if tag:
              if f.find(tag)<0:continue
            if f in remoteD and not update: continue
            fname = D+'/'+f
            cmd = "xrdcp -f "+fname+" $EOSSHIP/"+destination+"/"+fname
            print cmd
            os.system(cmd)
def importFromEos(source="/eos/experiment/ship/user/truf/muflux-sim/1GeV",tag="ship.conical.MuonBack-TGeant4.root",update=True):
    remote = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+source,shell=True).split('\n')
    for x in remote:
      if x.find('eos')<0:continue
      fname = x.split(source)[1]
      files = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+source+fname,shell=True).split('\n')
      for y in files:
       if y.find('eos')<0:continue
       afile = '/eos'+y.split('/eos')[1]
       if afile.find(tag)<0:continue
       destination = afile.split(source)[1]
       cmd = "xrdcp "
       if update: cmd += " -f "
       cmd += " $EOSSHIP/"+afile+" "+destination[1:]
       print cmd
       os.system(cmd)

def exportNtupleToEos(d="simulation10GeV-withDeadChannels",key='ntuple',update=True):
    eospath = "/eos/experiment/ship/user/truf/muflux-sim/"
    destination = eospath+d.replace('simulation','').split('-final')[0]
    for D in os.listdir(d):
        if os.path.isdir(d+'/'+D):
            for f in os.listdir(d+'/'+D):
                if f.find(key)==0:
                    cmd = "xrdcp  "+d+'/'+D+'/'+f+ " $EOSSHIP/"+destination+"/"+D+'/'+f
                    if update : cmd = "xrdcp -f "+d+'/'+D+'/'+f+ " $EOSSHIP/"+destination+"/"+D+'/'+f
                    print cmd
                    os.system(cmd)

def mergeHistos(command="anaResiduals"):
    dirList=getFilesLocal()
    cmd = {}
    for z in ['charm','mbias']:
        cmd[z] = 'hadd -f '+commandToSum[command]+z+'.root '
    for d in dirList:
        for x in os.listdir(d):
            z='mbias'
            if d.find('charm')>0: z='charm'
            if (not x.find(commandToHist[command])<0 ):  cmd[z] += d+'/'+x+" "
    for z in ['charm','mbias']:
        os.system(cmd[z])

def mergeNtuple():
    dirList=getFilesLocal()
    cmd = {}
    for z in ['charm','mbias']:
        cmd[z] = 'hadd -f ntuple-'+z+'.root '
    for d in dirList:
        for x in os.listdir(d):
            z='mbias'
            if d.find('charm')>0: z='charm'
            if (not x.find('ntuple')<0 ):  cmd[z] += d+'/'+x+" "
    for z in ['charm','mbias']:
        os.system(cmd[z])

import rootUtils as ut
def checkHistos():
    dirList=getFilesLocal()
    Ntot = 0
    shit = []
    for d in dirList:
        nfailed = 0
        for x in os.listdir(d):
            if not x.find('histos-analysis-')<0:
                h={}
                ut.readHists(h,d+'/'+x,['p/pt'])
                N = h['p/pt'].GetEntries()
                if N == 0: nfailed+=1
                print d+'/'+x,N
                Ntot+=N
        print nfailed
        if nfailed == 10: shit.append(d)
    print Ntot
    return shit



def checkForFilesWithTracks():
    eospathSim10GeV = '/eos/experiment/ship/data/muflux/MC/19feb2019'
    fileList = []
    trList = []
    temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim10GeV,shell=True)
    for x in temp.split('\n'):
        if x.find('RT.root')<0: continue
        fname = os.environ['EOSSHIP'] + x[x.find('/eos'):]
        fileList.append( fname )
        test = ROOT.TFile.Open(fname)
        if test.GetKey('cbmsim'): 
            if test.cbmsim.GetBranch('FitTracks'): trList.append(fname)
    print len(fileList),len(trList)

def mergeHistos10(case='residuals'):
    N = 1
    n = 0
    for x in os.listdir('.'):
        if n==0:
            if case == 'residuals':  cmd = 'hadd -f residuals-'+str(N)+'.root '
            elif case == 'momResolution':  cmd = 'hadd -f momentumResolution-'+str(N)+'.root '
            else:                    cmd = 'hadd -f momDistributions-'+str(N)+'.root '
        if (case == 'residuals' and not x.find('histos-residuals')<0 ):  cmd += x+" "
        elif (case == 'momResolution' and not x.find('momentumResolution')<0 ):  cmd += x+" "
        elif (case == 'momDistribution' and not x.find('analysis')<0 ):  cmd += x+" "
        n+=1
        if n==500:
            os.system(cmd)
            n=0
            N+=1
    if case == 'residuals':        histname = 'residuals.root '
    elif case == 'momResolution':  histname = 'momentumResolution.root '
    else:                          histname = 'momDistributions.root '
    cmd = 'hadd -f '+histname
    for n in range(1,N+1):
        cmd += histname.replace('.','-'+str(N)+'.')
    os.system(cmd)
def removeBranches(fname,branches=['RPCTrackX','RPCTrackY']):
 f=ROOT.TFile(fname,'update')
 sTree=f.cbmsim
 for br in branches:
            b = sTree.GetBranch(br)
            sTree.GetListOfBranches().Remove(b)
            l = sTree.GetLeaf(br)
            sTree.GetListOfLeaves().Remove(l)
 sTree.Write()
 f.Close()
def redoMuonTracks(D='.',copyToEos=False):
  if D=='.':
    fileList,x,y = checkFilesWithTracks(D='.')
    for df in fileList:
        tmp = df.split('/')
        if len(tmp)>1: 
            os.chdir(tmp[0])
            cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c  recoMuonTaggerTracks -u 1 -f "+tmp[1]+' &'
            print 'execute:', cmd
            os.system(cmd)
            os.chdir('../')
        while 1>0:
            if count_python_processes('drifttubeMonitoring')<ncpus: break 
            time.sleep(100)
    print "finished all the tasks."
  elif D.find('1GeV-repro')==0 or D.find('10GeV-repro')==0:
        eospathSim = '/eos/experiment/ship/user/truf/muflux-sim/'+D
        temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim,shell=True)
        for x in temp.split('\n'):
            if x.find('pythia8_Geant4')<0: continue
            d = x[x.rfind('/')+1:]
            if not d in os.listdir('.'): os.system('mkdir '+d)
            if not d in ['pythia8_Geant4_10.0_withCharmandBeauty9000_mu','pythia8_Geant4_10.0_withCharmandBeauty8000_mu',
                         'pythia8_Geant4_10.0_withCharmandBeauty7000_mu','pythia8_Geant4_10.0_withCharmandBeauty6000_mu',
                         'pythia8_Geant4_10.0_withCharmandBeauty60000_mu','pythia8_Geant4_10.0_withCharmandBeauty61000_mu',
                         'pythia8_Geant4_10.0_withCharmandBeauty62000_mu','pythia8_Geant4_10.0_withCharmandBeauty63000_mu',
                         'pythia8_Geant4_10.0_withCharmandBeauty64000_mu','pythia8_Geant4_10.0_withCharmandBeauty65000_mu',
                         'pythia8_Geant4_10.0_withCharmandBeauty66000_mu']: continue
            os.chdir(d)
            temp2 = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim+'/'+d,shell=True)
            fileList = []
            for y in temp2.split('\n'):
                f = os.environ['EOSSHIP'] + y[y.find('/eos'):]
                tmp = f.split('/')
                curFile = tmp[len(tmp)-1]
                if not curFile.find('ship.conical.MuonBack-TGeant4_dig_RT')==0: continue
                if curFile.find('ship.conical.MuonBack-TGeant4_dig_RT_mu')==0: continue
                newFile = curFile.replace("dig_RT","dig_RT_mu")
                if not copyToEos:
                  os.system('xrdcp '+f+' '+newFile)
                  removeBranches(newFile)
                  cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -u 1 -c  recoMuonTaggerTracks -d False -f "+newFile+' &'
                  print 'execute:', cmd
                  os.system(cmd)
                  while 1>0:
                    if count_python_processes('drifttubeMonitoring')<ncpus: break 
                    time.sleep(100)
                else:
                  if not os.path.isfile(newFile):
                     print "file missing ",os.path.abspath('.'),newFile
                  else:
                   f = ROOT.TFile(newFile)
                   if not f:
                     print "f corrupted ",os.path.abspath('.'),newFile
                   elif not f.Get('cbmsim'): print "f corrupted 2",os.path.abspath('.'),newFile
                   else:
                     os.system('xrdcp '+newFile+' $EOSSHIP/eos/experiment/ship/user/truf/muflux-sim/'+D+'/'+d+'/'+newFile)
            os.chdir('../')
  elif D.find('JpsiProduction')==0:
        eospathSim = '/eos/experiment/ship/user/truf/muflux-sim/'+D
        temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospathSim,shell=True)
        if not D in os.listdir('.'): os.system('mkdir '+D)
        os.chdir(D)
        for y in temp.split('\n'):
            f = os.environ['EOSSHIP'] + y[y.find('/eos'):]
            if f.find(D+'/pythia8_Geant4')<0: continue
            if f.find('dig_RT')<0: continue
            tmp = f.split('/')
            curFile = tmp[len(tmp)-1]
            if curFile.find('mu')>0: continue
            newFile = curFile.replace("dig_RT","dig_RT_mu")
            if not copyToEos:
               os.system('xrdcp '+f+' '+newFile)
               removeBranches(newFile)
               cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -u 1 -c  recoMuonTaggerTracks -d False -f "+newFile+' &'
               print 'execute:', cmd
               os.system(cmd)
               while 1>0:
                   if count_python_processes('drifttubeMonitoring')<ncpus: break 
                   time.sleep(100)
            else:
                  os.system('xrdcp '+newFile+' $EOSSHIP/eos/experiment/ship/user/truf/muflux-sim/'+D+'/'+newFile)
        os.chdir('../')
  print "finished all the tasks."

def splitOffBoostedEvents(splitFactor=5,check=False):
    remote = "/home/truf/ship-ubuntu-1710-32/muflux/simulation/"
    dirList=getFilesLocal(remote)
    for d in dirList:
        if not os.path.isdir(d): os.system('mkdir '+d)
        os.chdir(d)
        for f in os.listdir(remote+'/'+d):
            if f.find('histo')<0 and not f.find('ship.conical')<0:
                if not check:
                    os.system('cp '+remote+'/'+d+'/'+f+' .')
                    cmd = "python /home/truf/muflux/simulation/drifttubeMonitoring.py -c  splitOffBoostedEvents -f "+f+' &'
                    print 'execute:', cmd
                    os.system(cmd)
                    while 1>0:
                        if count_python_processes('drifttubeMonitoring')<ncpus: break 
                        time.sleep(100)
                else:
                    # check
                    f99 = f.replace('.root','_dimuon99.root')
                    f1 = f.replace('.root','_dimuon1.root')
                    l = os.listdir('.')
                    if not f in l or not f99 in l or f1 in l:
                        print 'something wrong',d,f
                        print f,f in l 
                        print f99,f99 in l 
                        print f1,f1 in l 
        os.chdir('../')

def runMufluxReco(D='1GeV',merge=False):
    N = 24
    ncpus = 8
    if merge:
        cmd = "hadd sumHistos--simulation10GeV-repro.root "
        for n in range(ncpus):
               cmd += "sumHistos--simulation10GeV-repro-"+str(n)+".root "
        os.system(cmd)
    else:
        t='repro'
        if D=='1GeV':
          cmd = "python $FAIRSHIP/charmdet/MufluxNtuple.py -t "+t+" -d simulation1GeV-"+t+"   -c MufluxReco  -A True &"
          os.system(cmd)
          cmd = "python $FAIRSHIP/charmdet/MufluxNtuple.py -t "+t+" -d simulation1GeV-"+t+"   -c MufluxReco  -C True &"
          os.system(cmd)
        elif D=='10GeV':
          for n in range(ncpus):
            cmd = "python $FAIRSHIP/charmdet/MufluxNtuple.py -t "+t+" -d simulation10GeV-"+t+"   -c MufluxReco  -B True -s "+str(n)+ " -x "+str(ncpus)+" &"
            os.system(cmd)
            while 1>0:
                if count_python_processes('MufluxNtuple')<ncpus: break
                time.sleep(20)
        elif D=='Jpsi':
          for n in range(ncpus):
            cmd = "python $FAIRSHIP/charmdet/MufluxNtuple.py -t "+t+" -d JpsiProduction  -c MufluxReco  -J True -s "+str(n)+ " -x "+str(ncpus)+" &"
            os.system(cmd)
            while 1>0:
                if count_python_processes('MufluxNtuple')<ncpus: break
                time.sleep(20)
        elif D=='JpsiP8':
          for n in range(ncpus):
            cmd = "python $FAIRSHIP/charmdet/MufluxNtuple.py -t "+t+" -d JpsiProduction  -c MufluxReco  -8 True -s "+str(n)+ " -x "+str(ncpus)+" &"
            os.system(cmd)
            while 1>0:
                if count_python_processes('MufluxNtuple')<ncpus: break
                time.sleep(20)

def runInvMass(MC='1GeV',merge=False):
    N = 20
    t='repro'
    if not merge:
      if MC=='Jpsi':
        for n in range(N):
          cmd = "python $FAIRSHIP/charmdet/MufluxNtuple.py -d JpsiProduction -t "+t+" -c invMass -p ship-ubuntu-1710-48 -s "+str(n)+ " -x "+str(N)+" -J True -r &"
          print cmd
          os.system(cmd)
          while 1>0:
            if count_python_processes('MufluxNtuple')<ncpus: break
            time.sleep(20)
      elif MC=='JpsiP8':
        for n in range(N):
          cmd = "python $FAIRSHIP/charmdet/MufluxNtuple.py -d JpsiProduction_P8 -t "+t+" -c invMass -p ship-ubuntu-1710-16 -s "+str(n)+ " -x "+str(N)+" -8 True -r &"
          print cmd
          os.system(cmd)
          while 1>0:
            if count_python_processes('MufluxNtuple')<ncpus: break
            time.sleep(20)
      elif MC=='1GeV':
         cmd = "python $FAIRSHIP/charmdet/MufluxNtuple.py -d simulation1GeV-"+t+" -t "+t+" -c invMass -p ship-ubuntu-1710-48 -A True -r &"
         print cmd
         os.system(cmd)
      elif MC=='10GeV':
        for n in range(N):
          cmd = "python $FAIRSHIP/charmdet/MufluxNtuple.py -d simulation10GeV-"+t+" -t "+t+" -c invMass -p ship-ubuntu-1710-48 -s "+str(n)+ " -x "+str(N)+" -B True -r &"
          print cmd
          os.system(cmd)
          while 1>0:
            if count_python_processes('MufluxNtuple')<ncpus: break
            time.sleep(20)
      else: 
        print "case not known, stop"
        1/0
    else:
        if MC=='Jpsi' or MC=='JpsiP8':
           cmd = 'hadd -f invMass-MC-Jpsi.root '
           for n in range(N):
               cmd+='invMass-MC-'+str(n)+'_refit.root '
           os.system(cmd)
           cmd = 'hadd -f ntuple-invMass-MC-Jpsi.root '
           for n in range(N):
              cmd+='ntuple-invMass-MC-'+str(n)+'_refit.root '
           os.system(cmd)
        else:
           x=''
           if t=='repro': x='_refit'
           cmd = 'hadd -f invMass-MC-'+MC+x+'.root '
           for n in range(N):
              cmd+='invMass-MC-'+str(n)+x+'.root '
           os.system(cmd)
           cmd = 'hadd -f ntuple-invMass-MC-'+MC+x+'.root '
           for n in range(N):
              cmd+='ntuple-invMass-MC-'+str(n)+x+'.root '
           os.system(cmd)
def checkStatistics(splitFactor=5):
    # 1GeV mbias 1.8 Billion PoT charm 10.2 Billion PoT 
    simFiles = getFilesFromEOS()  # input data
    reco,x,y = checkFilesWithTracks()  # 
    Nsim =  {'mbias':0,'charm':0}
    Nreco = {'mbias':0,'charm':0}
    for f in simFiles:
        if f.find('charm')>0: Nsim['charm']+=simFiles[f]
        else: Nsim['mbias'] += simFiles[f]
    allFiles = {}
    for a in simFiles.keys():
        x = a.split('/')
        allFiles[x[len(x)-1].replace('.root','')]=simFiles[a]
    for dname in allFiles:
        n = 0
        for x in reco:
            if  not x.find(dname)<0: n+=1
        fraction = n/float(splitFactor)
        print "fraction:",dname,fraction
        if dname.find('charm')>0: Nreco['charm']+=fraction*allFiles[dname]
        else: Nreco['mbias'] += fraction*allFiles[dname]
    print "total statistics, simulated     ",Nsim
    print "                , reconstructed ",Nreco
    # mbias statistics = 1.8 * Nreco/Nsim, charm statistics = 10.2 * Nreco/Nsim
    # norm factor = 1/charm statistics * mbias statistics
    print "internal MC normalization, to be applied to charm", 1.8*Nreco['mbias']/Nsim['mbias'] /(10.2*Nreco['charm']/Nsim['charm'])
def mergeOnurFiles(merge=False):
  if not merge:
    eospath = "/eos/experiment/ship/user/odurhan/Muflux-Digi"
    temp = subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+eospath,shell=True)
    fl = []
    for x in temp.split('\n'):
        if x.find('dig.root')<0: continue
        d   = x[x.rfind('/')+1:]
        fin = ROOT.TFile.Open(os.environ['EOSSHIP']+eospath+'/'+d)
        if not fin: continue
        t = fin.Get('cbmsim')
        if not t: continue
        if not t.FindBranch('FitTracks'): continue
        fout  = ROOT.TFile(d,'recreate')
        sTree = t.CloneTree(0)
        nEvents = 0
        pointContainers = []
        for b in sTree.GetListOfBranches():
           name = b.GetName() 
           if not name.find('Point')<0: pointContainers.append('sTree.'+name+'.GetEntries()') # makes use of convention that all sensitive detectors fill XXXPoint containers
        for n in range(t.GetEntries()):
           rc = t.GetEvent(n)
           empty = True 
           for p in pointContainers:
              if eval(p)>0: empty = False
           if not empty:
              rc = sTree.Fill()
              nEvents+=1
        sTree.AutoSave()
        fout.Close()
        print("removed empty events, left with:", nEvents)
        fin.SetWritable(False) # bpyass flush error
  else:
      N=0
      cmd = 'hadd -f ship.conical.FixedTarget-TGeant4_merged_dig.root '
      for x in os.listdir('.'):
        N+=1
        cmd += x+' '
        if N%500==0:
            os.system(cmd)
            os.system('cp ship.conical.FixedTarget-TGeant4_merged_dig.root  tmp.root')
            cmd = 'hadd -f ship.conical.FixedTarget-TGeant4_merged_dig.root tmp.root '
      os.system(cmd)
def JpsiProduction(step='simulation',prod='P8'):
 # directory should be ship-ubuntu-1710-48/JpsiProduction
 path = {} 
 path['Cascade']     ="ship-ubuntu-1710-48_run_MufluxfixedTarget_XXX/"
 path['P8']          ="ship-ubuntu-1710-16_run_MufluxfixedTarget_XXX/"
 ncpus = 16
 Ntot = {'Cascade':20313583,'P8':2293179}
 InFile = {'Cascade':"/eos/experiment/ship/data/jpsicascade/cascade_MSEL61_20M.root" ,
                'P8':"/eos/experiment/ship/user/truf/muflux-sim/JpsiProduction_P8/Jpsi-Pythia8_21788000000_0-3074.root"}
 Nstart = 0
 delN = int(float(Ntot[prod])/float(ncpus))
 if step == 'simulation':
  for n in range(ncpus):
    cmd = "python $SHIPBUILD/FairShip/muonShieldOptimization/run_MufluxfixedTarget.py -C -P -I "+ InFile[prod] +" -J -e 10. -n "+str(delN)+" -S  "+str(Nstart)+ " -r "+str(n)+" &"
    Nstart+=delN
    os.system(cmd)
 if step == 'digi':
  for n in range(ncpus):
     d = path[prod].replace('XXX',str(n))
     os.chdir(d)
     mcFile = 'pythia8_Geant4_'+str(n)+'_10.0.root'
     if mcFile.replace('.root','_dig.root') in os.listdir('.'):
        print "File already exists, skip",mcFile.replace('.root','_dig.root')
        os.chdir('../')
        continue
     geoFile = 'geofile_full.root'
     cmd = "python $FAIRSHIP/macro/runMufluxDigi.py -n 9999999 -f "+mcFile+" -g "+geoFile+" &"
     print 'step digi:', cmd,' in directory ',d
     os.system(cmd)
     os.chdir('../')
     while 1>0:
         if count_python_processes('runMufluxDigi')<ncpus/2: break 
         time.sleep(100)
 if step == 'reco':
  for n in range(ncpus):
     d = path[prod].replace('XXX',str(n))
     os.chdir(d)
     recoFile = 'pythia8_Geant4_'+str(n)+'_10.0_dig.root'
     cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -c recoStep1 -u 1 -f "+recoFile+' &'
     print 'step reco:', cmd,' in directory ',d
     os.system(cmd)
     os.chdir('../')
     while 1>0:
         if count_python_processes('drifttubeMonitoring')<ncpus/2: break 
         time.sleep(100)
 print "finished all the ",step," tasks"
def JpsiCopyToEOS(RT=False,prod='P8'):
 ncpus = range(16)
 dirName={}
 dirName['P8']     ="JpsiProduction_P8/"
 dirName['Cascade']="JpsiProduction/"
 eosPath = {}
 eosPath['P8']          =" $EOSSHIP/eos/experiment/ship/user/truf/muflux-sim/JpsiProduction_P8/"
 eosPath['Cascade']     =" $EOSSHIP/eos/experiment/ship/user/truf/muflux-sim/JpsiProduction/"
 for n in ncpus:
    fileName = "pythia8_Geant4_"+str(n)+"_10.0.root"
    if RT=='RT': fileName = fileName.replace('.root','_dig_RT_mu.root')
    if RT=='ntuple': fileName = 'ntuple-'+fileName.replace('.root','_dig_RT_mu.root')
    cmd = "xrdcp  "+dirName[prod].replace('XX',str(n))+fileName+eosPath[prod]+fileName
    print cmd
    rc = os.system(cmd)
    # if rc == 0: os.system('rm '+dirName+fileName)

def JpsiHistos(command = "anaResiduals",prod = 'P8',merge=False):
  # MCJpsiProd
  dirName={}
  dirName['P8']     ="JpsiProduction_P8/"
  dirName['Cascade']="JpsiProduction/"
  eosPath = {}
  eosPath['P8']          =" $EOSSHIP/eos/experiment/ship/user/truf/muflux-sim/JpsiProduction_P8/"
  eosPath['Cascade']     =" $EOSSHIP/eos/experiment/ship/user/truf/muflux-sim/JpsiProduction/"
  cmd = 'hadd -f '+commandToSum[command]+'.root '
  D=''
  D = eosPath[prod]
  for n in range(16):
    fileName = "pythia8_Geant4_"+str(n)+"_10.0_dig_RT_mu.root"
    if not merge:
       cmd = "python $FAIRSHIP/charmdet/drifttubeMonitoring.py -d False -c "+command+" -f "+D+fileName+' &'
       os.chdir(dirName[prod])
       print 'execute:', cmd
       os.system(cmd)
       os.chdir('../')
    else:
       cmd +=dirName[prod]+'/'+commandToHist[command]+fileName+' '
  if merge: os.system(cmd)
from array import array
def extractJpsi(prod = '10GeV'):
   Fntuple = 'JpsifromBackground-'+prod+'.root'
   ftup = ROOT.TFile.Open(Fntuple, 'RECREATE')
   Ntup = ROOT.TNtuple("pythia8","pythia8 Jpsi","id:px:py:pz:E:M:mid:mpx:mpy:mpz:mE:mM")
   template={}
   template['10GeV'] = ['/eos/experiment/ship/data/Mbias/background-prod-2018/pythia8_Geant4_10.0_cXXXX_mu.root',67]
   template['1GeV']  = ['/eos/experiment/ship/data/Mbias/background-prod-2018/pythia8_Geant4_1.0_cXXXX_mu.root',20]
   for n in range(0,template[prod][1]):
      fname = template[prod][0].replace('XXXX',str(n*1000))
      f=ROOT.TFile.Open(os.environ['EOSSHIP']+fname)
      print "opening ",fname,f.cbmsim.GetEntries()
      for event in f.cbmsim:
         jpsi = False
         for m in event.MCTrack:
            if m.GetPdgCode()==443:
              jpsi = True
              break
         if not jpsi: continue
         vl=array('f')
         vl.append(float(m.GetPdgCode()))
         vl.append(m.GetPx())
         vl.append(m.GetPy())
         vl.append(m.GetPz())
         vl.append(m.GetEnergy())
         vl.append(m.GetMass())
         vl.append(float(event.MCTrack[1].GetPdgCode()))
         vl.append(event.MCTrack[0].GetPx())
         vl.append(event.MCTrack[0].GetPy())
         vl.append(event.MCTrack[0].GetPz())
         vl.append(event.MCTrack[0].GetEnergy())
         if m.GetMotherId() < 0:
            vl.append(-1)
         else:
           vl.append(float(event.MCTrack[m.GetMotherId()].GetPdgCode()))
         rc = Ntup.Fill(vl)
   ftup.cd()
   Ntup.Write()
   ftup.Close()
