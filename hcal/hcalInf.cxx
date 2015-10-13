/**  hcalInf.cxx
 *@author Mikhail Prokudin
 **
 ** Container of HCAL geometry parameters
 **/

#include "hcalInf.h"

#include "FairRunAna.h"
#include "FairRuntimeDb.h"

#include "TSystem.h"
#include "TMap.h"

#include <iostream>
#include <fstream>
#include <string>

using std::cout;
using std::cerr;
using std::endl;
using std::string;

hcalInf* hcalInf::fInf=NULL;
Int_t hcalInf::fRefCount=0;


hcalInf::~hcalInf()
{
  for(Int_t i=0;i<fHcalStr.GetSize();i++)
    delete (TObjString*)(fHcalStr.At(i));
  fHcalStr.Clear();
}

hcalInf* hcalInf::GetInstance(const char* filename)
{
	if (filename==NULL)
	{
		if (fInf!=NULL)
			fRefCount++;
		return fInf;
	}
	TString newname=gSystem->Getenv("VMCWORKDIR");
	newname+="/geometry/";
	newname+=filename;
	if (fInf!=NULL) {
		if (fInf->fFileName==newname) {
			fRefCount++;
			return fInf;
		} else {
		  cerr << "hcalInf: Trying create ";
		  cerr << "instance of hcalInf with";
		  cerr << " name " << filename;
		  cerr << ", which is different from ";
		  cerr << fInf->fFileName << "." << endl;
		  return NULL;
		}
    }
	fInf=new hcalInf(newname);
	//Is something wrong?
	if (fInf->fSuccess==0)
	{
		delete fInf;
		return NULL;
	}
	fRefCount++;
	return fInf;
}

int cmp_nocase(const string &s, const string &s2 )
{
  string::const_iterator p=s.begin();
  string::const_iterator p2=s2.begin();
  while(p!=s.end()&&p2!=s2.end()) {
    if (toupper(*p)!=toupper(*p2)) return (toupper(*p)<toupper(*p2))?-1:1;
    ++p;
    ++p2;
  }
  return(s2.size()==s.size())?0:(s.size()<s2.size())?-1:1; // size is unsigned
}

Double_t hcalInf::GetVariableStrict(const char* key)
{
  TObjString* value=(TObjString*)fVariables->GetValue(key);
  if (value==NULL)
  {
    cerr << "Can't find variable named \"" << key << "\"";
    Fatal("GetVariableStrict","Exiting...");
  }
  Double_t val;
  char* err=NULL;
  val=strtod(value->GetString(),&err);
  if (err[0]!='\0')
  {
    cerr << "Can't convert variable named \"" << key ;
    cerr << "\" to floating point. Value is \"";
    cerr << value->GetString() << "\"." << endl;
    Fatal("GetVariableStrict","Exiting...");
  }
  return val;
}

TString hcalInf::GetStringVariable(const char* key)
{
  TObjString* value=(TObjString*)fVariables->GetValue(key);
  if (value==NULL)
  {
    Fatal("GetStringVariable","Can't find variable named %s.", key);
  }
  return value->GetString();
}



Double_t hcalInf::GetVariable(const char* key)
{
  TObjString* value=(TObjString*)fVariables->GetValue(key);
  if (value==NULL)
    return -1111;
  Double_t val;
  char* err=NULL;
  val=strtod(value->GetString(),&err);
  if (err[0]!='\0')
    return -1111;
  return val;
}

