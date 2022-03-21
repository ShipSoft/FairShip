import os,subprocess,time,multiprocessing
import pwd
import ROOT
ncpus = multiprocessing.cpu_count()


# use cases: H6, TI18
from argparse import ArgumentParser
parser = ArgumentParser()

parser.add_argument("-r", "--runNumbers", dest="runNumbers", help="list of run numbers",required=False, type=str,default="")
parser.add_argument("-P", "--production", dest="prod",       help="H6 / epfl / TI18"   ,required=False,default="TI18")
parser.add_argument("-c", "--command", dest="command",       help="command", default=None)
parser.add_argument("-o", "--overwrite", dest="overwrite",   action='store_true', help="overwrite EOS", default=False)
parser.add_argument("-cpp", "--convRawCPP", action='store_true', dest="FairTask_convRaw", help="convert raw data using ConvRawData FairTask", default=True)

global options
options = parser.parse_args()
runList = []

Mext = ''  
if options.FairTask_convRaw: 
   Mext = '_CPP'  

def count_python_processes(macroName):
    username = pwd.getpwuid(os.getuid()).pw_name
    callstring = "ps -f -u " + username
# only works if screen is wide enough to print full name!
    status = subprocess.check_output(callstring,shell=True)
    n=0
    for x in status.decode().split('\n'):
        if not x.find(macroName)<0 and not x.find('python') <0: n+=1
    return n

def getPartitions(runList,path):
 partitions = {}
 for r in runList:
   directory = path+"run_"+str(r).zfill(6)
   dirlist  = str( subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+directory,shell=True) )
   partitions[r] = []
   for x in dirlist.split('\\n'):
        ix = x.find('data_')
        if ix<0: continue
        partitions[r].append( int(x[ix+5:ix+9]) )
 return partitions

def convert(runList,path,partitions={}):
 if len(partitions)==0: partitions = getPartitions(runList,path)
 for r in partitions:
    runNr   = str(r).zfill(6)
    # find partitions
    for p in partitions[r]:
       os.system("python runProd.py -c  'runSinglePartition;"+path+";"+runNr+";"+str(p).zfill(4)+";EOScopy=True;check=True;'   &")
       time.sleep(10)
       while count_python_processes('convertRawData')>ncpus:
          time.sleep(200)
 return partitions         

def runSinglePartition(path,r,p,EOScopy=False,check=True):
     inFile = os.environ['EOSSHIP']+path+'run_'+ r+'/data_'+p+'.root'
     fI = ROOT.TFile.Open(inFile)
     if not fI:
        print('file not found',path,r,p)
        exit()
     if not fI.Get('event'):
        print('file corrupted',path,r,p)
        exit()
     if options.FairTask_convRaw:
        os.system("python $SNDSW_ROOT/shipLHC/rawData/convertRawData.py -cpp -b 100000 -p "+path+"  -r "+str(int(r))+ " -P "+str(int(p)) + "  >log_"+r+'-'+p)
     else: 
        os.system("python $SNDSW_ROOT/shipLHC/rawData/convertRawData.py -b 100000 -p "+path+"  -r "+str(int(r))+ " -P "+str(int(p)) + "  >log_"+r+'-'+p)
     if check:
        rc = checkFile(path,r,p)
        if rc<0: 
            print('converting failed',r,p,rc)
            exit()
     print('finished converting ',r,p)
     tmp = {int(r):[int(p)]}
     if EOScopy:  copy2EOS(path,tmp)

def checkFile(path,r,p):
     inFile = os.environ['EOSSHIP']+path+'run_'+ r+'/data_'+p+'.root'
     fI = ROOT.TFile.Open(inFile)
     Nraw = fI.event.GetEntries()
     outFile = 'sndsw_raw_'+r+'-'+p+Mext+'.root'
     fC = ROOT.TFile(outFile)
     test = fC.Get('rawConv')
     if not test:
          print('Error:',path,r,p,' rawConv not found')
          return -2       
     Nconv = fC.rawConv.GetEntries()
     if Nraw != Nconv: 
          print('Error:',path,r,p,':',Nraw,Nconv)
          return -1
     return 0

