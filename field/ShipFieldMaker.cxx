/*! \class ShipFieldMaker
  \brief Creates various magnetic fields and assigns them to geometry regions.

  The internal units here are cm for distances and Tesla for fields.
  Geant4 units for distance are mm, B fields = 0.001 megaVolt*ns/mm^2 (1 Tesla).
  VMC units require cm and kGauss (0.1 Tesla).
  Internally, use cm and Tesla, so keep distances unchanged but multiply B fields
  by 10 (1 Tesla = 10 kGauss)

  \author John Back <J.J.Back@warwick.ac.uk>
*/

#include "ShipFieldMaker.h"
#include "ShipBFieldMap.h"
#include "ShipConstField.h"
#include "ShipBellField.h"

#include "TGeoManager.h"
#include "TGeoChecker.h"
#include "TGeoPhysicalNode.h"
#include "TGeoUniformMagField.h"
#include "TGeoMatrix.h"
#include "TGeoNode.h"
#include "TGeoVolume.h"
#include "TVirtualMC.h"
#include "TObjArray.h"
#include "TH2.h"
#include "TCanvas.h"
#include "TStyle.h"
#include "TROOT.h"

#include <fstream>
#include <iostream>
#include <string>
#include <cstdlib>

ShipFieldMaker::ShipFieldMaker(Bool_t verbose) :
    TG4VUserPostDetConstruction(),
    globalField_(0),
    theFields_(),
    regionInfo_(),
    localInfo_(),
    verbose_(verbose),
    Tesla_(10.0), // To convert T to kGauss for VMC/FairRoot
    theNode_(0),
    gotNode_(kFALSE)
{
}

ShipFieldMaker::~ShipFieldMaker()
{

    // Delete the various magnetic fields
    SFMap::iterator iter;
    for (iter = theFields_.begin(); iter != theFields_.end(); ++iter) {

	delete iter->second;

    }

    theFields_.clear();

}

void ShipFieldMaker::Construct()
{

    // Assign volumes with their regional (local + global) or local B fields
    this->setAllRegionFields();
    this->setAllLocalFields();

}

void ShipFieldMaker::readInputFile(const std::string& inputFile)
{

    // Check that we have a non-empty string
    if (inputFile.size() < 1) {
	std::cerr<<"Skipping ShipFieldMaker::readInputFile(): file name is empty"<<std::endl;
	return;
    }

    std::string fullFileName = getenv("VMCWORKDIR");
    fullFileName += "/"; fullFileName += inputFile.c_str();

    std::cout<<"ShipFieldMaker::makeFields inputFile = "<<fullFileName<<std::endl;

    std::ifstream getData(fullFileName);
    std::string whiteSpace(" ");

    // Loop while the input file is readable
    while (getData.good()) {
	
	if (getData.peek() == '\n') {
	    
	    // Finish reading line
	    char c;
	    getData.get(c);
	    
	    // Stop while loop if we have reached the end of the file
	    if (getData.eof()) {break;}

	} else if (getData.peek() == '#') {
	    
	    // Skip comment line
	    getData.ignore(1000, '\n');
	    getData.putback('\n');

	    // Stop while loop if we have reached the end of the file
	    if (getData.eof()) {break;}

	} else {

	    // Read data line
	    std::string line("");
	    std::getline(getData, line);

	    // Stop while loop if we have reached the end of the file
	    if (getData.eof()) {break;}
	    
	    // Split up the line according to white spaces
	    std::vector<std::string> lineVect = this->splitString(line, whiteSpace);

	    size_t nWords = lineVect.size();

	    // Check to see if we have at least one keyword at the start of the line
	    if (nWords > 1) {

		TString keyWord(lineVect[0].c_str());
		keyWord.ToLower();

		if (!keyWord.CompareTo("uniform")) {

		    // Define the uniform magnetic field
		    this->defineUniform(lineVect);

		} else if (!keyWord.CompareTo("constant")) {

		    // Define a uniform field with an x,y,z boundary
		    this->defineConstant(lineVect);

		} else if (!keyWord.CompareTo("bell")) {

		    // Define the Bell-shaped field
		    this->defineBell(lineVect);

		} else if (!keyWord.CompareTo("fieldmap")) {

		    // Define the field map
		    this->defineFieldMap(lineVect);

		} else if (!keyWord.CompareTo("symfieldmap")) {

		    // Define the symmetric field map
		    this->defineFieldMap(lineVect, kTRUE);
  
		} else if (!keyWord.CompareTo("copymap")) {

		    // Copy (& translate) the field map
		    this->defineFieldMapCopy(lineVect);

		} else if (!keyWord.CompareTo("composite")) {

		    // Define the composite field
		    this->defineComposite(lineVect);

		} else if (!keyWord.CompareTo("global")) {

		    // Define which fields are global
		    this->defineGlobalField(lineVect);

		} else if (!keyWord.CompareTo("region")) {

		    // Define the local and global fields for the given volume
		    this->defineRegionField(lineVect);

		} else if (!keyWord.CompareTo("local")) {

		    // Define the field for the given volume as the local one only
		    this->defineLocalField(lineVect);

		}

	    }

	}

    }

    getData.close();

}

