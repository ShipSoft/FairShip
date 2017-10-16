/*! \class ShipCompField
  \brief Class that defines a magnetic field composed from many fields
  \author John Back <J.J.Back@warwick.ac.uk>
*/

#include "ShipCompField.h"

#include <iostream>

ShipCompField::ShipCompField(const std::string& label,
			     TVirtualMagField* firstField) : 
    TVirtualMagField(label.c_str()),
    theFields_()
{
    theFields_.push_back(firstField);
}

ShipCompField::ShipCompField(const std::string& label,
			     TVirtualMagField* firstField,
			     TVirtualMagField* secondField) : 
    TVirtualMagField(label.c_str()),
    theFields_()
{
    theFields_.push_back(firstField);
    theFields_.push_back(secondField);
}

ShipCompField::ShipCompField(const std::string& label,
			     const std::vector<TVirtualMagField*>& theFields) :
    TVirtualMagField(label.c_str()),
    theFields_(theFields)
{
}

ShipCompField::~ShipCompField()
{
    // The destructor does nothing since this class does not own
    // the various TVirtualMagField pointers
}

void ShipCompField::Field(const Double_t* position, Double_t* B)
{

    // Loop over the fields and do a simple linear superposition

    // First initialise the field components to zero
    B[0] = 0.0, B[1] = 0.0, B[2] = 0.0;

    std::vector<TVirtualMagField*>::const_iterator iter;
    for (iter = theFields_.begin(); iter != theFields_.end(); ++iter) {

	TVirtualMagField* theField = *iter;
	if (theField) {

	    //std::cout<<"Finding field for "<<theField->GetName()<<std::endl;

	    // Find the magnetic field components for this part
	    Double_t BVect[3] = {0.0, 0.0, 0.0};
	    theField->Field(position, BVect);
	    
	    // Simple linear superposition of the B field components
	    B[0] += BVect[0];
	    B[1] += BVect[1];
	    B[2] += BVect[2];

	    //std::cout<<"B = "<<BVect[0]<<", "<<BVect[1]<<", "<<BVect[2]<<std::endl;
	    //std::cout<<"BSum = "<<B[0]<<", "<<B[1]<<", "<<B[2]<<std::endl;

	}

    }

}