void hcalInf::AddVariable(const char* key, const char* value)
{
  TObjString* skey=(TObjString*)fVariables->FindObject(key);
  //Value for this key already exists!!!
  if (skey!=NULL) return;
  skey=new TObjString(key);
  skey->String().ToLower();
  TObjString* svalue=new TObjString(value);
  fVariables->Add(skey, svalue);
}
//=============================================================================
hcalInf::hcalInf(const char* filename)
  : TObject(), 
    fVariables(new TMap(200)), 
    fHcalStr(), 
    fXPos(0.), 
    fYPos(0.),
    fZPos(0.), 
    fNLayers(0), 
    fN1Layers(0), 
    fXSize(0), 
    fYSize(0), 
    fModuleSize(0.), 
    fAbsorber(0.), 
    fScin(0.), 
    fTyveec(0.), 
    fThicknessLayer(0.),
    fCellSize(0.), 
    fHcalSize(), 
    fECut(0.), 
    fHCut(0.), 
    fSemiX(0.),
    fSemiY(0.),
    fFastMC(-1),
    fSuccess(1), 
    fFileName(filename) 
{
  /**
   ** Constructor reads and parses the ascii file, and fill 
   ** the HCAL geometry container
   **
  FairRunAna* ana = FairRunAna::Instance();
  if (ana!=NULL)
  {
    FairRuntimeDb* rtdb=ana->GetRuntimeDb();
    rtdb->getContainer("CbmGeoHcalPar");
  }
  */
  std::ifstream file(filename);
  Int_t linenum;
  Double_t val;
  string buffer;
  string message;
  string variable;
  string value;
  TObjString* str=NULL;
  char** err=NULL;
  char winend[2]={13, 0};
  int ssize=-1;

  if (!file) {
    cerr << "hcalInf: Can't open information file " << filename << "!" << endl;
    cerr << "hcalInf: Hcal will not be constructed correctly." << endl;
    fSuccess=0;
    return;
  }

  linenum=0;
  while(getline(file,buffer)) {
    linenum++;
    message=buffer.substr(buffer.find_first_not_of(" 	"));	//Skiping initial spaces
    message=message.substr(0,message.find("#"));	//Removing comments
    // Threat windows end of strings correctly
    message=message.substr(0,message.find(winend));
    if (message.empty()) continue;		//This was just a comment
    variable=message.substr(0,message.find("="));
    if (variable=="structure") {
      while(getline(file,buffer)) {
	linenum++;
	if (buffer.empty()) break;
	message=buffer.substr(buffer.find_first_not_of(" 	"));	//Skiping initial spaces
	message=message.substr(0,message.find("#"));	//Removing comments
	message=message.substr(0,message.find_last_not_of(" 	")+1);	//Skiping ending spaces

        // Threat windows end of strings correctly
        message=message.substr(0,message.find(winend));

	if (!message.empty()) {
	  if (-1==ssize)
	    ssize=message.size();
	  else
	    if (ssize!=(Int_t)message.size()) {
	      cerr << "Error in HCAL structure at line " << linenum;
	      cerr << "." << endl;
	      cerr << "Line length differs from previous one" << endl;
              fSuccess=0;
	      file.close();
	      return;
	      
	    }
	  
	  str=new TObjString(message.c_str());
	  fHcalStr.Add(str);
	}
      }
      break;
    }
    if (variable==message) {
      cerr << "Syntax error: File " << filename << ".Line " << linenum << "." << endl;
      fSuccess=0;
      file.close();
      return;
    }
    variable=variable.substr(0,variable.find_first_of(" 	"));
    value=message.substr(message.find("=")+1);
    value=value.substr(value.find_first_not_of(" 	"));	//Skiping initial spaces
    value=value.substr(0,value.find_first_of(" 	"));
/*
    value=value.substr(0,value.find_first_not_of("1234567890-+e."));
    val=strtod(value.c_str(),err);
    if (err) {
      cerr << "Syntax error after =: File " << filename << ".Line " << linenum << "." << endl;
      fSuccess=0;
      file.close();
      return;
    }
*/
    AddVariable(variable.c_str(), value.c_str());
  }
  file.close();
  InitVariables();
}

Bool_t hcalInf::ExcludeParameter(TString parname)
{
  if (parname.CompareTo("hcalversion")==0) return kTRUE;
  return kFALSE;
}