void ShipFieldMaker::defineUniform(const stringVect& inputLine)
{

    size_t nWords = inputLine.size();

    // Expecting a line such as:
    // Uniform Name Bx By Bz

    if (nWords == 5) {

	const TString name(inputLine[1].c_str());

	Double_t Bx = std::atof(inputLine[2].c_str());
	Double_t By = std::atof(inputLine[3].c_str());
	Double_t Bz = std::atof(inputLine[4].c_str());
	const TVector3 BVector(Bx, By, Bz);

	this->defineUniform(name, BVector);

    } else {

	std::cout<<"Expecting 5 words for the definition of the uniform field: "
		 <<"Uniform Name Bx By Bz"<<std::endl;

    }

}

void ShipFieldMaker::defineUniform(const TString& name, const TVector3& BVector)
{

    // Check if the field is already in the map
    if (!this->gotField(name)) {

	if (verbose_) {std::cout<<"Creating uniform field for "<<name.Data()<<std::endl;}

	Double_t Bx = BVector.X()*Tesla_;
	Double_t By = BVector.Y()*Tesla_;
	Double_t Bz = BVector.Z()*Tesla_;

	TGeoUniformMagField* uField = new TGeoUniformMagField(Bx, By, Bz);
	theFields_[name] = uField;

    }  else {

	if (verbose_) {
	    std::cout<<"We already have a uniform field with the name "
		     <<name.Data()<<std::endl;
	}
    }
}


void ShipFieldMaker::defineConstant(const stringVect& inputLine)
{

    size_t nWords = inputLine.size();

    // Expecting a line such as:
    // Constant Name xMin xMax yMin yMax zMin zMax Bx By Bz

    if (nWords == 11) {

	TString name(inputLine[1].c_str());

	Double_t xMin = std::atof(inputLine[2].c_str());
	Double_t xMax = std::atof(inputLine[3].c_str());

	Double_t yMin = std::atof(inputLine[4].c_str());
	Double_t yMax = std::atof(inputLine[5].c_str());

	Double_t zMin = std::atof(inputLine[6].c_str());
	Double_t zMax = std::atof(inputLine[7].c_str());

	// Input field in Tesla_, interface needs kGauss units
	Double_t Bx = std::atof(inputLine[8].c_str());
	Double_t By = std::atof(inputLine[9].c_str());
	Double_t Bz = std::atof(inputLine[10].c_str());
	
	const TVector2 xRange(xMin, xMax);
	const TVector2 yRange(yMin, yMax);
	const TVector2 zRange(zMin, zMax);
	const TVector3 BVector(Bx, By, Bz);

	this->defineConstant(name, xRange, yRange, zRange, BVector);

    } else {

	std::cout<<"Expecting 11 words for the definition of the constant field: "
		 <<"Constant Name xMin xMax yMin yMax zMin zMax Bx By Bz"<<std::endl;

    }

}

void ShipFieldMaker::defineConstant(const TString& name, const TVector2& xRange, const TVector2& yRange,
				    const TVector2& zRange, const TVector3& BVector)
{

    // Check if the field is already in the map
    if (!this->gotField(name)) {

	Double_t xMin = xRange.X();
	Double_t xMax = xRange.Y();
	Double_t yMin = yRange.X();
	Double_t yMax = yRange.Y();
	Double_t zMin = zRange.X();
	Double_t zMax = zRange.Y();

	Double_t Bx = BVector.X()*Tesla_;
	Double_t By = BVector.Y()*Tesla_;
	Double_t Bz = BVector.Z()*Tesla_;

	ShipConstField* theField = new ShipConstField(name.Data(), xMin, xMax, yMin, yMax,
						      zMin, zMax, Bx, By, Bz);
	theFields_[name] = theField;

    }  else {

	if (verbose_) {
	    std::cout<<"We already have a constant field with the name "
		     <<name.Data()<<std::endl;
	}
    }
}

void ShipFieldMaker::defineBell(const stringVect& inputLine)
{

    size_t nWords = inputLine.size();

    // Expecting a line such as:
    // Bell Name BPeak zMiddle orientationInt tubeRadius

    if (nWords == 6 || nWords == 9) {

	TString name(inputLine[1].c_str());

	Double_t BPeak = std::atof(inputLine[2].c_str());
	Double_t zMiddle = std::atof(inputLine[3].c_str()); // cm

	Int_t orient = std::atoi(inputLine[4].c_str());
	Double_t tubeR = std::atof(inputLine[5].c_str()); // cm

	Double_t xy(0.0), z(0.0), L(0.0);

	if (nWords == 9) {
	    // Specify "target" dimensions (cm)
	    xy = std::atof(inputLine[6].c_str());
	    z  = std::atof(inputLine[7].c_str());
	    L  = std::atof(inputLine[8].c_str());
	}

	this->defineBell(name, BPeak, zMiddle, orient, tubeR, xy, z, L);

    } else {

	std::cout<<"Expecting 6 or 9 words for the definition of the Bell field: "
		 <<"Bell Name BPeak zMiddle orientationInt tubeRadius [targetXY targetZ0 targetL]"<<std::endl;

    }

}

void ShipFieldMaker::defineBell(const TString& name, Double_t BPeak, Double_t zMiddle, 
				Int_t orient, Double_t tubeR, Double_t xy, Double_t z, Double_t L) 
{
    
    if (!this->gotField(name)) {
	
	ShipBellField* theField = new ShipBellField(name.Data(), BPeak*Tesla_, zMiddle, orient, tubeR);

	// Set additional parameters if we have a non-zero target length
	if (fabs(L) > 0.0) {
	    theField->IncludeTarget(xy, z, L);
	}

	theFields_[name] = theField;
	
    } else {

	if (verbose_) {
	    std::cout<<"We already have a Bell field with the name "
		     <<name.Data()<<std::endl;
	}
    }
}


