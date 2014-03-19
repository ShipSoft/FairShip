This is a very basic implementation of a software framework for the Ship which is based on FairRoot 
To use this software you need:

1. Install FairSoft (see https://github.com/FairRootGroup/FairSoft/tree/dev )

2. Install FairRoot (http://fairroot.gsi.de/?q=node/82)

3. get the Ship software:
  
  > git clone   https://github.com/MohammadAlTurany/Ship.git
  
  > Set a variable SIMPATH to the directory  where the FairSoft  was installed
  
  > Set a variable FAIRROOTPATH to the directory where the FairRoot was installed 
  
  > create  build directory 
   
  > cd build
  
  build> cmake ../ship
  
  build>make 
  
  > if compiled successfully you can go to ship/macro directory and run macro (i.e:  "root run_sim.C -l")
  
  > After that you can also see what is done by running the eventdisplay.C macro  (i.e: "root  event display.C -l")
  
  
  
  