/*
void hcalInf::CheckVariables()
{
  FairRunAna* ana = FairRunAna::Instance();
  if (ana==NULL)
  {
    return;
  }
  FairRuntimeDb* rtdb=ana->GetRuntimeDb();
  CbmGeoHcalPar* par=(CbmGeoHcalPar*)(rtdb->findContainer("CbmGeoHcalPar"));
  if (par==NULL)
  {
    Info("CheckVariables","No parameters container is found.");
    return;
  }
  TMap* parVariables=par->GetVariables();
  if (parVariables)
  {
    TObjString* key;
    TIterator* iter=parVariables->MakeIterator();
    while((key=(TObjString*)iter->Next())!=NULL)
    {
      TObjString* first=(TObjString*)parVariables->GetValue(key->String());
      TObjString* second=(TObjString*)fVariables->GetValue(key->String());
      if (ExcludeParameter(key->String())==kFALSE)
      if (second==NULL)
      {
	Info("CheckVariables", "Parameter %s not found in .geo file, but found in parameter file.", key->String().Data());
      } else
      if (first->String()!=second->String())
      {
	Info("CheckVariables", "Parameter %s differs in .geo file and parameter file!", key->String().Data());
	Info("CheckVariables", "%s=%s in parameter file.", key->String().Data(), first->String().Data());
	Info("CheckVariables", "%s=%s in .geo file.", key->String().Data(), second->String().Data());
      }
      if (ExcludeParameter(key->String())==kTRUE)
	AddVariable(key->String().Data(), first->String().Data());
    }
  }

  TObjArray* parHcalStr=par->GetHcalStr();
  if (parHcalStr)
  {
    TObjString* key;
    for(Int_t i=0;i<parHcalStr->GetEntriesFast();i++)
    {
      TObjString* first=(TObjString*)parHcalStr->At(i);
      TObjString* second=(TObjString*)fHcalStr.At(i);
      if (second&&first->String()!=second->String())
      {
	Info("CheckVariables", "String %d in calorimeter structure differs in .geo file and in parameter file.", i);
	Info("CheckVariables", "%s=%s in parameter file", key->String().Data(), first->String().Data());
	Info("CheckVariables", "%s=%s in .geo file", key->String().Data(), second->String().Data());
      }
    }
  }
}
*/
void hcalInf::InitVariables()
{
  TString stri;
  TObjString* str=(TObjString*)fHcalStr.At(0);

  fXPos=GetVariableStrict("xpos");
  fYPos=GetVariableStrict("ypos");
  fZPos=GetVariableStrict("zpos");
  fNLayers=(Int_t)GetVariableStrict("nlayers");
  fN1Layers=(Int_t)GetVariableStrict("n1layers");
  fModuleSize=GetVariableStrict("modulesize");
  fAbsorber=GetVariableStrict("absorber");
  fScin=GetVariableStrict("scin");
  fTyveec=GetVariableStrict("tyveec");
  fHcalSize[2]=GetVariableStrict("hcalzsize");
  fECut=GetVariableStrict("ecut");
  fHCut=GetVariableStrict("hcut");
  fFastMC=(Int_t)GetVariableStrict("fastmc");
  fSemiX=GetVariableStrict("xsemiaxis");
  fSemiY=GetVariableStrict("ysemiaxis");

  stri=""; stri+=str->GetString().Length();
  AddVariable("xsize", stri);
  stri=""; stri+=fHcalStr.GetLast()+1;
  AddVariable("ysize", stri);

  fXSize=(Int_t)GetVariableStrict("xsize");
  fYSize=(Int_t)GetVariableStrict("ysize");
  fThicknessLayer = 2.0*GetTyveec()+GetScin()+GetAbsorber();
  fHcalSize[0]    = GetXSize()*GetModuleSize();
  fHcalSize[1]    = GetYSize()*GetModuleSize();
  stri=""; stri+=fHcalSize[0];
  AddVariable("xhcalsize",stri);
  stri=""; stri+=fHcalSize[1];
  AddVariable("yhcalsize",stri);
}

//-----------------------------------------------------------------------------
void hcalInf::DumpContainer() const
{
  // Print out the HCAL geometry container

  if (fVariables)
  {
    TObjString* key;
    TIterator* iter=fVariables->MakeIterator();
    while((key=(TObjString*)iter->Next())!=NULL)
    {
      TObjString* str=(TObjString*)fVariables->GetValue(key);
      cout << key->String() << "=" << str->String() << endl;
    }
  }
  TObjString* key;
  TIterator* iter=fHcalStr.MakeIterator();

  Int_t modules=0;
  Int_t channels=0;
  Int_t i;
  Int_t j;
  Int_t m[10];
  char stri[2]={0, 0};
  TString st;
  for(i=0;i<10;i++) m[i]=0;

  while((key=(TObjString*)iter->Next())!=NULL)
  {
    st=key->String();
    cout << key->String() << endl;
    for(i=0;i<st.Length();i++)
    {
      stri[0]=st[i];
      j=atoi(stri);
      m[j]++;
      if (j) modules++;
      channels+=j*j;
    }
  }
  cout << "Total modules:  " << modules << endl;
  cout << "Total channels: " << channels << endl;
  for(i=1;i<10;i++)
  {
    if (m[i]==0) continue;
    cout << "	Type " << i << " : modules=" << m[i] << ", channels=" << m[i]*i*i << endl;
  }

}

