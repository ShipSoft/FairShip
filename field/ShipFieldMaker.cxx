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
#include <cstdlib>

ShipFieldMaker::ShipFieldMaker(Bool_t verbose) :
    globalField_(0),
    theFields_(),
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

void ShipFieldMaker::makeFields(const std::string& inputFile)
{

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

		    // Create the uniform magnetic field
		    this->createUniform(lineVect);

		} else if (!keyWord.CompareTo("constant")) {

		    // Create a uniform field with an x,y,z boundary
		    this->createConstant(lineVect);

		} else if (!keyWord.CompareTo("bell")) {

		    // Create the Bell-shaped field
		    this->createBell(lineVect);

		} else if (!keyWord.CompareTo("fieldmap")) {

		    // Create the field map
		    this->createFieldMap(lineVect);

		} else if (!keyWord.CompareTo("symfieldmap")) {

		    // Create the symmetric field map
		    this->createFieldMap(lineVect, kTRUE);
  
		} else if (!keyWord.CompareTo("copymap")) {

		    // Copy (& translate) the field map
		    this->copyFieldMap(lineVect);

		} else if (!keyWord.CompareTo("composite")) {

		    // Create the composite field
		    this->createComposite(lineVect);

		} else if (!keyWord.CompareTo("global")) {

		    // Set which fields are global
		    this->setGlobalField(lineVect);

		} else if (!keyWord.CompareTo("region")) {

		    // Set the local and global fields for the given volume
		    this->setRegionField(lineVect);

		} else if (!keyWord.CompareTo("local")) {

		    // Set the field for the given volume as the local one only
		    this->setLocalField(lineVect);

		}

	    }

	}

    }

    getData.close();

}

void ShipFieldMaker::createUniform(const stringVect& inputLine)
{

    size_t nWords = inputLine.size();

    // Expecting a line such as:
    // Uniform LabelName Bx By Bz

    if (nWords == 5) {

	TString label(inputLine[1].c_str());

	// Check if the field is already in the map
	if (!this->gotField(label)) {

	    Double_t Bx = std::atof(inputLine[2].c_str())*Tesla_;
	    Double_t By = std::atof(inputLine[3].c_str())*Tesla_;
	    Double_t Bz = std::atof(inputLine[4].c_str())*Tesla_;
	    
	    if (verbose_) {std::cout<<"Creating uniform field for "<<label.Data()<<std::endl;}

	    TGeoUniformMagField* uField = new TGeoUniformMagField(Bx, By, Bz);
	    theFields_[label] = uField;

	} else {
	    std::cout<<"We already have a field with the name "
		     <<label.Data()<<std::endl;
	}

    } else {

	std::cout<<"Expecting 5 words for the definition of the uniform field: "
		 <<"Uniform Label Bx By Bz"<<std::endl;

    }


}

void ShipFieldMaker::createConstant(const stringVect& inputLine)
{

    size_t nWords = inputLine.size();

    // Expecting a line such as:
    // Constant LabelName xMin xMax yMin yMax zMin zMax Bx By Bz

    if (nWords == 11) {

	TString label(inputLine[1].c_str());

	// Check if the field is already in the map
	if (!this->gotField(label)) {

	    Double_t xMin = std::atof(inputLine[2].c_str());
	    Double_t xMax = std::atof(inputLine[3].c_str());

	    Double_t yMin = std::atof(inputLine[4].c_str());
	    Double_t yMax = std::atof(inputLine[5].c_str());

	    Double_t zMin = std::atof(inputLine[6].c_str());
	    Double_t zMax = std::atof(inputLine[7].c_str());

	    // Input field in Tesla_, interface needs kGauss units
	    Double_t Bx = std::atof(inputLine[8].c_str())*Tesla_;
	    Double_t By = std::atof(inputLine[9].c_str())*Tesla_;
	    Double_t Bz = std::atof(inputLine[10].c_str())*Tesla_;

	    if (verbose_) {std::cout<<"Creating constant field for "<<label.Data()<<std::endl;}

	    ShipConstField* theField = new ShipConstField(label.Data(), xMin, xMax, yMin, yMax,
							  zMin, zMax, Bx, By, Bz);
	    theFields_[label] = theField;

	} else {
	    std::cout<<"We already have a field with the name "
		     <<label.Data()<<std::endl;
	}

    } else {

	std::cout<<"Expecting 11 words for the definition of the constant field: "
		 <<"Constant Label xMin xMax yMin yMax zMin zMax Bx By Bz"<<std::endl;

    }


}