void ShipFieldMaker::defineFieldMap(const stringVect& inputLine, Bool_t useSymmetry)
{

    size_t nWords = inputLine.size();

    // Expecting the line:
    // FieldMap Name mapFileName [x0 y0 z0] [phi theta psi]

    if (nWords == 3 || nWords == 6 || nWords == 9) {

	const TString name(inputLine[1].c_str());
	const TString mapFileName(inputLine[2].c_str());
	
	Double_t x0(0.0), y0(0.0), z0(0.0);
	Double_t phi(0.0), theta(0.0), psi(0.0);

	if (nWords > 5) {
	    x0 = std::atof(inputLine[3].c_str());
	    y0 = std::atof(inputLine[4].c_str());
	    z0 = std::atof(inputLine[5].c_str());
	}

	if (nWords == 9) {
	    phi = std::atof(inputLine[6].c_str());
	    theta = std::atof(inputLine[7].c_str());
	    psi = std::atof(inputLine[8].c_str());
	}

	const TVector3 localCentre(x0, y0, z0);
	const TVector3 localAngles(phi, theta, psi);

	this->defineFieldMap(name, mapFileName, localCentre, localAngles, useSymmetry);

    } else {

	std::cout<<"Expecting 3, 6 or 9 words for the definition of the field map: "
		 <<"(Sym)FieldMap Name mapFileName [x0 y0 z0] [[phi theta psi]]"<<std::endl;

    }
}

void ShipFieldMaker::defineFieldMap(const TString& name, const TString& mapFileName, 
				    const TVector3& localCentre, const TVector3& localAngles,
				    Bool_t useSymmetry)
{
    // Check if the field is already in the map
    if (!this->gotField(name)) {

	// Add the VMCWORKDIR prefix to this map file location
	std::string fullFileName = getenv("VMCWORKDIR");
	fullFileName += "/"; fullFileName += mapFileName.Data();

	if (verbose_) {
	    if (useSymmetry) {
		std::cout<<"Creating symmetric field map called "<<name.Data()<<" using "<<fullFileName<<std::endl;
	    } else {
		std::cout<<"Creating field map called "<<name.Data()<<" using "<<fullFileName<<std::endl;
	    }
	}

	// Since field maps use floating point precision we convert any double parameter
	// values to floats, i.e. we can't simply pass TVector3 objects
	Float_t x0 = localCentre.X();
	Float_t y0 = localCentre.Y();
	Float_t z0 = localCentre.Z();

	Float_t phi = localAngles.X();
	Float_t theta = localAngles.Y();
	Float_t psi = localAngles.Z();

	Float_t scale(1.0);

	ShipBFieldMap* mapField = new ShipBFieldMap(name.Data(), fullFileName, x0, y0, z0, 
						    phi, theta, psi, scale, useSymmetry);
	theFields_[name] = mapField;

    } else {

	if (verbose_) {
	    std::cout<<"We already have a field map with the name "
		     <<name.Data()<<std::endl;	    
	}

    }

}

void ShipFieldMaker::defineFieldMapCopy(const stringVect& inputLine)
{

    // Define a (translated) copy of a field map based in the input file line

    size_t nWords = inputLine.size();

    // Expecting the line:
    // CopyMap Name MapNameToCopy x0 y0 z0 [phi theta psi]

    if (nWords == 6 || nWords == 9) {

	const TString name(inputLine[1].c_str());
	    
	// We want to try to copy and transpose an already existing field map
	const TString mapNameToCopy(inputLine[2].c_str());

	Double_t x0 = std::atof(inputLine[3].c_str());
	Double_t y0 = std::atof(inputLine[4].c_str());
	Double_t z0 = std::atof(inputLine[5].c_str());

	Double_t phi(0.0), theta(0.0), psi(0.0), scale(1.0);

	if (nWords == 9) {
	    phi = std::atof(inputLine[6].c_str());
	    theta = std::atof(inputLine[7].c_str());
	    psi = std::atof(inputLine[8].c_str());
	}

	const TVector3 translation(x0, y0, z0);
	const TVector3 eulerAngles(phi, theta, psi);

	this->defineFieldMapCopy(name, mapNameToCopy, translation, eulerAngles);

    } else {

	std::cout<<"Expecting 6 or 9 words for the copy of a field map: "
		 <<"CopyMap Name MapNameToCopy x0 y0 z0 [phi theta psi]"<<std::endl;

    }

}

