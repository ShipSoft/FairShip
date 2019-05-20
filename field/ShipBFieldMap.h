/*! \class ShipBFieldMap
  \brief Class that defines a (3d) magnetic field map
  \author John Back <J.J.Back@warwick.ac.uk>
*/

#ifndef ShipBFieldMap_H
#define ShipBFieldMap_H

#include "TGeoMatrix.h"
#include "TVirtualMagField.h"

#include <string>
#include <utility>
#include <vector>

class ShipBFieldMap : public TVirtualMagField
{

 public:

    //! Constructor
    /*!
      \param [in] label A descriptive name/title/label for this field
      \param [in] mapFileName The name of the field map file (distances in cm, fields in Tesla)
      \param [in] xOffset The x global co-ordinate shift to position the field map (cm)
      \param [in] yOffset The y global co-ordinate shift to position the field map (cm)
      \param [in] zOffset The z global co-ordinate shift to position the field map (cm)
      \param [in] phi The first Euler rotation angle about the z axis (degrees)
      \param [in] theta The second Euler rotation angle about the new x axis (degrees)
      \param [in] psi The third Euler rotation angle about the new z axis (degrees)
      \param [in] scale The field magnitude scaling factor (default = 1.0)
      \param [in] isSymmetric Boolean to specify if we have quadrant symmetry (default = false)
    */
    ShipBFieldMap(const std::string& label, const std::string& mapFileName,
		  Float_t xOffset = 0.0, Float_t yOffset = 0.0, Float_t zOffset = 0.0,
		  Float_t phi = 0.0, Float_t theta = 0.0, Float_t psi = 0.0,
		  Float_t scale = 1.0, Bool_t isSymmetric = kFALSE);

    //! Copy constructor with a new global transformation. Use this if you want
    //! to reuse the same field map information elsewhere in the geometry
    /*! 
      \param [in] rhs The ShipBFieldMap object to be copied (retaining any symmetry)
      \param [in] newName The new description or title of the field
      \param [in] newXOffset The new global offset x co-ordinate (cm)
      \param [in] newYOffset The new global offset y co-ordinate (cm)
      \param [in] newZOffset The new global offset z co-ordinate (cm)
      \param [in] newPhi The first Euler rotation angle about the z axis (degrees)
      \param [in] newTheta The second Euler rotation angle about the new x axis (degrees)
      \param [in] newPsi The third Euler rotation angle about the new z axis (degrees)
      \param [in] newScale The field magnitude scaling factor (default = 1.0)
     \returns a copy of the field map object "rhs", keeping the same fieldMap pointer
    */
    ShipBFieldMap(const std::string& newName, const ShipBFieldMap& rhs,
		  Float_t newXOffset, Float_t newYOffset, Float_t newZOffset,
		  Float_t newPhi = 0.0, Float_t newTheta = 0.0, Float_t newPsi = 0.0,
		  Float_t newScale = 1.0);

    //! Destructor
    virtual ~ShipBFieldMap();

    //! Implementation of evaluating the B field
    /*!
      \param [in] position The x,y,z global co-ordinates of the point (cm)
      \param [out] B The x,y,z components of the magnetic field (kGauss = 0.1 tesla)
    */
    virtual void Field(const Double_t* position, Double_t* B);

    //! Typedef for a vector containing a vector of floats
    typedef std::vector< std::vector<Float_t> > floatArray;

    //! Retrieve the field map
    /*!
      \returns the field map
    */
    floatArray* getFieldMap() const {return fieldMap_;}

    //! Set the x global co-ordinate shift
    /*!
      \param [in] xValue The value of the x global co-ordinate shift (cm)
    */
    void SetXOffset(Float_t xValue) {xOffset_ = xValue;}

    //! Set the y global co-ordinate shift
    /*!
      \param [in] yValue The value of the y global co-ordinate shift (cm)
    */
    void SetYOffset(Float_t yValue) {yOffset_ = yValue;}

    //! Set the z global co-ordinate shift
    /*!
      \param [in] zValue The value of the z global co-ordinate shift (cm)
    */
    void SetZOffset(Float_t zValue) {zOffset_ = zValue;}

    //! Set the first Euler rotation angle phi about the z axis
    /*!
      \param [in] phi The first Euler rotation angle about the z axis (degrees)
    */
    void SetPhi(Float_t phi) {phi_ = phi;}

    //! Set the second Euler rotation angle theta about the new x axis
    /*!
      \param [in] theta The second Euler rotation angle about the new x axis (degrees)
    */
    void SetTheta(Float_t theta) {theta_ = theta;}

    //! Set the third Euler rotation angle psi about the new z axis
    /*!
      \param [in] psi The third Euler rotation angle about the new z axis (degrees)
    */
    void SetPsi(Float_t psi) {psi_ = psi;}

    //! Set the field magnitude scaling factor
    /*!
      \param [in] scale The scaling factor for the field magnitude
    */
    void SetScale(Float_t scale) {scale_ = scale;}

