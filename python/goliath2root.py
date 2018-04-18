#!/usr/bin/env python
# file to convert goliath fieldmap text file to root
# EvH 11/4/2018


import ROOT,os,sys
import rootUtils as ut
import shipunit as u
import shipRoot_conf

h={}
ut.bookHist(h,'Bx','Bx',40,-71.86,84.14,15,-23.44,59.16,73,-176.27,183.73)
ut.bookHist(h,'By','By',40,-71.86,84.14,15,-23.44,59.16,73,-176.27,183.73)
ut.bookHist(h,'Bz','Bz',40,-71.86,84.14,15,-23.44,59.16,73,-176.27,183.73) 

f=open('GoliathFieldMap.txt','r')

i=0
for line in f:
  i+=1
  if i<6: continue
  x,y,z,Bx,By,Bz = line.split()
  Bx = Bx
  By = By  
  Bz = Bz  
  
  rc=h['Bx'].SetBinContent(i-5,float(Bx))
  rc=h['By'].SetBinContent(i-5,float(By))  
  rc=h['Bz'].SetBinContent(i-5,float(Bz))  
  
ut.writeHists(h,"GoliathFieldMap.root")