void ShipFieldMaker::defineFieldMapCopy(const TString& name, const TString& mapNameToCopy,
					const TVector3& translation, const TVector3& eulerAngles) 
{

    // Check if the field is already in the map
    if (!this->gotField(name)) {

	ShipBFieldMap* fieldToCopy = 
	    dynamic_cast<ShipBFieldMap*>(this->getField(mapNameToCopy));

	if (fieldToCopy) {
		
	    if (verbose_) {
		std::cout<<"Creating map field copy "<<name.Data()
			 <<" based on "<<mapNameToCopy.Data()<<std::endl;
	    }

	    // Since field maps use floating point precision we convert any double parameter
	    // values to floats, i.e. we can't simply pass TVector3 objects
	    Float_t x0 = translation.X();
	    Float_t y0 = translation.Y();
	    Float_t z0 = translation.Z();

	    Float_t phi = eulerAngles.X();
	    Float_t theta = eulerAngles.Y();
	    Float_t psi = eulerAngles.Z();
	    
	    Float_t scale(1.0);

	    ShipBFieldMap* copiedMap = new ShipBFieldMap(name.Data(), *fieldToCopy,
							 x0, y0, z0, phi, theta, psi, scale);
	    theFields_[name] = copiedMap;		    
		
	}

    } else {

	std::cout<<"We already have a copied field map with the name "
		 <<name.Data()<<std::endl;
    }

}


void ShipFieldMaker::defineComposite(const stringVect& inputLine)
{

    size_t nWords = inputLine.size();

    // Expecting a line such as:
    // Composite Name Field1 Field2 ... FieldN

    if (nWords > 2) {

	TString name(inputLine[1].c_str());

	std::vector<TString> fieldNames;
	for (size_t i = 2; i < nWords; i++) {

	    TString aName(inputLine[i].c_str());
	    fieldNames.push_back(aName);

	}

	this->defineComposite(name, fieldNames);

    } else {

	std::cout<<"Expecting at least 3 words for the composite definition: "
		 <<"Composite Name Field1 Field2 ... FieldN"<<std::endl;

    }

}

void ShipFieldMaker::defineComposite(const TString& name, const TString& field1Name,
				     const TString& field2Name, const TString& field3Name,
				     const TString& field4Name)
{

    std::vector<TString> fieldNames;
    fieldNames.push_back(field1Name);
    fieldNames.push_back(field2Name);

    if (field3Name.Length() > 0) {
	fieldNames.push_back(field3Name);
    }
    if (field4Name.Length() > 0) {
	fieldNames.push_back(field4Name);
    }

    this->defineComposite(name, fieldNames);

}

void ShipFieldMaker::defineComposite(const TString& name, std::vector<TString> fieldNames)
{

    // Check if the field is already in the map
    if (!this->gotField(name)) {

	// Loop over the list of fields and add them to the composite
	std::vector<TVirtualMagField*> vectFields;
	
	std::vector<TString>::iterator iter;
	for (iter = fieldNames.begin(); iter != fieldNames.end(); ++iter) {

	    TString aName = *iter;
	    TVirtualMagField* aField = this->getField(aName);
	    if (aField) {
		if (verbose_) {std::cout<<"Adding field "<<aName<<std::endl;}
		vectFields.push_back(aField);
	    }

	    ShipCompField* composite = new ShipCompField(name.Data(), vectFields);
	    theFields_[name] = composite;

	}

    } else {

	std::cout<<"We already have a composite field with the name "
		 <<name.Data()<<std::endl;
    }

}

void ShipFieldMaker::defineGlobalField(const stringVect& inputLine)
{

    // Define the global field using the input file line

    size_t nWords = inputLine.size();

    // Expecting the line:
    // Global Field1 ... FieldN

    if (nWords > 1) {

	TString name("Global");

	std::vector<TString> fieldNames;
	for (size_t i = 1; i < nWords; i++) {

	    TString aName(inputLine[i].c_str());
	    fieldNames.push_back(aName);

	}

	this->defineGlobalField(fieldNames);

    } else {

	std::cout<<"Expecting at least two words for the global field definition: "
		 <<"Global Field1 ... FieldN"<<std::endl;

    }

}

void ShipFieldMaker::defineGlobalField(const TString& field1Name, const TString& field2Name, 
				       const TString& field3Name, const TString& field4Name)
{

    std::vector<TString> fieldNames;
    fieldNames.push_back(field1Name);

    if (field2Name.Length() > 0) {
	fieldNames.push_back(field2Name);
    }
    if (field3Name.Length() > 0) {
	fieldNames.push_back(field3Name);
    }
    if (field4Name.Length() > 0) {
	fieldNames.push_back(field4Name);
    }

    this->defineGlobalField(fieldNames);

}

void ShipFieldMaker::defineGlobalField(std::vector<TString> fieldNames)
{

    if (globalField_) {
	if (verbose_) {
	    std::cout<<"Deleting already existing Global field"<<std::endl;
	}
	delete globalField_;
    }

    if (verbose_) {std::cout<<"Setting the Global field"<<std::endl;}

    std::vector<TVirtualMagField*> vectFields;

    std::vector<TString>::iterator iter;
    for (iter = fieldNames.begin(); iter != fieldNames.end(); ++iter) {

	TString aName = *iter;
	TVirtualMagField* aField = this->getField(aName);
	
	if (aField) {
	    if (verbose_) {std::cout<<"Adding field "<<aName<<" to Global"<<std::endl;}
	    vectFields.push_back(aField);
	} else {
	    std::cout<<"Could not find the field "<<aName<<std::endl;
	}

    }

    TString name("Global");
    globalField_ = new ShipCompField(name.Data(), vectFields);

    // Set this as the global field in the virtual MC
    if (gMC) {
	gMC->SetMagField(globalField_);
    } else {
	std::cout<<"The virtual MC pointer gMC is null! The global field can't be used by Geant4 but will work for track fitting and track extrapolation"<<std::endl;
    }

}