    //! Set the boolean to specify if we have quadrant symmetry
    /*!
      \param [in] isSymmetric Boolean to specify if we have quadrant symmetry
    */
    void UseSymmetry(Bool_t flag) {isSymmetric_ = flag;}


    //! Get the name of the map file
    /*!
      \returns the name of the map file as an STL string
    */
    std::string GetMapFileName() const {return mapFileName_;}

    //! Get the number of bins along x
    /*!
      \returns the number of bins along x
    */
    Int_t GetNx() const {return Nx_;}

    //! Get the number of bins along y
    /*!
      \returns the number of bins along y
    */
    Int_t GetNy() const {return Ny_;}

    //! Get the number of bins along z
    /*!
      \returns the number of bins along z
    */
    Int_t GetNz() const {return Nz_;}

    //! Get the total numer of bins
    /*!
      \returns the total number of bins
    */
    Int_t GetNBins() const {return N_;}

    //! Get the minimum value of x for the map
    /*!
      \returns the minimum x co-ordinate (cm)
    */
    Float_t GetXMin() const {return xMin_;}

    //! Get the maximum value of x for the map
    /*!
      \returns the maximum x co-ordinate (cm)
    */
    Float_t GetXMax() const {return xMax_;}

    //! Get the bin width along x for the map
    /*!
      \returns the bin width along x (cm)
    */
    Float_t GetdX() const {return dx_;}

     //! Get the x co-ordinate range for the map
    /*!
      \returns the x co-ordinate range (cm)
    */
    Float_t GetXRange() const {return xRange_;}

   //! Get the minimum value of y for the map
    /*!
      \returns the minimum y co-ordinate (cm)
    */
    Float_t GetYMin() const {return yMin_;}

    //! Get the maximum value of y for the map
    /*!
      \returns the maximum y co-ordinate (cm)
    */
    Float_t GetYMax() const {return yMax_;}

    //! Get the bin width along y for the map
    /*!
      \returns the bin width along y (cm)
    */
    Float_t GetdY() const {return dy_;}

     //! Get the y co-ordinate range for the map
    /*!
      \returns the y co-ordinate range (cm)
    */
    Float_t GetYRange() const {return yRange_;}

    //! Get the minimum value of z for the map
    /*!
      \returns the minimum z co-ordinate (cm)
    */
    Float_t GetZMin() const {return zMin_;}

    //! Get the maximum value of z for the map
    /*!
      \returns the maximum z co-ordinate (cm)
    */
    Float_t GetZMax() const {return zMax_;}

    //! Get the bin width along z for the map
    /*!
      \returns the bin width along z (cm)
    */
    Float_t GetdZ() const {return dz_;}

     //! Get the z co-ordinate range for the map
    /*!
      \returns the z co-ordinate range (cm)
    */
    Float_t GetZRange() const {return zRange_;}

    //! Get the x offset co-ordinate of the map for global positioning
    /*!
      \returns the map's x offset co-ordinate for global positioning (cm)
    */
    Float_t GetXOffset() const {return xOffset_;}

    //! Get the y offset co-ordinate of the map for global positioning
    /*!
      \returns the map's y offset co-ordinate for global positioning (cm)
    */
    Float_t GetYOffset() const {return yOffset_;}

    //! Get the z offset co-ordinate of the map for global positioning
    /*!
      \returns the map's z offset co-ordinate for global positioning (cm)
    */
    Float_t GetZOffset() const {return zOffset_;}

    //! Get the first Euler rotation angle about the z axis for global positioning
    /*!
      \returns the map's first Euler rotation angle about the z axis (degrees)
    */
    Float_t GetPhi() const {return phi_;}

    //! Get the second Euler rotation angle about the new x axis for global positioning
    /*!
      \returns the map's second Euler rotation angle about the new x axis (degrees)
    */
    Float_t GetTheta() const {return theta_;}

    //! Get the third Euler rotation angle about the new z axis for global positioning
    /*!
      \returns the map's third Euler rotation angle about the new z axis (degrees)
    */
    Float_t GetPsi() const {return psi_;}

    //! Get the field magnitude scaling factor
    /*!
      \returns the scaling factor for the field magnitude
    */
    Float_t GetScale() const {return scale_;}

    //! Get the boolean flag to specify if we have quadrant symmetry
    /*!
      \returns the boolean specifying if we have quadrant symmetry
    */
    Bool_t HasSymmetry() const {return isSymmetric_;}

    //! Get the boolean flag to specify if we are a "copy"
    /*!
      \returns the boolean copy flag status
    */
    Bool_t IsACopy() const {return isCopy_;}

    //! ClassDef for ROOT
    ClassDef(ShipBFieldMap,1);


 protected:

 private:

    //! Copy constructor not implemented
    ShipBFieldMap(const ShipBFieldMap& rhs);

    //! Copy assignment operator not implemented
    ShipBFieldMap& operator=(const ShipBFieldMap& rhs);

    //! Enumeration to specify the co-ordinate type
    enum CoordAxis {xAxis = 0, yAxis, zAxis};

