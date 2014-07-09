import os,time
path = '../'
if os.uname()[1]=='Ubuntu12': path = '/media/LHCb_software/sw/Genie/HNL/'
os.system('cp '+path+'g4opt_mu.py  g4opt_mu_thisProduction.py ')

for E in range(50,450,50):
  logfile =  'log'+str(E) 
  if logfile in os.listdir('.'):  os.system('rm '+logfile)
  cmd = 'python g4opt_mu_thisProduction.py  '+str(E)+'  > '+logfile+' &' 
  os.system(cmd)