void ShipFieldMaker::defineRegionField(const stringVect& inputLine)
{

    // Set the local + global field for the region using info from inputLine
    size_t nWords = inputLine.size();

    // Expecting the line:
    // Region VolName FieldName [FieldMapScaleFactor]

    if (nWords == 3 || nWords == 4) {
	
	TString volName(inputLine[1].c_str());
	TString fieldName(inputLine[2].c_str());

	Double_t scale(1.0);
	if (nWords == 4) {scale = std::atof(inputLine[3].c_str());}

	this->defineRegionField(volName, fieldName, scale);

    } else {

	std::cout<<"Expecting 3 or 4 words for the region (local + global) field definition: "
		 <<"Region VolName LocalFieldName [LocalFieldMapScale]"<<std::endl;

    }

}

void ShipFieldMaker::defineRegionField(const TString& volName, const TString& fieldName, Double_t scale)
{

    if (verbose_) {
	std::cout<<"ShipFieldMaker::defineRegionField for volume "
		 <<volName.Data()<<" and field "<<fieldName.Data()
		 <<" with scale = "<<scale<<std::endl;
    }

    fieldInfo theInfo(volName, fieldName, scale);
    regionInfo_.push_back(theInfo);

}

void ShipFieldMaker::setAllRegionFields()
{

    // Loop over all entries in the regionInfo_ vector and assign fields to their volumes
    std::vector<fieldInfo>::iterator regionIter;

    for (regionIter = regionInfo_.begin(); regionIter != regionInfo_.end(); ++regionIter) {

	fieldInfo theInfo = *regionIter;
	const TString volName = theInfo.volName_;
	TString fieldName = theInfo.fieldName_;
	Double_t scale = theInfo.scale_;

	// Find the volume
	TGeoVolume* theVol(0);
	if (gGeoManager) {theVol = gGeoManager->FindVolumeFast(volName.Data());}

	if (theVol) {	    

	    // Find the local field
	    TVirtualMagField* localField = this->getField(fieldName);

	    if (localField) {

		// Check local field maps know about their associated volume position and orientation.
		// This will update the localField pointer if required
		this->checkLocalFieldMap(localField, volName, scale);

		// Reset the fieldName to use the name from the localField pointer, since this
		// could have changed for a local field map, for example
		fieldName = localField->GetName();

		// See if we have already combined this local field with the global field
		if (globalField_ && fieldName.Length() > 0) {

		    TString lgName(fieldName); lgName += "Global";
		    TVirtualMagField* lgField = this->getField(lgName);

		    if (!lgField) {

			// Create the combined local + global field and store in the internal map.
			// Other volumes that use the same combined field will use the stored pointer
			if (verbose_) {
			    std::cout<<"Creating the combined field "<<lgName.Data()<<", with local field "
				     <<fieldName.Data()<<" with the global field for volume "
				     <<volName.Data()<<std::endl;
			}

			ShipCompField* combField = new ShipCompField(lgName.Data(), localField, globalField_);
			theFields_[lgName] = combField;
			theVol->SetField(combField);

		    } else {

			if (verbose_) {
			    std::cout<<"Setting the field "<<lgName.Data()
				     <<" for volume "<<volName.Data()<<std::endl;
			}
			theVol->SetField(lgField);

		    }

		} else {

		    if (verbose_) {
			std::cout<<"There is no global field defined. Just setting the local field"<<std::endl;
		    }
		    theVol->SetField(localField);

		}

	    } else {

		std::cout<<"Could not find the local field "<<fieldName.Data()<<std::endl;

	    }


	} else {

	    std::cout<<"Could not find the volume "<<volName<<std::endl;

	}

    } // regionIter loop

}

void ShipFieldMaker::defineLocalField(const stringVect& inputLine)
{

    // Set only the local field for the region using info from inputLine
    size_t nWords = inputLine.size();

    // Expecting the line:
    // Local VolName FieldName [FieldMapScaleFactor]

    if (nWords == 3 || nWords == 4) {
	
	TString volName(inputLine[1].c_str());
	TString fieldName(inputLine[2].c_str());

	Double_t scale(1.0);
	if (nWords == 4) {scale = std::atof(inputLine[3].c_str());}

	this->defineLocalField(volName, fieldName, scale);

    } else {

	std::cout<<"Expecting 3 or 4 words for the local field definition: "
		 <<"Local VolName LocalFieldName [FieldMapScale]"<<std::endl;

    }

}

void ShipFieldMaker::defineLocalField(const TString& volName, const TString& fieldName, Double_t scale)
{

    if (verbose_) {
	std::cout<<"ShipFieldMaker::defineLocalField for volume "
		 <<volName.Data()<<" and field "<<fieldName.Data()
		 <<" with scale = "<<scale<<std::endl;
    }
    
    fieldInfo theInfo(volName, fieldName,scale);
    localInfo_.push_back(theInfo);

}