    //! Initialisation
    void initialise();

    //! Read the field map data and store the information internally
    void readMapFile();

    //! Process the ROOT file containing the field map data
    void readRootFile();

    //! Process the text file containing the field map data
    void readTextFile();

    // ! Set the coordinate limits from information stored in the datafile
    void setLimits();

    //! Check to see if a point is within the map validity range
    /*!
      \param [in] x The x co-ordinate of the point (cm)
      \param [in] y The y co-ordinate of the point (cm)
      \param [in] z The z co-ordinate of the point (cm)
      \returns true/false if the point is inside the field map range
    */
    Bool_t insideRange(Float_t x, Float_t y, Float_t z);

    //! Typedef for an int-double pair
    typedef std::pair<Int_t, Float_t> binPair;

    //! Get the bin number and fractional distance from the leftmost bin edge
    /*!
      \param [in] x The co-ordinate component of the point (cm)
      \param [in] theAxis The co-ordinate axis (CoordAxis enumeration for x, y or z)
      \returns the bin number and fractional distance from the leftmost bin edge as a pair
    */
    binPair getBinInfo(Float_t x, CoordAxis theAxis);

    //! Find the vector entry of the field map data given the bins iX, iY and iZ
    /*!
      \param [in] iX The bin along the x axis
      \param [in] iY The bin along the y axis
      \param [in] iZ The bin along the z axis
      \returns the index entry for the field map data vector
    */
    Int_t getMapBin(Int_t iX, Int_t iY, Int_t iZ);

    //! Calculate the magnetic field component using trilinear interpolation.
    //! This function uses the various "binX" integers and "uFrac" variables
    /*!
      \param [in] theAxis The co-ordinate axis (CoordAxis enumeration for x, y or z)
      \returns the magnetic field component for the given axis
    */
    Float_t BInterCalc(CoordAxis theAxis);

    //! Store the field map information as a vector of 3 floats.
    //! Map data ordering is given by first incrementing z, then y, then x
    floatArray* fieldMap_;

    //! The name of the map file
    std::string mapFileName_;

    //! Initialisation boolean
    Bool_t initialised_;

    //! Flag to specify if we are a copy of the field map (just a change of global offsets)
    Bool_t isCopy_;

    //! The number of bins along x
    Int_t Nx_;
    
    //! The number of bins along y
    Int_t Ny_;

    //! The number of bins along z
    Int_t Nz_;

    //! The total number of bins
    Int_t N_;

    //! The minimum value of x for the map
    Float_t xMin_;

    //! The maximum value of x for the map
    Float_t xMax_;

    //! The bin width along x
    Float_t dx_;

    //! The co-ordinate range along x
    Float_t xRange_;

    //! The minimum value of y for the map
    Float_t yMin_;

    //! The maximum value of y for the map
    Float_t yMax_;

    //! The bin width along y
    Float_t dy_;

    //! The co-ordinate range along y
    Float_t yRange_;

    //! The minimum value of z for the map
    Float_t zMin_;

    //! The maximum value of z for the map
    Float_t zMax_;

    //! The bin width along z
    Float_t dz_;

    //! The co-ordinate range along z
    Float_t zRange_;

    //! The x value of the positional offset for the map
    Float_t xOffset_;

    //! The y value of the positional offset for the map
    Float_t yOffset_;

    //! The z value of the positional offset for the map
    Float_t zOffset_;

    //! The first Euler rotation angle about the z axis
    Float_t phi_;

    //! The second Euler rotation angle about the new x axis
    Float_t theta_;

    //! The third Euler rotation angle about the new z axis
    Float_t psi_;

    //! The B field magnitude scaling factor
    Float_t scale_;

    //! The boolean specifying if we have quadrant symmetry
    Bool_t isSymmetric_;

    //! The combined translation and rotation transformation
    TGeoMatrix* theTrans_;

    //! Double converting Tesla to kiloGauss (for VMC/FairRoot B field units)
    Float_t Tesla_;

    //! Bin A for the trilinear interpolation
    Int_t binA_;

    //! Bin B for the trilinear interpolation
    Int_t binB_;

    //! Bin C for the trilinear interpolation
    Int_t binC_;

    //! Bin D for the trilinear interpolation
    Int_t binD_;

    //! Bin E for the trilinear interpolation
    Int_t binE_;

    //! Bin F for the trilinear interpolation
    Int_t binF_;

    //! Bin G for the trilinear interpolation
    Int_t binG_;

    //! Bin H for the trilinear interpolation
    Int_t binH_;

    //! Fractional bin distance along x
    Float_t xFrac_;

    //! Fractional bin distance along y
    Float_t yFrac_;

    //! Fractional bin distance along z
    Float_t zFrac_;

    //! Complimentary fractional bin distance along x
    Float_t xFrac1_;

    //! Complimentary fractional bin distance along y
    Float_t yFrac1_;

    //! Complimentary fractional bin distance along z
    Float_t zFrac1_;

};

#endif