void ShipFieldMaker::createBell(const stringVect& inputLine)
{

    size_t nWords = inputLine.size();

    // Expecting a line such as:
    // Bell LabelName BPeak zMiddle orientationInt tubeRadius

    if (nWords == 6 || nWords == 9) {

	TString label(inputLine[1].c_str());

	// Check if the field is already in the map
	if (!this->gotField(label)) {

	    // Input field in Tesla_, interface needs kGauss units
	    Double_t BPeak = std::atof(inputLine[2].c_str())*Tesla_;
	    Double_t zMiddle = std::atof(inputLine[3].c_str()); // cm

	    Int_t orient = std::atoi(inputLine[4].c_str());
	    Double_t tubeR = std::atof(inputLine[5].c_str()); // cm

	    if (verbose_) {std::cout<<"Creating Bell field for "<<label.Data()<<std::endl;}

	    ShipBellField* theField = new ShipBellField(label.Data(), BPeak, zMiddle, orient, tubeR);

	    if (nWords == 9) {
		// Specify "target" dimensions (cm)
		Double_t xy = std::atof(inputLine[6].c_str());
		Double_t z  = std::atof(inputLine[7].c_str());
		Double_t L  = std::atof(inputLine[8].c_str());
		theField->IncludeTarget(xy, z, L);
	    }

	    theFields_[label] = theField;

	} else {
	    std::cout<<"We already have a field with the name "
		     <<label.Data()<<std::endl;
	}

    } else {

	std::cout<<"Expecting 6 or 9 words for the definition of the Bell field: "
		 <<"Bell Label BPeak zMiddle orientationInt tubeRadius [targetXY targetZ0 targetL]"<<std::endl;

    }


}


void ShipFieldMaker::createFieldMap(const stringVect& inputLine, Bool_t useSymmetry)
{

    size_t nWords = inputLine.size();

    // Expecting the line:
    // FieldMap LabelName mapFileName [x0 y0 z0] [phi theta psi]

    if (nWords == 3 || nWords == 6 || nWords == 9) {

	TString label(inputLine[1].c_str());

	// Check if the field is already in the map
	if (!this->gotField(label)) {

	    std::string mapFileName = inputLine[2];

	    // Add the VMCWORKDIR prefix to this map name
	    std::string fullFileName = getenv("VMCWORKDIR");
	    fullFileName += "/"; fullFileName += mapFileName.c_str();

	    Double_t x0(0.0), y0(0.0), z0(0.0);
	    Double_t phi(0.0), theta(0.0), psi(0.0);
	    Double_t scale(1.0);

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

	    if (verbose_) {
       	        if (useSymmetry) {
		    std::cout<<"Creating symmetric map field "<<label.Data()<<" using "<<fullFileName<<std::endl;
		} else {
		    std::cout<<"Creating map field "<<label.Data()<<" using "<<fullFileName<<std::endl;
		}
	    }
	    
	    ShipBFieldMap* mapField = new ShipBFieldMap(label.Data(), fullFileName, x0, y0, z0, 
							phi, theta, psi, scale, useSymmetry);
	    theFields_[label] = mapField;

	} else {

	    std::cout<<"We already have a field with the name "
		     <<label.Data()<<std::endl;

	}

    } else {

	std::cout<<"Expecting 3, 6 or 9 words for the definition of the field map: "
		 <<"(Sym)FieldMap Label mapFileName [x0 y0 z0] [[phi theta psi]]"<<std::endl;

    }


}