void ShipFieldMaker::setAllLocalFields()
{

    // Loop over all entries in the localInfo_ vector and assign fields to their volumes
    std::vector<fieldInfo>::iterator localIter;

    for (localIter = localInfo_.begin(); localIter != localInfo_.end(); ++localIter) {

	fieldInfo theInfo = *localIter;
	const TString volName = theInfo.volName_;
	TString fieldName = theInfo.fieldName_;
	Double_t scale = theInfo.scale_;

	TGeoVolume* theVol(0);
	if (gGeoManager) {theVol = gGeoManager->FindVolumeFast(volName.Data());}
 
	if (theVol) {	    

	    TVirtualMagField* localField = this->getField(fieldName);
	    
	    if (localField) {

		this->checkLocalFieldMap(localField, volName, scale);
		theVol->SetField(localField);

		if (verbose_) {
		    std::cout<<"Setting local field "<<localField->GetName()
			     <<" for volume "<<volName<<std::endl;
		}

	    } else {

		std::cout<<"Could not find the field "<<fieldName.Data()<<std::endl;
	    }

	} else {

	    std::cout<<"Could not find the volume "<<volName.Data()<<std::endl;
	}

    } // localIter loop

}

void ShipFieldMaker::checkLocalFieldMap(TVirtualMagField*& localField, const TString& volName, 
					Double_t scale) {

    // We assume that local field maps are stored using co-ordinates centred
    // on the volume. However, GetField() uses global co-ordinates, so we need
    // to find the global volume transformation (translation and rotation) so
    // that we can find the equivalent local co-ordinates. This also means that each
    // local volume needs to have its own lightweight field map copy, where we
    // reuse the field map data but just change the co-ordinate transformation info

    ShipBFieldMap* mapField = dynamic_cast<ShipBFieldMap*>(localField);
    if (mapField) {

	TString fieldName(mapField->GetName());
	TString localName(fieldName); localName += volName;

	if (verbose_) {
	    std::cout<<"Checking local field map "<<fieldName
		     <<" co-ord transformation for volume "<<volName<<std::endl;
	}

	// Check if we already have the local map to avoid duplication
	ShipBFieldMap* localMap = dynamic_cast<ShipBFieldMap*>(this->getField(localName));
	
	if (!localMap && volName.Length() > 0) {

	    // Get the volume and its associate global transformation
	    TString volName1(volName); volName1 += "_1";

	    transformInfo theInfo;
	    this->getTransformation(volName1, theInfo);
	    
	    // The original field map may have defined its own translation and rotation.
	    // Apply this before the volume global transformation
	    Double_t origX0 = mapField->GetXOffset();
	    Double_t origY0 = mapField->GetYOffset();
	    Double_t origZ0 = mapField->GetZOffset();
	    TGeoTranslation origTrans("origTrans", origX0, origY0, origZ0);

	    Double_t origPhi = mapField->GetPhi();
	    Double_t origTheta = mapField->GetTheta();
	    Double_t origPsi = mapField->GetPsi();
	    TGeoRotation origRot("origRot", origPhi, origTheta, origPsi);

	    TGeoCombiTrans origComb(origTrans, origRot);
	    if (verbose_) {
		std::cout<<"The original field map transformation:"<<std::endl;
		origComb.Print();
	    }

	    TGeoTranslation newTrans("newTrans", theInfo.x0_, theInfo.y0_, theInfo.z0_);
	    TGeoRotation newRot("newRot", theInfo.phi_, theInfo.theta_, theInfo.psi_);
	    
	    TGeoCombiTrans newComb(newTrans, newRot);

	    if (verbose_) {
		std::cout<<"The volume transformation:"<<std::endl;
		newComb.Print();
	    }

	    // The full transformation
	    newComb = newComb*origComb;

	    if (verbose_) {
		std::cout<<"The combined transformation:"<<std::endl;
		newComb.Print();
	    }

	    // Update transformation info
	    const Double_t* newTransArray = newComb.GetTranslation();
	    theInfo.x0_ = newTransArray[0];
	    theInfo.y0_ = newTransArray[1];
	    theInfo.z0_ = newTransArray[2];
	    
	    const TGeoRotation* fullRot = newComb.GetRotation();
	    if (fullRot) {
		fullRot->GetAngles(theInfo.phi_, theInfo.theta_, theInfo.psi_);
	    }

	    // Create a lightweight copy, reusing the map data but just updating
	    // the global transformation
	    if (verbose_) {
		std::cout<<"Creating field map copy for "<<localName
			 <<" based on "<<mapField->GetName()
			 <<": x0 = "<<theInfo.x0_<<", y0 = "<<theInfo.y0_
			 <<", z0 = "<<theInfo.z0_<<", phi = "<<theInfo.phi_
			 <<", theta = "<<theInfo.theta_
			 <<", psi = "<<theInfo.psi_<<", scale = "<<scale
			 <<" and symmetry = "<<mapField->HasSymmetry()<<std::endl;
	    }

	    localMap = new ShipBFieldMap(localName.Data(), *mapField, 
					 theInfo.x0_, theInfo.y0_, theInfo.z0_,
					 theInfo.phi_, theInfo.theta_, theInfo.psi_, scale);
	    // Keep track that we have created this field pointer
	    theFields_[localName] = localMap;

	}
	
	// Set the localField pointer to use the (new or already existing) localMap pointer
	localField = localMap;
	
    }

}

