/*! \class ShipFieldMaker
  \brief Creates various magnetic fields and assigns them to geometry regions
  \author John Back <J.J.Back@warwick.ac.uk>

  This inherits from TG4VUserPostDetConstruction and overloads the Contruct()
  function so that the VMC (re)assigns the G4 magnetic fields to volumes using the
  input configuration file defined in this class constructor, together with
  the code below used in the addVMCFields function in python/geomGeant4.py:

  geom = ROOT.TG4GeometryManager.Instance()
  geom.SetUserPostDetConstruction(fieldMaker)
  geom.ConstructSDandField()

*/

#ifndef ShipFieldMaker_H
#define ShipFieldMaker_H

#include "ShipCompField.h"

#include "TString.h"
#include "TVirtualMagField.h"
#include "TVector2.h"
#include "TVector3.h"
#include "TG4VUserPostDetConstruction.h"

#include <map>
#include <string>
#include <vector>

class TGeoMatrix;
class TGeoNode;
class TGeoVolume;

class ShipFieldMaker : public TG4VUserPostDetConstruction
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

    //! Structure to hold volume name, field name and field scaling factor
    struct fieldInfo {

	//! The name of the volume
	TString volName_;
	//! The name of the field
	TString fieldName_;
	//! The field scaling factor
	Double_t scale_;
	
	//! Default constructor
        fieldInfo() : volName_(""), fieldName_(""), scale_(1.0) {};

	//! Constructor
        fieldInfo(const TString& volName, const TString& fieldName, Double_t scale = 1.0) :
	          volName_(volName), fieldName_(fieldName), scale_(scale) {};

    };

    //! Set-up all local and regional fields and assign them to volumes
    virtual void Construct();

    //! Read an input file to define fields and associated volumes
    /*!
      \param [in] inputFile The input text file
    */
    void readInputFile(const std::string& inputFile);

    //! Define a uniform field
    /*!
      \param [in] name The name of the field
      \param [in] BVector The vector of B field components (Bx, By, Bz) in Tesla
    */
    void defineUniform(const TString& name, const TVector3& BVector);

    //! Define a constant field
    /*!
      \param [in] name The name of the field
      \param [in] xRange The x range as a TVector2(xMin, xMax)
      \param [in] yRange The y range as a TVector2(yMin, yMax)
      \param [in] zRange The z range as a TVector2(zMin, zMax)
      \param [in] BVector The vector of B field components (Bx, By, Bz) in Tesla
    */
    void defineConstant(const TString& name, const TVector2& xRange, const TVector2& yRange,
			const TVector2& zRange, const TVector3& BVector);

    //! Define a Bell field
    /*!
      \param [in] name The name of the field
      \param [in] BPeak The peak B field magnitude (Tesla)
      \param [in] zMiddle The middle z global position of the magnet (cm)
      \param [in] orient Orientation flag: 1 => Bx = 0 (default), 0 => By = 0  
      \param [in] tubeR The largest inner radius of the tube ellipse (cm); default = 500 cm
      \param [in] xy Optional target xy radius region (cm)
      \param [in] z Optional target start z global position (cm)
      \param [in] L Optional target region length (cm)
    */
    void defineBell(const TString& name, Double_t BPeak, Double_t zMiddle,
		    Int_t orient = 1, Double_t tubeR = 500.0,
		    Double_t xy = 0.0, Double_t z = 0.0, Double_t L = 0.0);

    // ! Define a field map
    /*!
      \param [in] name The name of the field
      \param [in] mapFileName The location of the field map ROOT file relative to VMCWORKDIR
      \param [in] localCentre The TVector3(x,y,z) offset shift applied to all field map coordinates
      \param [in] localAngles The TVector3(phi, theta, psi) Euler rotation applied to all map coords
      \param [in] useSymmetry Boolean to specify if the map has quadrant symmetry (default = false)
    */   
    void defineFieldMap(const TString& name, const TString& mapFileName,
			const TVector3& localCentre = TVector3(0.0, 0.0, 0.0),
			const TVector3& localAngles = TVector3(0.0, 0.0, 0.0),
			Bool_t useSymmetry = kFALSE);

    //! Define a copy of a field map with a coordinate translation and optional rotation
    /*!
      \param [in] name The name of the field
      \param [in] mapNameToCopy The name of the field map that is to be copied
      \param [in] translation The TVector3(x,y,z) coordinate translation
      \param [in] eulerAngles The TVector3(phi, theta, psi) Euler angle rotation
    */
    void defineFieldMapCopy(const TString& name, const TString& mapNameToCopy,
			    const TVector3& translation,
			    const TVector3& eulerAngles = TVector3(0.0, 0.0, 0.0));

    //! Define a composite field from up to four fields
    /*!
      \param [in] name The name of the composite field
      \param [in] field1Name The name of the first field
      \param [in] field2Name The name of the second field
      \param [in] field3Name The name of the third field (optional)
      \param [in] field4Name The name of the fourth field (optional)
    */
    void defineComposite(const TString& name, const TString& field1Name,
			 const TString& field2Name, const TString& field3Name = "",
			 const TString& field4Name = "");

    //! Define a composite field from a vector of field names
    /*!
      \param [in] name The name of the composite field
      \param [in] fieldNames Vector of all of the field names to be combined
    */
    void defineComposite(const TString& name, std::vector<TString> fieldNames);

    //! Define a composite field from up to four fields
    /*!
      \param [in] field1Name The name of the first field
      \param [in] field2Name The name of the second field (optional)
      \param [in] field3Name The name of the third field (optional)
      \param [in] field4Name The name of the fourth field (optional)
    */
    void defineGlobalField(const TString& field1Name, const TString& field2Name = "",
			   const TString& field3Name = "", const TString& field4Name = "");

    //! Define the Global field using a vector of field names
    /*!
      \param [in] fieldNames Vector of all of the field names to be combined
    */
    void defineGlobalField(std::vector<TString> fieldNames);

    //! Define a regional (local + global) field and volume pairing
    /*!
      \param [in] volName The name of the volume
      \param [in] fieldName The name of the field for the volume
      \param [in] scale Optional scale factor for field maps (default = 1.0)
    */
    void defineRegionField(const TString& volName, const TString& fieldName,
			   Double_t scale = 1.0);

    //! Define a localised field and volume pairing
    /*!
      \param [in] volName The name of the volume
      \param [in] fieldName The name of the local field for the volume
      \param [in] scale Optional scale factor for field maps (default = 1.0)
    */
    void defineLocalField(const TString& volName, const TString& fieldName,
			  Double_t scale = 1.0);


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

    //! Check if we have a field stored with the given name name
    /*!
      \param [in] name The name of the field
      \returns a boolean to say if we already have the field stored in the internal map
    */
    Bool_t gotField(const TString& name) const;

    //! Get the field stored with the given name name
    /*!
      \param [in] name The name of the field
      \returns the pointer to the magnetic field object
    */
    TVirtualMagField* getField(const TString& name) const;

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

    //! Define a uniform field based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void defineUniform(const stringVect& inputLine);

    //! Define a constant field based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void defineConstant(const stringVect& inputLine);

    //! Define a Bell field based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void defineBell(const stringVect& inputLine);

    //! Define a field map based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
      \param [in] useSymmetry Boolean to specify if we have x-y quadrant symmetry
    */
    void defineFieldMap(const stringVect& inputLine, Bool_t useSymmetry = kFALSE);

    //! Define a (translated) copy of a field map based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void defineFieldMapCopy(const stringVect& inputLine);

     //! Define a composite field based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void defineComposite(const stringVect& inputLine);

   //! Define the global field based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void defineGlobalField(const stringVect& inputLine);

    //! Define a regional (local+global) field based on the info from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void defineRegionField(const stringVect& inputLine);

    // ! Setup all of the regional fields. Called by Construct()
    void setAllRegionFields();


    //! Define a local field only based on information from the inputLine
    /*!
      \param [in] inputLine The space separated input line
    */
    void defineLocalField(const stringVect& inputLine);

    //! Check if we have a local field map and store the volume global transformation
    /*!
      \param [in] localField The pointer (reference) to the field map (which may be updated)
      \param [in] volName The name of the volume (which is used to find the transformation)
      \param [in] scale The B field magnitude scaling factor
    */
    void checkLocalFieldMap(TVirtualMagField*& localField, const TString& volName, Double_t scale);

    // ! Setup all of the local fields. Called by Construct()
    void setAllLocalFields();


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

    //! Vector of fieldInfo for regional fields
    std::vector<fieldInfo> regionInfo_;

    //! Vector of fieldInfo for local fields
    std::vector<fieldInfo> localInfo_;

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

