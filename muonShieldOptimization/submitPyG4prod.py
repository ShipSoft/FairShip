import os,time
path = '../'
if not os.uname()[1].find('Ubuntu')<0: path = os.environ['HNL']
os.system('cp '+path+'/g4Ex.py  g4Ex_thisProduction.py ')
nevents = {1:100000,10:1000000,100:10000000}
ecut = 100.
for run in range(30,40):
  logfile =  'log'+str(run)+'_'+str(ecut) 
  if logfile in os.listdir('.'): os.system('rm '+logfile) 
  cmd = 'python g4Ex_thisProduction.py  '+str(run)+' '+str(int(nevents[ecut]))+' '+str(ecut)+' > '+logfile+' &' 
  os.system(cmd)
  time.sleep(10)

# ecut 1,  1E4 events = 63000 seconds  = 17.5h :  for 1E9 -> 200yrs
# ecut 10, 1E4 events = 940   seconds             for 1E9 -> 3yrs
