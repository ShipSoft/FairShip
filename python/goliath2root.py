#!/usr/bin/env python
# file to convert goliath fieldmap text file to root
# EvH 11/4/2018


import ROOT,os,sys
import rootUtils as ut
import shipunit as u
import shipRoot_conf

h={}
# new limits x: -1118.6, 1241.4 (59); y: -411.40, 768.60 (20); z: -2512.7, 2537.3 (101)
# 

ut.bookHist(h,'Bx','Bx',60,-113.86,126.14,21,-44.09,79.81,102,-253.77,256.27)
ut.bookHist(h,'By','By',60,-113.86,126.14,21,-44.09,79.81,102,-253.77,256.27)
ut.bookHist(h,'Bz','Bz',60,-113.86,126.14,21,-44.09,79.81,102,-253.77,256.27) 
ut.bookHist(h,'Byvsz','By vs z for x=1.4,y=1.6',102,-253.77,256.27) 
f=open('ExtGoliathFieldMap.txt','r')

i=0
for line in f:
  i+=1
  if i<6: continue
  x,y,z,Bx,By,Bz = line.split()
  x=float(x)/10.
  y=float(y)/10.
  z=float(z)/10.
  Bx = Bx
  By = By  
  Bz = Bz  

  rc=h['Bx'].Fill(float(x),float(y),float(z),float(Bx))
  rc=h['By'].Fill(float(x),float(y),float(z),float(By)) 
  rc=h['Bz'].Fill(float(x),float(y),float(z),float(Bz)) 
  
  if (round(x,2)==0.14) and (round(y,2)==0.16):
     rc=h['Byvsz'].Fill(float(z),float(By)) 
  
ut.writeHists(h,"GoliathFieldMap.root")