void ShipFieldMaker::copyFieldMap(const stringVect& inputLine)
{

    size_t nWords = inputLine.size();

    // Expecting the line:
    // CopyMap LabelName MapLabelToCopy x0 y0 z0 [phi theta psi]

    if (nWords == 6 || nWords == 9) {

	TString label(inputLine[1].c_str());

	// Check if the field is already in the map
	if (!this->gotField(label)) {
	    
	    // We want to try to copy and transpose an already existing field map
	    TString mapToCopy(inputLine[2].c_str());
	    Double_t x0 = std::atof(inputLine[3].c_str());
	    Double_t y0 = std::atof(inputLine[4].c_str());
	    Double_t z0 = std::atof(inputLine[5].c_str());

	    Double_t phi(0.0), theta(0.0), psi(0.0), scale(1.0);

	    if (nWords == 9) {
		phi = std::atof(inputLine[6].c_str());
		theta = std::atof(inputLine[7].c_str());
		psi = std::atof(inputLine[8].c_str());
	    }

	    ShipBFieldMap* fieldToCopy = 
		dynamic_cast<ShipBFieldMap*>(this->getField(mapToCopy));

	    if (fieldToCopy) {
		
		if (verbose_) {
		    std::cout<<"Creating map field copy "<<label.Data()
			     <<" based on "<<mapToCopy.Data()<<std::endl;
		}

		ShipBFieldMap* copiedMap = new ShipBFieldMap(label.Data(), *fieldToCopy,
							     x0, y0, z0, phi, theta, psi, scale);
		theFields_[label] = copiedMap;		    
		
	    }
	    

	} else {
	    std::cout<<"We already have a field with the name "
		     <<label.Data()<<std::endl;
	}

    } else {

	std::cout<<"Expecting 6 or 9 words for the copy of a field map: "
		 <<"CopyMap Label MapLabelToCopy x0 y0 z0 [phi theta psi]"<<std::endl;

    }

}

void ShipFieldMaker::createComposite(const stringVect& inputLine)
{

    size_t nWords = inputLine.size();

    // Expecting a line such as:
    // Composite Label Field1 Field2 ... FieldN

    if (nWords > 2) {

	TString label(inputLine[1].c_str());

	// Check if the field is already in the map
	if (!this->gotField(label)) {

	    if (verbose_) {std::cout<<"Creating composite for "<<label.Data()<<std::endl;}

	    // Loop over the list of fields and add them to the composite
	    std::vector<TVirtualMagField*> vectFields;
	    for (size_t i = 2; i < nWords; i++) {

		TString aLabel(inputLine[i].c_str());
		TVirtualMagField* aField = this->getField(aLabel);
		if (aField) {
		    if (verbose_) {std::cout<<"Adding field "<<aLabel<<std::endl;}
		    vectFields.push_back(aField);
		}

	    }

	    ShipCompField* composite = new ShipCompField(label.Data(), vectFields);
	    theFields_[label] = composite;

	} else {
	    std::cout<<"We already have a field with the name "
		     <<label.Data()<<std::endl;
	}

    } else {

	std::cout<<"Expecting at least 3 words for the composite definition: "
		 <<"Composite Label Field1 Field2 ... FieldN"<<std::endl;

    }

}

void ShipFieldMaker::setGlobalField(const stringVect& inputLine)
{

    size_t nWords = inputLine.size();

    // Expecting the line:
    // Global Field1 ... FieldN

    if (globalField_) {delete globalField_;}

    if (nWords > 1) {

	if (verbose_) {std::cout<<"Setting the global field"<<std::endl;}

	TString label("Global");

	std::vector<TVirtualMagField*> vectFields;
	for (size_t i = 1; i < nWords; i++) {

	    TString aLabel(inputLine[i].c_str());
	    TVirtualMagField* aField = this->getField(aLabel);
	    if (aField) {
		if (verbose_) {std::cout<<"Adding field "<<aLabel<<" to global"<<std::endl;}
		vectFields.push_back(aField);
	    } else {
		std::cout<<"Could not find the field "<<aLabel<<std::endl;
	    }

	}

	globalField_ = new ShipCompField(label.Data(), vectFields);
	// Set this as the global field in the virtual MC
	if (gMC) {
	    if (verbose_) {
		std::cout<<"Settting "<<label.Data()<<" field as the global field for gMC"<<std::endl;
	    }
	    gMC->SetMagField(globalField_);
	} else {
	    std::cout<<"Error. The global virtual MC pointer gMC is null! The global field can't be used!"<<std::endl;
	}

    } else {

	std::cout<<"Expecting at least two words for the global field definition: "
		 <<"Global Field1 ... FieldN"<<std::endl;

    }

}

void ShipFieldMaker::setRegionField(const stringVect& inputLine)
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

	if (verbose_) {
	    std::cout<<"ShipFieldMaker::setRegionField for volume "
		     <<volName.Data()<<" and field "<<fieldName.Data()
		     <<" with scale = "<<scale<<std::endl;
	}

	TGeoVolume* theVol(0);
	if (gGeoManager) {theVol = gGeoManager->FindVolumeFast(volName.Data());}

	if (theVol) {	    

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

		    std::cout<<"There is no global field defined. Just setting the local field"<<std::endl;
		    theVol->SetField(localField);

		}

	    } else {

		std::cout<<"Could not find the local field "<<fieldName.Data()<<std::endl;

	    }


	} else {

	    std::cout<<"Could not find the volume "<<volName<<std::endl;

	}

    } else {

	std::cout<<"Expecting 3 or 4 words for the region (local + global) field definition: "
		 <<"Region VolName LocalFieldToInclude [LocalFieldMapScale]"<<std::endl;

    }

}

