/*! \class ShipCompField
  \brief Class that defines a magnetic field composed from many fields
  \author John Back <J.J.Back@warwick.ac.uk>
*/

#ifndef ShipCompField_H
#define ShipCompField_H

#include "TVirtualMagField.h"

#include <string>
#include <vector>

class ShipCompField: public TVirtualMagField
{

 public:

    //! Main constructor
    /*!
      \param [in] label A descriptive name/title/lable for the composite field
      \param [in] firstField The first magnetic field for the composite
    */
    ShipCompField(const std::string& label, TVirtualMagField* firstField);

    //! Secondary constructor
    /*!
      \param [in] label A descriptive name/title/lable for the composite field
      \param [in] firstField The first magnetic field pointer for the composite
      \param [in] secondField The second magnetic field pointer for the composite
    */
    ShipCompField(const std::string& label, TVirtualMagField* firstField,
		  TVirtualMagField* secondField);

    //! More general constructor
    /*!
      \param [in] label A descriptive name/title/lable for the composite field
      \param [in] theFields A vector of magnetic field pointers for the composite
    */
    ShipCompField(const std::string& label, const std::vector<TVirtualMagField*>& theFields);

    //! Destructor
    virtual ~ShipCompField();

    //! The total magnetic field from all of the composite sources (linear superposition)
    /*!
      \param [in] position The x,y,z global co-ordinates of the point
      \param [out] B The x,y,z components of the magnetic field
    */
    virtual void Field(const Double_t* position, Double_t* B);

    //! Get the number of fields in the composite
    /*!
      \returns the number of fields used in the composite
    */
    size_t nComposite() const {return theFields_.size();}

    //! Get the vector of fields
    /*!
      \returns the vector of fields
    */
    std::vector<TVirtualMagField*> getCompFields() const {return theFields_;}

    //! ClassDef for ROOT
    ClassDef(ShipCompField,1);

 protected:

 private:

    //! Private copy and assignment operators. 
    ShipCompField(const ShipCompField&);
    ShipCompField& operator=(const ShipCompField&);

    //! The vector of the various magnetic field pointers comprising the composite
    std::vector<TVirtualMagField*> theFields_;

};

#endif

