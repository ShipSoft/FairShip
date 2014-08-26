#include "ecalLightMap.h"

#include "TSystem.h"

#include <iostream>
#include <fstream>
#include <string>
#include <list>
#include <stdlib.h>

using namespace std;

ecalLightMap::ecalLightMap(const char* fname, const char* title) 
  : TNamed(fname, title),
    fSSide(-1111.), fS(-1111), fSize(0), fData(NULL)
{
  Init(fname);
}

/** Read information from file **/
void ecalLightMap::Init(const char* filename)
{
  TString fn=filename;
  gSystem->ExpandPathName(fn);
  ifstream f(fn);
  list<Double_t> lst;
  string buf;
  string token;
  string message;
  if (!f)
  {
    Fatal("Init","Can't open file %s.", filename);
    return;
  }

  while(getline(f, buf))
  {
    if (buf.empty()) continue;
    if (buf.find_first_not_of(" 	")==string::npos) continue;
    //Skipping initial spaces
    message=buf.substr(buf.find_first_not_of(" 	"));
    if (message.empty()) continue;
    //Removing comments
    message=message.substr(0,message.find("#"));
    if (message.empty()) continue;
    while(!message.empty())
    {
      token=message.substr(0,message.find_first_of(" 	"));
      if (token.empty()) break;
      lst.push_back(atof(token.c_str()));
      if (token==message) break;
      token=message.substr(message.find_first_of(" 	"));
      if (token.empty()) break;
      if (token.find_first_not_of(" 	")==string::npos) break;
      message=token.substr(token.find_first_not_of(" 	"));
    }
  }
  f.close();

  list<Double_t>::const_iterator p=lst.begin();
  Double_t xsize;
  Double_t ysize;
  Double_t sqside;
  Double_t l;
  Double_t x;
  Double_t y;
  Double_t z;
  Double_t v;
  Int_t n;
  Int_t i;

  xsize=(*p); ++p; ysize=(*p); ++p; sqside=(*p); ++p;
  fS=(Int_t)((xsize+0.00001)/sqside);
  fSize=fS*fS; fSSide=sqside/xsize;
  fData=new Double_t[fSize];
  for(i=0;i<fSize;i++)
    fData[i]=-1111;
  for(;;)
  {
    if (p==lst.end()) break; l=(*p); ++p;
    if (p==lst.end()) break; x=(*p); ++p;
    if (p==lst.end()) break; y=(*p); ++p;
    if (p==lst.end()) break; z=(*p); ++p;
    if (p==lst.end()) break; v=(*p); ++p;
    x/=xsize; y/=ysize;
    n=GetNum(x ,y);
    if (n>=fSize)
    {
      Info("Init","Data is not selfconsistent (%f, %f), %d", x, y, fSize);
    }
    fData[n]=v;
  }
  lst.clear();
  FillGaps();
  Normalize();
}

/** Fix a light collection map **/
void ecalLightMap::FillGaps()
{
  Int_t i;
  Int_t j;
  Double_t x;
  Double_t y;
  Int_t n[3];
  Double_t v;
  Int_t d;

  for(i=0;i<fSize;i++)
  if (fData[i]<0)
  {
    x=(i%fS)*fSSide-0.5+fSSide/2.0;
    y=(i/fS)*fSSide-0.5+fSSide/2.0;
    n[0]=GetNum( x,-y);
    n[1]=GetNum(-x, y);
    n[2]=GetNum(-x,-y);
    v=0; d=0;
    for(j=0;j<3;j++)
    if (n[j]>=0&&fData[n[j]]>=0)
      { d++; v+=fData[n[j]]; }
    if (d>0)
    {
      v/=d; fData[i]=v;
      if (fData[n[0]]<=0) fData[n[0]]=v;
      if (fData[n[1]]<=0) fData[n[1]]=v;
      if (fData[n[2]]<=0) fData[n[2]]=v;
    }
    else
      Info("FillGaps","No data for (%f,%f)", x, y);
  }
}

/** Set average efficiency of light collection to 1.0 **/
void ecalLightMap::Normalize()
{
  Int_t i;
  Int_t n=0;
  Double_t v=0;
  for(i=0;i<fSize;i++)
    if (fData[i]>0)
      { v+=fData[i]; n++; }
  v/=n;
  for(i=0;i<fSize;i++)
    if (fData[i]>0)
      fData[i]/=v;
}

ClassImp(ecalLightMap)