void ShipFieldMaker::setLocalField(const stringVect& inputLine)
{

    // Set the local + global field for the region using info from inputLine

    size_t nWords = inputLine.size();

    // Expecting the line:
    // Local VolName FieldName [FieldMapScaleFactor]

    if (nWords == 3 || nWords == 4) {
	
	TString volName(inputLine[1].c_str());
	TString fieldName(inputLine[2].c_str());

	Double_t scale(1.0);
	if (nWords == 4) {scale = std::atof(inputLine[3].c_str());}

	if (verbose_) {
	    std::cout<<"ShipFieldMaker::setLocalField for volume "
		     <<volName.Data()<<" and field "<<fieldName.Data()
		     <<" with scale = "<<scale<<std::endl;
	}

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

    } else {

	std::cout<<"Expecting 3 or 4 words for the local field definition: "
		 <<"Local VolName LocalFieldName [FieldMapScale]"<<std::endl;

    }

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

    //std::cout<<"Finding field for "<<volName<<std::endl;

    TGeoVolume* theVol(0);
    if (gGeoManager) {theVol = gGeoManager->FindVolumeFast(volName.Data());}

    if (theVol) {
	// Need to cast the TObject* to a TVirtualMagField*
	theField = dynamic_cast<TVirtualMagField*>(theVol->GetField());
    }

    return theField;

}

Bool_t ShipFieldMaker::gotField(const TString& label) const
{

    Bool_t result(kFALSE);

    // Iterate over the internal map and see if we have a match 
    SFMap::const_iterator iter;
    for (iter = theFields_.begin(); iter != theFields_.end(); ++iter) {
   
	TString key = iter->first;
	TVirtualMagField* theField = iter->second;

	// Check that we have the key already stored and the pointer is not null
	if (!key.CompareTo(label, TString::kExact) && theField) {
	    result = kTRUE;
	    break;
	}

    }

    return result;

}

TVirtualMagField* ShipFieldMaker::getField(const TString& label) const
{
  
    TVirtualMagField* theField(0);

    // Iterate over the internal map and see if we have a match 
    SFMap::const_iterator iter;
    for (iter = theFields_.begin(); iter != theFields_.end(); ++iter) {
   
	TString key = iter->first;
	TVirtualMagField* BField = iter->second;

	// Check that we have the key already stored
	if (!key.CompareTo(label, TString::kExact)) {
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

    std::cout<<"ShipFieldMaker plotField "<<plotFile<<std::endl;

    Double_t xMin = xAxis(0);
    Double_t xMax = xAxis(1);
    Double_t dx   = xAxis(2);
    Int_t Nx(0);
    if (dx > 0.0) {Nx = static_cast<Int_t>(((xMax - xMin)/dx) + 1);}
    
    Double_t yMin = yAxis(0);
    Double_t yMax = yAxis(1);
    Double_t dy   = yAxis(2);
    Int_t Ny(0);
    if (dy > 0.0) {Ny = static_cast<Int_t>(((yMax - yMin)/dy) + 1);}
    
    // Create a 2d histogram
    TH2D theHist("theHist", "", Nx, xMin, xMax, Ny, yMin, yMax);
    theHist.SetDirectory(0);
    if (type == 0) {
	// x-y
	theHist.SetXTitle("x (cm)"); 
	theHist.SetYTitle("y (cm)");
    } else if (type == 1) {
	// z-x
	theHist.SetXTitle("z (cm)"); 
	theHist.SetYTitle("x (cm)");
    } else if (type == 2) {
	// z-y
	theHist.SetXTitle("z (cm)"); 
	theHist.SetYTitle("y (cm)");
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
	    Double_t B[3] = {0.0, 0.0, 0.0};

	    // Initialise the position array to zero
	    Double_t position[3] = {0.0, 0.0, 0.0};
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
	    Double_t BMag = sqrt(B[0]*B[0] + B[1]*B[1] + B[2]*B[2])/Tesla_;
	    theHist.Fill(x, y, BMag);

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

    theCanvas.cd();
    theHist.Draw("colz");
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