void ShipFieldMaker::getTransformation(const TString& volName, transformInfo& theInfo) {

    // Find the geometry node that matches the volume name. We need to search
    // the geometry hierarchy recursively until we get a match. Note that nodes
    // have "_1" appended to the volume name.

    theInfo.x0_ = 0.0; theInfo.y0_ = 0.0; theInfo.z0_ = 0.0;
    theInfo.phi_ = 0.0; theInfo.theta_ = 0.0; theInfo.psi_ = 0.0;

    TGeoMatrix* theMatrix(0);

    TGeoVolume* topVolume = gGeoManager->GetTopVolume();
    if (!topVolume) {
	std::cout<<"Can't find the top volume in ShipFieldMaker::getTransformation"<<std::endl;
	return;
    }

    if (verbose_) {std::cout<<"Finding transformation for "<<volName<<std::endl;}

    // Find the geometry node that matches the required name
    theNode_ = 0;
    gotNode_ = kFALSE;
    this->findNode(topVolume, volName);

    if (theNode_) {theMatrix = theNode_->GetMatrix();}

    // Retrieve the translation and rotation information
    if (theMatrix) {

	// Translation displacement components
	const Double_t* theTrans = theMatrix->GetTranslation();
	theInfo.x0_ = theTrans[0];
	theInfo.y0_ = theTrans[1];
	theInfo.z0_ = theTrans[2];

	// Euler rotation angles. First check if we have a combined translation
	// and rotation, then check if we just have a pure rotation
	if (theMatrix->IsCombi()) {

	    TGeoCombiTrans* theCombi = dynamic_cast<TGeoCombiTrans*>(theMatrix);
	    if (theCombi) {		
		TGeoRotation* combRotn = theCombi->GetRotation();
		if (combRotn) {
		    combRotn->GetAngles(theInfo.phi_, theInfo.theta_, theInfo.psi_);
		}
	    }

	} else if (theMatrix->IsRotation()) {

	    TGeoRotation* theRotn = dynamic_cast<TGeoRotation*>(theMatrix);
	    if (theRotn) {
		theRotn->GetAngles(theInfo.phi_, theInfo.theta_, theInfo.psi_);
	    }
	}
    }

}

void ShipFieldMaker::findNode(TGeoVolume* aVolume, const TString& volName) {

    // Find the geometry node that matches the required volume name

    // Immediately exit the function if we have already found the volume
    if (gotNode_) {return;}

    if (aVolume) {

	TObjArray* volNodes = aVolume->GetNodes();

	if (volNodes) {

	    // Loop over the geometry nodes
	    int nNodes = volNodes->GetEntries();
	    for (int i = 0; i < nNodes; i++) {

		TGeoNode* node = dynamic_cast<TGeoNode*>(volNodes->At(i));

		if (node) {

		    const TString nodeName(node->GetName());
		    if (!nodeName.CompareTo(volName, TString::kExact)) {

			// We have a match. The node has the transformation we need
			theNode_ = node;
			gotNode_ = kTRUE;
			break;

		    } else if (node->GetNodes()) {

			// We have sub-volumes. Recursively call this function
			this->findNode(node->GetVolume(), volName);

		    }

		}

	    }

	}

    }

}

TVirtualMagField* ShipFieldMaker::getVolumeField(const TString& volName) const
{

    TVirtualMagField* theField(0);
    TGeoVolume* theVol(0);
    if (gGeoManager) {theVol = gGeoManager->FindVolumeFast(volName.Data());}

    if (theVol) {
	// Need to cast the TObject* to a TVirtualMagField*
	theField = dynamic_cast<TVirtualMagField*>(theVol->GetField());
    }

    return theField;

}

Bool_t ShipFieldMaker::gotField(const TString& name) const
{

    Bool_t result(kFALSE);

    // Iterate over the internal map and see if we have a match 
    SFMap::const_iterator iter;
    for (iter = theFields_.begin(); iter != theFields_.end(); ++iter) {
   
	TString key = iter->first;
	TVirtualMagField* theField = iter->second;

	// Check that we have the key already stored and the pointer is not null
	if (!key.CompareTo(name, TString::kExact) && theField) {
	    result = kTRUE;
	    break;
	}

    }

    return result;

}

TVirtualMagField* ShipFieldMaker::getField(const TString& name) const
{
  
    TVirtualMagField* theField(0);

    // Iterate over the internal map and see if we have a match 
    SFMap::const_iterator iter;
    for (iter = theFields_.begin(); iter != theFields_.end(); ++iter) {
   
	TString key = iter->first;
	TVirtualMagField* BField = iter->second;

	// Check that we have the key already stored
	if (!key.CompareTo(name, TString::kExact)) {
	    theField = BField;
	    break;
	}

    }

    return theField;

}

void ShipFieldMaker::plotXYField(const TVector3& xAxis, const TVector3& yAxis,
				 const std::string& plotFile) const
{    
    this->plotField(0, xAxis, yAxis, plotFile);
}

void ShipFieldMaker::plotZXField(const TVector3& zAxis, const TVector3& xAxis,
				 const std::string& plotFile) const
{    
    this->plotField(1, zAxis, xAxis, plotFile);
}

void ShipFieldMaker::plotZYField(const TVector3& zAxis, const TVector3& yAxis,
				 const std::string& plotFile) const
{    
    this->plotField(2, zAxis, yAxis, plotFile);
}