def copy2EOS(path,success,overwrite=options.overwrite):
  for i in success:
    r = str(i).zfill(6)
    for x in success[i]:
      p = str(x).zfill(4)
      outFile = 'sndsw_raw_'+r+'-'+p+Mext+'.root'
      tmp = path.split('raw_data')[1].replace('data/','')
      pathConv = os.environ['EOSSHIP']+"/eos/experiment/sndlhc/convertedData/"+tmp+"run_"+r+"/sndsw_raw-"+p+".root"
      print('copy '+outFile+' to '+tmp+"run_"+r+"/sndsw_raw-"+p+".root")
      os.system('xrdcp '+outFile+'  '+pathConv)

def check(path,partitions):
 success = {}
 for r in partitions:
    success[r] = []
    runNr   = str(r).zfill(6)
    for x in partitions[r]:
       p = str(x).zfill(4)
       rc = checkFile(path,runNr,p)
       if rc==0: success[r].append(x)
 return success      
 

def getConvStats(runList):
  for run in runList:
     try: 
        f=ROOT.TFile.Open("sndsw_raw_"+str(run).zfill(6)+'.root')
        print(run,':',f.rawConv.GetEntries())
     except:
        print('problem:',run)
         
def rawStats(runList):
   for run in runList:
     runNr   = str(run).zfill(6)
     r = ROOT.TFile.Open(os.environ['EOSSHIP']+path+"/run_"+runNr+"/data.root")
     raw = r.event.GetEntries()
     print(run,':',raw)

def makeHistos(runList):
  for run in runList:
    command = "$SNDSW_ROOT/shipLHC/scripts/Survey-MufiScifi.py -r "+str(run)+" -p "+pathConv+" -g geofile_sndlhc_H6.root -c Mufi_Efficiency -n -1 -t Scifi"
    os.system("python "+command+ " &")
    while count_python_processes('Survey-MufiScifi')>ncpus: 
       time.sleep(200)

def mips():
  for run in runs:
    command = "Survey-MufiScifi.py -r "+str(run)+" -p "+pathConv+" -g geofile_sndlhc_H6.root -c mips"
    os.system("python "+command+ " &")
    while count_python_processes('Survey-MufiScifi')>multiprocessing.cpu_count()-2: 
       time.sleep(200)


if options.prod == "TI18":
      path = "/eos/experiment/sndlhc/raw_data/commissioning/TI18/data/"
      pathConv = "/eos/experiment/sndlhc/convertedData/commissioning/TI18/"
      if len(runList)==0: 
          runList = [1,6,7,8,16,18,19,20,21,23,24,25,26,27]
          # 6,7,8   14,15,22 corrupted
          # 
elif options.prod == "H6":
      path     = "/eos/experiment/sndlhc/raw_data/commissioning/TB_H6/data/"
      pathConv = "/eos/experiment/sndlhc/convertedData/commissioning/TB_H6/"
      if len(runList)==0: 
          runList = [273,276,283,284,285,286,295,296,290,294,298,301,298,292,23,27,34,35,39,40, 41, 42, 43, 44, 45, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 123, 146, 165, 184] 
elif options.prod == "epfl":
      path = "/eos/experiment/sndlhc/raw_data/commissioning/scifi_cosmics_epfl/data/"   
      if len(runList)==0: 
          runList = [3,8]

else:
      print("production not known. you are on your own",options.prod)


if options.command == "convert":

   for r in options.runNumbers.split(','):
      if r!= '': runList.append(int(r))
      
   convert(runList,path)    
   
elif options.command:
    tmp = options.command.split(';')
    command = tmp[0]+"("
    for i in range(1,len(tmp)):
         if i<4: command+='"'+tmp[i]+'"'
         else:    command+=tmp[i]
         if i<len(tmp)-1: command+=","
    command+=")"
    print('executing ' + command )
    eval(command)
