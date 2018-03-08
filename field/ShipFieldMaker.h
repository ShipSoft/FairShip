/*! \class ShipFieldMaker
  \brief Creates various magnetic fields and assigns them to geometry regions
  \author John Back <J.J.Back@warwick.ac.uk>
*/

#ifndef ShipFieldMaker_H
#define ShipFieldMaker_H

#include "ShipCompField.h"

#include "TString.h"
#include "TVirtualMagField.h"
#include "TVector3.h"

#include <map>
#include <string>
#include <vector>

class TGeoMatrix;
class TGeoNode;
class TGeoVolume;

class ShipFieldMaker
{

 public:

    //! Constructor
    ShipFieldMaker(Bool_t verbose = kFALSE);

    //! Destructor
    virtual ~ShipFieldMaker();

    //! Typedef for a TString-TVirtualMagField* map
    typedef std::map<TString, TVirtualMagField*> SFMap;

    //! Typedef of a vector of strings
    typedef std::vector<std::string> stringVect;

    //! Set-up all the fields and assign to local volumes
    /*!
      \param [in] inputFile The file containing the information about fields and volumes
    */
    void makeFields(const std::string& inputFile);

    //! Get the global magnetic field
    /*!
      \returns the global magnetic field pointer
    */
    ShipCompField* getGlobalField() const {return globalField_;}

    //! Get the map storing volume names and their associated local magnetic fields
    /*!
      \returns the map of volume names and their corresponding magnetic field pointers
    */
    SFMap getAllFields() const {return theFields_;}

    //! Get the magnetic field for the given volume
    /*!
      \param [in] volName The name of the TGeo volume
      \returns the pointer of the local magnetic field for the volume
    */
    TVirtualMagField* getVolumeField(const TString& volName) const;

    //! Check if we have a field stored with the given label name
    /*!
      \param [in] label The label name of the field
      \returns a boolean to say if we already have the field stored in the internal map
    */
    Bool_t gotField(const TString& label) const;

    //! Get the field stored with the given label name
    /*!
      \param [in] label The label name of the field
      \returns the pointer to the magnetic field object
    */
    TVirtualMagField* getField(const TString& label) const;

    //! Plot the magnetic field in x-y plane
    /*!
      \param [in] xAxis Three vector specifying the min, max and bin width of the x axis
      \param [in] yAxis Three vector specifying the min, max and bin width of the y axis
      \param [in] plotFile The name of the output file containing the plot of the magnetic field
    */
    void plotXYField(const TVector3& xAxis, const TVector3& yAxis, const std::string& plotFile) const;

    //! Plot the magnetic field in z-x plane
    /*!
      \param [in] zAxis Three vector specifying the min, max and bin width of the z axis
      \param [in] xAxis Three vector specifying the min, max and bin width of the x axis
      \param [in] plotFile The name of the output file containing the plot of the magnetic field
    */
    void plotZXField(const TVector3& zAxis, const TVector3& xAxis, const std::string& plotFile) const;

    //! Plot the magnetic field in z-y plane
    /*!
      \param [in] zAxis Three vector specifying the min, max and bin width of the z axis
      \param [in] yAxis Three vector specifying the min, max and bin width of the y axis
      \param [in] plotFile The name of the output file containing the plot of the magnetic field
    */
    void plotZYField(const TVector3& zAxis, const TVector3& yAxis, const std::string& plotFile) const;

    //! Plot the magnetic field in "x-y" plane
    /*!
      \param [in] type The co-ordinate type: 0 = x-y, 1 = z-x and 2 = z-y
      \param [in] xAxis Three vector specifying the min, max and bin width of the x axis
      \param [in] yAxis Three vector specifying the min, max and bin width of the y axis
      \param [in] plotFile The name of the output file containing the plot of the magnetic field
    */
    void plotField(Int_t type, const TVector3& xAxis, const TVector3& yAxis, 
		   const std::string& plotFile) const;

    //! ClassDef for ROOT
    ClassDef(ShipFieldMaker,1);

 
 protected:

    //! Structure to hold transformation information
    struct transformInfo {

	//! The x translation displacement
	Double_t x0_;
	//! The y translation displacement
	Double_t y0_;
	//! The z translation displacement
	Double_t z0_;

	//! The first Euler rotation angle (about Z axis)
	Double_t phi_;
	//! The second Euler rotation angle (about new X' axis)
	Double_t theta_;
	//! The third Euler rotation angle (about new Z' axis)
	Double_t psi_;

    };

    //! Create the uniform field based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void createUniform(const stringVect& inputLine);

    //! Create the constant field based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void createConstant(const stringVect& inputLine);

    //! Create the Bell field based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void createBell(const stringVect& inputLine);

    //! Create the field map based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
      \param [in] useSymmetry Boolean to specify if we have x-y quadrant symmetry
    */
    void createFieldMap(const stringVect& inputLine, Bool_t useSymmetry = kFALSE);

    //! Copy (&translate) a field map based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void copyFieldMap(const stringVect& inputLine);

     //! Create the composite field based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void createComposite(const stringVect& inputLine);

   //! Set the global field based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void setGlobalField(const stringVect& inputLine);

    //! Set the regional (local+global) field based on the info from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void setRegionField(const stringVect& inputLine);

    //! Set the local field only based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void setLocalField(const stringVect& inputLine);

    //! Check if we have a local field map and store the volume global transformation
    /*!
      \param [in] localField The pointer (reference) to the field map (which may be updated)
      \param [in] volName The name of the volume (which is used to find the transformation)
      \param [in] scale The B field magnitude scaling factor
    */
    void checkLocalFieldMap(TVirtualMagField*& localField, const TString& volName, Double_t scale);

    //! Get the transformation matrix for the volume position and orientation
    /*!
      \param [in] volName The name of the volume
      \param [in] theInfo The transformation information structure
    */
    void getTransformation(const TString& volName, transformInfo& theInfo);

    //! Update the current geometry node pointer that matches the required volume name
    /*!
      \param [in] aVolume The current volume, whose nodes are looked at
      \param [in] volName The required volume name we want to find
    */
    void findNode(TGeoVolume* aVolume, const TString& volName);


 private:

    //! The global magnetic field
    ShipCompField* globalField_;

    //! The map storing all created magnetic fields
    SFMap theFields_;

    //! Verbose boolean
    Bool_t verbose_;

    //! Double converting Tesla to kiloGauss (for VMC/FairRoot B field units)
    Double_t Tesla_;

    //! The current volume node: used for finding volume transformations
    TGeoNode* theNode_;

    //! Boolean to specify if we have found the volume node we need
    Bool_t gotNode_;

    //! Split a string
    /*!
      \param [in] theString The string to be split up
      \param [in] splitted The delimiter that will be used to split up the string
      \returns a vector of the delimiter-separated strings
    */
    stringVect splitString(std::string& theString, std::string& splitter) const;

};

#endif