void ShipFieldMaker::plotField(Int_t type, const TVector3& xAxis, const TVector3& yAxis,
			       const std::string& plotFile) const
{

    std::cout<<"ShipFieldMaker plotField "<<plotFile<<": type = "<<type<<std::endl;

    Double_t xMin = xAxis(0);
    Double_t xMax = xAxis(1);
    Double_t dx   = xAxis(2);
    Int_t Nx(0);
    if (dx > 0.0) {Nx = static_cast<Int_t>(((xMax - xMin)/dx) + 0.5);}
    
    Double_t yMin = yAxis(0);
    Double_t yMax = yAxis(1);
    Double_t dy   = yAxis(2);
    Int_t Ny(0);
    if (dy > 0.0) {Ny = static_cast<Int_t>(((yMax - yMin)/dy) + 0.5);}

    // Create a 2d histogram
    const int nhistograms = 4; //x,y,z,and magnitude
    const int ncoordinates = 3; //x,y,z
    
    TH2D theHist[nhistograms]; 
    std::string titles[nhistograms] = {"Bx (T)","By (T)","Bz (T)","B (T)"};
    for (int icomponent = 0; icomponent< nhistograms; icomponent++){
      theHist[icomponent] = TH2D(Form("theHist[%i]",icomponent), titles[icomponent].data(), Nx, xMin, xMax, Ny, yMin, yMax);
      theHist[icomponent].SetDirectory(0);
      if (type == 0) {
	// x-y
	theHist[icomponent].SetXTitle("x (cm)"); 
	theHist[icomponent].SetYTitle("y (cm)");
     } 
      else if (type == 1) {
	// z-x
	theHist[icomponent].SetXTitle("z (cm)"); 
	theHist[icomponent].SetYTitle("x (cm)");
      } 
      else if (type == 2) {
	// z-y
	theHist[icomponent].SetXTitle("z (cm)"); 
	theHist[icomponent].SetYTitle("y (cm)");
      }
    }
    // Get list of volumes (to check for local fields)
    TObjArray* theVolumes = gGeoManager->GetListOfVolumes();
    Int_t nVol(0);
    if (theVolumes) {nVol = theVolumes->GetSize();}

    // Loop over "x" axis
    for (Int_t ix = 0; ix < Nx; ix++) {

	Double_t x = dx*ix + xMin;

	// Loop over "y" axis
	for (Int_t iy = 0; iy < Ny; iy++) {

	    Double_t y = dy*iy + yMin;

	    // Initialise the B field array to zero
	    Double_t B[ncoordinates] = {0.0, 0.0, 0.0};

	    // Initialise the position array to zero
	    Double_t position[ncoordinates] = {0.0, 0.0, 0.0};
	    if (type == 0) {
		// x-y
  	        position[0] = x, position[1] = y;
	    } else if (type == 1) {
		// z-x
		position[0] = y, position[2] = x;
	    } else if (type == 2) {
		// z-y
		position[1] = y; position[2] = x;
	    }

	    // Find out if the point is inside one of the geometry volumes
	    Bool_t inside(kFALSE);

	    // Find the geoemtry node (volume path)
	    TGeoNode* theNode = gGeoManager->FindNode(position[0], position[1], position[2]);
	    
	    if (theNode) {
		
		// Get the volume
		TGeoVolume* theVol = theNode->GetVolume();

		if (theVol) {

		    // Get the magnetic field
		    TVirtualMagField* theField = dynamic_cast<TVirtualMagField*>(theVol->GetField());

		    if (theField) {

			// Find the "local" field inside the volume (using global co-ords)
			theField->Field(position, B);
			inside = kTRUE;

		    } // theField

		} // volume

	    } // node

	    // If no local volumes found, use global field if it exists
	    if (inside == kFALSE && globalField_) {
		globalField_->Field(position, B);
	    }
		    
	    // Divide by the Tesla_ factor, since we want to plot Tesla_ not kGauss (VMC/FairRoot units)
	    for (int icomponent = 0; icomponent<ncoordinates; icomponent++){
	      theHist[icomponent].Fill(x,y, B[icomponent]/Tesla_);
	    }
	    Double_t BMag = sqrt(B[0]*B[0] + B[1]*B[1] + B[2]*B[2])/Tesla_;
	    theHist[3].Fill(x, y, BMag);

	} // "y" axis

    } // "x" axis

    Bool_t wasBatch = gROOT->IsBatch();
    // Disable pop-up windows
    gROOT->SetBatch(kTRUE);
    TCanvas theCanvas("theCanvas", "", 900, 700);
    gROOT->SetStyle("Plain");
    gStyle->SetOptStat(0);
    // Set colour style
    gStyle->SetPalette(kBird);
    theCanvas.UseCurrentStyle();

    theCanvas.Divide(2,2);
	for (int icomponent = 0; icomponent < nhistograms; icomponent++){
		theCanvas.cd(icomponent+1);
		theHist[icomponent].Draw("colz");
	}
    theCanvas.Print(plotFile.c_str());

    // Reset the batch boolean
    if (wasBatch == kFALSE) {gROOT->SetBatch(kFALSE);}

}

ShipFieldMaker::stringVect ShipFieldMaker::splitString(std::string& theString, 
						       std::string& splitter) const {

    // Code from STLplus
    stringVect result;

    if (!theString.empty() && !splitter.empty()) {

	for (std::string::size_type offset = 0;;) {

	    std::string::size_type found = theString.find(splitter, offset);

	    if (found != std::string::npos) {
		std::string tmpString = theString.substr(offset, found-offset);
		if (tmpString.size() > 0) {result.push_back(tmpString);}
		offset = found + splitter.size();
	    } else {
		std::string tmpString = theString.substr(offset, theString.size()-offset);
		if (tmpString.size() > 0) {result.push_back(tmpString);}
		break;
	    }
	}
    }
    
    return result;

}
